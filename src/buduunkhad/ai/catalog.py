"""Trusted offline resolver protocols and in-memory PR 1 implementations."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Protocol, TypeVar

from buduunkhad.ai.contracts import (
    AIJob,
    AIRequest,
    AIResponse,
    FrozenModel,
    PromptIdentity,
    SchemaIdentity,
    SourceReference,
)
from buduunkhad.ai.fingerprint import (
    persisted_model_bytes,
    persisted_model_sha256,
    request_fingerprint,
    sha256_value,
)
from buduunkhad.ai.providers.base import (
    AIProviderError,
    prohibit_provider_approval,
    validate_provider_output_contract,
    validation_error_details,
)

if TYPE_CHECKING:
    from buduunkhad.ai.artifacts import (
        AIArtifact,
        ArtifactReference,
        CritiqueAttestation,
        GeneratorCriticWaiver,
        ReviewerAuthorization,
        ReviewerAuthorizer,
        SupersessionRecord,
        ValidationAttestation,
        ValidatorRegistration,
    )
    from buduunkhad.ai.prompts import (
        PromptRegistry,
        ResolvedPrompt,
        SchemaRegistration,
        SchemaRegistry,
    )


class ArtifactResolutionError(LookupError):
    """Raised when an authoritative record cannot be resolved unambiguously."""


class ArtifactIdentityCollisionError(ValueError):
    """Raised when two records claim the same authoritative identity."""


class ArtifactResolver(Protocol):
    def resolve_artifact(self, reference: ArtifactReference) -> AIArtifact: ...

    def resolve_supersession(self, reference: ArtifactReference) -> SupersessionRecord | None: ...


class SourceAssetResolver(Protocol):
    """Trusted source-identity boundary; durable implementation is deferred."""

    def resolve_source(self, asset_id: str) -> SourceReference: ...


class ValidationAttestationResolver(Protocol):
    """Trusted validation-attestation issuance boundary."""

    def resolve_validation(self, attestation_id: str) -> ValidationAttestation: ...


class ProvenanceResolver(ArtifactResolver, SourceAssetResolver, Protocol):
    """Trust boundary used by artifact and lifecycle operations."""

    def resolve_request(self, request_id: str) -> AIRequest: ...

    def resolve_job(self, job_id: str) -> AIJob: ...

    def resolve_response(self, provider_response_id: str) -> AIResponse: ...

    def resolve_prompt(self, identity: PromptIdentity) -> ResolvedPrompt: ...

    def resolve_historical_prompt(self, identity: PromptIdentity) -> ResolvedPrompt: ...

    def resolve_schema(self, identity: SchemaIdentity) -> SchemaRegistration: ...

    def resolve_validation(self, attestation_id: str) -> ValidationAttestation: ...

    def resolve_validator(self, validator_identity: str) -> ValidatorRegistration: ...

    def resolve_critique(self, attestation_id: str) -> CritiqueAttestation: ...

    def resolve_waiver(self, waiver_id: str) -> GeneratorCriticWaiver: ...

    def resolve_authorization(self, authorization_id: str) -> ReviewerAuthorization: ...


class InMemoryArtifactCatalog:
    """Append-only content catalog with validated lifecycle replacements."""

    def __init__(self) -> None:
        self._artifacts: dict[tuple[str, int], AIArtifact] = {}
        self._supersessions: dict[tuple[str, int], SupersessionRecord] = {}

    def add_artifact(self, artifact: AIArtifact, *, resolver: ProvenanceResolver) -> None:
        from buduunkhad.ai.artifacts import validate_artifact_authority

        key = artifact.content.reference.key
        if key in self._artifacts:
            raise ArtifactIdentityCollisionError(
                f"artifact identity/version already exists: {key[0]}@{key[1]}"
            )
        persisted_model_sha256(artifact)
        validate_artifact_authority(artifact, resolver=resolver)
        self._artifacts[key] = artifact

    def update_artifact(self, artifact: AIArtifact, *, resolver: ProvenanceResolver) -> None:
        """Append lifecycle events while preserving the exact content bytes."""
        from buduunkhad.ai.artifacts import validate_artifact_authority

        key = artifact.content.reference.key
        try:
            current = self._artifacts[key]
        except KeyError as exc:
            raise ArtifactResolutionError(f"artifact not found: {key[0]}@{key[1]}") from exc
        if persisted_model_sha256(current.content) != persisted_model_sha256(artifact.content):
            raise ArtifactIdentityCollisionError("catalog update cannot replace artifact content")
        prefix = artifact.events[: len(current.events)]
        prefix_digests = tuple(persisted_model_sha256(event) for event in prefix)
        current_digests = tuple(persisted_model_sha256(event) for event in current.events)
        if prefix_digests != current_digests or len(artifact.events) <= len(current.events):
            raise ArtifactIdentityCollisionError("catalog update must append lifecycle events")
        validate_artifact_authority(artifact, resolver=resolver)
        self._artifacts[key] = artifact

    def resolve_artifact(self, reference: ArtifactReference) -> AIArtifact:
        try:
            return self._artifacts[reference.key]
        except KeyError as exc:
            raise ArtifactResolutionError(
                f"artifact not found: {reference.artifact_id}@{reference.artifact_version}"
            ) from exc

    def add_supersession(
        self,
        record: SupersessionRecord,
        *,
        resolver: ProvenanceResolver,
    ) -> None:
        from buduunkhad.ai.review import validate_supersession_record

        key = record.superseded.key
        if key in self._supersessions:
            raise ArtifactIdentityCollisionError(
                f"artifact already has a supersession: {key[0]}@{key[1]}"
            )
        persisted_model_sha256(record)
        validate_supersession_record(record, resolver=resolver)
        self._supersessions[key] = record

    def resolve_supersession(self, reference: ArtifactReference) -> SupersessionRecord | None:
        return self._supersessions.get(reference.key)


class InMemorySourceAssetCatalog:
    """Explicit offline trust root for registered synthetic source identities."""

    def __init__(self, sources: tuple[SourceReference, ...]) -> None:
        self._sources = _unique_records(sources, lambda value: value.asset_id, "source asset")

    def resolve_source(self, asset_id: str) -> SourceReference:
        return _resolve(self._sources, asset_id, "source asset")


class InMemoryValidationAttestationCatalog:
    """Explicit offline issuer for deterministic validation attestations."""

    def __init__(self, validations: tuple[ValidationAttestation, ...]) -> None:
        self._validations = _unique_records(
            validations,
            lambda value: value.attestation_id,
            "validation attestation",
        )

    def resolve_validation(self, attestation_id: str) -> ValidationAttestation:
        return _resolve(self._validations, attestation_id, "validation attestation")


class InMemoryProvenanceResolver:
    """Authoritative in-memory records used by offline tests and examples only."""

    def __init__(
        self,
        *,
        jobs: tuple[AIJob, ...],
        requests: tuple[AIRequest, ...],
        responses: tuple[AIResponse, ...],
        sources: tuple[SourceReference, ...],
        source_resolver: SourceAssetResolver,
        prompt_registry: PromptRegistry,
        schema_registry: SchemaRegistry,
        artifact_resolver: ArtifactResolver | None = None,
        validations: tuple[ValidationAttestation, ...] = (),
        validators: tuple[ValidatorRegistration, ...] = (),
        critiques: tuple[CritiqueAttestation, ...] = (),
        waivers: tuple[GeneratorCriticWaiver, ...] = (),
        authorizations: tuple[ReviewerAuthorization, ...] = (),
        validation_resolver: ValidationAttestationResolver | None = None,
        authorization_authorizer: ReviewerAuthorizer | None = None,
    ) -> None:
        self._jobs = _unique_records(jobs, lambda value: value.job_id, "job")
        self._requests = _unique_records(requests, lambda value: value.request_id, "request")
        self._responses = _unique_records(
            responses,
            lambda value: value.provider_response_id,
            "provider response",
        )
        self._sources = _unique_records(sources, lambda value: value.asset_id, "source asset")
        self._validations = _unique_records(
            validations, lambda value: value.attestation_id, "validation attestation"
        )
        self._validators = _unique_records(
            validators, lambda value: value.validator_identity, "validator registration"
        )
        self._critiques = _unique_records(
            critiques, lambda value: value.attestation_id, "critique attestation"
        )
        self._waivers = _unique_records(waivers, lambda value: value.waiver_id, "waiver")
        self._authorizations = _unique_records(
            authorizations,
            lambda value: value.authorization_id,
            "reviewer authorization",
        )
        for source in self._sources.values():
            authoritative_source = source_resolver.resolve_source(source.asset_id)
            if persisted_model_bytes(authoritative_source) != persisted_model_bytes(source):
                raise ArtifactIdentityCollisionError(
                    "source bootstrap differs from the trusted source resolver"
                )
        if self._validations and validation_resolver is None:
            raise ArtifactIdentityCollisionError(
                "validation bootstrap requires a trusted attestation resolver"
            )
        if validation_resolver is not None:
            for validation in self._validations.values():
                authoritative_validation = validation_resolver.resolve_validation(
                    validation.attestation_id
                )
                if persisted_model_bytes(authoritative_validation) != persisted_model_bytes(
                    validation
                ):
                    raise ArtifactIdentityCollisionError(
                        "validation bootstrap differs from the trusted attestation resolver"
                    )
        if self._authorizations and authorization_authorizer is None:
            raise ArtifactIdentityCollisionError(
                "authorization bootstrap requires a trusted reviewer authorizer"
            )
        if authorization_authorizer is not None:
            for authorization in self._authorizations.values():
                issued = authorization_authorizer.authorize(
                    authorization.reviewer_id,
                    reviewed_at=authorization.authorized_at,
                )
                if persisted_model_bytes(issued) != persisted_model_bytes(authorization):
                    raise ArtifactIdentityCollisionError(
                        "authorization bootstrap differs from the trusted authorizer"
                    )
        self._prompt_registry = prompt_registry
        self._schema_registry = schema_registry
        self._artifact_resolver = artifact_resolver
        for request in self._requests.values():
            self._validate_request_record(request, historical=True)
        for job in self._jobs.values():
            self._validate_job_record(job)
        for response in self._responses.values():
            self._validate_response_record(response)
        for validation in self._validations.values():
            self._validate_validation_record(validation)
        for critique in self._critiques.values():
            self._validate_critique_record(critique)

    def add_source(
        self,
        source: SourceReference,
        *,
        source_resolver: SourceAssetResolver,
    ) -> None:
        authoritative = source_resolver.resolve_source(source.asset_id)
        if persisted_model_bytes(authoritative) != persisted_model_bytes(source):
            raise ArtifactIdentityCollisionError(
                "source record was not issued by the trusted source resolver"
            )
        _insert_record(self._sources, source.asset_id, source, "source asset")

    def add_request(self, request: AIRequest) -> None:
        self._validate_request_record(request, historical=False)
        _insert_record(self._requests, request.request_id, request, "request")

    def add_historical_request(self, request: AIRequest) -> None:
        """Load a persisted request whose exact locked prompt may now be deprecated."""
        self._validate_request_record(request, historical=True)
        _insert_record(self._requests, request.request_id, request, "request")

    def add_job(self, job: AIJob) -> None:
        self._validate_job_record(job)
        _insert_record(self._jobs, job.job_id, job, "job")

    def add_response(self, response: AIResponse) -> None:
        self._validate_response_record(response)
        _insert_record(
            self._responses,
            response.provider_response_id,
            response,
            "provider response",
        )

    def add_validation(
        self,
        validation: ValidationAttestation,
        *,
        validation_resolver: ValidationAttestationResolver,
    ) -> None:
        issued = validation_resolver.resolve_validation(validation.attestation_id)
        if persisted_model_bytes(issued) != persisted_model_bytes(validation):
            raise ArtifactIdentityCollisionError(
                "validation attestation was not issued by the trusted resolver"
            )
        self._validate_validation_record(validation)
        _insert_record(
            self._validations,
            validation.attestation_id,
            validation,
            "validation attestation",
        )

    def add_critique(self, critique: CritiqueAttestation) -> None:
        self._validate_critique_record(critique)
        _insert_record(
            self._critiques,
            critique.attestation_id,
            critique,
            "critique attestation",
        )

    def add_waiver(self, waiver: GeneratorCriticWaiver) -> None:
        _insert_record(self._waivers, waiver.waiver_id, waiver, "waiver")

    def add_authorization(
        self,
        authorization: ReviewerAuthorization,
        *,
        authorizer: ReviewerAuthorizer,
        reviewed_at: datetime,
    ) -> None:
        issued = authorizer.authorize(authorization.reviewer_id, reviewed_at=reviewed_at)
        if persisted_model_bytes(issued) != persisted_model_bytes(authorization):
            raise ArtifactIdentityCollisionError(
                "reviewer authorization was not issued by the trusted authorizer"
            )
        _insert_record(
            self._authorizations,
            authorization.authorization_id,
            authorization,
            "reviewer authorization",
        )

    def resolve_job(self, job_id: str) -> AIJob:
        return _resolve(self._jobs, job_id, "job")

    def resolve_request(self, request_id: str) -> AIRequest:
        return _resolve(self._requests, request_id, "request")

    def resolve_response(self, provider_response_id: str) -> AIResponse:
        return _resolve(self._responses, provider_response_id, "provider response")

    def resolve_source(self, asset_id: str) -> SourceReference:
        return _resolve(self._sources, asset_id, "source asset")

    def resolve_prompt(self, identity: PromptIdentity) -> ResolvedPrompt:
        return self._prompt_registry.resolve(identity)

    def resolve_historical_prompt(self, identity: PromptIdentity) -> ResolvedPrompt:
        return self._prompt_registry.resolve_historical(identity)

    def resolve_schema(self, identity: SchemaIdentity) -> SchemaRegistration:
        return self._schema_registry.resolve(identity)

    def resolve_validation(self, attestation_id: str) -> ValidationAttestation:
        return _resolve(self._validations, attestation_id, "validation attestation")

    def resolve_validator(self, validator_identity: str) -> ValidatorRegistration:
        return _resolve(self._validators, validator_identity, "validator registration")

    def resolve_critique(self, attestation_id: str) -> CritiqueAttestation:
        return _resolve(self._critiques, attestation_id, "critique attestation")

    def resolve_waiver(self, waiver_id: str) -> GeneratorCriticWaiver:
        return _resolve(self._waivers, waiver_id, "waiver")

    def resolve_authorization(self, authorization_id: str) -> ReviewerAuthorization:
        return _resolve(self._authorizations, authorization_id, "reviewer authorization")

    def resolve_artifact(self, reference: ArtifactReference) -> AIArtifact:
        if self._artifact_resolver is None:
            raise ArtifactResolutionError("no authoritative artifact catalog is configured")
        return self._artifact_resolver.resolve_artifact(reference)

    def resolve_supersession(self, reference: ArtifactReference) -> SupersessionRecord | None:
        if self._artifact_resolver is None:
            raise ArtifactResolutionError("no authoritative artifact catalog is configured")
        return self._artifact_resolver.resolve_supersession(reference)

    def _validate_request_record(self, request: AIRequest, *, historical: bool) -> None:
        for source in request.source_references:
            if self.resolve_source(source.asset_id) != source:
                raise ArtifactIdentityCollisionError(
                    f"request source is not authoritative: {source.asset_id}"
                )
        prompt = (
            self.resolve_historical_prompt(request.prompt)
            if historical
            else self.resolve_prompt(request.prompt)
        )
        schema = self.resolve_schema(request.output_schema)
        if prompt.task_type is not request.task_type or not schema.accepts(prompt.output_schema):
            raise ArtifactIdentityCollisionError("request prompt/schema/task binding is invalid")

    def _validate_job_record(self, job: AIJob) -> None:
        request = self.resolve_request(job.request_id)
        expected = (
            request.job_id,
            request.run_id,
            request.phase_id,
            request.task_type,
            request_fingerprint(request),
            request.output_schema,
            request.provider.provider,
            request.provider.model,
            sha256_value(request.provider.parameters),
        )
        actual = (
            job.job_id,
            job.run_id,
            job.phase_id,
            job.task_type,
            job.request_fingerprint,
            job.output_schema,
            job.provider,
            job.model,
            job.provider_parameters_sha256,
        )
        if actual != expected:
            raise ArtifactIdentityCollisionError("job is not bound to its authoritative request")
        if request.created_at > job.created_at:
            raise ArtifactIdentityCollisionError("job creation predates its request")

    def _validate_response_record(self, response: AIResponse) -> None:
        from buduunkhad.ai.artifacts import _validate_payload_sources
        from buduunkhad.ai.contracts import AIJobStatus, AIResponseStatus

        request = self.resolve_request(response.request_id)
        job = self.resolve_job(response.job_id)
        fingerprint = request_fingerprint(request)
        expected = (
            request.job_id,
            request.run_id,
            request.phase_id,
            request.task_type,
            fingerprint,
            request.output_schema,
            request.provider.provider,
            request.provider.model,
        )
        actual = (
            response.job_id,
            response.run_id,
            response.phase_id,
            response.task_type,
            response.request_fingerprint,
            response.output_schema,
            response.provider,
            response.model,
        )
        if actual != expected:
            raise ArtifactIdentityCollisionError(
                "provider response is not bound to its authoritative request"
            )
        if (
            job.request_id != request.request_id
            or job.provider_response_id != response.provider_response_id
        ):
            raise ArtifactIdentityCollisionError("provider response is not bound to its job")
        status_pairs = {
            AIResponseStatus.SUCCESS: AIJobStatus.SUCCEEDED,
            AIResponseStatus.REFUSED: AIJobStatus.REFUSED,
            AIResponseStatus.INCOMPLETE: AIJobStatus.INCOMPLETE,
            AIResponseStatus.INVALID_OUTPUT: AIJobStatus.FAILED,
            AIResponseStatus.FAILURE: AIJobStatus.FAILED,
        }
        if job.status is not status_pairs[response.status]:
            raise ArtifactIdentityCollisionError("provider response and job states disagree")
        if job.started_at is None or job.completed_at is None:
            raise ArtifactIdentityCollisionError("response-linked job is not complete")
        if not (
            request.created_at
            <= job.created_at
            <= job.started_at
            <= response.created_at
            <= job.completed_at
        ):
            raise ArtifactIdentityCollisionError(
                "request/job/response timestamps violate causal order"
            )
        if job.usage != response.usage:
            raise ArtifactIdentityCollisionError("provider response usage differs from job")
        schema = self.resolve_schema(response.output_schema)
        try:
            prohibit_provider_approval(response)
        except AIProviderError as exc:
            raise ArtifactIdentityCollisionError(str(exc)) from exc
        if response.status is AIResponseStatus.SUCCESS:
            if response.output is None or type(response.output) is not schema.output_model:
                raise ArtifactIdentityCollisionError(
                    "successful response does not use the exact registered schema model"
                )
            try:
                validate_provider_output_contract(response.output, schema.output_model)
            except AIProviderError as exc:
                raise ArtifactIdentityCollisionError(str(exc)) from exc
            _validate_payload_sources(
                response.output,
                request,
                self,
                context="provider response",
            )
        elif response.status is AIResponseStatus.INVALID_OUTPUT:
            if response.raw_output is None:
                raise ArtifactIdentityCollisionError(
                    "invalid response is missing its raw schema payload"
                )
            raw_output = response.raw_output.to_python()
            current_errors = validation_error_details(schema.output_model, raw_output)
            if not current_errors:
                raise ArtifactIdentityCollisionError(
                    "valid schema payload cannot be labelled INVALID_OUTPUT"
                )
            if current_errors != response.validation_errors:
                raise ArtifactIdentityCollisionError(
                    "invalid response descriptions differ from current schema validation"
                )

    def _validate_validation_record(self, validation: ValidationAttestation) -> None:
        from buduunkhad.ai.artifacts import _validate_validation_attestation

        registration = self.resolve_validator(validation.validator_identity)
        if (
            validation.implementation,
            validation.implementation_version,
        ) != (registration.implementation, registration.implementation_version):
            raise ArtifactIdentityCollisionError(
                "validation attestation uses an unapproved validator implementation"
            )
        artifact = self.resolve_artifact(validation.artifact)
        _validate_validation_attestation(artifact.content, validation, self)

    def _validate_critique_record(self, critique: CritiqueAttestation) -> None:
        from buduunkhad.ai.artifacts import _validate_critique_attestation

        artifact = self.resolve_artifact(critique.artifact)
        _validate_critique_attestation(
            artifact.content,
            critique,
            event_time=critique.critiqued_at,
            resolver=self,
        )


RecordT = TypeVar("RecordT", bound=FrozenModel)


def _unique_records(
    values: tuple[RecordT, ...],
    key_function: Callable[[RecordT], str],
    label: str,
) -> dict[str, RecordT]:
    result: dict[str, RecordT] = {}
    for value in values:
        persisted_model_bytes(value)
        key = key_function(value)
        if key in result:
            raise ValueError(f"duplicate {label} ID: {key}")
        result[key] = value
    return result


def _resolve(records: dict[str, RecordT], key: str, label: str) -> RecordT:
    try:
        return records[key]
    except KeyError as exc:
        raise ArtifactResolutionError(f"{label} not found: {key}") from exc


def _insert_record(
    records: dict[str, RecordT],
    key: str,
    value: RecordT,
    label: str,
) -> None:
    value_bytes = persisted_model_bytes(value)
    existing = records.get(key)
    if existing is not None:
        if persisted_model_bytes(existing) == value_bytes:
            return
        raise ArtifactIdentityCollisionError(f"{label} identity already exists: {key}")
    records[key] = value
