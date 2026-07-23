"""Typed configuration and input-register loading.

Everything the pipeline needs to know that is *not* derivable from the data lives
in ``config/project.yaml`` (constants/paths) and ``config/input_register.csv`` (the
79 raw inputs). Both are validated here on load so we fail early and clearly.
"""

from __future__ import annotations

import csv
import os
from collections.abc import Mapping
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Self

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

#: Per-machine path overrides (so a local Drive/synced path is never committed).
RAW_ROOT_ENV = "BUDUUNKHAD_RAW_ROOT"
OUTPUT_ROOT_ENV = "BUDUUNKHAD_OUTPUT_ROOT"
WORK_ROOT_ENV = "BUDUUNKHAD_WORK_ROOT"

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
    buffers_m: list[int] = Field(default_factory=lambda: [500, 1000, 5000, 10000, 20000, 25000])


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


class ExecutionProfile(StrEnum):
    """Migration profiles; legacy remains the unchanged default."""

    LEGACY = "legacy"
    HYBRID = "hybrid"
    AI_FIRST = "ai-first"


class AIProviderSelection(StrEnum):
    """Configured provider identity, independent from provider construction."""

    DISABLED = "disabled"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class SourceEgressPolicy(StrEnum):
    """Policy applied before any source preview can leave the local machine."""

    DENY = "deny"
    REQUIRE_EXPLICIT_APPROVAL = "require-explicit-approval"


class _ValidatedAIConfigModel(BaseModel):
    """Revalidate copy operations for security-sensitive AI configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    @classmethod
    def model_construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        del _fields_set, values
        raise TypeError("model_construct is unsupported for AI configuration")

    @classmethod
    def construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        del _fields_set, values
        raise TypeError("construct is unsupported for AI configuration")

    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        del deep
        values = {name: object.__getattribute__(self, name) for name in type(self).model_fields}
        if update:
            for key, value in update.items():
                if key not in type(self).model_fields:
                    raise ValueError(f"unknown update field: {key}")
                values[key] = value
        return type(self).model_validate(values)

    def copy(
        self,
        *,
        include: object = None,
        exclude: object = None,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        if include is not None or exclude is not None:
            raise ValueError("copy include/exclude is unsupported for AI configuration")
        return self.model_copy(update=update, deep=deep)


class AIReviewPolicyConfig(_ValidatedAIConfigModel):
    """Default human-review requirements for future AI-enabled profiles."""

    require_named_reviewer: bool = True
    high_risk_requires_geologist: bool = True
    production_geometry_requires_approval: bool = True


class AIConfig(_ValidatedAIConfigModel):
    """AI execution settings; construction remains keyless and offline by default."""

    profile: ExecutionProfile = ExecutionProfile.LEGACY
    enabled: bool = False
    provider: AIProviderSelection = AIProviderSelection.DISABLED
    provider_model: str | None = None
    external_data_allowed: bool = False
    request_timeout_seconds: float = Field(default=120.0, gt=0, le=3600)
    max_output_tokens: int = Field(default=4096, ge=1)
    max_requests_per_run: int = Field(default=1, ge=1)
    max_cost_per_run_usd: Decimal = Field(default=Decimal("0"), ge=0)
    concurrency: int = Field(default=1, ge=1)
    source_egress_policy: SourceEgressPolicy = SourceEgressPolicy.DENY
    review_policy: AIReviewPolicyConfig = Field(default_factory=AIReviewPolicyConfig)

    @model_validator(mode="after")
    def _execution_policy(self) -> AIConfig:
        live_provider = self.provider in {
            AIProviderSelection.OPENAI,
            AIProviderSelection.ANTHROPIC,
        }
        if self.profile is ExecutionProfile.LEGACY:
            if self.enabled:
                raise ValueError("legacy execution cannot enable AI")
            if self.provider is not AIProviderSelection.DISABLED:
                raise ValueError("legacy execution requires the disabled provider")
            if self.external_data_allowed:
                raise ValueError("legacy execution cannot allow external data")
        if live_provider and self.profile is ExecutionProfile.LEGACY:
            raise ValueError("live providers require hybrid or ai-first execution")
        if self.enabled:
            if not live_provider:
                raise ValueError("enabled AI requires OpenAI or Anthropic")
            if not self.provider_model or not self.provider_model.strip():
                raise ValueError("enabled AI requires a provider_model")
            if not self.external_data_allowed:
                raise ValueError("enabled live AI requires external_data_allowed=true")
            if self.source_egress_policy is not SourceEgressPolicy.REQUIRE_EXPLICIT_APPROVAL:
                raise ValueError("enabled live AI requires explicit source-egress approval")
        elif self.external_data_allowed:
            raise ValueError("external data cannot be allowed while AI is disabled")
        if self.provider is AIProviderSelection.DISABLED and self.provider_model is not None:
            raise ValueError("disabled provider cannot define provider_model")
        if not all(
            (
                self.review_policy.require_named_reviewer,
                self.review_policy.high_risk_requires_geologist,
                self.review_policy.production_geometry_requires_approval,
            )
        ):
            raise ValueError("PR 1 review safeguards cannot be disabled")
        return self


class ProjectConfig(BaseModel):
    """Fully-validated project configuration.

    ``config_dir`` is the directory the YAML was loaded from; relative paths in the
    config resolve against ``base_dir`` (the repo root, parent of ``config/``).
    """

    model_config = ConfigDict(validate_assignment=True, revalidate_instances="always")

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
    ai: AIConfig = Field(default_factory=AIConfig)

    # Filled in by the loader; not part of the YAML.
    base_dir: Path

    @classmethod
    def model_construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        del _fields_set, values
        raise TypeError("model_construct is unsupported for project configuration")

    @classmethod
    def construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        del _fields_set, values
        raise TypeError("construct is unsupported for project configuration")

    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        del deep
        values = {name: object.__getattribute__(self, name) for name in type(self).model_fields}
        if update:
            for key, value in update.items():
                if key not in type(self).model_fields:
                    raise ValueError(f"unknown update field: {key}")
                values[key] = value
        return type(self).model_validate(values)

    def copy(
        self,
        *,
        include: object = None,
        exclude: object = None,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        if include is not None or exclude is not None:
            raise ValueError("copy include/exclude is unsupported for project configuration")
        return self.model_copy(update=update, deep=deep)

    @model_serializer(mode="wrap")
    def _versioned_serialization(
        self,
        handler: SerializerFunctionWrapHandler,
        info: SerializationInfo,
    ) -> dict[str, object]:
        """Keep the pre-AI serialized shape unless callers opt into ``ai-v1``."""
        data = handler(self)
        context = info.context or {}
        version = context.get("config_serialization_version", "legacy")
        if version == "legacy":
            data.pop("ai", None)
        elif version != "ai-v1":
            raise ValueError(f"unsupported config serialization version: {version!r}")
        return data

    # ---- convenience accessors ------------------------------------------- #

    @property
    def raw_root(self) -> Path:
        # Per-machine override (e.g. a Drive-for-Desktop path) wins, so the
        # The committed default stays portable. Configuration defines identity; AGENTS.md defines
        # the raw-path safety and immutability boundary.
        override = os.environ.get(RAW_ROOT_ENV)
        return Path(override).expanduser() if override else self._resolve(self.paths.raw_root)

    @property
    def output_root(self) -> Path:
        override = os.environ.get(OUTPUT_ROOT_ENV)
        return Path(override).expanduser() if override else self._resolve(self.paths.output_root)

    @property
    def runs_root(self) -> Path:
        work_root = os.environ.get(WORK_ROOT_ENV)
        if work_root:
            return Path(work_root).expanduser() / "runs"
        return self._resolve(self.paths.runs_root)

    @property
    def evidence_root(self) -> Path:
        """Immutable accepted-evidence manifests, separate from mutable execution paths."""

        work_root = os.environ.get(WORK_ROOT_ENV)
        if work_root:
            return Path(work_root).expanduser() / "evidence-authority"
        return self.runs_root.parent / "evidence-authority"

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
    filenames = [r.filename for r in records]
    dup_names = sorted({f for f in filenames if filenames.count(f) > 1})
    if dup_names:
        # All raw resolution is basename-keyed, so a duplicate filename would silently alias two
        # registered inputs to one physical file.
        raise ValueError(f"Register has duplicate filename(s): {dup_names}")
    names = set(filenames)
    for r in records:
        if r.is_sidecar and r.parent_file and r.parent_file not in names:
            raise ValueError(
                f"Input #{r.no} sidecar '{r.filename}' references missing parent '{r.parent_file}'"
            )


def _validate_register_groups(records: list[InputRecord], groups: list[EvidenceGroup]) -> None:
    """Cross-check the register's evidence-group names + per-group counts against project.yaml.

    ``evidence_group`` is load-bearing (archive folder, working-copy resolution, support-vs-decision
    role), so a typo'd or miscounted group must fail loudly rather than silently mis-classify.
    """
    from collections import Counter

    counts = Counter(r.evidence_group for r in records)
    declared = {g.name: g.count for g in groups}
    reg_names, dec_names = set(counts), set(declared)
    if reg_names != dec_names:
        raise ValueError(
            "Register evidence_group names do not match project.yaml "
            f"(only-in-register={sorted(reg_names - dec_names)}, "
            f"only-in-config={sorted(dec_names - reg_names)})"
        )
    for name, cnt in declared.items():
        if counts[name] != cnt:
            raise ValueError(
                f"evidence_group '{name}' count mismatch: register has {counts[name]}, "
                f"project.yaml declares {cnt}"
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
    config = ProjectConfig.model_validate(data)
    # When the register is present, cross-check its group names/counts against project.yaml so a
    # divergence between the two editable config files fails loudly at load time.
    if config.register_path.exists():
        _validate_register_groups(load_register(config.register_path), config.evidence_groups)
    return config
