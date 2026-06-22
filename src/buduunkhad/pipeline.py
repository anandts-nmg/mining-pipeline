"""Phase registry and the ordered pipeline runner.

Runs phases in order 00 -> 99, honouring the decision gate before advancing,
supporting ``--from/--to/--only`` and ``--dry-run/--override``, and writing a
per-run log plus a top-level run manifest.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from buduunkhad.config import InputRecord, ProjectConfig, load_config, load_register
from buduunkhad.core import paths, raw_guard, registers, winpath
from buduunkhad.core.gates import GateDecision, GateStatus
from buduunkhad.core.raw_guard import RawIntegrityError
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
    qaqc_passed: bool = False
    gate_status: str = ""
    gate_reason: str = ""
    gate_overridden: bool = False
    error: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "mode": self.mode,
            "status": self.status,
            "outputs": self.outputs,
            "qaqc_passed": self.qaqc_passed,
            "gate": {
                "status": self.gate_status,
                "reason": self.gate_reason,
                "overridden": self.gate_overridden,
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

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "override": self.override,
            "selected_phases": self.selected_phases,
            "stopped_at": self.stopped_at,
            "warnings": self.warnings,
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
    if only:
        wanted = {p.zfill(2) for p in only}
        unknown = wanted - set(PHASE_ORDER)
        if unknown:
            raise ValueError(f"Unknown phase id(s): {sorted(unknown)}")
        return [p for p in registry if p.id in wanted]

    start = PHASE_ORDER.index(from_.zfill(2)) if from_ else 0
    end = PHASE_ORDER.index(to.zfill(2)) if to else len(PHASE_ORDER) - 1
    if start > end:
        raise ValueError(f"--from {from_} comes after --to {to}")
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


def candidate_output_paths(config: ProjectConfig, register: list[InputRecord]) -> list[Path]:
    """Representative paths the pipeline will create (for the length pre-flight).

    Dominated by the 78 working copies (which hold the longest filenames) plus the
    known Phase 01 GIS deliverables.
    """
    out: list[Path] = []
    archive = paths.phase_dir(config.output_root, "00")
    for r in register:
        out.append(archive / r.evidence_group / r.filename)
    p1 = paths.phase_dir(config.output_root, "01")
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
) -> list[str]:
    """Warn (dry-run) or fail (real run) when generated paths exceed ``limit``.

    Skipped entirely when long-path support is enabled (or undeterminable -> we do
    not block). ``enabled`` may be supplied for testing. Returns warning lines.
    """
    if enabled is None:
        enabled = winpath.long_paths_enabled()
    if enabled is not False:  # True or None -> do not block
        return []
    hits = winpath.overlength_paths(candidate_output_paths(config, register), limit=limit)
    if not hits:
        return []
    longest, length = hits[0]
    warning = (
        f"{len(hits)} output path(s) would exceed {limit} chars (longest {length}: {longest}). "
        "Enable Windows long paths (LongPathsEnabled=1) or shorten paths.output_root."
    )
    if dry_run:
        logger.warning(warning)
        return [warning]
    logger.error(warning)
    raise PathTooLongError(warning)


# --------------------------------------------------------------------------- #
# runner
# --------------------------------------------------------------------------- #


def _setup_logger(run_dir: Path) -> logging.Logger:
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("buduunkhad")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(run_dir / "run.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    logger.propagate = False
    return logger


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
) -> RunManifest:
    """Execute the selected phases and return the run manifest."""
    run_id = run_id or datetime.now().strftime("%Y%m%dT%H%M%S")
    run_dir = config.runs_root / run_id
    logger = _setup_logger(run_dir)

    registry = build_registry()
    selected = select_phases(registry, from_=from_, to=to, only=only)
    manifest = RunManifest(
        run_id=run_id,
        started_at=datetime.now().isoformat(timespec="seconds"),
        dry_run=dry_run,
        override=override,
        selected_phases=[p.id for p in selected],
    )

    logger.info(
        "Run %s | dry_run=%s override=%s | phases=%s",
        run_id,
        dry_run,
        override,
        manifest.selected_phases,
    )

    # Path-length pre-flight (warns in dry-run, blocks a real run when long paths
    # are disabled). Runs in both modes so dry-run surfaces the risk early.
    manifest.warnings.extend(
        preflight_path_lengths(config, register, dry_run=dry_run, logger=logger)
    )

    # Real runs require raw data + an unchanged read-only archive; dry runs do not.
    if not dry_run:
        missing = validate_raw_inputs(register, config.raw_root)
        if missing:
            msg = (
                f"{len(missing)} registered raw input(s) missing from {config.raw_root}.\n"
                "First few: "
                + ", ".join(missing[:10])
                + "\nPoint paths.raw_root at the synced archive, or use --dry-run."
            )
            logger.error(msg)
            raise MissingRawDataError(msg)
        verify_raw_integrity(config, override=override, logger=logger)

    # Always ensure the full tree exists so handoffs have somewhere to land.
    paths.build_full_tree(config.output_root)

    ctx = RunContext(
        config=config,
        register=register,
        run_id=run_id,
        dry_run=dry_run,
        override=override,
        logger=logger,
    )

    for phase in selected:
        outcome = PhaseOutcome(
            phase_id=phase.id, name=phase.name, mode=phase.mode, status="pending"
        )
        try:
            phase.prepare(ctx)
            result = phase.run(ctx)
            outcome.status = result.status
            outcome.outputs = [str(p) for p in result.outputs]
            report = phase.qaqc(ctx)
            _write_phase_qaqc(ctx, phase, report)
            outcome.qaqc_passed = report.passed
            decision = phase.gate(report, ctx)
            outcome.gate_status = decision.status.value
            outcome.gate_reason = decision.reason
            outcome.gate_overridden = decision.overridden
            for msg in result.messages:
                logger.info("Phase %s: %s", phase.id, msg)
            logger.info("Phase %s gate: %s (%s)", phase.id, decision.status.value, decision.reason)
        except NotImplementedError as exc:
            outcome.status = "not-implemented"
            outcome.error = str(exc)
            manifest.phases.append(outcome)
            manifest.stopped_at = phase.id
            logger.warning("Phase %s not implemented: %s", phase.id, exc)
            break
        except Exception as exc:  # noqa: BLE001 - record + stop the run
            outcome.status = "error"
            outcome.error = f"{type(exc).__name__}: {exc}"
            manifest.phases.append(outcome)
            manifest.stopped_at = phase.id
            logger.exception("Phase %s errored", phase.id)
            break

        manifest.phases.append(outcome)

        if not dry_run and not _can_advance(decision):
            manifest.stopped_at = phase.id
            logger.warning("Phase %s gate blocked advance; stopping (use --override).", phase.id)
            break

    manifest.finished_at = datetime.now().isoformat(timespec="seconds")
    _write_manifest(run_dir, manifest)
    return manifest


def _can_advance(decision: GateDecision) -> bool:
    return decision.status is GateStatus.GO or decision.overridden


def _write_phase_qaqc(ctx: RunContext, phase: Phase, report) -> Path:  # type: ignore[no-untyped-def]
    name = f"{ctx.config.register_prefix}_Phase{phase.id}_QAQC_Log.xlsx"
    path = ctx.phase_dir(phase.id) / name
    report.write_xlsx(path)
    return path


def _write_manifest(run_dir: Path, manifest: RunManifest) -> Path:
    path = run_dir / "run_manifest.json"
    path.write_text(json.dumps(manifest.as_dict(), indent=2), encoding="utf-8")
    return path


def load_project(
    config_path: Path | str = "config/project.yaml",
) -> tuple[ProjectConfig, list[InputRecord]]:
    """Convenience loader returning ``(config, register)``."""
    config = load_config(config_path)
    register = load_register(config.register_path)
    return config, register
