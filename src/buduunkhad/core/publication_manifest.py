"""Versioned provenance contract for locally staged publication packages."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePath, PurePosixPath
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from buduunkhad.ai.fingerprint import sha256_value
from buduunkhad.core.run_artifacts import canonical_relative_path

PUBLICATION_MANIFEST_FORMAT_VERSION: Final[Literal["1.1.0"]] = "1.1.0"
QGZ_FLAT_DATASOURCE_REWRITE: Final[Literal["qgz-flat-datasource-rewrite-v1"]] = (
    "qgz-flat-datasource-rewrite-v1"
)
AGGREGATION_NOTICE: Final[
    Literal[
        "This package aggregates outputs from their recorded source runs; aggregation does not "
        "make them one scientific execution or one approval event."
    ]
] = (
    "This package aggregates outputs from their recorded source runs; aggregation does not make "
    "them one scientific execution or one approval event."
)

PublicationStatus = Literal["PROVISIONAL", "HUMAN_REVIEW_PENDING", "APPROVED"]
SourceBindingMode = Literal["SHA256_BOUND", "LEGACY_PATH_ONLY"]
TransformationIdentifier = Literal["qgz-flat-datasource-rewrite-v1"]


def phase_package_tag(relative: PurePath) -> str:
    """Map a canonical output-root path to its portable ``PhaseNN`` package group."""

    top = relative.parts[0] if relative.parts else ""
    if len(top) >= 3 and top[:2].isdigit() and top[2] == "_":
        return f"Phase{top[:2]}"
    return top or "misc"


def _parse_timestamp(value: str, field_name: str) -> str:
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc
    return value


class PublicationProjectReference(BaseModel):
    """Reference and byte identity of the authoritative project configuration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    configuration_reference: str = Field(min_length=1)
    configuration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("configuration_reference")
    @classmethod
    def _reference_is_portable(cls, value: str) -> str:
        if "\\" in value or value.startswith(("/", "~")) or ":/" in value:
            raise ValueError("project configuration reference must not contain a local path")
        return value


class PublishedOutput(BaseModel):
    """Published bytes and, where available, their source-run-sealed identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    source_path: str
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_size_bytes: int | None = Field(default=None, ge=0)
    transformation_id: TransformationIdentifier | None = None

    _path_is_relative = field_validator("path")(canonical_relative_path)
    _source_path_is_relative = field_validator("source_path")(canonical_relative_path)

    @model_validator(mode="after")
    def _source_identity_is_complete(self) -> PublishedOutput:
        if (self.source_sha256 is None) != (self.source_size_bytes is None):
            raise ValueError("source SHA-256 and size must be recorded together")
        if (
            self.transformation_id is None
            and self.source_sha256 is not None
            and (self.source_sha256 != self.sha256 or self.source_size_bytes != self.size_bytes)
        ):
            raise ValueError("an untransformed copy must preserve its source bytes exactly")
        return self


class PublishedPhase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase_id: str = Field(pattern=r"^(0[0-9]|1[01]|99)$")
    source_run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    source_started_at: str = Field(min_length=1)
    source_finished_at: str = Field(min_length=1)
    source_run_manifest_path: str
    source_run_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_status: Literal["ok"]
    gate_state: str = Field(min_length=1)
    gate_provisional: bool
    human_review_or_qaqc_pending: bool
    pending_human_review_or_qaqc_count: int | None = Field(default=None, ge=0)
    source_binding_mode: SourceBindingMode
    outputs: tuple[PublishedOutput, ...] = Field(min_length=1)

    _manifest_path_is_relative = field_validator("source_run_manifest_path")(
        canonical_relative_path
    )

    @field_validator("source_started_at")
    @classmethod
    def _started_at_is_timestamp(cls, value: str) -> str:
        return _parse_timestamp(value, "source started_at")

    @field_validator("source_finished_at")
    @classmethod
    def _finished_at_is_timestamp(cls, value: str) -> str:
        return _parse_timestamp(value, "source finished_at")

    @model_validator(mode="after")
    def _outputs_match_binding_mode(self) -> PublishedPhase:
        expected_manifest_path = f"source_run_manifests/{self.source_run_id}/run_manifest.json"
        if self.source_run_manifest_path != expected_manifest_path:
            raise ValueError("source run manifest path is inconsistent with its run identity")
        paths = tuple(item.path for item in self.outputs)
        source_paths = tuple(item.source_path for item in self.outputs)
        if len(set(paths)) != len(paths) or len(set(source_paths)) != len(source_paths):
            raise ValueError("published phase contains duplicate output paths")
        expected_package_tag = f"Phase{self.phase_id}"
        if any(PurePosixPath(path).parts[0] != expected_package_tag for path in paths):
            raise ValueError(f"published output path does not belong to {expected_package_tag}")
        if any(
            phase_package_tag(PurePosixPath(path)) != expected_package_tag for path in source_paths
        ):
            raise ValueError(f"source output path does not belong to {expected_package_tag}")
        if paths != tuple(sorted(paths)):
            raise ValueError("published phase outputs must be sorted by path")
        if self.source_binding_mode == "SHA256_BOUND":
            if any(item.source_sha256 is None for item in self.outputs):
                raise ValueError("SHA256-bound outputs require source hashes and sizes")
        elif any(item.source_sha256 is not None for item in self.outputs):
            raise ValueError("legacy path-only outputs must not claim source-run byte binding")
        return self


class CompatibilityRunManifest(BaseModel):
    """Identity of the selected source manifest copied to the package root for compatibility."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    path: Literal["run_manifest.json"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def publication_status_for(phases: tuple[PublishedPhase, ...]) -> PublicationStatus:
    """Derive a conservative package state without treating automation as approval."""

    if any(phase.human_review_or_qaqc_pending for phase in phases):
        return "HUMAN_REVIEW_PENDING"
    if any(phase.gate_provisional for phase in phases):
        return "PROVISIONAL"
    if any(phase.source_binding_mode == "LEGACY_PATH_ONLY" for phase in phases):
        return "PROVISIONAL"
    if phases and all(phase.gate_state.upper() == "APPROVED" for phase in phases):
        return "APPROVED"
    return "PROVISIONAL"


def publication_id_for(
    *,
    project: PublicationProjectReference,
    package_version: str,
    git_commit_sha: str | None,
    phases: tuple[PublishedPhase, ...],
    package_status: PublicationStatus,
    compatibility_run_manifest: CompatibilityRunManifest,
    superseded_publication_id: str | None,
) -> str:
    """Return the stable package identity; publication time is deliberately excluded."""

    digest = sha256_value(
        {
            "manifest_format_version": PUBLICATION_MANIFEST_FORMAT_VERSION,
            "project": project,
            "package_version": package_version,
            "git_commit_sha": git_commit_sha,
            "included_phase_ids": tuple(phase.phase_id for phase in phases),
            "phases": phases,
            "package_status": package_status,
            "compatibility_run_manifest": compatibility_run_manifest,
            "aggregation_notice": AGGREGATION_NOTICE,
            "superseded_publication_id": superseded_publication_id,
        }
    )
    return f"pub-{digest[:32]}"


class PublicationManifest(BaseModel):
    """Machine-readable identity and source-run provenance for one staged package."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_format_version: Literal["1.1.0"]
    project: PublicationProjectReference
    package_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    git_commit_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{40,64}$")
    published_at: datetime
    publication_id: str = Field(pattern=r"^pub-[0-9a-f]{32}$")
    included_phase_ids: tuple[str, ...]
    phases: tuple[PublishedPhase, ...] = Field(min_length=1)
    package_status: PublicationStatus
    compatibility_run_manifest: CompatibilityRunManifest
    aggregation_notice: Literal[
        "This package aggregates outputs from their recorded source runs; aggregation does not "
        "make them one scientific execution or one approval event."
    ]
    superseded_publication_id: str | None = Field(default=None, pattern=r"^pub-[0-9a-f]{32}$")

    @model_validator(mode="before")
    @classmethod
    def _raw_output_paths_are_globally_unique(cls, value: object) -> object:
        """Reject duplicate claims before nested ownership or publication-ID validation."""

        if not isinstance(value, dict):
            return value
        raw_phases = value.get("phases")
        if not isinstance(raw_phases, (list, tuple)):
            return value
        paths: list[str] = []
        for raw_phase in raw_phases:
            if isinstance(raw_phase, PublishedPhase):
                raw_outputs: object = raw_phase.outputs
            elif isinstance(raw_phase, dict):
                raw_outputs = raw_phase.get("outputs")
            else:
                continue
            if not isinstance(raw_outputs, (list, tuple)):
                continue
            for raw_output in raw_outputs:
                if isinstance(raw_output, PublishedOutput):
                    path: object = raw_output.path
                elif isinstance(raw_output, dict):
                    path = raw_output.get("path")
                else:
                    continue
                if isinstance(path, str):
                    paths.append(path)
        if len(set(paths)) != len(paths):
            raise ValueError("publication output paths must be globally unique")
        return value

    @model_validator(mode="after")
    def _identity_is_consistent(self) -> PublicationManifest:
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise ValueError("publication timestamp must be timezone-aware")
        if self.published_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("publication timestamp must be recorded in UTC")
        phase_ids = tuple(phase.phase_id for phase in self.phases)
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("publication manifest contains duplicate phase IDs")
        output_paths = tuple(output.path for phase in self.phases for output in phase.outputs)
        if len(set(output_paths)) != len(output_paths):
            raise ValueError("publication output paths must be globally unique")
        if phase_ids != tuple(sorted(phase_ids)):
            raise ValueError("publication phases must be sorted by phase ID")
        if self.included_phase_ids != phase_ids:
            raise ValueError("included phase IDs must exactly match phase records")
        matching_compatibility_sources = [
            phase
            for phase in self.phases
            if phase.source_run_id == self.compatibility_run_manifest.run_id
            and phase.source_run_manifest_sha256 == self.compatibility_run_manifest.sha256
        ]
        if not matching_compatibility_sources:
            raise ValueError("compatibility manifest must be one selected source run")
        expected_status = publication_status_for(self.phases)
        if self.package_status != expected_status:
            raise ValueError("publication package status is inconsistent with its phase gates")
        expected_id = publication_id_for(
            project=self.project,
            package_version=self.package_version,
            git_commit_sha=self.git_commit_sha,
            phases=self.phases,
            package_status=self.package_status,
            compatibility_run_manifest=self.compatibility_run_manifest,
            superseded_publication_id=self.superseded_publication_id,
        )
        if self.publication_id != expected_id:
            raise ValueError("publication ID does not match the manifest identity fields")
        return self
