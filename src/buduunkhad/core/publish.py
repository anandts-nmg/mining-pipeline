"""Publish curated deliverables to a publish root (e.g. a Google-Drive folder).

Per ADR 0001, generated outputs are build artifacts. This copies only the small,
high-value **deliverables** — GIS layers, registers, logs, reports — into a
*versioned* subfolder under ``publish_root`` (typically a Drive-for-Desktop folder
so teammates can see them once shared). The bulky **raw working copies** (rasters
and scans copied from the read-only archive) are deliberately excluded so we never
re-upload duplicates of data that already lives in the Drive.
"""

from __future__ import annotations

import json
import shutil
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
    }
)


@dataclass(frozen=True)
class PublishResult:
    dest: Path
    files: list[Path] = field(default_factory=list)
    skipped_working_copies: int = 0


def _is_working_copy(rel: Path) -> bool:
    return any(part in WORKING_COPY_DIRS for part in rel.parts)


def _phase_tag(rel: Path) -> str:
    """Shallow phase grouping for the published package (keeps paths short, reader-friendly)."""
    top = rel.parts[0] if rel.parts else ""
    if top.startswith("00_"):
        return "Phase00"
    if top.startswith("01_"):
        return "Phase01"
    if top.startswith("02_"):
        return "Phase02"
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


def publish(
    output_root: Path,
    publish_root: Path,
    label: str,
    *,
    runs_root: Path | None = None,
) -> PublishResult:
    """Copy deliverables into ``publish_root/BuduunKhad_..._<label>/`` with an INDEX.md."""
    output_root = Path(output_root)
    dest = Path(publish_root) / f"Buduunkhad_Deliverables_{label}"
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for src in collect_deliverables(output_root):
        # flatten into PhaseNN/<filename> — shallow, reader-friendly, MAX_PATH-safe
        target = dest / _phase_tag(src.relative_to(output_root)) / src.name
        target.parent.mkdir(parents=True, exist_ok=True)
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

    _write_index(dest, output_root, copied, label, manifest)
    return PublishResult(dest=dest, files=copied, skipped_working_copies=skipped)


def _write_index(
    dest: Path, output_root: Path, copied: list[Path], label: str, manifest: Path | None
) -> Path:
    lines = [
        f"# Buduunkhad XV-023222 — Deliverables ({label})",
        "",
        "Published deliverables (GIS layers, COG rasters, registers, logs, reports). Raw working",
        "copies are excluded — those are duplicates of the read-only Drive archive.",
        "",
    ]
    if manifest is not None and manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            lines.append(f"**Run:** {data.get('run_id', '?')}  ")
            gates = ", ".join(
                f"{p['phase_id']}={p.get('gate', {}).get('status', '?')}"
                for p in data.get("phases", [])
            )
            lines.append(f"**Gates:** {gates}")
            lines.append("")
        except (ValueError, KeyError):  # pragma: no cover - manifest shape guard
            pass
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
