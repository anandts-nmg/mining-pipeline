"""Runtime execution modes and narrowly scoped authorization records.

The methodology readiness registry remains a planning/evidence view.  This module loads the
separate execution-policy contract that translates the current implementation state and open
readiness obligations into conservative runtime permissions.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from enum import StrEnum
from importlib import resources
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from buduunkhad.ai.fingerprint import sha256_bytes, sha256_value
from buduunkhad.core.run_artifacts import has_symlink_component

_PHASE_IDS = tuple(f"{value:02d}" for value in range(12)) + ("99",)
_AUTH_PREFIX = "exec-auth-"
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class ExecutionPolicyError(RuntimeError):
    """Raised when a requested run purpose or authorization is not permitted."""


class ExecutionMode(StrEnum):
    SCAFFOLD = "scaffold"
    SUPPORT_EVIDENCE = "support-evidence"
    LEGACY_COMPARATOR = "legacy-comparator"
    AUTHORITATIVE = "authoritative"
    PUBLICATION = "publication"


class AuthorizationAction(StrEnum):
    RAW_IDENTITY_TRANSITION = "RawIdentityTransition"
    OPERATIONAL_EXCEPTION = "OperationalException"
    DATA_GAP_ACKNOWLEDGEMENT = "DataGapAcknowledgement"


class BlockedExecutionMode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: ExecutionMode
    readiness_ids: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _valid_block(self) -> BlockedExecutionMode:
        if self.mode in {ExecutionMode.SCAFFOLD, ExecutionMode.PUBLICATION}:
            raise ValueError("scaffold/publication cannot be a blocked real phase mode")
        if len(set(self.readiness_ids)) != len(self.readiness_ids):
            raise ValueError("blocked execution mode repeats readiness IDs")
        return self


class PhaseExecutionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase_id: str = Field(pattern=r"^(?:0[0-9]|1[01]|99)$")
    default_real_mode: ExecutionMode | None
    permitted_real_modes: tuple[ExecutionMode, ...]
    blocked_modes: tuple[BlockedExecutionMode, ...]

    @model_validator(mode="after")
    def _coherent_modes(self) -> PhaseExecutionPolicy:
        permitted = self.permitted_real_modes
        blocked = tuple(item.mode for item in self.blocked_modes)
        if len(set(permitted)) != len(permitted) or len(set(blocked)) != len(blocked):
            raise ValueError("phase execution policy repeats a mode")
        if set(permitted) & set(blocked):
            raise ValueError("phase execution mode cannot be both permitted and blocked")
        if any(mode is ExecutionMode.PUBLICATION for mode in permitted):
            raise ValueError("publication is an operation, not a phase execution mode")
        if self.default_real_mode is None:
            if permitted:
                raise ValueError("phase with permitted real modes requires a default")
        elif self.default_real_mode not in permitted:
            raise ValueError("default real mode must be permitted")
        return self


class PublicationExecutionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    approved_source_modes: tuple[ExecutionMode, ...]
    provisional_source_modes: tuple[ExecutionMode, ...]

    @model_validator(mode="after")
    def _coherent_publication_modes(self) -> PublicationExecutionPolicy:
        approved = set(self.approved_source_modes)
        provisional = set(self.provisional_source_modes)
        if approved != {ExecutionMode.AUTHORITATIVE}:
            raise ValueError("only authoritative runs may support APPROVED publication")
        if approved & provisional:
            raise ValueError("publication source modes overlap")
        expected = {
            ExecutionMode.SCAFFOLD,
            ExecutionMode.SUPPORT_EVIDENCE,
            ExecutionMode.LEGACY_COMPARATOR,
        }
        if provisional != expected:
            raise ValueError("publication provisional modes are incomplete")
        return self


class OperationalExceptionControl(BaseModel):
    """One explicitly classified non-scientific QA/QC failure that may be waived."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    control_id: str = Field(pattern=r"^OPERATIONAL-EXCEPTION-[A-Z0-9-]+$")
    phase_id: str = Field(pattern=r"^(?:0[0-9]|1[01]|99)$")
    qaqc_items: tuple[str, ...] = Field(min_length=1)
    permitted_modes: tuple[ExecutionMode, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _coherent_control(self) -> OperationalExceptionControl:
        if len(set(self.qaqc_items)) != len(self.qaqc_items):
            raise ValueError("operational-exception control repeats QA/QC items")
        if len(set(self.permitted_modes)) != len(self.permitted_modes):
            raise ValueError("operational-exception control repeats execution modes")
        if any(
            mode in {ExecutionMode.AUTHORITATIVE, ExecutionMode.PUBLICATION}
            for mode in self.permitted_modes
        ):
            raise ValueError("operational exceptions cannot grant authoritative execution")
        if self.phase_id in {"00", "03", "04", "05"}:
            raise ValueError("raw, scientific, comparator and flight controls are non-overridable")
        return self


class ExecutionPolicyRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    interpretation: Literal[
        "Runtime execution permissions derived from implementation state and open readiness "
        "obligations; not scientific approval or evidence that an obligation is resolved."
    ]
    phase_policies: tuple[PhaseExecutionPolicy, ...]
    operational_exception_controls: tuple[OperationalExceptionControl, ...]
    publication_policy: PublicationExecutionPolicy

    @model_validator(mode="after")
    def _complete_registry(self) -> ExecutionPolicyRegistry:
        phase_ids = tuple(item.phase_id for item in self.phase_policies)
        if phase_ids != _PHASE_IDS:
            raise ValueError("execution policy must cover phases 00-11 and 99 in order")
        control_ids = tuple(item.control_id for item in self.operational_exception_controls)
        if len(set(control_ids)) != len(control_ids):
            raise ValueError("execution policy repeats an operational-exception control")
        return self


class PhaseModeBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase_id: str = Field(pattern=r"^(?:0[0-9]|1[01]|99)$")
    execution_mode: ExecutionMode


class ExecutionPolicyBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    policy_sha256: Sha256
    phase_modes: tuple[PhaseModeBinding, ...]

    @model_validator(mode="after")
    def _unique_ordered_phases(self) -> ExecutionPolicyBinding:
        phase_ids = tuple(item.phase_id for item in self.phase_modes)
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("execution-policy binding repeats phase IDs")
        if tuple(sorted(phase_ids, key=_PHASE_IDS.index)) != phase_ids:
            raise ValueError("execution-policy binding phases are out of order")
        return self


class ExecutionAuthorizationIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"] = "1.0.0"
    action: AuthorizationAction
    actor: str = Field(min_length=1)
    authorization_reference: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    old_identity_sha256: Sha256 | None = None
    new_identity_sha256: Sha256 | None = None
    recorded_at: datetime
    scope_phase_ids: tuple[str, ...] = Field(min_length=1)
    validity: Literal["until-expiry", "until-superseded"]
    expires_at: datetime | None = None
    supersedes_authorization_id: str | None = Field(
        default=None, pattern=r"^exec-auth-[0-9a-f]{64}$"
    )
    resulting_permitted_mode: ExecutionMode

    @model_validator(mode="after")
    def _coherent_identity(self) -> ExecutionAuthorizationIdentity:
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("execution authorization timestamp must be timezone-aware")
        if self.recorded_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("execution authorization timestamp must be recorded in UTC")
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
                raise ValueError("execution authorization expiry must be timezone-aware")
            if self.expires_at.utcoffset() != UTC.utcoffset(None):
                raise ValueError("execution authorization expiry must be recorded in UTC")
            if self.expires_at <= self.recorded_at:
                raise ValueError("execution authorization expiry must follow its timestamp")
        if self.validity == "until-expiry" and self.expires_at is None:
            raise ValueError("expiring execution authorization requires an expiry")
        if self.validity == "until-superseded" and self.expires_at is not None:
            raise ValueError("until-superseded authorization must not carry an expiry")
        if len(set(self.scope_phase_ids)) != len(self.scope_phase_ids) or any(
            phase not in _PHASE_IDS for phase in self.scope_phase_ids
        ):
            raise ValueError("execution authorization phase scope is invalid")
        if self.resulting_permitted_mode is ExecutionMode.PUBLICATION:
            raise ValueError("phase authorization cannot grant publication mode")
        raw_action = self.action is AuthorizationAction.RAW_IDENTITY_TRANSITION
        if raw_action:
            if (
                self.subject != "raw-archive"
                or self.old_identity_sha256 is None
                or self.new_identity_sha256 is None
                or self.old_identity_sha256 == self.new_identity_sha256
            ):
                raise ValueError("raw identity transition requires exact distinct identities")
        elif self.old_identity_sha256 is not None or self.new_identity_sha256 is not None:
            raise ValueError("only raw identity transitions may carry old/new identities")
        if self.action is AuthorizationAction.DATA_GAP_ACKNOWLEDGEMENT:
            if not self.subject.startswith("raw-input:"):
                raise ValueError("data-gap acknowledgement requires a raw-input subject")
            if self.resulting_permitted_mode is ExecutionMode.AUTHORITATIVE:
                raise ValueError("a data gap cannot grant authoritative execution")
            if self.validity != "until-expiry":
                raise ValueError("data-gap acknowledgement must expire")
        if self.action is AuthorizationAction.OPERATIONAL_EXCEPTION:
            if (
                re.fullmatch(
                    r"phase-gate:(?:0[0-9]|1[01]|99):OPERATIONAL-EXCEPTION-[A-Z0-9-]+",
                    self.subject,
                )
                is None
            ):
                raise ValueError("operational exception requires an exact phase-gate subject")
            if set(self.scope_phase_ids) & {"03", "04", "05"}:
                raise ValueError("scientific, comparator and flight gates are non-overridable")
            if self.resulting_permitted_mode is ExecutionMode.AUTHORITATIVE:
                raise ValueError("an operational exception cannot grant authoritative execution")
            if self.validity != "until-expiry":
                raise ValueError("operational exception must expire")
        return self


class ExecutionAuthorization(ExecutionAuthorizationIdentity):
    authorization_id: str = Field(pattern=r"^exec-auth-[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _identity_matches(self) -> ExecutionAuthorization:
        identity = ExecutionAuthorizationIdentity.model_validate(
            self.model_dump(mode="python", exclude={"authorization_id"})
        )
        expected = _AUTH_PREFIX + sha256_value(identity)
        if self.authorization_id != expected:
            raise ValueError("execution authorization ID does not match its identity fields")
        return self

    @classmethod
    def create(cls, **values: object) -> Self:
        identity = ExecutionAuthorizationIdentity.model_validate(values)
        return cls(
            **identity.model_dump(mode="python"),
            authorization_id=_AUTH_PREFIX + sha256_value(identity),
        )


def _policy_bytes() -> bytes:
    filename = "execution_policy.yaml"
    try:
        return resources.files("buduunkhad").joinpath("methodology_data", filename).read_bytes()
    except (FileNotFoundError, OSError):
        path = Path(__file__).parents[3] / "config" / "methodology" / filename
        try:
            return path.read_bytes()
        except OSError as exc:
            raise ExecutionPolicyError("execution-policy resource is unavailable") from exc


def load_execution_policy() -> ExecutionPolicyRegistry:
    payload = _policy_bytes()
    try:
        registry = ExecutionPolicyRegistry.model_validate(yaml.safe_load(payload))
    except (yaml.YAMLError, ValueError) as exc:
        raise ExecutionPolicyError("execution-policy contract is invalid") from exc

    # Import locally so the methodology models remain independent of runtime policy code.
    from buduunkhad.geospatial_ai.methodology import load_automation_readiness

    readiness = {item.obligation_id: item for item in load_automation_readiness().obligations}
    policies = {item.phase_id: item for item in registry.phase_policies}
    for phase in registry.phase_policies:
        for blocked in phase.blocked_modes:
            for identity in blocked.readiness_ids:
                obligation = readiness.get(identity)
                if obligation is None or phase.phase_id not in obligation.affected_phases:
                    raise ExecutionPolicyError(
                        "execution policy references an inapplicable readiness obligation"
                    )
    for control in registry.operational_exception_controls:
        if not set(control.permitted_modes) <= set(policies[control.phase_id].permitted_real_modes):
            raise ExecutionPolicyError(
                "operational-exception control permits an unavailable execution mode"
            )
    return registry


def resolve_execution_policy(
    selected_phases: list[str],
    *,
    dry_run: bool,
    requested_modes: dict[str, ExecutionMode] | None = None,
) -> ExecutionPolicyBinding:
    registry = load_execution_policy()
    policies = {item.phase_id: item for item in registry.phase_policies}
    requested = dict(requested_modes or {})
    unexpected = sorted(set(requested) - set(selected_phases))
    if unexpected:
        raise ExecutionPolicyError(
            f"execution modes were supplied for unselected phases: {unexpected}"
        )

    bindings: list[PhaseModeBinding] = []
    for phase_id in selected_phases:
        policy = policies[phase_id]
        if dry_run:
            mode = requested.get(phase_id, ExecutionMode.SCAFFOLD)
            if mode is not ExecutionMode.SCAFFOLD:
                raise ExecutionPolicyError("dry runs permit scaffold mode only")
        else:
            mode = requested.get(phase_id, policy.default_real_mode)
            if mode is None:
                raise ExecutionPolicyError(f"Phase {phase_id} has no real execution mode")
            if mode not in policy.permitted_real_modes:
                blocked = next((item for item in policy.blocked_modes if item.mode is mode), None)
                if blocked is not None:
                    raise ExecutionPolicyError(
                        f"Phase {phase_id} {mode.value} mode is blocked by open readiness "
                        f"obligations: {list(blocked.readiness_ids)}"
                    )
                raise ExecutionPolicyError(f"Phase {phase_id} does not implement {mode.value} mode")
        bindings.append(PhaseModeBinding(phase_id=phase_id, execution_mode=mode))

    return ExecutionPolicyBinding(
        format_version=registry.format_version,
        policy_sha256=sha256_bytes(_policy_bytes()),
        phase_modes=tuple(bindings),
    )


def validate_execution_policy_binding(
    binding: ExecutionPolicyBinding,
    selected_phases: list[str],
    *,
    dry_run: bool,
) -> None:
    """Re-resolve a persisted binding against the repository-controlled policy bytes."""

    requested = {item.phase_id: item.execution_mode for item in binding.phase_modes}
    current = resolve_execution_policy(
        selected_phases,
        dry_run=dry_run,
        requested_modes=requested,
    )
    if current != binding:
        raise ExecutionPolicyError(
            "execution-policy binding does not match the repository-controlled contract"
        )


def load_execution_authorizations(paths: list[Path] | None) -> tuple[ExecutionAuthorization, ...]:
    records: list[ExecutionAuthorization] = []
    for source in paths or []:
        path = Path(source).absolute()
        if has_symlink_component(path) or not path.is_file() or path.is_symlink():
            raise ExecutionPolicyError(
                f"execution authorization must be a regular link-free file: {source}"
            )
        try:
            value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
            records.append(ExecutionAuthorization.model_validate(value))
        except (OSError, UnicodeError, ValueError) as exc:
            raise ExecutionPolicyError(f"execution authorization is invalid: {source}") from exc
    identities = tuple(item.authorization_id for item in records)
    if len(set(identities)) != len(identities):
        raise ExecutionPolicyError("execution authorization selection contains duplicates")
    return tuple(records)


def validate_authorizations_for_run(
    authorizations: tuple[ExecutionAuthorization, ...],
    binding: ExecutionPolicyBinding,
    *,
    now: datetime | None = None,
) -> None:
    selected_modes = {item.phase_id: item.execution_mode for item in binding.phase_modes}
    instant = (now or datetime.now(UTC)).astimezone(UTC)
    selected_ids = {item.authorization_id for item in authorizations}
    claims: dict[tuple[AuthorizationAction, str, str], str] = {}
    for record in authorizations:
        if record.supersedes_authorization_id in selected_ids:
            raise ExecutionPolicyError(
                "an execution authorization and its superseded record cannot both be selected"
            )
        if record.recorded_at > instant:
            raise ExecutionPolicyError(
                f"execution authorization is not yet valid: {record.authorization_id}"
            )
        if record.expires_at is not None and record.expires_at <= instant:
            raise ExecutionPolicyError(
                f"execution authorization is expired: {record.authorization_id}"
            )
        if not set(record.scope_phase_ids) <= set(selected_modes):
            raise ExecutionPolicyError(
                f"execution authorization scope includes unselected phases: {record.authorization_id}"
            )
        if any(
            selected_modes[phase] is not record.resulting_permitted_mode
            for phase in record.scope_phase_ids
        ):
            raise ExecutionPolicyError(
                f"execution authorization mode does not match its scoped phases: {record.authorization_id}"
            )
        for phase_id in record.scope_phase_ids:
            key = (record.action, record.subject, phase_id)
            previous = claims.get(key)
            if previous is not None:
                raise ExecutionPolicyError(
                    "execution authorizations contain overlapping claims: "
                    f"{previous}; {record.authorization_id}"
                )
            claims[key] = record.authorization_id


def phase_gate_subject(phase_id: str, control_id: str) -> str:
    """Return the stable subject for one explicitly classified gate control."""

    if (
        re.fullmatch(r"(?:0[0-9]|1[01]|99)", phase_id) is None
        or re.fullmatch(r"OPERATIONAL-EXCEPTION-[A-Z0-9-]+", control_id) is None
    ):
        raise ExecutionPolicyError("operational-exception control identity is invalid")
    return f"phase-gate:{phase_id}:{control_id}"


def legacy_execution_mode(phase_id: str, *, dry_run: bool = False) -> ExecutionMode:
    if dry_run:
        return ExecutionMode.SCAFFOLD
    defaults = {
        "00": ExecutionMode.AUTHORITATIVE,
        "01": ExecutionMode.SCAFFOLD,
        "02": ExecutionMode.SUPPORT_EVIDENCE,
        "03": ExecutionMode.SUPPORT_EVIDENCE,
        "04": ExecutionMode.LEGACY_COMPARATOR,
    }
    return defaults.get(phase_id, ExecutionMode.SCAFFOLD)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
