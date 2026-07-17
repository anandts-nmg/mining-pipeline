"""Portable byte identities for publishable phase outputs recorded by a run."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

DELIVERABLE_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".gpkg", ".qgz", ".xlsx", ".csv", ".docx", ".pdf", ".md", ".json", ".tif"}
)

WORKING_COPY_DIRS: Final[frozenset[str]] = frozenset(
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
        "02_Band_Extraction",
        "03_Project_UTM47",
        "08_Supplementary_Source_Documents",
    }
)


class ArtifactSealError(RuntimeError):
    """Raised when a phase output cannot be safely sealed into a run manifest."""


def canonical_relative_path(value: str) -> str:
    """Validate a non-empty canonical POSIX path with no traversal."""

    if not value or "\\" in value:
        raise ValueError("artifact paths must be non-empty POSIX relative paths")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("artifact paths must stay within their declared root")
    if path.as_posix() != value:
        raise ValueError("artifact paths must use canonical POSIX form")
    return value


class RunOutputArtifact(BaseModel):
    """One completed publishable phase output sealed by byte hash and size."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

    _path_is_relative = field_validator("path")(canonical_relative_path)


def sha256_file(path: Path) -> str:
    """Hash a file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_working_copy(relative: Path) -> bool:
    return any(part in WORKING_COPY_DIRS for part in relative.parts)


def is_publishable_relative(relative: Path) -> bool:
    return not is_working_copy(relative) and relative.suffix.lower() in DELIVERABLE_SUFFIXES


def has_symlink_component(path: Path) -> bool:
    """Return whether any existing component from the filesystem anchor is a symlink."""

    absolute = Path(path).absolute()
    for component in (absolute, *absolute.parents):
        if component == Path(component.anchor):
            break
        if component.is_symlink():
            return True
    return False


def require_regular_file_under(root: Path, path: Path, *, description: str) -> Path:
    """Return a resolved regular file only when its lexical path is link-free and contained."""

    root_path = Path(root).absolute()
    candidate = Path(path).absolute()
    if has_symlink_component(root_path) or has_symlink_component(candidate):
        raise ArtifactSealError(f"{description} must not use a symlink: {path}")
    resolved_root = root_path.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ArtifactSealError(f"{description} escapes its expected root: {path}") from exc
    if not resolved_candidate.is_file():
        raise ArtifactSealError(f"{description} is missing or is not a regular file: {path}")
    return resolved_candidate


def seal_output_artifacts(
    output_root: Path, outputs: Iterable[Path]
) -> tuple[RunOutputArtifact, ...]:
    """Seal each publishable output after successful phase completion."""

    root = Path(output_root).absolute()
    artifacts: list[RunOutputArtifact] = []
    seen: set[str] = set()
    for output in outputs:
        candidate = require_regular_file_under(root, Path(output), description="phase output")
        relative = candidate.relative_to(root.resolve())
        if not is_publishable_relative(relative):
            continue
        portable = relative.as_posix()
        if portable in seen:
            raise ArtifactSealError(f"phase output path is duplicated: {portable}")
        seen.add(portable)
        artifacts.append(
            RunOutputArtifact(
                path=portable,
                sha256=sha256_file(candidate),
                size_bytes=candidate.stat().st_size,
            )
        )
    return tuple(sorted(artifacts, key=lambda artifact: artifact.path))
