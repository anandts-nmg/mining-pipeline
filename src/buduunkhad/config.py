"""Typed configuration and input-register loading.

Everything the pipeline needs to know that is *not* derivable from the data lives
in ``config/project.yaml`` (constants/paths) and ``config/input_register.csv`` (the
79 raw inputs). Both are validated here on load so we fail early and clearly.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Per-machine path overrides (so a local Drive/synced path is never committed).
RAW_ROOT_ENV = "BUDUUNKHAD_RAW_ROOT"
OUTPUT_ROOT_ENV = "BUDUUNKHAD_OUTPUT_ROOT"

# --------------------------------------------------------------------------- #
# Register model
# --------------------------------------------------------------------------- #


class InputRecord(BaseModel):
    """One of the 79 raw input files."""

    model_config = ConfigDict(frozen=True)

    no: int = Field(..., ge=1)
    evidence_group: str
    filename: str
    file_type: str
    primary_phase: str
    methodology_action: str = ""
    is_sidecar: bool = False
    parent_file: str = ""

    @field_validator("primary_phase", mode="before")
    @classmethod
    def _normalise_phase(cls, v: object) -> str:
        # Accept "1" / "01" / 1 and normalise to a two-character phase id.
        s = str(v).strip()
        return s.zfill(2) if s.isdigit() else s


# --------------------------------------------------------------------------- #
# Project config models
# --------------------------------------------------------------------------- #


class ProjectMeta(BaseModel):
    name: str
    project_code: str
    license_code: str
    data_prefix_code: str


class CRSConfig(BaseModel):
    target_epsg: int
    target_name: str
    source_geographic_epsg: int = 4326

    @property
    def target_authority(self) -> str:
        return f"EPSG:{self.target_epsg}"


class PathsConfig(BaseModel):
    raw_root: Path
    output_root: Path
    runs_root: Path


class RegisterConfig(BaseModel):
    path: Path


class RawManifestConfig(BaseModel):
    """Optional manifest pinning each raw input to its canonical Drive file ID."""

    path: Path


class BoundaryConfig(BaseModel):
    input_no: int = 8
    buffers_m: list[int] = Field(default_factory=lambda: [500, 1000, 5000, 10000, 20000])


class EvidenceGroup(BaseModel):
    group_no: int
    name: str
    count: int


class GpkgLayer(BaseModel):
    name: str
    geometry: str  # "Point" | "LineString" | "Polygon" | "None"

    @property
    def is_spatial(self) -> bool:
        return self.geometry.lower() not in ("none", "")


class VersioningConfig(BaseModel):
    default_version: int = 1
    draft_suffix: str = "_DRAFT"


class ProjectConfig(BaseModel):
    """Fully-validated project configuration.

    ``config_dir`` is the directory the YAML was loaded from; relative paths in the
    config resolve against ``base_dir`` (the repo root, parent of ``config/``).
    """

    project: ProjectMeta
    crs: CRSConfig
    paths: PathsConfig
    input_register: RegisterConfig
    raw_manifest: RawManifestConfig | None = None
    boundary: BoundaryConfig
    evidence_groups: list[EvidenceGroup]
    master_gpkg_layers: list[GpkgLayer]
    confidence_levels: list[str]
    versioning: VersioningConfig = Field(default_factory=VersioningConfig)

    # Filled in by the loader; not part of the YAML.
    base_dir: Path

    # ---- convenience accessors ------------------------------------------- #

    @property
    def raw_root(self) -> Path:
        # Per-machine override (e.g. a Drive-for-Desktop path) wins, so the
        # committed default stays portable. See docs/adr/0001.
        override = os.environ.get(RAW_ROOT_ENV)
        return Path(override).expanduser() if override else self._resolve(self.paths.raw_root)

    @property
    def output_root(self) -> Path:
        override = os.environ.get(OUTPUT_ROOT_ENV)
        return Path(override).expanduser() if override else self._resolve(self.paths.output_root)

    @property
    def runs_root(self) -> Path:
        return self._resolve(self.paths.runs_root)

    @property
    def register_path(self) -> Path:
        return self._resolve(self.input_register.path)

    @property
    def manifest_path(self) -> Path | None:
        """Resolved path to the raw manifest, or ``None`` if not configured."""
        return self._resolve(self.raw_manifest.path) if self.raw_manifest else None

    @property
    def target_epsg(self) -> int:
        return self.crs.target_epsg

    @property
    def data_prefix(self) -> str:
        """Prefix for GIS data layers, e.g. ``XV023222_Buduunkhad``."""
        return f"{self.project.data_prefix_code}_{self.project.name}"

    @property
    def register_prefix(self) -> str:
        """Prefix for admin registers/logs, e.g. ``XV-023222_Buduunkhad``."""
        return f"{self.project.project_code}_{self.project.name}"

    def _resolve(self, p: Path) -> Path:
        return p if p.is_absolute() else (self.base_dir / p)

    @field_validator("evidence_groups")
    @classmethod
    def _check_group_total(cls, v: list[EvidenceGroup]) -> list[EvidenceGroup]:
        # Must equal the number of register rows (78 methodology inputs + the SAS
        # hand-interpreted 1:25k scan reconciled from the real archive = 79).
        total = sum(g.count for g in v)
        if total != 79:
            raise ValueError(f"evidence_groups counts sum to {total}, expected 79")
        return v


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #

_BOOL_TRUE = {"true", "1", "yes", "y"}


def load_register(path: Path) -> list[InputRecord]:
    """Load and validate ``input_register.csv``."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input register not found: {path}")
    records: list[InputRecord] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                InputRecord(
                    no=int(row["no"]),
                    evidence_group=row["evidence_group"].strip(),
                    filename=row["filename"].strip(),
                    file_type=row["file_type"].strip(),
                    primary_phase=row["primary_phase"].strip(),
                    methodology_action=row.get("methodology_action", "").strip(),
                    is_sidecar=row.get("is_sidecar", "").strip().lower() in _BOOL_TRUE,
                    parent_file=row.get("parent_file", "").strip(),
                )
            )
    _validate_register(records)
    return records


def _validate_register(records: list[InputRecord]) -> None:
    if not records:
        raise ValueError("Input register is empty")
    # Numbering must be contiguous from 1 (count is whatever the register holds:
    # 78 methodology inputs + the reconciled SAS hand-interpreted scan = 79).
    n = len(records)
    numbers = sorted(r.no for r in records)
    if numbers != list(range(1, n + 1)):
        missing = sorted(set(range(1, n + 1)) - set(numbers))
        dupes = sorted({x for x in numbers if numbers.count(x) > 1})
        raise ValueError(f"Register numbering broken (missing={missing}, duplicates={dupes})")
    names = {r.filename for r in records}
    for r in records:
        if r.is_sidecar and r.parent_file and r.parent_file not in names:
            raise ValueError(
                f"Input #{r.no} sidecar '{r.filename}' references missing parent '{r.parent_file}'"
            )


def load_config(config_path: Path | str = "config/project.yaml") -> ProjectConfig:
    """Load ``project.yaml`` into a validated :class:`ProjectConfig`.

    ``base_dir`` is the parent of the ``config/`` directory (i.e. the repo root),
    against which relative paths resolve.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Project config not found: {config_path}")
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    base_dir = config_path.resolve().parent.parent
    data["base_dir"] = base_dir
    return ProjectConfig.model_validate(data)
