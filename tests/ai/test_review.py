from __future__ import annotations

import json
from datetime import timedelta, timezone
from decimal import Decimal
from typing import cast

import pytest
from pydantic import ValidationError

from buduunkhad.ai.artifacts import (
    AIArtifact,
    ArtifactContractError,
    ArtifactValidatedEvent,
    CritiqueAttestation,
    CritiqueRejectionBasis,
    HumanRejectionBasis,
    ReviewerAuthorization,
    SupersessionRecord,
    ValidationAttestation,
    ValidationRejectionBasis,
    validate_artifact_authority,
)
from buduunkhad.ai.catalog import (
    ArtifactIdentityCollisionError,
    ArtifactResolutionError,
    InMemoryValidationAttestationCatalog,
    ProvenanceResolver,
)
from buduunkhad.ai.contracts import CritiqueVerdict, ReviewStatus
from buduunkhad.ai.review import (
    InMemoryReviewerAuthorizer,
    ReviewTransitionError,
    approve_artifact,
    create_supersession,
    effective_review_status,
    reject_artifact,
    validate_artifact,
)


def _register_validation_copy(scenario, **updates: object) -> ValidationAttestation:
    assert scenario.validation is not None
    copied = scenario.validation.model_copy(
        update={"attestation_id": f"{scenario.validation.attestation_id}-negative", **updates}
    )
    scenario.resolver.add_validation(
        copied,
        validation_resolver=InMemoryValidationAttestationCatalog((copied,)),
    )
    return copied


def _register_critique_copy(scenario, **updates: object) -> CritiqueAttestation:
    assert scenario.critique is not None
    copied = scenario.critique.model_copy(
        update={"attestation_id": f"{scenario.critique.attestation_id}-negative", **updates}
    )
    scenario.resolver.add_critique(copied)
    return copied


def _authorization(
    scenario,
    *,
    suffix: str = "review",
    reviewer_id: str = "reviewer-1",
    authorized: bool = True,
    authorized_at=None,
) -> ReviewerAuthorization:
    value = ReviewerAuthorization(
        authorization_id=f"authorization-{suffix}",
        reviewer_id=reviewer_id,
        reviewer_name="Dr Reviewer",
        authorizer_identity="offline-reviewer-registry",
        authorized=authorized,
        authorized_at=authorized_at or scenario.times[12],
        qualification="Qualified geologist",
    )
    scenario.resolver.add_authorization(
        value,
        authorizer=InMemoryReviewerAuthorizer((value,)),
        reviewed_at=value.authorized_at,
    )
    return value


def test_creation_and_authoritative_validation_transitions(scenario_factory) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.artifact.review_status is ReviewStatus.AI_DRAFT
    assert scenario.validation is not None
    assert scenario.critique is not None
    validated = validate_artifact(
        scenario.artifact,
        validation=scenario.validation,
        critique=scenario.critique,
        occurred_at=scenario.times[11],
        resolver=scenario.resolver,
    )
    assert validated.review_status is ReviewStatus.AI_VALIDATED
    scenario.catalog.update_artifact(validated, resolver=scenario.resolver)
    assert scenario.catalog.resolve_artifact(validated.content.reference) == validated


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"validated_content_sha256": "f" * 64}, "different content"),
        ({"validated_at": None}, "datetime"),
    ],
)
def test_validation_attestation_subject_and_time_are_enforced(
    scenario_factory,
    updates: dict[str, object],
    message: str,
) -> None:
    scenario = scenario_factory(prepare_review=True)
    if "validated_at" in updates:
        updates = updates | {"validated_at": scenario.times[3] - timedelta(seconds=1)}
        message = "predate"
    assert scenario.critique is not None
    with pytest.raises((ReviewTransitionError, ValidationError, ValueError), match=message):
        validation = _register_validation_copy(scenario, **updates)
        validate_artifact(
            scenario.artifact,
            validation=validation,
            critique=scenario.critique,
            occurred_at=scenario.times[11],
            resolver=scenario.resolver,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("critiqued_content_sha256", "f" * 64, "content"),
        ("generator_job_id", "unrelated-generator", "generator job"),
        ("critic_job_id", "unrelated-critic", "job"),
        ("critic_response_id", "unrelated-response", "response"),
        ("critic_request_fingerprint", "f" * 64, "fingerprint"),
        ("disposition", CritiqueVerdict.REJECT, "disposition"),
        ("independent_critic_policy_passed", False, "independent critic policy"),
    ],
)
def test_critique_attestation_mismatches_are_rejected(
    scenario_factory,
    field: str,
    value: object,
    message: str,
) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.validation is not None
    with pytest.raises((ReviewTransitionError, ArtifactResolutionError, ValueError), match=message):
        critique = _register_critique_copy(scenario, **{field: value})
        validate_artifact(
            scenario.artifact,
            validation=scenario.validation,
            critique=critique,
            occurred_at=scenario.times[11],
            resolver=scenario.resolver,
        )


def test_validation_event_cannot_precede_attestations(scenario_factory) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.validation is not None
    assert scenario.critique is not None
    with pytest.raises(ReviewTransitionError, match="postdate validation event"):
        validate_artifact(
            scenario.artifact,
            validation=scenario.validation,
            critique=scenario.critique,
            occurred_at=scenario.times[9],
            resolver=scenario.resolver,
        )


def test_critic_completion_must_precede_critique_across_reload_copy_and_authority_paths(
    scenario_factory,
) -> None:
    scenario = scenario_factory(
        prepare_review=True,
        critic_completed_index=11,
        critique_index=10,
        register_critique=False,
    )
    assert scenario.validation is not None
    assert scenario.critique is not None
    with pytest.raises(ArtifactContractError, match="critic completion"):
        scenario.resolver.add_critique(scenario.critique)

    class ResolverWithUninsertedCritique:
        def __getattr__(self, name: str):
            return getattr(scenario.resolver, name)

        def resolve_critique(self, attestation_id: str) -> CritiqueAttestation:
            if attestation_id != scenario.critique.attestation_id:
                raise LookupError(attestation_id)
            assert scenario.critique is not None
            return scenario.critique

    resolver = cast(ProvenanceResolver, ResolverWithUninsertedCritique())
    event = ArtifactValidatedEvent(
        artifact=scenario.artifact.content.reference,
        content_sha256=scenario.artifact.content.content_sha256,
        validation=scenario.validation,
        critique=scenario.critique,
        occurred_at=scenario.times[12],
    )
    values = {
        "content": scenario.artifact.content,
        "events": (*scenario.artifact.events, event),
    }
    candidates = (
        AIArtifact(**values),
        AIArtifact.model_validate(values),
        AIArtifact.model_validate_json(AIArtifact(**values).model_dump_json()),
        scenario.artifact.model_copy(update={"events": values["events"]}),
        scenario.artifact.copy(update={"events": values["events"]}),
    )
    for candidate in candidates:
        with pytest.raises(ArtifactContractError, match="critic completion"):
            validate_artifact_authority(candidate, resolver=resolver)
        with pytest.raises(ReviewTransitionError):
            effective_review_status(candidate, resolver=resolver)
    with pytest.raises(ArtifactContractError, match="critic completion"):
        scenario.catalog.update_artifact(candidates[0], resolver=resolver)


def test_same_generator_critic_configuration_requires_resolved_waiver(
    scenario_factory,
) -> None:
    scenario = scenario_factory(prepare_review=True, reuse_generator_configuration=True)
    assert scenario.validation is not None
    assert scenario.critique is not None
    assert scenario.waiver is not None
    with pytest.raises(ReviewTransitionError, match="requires a waiver"):
        validate_artifact(
            scenario.artifact,
            validation=scenario.validation,
            critique=scenario.critique,
            occurred_at=scenario.times[11],
            resolver=scenario.resolver,
        )
    validated = validate_artifact(
        scenario.artifact,
        validation=scenario.validation,
        critique=scenario.critique,
        waiver=scenario.waiver,
        occurred_at=scenario.times[11],
        resolver=scenario.resolver,
    )
    assert validated.review_status is ReviewStatus.AI_VALIDATED


def test_approval_requires_matching_resolved_authorization_after_validation(
    scenario_factory,
) -> None:
    scenario = scenario_factory(validate=True)
    authorization = _authorization(scenario)
    approved = approve_artifact(
        scenario.artifact,
        reviewer_id="reviewer-1",
        reviewed_at=scenario.times[13],
        review_note="approved synthetic artifact",
        authorizer=InMemoryReviewerAuthorizer((authorization,)),
        resolver=scenario.resolver,
    )
    assert approved.review_status is ReviewStatus.GEOLOGIST_APPROVED

    wrong_identity = _authorization(
        scenario,
        suffix="wrong-identity",
        reviewer_id="reviewer-2",
    )

    class WrongReviewerAuthorizer:
        def authorize(self, reviewer_id: str, *, reviewed_at):
            return wrong_identity

    with pytest.raises(ReviewTransitionError, match="another reviewer"):
        approve_artifact(
            scenario.artifact,
            reviewer_id="reviewer-1",
            reviewed_at=scenario.times[13],
            review_note="forged",
            authorizer=WrongReviewerAuthorizer(),
            resolver=scenario.resolver,
        )


def test_authorization_catalog_rejects_caller_record_not_issued_by_authorizer(
    scenario_factory,
) -> None:
    scenario = scenario_factory()
    supplied = ReviewerAuthorization(
        authorization_id="authorization-untrusted-caller",
        reviewer_id="reviewer-1",
        reviewer_name="Caller supplied name",
        authorizer_identity="offline-reviewer-registry",
        authorized=True,
        authorized_at=scenario.times[9],
        qualification="Caller supplied qualification",
    )
    trusted = supplied.model_copy(
        update={
            "reviewer_name": "Dr Trusted Reviewer",
            "qualification": "Qualified geologist",
        }
    )
    with pytest.raises(ArtifactIdentityCollisionError, match="trusted authorizer"):
        scenario.resolver.add_authorization(
            supplied,
            authorizer=InMemoryReviewerAuthorizer((trusted,)),
            reviewed_at=scenario.times[10],
        )


def test_authorization_cannot_predate_ai_validated_event(scenario_factory) -> None:
    scenario = scenario_factory(validate=True)
    authorization = _authorization(
        scenario,
        suffix="too-early",
        authorized_at=scenario.times[10],
    )
    with pytest.raises(ReviewTransitionError, match="follow AI_VALIDATED"):
        approve_artifact(
            scenario.artifact,
            reviewer_id="reviewer-1",
            reviewed_at=scenario.times[13],
            review_note="too early",
            authorizer=InMemoryReviewerAuthorizer((authorization,)),
            resolver=scenario.resolver,
        )


def test_rejection_is_terminal_and_authoritative(scenario_factory) -> None:
    scenario = scenario_factory()
    rejection_authorization = _authorization(
        scenario,
        suffix="rejection",
        authorized_at=scenario.times[9],
    )
    rejected = reject_artifact(
        scenario.artifact,
        basis=HumanRejectionBasis(authorization=rejection_authorization),
        occurred_at=scenario.times[10],
        note="rejected",
        resolver=scenario.resolver,
    )
    scenario.catalog.update_artifact(rejected, resolver=scenario.resolver)
    assert rejected.review_status is ReviewStatus.REJECTED
    authorization = _authorization(scenario)
    with pytest.raises(ReviewTransitionError, match="approval requires"):
        approve_artifact(
            rejected,
            reviewer_id="reviewer-1",
            reviewed_at=scenario.times[13],
            review_note="forbidden",
            authorizer=InMemoryReviewerAuthorizer((authorization,)),
            resolver=scenario.resolver,
        )


def test_failed_resolved_validation_is_an_authoritative_rejection_basis(
    scenario_factory,
) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.validation is not None
    failed_check = scenario.validation.checks[0].model_copy(update={"passed": False})
    failed = scenario.validation.model_copy(
        update={
            "attestation_id": "failed-required-validation",
            "checks": (failed_check, *scenario.validation.checks[1:]),
        }
    )
    scenario.resolver.add_validation(
        failed,
        validation_resolver=InMemoryValidationAttestationCatalog((failed,)),
    )
    rejected = reject_artifact(
        scenario.artifact,
        basis=ValidationRejectionBasis(validation=failed),
        occurred_at=scenario.times[11],
        note="required validation failed",
        resolver=scenario.resolver,
    )
    scenario.catalog.update_artifact(rejected, resolver=scenario.resolver)
    assert effective_review_status(rejected, resolver=scenario.resolver) is ReviewStatus.REJECTED


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("artifact", {"artifact_id": "wrong", "artifact_version": 1}, "artifact"),
        ("validated_content_sha256", "f" * 64, "content"),
        ("run_id", "wrong-run", "run"),
        ("phase_id", "wrong-phase", "phase"),
        ("task_type", "image_raster_interpretation", "task"),
        ("generator_job_id", "wrong-job", "generator job"),
        ("generator_response_id", "wrong-response", "generator response"),
    ],
)
def test_validation_rejection_basis_rejects_every_subject_cross_link(
    scenario_factory,
    field: str,
    value: object,
    message: str,
) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.validation is not None
    failed_check = scenario.validation.checks[0].model_copy(update={"passed": False})
    failed = scenario.validation.model_copy(
        update={
            "attestation_id": f"failed-{field}",
            "checks": (failed_check, *scenario.validation.checks[1:]),
            field: value,
        }
    )
    event = {
        "kind": "REJECTED",
        "artifact": scenario.artifact.content.reference,
        "content_sha256": scenario.artifact.content.content_sha256,
        "basis": {"kind": "VALIDATION", "validation": failed.model_dump(mode="python")},
        "note": "forged rejection",
        "occurred_at": scenario.times[11],
    }
    artifact_values = scenario.artifact.model_dump(mode="python")
    artifact_values["events"] = (*scenario.artifact.events, event)
    json_values = scenario.artifact.model_dump(mode="json")
    json_event = event | {
        "artifact": scenario.artifact.content.reference.model_dump(mode="json"),
        "basis": {"kind": "VALIDATION", "validation": failed.model_dump(mode="json")},
        "occurred_at": scenario.times[11].isoformat(),
    }
    json_values["events"] = [*json_values["events"], json_event]
    operations = (
        lambda: AIArtifact(**artifact_values),
        lambda: AIArtifact.model_validate(artifact_values),
        lambda: AIArtifact.model_validate_json(json.dumps(json_values)),
        lambda: scenario.artifact.model_copy(update={"events": artifact_values["events"]}),
        lambda: scenario.artifact.copy(update={"events": artifact_values["events"]}),
    )
    for operation in operations:
        with pytest.raises(ValidationError, match=message):
            operation()


def test_fabricated_validator_identity_cannot_become_authoritative_rejection(
    scenario_factory,
) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.validation is not None
    failed_check = scenario.validation.checks[0].model_copy(update={"passed": False})
    fabricated = scenario.validation.model_copy(
        update={
            "attestation_id": "fabricated-validator",
            "validator_identity": "fabricated-validator",
            "checks": (failed_check, *scenario.validation.checks[1:]),
        }
    )
    with pytest.raises(ArtifactResolutionError, match="validator registration"):
        scenario.resolver.add_validation(
            fabricated,
            validation_resolver=InMemoryValidationAttestationCatalog((fabricated,)),
        )


def test_validation_catalog_rejects_caller_attestation_not_issued_by_trusted_resolver(
    scenario_factory,
) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.validation is not None
    supplied = scenario.validation.model_copy(
        update={
            "attestation_id": "caller-validation",
            "findings": ("caller fabricated finding",),
        }
    )
    trusted = supplied.model_copy(update={"findings": ("trusted deterministic finding",)})
    with pytest.raises(ArtifactIdentityCollisionError, match="trusted resolver"):
        scenario.resolver.add_validation(
            supplied,
            validation_resolver=InMemoryValidationAttestationCatalog((trusted,)),
        )


def test_critique_rejection_basis_cannot_fabricate_reject_disposition(
    scenario_factory,
) -> None:
    scenario = scenario_factory(prepare_review=True)
    assert scenario.critique is not None
    event = {
        "kind": "REJECTED",
        "artifact": scenario.artifact.content.reference,
        "content_sha256": scenario.artifact.content.content_sha256,
        "basis": {
            "kind": "CRITIQUE",
            "critique": scenario.critique.model_dump(mode="python"),
        },
        "note": "fabricated disposition",
        "occurred_at": scenario.times[11],
    }
    with pytest.raises(ValidationError, match="REJECT disposition"):
        scenario.artifact.model_copy(update={"events": (*scenario.artifact.events, event)})


def test_resolved_rejecting_critique_is_an_authoritative_terminal_basis(
    scenario_factory,
) -> None:
    scenario = scenario_factory(
        prepare_review=True,
        critic_verdict=CritiqueVerdict.REJECT,
    )
    assert scenario.critique is not None
    rejected = reject_artifact(
        scenario.artifact,
        basis=CritiqueRejectionBasis(critique=scenario.critique),
        occurred_at=scenario.times[11],
        note="independent critic rejected the artifact",
        resolver=scenario.resolver,
    )
    scenario.catalog.update_artifact(rejected, resolver=scenario.resolver)
    assert effective_review_status(rejected, resolver=scenario.resolver) is ReviewStatus.REJECTED


def _supersession_authorization(
    old,
    replacement,
    *,
    suffix: str = "supersession",
    authorized_at=None,
):
    approved_at = authorized_at or replacement.times[13] + timedelta(minutes=1)
    authorization = ReviewerAuthorization(
        authorization_id=f"authorization-{suffix}",
        reviewer_id="reviewer-1",
        reviewer_name="Dr Reviewer",
        authorizer_identity="offline-reviewer-registry",
        authorized=True,
        authorized_at=approved_at,
        qualification="Qualified geologist",
    )
    old.resolver.add_authorization(
        authorization,
        authorizer=InMemoryReviewerAuthorizer((authorization,)),
        reviewed_at=authorization.authorized_at,
    )
    return authorization


def test_supersession_preserves_predecessor_bytes_and_effective_status(
    scenario_factory,
) -> None:
    old = scenario_factory(approve=True)
    old_bytes = old.artifact.model_dump_json().encode("utf-8")
    replacement = scenario_factory(
        artifact_id="artifact-1",
        artifact_version=2,
        parents=(old.artifact.content.reference,),
        summary="Corrected extraction",
        approve=True,
    )
    authorization = _supersession_authorization(old, replacement)
    record = create_supersession(
        supersession_id="supersession-1",
        old=old.artifact,
        replacement=replacement.artifact,
        reviewer_id="reviewer-1",
        superseded_at=authorization.authorized_at + timedelta(minutes=1),
        note="corrected content",
        authorizer=InMemoryReviewerAuthorizer((authorization,)),
        resolver=old.resolver,
    )
    old.catalog.add_supersession(record, resolver=old.resolver)
    assert old.artifact.model_dump_json().encode("utf-8") == old_bytes
    assert (
        old.catalog.resolve_artifact(old.artifact.content.reference)
        .model_dump_json()
        .encode("utf-8")
        == old_bytes
    )
    assert effective_review_status(old.artifact, resolver=old.resolver) is ReviewStatus.SUPERSEDED
    assert (
        effective_review_status(replacement.artifact, resolver=old.resolver)
        is ReviewStatus.GEOLOGIST_APPROVED
    )


def test_authoritative_approval_identity_uses_exact_persisted_bytes(scenario_factory) -> None:
    scenario = scenario_factory(approve=True)
    approval = scenario.artifact.events[-1]
    assert hasattr(approval, "reviewed_at")
    equivalent_offset = approval.reviewed_at.astimezone(timezone(timedelta(hours=8)))
    forged_approval = approval.model_copy(update={"reviewed_at": equivalent_offset})
    forged = scenario.artifact.model_copy(
        update={"events": (*scenario.artifact.events[:-1], forged_approval)}
    )
    assert forged_approval.reviewed_at == approval.reviewed_at
    with pytest.raises(ReviewTransitionError, match="authoritative catalog"):
        effective_review_status(forged, resolver=scenario.resolver)


def test_supersession_decimal_equivalent_content_is_not_a_change(scenario_factory) -> None:
    old = scenario_factory(approve=True, extracted_value=Decimal("1.2300"))
    replacement = scenario_factory(
        artifact_id="artifact-1",
        artifact_version=2,
        parents=(old.artifact.content.reference,),
        approve=True,
        extracted_value=Decimal("1.23"),
    )
    assert old.artifact.content.content_sha256 == replacement.artifact.content.content_sha256
    authorization = _supersession_authorization(old, replacement, suffix="decimal-equivalent")
    with pytest.raises(ReviewTransitionError, match="changed content"):
        create_supersession(
            supersession_id="decimal-equivalent",
            old=old.artifact,
            replacement=replacement.artifact,
            reviewer_id="reviewer-1",
            superseded_at=authorization.authorized_at + timedelta(minutes=1),
            note="numeric spelling only",
            authorizer=InMemoryReviewerAuthorizer((authorization,)),
            resolver=old.resolver,
        )


def test_supersession_chain_preserves_valid_historical_ordering(scenario_factory) -> None:
    first = scenario_factory(artifact_id="chain-a", approve=True)
    second = scenario_factory(
        artifact_id="chain-b",
        parents=(first.artifact.content.reference,),
        summary="chain b",
        approve=True,
    )
    third = scenario_factory(
        artifact_id="chain-c",
        parents=(second.artifact.content.reference,),
        summary="chain c",
        approve=True,
    )
    first_auth = _supersession_authorization(first, second, suffix="chain-a-b")
    first_record = create_supersession(
        supersession_id="chain-a-b",
        old=first.artifact,
        replacement=second.artifact,
        reviewer_id="reviewer-1",
        superseded_at=first_auth.authorized_at + timedelta(minutes=1),
        note="a to b",
        authorizer=InMemoryReviewerAuthorizer((first_auth,)),
        resolver=first.resolver,
    )
    first.catalog.add_supersession(first_record, resolver=first.resolver)
    second_auth = _supersession_authorization(second, third, suffix="chain-b-c")
    second_record = create_supersession(
        supersession_id="chain-b-c",
        old=second.artifact,
        replacement=third.artifact,
        reviewer_id="reviewer-1",
        superseded_at=second_auth.authorized_at + timedelta(minutes=1),
        note="b to c",
        authorizer=InMemoryReviewerAuthorizer((second_auth,)),
        resolver=first.resolver,
    )
    first.catalog.add_supersession(second_record, resolver=first.resolver)
    assert (
        effective_review_status(first.artifact, resolver=first.resolver) is ReviewStatus.SUPERSEDED
    )
    assert (
        effective_review_status(second.artifact, resolver=first.resolver) is ReviewStatus.SUPERSEDED
    )
    assert (
        effective_review_status(third.artifact, resolver=first.resolver)
        is ReviewStatus.GEOLOGIST_APPROVED
    )


@pytest.mark.parametrize("time_relation", ["simultaneous", "later"])
def test_already_superseded_artifact_cannot_be_reused_as_replacement(
    scenario_factory,
    time_relation: str,
) -> None:
    predecessor = scenario_factory(artifact_id=f"reuse-a-{time_relation}", approve=True)
    replacement = scenario_factory(
        artifact_id=f"reuse-b-{time_relation}",
        parents=(predecessor.artifact.content.reference,),
        summary="replacement b",
        approve=True,
    )
    final = scenario_factory(
        artifact_id=f"reuse-c-{time_relation}",
        parents=(replacement.artifact.content.reference,),
        summary="replacement c",
        approve=True,
    )
    replacement_auth = _supersession_authorization(
        replacement,
        final,
        suffix=f"reuse-b-c-{time_relation}",
    )
    replacement_time = replacement_auth.authorized_at + timedelta(minutes=1)
    replacement_record = create_supersession(
        supersession_id=f"reuse-b-c-{time_relation}",
        old=replacement.artifact,
        replacement=final.artifact,
        reviewer_id="reviewer-1",
        superseded_at=replacement_time,
        note="b to c",
        authorizer=InMemoryReviewerAuthorizer((replacement_auth,)),
        resolver=predecessor.resolver,
    )
    predecessor.catalog.add_supersession(replacement_record, resolver=predecessor.resolver)
    proposed_time = (
        replacement_time
        if time_relation == "simultaneous"
        else replacement_time + timedelta(minutes=1)
    )
    reuse_auth = _supersession_authorization(
        predecessor,
        replacement,
        suffix=f"reuse-a-b-{time_relation}",
        authorized_at=proposed_time,
    )
    with pytest.raises(ReviewTransitionError, match="effectively GEOLOGIST_APPROVED"):
        create_supersession(
            supersession_id=f"reuse-a-b-{time_relation}",
            old=predecessor.artifact,
            replacement=replacement.artifact,
            reviewer_id="reviewer-1",
            superseded_at=proposed_time,
            note="invalid reuse",
            authorizer=InMemoryReviewerAuthorizer((reuse_auth,)),
            resolver=predecessor.resolver,
        )


@pytest.mark.parametrize(
    ("replacement_mode", "message"),
    [
        ("unapproved", "must be GEOLOGIST_APPROVED"),
        ("same-content", "changed content"),
        ("missing-lineage", "explicitly reference"),
        ("self", "cannot supersede itself"),
    ],
)
def test_supersession_rejects_every_invalid_replacement(
    scenario_factory,
    replacement_mode: str,
    message: str,
) -> None:
    old = scenario_factory(approve=True)
    if replacement_mode == "self":
        replacement = old
    else:
        replacement = scenario_factory(
            artifact_id="artifact-1",
            artifact_version=2,
            parents=()
            if replacement_mode == "missing-lineage"
            else (old.artifact.content.reference,),
            summary=(
                "Synthetic extraction"
                if replacement_mode == "same-content"
                else "Corrected extraction"
            ),
            approve=replacement_mode != "unapproved",
        )
    authorization = _supersession_authorization(old, replacement, suffix=replacement_mode)
    with pytest.raises(ReviewTransitionError, match=message):
        create_supersession(
            supersession_id=f"supersession-{replacement_mode}",
            old=old.artifact,
            replacement=replacement.artifact,
            reviewer_id="reviewer-1",
            superseded_at=authorization.authorized_at + timedelta(minutes=1),
            note="invalid replacement test",
            authorizer=InMemoryReviewerAuthorizer((authorization,)),
            resolver=old.resolver,
        )


def test_supersession_must_follow_both_approvals_and_authorization(scenario_factory) -> None:
    old = scenario_factory(approve=True)
    replacement = scenario_factory(
        artifact_id="artifact-1",
        artifact_version=2,
        parents=(old.artifact.content.reference,),
        summary="Corrected extraction",
        approve=True,
    )
    too_early = replacement.times[13]
    authorization = ReviewerAuthorization(
        authorization_id="authorization-too-early-supersession",
        reviewer_id="reviewer-1",
        reviewer_name="Dr Reviewer",
        authorizer_identity="offline-reviewer-registry",
        authorized=True,
        authorized_at=too_early - timedelta(minutes=1),
        qualification="Qualified geologist",
    )
    old.resolver.add_authorization(
        authorization,
        authorizer=InMemoryReviewerAuthorizer((authorization,)),
        reviewed_at=authorization.authorized_at,
    )
    with pytest.raises(ReviewTransitionError, match="after both approvals"):
        create_supersession(
            supersession_id="supersession-too-early",
            old=old.artifact,
            replacement=replacement.artifact,
            reviewer_id="reviewer-1",
            superseded_at=too_early,
            note="too early",
            authorizer=InMemoryReviewerAuthorizer((authorization,)),
            resolver=old.resolver,
        )


def test_unresolvable_serialized_supersession_never_changes_status(scenario_factory) -> None:
    old = scenario_factory(approve=True)
    authorization = ReviewerAuthorization(
        authorization_id="authorization-unresolved",
        reviewer_id="reviewer-1",
        reviewer_name="Dr Reviewer",
        authorizer_identity="offline-reviewer-registry",
        authorized=True,
        authorized_at=old.times[13] + timedelta(minutes=1),
        qualification="Qualified geologist",
    )
    old.resolver.add_authorization(
        authorization,
        authorizer=InMemoryReviewerAuthorizer((authorization,)),
        reviewed_at=authorization.authorized_at,
    )
    record = SupersessionRecord(
        supersession_id="unresolved",
        superseded=old.artifact.content.reference,
        replacement=old.artifact.content.reference.model_copy(update={"artifact_version": 99}),
        reviewer_authorization=authorization,
        superseded_at=authorization.authorized_at + timedelta(minutes=1),
        note="unresolvable",
    )
    reloaded = SupersessionRecord.model_validate_json(record.model_dump_json())
    assert (
        effective_review_status(old.artifact, resolver=old.resolver)
        is ReviewStatus.GEOLOGIST_APPROVED
    )
    with pytest.raises(ArtifactResolutionError, match="not found"):
        old.catalog.add_supersession(reloaded, resolver=old.resolver)
