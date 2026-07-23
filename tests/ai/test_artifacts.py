from __future__ import annotations

import json
from datetime import timedelta, timezone

import pytest
from pydantic import ValidationError

from buduunkhad.ai.artifacts import (
    AIArtifact,
    AIArtifactContentRecord,
    ArtifactContractError,
    ArtifactReference,
    ValidatorRegistration,
    build_artifact,
    validate_artifact_authority,
)
from buduunkhad.ai.catalog import (
    ArtifactIdentityCollisionError,
    ArtifactResolutionError,
    InMemoryArtifactCatalog,
    InMemoryProvenanceResolver,
    InMemorySourceAssetCatalog,
)
from buduunkhad.ai.contracts import (
    AIJobStatus,
    AIResponse,
    AIResponseStatus,
    CanonicalJSONValue,
    ConfidenceComponent,
    DocumentExtraction,
    FrozenModel,
    PageLocator,
    PromptIdentity,
    RiskLevel,
    SchemaIdentity,
    SourceReference,
    TaskType,
)
from buduunkhad.ai.fingerprint import (
    canonical_value_from_text,
    request_fingerprint,
    sha256_bytes,
    sha256_value,
)
from buduunkhad.ai.prompts import default_schema_registry


def _payload(scenario) -> DocumentExtraction:
    return DocumentExtraction.model_validate(
        canonical_value_from_text(scenario.artifact.content.payload_canonical_json)
    )


def _build(scenario, *, resolver=None, **overrides: object) -> AIArtifact:
    values: dict[str, object] = {
        "reference": scenario.artifact.content.reference,
        "parent_artifacts": (),
        "payload": _payload(scenario),
        "generator_job": scenario.generator_job,
        "critic_job": scenario.critic_job,
        "request": scenario.request,
        "response": scenario.response,
        "source_references": scenario.request.source_references,
        "resolver": resolver or scenario.resolver,
        "confidence_components": (
            ConfidenceComponent(name="schema", score=1.0, rationale="synthetic"),
        ),
        "limitations": ("synthetic only",),
        "risk_level": RiskLevel.LOW,
        "evidence_status": "SUPPORT_EVIDENCE",
    }
    values.update(overrides)
    return build_artifact(**values)  # ty: ignore[invalid-argument-type]


def _isolated_resolver(
    scenario,
    prompt_registry,
    *,
    generator_job=None,
    request=None,
    response=None,
    critic_job=None,
    critic_request=None,
    critic_response=None,
    sources=None,
    catalog=None,
) -> InMemoryProvenanceResolver:
    resolved_sources = sources or scenario.request.source_references
    return InMemoryProvenanceResolver(
        jobs=(generator_job or scenario.generator_job, critic_job or scenario.critic_job),
        requests=(request or scenario.request, critic_request or scenario.critic_request),
        responses=(response or scenario.response, critic_response or scenario.critic_response),
        sources=resolved_sources,
        source_resolver=InMemorySourceAssetCatalog(resolved_sources),
        prompt_registry=prompt_registry,
        schema_registry=default_schema_registry(),
        artifact_resolver=catalog or InMemoryArtifactCatalog(),
        validators=(
            ValidatorRegistration(
                validator_identity="deterministic-validator",
                implementation="offline-contract-validator",
                implementation_version="1.0.0",
            ),
        ),
    )


def test_builder_calculates_content_hash_and_resolves_complete_lineage(
    scenario_factory,
) -> None:
    scenario = scenario_factory()
    content = scenario.artifact.content
    assert content.content_sha256 == sha256_value(_payload(scenario))
    assert content.request_fingerprint == request_fingerprint(scenario.request)
    assert content.generator_job_id == scenario.generator_job.job_id
    assert content.critic_job_id == scenario.critic_job.job_id
    validate_artifact_authority(scenario.artifact, resolver=scenario.resolver)


def test_payload_tampering_is_rejected(scenario_factory) -> None:
    scenario = scenario_factory()
    tampered = _payload(scenario).model_copy(update={"summary": "tampered"})
    with pytest.raises(ArtifactContractError, match="unrelated"):
        _build(scenario, payload=tampered)


def test_content_hash_and_stored_canonical_text_are_both_validated(scenario_factory) -> None:
    content = scenario_factory().artifact.content
    values = content.model_dump(mode="python")
    values["content_sha256"] = "f" * 64
    with pytest.raises(ValidationError, match="content_sha256"):
        AIArtifactContentRecord.model_validate(values)
    noncanonical = content.payload_canonical_json.replace(",", ", ", 1)
    values = content.model_dump(mode="python") | {
        "payload_canonical_json": noncanonical,
        "content_sha256": sha256_bytes(noncanonical.encode("utf-8")),
    }
    with pytest.raises(ValidationError, match="canonical form"):
        AIArtifactContentRecord.model_validate(values)


def test_self_consistent_forged_reload_is_non_authoritative_at_catalog_boundary(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory()
    forged_content = scenario.artifact.content.model_copy(update={"provider": "fabricated"})
    forged = scenario.artifact.model_copy(update={"content": forged_content})
    reloaded = AIArtifact.model_validate_json(forged.model_dump_json())
    catalog = InMemoryArtifactCatalog()
    resolver = _isolated_resolver(scenario, prompt_registry, catalog=catalog)
    with pytest.raises(ArtifactContractError, match="provider"):
        catalog.add_artifact(reloaded, resolver=resolver)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_id", "unrelated-request"),
        ("job_id", "unrelated-job"),
        ("run_id", "unrelated-run"),
        ("phase_id", "phase-99"),
        ("task_type", TaskType.IMAGE_RASTER_INTERPRETATION),
        ("request_fingerprint", "f" * 64),
        ("provider", "unrelated-provider"),
        ("model", "unrelated-model"),
    ],
)
def test_every_generator_response_cross_link_mismatch_fails(
    scenario_factory,
    prompt_registry,
    field: str,
    value: object,
) -> None:
    scenario = scenario_factory()
    wrong_response = scenario.response.model_copy(update={field: value})
    with pytest.raises((ValueError, LookupError)):
        resolver = _isolated_resolver(
            scenario,
            prompt_registry,
            response=wrong_response,
        )
        _build(scenario, response=wrong_response, resolver=resolver)


@pytest.mark.parametrize(
    ("record", "task"),
    [
        ("job", TaskType.IMAGE_RASTER_INTERPRETATION),
        ("request", TaskType.IMAGE_RASTER_INTERPRETATION),
        ("response", TaskType.IMAGE_RASTER_INTERPRETATION),
    ],
)
def test_job_request_response_artifact_task_types_must_match(
    scenario_factory,
    prompt_registry,
    record: str,
    task: TaskType,
) -> None:
    scenario = scenario_factory()
    job = scenario.generator_job
    request = scenario.request
    response = scenario.response
    if record == "job":
        job = job.model_copy(update={"task_type": task})
    elif record == "request":
        request = request.model_copy(update={"task_type": task})
        changed_fingerprint = request_fingerprint(request)
        job = job.model_copy(update={"request_fingerprint": changed_fingerprint})
        response = response.model_copy(update={"request_fingerprint": changed_fingerprint})
    else:
        response = response.model_copy(update={"task_type": task})
    with pytest.raises((ValueError, LookupError), match="task|prompt|bound"):
        resolver = _isolated_resolver(
            scenario,
            prompt_registry,
            generator_job=job,
            request=request,
            response=response,
        )
        _build(
            scenario,
            generator_job=job,
            request=request,
            response=response,
            resolver=resolver,
        )


def test_generator_causal_order_is_enforced_across_authoritative_records(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory()
    late_request = scenario.request.model_copy(
        update={"created_at": scenario.generator_job.completed_at + timedelta(seconds=1)}
    )
    changed_fingerprint = request_fingerprint(late_request)
    job = scenario.generator_job.model_copy(update={"request_fingerprint": changed_fingerprint})
    response = scenario.response.model_copy(update={"request_fingerprint": changed_fingerprint})
    with pytest.raises((ValueError, LookupError), match="causal order|predates"):
        resolver = _isolated_resolver(
            scenario,
            prompt_registry,
            generator_job=job,
            request=late_request,
            response=response,
        )
        _build(
            scenario,
            generator_job=job,
            request=late_request,
            response=response,
            resolver=resolver,
        )


@pytest.mark.parametrize("position", ["before-start", "after-completion"])
def test_response_resolver_insertion_rejects_out_of_interval_records(
    scenario_factory,
    position: str,
) -> None:
    scenario = scenario_factory()
    if position == "before-start":
        assert scenario.generator_job.started_at is not None
        created_at = scenario.generator_job.started_at - timedelta(seconds=1)
    else:
        assert scenario.generator_job.completed_at is not None
        created_at = scenario.generator_job.completed_at + timedelta(seconds=1)
    forged = scenario.response.model_copy(update={"created_at": created_at})
    with pytest.raises(ValueError, match="causal order"):
        scenario.resolver.add_response(forged)


@pytest.mark.parametrize("case", ["valid-labelled-invalid", "stale-descriptions"])
def test_response_resolver_revalidates_invalid_output_descriptions(
    scenario_factory,
    prompt_registry,
    case: str,
) -> None:
    scenario = scenario_factory()
    raw_output: object
    if case == "valid-labelled-invalid":
        raw_output = _payload(scenario).model_dump(mode="python")
    else:
        raw_output = {}
    forged_response = scenario.response.model_copy(
        update={
            "status": AIResponseStatus.INVALID_OUTPUT,
            "output": None,
            "raw_output": raw_output,
            "validation_errors": ("fabricated validation description",),
        }
    )
    forged_job = scenario.generator_job.model_copy(update={"status": AIJobStatus.FAILED})
    with pytest.raises(ValueError, match="valid schema payload|descriptions"):
        _isolated_resolver(
            scenario,
            prompt_registry,
            generator_job=forged_job,
            response=forged_response,
        )


def test_critic_subject_fingerprint_response_schema_and_run_are_linked(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory()
    subject = scenario.critic_request.subject
    assert subject is not None
    mutations = (
        ("subject", subject.model_copy(update={"content_sha256": "f" * 64})),
        ("run_id", "unrelated-run"),
    )
    for field, value in mutations:
        request = scenario.critic_request.model_copy(update={field: value})
        job = scenario.critic_job.model_copy(
            update={"request_fingerprint": request_fingerprint(request)}
        )
        response = scenario.critic_response.model_copy(
            update={
                "run_id": request.run_id,
                "request_fingerprint": request_fingerprint(request),
            }
        )
        with pytest.raises((ValueError, LookupError)):
            resolver = _isolated_resolver(
                scenario,
                prompt_registry,
                critic_job=job,
                critic_request=request,
                critic_response=response,
            )
            _build(scenario, critic_job=job, resolver=resolver)

    assert scenario.critic_response.output is not None
    wrong_output = scenario.critic_response.output.model_copy(
        update={"feature_id": "unrelated-artifact"}
    )
    wrong_response = scenario.critic_response.model_copy(update={"output": wrong_output})
    resolver = _isolated_resolver(
        scenario,
        prompt_registry,
        critic_response=wrong_response,
    )
    with pytest.raises(ArtifactContractError, match="critic response subject"):
        _build(scenario, resolver=resolver)


def test_response_output_must_be_exact_registered_model_not_structural_twin(
    scenario_factory,
    prompt_registry,
) -> None:
    class StructuralTwin(FrozenModel):
        document_id: str
        fields: tuple[object, ...]
        summary: str
        limitations: tuple[str, ...]

    scenario = scenario_factory()
    twin = StructuralTwin.model_validate(_payload(scenario).model_dump(mode="python"))
    response_type = AIResponse[StructuralTwin]
    values = scenario.response.model_dump(mode="python") | {"output": twin}
    wrong_response = response_type.model_validate(values)
    with pytest.raises((ValueError, LookupError), match="model|schema"):
        resolver = _isolated_resolver(scenario, prompt_registry, response=wrong_response)
        _build(scenario, response=wrong_response, resolver=resolver)


def test_unregistered_prompt_and_schema_identities_fail_resolution(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory()
    forged_prompt = scenario.request.model_copy(
        update={
            "prompt": PromptIdentity(
                prompt_id="self-created",
                version="1.0.0",
                sha256="f" * 64,
            )
        }
    )
    with pytest.raises(ValueError, match="not registered"):
        resolver = _isolated_resolver(scenario, prompt_registry, request=forged_prompt)
        _build(scenario, request=forged_prompt, resolver=resolver)
    forged_schema = scenario.request.model_copy(
        update={
            "output_schema": SchemaIdentity(
                schema_id="self-created", version="1.0.0", sha256="e" * 64
            )
        }
    )
    with pytest.raises(ValueError, match="not approved"):
        resolver = _isolated_resolver(scenario, prompt_registry, request=forged_schema)
        _build(scenario, request=forged_schema, resolver=resolver)


@pytest.mark.parametrize("mutation", ["unregistered", "wrong-hash", "wrong-locator", "unrequested"])
def test_nested_generator_output_sources_resolve_exactly_and_belong_to_request(
    scenario_factory,
    prompt_registry,
    mutation: str,
) -> None:
    scenario = scenario_factory(extracted_value="nested source fixture")
    payload = _payload(scenario)
    field = payload.fields[0]
    original = scenario.request.source_references[0]
    if mutation == "unregistered":
        nested_source = original.model_copy(update={"asset_id": "unregistered-source"})
        sources = (original,)
    elif mutation == "wrong-hash":
        nested_source = original.model_copy(update={"sha256": "f" * 64})
        sources = (original,)
    elif mutation == "wrong-locator":
        nested_source = original.model_copy(update={"locators": (PageLocator(page_number=99),)})
        sources = (original,)
    else:
        nested_source = SourceReference(
            asset_id="registered-but-unrequested",
            sha256="b" * 64,
            locators=(PageLocator(page_number=2),),
        )
        sources = (original, nested_source)
    forged_field = field.model_copy(update={"source_references": (nested_source,)})
    forged_payload = payload.model_copy(update={"fields": (forged_field,)})
    forged_response = scenario.response.model_copy(update={"output": forged_payload})
    with pytest.raises((ValueError, LookupError), match="source|unrequested|not found"):
        _isolated_resolver(
            scenario,
            prompt_registry,
            response=forged_response,
            sources=sources,
        )


def test_source_catalog_insertion_requires_the_trusted_source_record(
    scenario_factory,
) -> None:
    scenario = scenario_factory()
    authoritative = scenario.request.source_references[0]
    caller_record = authoritative.model_copy(update={"sha256": "f" * 64})

    class TrustedSourceResolver:
        def resolve_source(self, asset_id: str) -> SourceReference:
            assert asset_id == authoritative.asset_id
            return authoritative

    with pytest.raises(ArtifactIdentityCollisionError, match="trusted source resolver"):
        scenario.resolver.add_source(
            caller_record,
            source_resolver=TrustedSourceResolver(),
        )


def test_source_hidden_in_canonical_nested_value_is_still_resolved(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory(extracted_value="nested source fixture")
    payload = _payload(scenario)
    field = payload.fields[0]
    unrequested = SourceReference(
        asset_id="canonical-unrequested-source",
        sha256="b" * 64,
        locators=(PageLocator(page_number=2),),
    )
    hidden = CanonicalJSONValue.from_value(
        {"nested": {"source": unrequested.model_dump(mode="python")}}
    )
    forged_field = field.model_copy(update={"value": hidden})
    forged_payload = payload.model_copy(update={"fields": (forged_field,)})
    forged_response = scenario.response.model_copy(update={"output": forged_payload})
    with pytest.raises(ArtifactContractError, match="unrequested source"):
        _isolated_resolver(
            scenario,
            prompt_registry,
            response=forged_response,
            sources=(*scenario.request.source_references, unrequested),
        )


def test_critic_cannot_substitute_a_different_authoritative_source(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory()
    extra = SourceReference(
        asset_id="critic-only-source",
        sha256="b" * 64,
        locators=(PageLocator(page_number=2),),
    )
    critic_request = scenario.critic_request.model_copy(update={"source_references": (extra,)})
    fingerprint = request_fingerprint(critic_request)
    critic_job = scenario.critic_job.model_copy(update={"request_fingerprint": fingerprint})
    critic_response = scenario.critic_response.model_copy(
        update={"request_fingerprint": fingerprint}
    )
    resolver = _isolated_resolver(
        scenario,
        prompt_registry,
        critic_job=critic_job,
        critic_request=critic_request,
        critic_response=critic_response,
        sources=(*scenario.request.source_references, extra),
    )
    with pytest.raises(ArtifactContractError, match="critic sources differ"):
        _build(scenario, critic_job=critic_job, resolver=resolver)


def test_every_parent_must_resolve_to_exact_existing_version(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory()
    missing = ArtifactReference(artifact_id="missing", artifact_version=1)
    with pytest.raises(ArtifactResolutionError, match="not found"):
        _build(scenario, parent_artifacts=(missing,))
    parent = scenario_factory(artifact_id="parent", artifact_version=1)
    child = scenario_factory(
        artifact_id="child",
        parents=(parent.artifact.content.reference,),
    )
    assert child.artifact.content.parent_artifacts == (parent.artifact.content.reference,)
    wrong_version = parent.artifact.content.reference.model_copy(update={"artifact_version": 99})
    with pytest.raises(ArtifactResolutionError, match="not found"):
        _build(child, parent_artifacts=(wrong_version,))


def test_missing_hash_and_provenance_fields_fail_direct_validation(scenario_factory) -> None:
    scenario = scenario_factory()
    content_values = scenario.artifact.content.model_dump(mode="python")
    del content_values["provider_response_id"]
    with pytest.raises(ValidationError, match="provider_response_id"):
        AIArtifactContentRecord.model_validate(content_values)
    source_values = scenario.request.source_references[0].model_dump(mode="python")
    del source_values["sha256"]
    with pytest.raises(ValidationError, match="sha256"):
        SourceReference.model_validate(source_values)


def test_catalog_content_immutability_uses_exact_persisted_timezone_bytes(
    scenario_factory,
) -> None:
    scenario = scenario_factory()
    equivalent_offset = scenario.artifact.content.created_at.astimezone(
        timezone(timedelta(hours=8))
    )
    forged_content = scenario.artifact.content.model_copy(update={"created_at": equivalent_offset})
    forged = scenario.artifact.model_copy(update={"content": forged_content})
    assert forged.content.created_at == scenario.artifact.content.created_at
    with pytest.raises(ValueError, match="cannot replace artifact content"):
        scenario.catalog.update_artifact(forged, resolver=scenario.resolver)


def test_catalog_content_immutability_distinguishes_signed_zero_bytes(scenario_factory) -> None:
    scenario = scenario_factory(confidence_score=0.0)
    component = scenario.artifact.content.confidence_components[0].model_copy(
        update={"score": -0.0}
    )
    forged_content = scenario.artifact.content.model_copy(
        update={"confidence_components": (component,)}
    )
    forged = scenario.artifact.model_copy(update={"content": forged_content})
    assert forged.content.confidence_components == scenario.artifact.content.confidence_components
    with pytest.raises(ValueError, match="cannot replace artifact content"):
        scenario.catalog.update_artifact(forged, resolver=scenario.resolver)


def test_catalog_rejects_json_reloaded_artifact_with_unresolved_parent(
    scenario_factory,
    prompt_registry,
) -> None:
    scenario = scenario_factory()
    missing = ArtifactReference(artifact_id="missing", artifact_version=1)
    values = json.loads(scenario.artifact.model_dump_json())
    values["content"]["parent_artifacts"] = [missing.model_dump(mode="json")]
    reloaded = AIArtifact.model_validate(values)
    catalog = InMemoryArtifactCatalog()
    resolver = _isolated_resolver(scenario, prompt_registry, catalog=catalog)
    with pytest.raises(ArtifactResolutionError):
        catalog.add_artifact(reloaded, resolver=resolver)
