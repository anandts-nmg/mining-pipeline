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
import shutil
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

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


def publish(
    output_root: Path,
    publish_root: Path,
    label: str,
    *,
    runs_root: Path | None = None,
    overwrite: bool = False,
) -> PublishResult:
    """Copy deliverables into ``publish_root/BuduunKhad_..._<label>/`` with an INDEX.md.

    Raises :class:`PublishError` if the label dir already exists and is non-empty (unless
    ``overwrite=True``) or if two source files would flatten to the same published path — both
    would otherwise silently overwrite, so we fail loudly per the repo's philosophy.
    """
    output_root = Path(output_root)
    dest = Path(publish_root) / f"Buduunkhad_Deliverables_{label}"
    if dest.exists() and any(dest.iterdir()) and not overwrite:
        raise PublishError(
            f"Publish destination already exists and is not empty: {dest}. "
            "Choose a new --label or remove that folder first."
        )
    dest.mkdir(parents=True, exist_ok=True)

    # Map each source to its flattened PhaseNN/<filename> target, failing on any collision (two
    # distinct sources -> same published path) rather than silently overwriting.
    targets: dict[Path, Path] = {}
    for src in collect_deliverables(output_root):
        target = dest / _phase_tag(src.relative_to(output_root)) / src.name
        if target in targets:
            raise PublishError(
                f"Publish name collision: {targets[target]} and {src} both map to {target}"
            )
        targets[target] = src

    copied: list[Path] = []
    for target, src in targets.items():
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

    gates = latest_gate_per_phase(runs_root) if runs_root is not None else {}
    _write_index(dest, output_root, copied, label, gates)
    return PublishResult(dest=dest, files=copied, skipped_working_copies=skipped)


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
    output_root: Path,
    copied: list[Path],
    label: str,
    gates: dict[str, dict[str, object]],
) -> Path:
    lines = [
        f"# Buduunkhad XV-023222 — Deliverables ({label})",
        "",
        "Published deliverables (GIS layers, COG rasters, registers, logs, reports). Raw working",
        "copies are excluded — those are duplicates of the read-only Drive archive.",
        "",
    ]
    if gates:
        parts = []
        for pid in sorted(gates):
            g = gates[pid]
            tag = f"{pid}={g['status']}"
            if g.get("provisional"):
                tag += " (provisional)"
            parts.append(tag)
        lines.append(f"**Gates (most recent real run per phase):** {', '.join(parts)}")
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
