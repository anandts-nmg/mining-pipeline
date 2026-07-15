"""Immutable snapshot inventory creation and verification."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from buduunkhad.ai.contracts import require_aware_datetime
from buduunkhad.ai.fingerprint import sha256_file
from buduunkhad.geospatial_ai.path_safety import PathSafetyError, StorageRoots

SourceRootId = Literal["raw", "snapshot"]
_SIDECARS = (".tfw", ".jgw", ".pgw", ".wld", ".aux.xml", ".ovr", ".rpc", ".eph")


class SnapshotEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    relative_path: str
    size: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bundle_parent: str | None = None
    sidecar_kind: str | None = None


class SnapshotManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    format_version: Literal["1.0.0"] = "1.0.0"
    source_root_id: SourceRootId
    created_at: datetime
    entries: tuple[SnapshotEntry, ...]

    @field_validator("created_at")
    @classmethod
    def _aware_creation_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")


class SnapshotVerification(BaseModel):
    model_config = ConfigDict(frozen=True)

    valid: bool
    missing: tuple[str, ...]
    changed: tuple[str, ...]
    unexpected: tuple[str, ...]


def create_snapshot_manifest(
    source_root: Path,
    manifest_path: Path,
    *,
    source_root_id: SourceRootId,
    roots: StorageRoots,
    run_id: str,
    now: datetime | None = None,
) -> SnapshotManifest:
    source = _authorized_source_root(source_root, source_root_id=source_root_id, roots=roots)
    destination = roots.assert_writable(manifest_path, run_id=run_id)
    if destination.exists():
        raise PathSafetyError("snapshot manifests are immutable and cannot be overwritten")
    files = _inventory_files(source)
    relatives = {path.relative_to(source).as_posix(): path for path in files}
    entries = tuple(_entry(path, source=source, relatives=relatives) for path in files)
    manifest = SnapshotManifest(
        source_root_id=source_root_id,
        created_at=now or datetime.now(UTC),
        entries=entries,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(manifest.model_dump_json(indent=2), encoding="utf-8", newline="\n")
    return manifest


def verify_snapshot_manifest(
    source_root: Path,
    manifest_path: Path,
    *,
    source_root_id: SourceRootId,
    roots: StorageRoots,
) -> SnapshotVerification:
    source = _authorized_source_root(source_root, source_root_id=source_root_id, roots=roots)
    try:
        manifest = SnapshotManifest.model_validate(
            json.loads(
                manifest_path.read_text(encoding="utf-8"),
                object_pairs_hook=_unique_object,
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise PathSafetyError("snapshot manifest is unreadable or invalid") from exc
    if manifest.source_root_id != source_root_id:
        raise PathSafetyError("snapshot manifest source-root identity mismatch")
    expected = {entry.relative_path: entry for entry in manifest.entries}
    actual_paths = _inventory_files(source)
    actual = {path.relative_to(source).as_posix(): path for path in actual_paths}
    missing = tuple(sorted(set(expected) - set(actual)))
    unexpected = tuple(sorted(set(actual) - set(expected)))
    changed = tuple(
        sorted(
            relative
            for relative in set(expected) & set(actual)
            if actual[relative].stat().st_size != expected[relative].size
            or sha256_file(actual[relative]) != expected[relative].sha256
        )
    )
    return SnapshotVerification(
        valid=not missing and not changed and not unexpected,
        missing=missing,
        changed=changed,
        unexpected=unexpected,
    )


def _authorized_source_root(
    source_root: Path,
    *,
    source_root_id: SourceRootId,
    roots: StorageRoots,
) -> Path:
    if source_root_id not in ("raw", "snapshot"):
        raise PathSafetyError(
            "snapshot creation and verification are limited to raw or immutable snapshot roots; "
            "workflow documents must not be bulk-read"
        )
    source = source_root.expanduser().resolve(strict=True)
    expected = {
        "raw": roots.raw_root,
        "snapshot": roots.snapshot_root,
    }[source_root_id]
    if expected is None or source != expected:
        raise PathSafetyError("snapshot source root does not match its configured identity")
    return source


def _entry(path: Path, *, source: Path, relatives: dict[str, Path]) -> SnapshotEntry:
    relative = path.relative_to(source).as_posix()
    lower = relative.casefold()
    suffix = next((value for value in _SIDECARS if lower.endswith(value)), None)
    parent = _bundle_parent(relative, relatives, suffix) if suffix else None
    return SnapshotEntry(
        relative_path=relative,
        size=path.stat().st_size,
        sha256=sha256_file(path),
        bundle_parent=parent,
        sidecar_kind=suffix,
    )


def _bundle_parent(relative: str, relatives: dict[str, Path], suffix: str) -> str | None:
    base = relative[: -len(suffix)]
    candidates = (base, base + ".tif", base + ".tiff", base + ".jpg", base + ".png")
    return next((candidate for candidate in candidates if candidate in relatives), None)


def _path_key(path: Path) -> str:
    return path.as_posix().casefold()


def _inventory_files(source: Path) -> tuple[Path, ...]:
    entries = tuple(sorted(source.rglob("*"), key=_path_key))
    symlinks = tuple(path.relative_to(source).as_posix() for path in entries if path.is_symlink())
    if symlinks:
        raise PathSafetyError(f"snapshot roots cannot contain symlinks: {symlinks[0]}")
    return tuple(path for path in entries if path.is_file())


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate snapshot-manifest key: {key}")
        value[key] = item
    return value
