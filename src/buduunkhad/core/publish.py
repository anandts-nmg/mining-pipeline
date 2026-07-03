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
