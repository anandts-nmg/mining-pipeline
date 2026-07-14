"""Immutable AI artifact content, lifecycle events, and trusted construction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Literal, Protocol, TypeVar, cast

from pydantic import BaseModel, Field, field_validator, model_validator

from buduunkhad.ai.catalog import ProvenanceResolver
from buduunkhad.ai.contracts import (
    AIJob,
    AIJobStatus,
    AIRequest,
    AIResponse,
    AIResponseStatus,
    CanonicalJSONValue,
    ConfidenceComponent,
    CritiqueVerdict,
    FeatureCritique,
    FrozenModel,
    NonEmptyStr,
    PromptIdentity,
    ReviewStatus,
    RiskLevel,
    SchemaIdentity,
    SemanticVersion,
    Sha256,
    SourceReference,
    TaskType,
    require_aware_datetime,
)
from buduunkhad.ai.fingerprint import (
    canonical_json_text,
    canonical_value_from_text,
    persisted_model_bytes,
    request_fingerprint,
    sha256_bytes,
    sha256_value,
)

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


class ArtifactContractError(ValueError):
    """Raised when artifact provenance or lifecycle invariants are inconsistent."""


ArtifactOutputT = TypeVar("ArtifactOutputT", bound=FrozenModel)


class ArtifactReference(FrozenModel):
    artifact_id: NonEmptyStr
    artifact_version: int = Field(ge=1)

    @property
    def key(self) -> tuple[str, int]:
        return (self.artifact_id, self.artifact_version)


class ActorConfigurationIdentity(FrozenModel):
    provider: NonEmptyStr
    model: NonEmptyStr
    parameters_sha256: Sha256


class ValidationCheckName(StrEnum):
    SCHEMA = "SCHEMA"
    PROVENANCE = "PROVENANCE"
    REGISTRATION = "REGISTRATION"
    GEOMETRY = "GEOMETRY"
    TOPOLOGY = "TOPOLOGY"


class ValidationCheck(FrozenModel):
    check: ValidationCheckName
    required: bool
    passed: bool
    detail: NonEmptyStr


class ValidatorRegistration(FrozenModel):
    validator_identity: NonEmptyStr
    implementation: NonEmptyStr
    implementation_version: SemanticVersion


class ValidationAttestation(FrozenModel):
    attestation_id: NonEmptyStr
    artifact: ArtifactReference
    run_id: NonEmptyStr
    phase_id: NonEmptyStr
    task_type: TaskType
    generator_job_id: NonEmptyStr
    generator_response_id: NonEmptyStr
    generator_request_fingerprint: Sha256
    validator_identity: NonEmptyStr
    implementation: NonEmptyStr
    implementation_version: SemanticVersion
    checks: tuple[ValidationCheck, ...] = Field(min_length=1)
    validated_at: datetime
    validated_content_sha256: Sha256
    findings: tuple[NonEmptyStr, ...]
    limitations: tuple[NonEmptyStr, ...]

    @field_validator("validated_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "validated_at")

    @model_validator(mode="after")
    def _unique_checks(self) -> ValidationAttestation:
        names = tuple(check.check for check in self.checks)
        if len(set(names)) != len(names):
            raise ValueError("validation attestation contains duplicate checks")
        return self


class CritiqueAttestation(FrozenModel):
    attestation_id: NonEmptyStr
    artifact: ArtifactReference
    generator_job_id: NonEmptyStr
    critic_job_id: NonEmptyStr
    critic_response_id: NonEmptyStr
    critic_request_fingerprint: Sha256
    output_schema: SchemaIdentity
    critic_configuration: ActorConfigurationIdentity
    critiqued_content_sha256: Sha256
    independent_critic_policy_passed: bool
    findings: tuple[NonEmptyStr, ...]
    disposition: CritiqueVerdict
    critiqued_at: datetime

    @field_validator("critiqued_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "critiqued_at")


class GeneratorCriticWaiver(FrozenModel):
    waiver_id: NonEmptyStr
    artifact: ArtifactReference
    generator_job_id: NonEmptyStr
    critic_job_id: NonEmptyStr
    generator_configuration: ActorConfigurationIdentity
    critic_configuration: ActorConfigurationIdentity
    approved_by: NonEmptyStr
    approved_at: datetime
    reason: NonEmptyStr

    @field_validator("approved_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "approved_at")

    @model_validator(mode="after")
    def _only_for_reused_configuration(self) -> GeneratorCriticWaiver:
        if self.generator_job_id == self.critic_job_id:
            raise ValueError("waiver cannot identify one job as generator and critic")
        if self.generator_configuration != self.critic_configuration:
            raise ValueError("generator/critic waiver is valid only for reused configuration")
        return self


class ReviewerAuthorization(FrozenModel):
    authorization_id: NonEmptyStr
    reviewer_id: NonEmptyStr
    reviewer_name: NonEmptyStr
    authorizer_identity: NonEmptyStr
    authorized: bool
    authorized_at: datetime
    qualification: NonEmptyStr

    @field_validator("authorized_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "authorized_at")


class ReviewerAuthorizer(Protocol):
    def authorize(self, reviewer_id: str, *, reviewed_at: datetime) -> ReviewerAuthorization: ...


class AIArtifactContentRecord(FrozenModel):
    """Immutable artifact payload and provenance, independent of lifecycle state."""

    reference: ArtifactReference
    parent_artifacts: tuple[ArtifactReference, ...]
    run_id: NonEmptyStr
    phase_id: NonEmptyStr
    job_id: NonEmptyStr
    request_id: NonEmptyStr
    request_fingerprint: Sha256
    task_type: TaskType
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    prompt: PromptIdentity
    output_schema: SchemaIdentity
    provider: NonEmptyStr
    model: NonEmptyStr
    provider_response_id: NonEmptyStr
    generator_job_id: NonEmptyStr
    critic_job_id: NonEmptyStr
    generator_configuration: ActorConfigurationIdentity
    critic_configuration: ActorConfigurationIdentity
    payload_canonical_json: NonEmptyStr
    content_sha256: Sha256
    created_at: datetime
    confidence_components: tuple[ConfidenceComponent, ...] = Field(min_length=1)
    limitations: tuple[NonEmptyStr, ...]
    risk_level: RiskLevel
    evidence_status: NonEmptyStr

    @field_validator("created_at")
    @classmethod
    def _aware_created_at(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")

    @model_validator(mode="after")
    def _content_and_lineage_consistency(self) -> AIArtifactContentRecord:
        canonical_value_from_text(self.payload_canonical_json)
        if sha256_bytes(self.payload_canonical_json.encode("utf-8")) != self.content_sha256:
            raise ValueError("content_sha256 does not match payload_canonical_json")
        if self.job_id != self.generator_job_id:
            raise ValueError("artifact job_id must identify the generator job")
        if self.generator_job_id == self.critic_job_id:
            raise ValueError("generator and critic must be distinct jobs")
        parent_keys = tuple(parent.key for parent in self.parent_artifacts)
        if len(set(parent_keys)) != len(parent_keys):
            raise ValueError("duplicate parent artifact lineage")
        if self.reference.key in parent_keys:
            raise ValueError("artifact cannot name itself as a parent")
        source_ids = tuple(source.asset_id for source in self.source_references)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("duplicate source asset lineage")
        return self


class ArtifactCreatedEvent(FrozenModel):
    kind: Literal["CREATED"] = "CREATED"
    artifact: ArtifactReference
    content_sha256: Sha256
    generator_job_id: NonEmptyStr
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "occurred_at")


class ArtifactValidatedEvent(FrozenModel):
    kind: Literal["VALIDATED"] = "VALIDATED"
    artifact: ArtifactReference
    content_sha256: Sha256
    validation: ValidationAttestation
    critique: CritiqueAttestation
    waiver: GeneratorCriticWaiver | None = None
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "occurred_at")


class CritiqueRejectionBasis(FrozenModel):
    kind: Literal["CRITIQUE"] = "CRITIQUE"
    critique: CritiqueAttestation


class ValidationRejectionBasis(FrozenModel):
    kind: Literal["VALIDATION"] = "VALIDATION"
    validation: ValidationAttestation


class HumanRejectionBasis(FrozenModel):
    kind: Literal["HUMAN"] = "HUMAN"
    authorization: ReviewerAuthorization

    @model_validator(mode="after")
    def _authorized_reviewer(self) -> HumanRejectionBasis:
        if not self.authorization.authorized:
            raise ValueError("human rejection requires an authorized reviewer")
        return self


RejectionBasis = Annotated[
    CritiqueRejectionBasis | ValidationRejectionBasis | HumanRejectionBasis,
    Field(discriminator="kind"),
]


class ArtifactRejectedEvent(FrozenModel):
    kind: Literal["REJECTED"] = "REJECTED"
    artifact: ArtifactReference
    content_sha256: Sha256
    basis: RejectionBasis
    note: NonEmptyStr
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "occurred_at")

    @model_validator(mode="after")
    def _valid_basis_time(self) -> ArtifactRejectedEvent:
        if isinstance(self.basis, CritiqueRejectionBasis):
            if self.basis.critique.critiqued_at > self.occurred_at:
                raise ValueError("critique cannot postdate its rejection event")
        elif isinstance(self.basis, ValidationRejectionBasis):
            if self.basis.validation.validated_at > self.occurred_at:
                raise ValueError("validation cannot postdate its rejection event")
        elif self.basis.authorization.authorized_at > self.occurred_at:
            raise ValueError("reviewer authorization cannot postdate rejection")
        return self


class HumanApprovalAttestation(FrozenModel):
    kind: Literal["APPROVED"] = "APPROVED"
    artifact: ArtifactReference
    content_sha256: Sha256
    authorization: ReviewerAuthorization
    reviewed_at: datetime
    review_note: NonEmptyStr

    @field_validator("reviewed_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "reviewed_at")

    @model_validator(mode="after")
    def _authorized_reviewer(self) -> HumanApprovalAttestation:
        if not self.authorization.authorized:
            raise ValueError("reviewer authorization must be successful")
        if self.authorization.authorized_at > self.reviewed_at:
            raise ValueError("reviewer authorization cannot postdate approval")
        return self


ReviewEvent = Annotated[
    ArtifactCreatedEvent
    | ArtifactValidatedEvent
    | ArtifactRejectedEvent
    | HumanApprovalAttestation,
    Field(discriminator="kind"),
]


class AIArtifact(FrozenModel):
    """Immutable content plus a structurally valid lifecycle history.

    Authority is established only by ``validate_artifact_authority`` or a catalog
    operation using a trusted resolver.
    """

    content: AIArtifactContentRecord
    events: tuple[ReviewEvent, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _valid_history(self) -> AIArtifact:
        _validate_event_history(self.content, self.events)
        return self

    @property
    def review_status(self) -> ReviewStatus:
        """Return structural status; authoritative effective status needs a resolver."""
        return _validate_event_history(self.content, self.events)


class SupersessionRecord(FrozenModel):
    """Non-authoritative until inserted through a trusted catalog boundary."""

    supersession_id: NonEmptyStr
    superseded: ArtifactReference
    replacement: ArtifactReference
    reviewer_authorization: ReviewerAuthorization
    superseded_at: datetime
    note: NonEmptyStr

    @field_validator("superseded_at")
    @classmethod
    def _aware_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "superseded_at")

    @model_validator(mode="after")
    def _distinct_replacement(self) -> SupersessionRecord:
        if self.superseded.key == self.replacement.key:
            raise ValueError("an artifact version cannot supersede itself")
        if (
            self.superseded.artifact_id == self.replacement.artifact_id
            and self.replacement.artifact_version <= self.superseded.artifact_version
        ):
            raise ValueError("replacement version must increase within an artifact lineage")
        if not self.reviewer_authorization.authorized:
            raise ValueError("supersession requires reviewer authorization")
        if self.reviewer_authorization.authorized_at > self.superseded_at:
            raise ValueError("reviewer authorization cannot postdate supersession")
        return self


def create_draft_artifact(content: AIArtifactContentRecord) -> AIArtifact:
    created = ArtifactCreatedEvent(
        artifact=content.reference,
        content_sha256=content.content_sha256,
        generator_job_id=content.generator_job_id,
        occurred_at=content.created_at,
    )
    return AIArtifact(content=content, events=(created,))


def build_artifact(
    *,
    reference: ArtifactReference,
    parent_artifacts: tuple[ArtifactReference, ...],
    payload: ArtifactOutputT,
    generator_job: AIJob,
    critic_job: AIJob,
    request: AIRequest,
    response: AIResponse[ArtifactOutputT],
    source_references: tuple[SourceReference, ...],
    resolver: ProvenanceResolver,
    confidence_components: tuple[ConfidenceComponent, ...],
    limitations: tuple[str, ...],
    risk_level: RiskLevel,
    evidence_status: str,
    validation: ValidationAttestation | None = None,
    critique: CritiqueAttestation | None = None,
    waiver: GeneratorCriticWaiver | None = None,
) -> AIArtifact:
    """Build from records resolved at the trusted boundary; caller objects are hints only."""
    fingerprint = request_fingerprint(request)
    schema_registration = resolver.resolve_schema(request.output_schema)
    resolved_prompt = resolver.resolve_prompt(request.prompt)
    if resolved_prompt.task_type is not request.task_type:
        raise ArtifactContractError("resolved prompt task does not match request task")
    if resolved_prompt.output_schema != schema_registration.identity:
        raise ArtifactContractError("locked prompt schema does not match approved schema")
    if type(payload) is not schema_registration.output_model:
        raise ArtifactContractError("payload type is not the registered output model")
    _validate_job_request_response(
        job=generator_job,
        request=request,
        response=response,
        resolver=resolver,
        expected_task=request.task_type,
        historical_prompt=False,
    )
    _validate_sources(source_references, request, resolver)
    if generator_job.completed_at is None:
        raise ArtifactContractError("generator job is missing completed_at")
    artifact_created_at = generator_job.completed_at
    _validate_parents(parent_artifacts, reference, artifact_created_at, resolver)
    if response.output is None or type(response.output) is not schema_registration.output_model:
        raise ArtifactContractError("response output type is not the registered output model")
    _validate_payload_sources(response.output, request, resolver, context="generator response")
    _validate_payload_sources(payload, request, resolver, context="artifact payload")
    if canonical_json_text(response.output) != canonical_json_text(payload):
        raise ArtifactContractError("response output and artifact payload are unrelated")

    payload_text = canonical_json_text(payload)
    content_hash = sha256_bytes(payload_text.encode("utf-8"))
    _validate_critic_records(
        critic_job=critic_job,
        generator_job=generator_job,
        reference=reference,
        content_sha256=content_hash,
        content_created_at=artifact_created_at,
        resolver=resolver,
        historical_prompts=False,
    )
    content = AIArtifactContentRecord(
        reference=reference,
        parent_artifacts=parent_artifacts,
        run_id=generator_job.run_id,
        phase_id=generator_job.phase_id,
        job_id=generator_job.job_id,
        request_id=request.request_id,
        request_fingerprint=fingerprint,
        task_type=request.task_type,
        source_references=source_references,
        prompt=request.prompt,
        output_schema=request.output_schema,
        provider=response.provider,
        model=response.model,
        provider_response_id=response.provider_response_id,
        generator_job_id=generator_job.job_id,
        critic_job_id=critic_job.job_id,
        generator_configuration=_configuration_from_job(generator_job),
        critic_configuration=_configuration_from_job(critic_job),
        payload_canonical_json=payload_text,
        content_sha256=content_hash,
        created_at=artifact_created_at,
        confidence_components=confidence_components,
        limitations=limitations,
        risk_level=risk_level,
        evidence_status=evidence_status,
    )
    artifact = create_draft_artifact(content)
    if (validation is None) != (critique is None):
        raise ArtifactContractError("validation and critique must be supplied together")
    if validation is not None and critique is not None:
        event_time = max(
            validation.validated_at,
            critique.critiqued_at,
            waiver.approved_at if waiver is not None else content.created_at,
        )
        event = ArtifactValidatedEvent(
            artifact=reference,
            content_sha256=content_hash,
            validation=validation,
            critique=critique,
            waiver=waiver,
            occurred_at=event_time,
        )
        artifact = artifact.model_copy(update={"events": (*artifact.events, event)})
        _validate_event_authority(content, event, resolver)
    elif waiver is not None:
        raise ArtifactContractError("a waiver is valid only with a validation event")
    return artifact


def validate_artifact_authority(
    artifact: AIArtifact,
    *,
    resolver: ProvenanceResolver,
) -> None:
    """Resolve and cross-check every authoritative record used by an artifact."""
    content = artifact.content
    request = resolver.resolve_request(content.request_id)
    job = resolver.resolve_job(content.generator_job_id)
    response = resolver.resolve_response(content.provider_response_id)
    _validate_job_request_response(
        job=job,
        request=request,
        response=response,
        resolver=resolver,
        expected_task=content.task_type,
        historical_prompt=True,
    )
    schema_registration = resolver.resolve_schema(content.output_schema)
    resolved_prompt = resolver.resolve_historical_prompt(content.prompt)
    if resolved_prompt.task_type is not content.task_type:
        raise ArtifactContractError("artifact prompt task mismatch")
    if resolved_prompt.output_schema != schema_registration.identity:
        raise ArtifactContractError("artifact prompt/schema binding mismatch")
    decoded = canonical_value_from_text(content.payload_canonical_json)
    try:
        payload = schema_registration.output_model.model_validate(decoded)
    except ValueError as exc:
        raise ArtifactContractError("artifact payload fails its registered schema") from exc
    if type(payload) is not schema_registration.output_model:
        raise ArtifactContractError("artifact payload resolved to the wrong model type")
    if canonical_json_text(payload) != content.payload_canonical_json:
        raise ArtifactContractError("stored payload is not the schema model's canonical payload")
    _validate_payload_sources(payload, request, resolver, context="artifact payload")
    if (
        response.output is None
        or canonical_json_text(response.output) != content.payload_canonical_json
    ):
        raise ArtifactContractError("artifact payload differs from authoritative response output")
    _validate_payload_sources(response.output, request, resolver, context="generator response")
    fingerprint = request_fingerprint(request)
    expected_content_values: tuple[tuple[str, object], ...] = (
        ("run_id", job.run_id),
        ("phase_id", job.phase_id),
        ("job_id", job.job_id),
        ("request_fingerprint", fingerprint),
        ("prompt", request.prompt),
        ("output_schema", request.output_schema),
        ("provider", response.provider),
        ("model", response.model),
        ("provider_response_id", response.provider_response_id),
        ("generator_configuration", _configuration_from_job(job)),
        ("created_at", job.completed_at),
    )
    for field_name, expected in expected_content_values:
        actual = getattr(content, field_name)
        if not _same_persisted_value(actual, expected):
            raise ArtifactContractError(f"artifact authoritative {field_name} mismatch")
    _validate_sources(content.source_references, request, resolver)
    _validate_parents(content.parent_artifacts, content.reference, content.created_at, resolver)
    critic_job = resolver.resolve_job(content.critic_job_id)
    _validate_critic_records(
        critic_job=critic_job,
        generator_job=job,
        reference=content.reference,
        content_sha256=content.content_sha256,
        content_created_at=content.created_at,
        resolver=resolver,
        historical_prompts=True,
    )
    if content.critic_configuration != _configuration_from_job(critic_job):
        raise ArtifactContractError("artifact critic configuration mismatch")
    for event in artifact.events:
        _validate_event_authority(content, event, resolver)


def _validate_event_history(
    content: AIArtifactContentRecord, events: tuple[ReviewEvent, ...]
) -> ReviewStatus:
    status: ReviewStatus | None = None
    last_time: datetime | None = None
    validated_event_time: datetime | None = None
    for index, event in enumerate(events):
        if event.artifact != content.reference or event.content_sha256 != content.content_sha256:
            raise ValueError("review event references different artifact content")
        event_time = _event_time(event)
        if last_time is not None and event_time < last_time:
            raise ValueError("review events must be chronological")
        if event_time < content.created_at:
            raise ValueError("review event cannot predate artifact creation")
        last_time = event_time
        if isinstance(event, ArtifactCreatedEvent):
            if index != 0 or status is not None:
                raise ValueError("artifact creation must be the first and only creation event")
            if event.generator_job_id != content.generator_job_id:
                raise ValueError("creation event generator job mismatch")
            if event.occurred_at != content.created_at:
                raise ValueError("creation event time must equal artifact creation time")
            status = ReviewStatus.AI_DRAFT
        elif isinstance(event, ArtifactValidatedEvent):
            if status is not ReviewStatus.AI_DRAFT:
                raise ValueError("validation requires AI_DRAFT status")
            _validate_attestations(content, event)
            if event.validation.validated_at > event.occurred_at:
                raise ValueError("validation attestation cannot postdate validation event")
            if event.critique.critiqued_at > event.occurred_at:
                raise ValueError("critique attestation cannot postdate validation event")
            if event.waiver is not None and event.waiver.approved_at > event.occurred_at:
                raise ValueError("waiver cannot postdate validation event")
            validated_event_time = event.occurred_at
            status = ReviewStatus.AI_VALIDATED
        elif isinstance(event, ArtifactRejectedEvent):
            if status not in {ReviewStatus.AI_DRAFT, ReviewStatus.AI_VALIDATED}:
                raise ValueError("rejection requires AI_DRAFT or AI_VALIDATED status")
            _validate_rejection_basis(content, event)
            status = ReviewStatus.REJECTED
        elif isinstance(event, HumanApprovalAttestation):
            if status is not ReviewStatus.AI_VALIDATED or validated_event_time is None:
                raise ValueError("approval requires AI_VALIDATED status")
            if event.authorization.authorized_at < validated_event_time:
                raise ValueError("reviewer authorization must follow AI_VALIDATED status")
            status = ReviewStatus.GEOLOGIST_APPROVED
    if status is None:
        raise ValueError("artifact history must establish AI_DRAFT")
    return status


def _validate_attestations(content: AIArtifactContentRecord, event: ArtifactValidatedEvent) -> None:
    validation = event.validation
    critique = event.critique
    _validate_validation_subject(content, validation)
    checks = {check.check: check for check in validation.checks}
    for required in _required_checks(content.task_type):
        result = checks.get(required)
        if result is None or not result.required or not result.passed:
            raise ValueError(f"required validation check did not pass: {required}")
    if any(check.required and not check.passed for check in validation.checks):
        raise ValueError("required validation checks must all pass")
    if critique.artifact != content.reference:
        raise ValueError("critique attests to a different artifact")
    if critique.critiqued_content_sha256 != content.content_sha256:
        raise ValueError("critique attests to different content")
    if critique.critiqued_at < content.created_at:
        raise ValueError("critique cannot predate artifact creation")
    if critique.generator_job_id != content.generator_job_id:
        raise ValueError("critique generator job does not match artifact provenance")
    if critique.critic_job_id != content.critic_job_id:
        raise ValueError("critique job does not match artifact provenance")
    if critique.critic_configuration != content.critic_configuration:
        raise ValueError("critique configuration does not match artifact provenance")
    if not critique.independent_critic_policy_passed:
        raise ValueError("independent critic policy did not pass")
    if critique.disposition is not CritiqueVerdict.ACCEPT_FOR_VALIDATION:
        raise ValueError("critique disposition does not allow validation")
    same_configuration = content.generator_configuration == content.critic_configuration
    if same_configuration:
        if event.waiver is None:
            raise ValueError("reused generator/critic configuration requires a waiver")
        waiver = event.waiver
        if (
            waiver.artifact != content.reference
            or waiver.generator_job_id != content.generator_job_id
            or waiver.critic_job_id != content.critic_job_id
            or waiver.generator_configuration != content.generator_configuration
            or waiver.critic_configuration != content.critic_configuration
        ):
            raise ValueError("generator/critic waiver does not match artifact provenance")
    elif event.waiver is not None:
        raise ValueError("generator/critic waiver contradicts distinct configurations")


def _validate_validation_subject(
    content: AIArtifactContentRecord,
    validation: ValidationAttestation,
) -> None:
    comparisons = (
        ("artifact", validation.artifact, content.reference),
        ("run", validation.run_id, content.run_id),
        ("phase", validation.phase_id, content.phase_id),
        ("task", validation.task_type, content.task_type),
        ("generator job", validation.generator_job_id, content.generator_job_id),
        ("generator response", validation.generator_response_id, content.provider_response_id),
        (
            "generator request fingerprint",
            validation.generator_request_fingerprint,
            content.request_fingerprint,
        ),
        ("content", validation.validated_content_sha256, content.content_sha256),
    )
    for label, actual, expected in comparisons:
        if actual != expected:
            raise ValueError(f"validation attests to different {label}")
    if validation.validated_at < content.created_at:
        raise ValueError("validation cannot predate artifact creation")


def _validate_rejection_basis(
    content: AIArtifactContentRecord,
    event: ArtifactRejectedEvent,
) -> None:
    basis = event.basis
    if isinstance(basis, CritiqueRejectionBasis):
        critique = basis.critique
        if (
            critique.artifact != content.reference
            or critique.critiqued_content_sha256 != content.content_sha256
            or critique.generator_job_id != content.generator_job_id
            or critique.critic_job_id != content.critic_job_id
            or critique.critic_configuration != content.critic_configuration
        ):
            raise ValueError("critique rejection basis does not match artifact provenance")
        if critique.disposition is not CritiqueVerdict.REJECT:
            raise ValueError("critique rejection basis must have REJECT disposition")
        if critique.critiqued_at < content.created_at:
            raise ValueError("critique rejection cannot predate artifact creation")
        return
    if isinstance(basis, ValidationRejectionBasis):
        validation = basis.validation
        _validate_validation_subject(content, validation)
        if not any(check.required and not check.passed for check in validation.checks):
            raise ValueError("validation rejection basis requires a failed required check")
        return
    if basis.authorization.authorized_at < content.created_at:
        raise ValueError("human rejection authorization cannot predate artifact creation")


def _validate_event_authority(
    content: AIArtifactContentRecord,
    event: ReviewEvent,
    resolver: ProvenanceResolver,
) -> None:
    if isinstance(event, ArtifactCreatedEvent):
        if event.occurred_at != content.created_at:
            raise ArtifactContractError("authoritative creation time mismatch")
        return
    if isinstance(event, ArtifactValidatedEvent):
        _validate_validator_registration(event.validation, resolver)
        if not _same_persisted_record(
            resolver.resolve_validation(event.validation.attestation_id),
            event.validation,
        ):
            raise ArtifactContractError("validation attestation is not authoritative")
        if not _same_persisted_record(
            resolver.resolve_critique(event.critique.attestation_id),
            event.critique,
        ):
            raise ArtifactContractError("critique attestation is not authoritative")
        if event.waiver is not None and not _same_persisted_record(
            resolver.resolve_waiver(event.waiver.waiver_id),
            event.waiver,
        ):
            raise ArtifactContractError("generator/critic waiver is not authoritative")
        _validate_validation_attestation(content, event.validation, resolver)
        _validate_critique_attestation(
            content,
            event.critique,
            event_time=event.occurred_at,
            resolver=resolver,
        )
        if event.waiver is not None:
            generator_job = resolver.resolve_job(content.generator_job_id)
            critic_job = resolver.resolve_job(content.critic_job_id)
            if event.waiver.approved_at < max(generator_job.created_at, critic_job.created_at):
                raise ArtifactContractError("waiver predates the jobs it authorizes")
        return
    if isinstance(event, ArtifactRejectedEvent):
        basis = event.basis
        if isinstance(basis, CritiqueRejectionBasis):
            critique = resolver.resolve_critique(basis.critique.attestation_id)
            if not _same_persisted_record(critique, basis.critique):
                raise ArtifactContractError("critique rejection basis is not authoritative")
            _validate_critique_attestation(
                content,
                critique,
                event_time=event.occurred_at,
                resolver=resolver,
            )
        elif isinstance(basis, ValidationRejectionBasis):
            _validate_validator_registration(basis.validation, resolver)
            validation = resolver.resolve_validation(basis.validation.attestation_id)
            if not _same_persisted_record(validation, basis.validation):
                raise ArtifactContractError("validation rejection basis is not authoritative")
            _validate_validation_attestation(content, validation, resolver)
        else:
            authorization = resolver.resolve_authorization(basis.authorization.authorization_id)
            if not _same_persisted_record(authorization, basis.authorization):
                raise ArtifactContractError("human rejection authorization is not authoritative")
        return
    if isinstance(event, HumanApprovalAttestation):
        authorization = resolver.resolve_authorization(event.authorization.authorization_id)
        if not _same_persisted_record(authorization, event.authorization):
            raise ArtifactContractError("reviewer authorization is not authoritative")


def _validate_validator_registration(
    validation: ValidationAttestation,
    resolver: ProvenanceResolver,
) -> None:
    registration = resolver.resolve_validator(validation.validator_identity)
    if (
        validation.implementation,
        validation.implementation_version,
    ) != (registration.implementation, registration.implementation_version):
        raise ArtifactContractError("validation attestation validator is not approved")


def _validate_validation_attestation(
    content: AIArtifactContentRecord,
    validation: ValidationAttestation,
    resolver: ProvenanceResolver,
) -> None:
    _validate_validator_registration(validation, resolver)
    try:
        _validate_validation_subject(content, validation)
    except ValueError as exc:
        raise ArtifactContractError(str(exc)) from exc
    generator_job = resolver.resolve_job(validation.generator_job_id)
    generator_request = resolver.resolve_request(generator_job.request_id)
    if generator_job.provider_response_id != validation.generator_response_id:
        raise ArtifactContractError("validation generator response ID mismatch")
    generator_response = resolver.resolve_response(validation.generator_response_id)
    _validate_job_request_response(
        job=generator_job,
        request=generator_request,
        response=generator_response,
        resolver=resolver,
        expected_task=content.task_type,
        historical_prompt=True,
    )
    if request_fingerprint(generator_request) != validation.generator_request_fingerprint:
        raise ArtifactContractError("validation generator request fingerprint mismatch")
    if generator_job.completed_at is None or generator_job.completed_at > validation.validated_at:
        raise ArtifactContractError("validation predates generator job completion")


def _validate_critique_attestation(
    content: AIArtifactContentRecord,
    critique: CritiqueAttestation,
    *,
    event_time: datetime,
    resolver: ProvenanceResolver,
) -> None:
    critic_job = resolver.resolve_job(critique.critic_job_id)
    critic_request = resolver.resolve_request(critic_job.request_id)
    generator_job = resolver.resolve_job(content.generator_job_id)
    _validate_critic_records(
        critic_job=critic_job,
        generator_job=generator_job,
        reference=content.reference,
        content_sha256=content.content_sha256,
        content_created_at=content.created_at,
        resolver=resolver,
        historical_prompts=True,
    )
    if critique.artifact != content.reference:
        raise ArtifactContractError("critique attestation subject mismatch")
    if critique.generator_job_id != content.generator_job_id:
        raise ArtifactContractError("critique attestation generator job mismatch")
    if critique.critic_job_id != content.critic_job_id:
        raise ArtifactContractError("critique attestation critic job mismatch")
    if critique.critiqued_content_sha256 != content.content_sha256:
        raise ArtifactContractError("critique attestation content mismatch")
    if critique.critic_configuration != _configuration_from_job(critic_job):
        raise ArtifactContractError("critique attestation critic configuration mismatch")
    if request_fingerprint(critic_request) != critique.critic_request_fingerprint:
        raise ArtifactContractError("critique attestation request fingerprint mismatch")
    if critic_job.provider_response_id != critique.critic_response_id:
        raise ArtifactContractError("critique attestation response ID mismatch")
    response = resolver.resolve_response(critique.critic_response_id)
    if response.output_schema != critique.output_schema:
        raise ArtifactContractError("critique attestation schema mismatch")
    if response.created_at > critique.critiqued_at:
        raise ArtifactContractError("critique attestation predates the critic response")
    if not isinstance(response.output, FeatureCritique):
        raise ArtifactContractError("critic response is not a FeatureCritique")
    if response.output.verdict is not critique.disposition:
        raise ArtifactContractError("critique disposition differs from critic response")
    if response.output.feature_id != content.reference.artifact_id:
        raise ArtifactContractError("critic response subject differs from artifact identity")
    if response.output.findings != critique.findings:
        raise ArtifactContractError("critique findings differ from critic response")
    if critic_job.completed_at is None:
        raise ArtifactContractError("successful critique requires critic job completion")
    if not (critic_job.completed_at <= critique.critiqued_at <= event_time):
        raise ArtifactContractError("critic completion, critique, and event order is invalid")


def _required_checks(task_type: TaskType) -> tuple[ValidationCheckName, ...]:
    checks = [ValidationCheckName.SCHEMA, ValidationCheckName.PROVENANCE]
    if task_type in {
        TaskType.IMAGE_RASTER_INTERPRETATION,
        TaskType.GEOLOGICAL_FEATURE_PROPOSAL,
    }:
        checks.extend((ValidationCheckName.REGISTRATION, ValidationCheckName.GEOMETRY))
    if task_type is TaskType.GEOLOGICAL_FEATURE_PROPOSAL:
        checks.append(ValidationCheckName.TOPOLOGY)
    return tuple(checks)


def _event_time(event: ReviewEvent) -> datetime:
    if isinstance(event, HumanApprovalAttestation):
        return event.reviewed_at
    return event.occurred_at


def _configuration_from_job(job: AIJob) -> ActorConfigurationIdentity:
    return ActorConfigurationIdentity(
        provider=job.provider,
        model=job.model,
        parameters_sha256=job.provider_parameters_sha256,
    )


def _validate_job_request_response(
    *,
    job: AIJob,
    request: AIRequest,
    response: AIResponse,
    resolver: ProvenanceResolver,
    expected_task: TaskType,
    historical_prompt: bool,
) -> None:
    if not _same_persisted_record(resolver.resolve_job(job.job_id), job):
        raise ArtifactContractError("job differs from the authoritative record")
    if not _same_persisted_record(resolver.resolve_request(request.request_id), request):
        raise ArtifactContractError("request differs from the authoritative record")
    if not _same_persisted_record(
        resolver.resolve_response(response.provider_response_id),
        response,
    ):
        raise ArtifactContractError("response differs from the authoritative record")
    fingerprint = request_fingerprint(request)
    if job.status is not AIJobStatus.SUCCEEDED or response.status is not AIResponseStatus.SUCCESS:
        raise ArtifactContractError("artifact-linked job and response must both succeed")
    if job.provider_response_id != response.provider_response_id:
        raise ArtifactContractError("job provider response ID mismatch")
    if job.request_id != request.request_id or job.request_fingerprint != fingerprint:
        raise ArtifactContractError("job is unrelated to the request")
    if request.job_id != job.job_id:
        raise ArtifactContractError("request job identity mismatch")
    if not (job.task_type is request.task_type is response.task_type is expected_task):
        raise ArtifactContractError("job, request, response, and artifact task types must match")
    expected_run_phase = (job.run_id, job.phase_id)
    if (request.run_id, request.phase_id) != expected_run_phase:
        raise ArtifactContractError("request run/phase differs from job")
    if (response.run_id, response.phase_id) != expected_run_phase:
        raise ArtifactContractError("response run/phase differs from job")
    if (response.request_id, response.job_id) != (request.request_id, job.job_id):
        raise ArtifactContractError("response request/job identity mismatch")
    if response.request_fingerprint != fingerprint:
        raise ArtifactContractError("response fingerprint is unrelated to request")
    if (
        job.output_schema != request.output_schema
        or response.output_schema != request.output_schema
    ):
        raise ArtifactContractError("job/request/response output schema mismatch")
    if (job.provider, job.model) != (request.provider.provider, request.provider.model):
        raise ArtifactContractError("job provider/model differs from request")
    if (response.provider, response.model) != (job.provider, job.model):
        raise ArtifactContractError("response provider/model differs from job")
    if job.provider_parameters_sha256 != sha256_value(request.provider.parameters):
        raise ArtifactContractError("job parameters differ from request")
    if job.usage != response.usage:
        raise ArtifactContractError("job usage differs from provider response")
    if job.started_at is None or job.completed_at is None:
        raise ArtifactContractError("successful job is missing lifecycle timestamps")
    if not (
        request.created_at
        <= job.created_at
        <= job.started_at
        <= response.created_at
        <= job.completed_at
    ):
        raise ArtifactContractError("request/job/response timestamps violate causal order")
    prompt = (
        resolver.resolve_historical_prompt(request.prompt)
        if historical_prompt
        else resolver.resolve_prompt(request.prompt)
    )
    if prompt.task_type is not request.task_type:
        raise ArtifactContractError("request prompt task mismatch")
    schema = resolver.resolve_schema(request.output_schema)
    if prompt.output_schema != schema.identity:
        raise ArtifactContractError("request prompt/schema binding mismatch")
    if response.output is None or type(response.output) is not schema.output_model:
        raise ArtifactContractError("response output has the wrong registered model type")


def _validate_critic_records(
    *,
    critic_job: AIJob,
    generator_job: AIJob,
    reference: ArtifactReference,
    content_sha256: str,
    content_created_at: datetime,
    resolver: ProvenanceResolver,
    historical_prompts: bool,
) -> None:
    if critic_job.job_id == generator_job.job_id:
        raise ArtifactContractError("generator and critic must be different jobs")
    if (critic_job.run_id, critic_job.phase_id) != (
        generator_job.run_id,
        generator_job.phase_id,
    ):
        raise ArtifactContractError("critic job is unrelated to generator run and phase")
    generator_request = resolver.resolve_request(generator_job.request_id)
    critic_request = resolver.resolve_request(critic_job.request_id)
    _validate_sources(critic_request.source_references, critic_request, resolver)
    if critic_request.source_references != generator_request.source_references:
        raise ArtifactContractError("critic sources differ from generator sources")
    if critic_job.provider_response_id is None:
        raise ArtifactContractError("critic job has no provider response")
    critic_response = resolver.resolve_response(critic_job.provider_response_id)
    _validate_job_request_response(
        job=critic_job,
        request=critic_request,
        response=critic_response,
        resolver=resolver,
        expected_task=TaskType.FEATURE_CRITIQUE,
        historical_prompt=historical_prompts,
    )
    subject = critic_request.subject
    if subject is None:
        raise ArtifactContractError("critic request has no artifact subject")
    if (
        subject.artifact_id,
        subject.artifact_version,
        subject.content_sha256,
        subject.generator_job_id,
    ) != (
        reference.artifact_id,
        reference.artifact_version,
        content_sha256,
        generator_job.job_id,
    ):
        raise ArtifactContractError("critic request subject is unrelated to artifact content")
    if critic_request.created_at < content_created_at:
        raise ArtifactContractError("critic request predates artifact content")
    schema = resolver.resolve_schema(critic_request.output_schema)
    if schema.output_model is not FeatureCritique:
        raise ArtifactContractError("critic request schema is not FeatureCritique")
    if not isinstance(critic_response.output, FeatureCritique):
        raise ArtifactContractError("critic response is not a FeatureCritique")
    _validate_payload_sources(
        critic_response.output,
        critic_request,
        resolver,
        context="critic response",
    )
    if critic_response.output.feature_id != reference.artifact_id:
        raise ArtifactContractError("critic response subject differs from artifact identity")


def _validate_sources(
    supplied: tuple[SourceReference, ...],
    request: AIRequest,
    resolver: ProvenanceResolver,
) -> None:
    if tuple(persisted_model_bytes(source) for source in supplied) != tuple(
        persisted_model_bytes(source) for source in request.source_references
    ):
        raise ArtifactContractError("artifact sources differ from request sources")
    for source in supplied:
        if not _same_persisted_record(resolver.resolve_source(source.asset_id), source):
            raise ArtifactContractError(f"source hash/reference mismatch: {source.asset_id}")


def _validate_payload_sources(
    payload: object,
    request: AIRequest,
    resolver: ProvenanceResolver,
    *,
    context: str,
) -> None:
    requested = {source.asset_id: source for source in request.source_references}
    for source in _collect_source_references(payload):
        authoritative = resolver.resolve_source(source.asset_id)
        if not _same_persisted_record(authoritative, source):
            raise ArtifactContractError(
                f"{context} source hash/locator mismatch: {source.asset_id}"
            )
        requested_source = requested.get(source.asset_id)
        if requested_source is None or not _same_persisted_record(requested_source, source):
            raise ArtifactContractError(
                f"{context} contains an unrequested source reference: {source.asset_id}"
            )


def _collect_source_references(value: object) -> tuple[SourceReference, ...]:
    found: list[SourceReference] = []
    active: set[int] = set()

    def visit(item: object) -> None:
        if isinstance(item, SourceReference):
            found.append(item)
            return
        if isinstance(item, CanonicalJSONValue):
            visit(item.to_python())
            return
        if type(item) is dict and set(item) == {"asset_id", "sha256", "locators"}:
            try:
                found.append(SourceReference.model_validate(item))
            except ValueError as exc:
                raise ArtifactContractError(
                    "schema-bound payload contains a malformed source reference"
                ) from exc
            return
        if item is None or type(item) in {bool, int, float, str, bytes}:
            return
        container = isinstance(item, (BaseModel, Mapping, tuple, list, set, frozenset))
        container = container or (is_dataclass(item) and not isinstance(item, type))
        if not container:
            return
        identity = id(item)
        if identity in active:
            raise ArtifactContractError("cyclic schema-bound payload is unsupported")
        active.add(identity)
        try:
            if isinstance(item, BaseModel):
                for field_name in type(item).model_fields:
                    visit(getattr(item, field_name))
            elif isinstance(item, Mapping):
                for key, nested in item.items():
                    visit(key)
                    visit(nested)
            elif isinstance(item, (tuple, list, set, frozenset)):
                for nested in item:
                    visit(nested)
            else:
                for field in dataclass_fields(cast("DataclassInstance", item)):
                    visit(getattr(item, field.name))
        finally:
            active.remove(identity)

    visit(value)
    return tuple(found)


def _validate_parents(
    parents: tuple[ArtifactReference, ...],
    reference: ArtifactReference,
    created_at: datetime,
    resolver: ProvenanceResolver,
) -> None:
    for parent in parents:
        if parent == reference:
            raise ArtifactContractError("artifact cannot be its own parent")
        resolved = resolver.resolve_artifact(parent)
        if resolved.content.reference != parent:
            raise ArtifactContractError("parent resolver returned the wrong artifact version")
        if resolved.content.created_at > created_at:
            raise ArtifactContractError("parent artifact cannot postdate child creation")


def _same_persisted_record(left: FrozenModel, right: FrozenModel) -> bool:
    return persisted_model_bytes(left) == persisted_model_bytes(right)


def _same_persisted_value(left: object, right: object) -> bool:
    if isinstance(left, FrozenModel) and isinstance(right, FrozenModel):
        return _same_persisted_record(left, right)
    if isinstance(left, datetime) and isinstance(right, datetime):
        return left.isoformat() == right.isoformat() and left.fold == right.fold
    return left == right
