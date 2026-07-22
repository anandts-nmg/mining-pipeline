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
BlockerCategory = Literal[
    "implementation",
    "legal-license",
    "lineage-reconciliation",
    "missing-validation-evidence",
    "parameter-selection",
]
ReadinessStatus = Literal["blocked-dataset", "blocked-human-evidence", "excluded", "parked"]


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

    format_version: Literal["1.3.0"]
    sources: tuple[MethodologySource, ...]
    precedence: tuple[str, ...]

    @model_validator(mode="after")
    def _source_identities_and_precedence_are_valid(self) -> AuthorityRegistry:
        identities = tuple(item.source_id for item in self.sources)
        if len(set(identities)) != len(identities):
            raise ValueError("methodology authority contains duplicate source IDs")
        if not self.precedence or self.precedence[:2] != (
            "methodology.master-v9",
            "repository.methodology-contracts",
        ):
            raise ValueError(
                "methodology precedence must begin with the exact master followed by "
                "repository contracts"
            )
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
    affected_phases: tuple[str, ...] = ()
    blocker_category: BlockerCategory | None = None
    missing_evidence: tuple[str, ...] = ()
    resolves_discrepancy_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _status_requirements(self) -> MethodologyDiscrepancy:
        if len(set(self.affected_phases)) != len(self.affected_phases):
            raise ValueError("affected_phases contains duplicates")
        if any(
            phase not in {f"{value:02d}" for value in range(12)} | {"99"}
            for phase in self.affected_phases
        ):
            raise ValueError("affected_phases contains an unknown phase")
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
            if self.resolves_discrepancy_ids:
                raise ValueError("unresolved discrepancies cannot resolve earlier records")
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
            if self.blocker_category is not None or self.missing_evidence:
                raise ValueError("resolved discrepancies cannot carry active blocker metadata")
            if self.status == "superseded" and self.resolves_discrepancy_ids:
                raise ValueError("superseded discrepancies cannot resolve earlier records")
        else:  # withdrawn
            if not self.withdrawal_reason:
                raise ValueError("withdrawn discrepancies require a withdrawal reason")
            if any((self.resolution, self.superseded_by)):
                raise ValueError("withdrawn discrepancies cannot carry resolution fields")
            if self.resolves_discrepancy_ids:
                raise ValueError("withdrawn discrepancies cannot resolve earlier records")
        return self


class DiscrepancyRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.4.0"]
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
            if len(set(item.resolves_discrepancy_ids)) != len(item.resolves_discrepancy_ids):
                raise ValueError(
                    f"resolves_discrepancy_ids contains duplicates: {item.discrepancy_id}"
                )
            for resolved in item.resolves_discrepancy_ids:
                if resolved not in known:
                    raise ValueError(
                        f"resolves_discrepancy_ids references an unknown record: {resolved}"
                    )
                if positions[resolved] >= positions[item.discrepancy_id]:
                    raise ValueError(
                        "resolution records may resolve only earlier append-only history"
                    )
                target_record = self.discrepancies[positions[resolved]]
                if target_record.status != "unresolved":
                    raise ValueError(
                        "resolution records may target only historically unresolved records"
                    )
                if item.status != "resolved":
                    raise ValueError("only resolved records may close earlier discrepancies")
        resolved_targets = tuple(
            target for item in self.discrepancies for target in item.resolves_discrepancy_ids
        )
        if len(set(resolved_targets)) != len(resolved_targets):
            raise ValueError("an unresolved discrepancy cannot have multiple resolution records")
        return self

    def unresolved(self) -> tuple[MethodologyDiscrepancy, ...]:
        """Filtered view of open obligations; never removes records from the register."""

        resolved_targets = {
            target for item in self.discrepancies for target in item.resolves_discrepancy_ids
        }
        return tuple(
            item
            for item in self.discrepancies
            if item.status == "unresolved" and item.discrepancy_id not in resolved_targets
        )

    def historical_unresolved(self) -> tuple[MethodologyDiscrepancy, ...]:
        """Raw historical status view, including items closed by later linked decisions."""

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


class AutomationReadinessObligation(BaseModel):
    """One explicit operational prerequisite or conservative dataset exclusion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    obligation_id: str = Field(pattern=r"^METH-READY-\d{3}$")
    subject: str
    affected_phases: tuple[str, ...] = Field(min_length=1)
    status: ReadinessStatus
    blocks_phase_completion: bool
    decision: str
    required_evidence: tuple[str, ...] = Field(min_length=1)
    deterministic_next_steps: tuple[str, ...] = Field(min_length=1)
    required_human_authority: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _values_are_coherent(self) -> AutomationReadinessObligation:
        known_phases = {f"{value:02d}" for value in range(12)} | {"99"}
        if len(set(self.affected_phases)) != len(self.affected_phases):
            raise ValueError("readiness obligation contains duplicate phases")
        if any(phase not in known_phases for phase in self.affected_phases):
            raise ValueError("readiness obligation contains an unknown phase")
        if len(set(self.source_refs)) != len(self.source_refs):
            raise ValueError("readiness obligation contains duplicate source references")
        if self.status in {"excluded", "blocked-dataset"} and self.blocks_phase_completion:
            raise ValueError("dataset exclusions cannot claim to block the whole phase")
        if self.status in {"parked", "blocked-human-evidence"} and not self.blocks_phase_completion:
            raise ValueError("parked or human-blocked obligations must block phase completion")
        return self


class AutomationReadinessRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    interpretation: Literal[
        "Operational prerequisites and exclusions; not unresolved methodology authority, "
        "scientific approval or a gate decision."
    ]
    obligations: tuple[AutomationReadinessObligation, ...]

    @model_validator(mode="after")
    def _identities_are_unique(self) -> AutomationReadinessRegistry:
        identities = tuple(item.obligation_id for item in self.obligations)
        if len(set(identities)) != len(identities):
            raise ValueError("automation readiness contains duplicate obligation IDs")
        return self


class BasemapAssetPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    input_number: Literal[75, 76]
    role: Literal["district-context-visual-reference", "detailed-surface-visual-reference"]
    operation: Literal["reproject-full-extent", "reproject-and-clip"]
    clip_buffer_m: int | None = Field(default=None, ge=0)
    rationale: str

    @model_validator(mode="after")
    def _operation_matches_buffer(self) -> BasemapAssetPolicy:
        if self.operation == "reproject-full-extent" and self.clip_buffer_m is not None:
            raise ValueError("full-extent basemap cannot carry a clip buffer")
        if self.operation == "reproject-and-clip" and self.clip_buffer_m is None:
            raise ValueError("clipped basemap requires a clip buffer")
        return self


class DemProcessingProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str
    input_number: Literal[9, 12]
    nominal_resolution_m: float = Field(gt=0)
    clip_buffer_m: int = Field(gt=0)
    raster_derivatives: bool
    vector_hydrology: bool
    sink_treatment: Literal["fill-depressions", "not-applied"]
    contour_interval_m: float | None = Field(default=None, gt=0)
    stream_threshold_cells: int | None = Field(default=None, gt=0)
    minimum_basin_area_ha: float | None = Field(default=None, ge=0)
    rationale: str

    @model_validator(mode="after")
    def _hydrology_parameters_are_complete(self) -> DemProcessingProfile:
        parameters = (
            self.contour_interval_m,
            self.stream_threshold_cells,
            self.minimum_basin_area_ha,
        )
        if self.vector_hydrology:
            if self.sink_treatment != "fill-depressions" or any(
                value is None for value in parameters
            ):
                raise ValueError("vector hydrology requires complete processing parameters")
        elif self.sink_treatment != "not-applied" or any(value is not None for value in parameters):
            raise ValueError("non-hydrology DEM profile cannot carry hydrology parameters")
        return self


class Phase02ProcessingContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    phase_id: Literal["02"]
    authority_source: Literal["methodology.master-v9"]
    decision_sources: tuple[Literal["METH-DISC-052", "METH-DISC-053"], ...]
    policy_status: Literal["adopted-support-evidence-contract"]
    scientific_use: Literal["support-evidence-only"]
    basemap_assets: tuple[BasemapAssetPolicy, ...]
    dem_profiles: tuple[DemProcessingProfile, ...]
    parameter_policy: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _covers_the_exact_registered_assets(self) -> Phase02ProcessingContract:
        if tuple(item.input_number for item in self.basemap_assets) != (75, 76):
            raise ValueError("Phase 02 basemap contract must cover inputs 75 and 76 in order")
        if tuple(item.input_number for item in self.dem_profiles) != (12, 9):
            raise ValueError("Phase 02 DEM contract must cover primary input 12 then input 9")
        if self.decision_sources != ("METH-DISC-052", "METH-DISC-053"):
            raise ValueError("Phase 02 processing decisions must be exact and ordered")
        return self


class Phase04Criterion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    criterion_id: str
    maximum_points: int = Field(ge=1, le=100)
    scoring_semantics: Literal["ranged-prospect-level"]


class Phase04ClassBand(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    class_id: Literal["A", "B", "C", "D"]
    minimum_score: int = Field(ge=0, le=100)
    maximum_score: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def _ordered(self) -> Phase04ClassBand:
        if self.minimum_score > self.maximum_score:
            raise ValueError("Phase 04 class-band bounds are reversed")
        return self


class Phase04MigrationContract(BaseModel):
    """Master-aligned target contract kept separate from the legacy comparator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    phase_id: Literal["04"]
    authority_source: Literal["methodology.master-v9"]
    authority_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scoring_source: Literal["phase04.guide"]
    class_band_source: Literal["methodology.master-v9"]
    decision_sources: tuple[Literal["METH-DISC-060", "METH-DISC-068"], ...]
    status: Literal["specified-not-integrated"]
    legacy_comparator_status: Literal["retained-regression-only"]
    target_geometry: Literal["human-reviewed-prospect-polygons"]
    criteria: tuple[Phase04Criterion, ...] = Field(min_length=1)
    class_bands: tuple[Phase04ClassBand, ...] = Field(min_length=1)
    required_input_contracts: tuple[str, ...] = Field(min_length=1)
    required_fields: tuple[str, ...] = Field(min_length=1)
    ai_policy: tuple[str, ...] = Field(min_length=1)
    activation_requirements: tuple[str, ...] = Field(min_length=1)
    blocking_readiness_ids: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _complete_scoring_contract(self) -> Phase04MigrationContract:
        criteria = tuple((item.criterion_id, item.maximum_points) for item in self.criteria)
        if criteria != (
            ("geology", 20),
            ("occurrence", 15),
            ("geochemistry", 20),
            ("remote_sensing", 15),
            ("structure", 10),
            ("deposit_model_fit", 10),
            ("access", 5),
            ("confidence", 5),
        ):
            raise ValueError("Phase 04 target criteria must match the adopted desktop matrix")
        class_bands = tuple(
            (item.class_id, item.minimum_score, item.maximum_score) for item in self.class_bands
        )
        if class_bands != (
            ("A", 75, 100),
            ("B", 55, 74),
            ("C", 35, 54),
            ("D", 0, 34),
        ):
            raise ValueError("Phase 04 target class bands must match the exact master")
        if len(set(self.required_fields)) != len(self.required_fields):
            raise ValueError("Phase 04 required fields contain duplicates")
        if self.decision_sources != ("METH-DISC-060", "METH-DISC-068"):
            raise ValueError("Phase 04 migration decisions must be exact and ordered")
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


def load_automation_readiness() -> AutomationReadinessRegistry:
    registry = AutomationReadinessRegistry.model_validate(
        _load_packaged_yaml("automation_readiness.yaml")
    )
    authority = load_authority_registry()
    discrepancies = load_discrepancy_registry()
    known = {item.source_id for item in authority.sources} | {
        item.discrepancy_id for item in discrepancies.discrepancies
    }
    allowed_contract_refs = {"phase04_migration.yaml"}
    for obligation in registry.obligations:
        unknown = set(obligation.source_refs) - known - allowed_contract_refs
        if unknown:
            raise MethodologyError(
                f"automation readiness references unknown sources: {sorted(unknown)}"
            )
    return registry


def load_phase02_processing_contract() -> Phase02ProcessingContract:
    contract = Phase02ProcessingContract.model_validate(
        _load_packaged_yaml("phase02_processing.yaml")
    )
    authority = load_authority_registry()
    master = next(
        (source for source in authority.sources if source.source_id == contract.authority_source),
        None,
    )
    if master is None or master.authority_status != "adopted":
        raise MethodologyError("Phase 02 processing authority is not an adopted source")
    discrepancies = {
        item.discrepancy_id: item for item in load_discrepancy_registry().discrepancies
    }
    invalid_decisions = {
        identity
        for identity in contract.decision_sources
        if identity not in discrepancies or discrepancies[identity].status != "resolved"
    }
    if invalid_decisions:
        raise MethodologyError(
            f"Phase 02 processing decisions are not resolved: {sorted(invalid_decisions)}"
        )
    return contract


def load_phase04_migration_contract() -> Phase04MigrationContract:
    contract = Phase04MigrationContract.model_validate(
        _load_packaged_yaml("phase04_migration.yaml")
    )
    authority = load_authority_registry()
    sources = {source.source_id: source for source in authority.sources}
    master = sources.get(contract.authority_source)
    if master is None:
        raise MethodologyError("Phase 04 migration master source is not registered")
    if master.repository_copy_sha256 != contract.authority_sha256:
        raise MethodologyError("Phase 04 migration authority does not match the exact master")
    scoring_source = sources.get(contract.scoring_source)
    if scoring_source is None:
        raise MethodologyError("Phase 04 migration scoring source is not registered")
    if (
        scoring_source.authority_status != "adopted"
        or scoring_source.repository_copy_sha256 is None
    ):
        raise MethodologyError("Phase 04 scoring source is not an adopted byte-bound guide")
    discrepancies = {
        item.discrepancy_id: item for item in load_discrepancy_registry().discrepancies
    }
    invalid_decisions = {
        identity
        for identity in contract.decision_sources
        if identity not in discrepancies or discrepancies[identity].status != "resolved"
    }
    if invalid_decisions:
        raise MethodologyError(
            f"Phase 04 migration decisions are not resolved: {sorted(invalid_decisions)}"
        )
    readiness_records = {
        item.obligation_id: item for item in load_automation_readiness().obligations
    }
    unknown = set(contract.blocking_readiness_ids) - set(readiness_records)
    if unknown:
        raise MethodologyError(
            f"Phase 04 migration blockers are not readiness obligations: {sorted(unknown)}"
        )
    wrong_phase = {
        identity
        for identity in contract.blocking_readiness_ids
        if "04" not in readiness_records[identity].affected_phases
        or not readiness_records[identity].blocks_phase_completion
    }
    if wrong_phase:
        raise MethodologyError(
            f"Phase 04 migration blockers do not block Phase 04: {sorted(wrong_phase)}"
        )
    return contract


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
