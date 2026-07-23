"""Phase registry and the ordered pipeline runner.

Runs phases in order 00 -> 99, honouring the decision gate before advancing,
supporting ``--from/--to/--only`` and ``--dry-run/--override``, and writing a
per-run log plus a top-level run manifest.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from buduunkhad import __version__
from buduunkhad.config import InputRecord, ProjectConfig, load_config, load_register
from buduunkhad.core import paths, raw_guard, registers, winpath
from buduunkhad.core.gates import GateDecision, GateStatus
from buduunkhad.core.qaqc import Decision
from buduunkhad.core.raw_guard import RawIntegrityError
from buduunkhad.core.run_artifacts import RunOutputArtifact, has_symlink_component, sha256_file
from buduunkhad.core.run_storage import (
    RUN_LAYOUT_VERSION,
    RUN_MANIFEST_FORMAT_VERSION,
    ProjectExecutionLock,
    RunLayout,
    RunStorageError,
    generate_run_id,
    prepare_staging_phase,
    promote_phase_to_current,
    seal_and_finalize_phase,
    validate_execution_roots,
    validate_run_id,
    verify_sealed_artifacts,
)
from buduunkhad.phases.base import Phase, RunContext
from buduunkhad.phases.phase00_archive import PHASE as Phase00
from buduunkhad.phases.phase01_data_audit import PHASE as Phase01
from buduunkhad.phases.phase02_remote_sensing import PHASE as Phase02
from buduunkhad.phases.phase03_geology_synthesis import PHASE as Phase03
from buduunkhad.phases.phase04_prospect_ranking import PHASE as Phase04
from buduunkhad.phases.phase05_drone_lidar import PHASE as Phase05
from buduunkhad.phases.phase06_recon_pxrf import PHASE as Phase06
from buduunkhad.phases.phase07_rock_chip_sampling import PHASE as Phase07
from buduunkhad.phases.phase08_orientation_geochem import PHASE as Phase08
from buduunkhad.phases.phase09_soil_grid import PHASE as Phase09
from buduunkhad.phases.phase10_integration import PHASE as Phase10
from buduunkhad.phases.phase11_followup import PHASE as Phase11
from buduunkhad.phases.phase99_deliverables import PHASE as Phase99

# Ordered phase classes (the registry).
PHASE_CLASSES: list[type[Phase]] = [
    Phase00,
    Phase01,
    Phase02,
    Phase03,
    Phase04,
    Phase05,
    Phase06,
    Phase07,
    Phase08,
    Phase09,
    Phase10,
    Phase11,
    Phase99,
]

PHASE_ORDER: list[str] = [c.id for c in PHASE_CLASSES]


def build_registry() -> list[Phase]:
    """Instantiate every registered phase in workflow order."""
    return [cls() for cls in PHASE_CLASSES]


# --------------------------------------------------------------------------- #
# results & manifest
# --------------------------------------------------------------------------- #


@dataclass
class PhaseOutcome:
    phase_id: str
    name: str
    mode: str
    status: str
    outputs: list[str] = field(default_factory=list)
    output_artifacts: list[RunOutputArtifact] = field(default_factory=list)
    sealed_files: list[RunOutputArtifact] = field(default_factory=list)
    #: ``qaqc_passed`` means "no QA/QC item failed" — it is True even when items are
    #: still PENDING human completion. ``qaqc_pending`` is the companion signal: a
    #: consumer that needs true completion must read both (passed AND not pending).
    qaqc_passed: bool = False
    qaqc_pending: bool = False
    pending_human_review_or_qaqc_count: int = 0
    gate_status: str = ""
    gate_reason: str = ""
    gate_overridden: bool = False
    gate_provisional: bool = False
    error: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "mode": self.mode,
            "status": self.status,
            "outputs": self.outputs,
            "output_artifacts": [
                artifact.model_dump(mode="json") for artifact in self.output_artifacts
            ],
            "sealed_files": [artifact.model_dump(mode="json") for artifact in self.sealed_files],
            "qaqc_passed": self.qaqc_passed,
            "qaqc_pending": self.qaqc_pending,
            "pending_human_review_or_qaqc_count": self.pending_human_review_or_qaqc_count,
            "gate": {
                "status": self.gate_status,
                "reason": self.gate_reason,
                "overridden": self.gate_overridden,
                "provisional": self.gate_provisional,
            },
            "error": self.error,
        }


@dataclass
class RunManifest:
    run_id: str
    started_at: str
    dry_run: bool
    override: bool
    selected_phases: list[str]
    phases: list[PhaseOutcome] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stopped_at: str = ""
    finished_at: str = ""
    #: Set when the run aborts during startup checks (before/at the phase loop) — records the
    #: error so even a failed run leaves a machine-readable manifest.
    error: str = ""
    manifest_format_version: str = RUN_MANIFEST_FORMAT_VERSION
    run_layout_version: str = RUN_LAYOUT_VERSION
    execution_identity: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "manifest_format_version": self.manifest_format_version,
            "run_layout_version": self.run_layout_version,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "override": self.override,
            "selected_phases": self.selected_phases,
            "stopped_at": self.stopped_at,
            "error": self.error,
            "warnings": self.warnings,
            "execution_identity": self.execution_identity,
            "phases": [p.as_dict() for p in self.phases],
        }


# --------------------------------------------------------------------------- #
# selection & validation
# --------------------------------------------------------------------------- #


def select_phases(
    registry: list[Phase],
    *,
    from_: str | None = None,
    to: str | None = None,
    only: list[str] | None = None,
) -> list[Phase]:
    """Filter the registry by --only or the --from/--to range (inclusive)."""
    if only is not None:
        # `only is not None` (not `if only`): an explicitly-empty list — e.g. `--only ,` which the
        # CLI reduces to [] — must error, not fall through to the full-range branch (which would
        # silently run every phase). Reject empty/whitespace tokens too ('' .zfill(2) == '00').
        cleaned = [p.strip() for p in only if p.strip()]
        if not cleaned:
            raise SelectionError("--only was given but contained no phase ids")
        wanted = {p.zfill(2) for p in cleaned}
        unknown = wanted - set(PHASE_ORDER)
        if unknown:
            raise SelectionError(f"Unknown phase id(s): {sorted(unknown)}")
        return [p for p in registry if p.id in wanted]

    if from_ and from_.zfill(2) not in PHASE_ORDER:
        raise SelectionError(f"Unknown phase id: --from {from_}")
    if to and to.zfill(2) not in PHASE_ORDER:
        raise SelectionError(f"Unknown phase id: --to {to}")
    start = PHASE_ORDER.index(from_.zfill(2)) if from_ else 0
    end = PHASE_ORDER.index(to.zfill(2)) if to else len(PHASE_ORDER) - 1
    if start > end:
        raise SelectionError(f"--from {from_} comes after --to {to}")
    selected_ids = PHASE_ORDER[start : end + 1]
    return [p for p in registry if p.id in selected_ids]


def validate_raw_inputs(register: list[InputRecord], raw_root: Path) -> list[str]:
    """Return the registered filenames that are absent from ``raw_root``."""
    if not raw_root.exists():
        return [r.filename for r in register]
    present = {p.name for p in raw_guard.iter_files(raw_root)}
    return [r.filename for r in register if r.filename not in present]


class MissingRawDataError(RuntimeError):
    """Raised on a real run when registered raw inputs are not present."""


class PathTooLongError(RuntimeError):
    """Raised on a real run when generated paths would exceed the Windows limit."""


class SelectionError(ValueError):
    """Raised when --only/--from/--to name an unknown or empty phase id.

    Subclasses ValueError so existing ``pytest.raises(ValueError)`` callers still match.
    """


class ResumeError(RunStorageError):
    """Raised when an existing run cannot be resumed without changing its identity."""


def _acknowledged_absent(config: ProjectConfig) -> set[str]:
    """Filenames the raw manifest records as documented gaps (absent from the archive)."""
    mpath = config.manifest_path
    if not (mpath and mpath.exists()):
        return set()
    from buduunkhad.core.ingest import acknowledged_absent, load_manifest

    return acknowledged_absent(load_manifest(mpath))


def _manifest_present_names(config: ProjectConfig) -> set[str]:
    """Filenames the manifest records as PRESENT in the canonical archive (status 'matched')."""
    mpath = config.manifest_path
    if not (mpath and mpath.exists()):
        return set()
    from buduunkhad.core.ingest import load_manifest

    return {fn for fn, e in load_manifest(mpath).items() if e.present_in_archive}


def _missing_raw_message(
    unexpected: list[str],
    register: list[InputRecord],
    present_names: set[str],
    config: ProjectConfig,
) -> str:
    """Build the missing-raw-data error, flagging a likely *incomplete directory walk*.

    A common trap is pointing ``raw_root`` at a cloud virtual filesystem (e.g. Google Drive for
    Desktop): its directory listing under-enumerates for Python's walk, so files the manifest
    records as present read as 'missing'. When the walk found *some* inputs yet is missing ones the
    manifest says are present, we say so explicitly — so the operator syncs a real local copy
    instead of chasing phantom gaps. Cross-checks the walk count against the manifest.
    """
    expected_present = _manifest_present_names(config)
    walked_present = sum(1 for r in register if r.filename in present_names)
    suspect = [m for m in unexpected if m in expected_present]
    lines = [
        f"{len(unexpected)} registered raw input(s) missing from {config.raw_root}.",
        "First few: " + ", ".join(unexpected[:10]),
    ]
    if expected_present:
        lines.append(
            f"(directory walk found {walked_present}/{len(expected_present)} manifest-listed inputs.)"
        )
    if suspect and present_names:
        lines.append(
            f"{len(suspect)} of the missing file(s) are recorded PRESENT in the manifest. If "
            "raw_root is a cloud virtual filesystem (e.g. Google Drive for Desktop), its directory "
            "listing can be incomplete for Python — copy the archive to a real LOCAL folder and "
            "point raw_root there. Otherwise these were removed or not yet synced."
        )
    lines.append("Point paths.raw_root at a complete local archive, or use --dry-run.")
    return "\n".join(lines)


def baseline_checksum_path(config: ProjectConfig) -> Path:
    """Location of the SHA-256 baseline written by Phase 00."""
    return paths.phase_dir(config.output_root, "00") / "SHA-256_Checksum_Register.csv"


def verify_raw_integrity(
    config: ProjectConfig, *, override: bool, logger: logging.Logger
) -> raw_guard.IntegrityResult | None:
    """Verify raw_root against the Phase 00 SHA-256 baseline, if one exists.

    Enforces the read-only invariant across runs: if a raw file changed or vanished
    since it was archived, a real run stops loudly (unless ``override``). Returns the
    integrity result, or ``None`` when there is no baseline yet (first run).
    """
    expected = registers.read_checksum_register_csv(baseline_checksum_path(config))
    if not expected:
        return None
    result = raw_guard.verify_against(config.raw_root, expected)
    if result.ok:
        logger.info("Raw integrity OK vs baseline (%d files).", len(expected))
        return result
    msg = (
        f"Raw integrity check failed vs baseline: {result.summary()}. "
        f"changed={result.mismatched[:5]} missing={result.missing[:5]}. "
        "Re-run Phase 00 to refresh the baseline if this change is intentional, "
        "or pass --override to proceed."
    )
    if override:
        logger.warning("OVERRIDE: proceeding despite raw integrity drift. %s", msg)
        return result
    logger.error(msg)
    raise RawIntegrityError(msg)


def candidate_output_paths(
    config: ProjectConfig,
    register: list[InputRecord],
    *,
    execution_root: Path | None = None,
) -> list[Path]:
    """Representative paths the pipeline will create (for the length pre-flight).

    Dominated by the 79 working copies (which hold the longest filenames) plus the
    known Phase 01 GIS deliverables.
    """
    out: list[Path] = []
    archive = (
        execution_root / "00"
        if execution_root is not None
        else paths.phase_dir(config.output_root, "00")
    )
    for r in register:
        out.append(archive / r.evidence_group / r.filename)
    p1 = (
        execution_root / "01"
        if execution_root is not None
        else paths.phase_dir(config.output_root, "01")
    )
    prefix = config.register_prefix
    out.append(p1 / "06_Master_GeoPackage_Schema" / f"{prefix}_Master_GIS_Database.gpkg")
    out.append(p1 / "03_CRS_Check" / f"{prefix}_CRS_Georeference_QAQC_Log.xlsx")
    return out


def preflight_path_lengths(
    config: ProjectConfig,
    register: list[InputRecord],
    *,
    dry_run: bool,
    logger: logging.Logger,
    limit: int = winpath.WINDOWS_MAX_PATH,
    enabled: bool | None = None,
    execution_root: Path | None = None,
) -> list[str]:
    """Warn (dry-run) or fail (real run) when generated paths exceed ``limit``.

    Skipped entirely when long-path support is enabled (or undeterminable -> we do
    not block). ``enabled`` may be supplied for testing. Returns warning lines.
    """
    if enabled is None:
        enabled = winpath.long_paths_enabled()
    if enabled is not False:  # True or None -> do not block
        return []
    hits = winpath.overlength_paths(
        candidate_output_paths(config, register, execution_root=execution_root), limit=limit
    )
    if not hits:
        return []
    longest, length = hits[0]
    warning = (
        f"{len(hits)} output path(s) would exceed {limit} chars (longest {length}: {longest}). "
        "Enable Windows long paths (LongPathsEnabled=1) or shorten paths.runs_root."
    )
    if dry_run:
        logger.warning(warning)
        return [warning]
    logger.error(warning)
    raise PathTooLongError(warning)


# --------------------------------------------------------------------------- #
# immutable execution identity and resume
# --------------------------------------------------------------------------- #


def _sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _project_configuration_identity(config: ProjectConfig) -> str:
    data = config.model_dump(mode="json", context={"config_serialization_version": "ai-v1"})
    data.pop("base_dir", None)
    return _sha256_json(data)


def _methodology_contract_identity(config: ProjectConfig) -> str:
    records: list[dict[str, object]] = []
    for root in (
        config.base_dir / "config" / "methodology",
        config.base_dir / "docs" / "methodology",
    ):
        if not root.is_dir():
            continue
        for path in sorted(value for value in root.rglob("*") if value.is_file()):
            relative = path.relative_to(config.base_dir).as_posix()
            records.append(
                {
                    "path": relative,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return _sha256_json(records)


def _code_identity() -> str:
    root = Path(__file__).resolve().parent
    records: list[dict[str, object]] = []
    if root.is_dir():
        for path in sorted(root.rglob("*.py")):
            records.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_file(path),
                }
            )
    return f"{__version__}:{_sha256_json(records)}"


def _source_inventory_identity(config: ProjectConfig, register: list[InputRecord]) -> str:
    index = (
        {path.name: path for path in raw_guard.iter_files(config.raw_root)}
        if config.raw_root.is_dir()
        else {}
    )
    records: list[dict[str, object]] = []
    for item in sorted(register, key=lambda value: value.no):
        path = index.get(item.filename)
        records.append(
            {
                "no": item.no,
                "evidence_group": item.evidence_group,
                "filename": item.filename,
                "present": path is not None,
                "sha256": sha256_file(path) if path is not None else None,
                "size_bytes": path.stat().st_size if path is not None else None,
            }
        )
    return _sha256_json(records)


def _execution_identity(
    config: ProjectConfig,
    register: list[InputRecord],
    *,
    selected_phases: list[str],
    dry_run: bool,
    override: bool,
) -> dict[str, str]:
    parameters = {
        "selected_phases": selected_phases,
        "dry_run": dry_run,
        "override": override,
    }
    register_data = [item.model_dump(mode="json") for item in register]
    return {
        "source_inventory_sha256": _source_inventory_identity(config, register),
        "input_register_sha256": _sha256_json(register_data),
        "project_configuration_sha256": _project_configuration_identity(config),
        "methodology_contract_sha256": _methodology_contract_identity(config),
        "code_version": _code_identity(),
        "parameters_sha256": _sha256_json(parameters),
    }


def _phase_outcome_from_dict(value: dict[str, Any]) -> PhaseOutcome:
    gate = value.get("gate")
    if not isinstance(gate, dict):
        raise ResumeError("run manifest phase gate is malformed")
    artifacts = value.get("output_artifacts")
    sealed_files = value.get("sealed_files")
    if not isinstance(artifacts, list) or not isinstance(sealed_files, list):
        raise ResumeError("run manifest phase artifact inventory is malformed")
    outputs = value.get("outputs")
    if not isinstance(outputs, list) or not all(isinstance(item, str) for item in outputs):
        raise ResumeError("run manifest phase output inventory is malformed")
    try:
        return PhaseOutcome(
            phase_id=str(value["phase_id"]),
            name=str(value["name"]),
            mode=str(value["mode"]),
            status=str(value["status"]),
            outputs=list(outputs),
            output_artifacts=[RunOutputArtifact.model_validate(item) for item in artifacts],
            sealed_files=[RunOutputArtifact.model_validate(item) for item in sealed_files],
            qaqc_passed=value.get("qaqc_passed") is True,
            qaqc_pending=value.get("qaqc_pending") is True,
            pending_human_review_or_qaqc_count=int(
                value.get("pending_human_review_or_qaqc_count", 0)
            ),
            gate_status=str(gate.get("status", "")),
            gate_reason=str(gate.get("reason", "")),
            gate_overridden=gate.get("overridden") is True,
            gate_provisional=gate.get("provisional") is True,
            error=str(value.get("error", "")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ResumeError("run manifest phase record is malformed") from exc


def _load_resume_manifest(layout: RunLayout) -> RunManifest:
    try:
        data = json.loads(layout.manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ResumeError(f"run manifest is unreadable: {layout.manifest_path}") from exc
    if not isinstance(data, dict):
        raise ResumeError("run manifest root must be an object")
    if data.get("manifest_format_version") != RUN_MANIFEST_FORMAT_VERSION:
        raise ResumeError("only run-isolated v2 manifests can be resumed")
    if data.get("run_layout_version") != RUN_LAYOUT_VERSION:
        raise ResumeError("run manifest layout is unsupported for resume")
    if data.get("run_id") != layout.run_id:
        raise ResumeError("run manifest identity does not match its directory")
    phases = data.get("phases")
    identity = data.get("execution_identity")
    selected = data.get("selected_phases")
    if (
        not isinstance(phases, list)
        or not all(isinstance(value, dict) for value in phases)
        or not isinstance(identity, dict)
        or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in identity.items()
        )
        or not isinstance(selected, list)
        or not all(isinstance(value, str) for value in selected)
    ):
        raise ResumeError("run manifest execution identity is malformed")
    return RunManifest(
        run_id=layout.run_id,
        started_at=str(data.get("started_at", "")),
        dry_run=data.get("dry_run") is True,
        override=data.get("override") is True,
        selected_phases=list(selected),
        phases=[_phase_outcome_from_dict(value) for value in phases],
        warnings=[str(value) for value in data.get("warnings", [])],
        stopped_at=str(data.get("stopped_at", "")),
        finished_at=str(data.get("finished_at", "")),
        error=str(data.get("error", "")),
        execution_identity=dict(identity),
    )


def _discard_partial_stage(layout: RunLayout, phase_id: str) -> None:
    stage = layout.staging_phase(phase_id)
    if not stage.exists():
        return
    if stage.is_symlink() or has_symlink_component(stage):
        raise ResumeError(f"partial phase staging is unsafe and cannot be discarded: {stage}")
    try:
        stage.resolve().relative_to(layout.staging_root.resolve())
    except ValueError as exc:
        raise ResumeError(f"partial phase staging escapes the run: {stage}") from exc
    shutil.rmtree(stage)


def _discard_unrecorded_finalized_phase(layout: RunLayout, phase_id: str) -> None:
    """Discard a crash-window phase directory that no manifest outcome sealed."""

    phase_dir = layout.sealed_phase(phase_id)
    if not phase_dir.exists():
        return
    if phase_dir.is_symlink() or has_symlink_component(phase_dir):
        raise ResumeError(f"unrecorded finalized phase is unsafe: {phase_dir}")
    try:
        phase_dir.resolve().relative_to(layout.phases_root.resolve())
    except ValueError as exc:
        raise ResumeError(f"unrecorded finalized phase escapes the run: {phase_dir}") from exc
    shutil.rmtree(phase_dir)


# --------------------------------------------------------------------------- #
# runner
# --------------------------------------------------------------------------- #


def _setup_logger(layout: RunLayout, *, append: bool = False) -> logging.Logger:
    layout.logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("buduunkhad")
    logger.setLevel(logging.INFO)
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    fh = logging.FileHandler(layout.log_path, mode="a" if append else "w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    logger.propagate = False
    return logger


def _close_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.flush()
        handler.close()
    logger.handlers.clear()


def run_pipeline(
    config: ProjectConfig,
    register: list[InputRecord],
    *,
    from_: str | None = None,
    to: str | None = None,
    only: list[str] | None = None,
    dry_run: bool = False,
    override: bool = False,
    run_id: str | None = None,
    resume: bool = False,
) -> RunManifest:
    """Execute selected phases in one isolated run directory.

    ``resume=True`` requires an explicit existing ``run_id`` and an exact match of source,
    configuration, methodology, code, and invocation identities. Completed sealed phases are
    verified and never repeated; any partial staging for the first incomplete phase is discarded
    before that phase is restarted from an empty directory.
    """
    if resume and run_id is None:
        raise ResumeError("resume requires an explicit run ID")
    run_id = validate_run_id(run_id or generate_run_id())

    # Validate the phase selection BEFORE creating the run dir/logger, so a bad --only/--from/--to
    # fails without leaving an orphan run directory (C3).
    registry = build_registry()
    selected = select_phases(registry, from_=from_, to=to, only=only)

    selected_ids = [phase.id for phase in selected]
    validate_execution_roots(config.raw_root, config.output_root, config.runs_root)
    layout = RunLayout(config.runs_root, run_id)
    with ProjectExecutionLock(config.runs_root, run_id):
        layout.initialize(resume=resume)
        logger = _setup_logger(layout, append=resume)
        identity = _execution_identity(
            config,
            register,
            selected_phases=selected_ids,
            dry_run=dry_run,
            override=override,
        )
        completed_ids: set[str] = set()
        if resume:
            manifest = _load_resume_manifest(layout)
            if (
                manifest.selected_phases != selected_ids
                or manifest.dry_run != dry_run
                or manifest.override != override
                or manifest.execution_identity != identity
            ):
                raise ResumeError(
                    "resume identity differs from the recorded sources, configuration, "
                    "methodology, code, or parameters"
                )
            retained: list[PhaseOutcome] = []
            for outcome in manifest.phases:
                if outcome.phase_id not in selected_ids:
                    raise ResumeError("run manifest contains an unselected phase")
                if outcome.status not in {"ok", "dry-run"}:
                    break
                if not layout.sealed_phase(outcome.phase_id).is_dir():
                    raise ResumeError(
                        f"completed Phase {outcome.phase_id} lacks its finalized directory"
                    )
                sealed_map = {artifact.path: artifact for artifact in outcome.sealed_files}
                output_map = {artifact.path: artifact for artifact in outcome.output_artifacts}
                inconsistent = (
                    len(sealed_map) != len(outcome.sealed_files)
                    or len(output_map) != len(outcome.output_artifacts)
                    or not set(outcome.outputs) <= set(sealed_map)
                    or any(
                        sealed_map.get(path) != artifact for path, artifact in output_map.items()
                    )
                )
                if dry_run:
                    inconsistent = inconsistent or bool(output_map)
                else:
                    inconsistent = inconsistent or set(outcome.outputs) != set(output_map)
                if inconsistent:
                    raise ResumeError(
                        f"completed Phase {outcome.phase_id} has an inconsistent file seal"
                    )
                try:
                    verify_sealed_artifacts(layout, outcome.sealed_files)
                except RunStorageError as exc:
                    raise ResumeError(str(exc)) from exc
                retained.append(outcome)
                completed_ids.add(outcome.phase_id)
            expected_prefix = selected_ids[: len(retained)]
            if [outcome.phase_id for outcome in retained] != expected_prefix:
                raise ResumeError("completed phases are not a prefix of the selected run")
            if retained and retained[-1].gate_status == GateStatus.BLOCKED.value:
                if manifest.error:
                    for outcome in retained:
                        if not dry_run:
                            promote_phase_to_current(
                                layout,
                                outcome.phase_id,
                                config.output_root,
                                outcome.sealed_files,
                            )
                        outcome.error = ""
                    manifest.error = ""
                    manifest.finished_at = datetime.now(UTC).isoformat()
                    _write_manifest(layout, manifest)
                logger.info("Resume verified a gate-blocked completed run; no work repeated.")
                _close_logger(logger)
                return manifest
            if len(retained) == len(selected):
                if manifest.error:
                    for outcome in retained:
                        if not dry_run:
                            promote_phase_to_current(
                                layout,
                                outcome.phase_id,
                                config.output_root,
                                outcome.sealed_files,
                            )
                        outcome.error = ""
                    manifest.error = ""
                    manifest.stopped_at = ""
                    manifest.finished_at = datetime.now(UTC).isoformat()
                    _write_manifest(layout, manifest)
                logger.info("Resume verified a completed run; no work repeated.")
                _close_logger(logger)
                return manifest
            manifest.phases = retained
            manifest.stopped_at = ""
            manifest.finished_at = ""
            manifest.error = ""
            for phase_id in selected_ids[len(retained) :]:
                _discard_partial_stage(layout, phase_id)
                _discard_unrecorded_finalized_phase(layout, phase_id)
        else:
            manifest = RunManifest(
                run_id=run_id,
                started_at=datetime.now(UTC).isoformat(),
                dry_run=dry_run,
                override=override,
                selected_phases=selected_ids,
                execution_identity=identity,
            )

        # Persist the immutable run identity before any preflight or phase side effect. A hard
        # interruption during the first phase therefore leaves enough information to validate the
        # resume and discard its partial staging instead of creating an orphaned, ambiguous run.
        _write_manifest(layout, manifest)

        logger.info(
            "Run %s | dry_run=%s override=%s resume=%s | phases=%s",
            run_id,
            dry_run,
            override,
            resume,
            manifest.selected_phases,
        )

        # The body runs under try/finally so a startup abort still leaves a machine-readable
        # manifest. The lock covers every filesystem mutation and is always released last.
        try:
            # Path-length pre-flight runs in both modes so dry-run surfaces the risk early.
            manifest.warnings.extend(
                preflight_path_lengths(
                    config,
                    register,
                    dry_run=dry_run,
                    logger=logger,
                    execution_root=layout.staging_root,
                )
            )

            # Real runs require raw data + an unchanged read-only archive; dry runs do not.
            if not dry_run:
                present_names = (
                    {p.name for p in raw_guard.iter_files(config.raw_root)}
                    if config.raw_root.exists()
                    else set()
                )
                missing = [r.filename for r in register if r.filename not in present_names]
                if missing:
                    acknowledged = _acknowledged_absent(config)
                    unexpected = [m for m in missing if m not in acknowledged]
                    ack = [m for m in missing if m in acknowledged]
                    if ack:
                        logger.warning(
                            "%d acknowledged data gap(s) (manifest-flagged absent): %s",
                            len(ack),
                            ", ".join(ack[:10]),
                        )
                        manifest.warnings.append(
                            f"{len(ack)} acknowledged data gap(s): {', '.join(ack)}"
                        )
                    if unexpected:
                        msg = _missing_raw_message(unexpected, register, present_names, config)
                        logger.error(msg)
                        raise MissingRawDataError(msg)
                verify_raw_integrity(config, override=override, logger=logger)

            ctx = RunContext(
                config=config,
                register=register,
                run_id=run_id,
                dry_run=dry_run,
                override=override,
                logger=logger,
                run_isolated=True,
            )

            for phase in selected:
                if phase.id in completed_ids:
                    continue
                outcome = PhaseOutcome(
                    phase_id=phase.id, name=phase.name, mode=phase.mode, status="pending"
                )
                decision: GateDecision | None = None
                finalized = False
                try:
                    prepare_staging_phase(layout, phase.id)
                    ctx.active_phase_id = phase.id
                    phase.prepare(ctx)
                    result = phase.run(ctx)
                    outcome.status = result.status
                    declared_outputs = list(result.outputs)
                    report = phase.qaqc(ctx)
                    qaqc_path = _write_phase_qaqc(ctx, phase, report)
                    declared_outputs.append(qaqc_path)
                    outcome.qaqc_passed = report.passed
                    outcome.qaqc_pending = report.has_pending
                    outcome.pending_human_review_or_qaqc_count = sum(
                        item.decision is Decision.PENDING for item in report.items
                    )
                    decision = phase.gate(report, ctx)
                    outcome.gate_status = decision.status.value
                    outcome.gate_reason = decision.reason
                    outcome.gate_overridden = decision.overridden
                    outcome.gate_provisional = decision.provisional
                    if not report.passed and not dry_run:
                        outcome.status = "qaqc-failed"
                        outcome.outputs = []
                    else:
                        finalized_outputs, artifacts, sealed_files = seal_and_finalize_phase(
                            layout, phase.id, declared_outputs
                        )
                        finalized = True
                        outcome.outputs = [
                            path.relative_to(layout.run_dir).as_posix()
                            for path in finalized_outputs
                        ]
                        outcome.sealed_files = list(sealed_files)
                        if not dry_run:
                            outcome.output_artifacts = list(artifacts)
                            promote_phase_to_current(
                                layout,
                                phase.id,
                                config.output_root,
                                outcome.sealed_files,
                            )
                    for msg in result.messages:
                        logger.info("Phase %s: %s", phase.id, msg)
                    logger.info(
                        "Phase %s gate: %s (%s)",
                        phase.id,
                        decision.status.value,
                        decision.reason,
                    )
                except NotImplementedError as exc:
                    outcome.status = "not-implemented"
                    outcome.outputs = []
                    outcome.output_artifacts = []
                    outcome.sealed_files = []
                    outcome.error = str(exc)
                    manifest.error = f"NotImplementedError: {exc}"
                    manifest.phases.append(outcome)
                    manifest.stopped_at = phase.id
                    logger.warning("Phase %s not implemented: %s", phase.id, exc)
                    _write_manifest(layout, manifest)
                    break
                except Exception as exc:  # noqa: BLE001 - record + stop the run
                    if not finalized:
                        outcome.status = "error"
                        outcome.outputs = []
                        outcome.output_artifacts = []
                        outcome.sealed_files = []
                    outcome.error = f"{type(exc).__name__}: {exc}"
                    manifest.error = outcome.error
                    manifest.phases.append(outcome)
                    manifest.stopped_at = phase.id
                    logger.exception("Phase %s errored", phase.id)
                    _write_manifest(layout, manifest)
                    break
                finally:
                    ctx.active_phase_id = None

                manifest.phases.append(outcome)
                _write_manifest(layout, manifest)

                if outcome.status == "qaqc-failed":
                    manifest.stopped_at = phase.id
                    manifest.error = f"Phase {phase.id} QA/QC failed before artifact sealing"
                    logger.warning("Phase %s QA/QC failed; unsealed staging retained.", phase.id)
                    break
                if not dry_run and decision is not None and not _can_advance(decision):
                    manifest.stopped_at = phase.id
                    logger.warning(
                        "Phase %s gate blocked advance; stopping (%s).",
                        phase.id,
                        decision.reason,
                    )
                    break
        except Exception as exc:  # startup abort — record it in the manifest, then re-raise
            manifest.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            manifest.finished_at = datetime.now(UTC).isoformat()
            try:
                _write_manifest(layout, manifest)
            finally:
                _close_logger(logger)

        return manifest


def _can_advance(decision: GateDecision) -> bool:
    return decision.status is GateStatus.GO or decision.overridden


def _write_phase_qaqc(ctx: RunContext, phase: Phase, report) -> Path:
    name = f"{ctx.config.register_prefix}_Phase{phase.id}_QAQC_Log.xlsx"
    path = ctx.phase_dir(phase.id) / name
    report.write_xlsx(path)
    return path


def _write_manifest(layout: RunLayout, manifest: RunManifest) -> Path:
    path = layout.manifest_path
    temporary = layout.run_dir / ".run_manifest.json.tmp"
    temporary.write_text(
        json.dumps(manifest.as_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def load_project(
    config_path: Path | str = "config/project.yaml",
) -> tuple[ProjectConfig, list[InputRecord]]:
    """Convenience loader returning ``(config, register)``."""
    config = load_config(config_path)
    register = load_register(config.register_path)
    return config, register
