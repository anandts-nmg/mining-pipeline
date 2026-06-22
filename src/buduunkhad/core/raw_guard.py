"""Raw-data read-only enforcement and integrity verification.

Invariant #1: raw is read-only. Nothing in the pipeline may open a path inside the
raw archive in a write mode, and at the start of every real run we re-verify that
the raw files' SHA-256 checksums are unchanged from the archived register.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

_WRITE_TOKENS = ("w", "a", "x", "+")
_CHUNK = 1024 * 1024  # 1 MiB


class RawReadOnlyError(RuntimeError):
    """Raised on any attempt to open/modify a raw archive path for writing."""


class RawIntegrityError(RuntimeError):
    """Raised when a raw file's checksum no longer matches the recorded value."""


def _is_within(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def assert_not_raw_write(path: Path, raw_root: Path) -> None:
    """Refuse to designate a write target inside the raw archive."""
    if _is_within(path, raw_root):
        raise RawReadOnlyError(
            f"Refusing to write inside the raw archive: {path}\n"
            f"Raw data is read-only; write working copies under the output root instead."
        )


def open_raw(path: Path, mode: str = "rb", raw_root: Path | None = None, **kwargs: Any) -> IO[Any]:
    """Open a raw file, but only ever for reading.

    Any write/append/exclusive/update mode raises :class:`RawReadOnlyError`. If
    ``raw_root`` is given, the path is also asserted to live inside it.
    """
    if any(tok in mode for tok in _WRITE_TOKENS):
        raise RawReadOnlyError(f"Refusing to open raw file in write mode {mode!r}: {path}")
    if raw_root is not None and not _is_within(path, raw_root):
        raise RawReadOnlyError(f"{path} is not inside the raw archive {raw_root}")
    return open(path, mode, **kwargs)  # noqa: SIM115 - caller manages the handle


def compute_sha256(path: Path) -> str:
    """Streaming SHA-256 of a file (hex digest)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class ChecksumRecord:
    """One row of the SHA-256 checksum register."""

    filename: str
    relative_path: str
    sha256: str
    size_bytes: int


def iter_files(root: Path) -> Iterator[Path]:
    """Yield every file under ``root`` (recursively), sorted for determinism."""
    yield from sorted(p for p in Path(root).rglob("*") if p.is_file())


def build_checksum_records(raw_root: Path) -> list[ChecksumRecord]:
    """Compute checksum records for every file currently in the raw archive."""
    raw_root = Path(raw_root)
    records: list[ChecksumRecord] = []
    for p in iter_files(raw_root):
        records.append(
            ChecksumRecord(
                filename=p.name,
                relative_path=p.relative_to(raw_root).as_posix(),
                sha256=compute_sha256(p),
                size_bytes=p.stat().st_size,
            )
        )
    return records


@dataclass(frozen=True)
class IntegrityResult:
    """Outcome of verifying raw files against a previously-recorded checksum set."""

    ok: bool
    mismatched: list[str]
    missing: list[str]
    new: list[str]

    def summary(self) -> str:
        if self.ok:
            return "raw integrity OK"
        bits = []
        if self.mismatched:
            bits.append(f"{len(self.mismatched)} changed")
        if self.missing:
            bits.append(f"{len(self.missing)} missing")
        if self.new:
            bits.append(f"{len(self.new)} new/unregistered")
        return "raw integrity FAILED: " + ", ".join(bits)


def verify_against(raw_root: Path, expected: dict[str, str]) -> IntegrityResult:
    """Compare current raw checksums against ``expected`` (relative_path -> sha256).

    ``new`` files (present now but not in ``expected``) are reported but do not by
    themselves fail integrity - only changed or missing recorded files do.
    """
    current = {r.relative_path: r.sha256 for r in build_checksum_records(raw_root)}
    mismatched = sorted(k for k, v in expected.items() if k in current and current[k] != v)
    missing = sorted(k for k in expected if k not in current)
    new = sorted(k for k in current if k not in expected)
    ok = not mismatched and not missing
    return IntegrityResult(ok=ok, mismatched=mismatched, missing=missing, new=new)
