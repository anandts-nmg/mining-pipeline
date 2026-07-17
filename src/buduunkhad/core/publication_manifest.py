"""Versioned provenance contract for locally staged publication packages."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from buduunkhad.ai.fingerprint import sha256_value

PUBLICATION_MANIFEST_FORMAT_VERSION: Final[Literal["1.0.0"]] = "1.0.0"
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


def _relative_package_path(value: str) -> str:
    if not value or "\\" in value:
        raise ValueError("package paths must be non-empty POSIX relative paths")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("package paths must stay within the publication package")
    if path.as_posix() != value:
        raise ValueError("package paths must use canonical POSIX form")
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
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    _path_is_relative = field_validator("path")(_relative_package_path)


class PublishedPhase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase_id: str = Field(pattern=r"^(0[0-9]|1[01]|99)$")
    source_run_id: str = Field(min_length=1)
    source_run_manifest_path: str
    source_run_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gate_state: str = Field(min_length=1)
    gate_provisional: bool
    human_review_or_qaqc_pending: bool
    pending_human_review_or_qaqc_count: int | None = Field(default=None, ge=0)
    outputs: tuple[PublishedOutput, ...] = Field(min_length=1)

    _manifest_path_is_relative = field_validator("source_run_manifest_path")(_relative_package_path)

    @model_validator(mode="after")
    def _outputs_are_unique_and_sorted(self) -> PublishedPhase:
        paths = tuple(item.path for item in self.outputs)
        if len(set(paths)) != len(paths):
            raise ValueError("published phase contains duplicate output paths")
        if paths != tuple(sorted(paths)):
            raise ValueError("published phase outputs must be sorted by path")
        return self


def publication_status_for(phases: tuple[PublishedPhase, ...]) -> PublicationStatus:
    """Derive a conservative package state without treating automated completion as approval."""

    if any(phase.human_review_or_qaqc_pending for phase in phases):
        return "HUMAN_REVIEW_PENDING"
    if any(phase.gate_provisional for phase in phases):
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
    superseded_publication_id: str | None,
) -> str:
    """Return the stable package identity; publication time is deliberately not identity input."""

    digest = sha256_value(
        {
            "manifest_format_version": PUBLICATION_MANIFEST_FORMAT_VERSION,
            "project": project,
            "package_version": package_version,
            "git_commit_sha": git_commit_sha,
            "included_phase_ids": tuple(phase.phase_id for phase in phases),
            "phases": phases,
            "package_status": package_status,
            "aggregation_notice": AGGREGATION_NOTICE,
            "superseded_publication_id": superseded_publication_id,
        }
    )
    return f"pub-{digest[:32]}"


class PublicationManifest(BaseModel):
    """Machine-readable identity and source-run provenance for one staged package."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_format_version: Literal["1.0.0"]
    project: PublicationProjectReference
    package_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    git_commit_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{40,64}$")
    published_at: datetime
    publication_id: str = Field(pattern=r"^pub-[0-9a-f]{32}$")
    included_phase_ids: tuple[str, ...]
    phases: tuple[PublishedPhase, ...] = Field(min_length=1)
    package_status: PublicationStatus
    aggregation_notice: Literal[
        "This package aggregates outputs from their recorded source runs; aggregation does not "
        "make them one scientific execution or one approval event."
    ]
    superseded_publication_id: str | None = Field(default=None, pattern=r"^pub-[0-9a-f]{32}$")

    @model_validator(mode="after")
    def _identity_is_consistent(self) -> PublicationManifest:
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise ValueError("publication timestamp must be timezone-aware")
        if self.published_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("publication timestamp must be recorded in UTC")
        phase_ids = tuple(phase.phase_id for phase in self.phases)
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("publication manifest contains duplicate phase IDs")
        if phase_ids != tuple(sorted(phase_ids)):
            raise ValueError("publication phases must be sorted by phase ID")
        if self.included_phase_ids != phase_ids:
            raise ValueError("included phase IDs must exactly match phase records")
        expected_status = publication_status_for(self.phases)
        if self.package_status != expected_status:
            raise ValueError("publication package status is inconsistent with its phase gates")
        expected_id = publication_id_for(
            project=self.project,
            package_version=self.package_version,
            git_commit_sha=self.git_commit_sha,
            phases=self.phases,
            package_status=self.package_status,
            superseded_publication_id=self.superseded_publication_id,
        )
        if self.publication_id != expected_id:
            raise ValueError("publication ID does not match the manifest identity fields")
        return self
