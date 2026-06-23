"""Sidecar detection and bundle copying.

Invariant #3: sidecar metadata travels with its parent raster/image and is never
orphaned. A "bundle" is a parent file plus every sidecar that shares its stem
(``.tfw``, ``.aux.xml``, ``.ovr`` ...) in the same directory.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

# Sidecar suffixes recognised by the methodology. Order matters for matching the
# longest (compound) suffix first.
SIDECAR_SUFFIXES: tuple[str, ...] = (
    ".tif.aux.xml",
    ".tif.ovr",
    ".aux.xml",
    ".ovr",
    ".tfw",
    ".jgw",
    ".pgw",
    ".wld",
    ".rpc",
    ".eph",
    ".rrd",
    ".prj",
    ".txt",
)

# World-file suffix -> the image extension it belongs to.
_WORLD_FILE_PARENT_EXT = {".tfw": ".tif", ".jgw": ".jpg", ".pgw": ".png"}


def is_sidecar(path: str | Path) -> bool:
    """True if ``path``'s name ends with a known sidecar suffix."""
    name = Path(path).name.lower()
    return any(name.endswith(s) for s in SIDECAR_SUFFIXES)


def sidecar_stem(path: str | Path) -> str:
    """The shared stem a sidecar groups under.

    ``X.tif.aux.xml -> 'X'``, ``X.tfw -> 'X'``, ``X.rpc -> 'X'``. For non-sidecars,
    returns the plain stem.
    """
    name = Path(path).name
    low = name.lower()
    for suf in SIDECAR_SUFFIXES:
        if low.endswith(suf):
            base = name[: -len(suf)]
            # ``.aux.xml`` / ``.ovr`` sit on top of the full raster name (X.tif.ovr),
            # so strip a trailing image extension too.
            return Path(base).stem if "." in base else base
    return Path(name).stem


def parent_filename(sidecar: str | Path) -> str | None:
    """Best-effort parent filename for a sidecar, or ``None`` if not derivable.

    World files map to a specific image extension; ``.aux.xml`` / ``.ovr`` strip
    their own suffix to reveal the parent (e.g. ``X.tif.ovr`` -> ``X.tif``).
    """
    name = Path(sidecar).name
    low = name.lower()
    _, dot, ext = name.rpartition(".")
    ext = "." + ext.lower() if dot else ""
    if ext in _WORLD_FILE_PARENT_EXT:
        return name[: -len(ext)] + _WORLD_FILE_PARENT_EXT[ext]
    if low.endswith(".aux.xml"):
        return name[: -len(".aux.xml")]
    if low.endswith(".ovr"):
        return name[: -len(".ovr")]
    return None


def find_sidecars(parent: Path) -> list[Path]:
    """Return sibling sidecar files that belong to ``parent`` (same dir, same stem)."""
    parent = Path(parent)
    folder = parent.parent
    if not folder.exists():
        return []
    stem = parent.stem  # e.g. "X" for "X.tif"
    full = parent.name  # e.g. "X.tif"
    found: list[Path] = []
    for sib in sorted(folder.iterdir()):
        if sib == parent or not sib.is_file() or not is_sidecar(sib):
            continue
        sib_name = sib.name
        # Match either "<full>.<sidecarext>" (X.tif.ovr) or "<stem>.<sidecarext>" (X.tfw).
        if sib_name.startswith(full + ".") or Path(sib_name).stem == stem:
            found.append(sib)
    return found


@dataclass(frozen=True)
class BundleCopy:
    """Result of copying a parent + sidecars to a destination directory."""

    parent: Path
    sidecars: list[Path]

    @property
    def all_files(self) -> list[Path]:
        return [self.parent, *self.sidecars]


def copy_bundle(src_parent: Path, dst_dir: Path, *, overwrite: bool = False) -> BundleCopy:
    """Copy ``src_parent`` and all its sidecars into ``dst_dir`` as a bundle.

    Returns the destination paths. Never modifies the source. Raises if a target
    exists and ``overwrite`` is False.
    """
    src_parent = Path(src_parent)
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    members = [src_parent, *find_sidecars(src_parent)]
    copied: list[Path] = []
    for member in members:
        target = dst_dir / member.name
        if target.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing working copy: {target}")
        shutil.copy2(member, target)
        copied.append(target)
    return BundleCopy(parent=copied[0], sidecars=copied[1:])
