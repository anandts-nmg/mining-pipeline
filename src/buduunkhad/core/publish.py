"""Publish curated deliverables to a publish root (e.g. a Google-Drive folder).

Per ADR 0001, generated outputs are build artifacts. This copies only the small,
high-value **deliverables** — GIS layers, registers, logs, reports — into a
*versioned* subfolder under ``publish_root`` (typically a Drive-for-Desktop folder
so teammates can see them once shared). The bulky **raw working copies** (rasters
and scans copied from the read-only archive) are deliberately excluded so we never
re-upload duplicates of data that already lives in the Drive.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from buduunkhad import __version__
from buduunkhad.core.publication_manifest import (
    AGGREGATION_NOTICE,
    PUBLICATION_MANIFEST_FORMAT_VERSION,
    PublicationManifest,
    PublicationProjectReference,
    PublishedOutput,
    PublishedPhase,
    publication_id_for,
    publication_status_for,
)

#: Deliverable file types. Derived rasters (``.tif`` COGs from Phase 02 onward) are
#: deliverables; raw working copies are excluded by **folder** (see ``WORKING_COPY_DIRS``),
#: not by extension, so raw ``.tif`` duplicates of the Drive archive are never re-uploaded.
DELIVERABLE_SUFFIXES: frozenset[str] = frozenset(
    {".gpkg", ".qgz", ".xlsx", ".csv", ".docx", ".pdf", ".md", ".json", ".tif"}
)

#: Folders that hold raw working copies — never published (belt-and-suspenders on top
#: of the extension filter).
WORKING_COPY_DIRS: frozenset[str] = frozenset(
    {
        "01_Tectonic_Terrane_KMZ",
        "02_DEM_ALOS_ASTERGDEM",
        "03_KOMPSAT2_MSC_L1G",
        "04_HeavyMineral_StreamSediment_Field",
        "05_Geology_Mineral_Prospectivity",
        "06_Regional_Metallogenic_L47B",
        "07_Basemap_Sentinel2_ASTER",
        "01_Input_Working_Copy",
        "00_Input_Working_Copy",
        # ASTER per-band warp intermediates (re-derivable from #73; the deliverables are the
        # index/score/target products in 04_Index_Calculation and 05_Score_Class_Binary).
        "02_Band_Extraction",
        "03_Project_UTM47",
        # Phase-00 copies of UNREGISTERED raw docs (DataRoom registers, folder readme) —
        # raw duplicates like the evidence-group folders above (also in the raw backup).
        "08_Supplementary_Source_Documents",
    }
)


class PublishError(RuntimeError):
    """Raised when a publish would silently overwrite (label reuse) or clobber (name collision)."""


@dataclass(frozen=True)
class PublishResult:
    dest: Path
    files: list[Path] = field(default_factory=list)
    skipped_working_copies: int = 0


@dataclass(frozen=True)
class _RunPhaseRecord:
    manifest_path: Path
    manifest_sha256: str
    run_id: str
    phase_id: str
    execution_status: str
    outputs: tuple[Path, ...]
    gate_state: str
    gate_provisional: bool
    human_review_or_qaqc_pending: bool
    pending_human_review_or_qaqc_count: int | None


def _require_safe_component(value: str, field_name: str) -> str:
    if (
        not value
        or value in {".", ".."}
        or any(separator in value for separator in ("/", "\\", ":"))
    ):
        raise PublishError(f"{field_name} must be one path-safe component")
    return value


def _is_working_copy(rel: Path) -> bool:
    return any(part in WORKING_COPY_DIRS for part in rel.parts)


def _phase_tag(rel: Path) -> str:
    """Shallow phase grouping for the published package (keeps paths short, reader-friendly).

    Phase folders are named ``<NN>_<...>``; group everything by the two-digit prefix into
    ``PhaseNN`` (so ``03_Phase_3_Geological_...`` publishes under ``Phase03/``, not its long name).
    """
    top = rel.parts[0] if rel.parts else ""
    if len(top) >= 3 and top[:2].isdigit() and top[2] == "_":
        return f"Phase{top[:2]}"
    return top or "misc"


def collect_deliverables(output_root: Path) -> list[Path]:
    """Deliverable files under ``output_root`` (excludes raw working copies)."""
    output_root = Path(output_root)
    out: list[Path] = []
    for p in sorted(output_root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(output_root)
        if _is_working_copy(rel):
            continue
        if p.suffix.lower() in DELIVERABLE_SUFFIXES:
            out.append(p)
    return out


def latest_run_manifest(runs_root: Path) -> Path | None:
    """The newest ``run_manifest.json`` under ``runs_root`` (runs are timestamp-named)."""
    runs_root = Path(runs_root)
    if not runs_root.exists():
        return None
    manifests = sorted(runs_root.glob("*/run_manifest.json"))
    return manifests[-1] if manifests else None


def latest_gate_per_phase(runs_root: Path) -> dict[str, dict[str, object]]:
    """Most-recent **real** (non-dry) gate per phase across all run manifests.

    The published package spans phases run at different times, so a single latest manifest
    (which may be a dry run or cover only some phases) can't describe every PhaseNN folder.
    Iterate manifests in ascending (timestamp) order so the last real gate seen per phase wins.
    """
    runs_root = Path(runs_root)
    out: dict[str, dict[str, object]] = {}
    if not runs_root.exists():
        return out
    for man in sorted(runs_root.glob("*/run_manifest.json")):
        try:
            data = json.loads(man.read_text(encoding="utf-8"))
        except (ValueError, OSError):  # pragma: no cover - defensive
            continue
        if data.get("dry_run"):
            continue
        for p in data.get("phases", []):
            gate = p.get("gate", {})
            if gate.get("status"):
                out[p["phase_id"]] = {
                    "status": gate["status"],
                    "provisional": gate.get("provisional", False),
                    "run_id": data.get("run_id", ""),
                }
    return out


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PublishError(f"run manifest contains duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise PublishError(f"run manifest is unreadable or invalid: {path}") from exc
    if not isinstance(value, dict):
        raise PublishError(f"run manifest root must be an object: {path}")
    return value


def _resolve_recorded_output(value: str, output_root: Path) -> Path:
    recorded = Path(value)
    if recorded.is_absolute():
        return recorded.resolve()
    candidates = (
        (output_root / recorded).resolve(),
        (output_root.parent / recorded).resolve(),
        (Path.cwd() / recorded).resolve(),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    for candidate in candidates:
        try:
            candidate.relative_to(output_root.resolve())
        except ValueError:
            continue
        return candidate
    return candidates[0]


def _deliverable_relative(path: Path, output_root: Path) -> Path | None:
    try:
        relative = path.resolve().relative_to(output_root.resolve())
    except ValueError:
        return None
    if _is_working_copy(relative) or path.suffix.lower() not in DELIVERABLE_SUFFIXES:
        return None
    return relative


def _load_run_phase_records(runs_root: Path, output_root: Path) -> dict[str, list[_RunPhaseRecord]]:
    records: dict[str, list[_RunPhaseRecord]] = {}
    if not runs_root.exists():
        raise PublishError(f"runs root does not exist: {runs_root}")
    manifests = sorted(runs_root.glob("*/run_manifest.json"))
    if not manifests:
        raise PublishError(f"no source run manifests found under: {runs_root}")
    for manifest_path in manifests:
        data = _load_json_object(manifest_path)
        if data.get("dry_run") is True:
            continue
        run_id = data.get("run_id")
        phases = data.get("phases")
        if not isinstance(run_id, str) or not run_id.strip() or not isinstance(phases, list):
            raise PublishError(f"run manifest lacks a valid run_id or phases list: {manifest_path}")
        _require_safe_component(run_id, "source run ID")
        for phase in phases:
            if not isinstance(phase, dict):
                raise PublishError(
                    f"run manifest contains a malformed phase record: {manifest_path}"
                )
            phase_id = phase.get("phase_id")
            execution_status = phase.get("status")
            output_values = phase.get("outputs")
            gate = phase.get("gate")
            if (
                not isinstance(phase_id, str)
                or re.fullmatch(r"(0[0-9]|1[01]|99)", phase_id) is None
                or not isinstance(execution_status, str)
                or not isinstance(output_values, list)
                or not all(isinstance(item, str) for item in output_values)
                or not isinstance(gate, dict)
                or not isinstance(gate.get("status"), str)
            ):
                raise PublishError(
                    f"run manifest phase lacks outputs or gate provenance: {manifest_path}"
                )
            pending_count = phase.get("pending_human_review_or_qaqc_count")
            if pending_count is not None and (type(pending_count) is not int or pending_count < 0):
                raise PublishError(f"run manifest has an invalid pending count: {manifest_path}")
            record = _RunPhaseRecord(
                manifest_path=manifest_path,
                manifest_sha256=_sha256(manifest_path),
                run_id=run_id,
                phase_id=phase_id,
                execution_status=execution_status,
                outputs=tuple(
                    _resolve_recorded_output(item, output_root) for item in output_values
                ),
                gate_state=str(gate["status"]),
                gate_provisional=gate.get("provisional") is True,
                human_review_or_qaqc_pending=phase.get("qaqc_pending") is True,
                pending_human_review_or_qaqc_count=pending_count,
            )
            records.setdefault(phase_id, []).append(record)
    return records


def _phase_id_from_relative(relative: Path) -> str:
    tag = _phase_tag(relative)
    if not tag.startswith("Phase") or len(tag) != 7 or not tag[5:].isdigit():
        raise PublishError(f"deliverable is not inside a registered phase directory: {relative}")
    return tag[5:]


def _is_runner_qaqc_output(path: Path, output_root: Path, phase_id: str) -> bool:
    relative = path.resolve().relative_to(output_root.resolve())
    return _phase_id_from_relative(relative) == phase_id and relative.name.endswith(
        f"_Phase{phase_id}_QAQC_Log.xlsx"
    )


def _select_publication_records(
    output_root: Path,
    sources: tuple[Path, ...],
    records: dict[str, list[_RunPhaseRecord]],
) -> dict[str, _RunPhaseRecord]:
    actual: dict[str, set[Path]] = {}
    for source in sources:
        relative = source.resolve().relative_to(output_root.resolve())
        actual.setdefault(_phase_id_from_relative(relative), set()).add(source.resolve())

    phase_ids = set(actual)
    for phase_id, candidates in records.items():
        latest = candidates[-1]
        if any(_deliverable_relative(path, output_root) is not None for path in latest.outputs):
            phase_ids.add(phase_id)

    selected: dict[str, _RunPhaseRecord] = {}
    for phase_id in sorted(phase_ids):
        phase_candidates = records.get(phase_id)
        if not phase_candidates:
            raise PublishError(f"no source run manifest records published Phase {phase_id}")
        record = phase_candidates[-1]
        if record.execution_status != "ok":
            raise PublishError(
                f"Phase {phase_id} source run {record.run_id} is not complete: "
                f"{record.execution_status}"
            )
        expected = {
            path.resolve()
            for path in record.outputs
            if _deliverable_relative(path, output_root) is not None
        }
        observed = actual.get(phase_id, set())
        missing = sorted(str(path) for path in expected - observed)
        unattributed = sorted(
            str(path)
            for path in observed - expected
            if not _is_runner_qaqc_output(path, output_root, phase_id)
        )
        if missing:
            raise PublishError(
                f"Phase {phase_id} source run {record.run_id} has missing output(s): {missing}"
            )
        if unattributed:
            raise PublishError(
                f"Phase {phase_id} contains output(s) not attributed to its latest source run: "
                f"{unattributed}"
            )
        if not observed:
            raise PublishError(f"Phase {phase_id} source run has no publishable outputs")
        selected[phase_id] = record
    if not selected:
        raise PublishError("publication contains no phase deliverables")
    return selected


def _portable_project_reference(config_path: Path) -> str:
    resolved = config_path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return f"external-config::{resolved.name}"


def _git_commit_sha(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip().lower()
    if len(value) not in {40, 64} or any(
        character not in "0123456789abcdef" for character in value
    ):
        return None
    return value


def publish(
    output_root: Path,
    publish_root: Path,
    label: str,
    *,
    runs_root: Path | None = None,
    overwrite: bool = False,
    project_config_path: Path | None = None,
    superseded_publication_id: str | None = None,
    published_at: datetime | None = None,
) -> PublishResult:
    """Copy provenance-bound deliverables into a local publication staging package.

    Raises :class:`PublishError` if the label dir already exists and is non-empty (unless
    ``overwrite=True``) or if two source files would flatten to the same published path — both
    would otherwise silently overwrite, so we fail loudly per the repo's philosophy.
    """
    _require_safe_component(label, "publish label")
    if (
        superseded_publication_id is not None
        and re.fullmatch(r"pub-[0-9a-f]{32}", superseded_publication_id) is None
    ):
        raise PublishError("superseded publication ID is invalid")
    if published_at is not None and (
        published_at.tzinfo is None or published_at.utcoffset() is None
    ):
        raise PublishError("publication timestamp must be timezone-aware")
    publication_time = (published_at or datetime.now(UTC)).astimezone(UTC)
    output_root = Path(output_root).resolve()
    publish_root = Path(publish_root).resolve()
    if runs_root is None:
        raise PublishError("runs_root is required to bind published phases to source runs")
    runs_root = Path(runs_root).resolve()
    config_path = Path(project_config_path or "config/project.yaml")
    if not config_path.is_file():
        raise PublishError(f"authoritative project configuration is unavailable: {config_path}")
    project = PublicationProjectReference(
        configuration_reference=_portable_project_reference(config_path),
        configuration_sha256=_sha256(config_path),
    )

    dest = publish_root / f"Buduunkhad_Deliverables_{label}"
    if dest.exists() and any(dest.iterdir()) and not overwrite:
        raise PublishError(
            f"Publish destination already exists and is not empty: {dest}. "
            "Choose a new --label or remove that folder first."
        )

    # Map each source to its flattened PhaseNN/<filename> target, failing on any collision (two
    # distinct sources -> same published path) rather than silently overwriting.
    targets: dict[Path, Path] = {}
    for src in collect_deliverables(output_root):
        target_relative = Path(_phase_tag(src.relative_to(output_root))) / src.name
        if target_relative in targets.values():
            previous = next(
                source for source, target in targets.items() if target == target_relative
            )
            raise PublishError(
                f"Publish name collision: {previous} and {src} both map to {target_relative}"
            )
        targets[src.resolve()] = target_relative

    records = _load_run_phase_records(runs_root, output_root)
    selected = _select_publication_records(output_root, tuple(targets), records)

    if dest.exists() and overwrite:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for src, target_relative in sorted(targets.items(), key=lambda item: item[1].as_posix()):
        target = dest / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() == ".qgz":
            _publish_qgz_flat(src, target)
        else:
            shutil.copy2(src, target)
        copied.append(target)

    skipped = sum(
        1
        for p in output_root.rglob("*")
        if p.is_file() and _is_working_copy(p.relative_to(output_root))
    )

    manifest = latest_run_manifest(runs_root) if runs_root is not None else None
    if manifest is not None and manifest.exists():
        shutil.copy2(manifest, dest / "run_manifest.json")
        copied.append(dest / "run_manifest.json")

    phase_records: list[PublishedPhase] = []
    copied_source_manifests: dict[Path, Path] = {}
    for phase_id, record in sorted(selected.items()):
        source_manifest_relative = (
            Path("source_run_manifests") / record.run_id / "run_manifest.json"
        )
        source_manifest_target = dest / source_manifest_relative
        if record.manifest_path not in copied_source_manifests:
            source_manifest_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(record.manifest_path, source_manifest_target)
            copied_source_manifests[record.manifest_path] = source_manifest_target
            copied.append(source_manifest_target)
        phase_outputs = tuple(
            PublishedOutput(
                path=targets[source].as_posix(),
                sha256=_sha256(dest / targets[source]),
            )
            for source in sorted(
                (
                    source
                    for source in targets
                    if _phase_id_from_relative(source.relative_to(output_root)) == phase_id
                ),
                key=lambda source: targets[source].as_posix(),
            )
        )
        phase_records.append(
            PublishedPhase(
                phase_id=phase_id,
                source_run_id=record.run_id,
                source_run_manifest_path=source_manifest_relative.as_posix(),
                source_run_manifest_sha256=record.manifest_sha256,
                gate_state=record.gate_state,
                gate_provisional=record.gate_provisional,
                human_review_or_qaqc_pending=record.human_review_or_qaqc_pending,
                pending_human_review_or_qaqc_count=record.pending_human_review_or_qaqc_count,
                outputs=phase_outputs,
            )
        )

    phases = tuple(phase_records)
    package_status = publication_status_for(phases)
    git_commit_sha = _git_commit_sha(Path.cwd())
    publication_id = publication_id_for(
        project=project,
        package_version=__version__,
        git_commit_sha=git_commit_sha,
        phases=phases,
        package_status=package_status,
        superseded_publication_id=superseded_publication_id,
    )
    publication_manifest = PublicationManifest(
        manifest_format_version=PUBLICATION_MANIFEST_FORMAT_VERSION,
        project=project,
        package_version=__version__,
        git_commit_sha=git_commit_sha,
        published_at=publication_time,
        publication_id=publication_id,
        included_phase_ids=tuple(phase.phase_id for phase in phases),
        phases=phases,
        package_status=package_status,
        aggregation_notice=AGGREGATION_NOTICE,
        superseded_publication_id=superseded_publication_id,
    )
    publication_manifest_path = dest / "publication_manifest.json"
    publication_manifest_path.write_text(
        publication_manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    copied.append(publication_manifest_path)
    verify_publication_package(dest)
    _write_index(dest, copied, label, publication_manifest)
    return PublishResult(dest=dest, files=copied, skipped_working_copies=skipped)


def load_publication_manifest(package_root: Path) -> PublicationManifest:
    path = Path(package_root) / "publication_manifest.json"
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
        return PublicationManifest.model_validate(data)
    except (OSError, UnicodeError, ValueError, ValidationError) as exc:
        raise PublishError(f"publication manifest is unreadable or invalid: {path}") from exc


def verify_publication_package(package_root: Path) -> PublicationManifest:
    """Re-hash every recorded output and source manifest in a staged package."""

    package_root = Path(package_root).resolve()
    manifest = load_publication_manifest(package_root)
    for phase in manifest.phases:
        source_manifest = package_root / Path(phase.source_run_manifest_path)
        if (
            not source_manifest.is_file()
            or _sha256(source_manifest) != phase.source_run_manifest_sha256
        ):
            raise PublishError(
                f"source run manifest is missing or changed: {phase.source_run_manifest_path}"
            )
        source_data = _load_json_object(source_manifest)
        if source_data.get("run_id") != phase.source_run_id:
            raise PublishError(f"source run identity mismatch for Phase {phase.phase_id}")
        source_phases = source_data.get("phases")
        if not isinstance(source_phases, list):
            raise PublishError(f"source run has no phase records for Phase {phase.phase_id}")
        matching = [
            item
            for item in source_phases
            if isinstance(item, dict) and item.get("phase_id") == phase.phase_id
        ]
        if len(matching) != 1:
            raise PublishError(f"source run phase identity is ambiguous for Phase {phase.phase_id}")
        source_phase = matching[0]
        source_gate = source_phase.get("gate")
        if (
            source_phase.get("status") != "ok"
            or not isinstance(source_gate, dict)
            or source_gate.get("status") != phase.gate_state
            or (source_gate.get("provisional") is True) != phase.gate_provisional
            or (source_phase.get("qaqc_pending") is True) != phase.human_review_or_qaqc_pending
        ):
            raise PublishError(f"source run gate provenance mismatch for Phase {phase.phase_id}")
        for output in phase.outputs:
            path = package_root / Path(output.path)
            if not path.is_file() or _sha256(path) != output.sha256:
                raise PublishError(f"published output is missing or changed: {output.path}")
    return manifest


def _publish_qgz_flat(src: Path, target: Path) -> None:
    """Copy a QGIS project, rewriting layer datasources for the flat publish layout.

    Phase outputs reference their GPKGs relative to the .qgz inside the phase's
    subfolder tree (e.g. ``../05_KMZ_KML_to_GPKG/x.gpkg|layername=y``); publishing
    flattens every deliverable of a phase into one ``PhaseNN/`` folder, so each
    datasource is rewritten to ``./<basename>`` — the published project then opens
    with its layers resolving beside it.
    """
    import zipfile
    from xml.etree import ElementTree as ET

    def flatten(source: str) -> str:
        path_part, sep, layer_part = source.partition("|")
        return f"./{Path(path_part).name}{sep}{layer_part}"

    with zipfile.ZipFile(src) as zf:
        qgs_name = next(n for n in zf.namelist() if n.endswith(".qgs"))
        root = ET.fromstring(zf.read(qgs_name))
    for node in root.iter("layer-tree-layer"):
        if node.get("source"):
            node.set("source", flatten(node.get("source", "")))
    for ds in root.iter("datasource"):
        if ds.text:
            ds.text = flatten(ds.text)
    ET.indent(root)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(qgs_name, ET.tostring(root, encoding="unicode", xml_declaration=True))


def _write_index(
    dest: Path,
    copied: list[Path],
    label: str,
    manifest: PublicationManifest,
) -> Path:
    lines = [
        f"# Deliverable publication package ({label})",
        "",
        "Published deliverables (GIS layers, COG rasters, registers, logs, reports). Raw working",
        "copies are excluded — those are duplicates of the read-only Drive archive.",
        "",
        f"**Package status:** {manifest.package_status}",
        "",
        "Machine-readable package provenance and output hashes are recorded in",
        "`publication_manifest.json`. The root `run_manifest.json`, when present, is retained only",
        "for compatibility and must not be interpreted as provenance for the complete package.",
        "",
        manifest.aggregation_notice,
        "",
    ]
    parts = []
    for phase in manifest.phases:
        tag = f"{phase.phase_id}={phase.gate_state} from run {phase.source_run_id}"
        if phase.gate_provisional:
            tag += " (provisional)"
        if phase.human_review_or_qaqc_pending:
            tag += " (human review / QA/QC pending)"
        parts.append(tag)
    lines.append(f"**Source phase gates:** {', '.join(parts)}")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for p in copied:
        rel = p.relative_to(dest).as_posix()
        size_kb = p.stat().st_size / 1024
        lines.append(f"- `{rel}` ({size_kb:.1f} KB)")
    lines.append("")
    index = dest / "INDEX.md"
    index.write_text("\n".join(lines), encoding="utf-8")
    return index


# --------------------------------------------------------------------------- #
# raw-archive backup (a frozen, checksum-verified copy of the complete raw set)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RawBackupResult:
    dest: Path
    files: int
    verified: int
    missing: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def backup_raw_archive(
    raw_root: Path,
    checksum_register: Path,
    publish_root: Path,
    label: str,
    *,
    integrity_files: Sequence[Path] = (),
    overwrite: bool = False,
) -> RawBackupResult:
    """Copy the *complete* raw archive to a frozen, checksum-verified backup under ``publish_root``.

    Creates ``publish_root/Raw_Archive_Backup_<label>/`` with the full raw tree under
    ``0_Raw_Data/``, the Phase-00 checksum register + any ``integrity_files`` at the root, and a
    README. Every row of the checksum register is re-hashed against the copied file; a missing or
    mismatched file raises :class:`PublishError` (the README is still written for diagnosis).

    Raw is read-only — this only *reads* ``raw_root``. Unlike :func:`publish` (which excludes raw
    working copies), this deliberately backs up the raw data so teammates have an immutable,
    verifiable copy separate from the working source. Intended one-time / on-change, not per run.
    """
    raw_root = Path(raw_root)
    publish_root = Path(publish_root)
    checksum_register = Path(checksum_register)
    if not raw_root.exists():
        raise PublishError(f"raw_root does not exist: {raw_root}")
    if not checksum_register.exists():
        raise PublishError(f"checksum register not found: {checksum_register} (run Phase 00 first)")
    dest = publish_root / f"Raw_Archive_Backup_{label}"
    if dest.exists() and any(dest.iterdir()) and not overwrite:
        raise PublishError(
            f"{dest} already exists and is non-empty; pass overwrite=True or use a new label"
        )
    data_dir = dest / "0_Raw_Data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # copy the complete raw tree (skip Windows desktop.ini folder-config junk Drive re-creates)
    files = 0
    for f in sorted(raw_root.rglob("*")):
        if not f.is_file() or f.name.lower() == "desktop.ini":
            continue
        target = data_dir / f.relative_to(raw_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        files += 1

    # copy the integrity evidence (register + inventory/log/readme) to the backup root
    shutil.copy2(checksum_register, dest / checksum_register.name)
    for extra in integrity_files:
        extra = Path(extra)
        if extra.exists():
            shutil.copy2(extra, dest / extra.name)

    # verify every register row against the copied file
    verified = 0
    missing: list[str] = []
    mismatched: list[str] = []
    with open(checksum_register, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rel = row["relative_path"].replace("/", os.sep)
            p = data_dir / rel
            if not p.exists():
                missing.append(row["relative_path"])
            elif _sha256(p) == row["sha256"]:
                verified += 1
            else:
                mismatched.append(row["relative_path"])

    _write_raw_backup_readme(dest, label, files, verified, checksum_register.name)
    if missing or mismatched:
        raise PublishError(
            f"raw backup verification failed: {len(missing)} missing, "
            f"{len(mismatched)} mismatched vs the checksum register (dest={dest})"
        )
    return RawBackupResult(
        dest=dest, files=files, verified=verified, missing=missing, mismatched=mismatched
    )


def _write_raw_backup_readme(
    dest: Path, label: str, files: int, verified: int, register_name: str
) -> Path:
    lines = [
        f"# Raw Archive Backup — {label}",
        "",
        "**Frozen, checksum-verified backup of the complete raw exploration data archive.**",
        "Do not edit anything in this folder — it exists so the working source can be protected",
        "and, if it is ever altered, restored/verified against this snapshot.",
        "",
        "## Contents",
        f"- `0_Raw_Data/` — complete raw archive ({files} files, full folder structure).",
        f"- `{register_name}` — SHA-256 integrity baseline (the source of truth for verification).",
        "- Phase-00 inventory / integrity log / source readme (where provided).",
        "",
        "## Verification",
        f"All {verified} checksum-register rows were re-hashed against the copied files and "
        "matched byte-for-byte at backup time. To re-verify a file, compare its SHA-256 against "
        f"the `sha256` column in `{register_name}` (`Get-FileHash -Algorithm SHA256` / `sha256sum`).",
        "",
        "## Notes",
        "- One-time, versioned backup — raw data does not change, so it is not re-uploaded per run.",
        "  If the raw archive is ever legitimately updated, create a new label rather than overwriting.",
        "- Raw inputs are read-only source evidence; remote-sensing / pXRF / drone data are *support*",
        "  evidence, never ore proof.",
    ]
    readme = dest / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
    return readme
