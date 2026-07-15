from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from buduunkhad.ai.artifacts import (
    AIArtifact,
    ArtifactRejectedEvent,
    HumanApprovalAttestation,
    HumanRejectionBasis,
    ReviewerAuthorization,
)
from buduunkhad.ai.contracts import (
    AIJob,
    AIJobStatus,
    AIRequest,
    AIResponseStatus,
    AIUsage,
    CanonicalJSONValue,
    ConfidenceComponent,
    GeologicalFeatureProposal,
    ImageRasterInterpretation,
    NamedJSONValue,
    PixelLineString,
    PixelPolygon,
    ProviderConfiguration,
    ReviewStatus,
    SourceReference,
    TaskType,
    ensure_supported_pydantic,
)
from buduunkhad.ai.fingerprint import request_fingerprint


def test_review_states_are_exact() -> None:
    assert [status.value for status in ReviewStatus] == [
        "AI_DRAFT",
        "AI_VALIDATED",
        "GEOLOGIST_APPROVED",
        "REJECTED",
        "SUPERSEDED",
    ]


def test_runtime_pydantic_floor_matches_packaging_contract() -> None:
    ensure_supported_pydantic("2.7.0")
    with pytest.raises(RuntimeError, match="Pydantic >=2.7"):
        ensure_supported_pydantic("2.6.9")


def test_security_records_reject_setattr_and_nested_mutation(scenario_factory) -> None:
    artifact = scenario_factory().artifact
    with pytest.raises(ValidationError, match="frozen"):
        artifact.content.content_sha256 = "f" * 64
    with pytest.raises(AttributeError):
        artifact.events.append(artifact.events[0])  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        artifact.content.source_references.append(  # type: ignore[attr-defined]
            artifact.content.source_references[0]
        )


def test_model_copy_and_deprecated_copy_revalidate_every_sensitive_record(
    scenario_factory,
) -> None:
    scenario = scenario_factory()
    invalid_updates = (
        (scenario.artifact.content, {"content_sha256": "f" * 64}, "content_sha256"),
        (scenario.request, {"task_type": TaskType.FEATURE_CRITIQUE}, "artifact subject"),
        (scenario.response, {"status": AIResponseStatus.REFUSED}, "non-success"),
        (scenario.generator_job, {"status": AIJobStatus.PENDING}, "pending job"),
    )
    for model, update, message in invalid_updates:
        with pytest.raises((ValidationError, ValueError), match=message):
            model.model_copy(update=update)
        with pytest.raises((ValidationError, ValueError), match=message):
            model.copy(update=update)


def test_copy_include_and_exclude_are_explicitly_unsupported(scenario_factory) -> None:
    request = scenario_factory().request
    with pytest.raises(ValueError, match="include/exclude"):
        request.copy(include={"request_id"})
    with pytest.raises(ValueError, match="include/exclude"):
        request.copy(exclude={"provider"})


def test_unvalidated_construct_apis_are_explicitly_unsupported(scenario_factory) -> None:
    request = scenario_factory().request
    values = request.model_dump(mode="python")
    with pytest.raises(TypeError, match="model_construct is unsupported"):
        type(request).model_construct(**values)
    with pytest.raises(TypeError, match="construct is unsupported"):
        type(request).construct(**values)


def test_model_validate_revalidates_a_tampered_existing_instance(scenario_factory) -> None:
    request = scenario_factory().request.model_copy()
    object.__setattr__(request, "created_at", datetime(2026, 1, 1))
    with pytest.raises(ValidationError, match="timezone-aware"):
        AIRequest.model_validate(request)


def test_response_and_job_direct_validation_and_json_reload_match_copy_security(
    scenario_factory,
) -> None:
    scenario = scenario_factory()
    response_values = scenario.response.model_dump(mode="python")
    response_values["status"] = AIResponseStatus.REFUSED
    for reload_operation in (
        lambda: type(scenario.response).model_validate(response_values),
        lambda: type(scenario.response).model_validate_json(
            json.dumps(scenario.response.model_dump(mode="json") | {"status": "REFUSED"})
        ),
    ):
        with pytest.raises(ValidationError, match="non-success"):
            reload_operation()

    job_values = scenario.generator_job.model_dump(mode="python")
    job_values["status"] = AIJobStatus.PENDING
    for reload_operation in (
        lambda: AIJob.model_validate(job_values),
        lambda: AIJob.model_validate_json(
            json.dumps(scenario.generator_job.model_dump(mode="json") | {"status": "PENDING"})
        ),
    ):
        with pytest.raises(ValidationError, match="pending job"):
            reload_operation()


def _forged_approval(draft: AIArtifact) -> HumanApprovalAttestation:
    reviewed_at = draft.content.created_at + timedelta(hours=2)
    authorization = ReviewerAuthorization(
        authorization_id="auth-forged",
        reviewer_id="reviewer-1",
        reviewer_name="Dr Reviewer",
        authorizer_identity="offline-reviewer-registry",
        authorized=True,
        authorized_at=reviewed_at - timedelta(minutes=1),
        qualification="Qualified geologist",
    )
    return HumanApprovalAttestation(
        artifact=draft.content.reference,
        content_sha256=draft.content.content_sha256,
        authorization=authorization,
        reviewed_at=reviewed_at,
        review_note="attempted direct approval",
    )


def test_constructor_validate_copy_and_json_reload_reject_forged_approval(
    scenario_factory,
) -> None:
    draft = scenario_factory().artifact
    approval = _forged_approval(draft)
    values = draft.model_dump(mode="python")
    values["events"] = (*draft.events, approval)
    with pytest.raises(ValidationError, match="approval requires AI_VALIDATED"):
        AIArtifact(**values)
    with pytest.raises(ValidationError, match="approval requires AI_VALIDATED"):
        AIArtifact.model_validate(values)
    with pytest.raises(ValidationError, match="approval requires AI_VALIDATED"):
        draft.model_copy(update={"events": (*draft.events, approval)})
    with pytest.raises(ValidationError, match="approval requires AI_VALIDATED"):
        draft.copy(update={"events": (*draft.events, approval)})
    serialized = json.loads(draft.model_dump_json())
    serialized["events"].append(json.loads(approval.model_dump_json()))
    with pytest.raises(ValidationError, match="approval requires AI_VALIDATED"):
        AIArtifact.model_validate_json(json.dumps(serialized))


def test_direct_validate_rejects_rejection_without_creation(scenario_factory) -> None:
    draft = scenario_factory().artifact
    authorization = ReviewerAuthorization(
        authorization_id="rejection-authorization",
        reviewer_id="reviewer-1",
        reviewer_name="Dr Reviewer",
        authorizer_identity="offline-reviewer-registry",
        authorized=True,
        authorized_at=draft.content.created_at,
        qualification="Qualified geologist",
    )
    rejection = ArtifactRejectedEvent(
        artifact=draft.content.reference,
        content_sha256=draft.content.content_sha256,
        basis=HumanRejectionBasis(authorization=authorization),
        note="reject",
        occurred_at=draft.content.created_at + timedelta(minutes=1),
    )
    with pytest.raises(ValidationError, match="rejection requires"):
        AIArtifact.model_validate({"content": draft.content, "events": (rejection,)})


def test_rejection_event_has_no_arbitrary_actor_string_path(scenario_factory) -> None:
    draft = scenario_factory().artifact
    with pytest.raises(ValidationError, match="basis|extra"):
        ArtifactRejectedEvent.model_validate(
            {
                "artifact": draft.content.reference,
                "content_sha256": draft.content.content_sha256,
                "actor_type": "AI_CRITIC",
                "actor_identity": "fabricated-critic",
                "note": "fabricated",
                "occurred_at": draft.content.created_at + timedelta(minutes=1),
            }
        )


def test_named_parameters_reject_duplicates_and_sort_canonically() -> None:
    duplicate = (
        {"name": "temperature", "value": 0},
        {"name": "temperature", "value": 1},
    )
    with pytest.raises(ValidationError, match="duplicate names"):
        ProviderConfiguration.model_validate(
            {"provider": "test-provider", "model": "offline", "parameters": duplicate}
        )
    first = ProviderConfiguration.model_validate(
        {"provider": "test-provider", "model": "offline", "parameters": {"z": 1, "a": 2}}
    )
    second = ProviderConfiguration.model_validate(
        {"provider": "test-provider", "model": "offline", "parameters": {"a": 2, "z": 1}}
    )
    assert first.parameters == second.parameters
    assert tuple(item.name for item in first.parameters) == ("a", "z")


@pytest.mark.parametrize(
    "update",
    [
        {"status": AIJobStatus.PENDING},
        {"status": AIJobStatus.RUNNING, "completed_at": None},
        {"started_at": None},
        {"completed_at": datetime(2000, 1, 1)},
    ],
)
def test_job_status_and_timestamp_invariants_survive_copy(scenario_factory, update) -> None:
    job: AIJob = scenario_factory().generator_job
    with pytest.raises((ValidationError, ValueError)):
        job.model_copy(update=update)


def test_geological_evidence_status_is_separate_from_review_status(
    source_reference: SourceReference,
) -> None:
    proposal = GeologicalFeatureProposal.model_validate(
        {
            "feature_id": "feature-1",
            "feature_type": "synthetic_contact",
            "geometry": PixelLineString(coordinates=((0.0, 0.0), (2.0, 2.0))),
            "attributes": {},
            "evidence_status": "SUPPORT_EVIDENCE",
            "source_references": (source_reference,),
            "confidence_components": (
                ConfidenceComponent(name="visibility", score=0.8, rationale="synthetic fixture"),
            ),
            "limitations": ("not geological evidence",),
        }
    )
    assert proposal.evidence_status == "SUPPORT_EVIDENCE"
    assert proposal.review_status is ReviewStatus.AI_DRAFT


def test_polygon_contract_rejects_open_ring() -> None:
    with pytest.raises(ValidationError, match="must be closed"):
        PixelPolygon(coordinates=(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),))


def test_decimal_round_trip_never_uses_float() -> None:
    usage = AIUsage(cost_usd=Decimal("1.2300"))
    restored = AIUsage.model_validate_json(usage.model_dump_json())
    assert restored.cost_usd.as_tuple() == Decimal("1.2300").as_tuple()


def test_canonical_records_and_schema_outputs_round_trip_without_double_wrapping(
    scenario_factory,
    source_reference: SourceReference,
) -> None:
    scenario = scenario_factory()
    assert scenario.response.output is not None
    assert scenario.critic_response.output is not None
    named = NamedJSONValue.model_validate(
        {"name": "threshold", "value": {"nested": [1, Decimal("1.20")]}}
    )
    canonical_raw_tag = CanonicalJSONValue.from_value({"canonical_json": "raw user value"})
    raster = ImageRasterInterpretation(
        source_reference=source_reference,
        observations=(),
        limitations=("synthetic",),
    )
    geological = GeologicalFeatureProposal.model_validate(
        {
            "feature_id": "feature-round-trip",
            "feature_type": "synthetic",
            "geometry": PixelLineString(coordinates=((0.0, 0.0), (1.0, 1.0))),
            "attributes": {"threshold": Decimal("1.20")},
            "evidence_status": "SUPPORT_EVIDENCE",
            "source_references": (source_reference,),
            "confidence_components": (
                ConfidenceComponent(name="schema", score=1.0, rationale="synthetic"),
            ),
            "limitations": ("synthetic",),
        }
    )
    values = (
        named,
        canonical_raw_tag,
        scenario.request.provider,
        scenario.request,
        scenario.response,
        scenario.response.output,
        raster,
        geological,
        scenario.critic_response.output,
    )
    for value in values:
        restored = type(value).model_validate_json(value.model_dump_json())
        assert restored.model_dump_json() == value.model_dump_json()
    assert request_fingerprint(
        AIRequest.model_validate_json(scenario.request.model_dump_json())
    ) == request_fingerprint(scenario.request)
    assert canonical_raw_tag.to_python() == {"canonical_json": "raw user value"}


def test_duplicate_interpretation_parameters_fail_all_copy_and_reload_paths(
    scenario_factory,
) -> None:
    request = scenario_factory().request
    duplicate = (
        {"name": "threshold", "value": 1},
        {"name": "threshold", "value": 2},
    )
    python_values = request.model_dump(mode="python") | {"interpretation_parameters": duplicate}
    json_values = request.model_dump(mode="json") | {"interpretation_parameters": list(duplicate)}
    operations = (
        lambda: AIRequest(**python_values),
        lambda: AIRequest.model_validate(python_values),
        lambda: AIRequest.model_validate_json(json.dumps(json_values)),
        lambda: request.model_copy(update={"interpretation_parameters": duplicate}),
        lambda: request.copy(update={"interpretation_parameters": duplicate}),
    )
    for operation in operations:
        with pytest.raises(ValidationError, match="duplicate names"):
            operation()


def test_naive_artifact_timestamp_is_rejected(scenario_factory) -> None:
    content = scenario_factory().artifact.content
    values = content.model_dump(mode="python")
    values["created_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError, match="timezone-aware"):
        type(content).model_validate(values)
