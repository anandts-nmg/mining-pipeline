"""Typed access to versioned methodology authority and discrepancy records."""

from __future__ import annotations

from datetime import datetime
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MethodologyError(ValueError):
    """A methodology authority resource is malformed or unavailable."""


#: Explicit marker for migrated historical decisions whose approver or date was not recorded.
HISTORICAL_UNKNOWN = "historical-unknown"

DiscrepancyStatus = Literal["unresolved", "resolved", "superseded", "withdrawn"]
AuthorityStatus = Literal["adopted", "reference-only", "pending-review", "obsolete"]
RequirementStatus = Literal["adopted", "adopted-with-unresolved-discrepancy"]
AutomationStatus = Literal[
    "implemented",
    "partially-implemented",
    "legacy-comparator",
    "stub",
]


class MethodologySource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    role: str
    repository_path: str | None = None
    external_reference: str | None = None
    authority_status: AuthorityStatus = "adopted"
    expected_document: str | None = None
    repository_copy: str | None = None
    repository_copy_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    repository_copy_size_bytes: int | None = Field(default=None, ge=0)
    repository_snapshot_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    existence_verified: bool = False
    external_file_id: str | None = Field(default=None, min_length=1)
    existence_verified_at: datetime | None = None
    existence_verified_by: str | None = Field(default=None, min_length=1)
    existence_evidence_reference: str | None = Field(default=None, min_length=1)
    superseding_contract: str | None = None
    remaining_actions: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _has_exactly_one_location(self) -> MethodologySource:
        locations = (self.repository_path, self.external_reference)
        if sum(item is not None for item in locations) != 1:
            raise ValueError("methodology source requires exactly one location")
        if self.external_reference is not None and not self.external_reference.startswith(
            "BUDUUNKHAD_WORKFLOW_DOCS_ROOT::"
        ):
            raise ValueError("external methodology must use BUDUUNKHAD_WORKFLOW_DOCS_ROOT")
        copy_facts = (
            self.repository_copy_sha256,
            self.repository_copy_size_bytes,
            self.repository_snapshot_sha256,
        )
        if self.repository_copy is None:
            if any(value is not None for value in copy_facts):
                raise ValueError("repository-copy identity requires repository_copy")
        else:
            if not all(value is not None for value in copy_facts):
                raise ValueError(
                    "repository_copy requires SHA-256, byte size, and snapshot SHA-256"
                )
            copy_path = PurePosixPath(self.repository_copy)
            if (
                copy_path.is_absolute()
                or copy_path.as_posix() != self.repository_copy
                or ".." in copy_path.parts
                or copy_path.parts[:2] != ("docs", "methodology")
            ):
                raise ValueError(
                    "repository_copy must be a canonical relative path below docs/methodology"
                )
            if self.expected_document is None or copy_path.name != self.expected_document:
                raise ValueError("repository_copy filename must match expected_document")
        verification_facts = (
            self.existence_verified_at,
            self.existence_verified_by,
            self.existence_evidence_reference,
        )
        if self.external_reference is None and any(
            value is not None for value in (self.external_file_id, *verification_facts)
        ):
            raise ValueError("external verification facts require an external methodology source")
        if self.external_reference is not None and self.existence_verified:
            if not all(value is not None for value in (self.external_file_id, *verification_facts)):
                raise ValueError(
                    "verified external methodology requires file ID, timestamp, verifier, "
                    "and evidence reference"
                )
            assert self.existence_verified_at is not None
            if (
                self.existence_verified_at.tzinfo is None
                or self.existence_verified_at.utcoffset() is None
            ):
                raise ValueError("external verification timestamp must be timezone-aware")
        elif any(value is not None for value in verification_facts):
            raise ValueError("unverified methodology cannot carry verification evidence")
        return self


class MethodologyRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    requirement_id: str
    statement: str
    source_refs: tuple[str, ...] = Field(min_length=1)
    status: RequirementStatus

    @model_validator(mode="after")
    def _source_refs_are_unique(self) -> MethodologyRequirement:
        if len(set(self.source_refs)) != len(self.source_refs):
            raise ValueError("methodology requirement contains duplicate source references")
        return self


class PhaseMethodology(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    phase_id: str = Field(pattern=r"^0[0-5]$")
    requirements: tuple[MethodologyRequirement, ...]

    @model_validator(mode="after")
    def _unique_requirement_ids(self) -> PhaseMethodology:
        identities = tuple(item.requirement_id for item in self.requirements)
        if len(set(identities)) != len(identities):
            raise ValueError("phase methodology contains duplicate stable requirement IDs")
        return self


class AuthorityRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.2.0"]
    sources: tuple[MethodologySource, ...]
    precedence: tuple[str, ...]

    @model_validator(mode="after")
    def _source_identities_and_precedence_are_valid(self) -> AuthorityRegistry:
        identities = tuple(item.source_id for item in self.sources)
        if len(set(identities)) != len(identities):
            raise ValueError("methodology authority contains duplicate source IDs")
        if not self.precedence or self.precedence[0] != "repository.methodology-contracts":
            raise ValueError("methodology precedence must begin with repository contracts")
        if len(set(self.precedence)) != len(self.precedence):
            raise ValueError("methodology precedence contains duplicate source IDs")
        unknown = set(self.precedence) - set(identities)
        if unknown:
            raise ValueError(
                f"methodology precedence references unknown sources: {sorted(unknown)}"
            )
        return self


class MethodologyDiscrepancy(BaseModel):
    """One record in the append-only methodology decision register.

    The register is the complete decision history: unresolved obligations plus
    resolved, superseded, and withdrawn records. Resolved history is never
    erased; a later issue gets a new linked record instead of reopening one.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    discrepancy_id: str = Field(pattern=r"^METH-DISC-\d{3}$")
    subject: str
    compared_sources: tuple[str, ...] = Field(min_length=2)
    statement: str
    operational_impact: str
    status: DiscrepancyStatus
    proposed_resolution: str | None = None
    required_approver: str | None = None
    remaining_actions: tuple[str, ...] = ()
    resolution: str | None = None
    rationale: str | None = None
    approver: str | None = None
    resolved_on: str | None = None
    effective_version: str | None = None
    implementation_evidence: str | None = None
    superseded_by: str | None = None
    withdrawal_reason: str | None = None
    migration_source: str | None = None
    related_discrepancy_ids: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _status_requirements(self) -> MethodologyDiscrepancy:
        if self.status == "unresolved":
            if not (self.proposed_resolution and self.required_approver):
                raise ValueError(
                    "unresolved discrepancies require a proposed resolution (or an explicit "
                    "statement that none exists) and a required approver"
                )
            if not self.remaining_actions:
                raise ValueError("unresolved discrepancies require remaining actions")
            adopted = (
                self.resolution,
                self.rationale,
                self.approver,
                self.resolved_on,
                self.effective_version,
                self.superseded_by,
                self.withdrawal_reason,
            )
            if any(adopted):
                raise ValueError("unresolved discrepancies cannot carry adopted-resolution fields")
        elif self.status in {"resolved", "superseded"}:
            required = (
                self.resolution,
                self.rationale,
                self.approver,
                self.resolved_on,
                self.effective_version,
            )
            if not all(required):
                raise ValueError(
                    "resolved discrepancies require resolution, rationale, approver, "
                    f"resolution date, and effective version (use {HISTORICAL_UNKNOWN!r} "
                    "for unrecorded historical approvers or dates)"
                )
            if not (self.implementation_evidence or self.remaining_actions):
                raise ValueError(
                    "resolved discrepancies require implementation evidence or remaining actions"
                )
            if self.withdrawal_reason is not None:
                raise ValueError("only withdrawn discrepancies carry a withdrawal reason")
            if self.status == "superseded" and self.superseded_by is None:
                raise ValueError("superseded discrepancies require a superseded_by link")
            if self.status == "resolved" and self.superseded_by is not None:
                raise ValueError("resolved discrepancies cannot carry a superseded_by link")
        else:  # withdrawn
            if not self.withdrawal_reason:
                raise ValueError("withdrawn discrepancies require a withdrawal reason")
            if any((self.resolution, self.superseded_by)):
                raise ValueError("withdrawn discrepancies cannot carry resolution fields")
        return self


class DiscrepancyRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.2.0"]
    discrepancies: tuple[MethodologyDiscrepancy, ...]

    @model_validator(mode="after")
    def _links_are_valid(self) -> DiscrepancyRegistry:
        identities = tuple(item.discrepancy_id for item in self.discrepancies)
        if len(set(identities)) != len(identities):
            raise ValueError("methodology discrepancies contain duplicate stable IDs")
        known = set(identities)
        positions = {identity: index for index, identity in enumerate(identities)}
        successors = {
            item.discrepancy_id: item.superseded_by
            for item in self.discrepancies
            if item.superseded_by is not None
        }
        for origin, target in successors.items():
            if target not in known:
                raise ValueError(f"superseded_by references an unknown record: {origin}")
            seen = {origin}
            cursor: str | None = target
            while cursor is not None:
                if cursor in seen:
                    raise ValueError(f"supersession chain is cyclic at: {cursor}")
                seen.add(cursor)
                cursor = successors.get(cursor)
        for item in self.discrepancies:
            if len(set(item.related_discrepancy_ids)) != len(item.related_discrepancy_ids):
                raise ValueError(
                    f"related_discrepancy_ids contains duplicates: {item.discrepancy_id}"
                )
            for related in item.related_discrepancy_ids:
                if related not in known:
                    raise ValueError(
                        f"related_discrepancy_ids references an unknown record: {related}"
                    )
                if positions[related] >= positions[item.discrepancy_id]:
                    raise ValueError(
                        "new discrepancy records may link only to earlier append-only history"
                    )
        return self

    def unresolved(self) -> tuple[MethodologyDiscrepancy, ...]:
        """Filtered view of open obligations; never removes records from the register."""

        return tuple(item for item in self.discrepancies if item.status == "unresolved")


class AutomationBoundary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase_id: str = Field(pattern=r"^(0[0-9]|1[01]|99)$")
    automation_category: Literal[
        "desktop-deterministic",
        "desktop-orchestrated",
        "field-acquisition",
        "desktop-integration",
        "desktop-planning",
        "desktop-packaging",
    ]
    deterministic_authority: tuple[str, ...] = Field(min_length=1)
    human_review_boundary: tuple[str, ...] = Field(min_length=1)
    ai_permitted: tuple[str, ...] = ()
    ai_prohibited: tuple[str, ...] = Field(min_length=1)
    blocking_dependencies: tuple[str, ...] = ()
    status: AutomationStatus
    migration_source: str


class AutomationBoundariesRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    boundaries: tuple[AutomationBoundary, ...]

    @model_validator(mode="after")
    def _covers_every_registered_phase(self) -> AutomationBoundariesRegistry:
        expected = {f"{value:02d}" for value in range(12)} | {"99"}
        actual = tuple(item.phase_id for item in self.boundaries)
        if len(set(actual)) != len(actual):
            raise ValueError("automation boundaries contain duplicate phase IDs")
        if set(actual) != expected:
            raise ValueError("automation boundaries must cover phases 00-11 and 99 exactly")
        return self


def load_phase_methodology(phase_id: str) -> PhaseMethodology:
    if phase_id not in {f"{value:02d}" for value in range(6)}:
        raise MethodologyError(f"unsupported methodology phase: {phase_id}")
    try:
        phase = PhaseMethodology.model_validate(_load_packaged_yaml(f"phase{phase_id}.yaml"))
        _validate_phase_source_refs(
            phase,
            load_authority_registry(),
            load_discrepancy_registry(),
        )
    except ValueError as exc:
        raise MethodologyError(f"phase methodology is invalid: {phase_id}: {exc}") from exc
    return phase


def load_authority_registry() -> AuthorityRegistry:
    return AuthorityRegistry.model_validate(_load_packaged_yaml("authority.yaml"))


def load_discrepancy_registry() -> DiscrepancyRegistry:
    return DiscrepancyRegistry.model_validate(_load_packaged_yaml("discrepancies.yaml"))


def load_automation_boundaries() -> AutomationBoundariesRegistry:
    return AutomationBoundariesRegistry.model_validate(
        _load_packaged_yaml("automation_boundaries.yaml")
    )


def _load_packaged_yaml(filename: str) -> object:
    try:
        resource = resources.files("buduunkhad").joinpath("methodology_data", filename)
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeError, OSError):
        try:
            checkout = Path(__file__).parents[3] / "config" / "methodology" / filename
            text = checkout.read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeError, OSError) as exc:
            raise MethodologyError(
                f"packaged methodology resource is unavailable: {filename}"
            ) from exc
    try:
        return _parse_yaml(text)
    except yaml.YAMLError as exc:
        raise MethodologyError(f"packaged methodology YAML is invalid: {filename}") from exc


def load_phase_methodology_from_checkout(root: Path, phase_id: str) -> PhaseMethodology:
    path = root / "config" / "methodology" / f"phase{phase_id}.yaml"
    try:
        phase = PhaseMethodology.model_validate(_parse_yaml(path.read_text(encoding="utf-8")))
        methodology_root = root / "config" / "methodology"
        authority = AuthorityRegistry.model_validate(
            _parse_yaml((methodology_root / "authority.yaml").read_text(encoding="utf-8"))
        )
        discrepancies = DiscrepancyRegistry.model_validate(
            _parse_yaml((methodology_root / "discrepancies.yaml").read_text(encoding="utf-8"))
        )
        _validate_phase_source_refs(phase, authority, discrepancies)
        return phase
    except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
        raise MethodologyError(f"methodology file is invalid: {path}: {exc}") from exc


def _validate_phase_source_refs(
    phase: PhaseMethodology,
    authority: AuthorityRegistry,
    discrepancies: DiscrepancyRegistry,
) -> None:
    known = {item.source_id for item in authority.sources} | {
        item.discrepancy_id for item in discrepancies.discrepancies
    }
    for requirement in phase.requirements:
        unknown = set(requirement.source_refs) - known
        if unknown:
            raise ValueError(
                f"{requirement.requirement_id} references unknown methodology sources: "
                f"{sorted(unknown)}"
            )


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    value: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in value:
            raise yaml.constructor.ConstructorError(
                "while constructing a methodology mapping",
                node.start_mark,
                f"duplicate key: {key!r}",
                key_node.start_mark,
            )
        value[key] = loader.construct_object(value_node, deep=deep)
    return value


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _parse_yaml(text: str) -> object:
    return yaml.load(text, Loader=_UniqueKeyLoader)
