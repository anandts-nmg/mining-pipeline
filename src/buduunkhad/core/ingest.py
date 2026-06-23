"""Manifest-aware raw-data ingest.

Per ADR 0001 the canonical raw set is pinned by Drive file ID in
``config/raw_manifest.csv``, but the running pipeline reads from a **local**
``raw_root`` (a copy/sync of the canonical ``0. Raw Data`` archive, or any folder
whose file *basenames* match the register). This module:

- loads the manifest (``register filename -> ManifestEntry``),
- resolves a register record to its local path (by basename, recursive, so the
  archive's theme-folder layout doesn't matter),
- applies a tiered copy/reference policy (small files copy; large rasters are
  referenced) by manifest size, and
- exposes provenance (Drive file ID / theme / size / status) for the inventory.

Remote fetch for ``drive``/``gcs`` modes is an *injected* callable so no
credentials live in the pipeline; ``local`` mode (the default) needs none.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from buduunkhad.config import InputRecord
from buduunkhad.core import raw_guard

#: Files at/above this size are *referenced* in place rather than copied.
DEFAULT_SIZE_THRESHOLD_MB = 50.0


@dataclass(frozen=True)
class ManifestEntry:
    """One row of ``config/raw_manifest.csv`` (a canonical raw input)."""

    filename: str
    drive_file_id: str
    size_bytes: int
    theme_folder: str
    status: str
    no: int | None = None

    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / (1024 * 1024), 4)

    @property
    def present_in_archive(self) -> bool:
        return self.status == "matched"


def load_manifest(path: Path | str) -> dict[str, ManifestEntry]:
    """Load the raw manifest, keyed by filename."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raw manifest not found: {path}")
    out: dict[str, ManifestEntry] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            filename = (row.get("filename") or "").strip()
            if not filename:
                continue
            no_raw = (row.get("no") or "").strip()
            size_raw = (row.get("drive_size_bytes") or "").strip()
            out[filename] = ManifestEntry(
                filename=filename,
                drive_file_id=(row.get("drive_file_id") or "").strip(),
                size_bytes=int(size_raw) if size_raw.isdigit() else 0,
                theme_folder=(row.get("drive_theme_folder") or "").strip(),
                status=(row.get("match_status") or "").strip(),
                no=int(no_raw) if no_raw.isdigit() else None,
            )
    return out


def acknowledged_absent(manifest: dict[str, ManifestEntry]) -> set[str]:
    """Filenames the manifest records as absent from the canonical archive.

    These are *documented* gaps (e.g. the KOMPSAT EULA): a real run records them
    in the data-gap register rather than hard-failing, whereas an input that is
    unexpectedly missing (or not in the manifest at all) still stops the run.
    """
    return {fn for fn, e in manifest.items() if e.status and not e.present_in_archive}


#: ``(entry, dest) -> written_path`` — fetches one file for drive/gcs modes.
Fetcher = Callable[[ManifestEntry, Path], Path]


class RawSource:
    """Resolve register records to local paths, with a tiered materialisation policy."""

    def __init__(
        self,
        raw_root: Path | str,
        manifest: dict[str, ManifestEntry] | None = None,
        *,
        mode: str = "local",
        size_threshold_mb: float = DEFAULT_SIZE_THRESHOLD_MB,
        fetcher: Fetcher | None = None,
    ) -> None:
        self.raw_root = Path(raw_root)
        self.manifest = manifest or {}
        self.mode = mode
        self.size_threshold_mb = size_threshold_mb
        self.fetcher = fetcher
        self._index: dict[str, Path] | None = None

    # ---- local discovery -------------------------------------------------- #

    def _index_by_name(self) -> dict[str, Path]:
        if self._index is None:
            self._index = (
                {p.name: p for p in raw_guard.iter_files(self.raw_root)}
                if self.raw_root.exists()
                else {}
            )
        return self._index

    def local_path(self, record: InputRecord) -> Path | None:
        """Local path for ``record`` (matched by basename), or ``None`` if absent."""
        return self._index_by_name().get(record.filename)

    # ---- manifest helpers ------------------------------------------------- #

    def entry(self, record: InputRecord) -> ManifestEntry | None:
        return self.manifest.get(record.filename)

    def is_large(self, record: InputRecord) -> bool:
        entry = self.entry(record)
        return bool(entry and entry.size_mb >= self.size_threshold_mb)

    def should_copy(self, record: InputRecord) -> bool:
        """Copy small files + sidecars; reference large rasters in place."""
        if record.is_sidecar:
            return True
        return not self.is_large(record)

    def provenance(self, record: InputRecord) -> dict[str, object]:
        """Inventory provenance columns for ``record``."""
        entry = self.entry(record)
        return {
            "drive_file_id": entry.drive_file_id if entry else "",
            "drive_theme_folder": entry.theme_folder if entry else "",
            "manifest_size_bytes": entry.size_bytes if entry else "",
            "manifest_status": entry.status if entry else "not-in-manifest",
        }

    # ---- resolution ------------------------------------------------------- #

    def resolve(self, record: InputRecord) -> Path | None:
        """Return a local path, fetching on demand for non-local modes.

        ``local`` mode never fetches (returns ``None`` if absent). For ``drive`` /
        ``gcs`` a ``fetcher`` must be supplied, else a clear error is raised.
        """
        path = self.local_path(record)
        if path is not None:
            return path
        if self.mode == "local":
            return None
        entry = self.entry(record)
        if entry is None or not entry.drive_file_id:
            return None
        if self.fetcher is None:
            raise NotImplementedError(
                f"{self.mode!r} ingest needs a fetcher (e.g. rclone/gsutil). "
                f"Sync the canonical '0. Raw Data' archive locally and point "
                f"paths.raw_root at it, or inject a fetcher."
            )
        dest = self.raw_root / entry.theme_folder / entry.filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        written = self.fetcher(entry, dest)
        self._index = None  # invalidate cache; a new file landed
        return Path(written)


@dataclass(frozen=True)
class Coverage:
    """Result of cross-checking ``raw_root`` against the manifest."""

    present: list[str]
    missing: list[str]
    size_mismatch: list[tuple[str, int, int]]  # (name, manifest_size, local_size)
    untracked_local: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing and not self.size_mismatch


def coverage(
    records: Iterable[InputRecord],
    manifest: dict[str, ManifestEntry],
    raw_root: Path | str,
) -> Coverage:
    """Compare the local ``raw_root`` against the manifest (presence + size)."""
    source = RawSource(raw_root, manifest)
    index = source._index_by_name()
    present: list[str] = []
    missing: list[str] = []
    mismatch: list[tuple[str, int, int]] = []
    for rec in records:
        local = index.get(rec.filename)
        if local is None:
            missing.append(rec.filename)
            continue
        present.append(rec.filename)
        entry = manifest.get(rec.filename)
        if entry and entry.size_bytes:
            actual = local.stat().st_size
            if actual != entry.size_bytes:
                mismatch.append((rec.filename, entry.size_bytes, actual))
    wanted = {r.filename for r in records}
    untracked = sorted(n for n in index if n not in wanted)
    return Coverage(present, missing, mismatch, untracked)
