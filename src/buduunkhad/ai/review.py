"""Validated lifecycle operations over immutable AI artifact records."""

from __future__ import annotations

from datetime import datetime

from buduunkhad.ai.artifacts import (
    AIArtifact,
    ArtifactContractError,
    ArtifactRejectedEvent,
    ArtifactValidatedEvent,
    CritiqueAttestation,
    GeneratorCriticWaiver,
    HumanApprovalAttestation,
    RejectionBasis,
    ReviewerAuthorization,
    ReviewerAuthorizer,
    SupersessionRecord,
    ValidationAttestation,
    validate_artifact_authority,
)
from buduunkhad.ai.catalog import ProvenanceResolver
from buduunkhad.ai.contracts import ReviewStatus, require_aware_datetime
from buduunkhad.ai.fingerprint import persisted_model_bytes, persisted_model_sha256


class ReviewTransitionError(ArtifactContractError):
    """Raised when a lifecycle operation violates the immutable state machine."""


class InMemoryReviewerAuthorizer:
    """Offline authorizer; production reviewer identity is deliberately deferred."""

    def __init__(
        self,
        reviewers: tuple[ReviewerAuthorization, ...],
        *,
        authorizer_identity: str = "offline-reviewer-registry",
    ) -> None:
        self._reviewers = {reviewer.reviewer_id: reviewer for reviewer in reviewers}
        self.authorizer_identity = authorizer_identity
        if len(self._reviewers) != len(reviewers):
            raise ValueError("duplicate reviewer IDs")

    def authorize(self, reviewer_id: str, *, reviewed_at: datetime) -> ReviewerAuthorization:
        require_aware_datetime(reviewed_at, "reviewed_at")
        try:
            authorization = self._reviewers[reviewer_id]
        except KeyError as exc:
            raise ReviewTransitionError(f"reviewer is not registered: {reviewer_id}") from exc
        if authorization.reviewer_id != reviewer_id:
            raise ReviewTransitionError("authorizer returned a different reviewer identity")
        if not authorization.authorized:
            raise ReviewTransitionError(f"reviewer is not authorized: {reviewer_id}")
        if authorization.authorizer_identity != self.authorizer_identity:
            raise ReviewTransitionError("reviewer authorization has an unexpected authorizer")
        if authorization.authorized_at > reviewed_at:
            raise ReviewTransitionError("reviewer authorization postdates the review")
        return authorization


def validate_artifact(
    artifact: AIArtifact,
    *,
    validation: ValidationAttestation,
    critique: CritiqueAttestation,
    occurred_at: datetime,
    resolver: ProvenanceResolver,
    waiver: GeneratorCriticWaiver | None = None,
) -> AIArtifact:
    _require_current_authoritative_artifact(artifact, resolver)
    if artifact.review_status is not ReviewStatus.AI_DRAFT:
        raise ReviewTransitionError("only AI_DRAFT content can be validated")
    if persisted_model_bytes(
        resolver.resolve_validation(validation.attestation_id)
    ) != persisted_model_bytes(validation):
        raise ReviewTransitionError("validation attestation is not authoritative")
    if persisted_model_bytes(
        resolver.resolve_critique(critique.attestation_id)
    ) != persisted_model_bytes(critique):
        raise ReviewTransitionError("critique attestation is not authoritative")
    if waiver is not None and persisted_model_bytes(
        resolver.resolve_waiver(waiver.waiver_id)
    ) != persisted_model_bytes(waiver):
        raise ReviewTransitionError("generator/critic waiver is not authoritative")
    event = ArtifactValidatedEvent(
        artifact=artifact.content.reference,
        content_sha256=artifact.content.content_sha256,
        validation=validation,
        critique=critique,
        waiver=waiver,
        occurred_at=occurred_at,
    )
    try:
        result = artifact.model_copy(update={"events": (*artifact.events, event)})
        validate_artifact_authority(result, resolver=resolver)
        return result
    except (LookupError, ValueError) as exc:
        raise ReviewTransitionError(str(exc)) from exc


def reject_artifact(
    artifact: AIArtifact,
    *,
    basis: RejectionBasis,
    occurred_at: datetime,
    note: str,
    resolver: ProvenanceResolver,
) -> AIArtifact:
    _require_current_authoritative_artifact(artifact, resolver)
    if artifact.review_status not in {ReviewStatus.AI_DRAFT, ReviewStatus.AI_VALIDATED}:
        raise ReviewTransitionError("only AI_DRAFT or AI_VALIDATED content can be rejected")
    event = ArtifactRejectedEvent(
        artifact=artifact.content.reference,
        content_sha256=artifact.content.content_sha256,
        basis=basis,
        note=note,
        occurred_at=occurred_at,
    )
    try:
        result = artifact.model_copy(update={"events": (*artifact.events, event)})
        validate_artifact_authority(result, resolver=resolver)
        return result
    except (LookupError, ValueError) as exc:
        raise ReviewTransitionError(str(exc)) from exc


def approve_artifact(
    artifact: AIArtifact,
    *,
    reviewer_id: str,
    reviewed_at: datetime,
    review_note: str,
    authorizer: ReviewerAuthorizer,
    resolver: ProvenanceResolver,
) -> AIArtifact:
    _require_current_authoritative_artifact(artifact, resolver)
    if artifact.review_status is not ReviewStatus.AI_VALIDATED:
        raise ReviewTransitionError("approval requires AI_VALIDATED content")
    authorization = authorizer.authorize(reviewer_id, reviewed_at=reviewed_at)
    if authorization.reviewer_id != reviewer_id:
        raise ReviewTransitionError("authorizer returned authorization for another reviewer")
    if persisted_model_bytes(
        resolver.resolve_authorization(authorization.authorization_id)
    ) != persisted_model_bytes(authorization):
        raise ReviewTransitionError("reviewer authorization is not authoritative")
    event = HumanApprovalAttestation(
        artifact=artifact.content.reference,
        content_sha256=artifact.content.content_sha256,
        authorization=authorization,
        reviewed_at=reviewed_at,
        review_note=review_note,
    )
    try:
        result = artifact.model_copy(update={"events": (*artifact.events, event)})
        validate_artifact_authority(result, resolver=resolver)
        return result
    except (LookupError, ValueError) as exc:
        raise ReviewTransitionError(str(exc)) from exc


def create_supersession(
    *,
    supersession_id: str,
    old: AIArtifact,
    replacement: AIArtifact,
    reviewer_id: str,
    superseded_at: datetime,
    note: str,
    authorizer: ReviewerAuthorizer,
    resolver: ProvenanceResolver,
) -> SupersessionRecord:
    _require_current_authoritative_artifact(old, resolver)
    _require_current_authoritative_artifact(replacement, resolver)
    before = persisted_model_bytes(old)
    authorization = authorizer.authorize(reviewer_id, reviewed_at=superseded_at)
    if authorization.reviewer_id != reviewer_id:
        raise ReviewTransitionError("authorizer returned authorization for another reviewer")
    if persisted_model_bytes(
        resolver.resolve_authorization(authorization.authorization_id)
    ) != persisted_model_bytes(authorization):
        raise ReviewTransitionError("supersession authorization is not authoritative")
    try:
        record = SupersessionRecord(
            supersession_id=supersession_id,
            superseded=old.content.reference,
            replacement=replacement.content.reference,
            reviewer_authorization=authorization,
            superseded_at=superseded_at,
            note=note,
        )
        validate_supersession_record(record, resolver=resolver)
    except (LookupError, ValueError) as exc:
        raise ReviewTransitionError(str(exc)) from exc
    if persisted_model_bytes(old) != before:
        raise ReviewTransitionError("supersession mutated approved predecessor bytes")
    return record


def validate_supersession_record(
    record: SupersessionRecord,
    *,
    resolver: ProvenanceResolver,
) -> None:
    """Resolve a supersession record before it can affect authoritative status."""
    old = resolver.resolve_artifact(record.superseded)
    replacement = resolver.resolve_artifact(record.replacement)
    validate_artifact_authority(old, resolver=resolver)
    validate_artifact_authority(replacement, resolver=resolver)
    if old.content.reference == replacement.content.reference:
        raise ReviewTransitionError("an artifact version cannot supersede itself")
    if old.review_status is not ReviewStatus.GEOLOGIST_APPROVED:
        raise ReviewTransitionError("only a GEOLOGIST_APPROVED artifact can be superseded")
    if replacement.review_status is not ReviewStatus.GEOLOGIST_APPROVED:
        raise ReviewTransitionError("replacement artifact must be GEOLOGIST_APPROVED")
    replacement_supersession = resolver.resolve_supersession(replacement.content.reference)
    if (
        replacement_supersession is not None
        and replacement_supersession.superseded_at <= record.superseded_at
    ):
        raise ReviewTransitionError(
            "replacement must still be effectively GEOLOGIST_APPROVED at supersession time"
        )
    if old.content.content_sha256 == replacement.content.content_sha256:
        raise ReviewTransitionError("replacement must contain changed content")
    if old.content.reference not in replacement.content.parent_artifacts:
        raise ReviewTransitionError("replacement must explicitly reference the predecessor")
    old_approval = _approval_time(old)
    replacement_approval = _approval_time(replacement)
    if record.superseded_at <= max(old_approval, replacement_approval):
        raise ReviewTransitionError("supersession must occur after both approvals")
    authorization = resolver.resolve_authorization(record.reviewer_authorization.authorization_id)
    if persisted_model_bytes(authorization) != persisted_model_bytes(record.reviewer_authorization):
        raise ReviewTransitionError("supersession authorization is not authoritative")
    if authorization.authorized_at < max(old_approval, replacement_approval):
        raise ReviewTransitionError("supersession authorization must follow both approvals")
    if authorization.authorized_at > record.superseded_at:
        raise ReviewTransitionError("supersession authorization postdates supersession")


def effective_review_status(
    artifact: AIArtifact,
    *,
    resolver: ProvenanceResolver,
) -> ReviewStatus:
    _require_current_authoritative_artifact(artifact, resolver)
    supersession = resolver.resolve_supersession(artifact.content.reference)
    if supersession is None:
        return artifact.review_status
    validate_supersession_record(supersession, resolver=resolver)
    if supersession.superseded != artifact.content.reference:
        raise ReviewTransitionError("supersession does not reference the artifact")
    return ReviewStatus.SUPERSEDED


def _require_current_authoritative_artifact(
    artifact: AIArtifact,
    resolver: ProvenanceResolver,
) -> None:
    try:
        authoritative = resolver.resolve_artifact(artifact.content.reference)
        if persisted_model_sha256(authoritative) != persisted_model_sha256(artifact):
            raise ReviewTransitionError("artifact does not match the authoritative catalog")
        validate_artifact_authority(artifact, resolver=resolver)
    except (LookupError, ValueError) as exc:
        if isinstance(exc, ReviewTransitionError):
            raise
        raise ReviewTransitionError(str(exc)) from exc


def _approval_time(artifact: AIArtifact) -> datetime:
    approvals = [
        event.reviewed_at
        for event in artifact.events
        if isinstance(event, HumanApprovalAttestation)
    ]
    if len(approvals) != 1:
        raise ReviewTransitionError("approved artifact must contain exactly one approval")
    return approvals[0]
