from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from buduunkhad.ai.artifacts import (
    ActorConfigurationIdentity,
    AIArtifact,
    ArtifactReference,
    CritiqueAttestation,
    GeneratorCriticWaiver,
    ReviewerAuthorization,
    ValidationAttestation,
    ValidationCheck,
    ValidationCheckName,
    ValidatorRegistration,
    build_artifact,
)
from buduunkhad.ai.catalog import (
    InMemoryArtifactCatalog,
    InMemoryProvenanceResolver,
    InMemorySourceAssetCatalog,
    InMemoryValidationAttestationCatalog,
)
from buduunkhad.ai.contracts import (
    AIJob,
    AIJobStatus,
    AIRequest,
    AIResponse,
    AIUsage,
    ArtifactSubjectIdentity,
    ConfidenceComponent,
    CritiqueVerdict,
    DocumentExtraction,
    ExtractedDocumentField,
    FeatureCritique,
    PageLocator,
    ProviderConfiguration,
    RiskLevel,
    SourceReference,
    TaskType,
)
from buduunkhad.ai.fingerprint import (
    canonical_json_text,
    request_fingerprint,
    sha256_bytes,
    sha256_value,
)
from buduunkhad.ai.prompts import PromptRegistry, default_schema_registry
from buduunkhad.ai.providers import FakeAIProvider, fake_response_id
from buduunkhad.ai.review import InMemoryReviewerAuthorizer, approve_artifact, validate_artifact

SHA_A = "a" * 64
BASE_TIME = datetime(2026, 2, 1, tzinfo=UTC)
_NO_EXTRACTED_FIELD = object()


@dataclass(frozen=True, slots=True)
class ArtifactScenario:
    artifact: AIArtifact
    catalog: InMemoryArtifactCatalog
    resolver: InMemoryProvenanceResolver
    request: AIRequest
    response: AIResponse
    generator_job: AIJob
    critic_request: AIRequest
    critic_response: AIResponse
    critic_job: AIJob
    validation: ValidationAttestation | None
    critique: CritiqueAttestation | None
    waiver: GeneratorCriticWaiver | None
    authorization: ReviewerAuthorization | None
    times: tuple[datetime, ...]


@pytest.fixture
def source_reference() -> SourceReference:
    return SourceReference(
        asset_id="synthetic-document",
        sha256=SHA_A,
        locators=(PageLocator(page_number=1),),
    )


@pytest.fixture
def prompt_registry() -> PromptRegistry:
    return PromptRegistry.load_packaged(schema_registry=default_schema_registry())


@pytest.fixture
def scenario_factory(
    source_reference: SourceReference,
    prompt_registry: PromptRegistry,
) -> Callable[..., ArtifactScenario]:
    schema_registry = default_schema_registry()
    catalog = InMemoryArtifactCatalog()
    source_catalog = InMemorySourceAssetCatalog((source_reference,))
    resolver = InMemoryProvenanceResolver(
        jobs=(),
        requests=(),
        responses=(),
        sources=(source_reference,),
        source_resolver=source_catalog,
        prompt_registry=prompt_registry,
        schema_registry=schema_registry,
        artifact_resolver=catalog,
        validators=(
            ValidatorRegistration(
                validator_identity="deterministic-validator",
                implementation="offline-contract-validator",
                implementation_version="1.0.0",
            ),
        ),
    )
    counter = 0

    def factory(
        *,
        artifact_id: str = "artifact-1",
        artifact_version: int = 1,
        parents: tuple[ArtifactReference, ...] = (),
        summary: str = "Synthetic extraction",
        extracted_value: object = _NO_EXTRACTED_FIELD,
        confidence_score: float = 1.0,
        prepare_review: bool = False,
        validate: bool = False,
        approve: bool = False,
        generator_model: str = "generator-model",
        critic_model: str = "critic-model",
        reuse_generator_configuration: bool = False,
        critic_verdict: CritiqueVerdict = CritiqueVerdict.ACCEPT_FOR_VALIDATION,
        critic_completed_index: int = 9,
        critique_index: int = 10,
        register_critique: bool = True,
    ) -> ArtifactScenario:
        nonlocal counter
        offset = timedelta(hours=counter)
        counter += 1
        times = tuple(BASE_TIME + offset + timedelta(minutes=index) for index in range(15))
        reference = ArtifactReference(
            artifact_id=artifact_id,
            artifact_version=artifact_version,
        )
        payload = DocumentExtraction(
            document_id="synthetic-document",
            fields=(
                ()
                if extracted_value is _NO_EXTRACTED_FIELD
                else (
                    ExtractedDocumentField.model_validate(
                        {
                            "field_name": "synthetic_value",
                            "value": extracted_value,
                            "confidence": 1.0,
                            "source_references": (source_reference,),
                            "limitations": ("synthetic fixture only",),
                        }
                    ),
                )
            ),
            summary=summary,
            limitations=("synthetic fixture only",),
        )
        generator_prompt = prompt_registry.get("fixture.document-extraction", "1.0.0")
        generator_schema = schema_registry.resolve(generator_prompt.output_schema)
        generator_job_id = f"generator-{artifact_id}-{artifact_version}"
        request = AIRequest.model_validate(
            {
                "request_id": f"request-{artifact_id}-{artifact_version}",
                "job_id": generator_job_id,
                "run_id": "run-1",
                "phase_id": "phase-00",
                "task_type": TaskType.DOCUMENT_EXTRACTION,
                "created_at": times[0],
                "source_references": (source_reference,),
                "prompt": generator_prompt.identity,
                "output_schema": generator_schema.identity,
                "provider": {
                    "provider": "fake",
                    "model": generator_model,
                    "parameters": {"temperature": 0},
                },
                "interpretation_parameters": {"artifact_version": artifact_version},
            }
        )
        generator = AIJob(
            job_id=generator_job_id,
            run_id=request.run_id,
            phase_id=request.phase_id,
            task_type=request.task_type,
            request_id=request.request_id,
            request_fingerprint=request_fingerprint(request),
            output_schema=request.output_schema,
            provider=request.provider.provider,
            model=request.provider.model,
            provider_parameters_sha256=sha256_value(request.provider.parameters),
            status=AIJobStatus.SUCCEEDED,
            provider_response_id=fake_response_id(request),
            created_at=times[1],
            started_at=times[2],
            completed_at=times[4],
            usage=AIUsage(),
        )
        resolver.add_request(request)
        resolver.add_job(generator)
        response = FakeAIProvider(
            payload=payload.model_dump(mode="python"),
            created_at=times[3],
        ).generate(request, DocumentExtraction, resolver=resolver)
        resolver.add_response(response)

        content_hash = sha256_bytes(canonical_json_text(payload).encode("utf-8"))
        critic_prompt = prompt_registry.get("fixture.feature-critique", "1.0.0")
        critic_schema = schema_registry.resolve(critic_prompt.output_schema)
        critic_job_id = f"critic-{artifact_id}-{artifact_version}"
        critic_parameters = (
            request.provider.parameters
            if reuse_generator_configuration
            else ProviderConfiguration.model_validate(
                {"provider": "fake", "model": "placeholder", "parameters": {"role": "critic"}}
            ).parameters
        )
        critic_effective_model = generator_model if reuse_generator_configuration else critic_model
        critic_request = AIRequest.model_validate(
            {
                "request_id": f"critic-request-{artifact_id}-{artifact_version}",
                "job_id": critic_job_id,
                "run_id": generator.run_id,
                "phase_id": generator.phase_id,
                "task_type": TaskType.FEATURE_CRITIQUE,
                "created_at": times[5],
                "source_references": (source_reference,),
                "prompt": critic_prompt.identity,
                "output_schema": critic_schema.identity,
                "provider": {
                    "provider": "fake",
                    "model": critic_effective_model,
                    "parameters": critic_parameters,
                },
                "interpretation_parameters": {"subject_hash": content_hash},
                "subject": ArtifactSubjectIdentity(
                    artifact_id=reference.artifact_id,
                    artifact_version=reference.artifact_version,
                    content_sha256=content_hash,
                    generator_job_id=generator.job_id,
                ),
            }
        )
        critique_payload = FeatureCritique(
            feature_id=reference.artifact_id,
            verdict=critic_verdict,
            findings=("independent synthetic critique",),
            confidence_components=(
                ConfidenceComponent(name="independence", score=1.0, rationale="synthetic"),
            ),
            limitations=("synthetic fixture only",),
        )
        critic = AIJob(
            job_id=critic_job_id,
            run_id=critic_request.run_id,
            phase_id=critic_request.phase_id,
            task_type=critic_request.task_type,
            request_id=critic_request.request_id,
            request_fingerprint=request_fingerprint(critic_request),
            output_schema=critic_request.output_schema,
            provider=critic_request.provider.provider,
            model=critic_request.provider.model,
            provider_parameters_sha256=sha256_value(critic_request.provider.parameters),
            status=AIJobStatus.SUCCEEDED,
            provider_response_id=fake_response_id(critic_request),
            created_at=times[6],
            started_at=times[7],
            completed_at=times[critic_completed_index],
            usage=AIUsage(),
        )
        resolver.add_request(critic_request)
        resolver.add_job(critic)
        critic_response = FakeAIProvider(
            payload=critique_payload.model_dump(mode="python"),
            created_at=times[8],
        ).generate(critic_request, FeatureCritique, resolver=resolver)
        resolver.add_response(critic_response)

        artifact = build_artifact(
            reference=reference,
            parent_artifacts=parents,
            payload=payload,
            generator_job=generator,
            critic_job=critic,
            request=request,
            response=response,
            source_references=(source_reference,),
            resolver=resolver,
            confidence_components=(
                ConfidenceComponent(name="schema", score=confidence_score, rationale="synthetic"),
            ),
            limitations=("synthetic fixture only",),
            risk_level=RiskLevel.LOW,
            evidence_status="SUPPORT_EVIDENCE",
        )
        catalog.add_artifact(artifact, resolver=resolver)

        validation_attestation: ValidationAttestation | None = None
        critique_attestation: CritiqueAttestation | None = None
        waiver: GeneratorCriticWaiver | None = None
        authorization: ReviewerAuthorization | None = None
        if prepare_review or validate or approve:
            validation_attestation = ValidationAttestation(
                attestation_id=f"validation-{artifact_id}-{artifact_version}",
                artifact=reference,
                run_id=generator.run_id,
                phase_id=generator.phase_id,
                task_type=generator.task_type,
                generator_job_id=generator.job_id,
                generator_response_id=response.provider_response_id,
                generator_request_fingerprint=request_fingerprint(request),
                validator_identity="deterministic-validator",
                implementation="offline-contract-validator",
                implementation_version="1.0.0",
                checks=(
                    ValidationCheck(
                        check=ValidationCheckName.SCHEMA,
                        required=True,
                        passed=True,
                        detail="schema valid",
                    ),
                    ValidationCheck(
                        check=ValidationCheckName.PROVENANCE,
                        required=True,
                        passed=True,
                        detail="provenance valid",
                    ),
                ),
                validated_at=times[10],
                validated_content_sha256=content_hash,
                findings=(),
                limitations=(),
            )
            critique_attestation = CritiqueAttestation(
                attestation_id=f"critique-{artifact_id}-{artifact_version}",
                artifact=reference,
                generator_job_id=generator.job_id,
                critic_job_id=critic.job_id,
                critic_response_id=critic_response.provider_response_id,
                critic_request_fingerprint=request_fingerprint(critic_request),
                output_schema=critic_request.output_schema,
                critic_configuration=ActorConfigurationIdentity(
                    provider=critic.provider,
                    model=critic.model,
                    parameters_sha256=critic.provider_parameters_sha256,
                ),
                critiqued_content_sha256=content_hash,
                independent_critic_policy_passed=True,
                findings=critique_payload.findings,
                disposition=critique_payload.verdict,
                critiqued_at=times[critique_index],
            )
            if reuse_generator_configuration:
                waiver = GeneratorCriticWaiver(
                    waiver_id=f"waiver-{artifact_id}-{artifact_version}",
                    artifact=reference,
                    generator_job_id=generator.job_id,
                    critic_job_id=critic.job_id,
                    generator_configuration=ActorConfigurationIdentity(
                        provider=generator.provider,
                        model=generator.model,
                        parameters_sha256=generator.provider_parameters_sha256,
                    ),
                    critic_configuration=ActorConfigurationIdentity(
                        provider=critic.provider,
                        model=critic.model,
                        parameters_sha256=critic.provider_parameters_sha256,
                    ),
                    approved_by="offline-waiver-authority",
                    approved_at=times[10],
                    reason="synthetic same-configuration test",
                )
                resolver.add_waiver(waiver)
            resolver.add_validation(
                validation_attestation,
                validation_resolver=InMemoryValidationAttestationCatalog((validation_attestation,)),
            )
            if register_critique:
                resolver.add_critique(critique_attestation)
        if validate or approve:
            assert validation_attestation is not None
            assert critique_attestation is not None
            artifact = validate_artifact(
                artifact,
                validation=validation_attestation,
                critique=critique_attestation,
                occurred_at=times[11],
                resolver=resolver,
                waiver=waiver,
            )
            catalog.update_artifact(artifact, resolver=resolver)
        if approve:
            authorization = ReviewerAuthorization(
                authorization_id=f"authorization-{artifact_id}-{artifact_version}",
                reviewer_id="reviewer-1",
                reviewer_name="Dr Reviewer",
                authorizer_identity="offline-reviewer-registry",
                authorized=True,
                authorized_at=times[12],
                qualification="Qualified geologist",
            )
            reviewer_authorizer = InMemoryReviewerAuthorizer((authorization,))
            resolver.add_authorization(
                authorization,
                authorizer=reviewer_authorizer,
                reviewed_at=times[13],
            )
            artifact = approve_artifact(
                artifact,
                reviewer_id="reviewer-1",
                reviewed_at=times[13],
                review_note="synthetic approval",
                authorizer=reviewer_authorizer,
                resolver=resolver,
            )
            catalog.update_artifact(artifact, resolver=resolver)
        return ArtifactScenario(
            artifact=artifact,
            catalog=catalog,
            resolver=resolver,
            request=request,
            response=response,
            generator_job=generator,
            critic_request=critic_request,
            critic_response=critic_response,
            critic_job=critic,
            validation=validation_attestation,
            critique=critique_attestation,
            waiver=waiver,
            authorization=authorization,
            times=times,
        )

    return factory


@pytest.fixture
def artifact_factory(
    scenario_factory: Callable[..., ArtifactScenario],
) -> Callable[..., AIArtifact]:
    def factory(**kwargs: object) -> AIArtifact:
        return scenario_factory(**kwargs).artifact

    return factory
