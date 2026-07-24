"""Runtime execution-policy and scoped-authorization contract tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from buduunkhad.core.execution_policy import (
    AuthorizationAction,
    ExecutionAuthorization,
    ExecutionMode,
    ExecutionPolicyError,
    load_execution_authorizations,
    load_execution_policy,
    phase_gate_subject,
    resolve_execution_policy,
    validate_authorizations_for_run,
)


def _authorization(**updates: object) -> ExecutionAuthorization:
    values: dict[str, object] = {
        "action": AuthorizationAction.OPERATIONAL_EXCEPTION,
        "actor": "pipeline-operator-test",
        "authorization_reference": "TEST-OPS-001",
        "reason": "Synthetic bounded operational exception.",
        "subject": phase_gate_subject("01", "OPERATIONAL-EXCEPTION-01-HANDOFF-PACKAGE"),
        "recorded_at": datetime(2026, 7, 24, tzinfo=UTC),
        "scope_phase_ids": ("01",),
        "validity": "until-expiry",
        "expires_at": datetime(2026, 7, 25, tzinfo=UTC),
        "resulting_permitted_mode": ExecutionMode.SCAFFOLD,
    }
    values.update(updates)
    return ExecutionAuthorization.create(**values)


def test_execution_policy_covers_every_registered_phase_and_current_boundaries() -> None:
    registry = load_execution_policy()
    by_phase = {item.phase_id: item for item in registry.phase_policies}

    assert tuple(by_phase) == tuple(f"{value:02d}" for value in range(12)) + ("99",)
    assert by_phase["00"].default_real_mode is ExecutionMode.AUTHORITATIVE
    assert by_phase["01"].default_real_mode is ExecutionMode.SCAFFOLD
    assert by_phase["02"].default_real_mode is ExecutionMode.SUPPORT_EVIDENCE
    assert by_phase["03"].default_real_mode is ExecutionMode.SUPPORT_EVIDENCE
    assert by_phase["04"].default_real_mode is ExecutionMode.LEGACY_COMPARATOR
    assert all(by_phase[phase].default_real_mode is None for phase in (*by_phase.keys(),)[5:])
    assert {
        phase_id: tuple(
            readiness for block in policy.blocked_modes for readiness in block.readiness_ids
        )
        for phase_id, policy in by_phase.items()
        if policy.blocked_modes
    } == {
        "01": ("METH-READY-005",),
        "02": ("METH-READY-003", "METH-READY-005"),
        "03": ("METH-READY-004", "METH-READY-005", "METH-READY-006"),
        "04": (
            "METH-READY-004",
            "METH-READY-005",
            "METH-READY-006",
            "METH-READY-007",
        ),
        "05": ("METH-READY-001",),
    }
    assert tuple(item.control_id for item in registry.operational_exception_controls) == (
        "OPERATIONAL-EXCEPTION-01-HANDOFF-PACKAGE",
    )


def test_policy_rejects_blocked_authoritative_and_unimplemented_real_modes() -> None:
    with pytest.raises(ExecutionPolicyError, match=r"METH-READY-004.*METH-READY-006"):
        resolve_execution_policy(
            ["03"],
            dry_run=False,
            requested_modes={"03": ExecutionMode.AUTHORITATIVE},
        )
    with pytest.raises(ExecutionPolicyError, match="Phase 05 has no real execution mode"):
        resolve_execution_policy(["05"], dry_run=False)


def test_dry_run_is_scaffold_only() -> None:
    binding = resolve_execution_policy(["00", "04", "99"], dry_run=True)
    assert {item.execution_mode for item in binding.phase_modes} == {ExecutionMode.SCAFFOLD}
    with pytest.raises(ExecutionPolicyError, match="dry runs permit scaffold mode only"):
        resolve_execution_policy(
            ["04"],
            dry_run=True,
            requested_modes={"04": ExecutionMode.LEGACY_COMPARATOR},
        )


def test_authorization_identity_is_hash_bound_and_duplicate_keys_fail(tmp_path) -> None:
    record = _authorization()
    tampered = record.model_dump(mode="json") | {"reason": "changed"}
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ExecutionPolicyError, match="invalid"):
        load_execution_authorizations([path])

    path.write_text('{"format_version":"1.0.0","format_version":"1.0.0"}')
    with pytest.raises(ExecutionPolicyError, match="invalid"):
        load_execution_authorizations([path])


def test_operational_exception_cannot_claim_scientific_or_flight_scope() -> None:
    for phase_id in ("03", "04", "05"):
        with pytest.raises(ValueError, match="non-overridable"):
            _authorization(
                subject=phase_gate_subject(phase_id, f"OPERATIONAL-EXCEPTION-{phase_id}-SYNTHETIC"),
                scope_phase_ids=(phase_id,),
            )
    with pytest.raises(ValueError, match="must expire"):
        _authorization(validity="until-superseded", expires_at=None)


def test_authorization_must_match_selected_mode_scope_and_expiry() -> None:
    binding = resolve_execution_policy(["01"], dry_run=False)
    record = _authorization()
    validate_authorizations_for_run((record,), binding, now=datetime(2026, 7, 24, 1, tzinfo=UTC))
    overlapping = _authorization(authorization_reference="TEST-OPS-002")
    with pytest.raises(ExecutionPolicyError, match="overlapping claims"):
        validate_authorizations_for_run(
            (record, overlapping),
            binding,
            now=datetime(2026, 7, 24, 1, tzinfo=UTC),
        )

    expired = _authorization(
        expires_at=datetime(2026, 7, 24, 2, tzinfo=UTC),
    )
    with pytest.raises(ExecutionPolicyError, match="expired"):
        validate_authorizations_for_run(
            (expired,), binding, now=datetime(2026, 7, 24, 3, tzinfo=UTC)
        )

    future = _authorization(
        expires_at=datetime(2026, 7, 24, tzinfo=UTC) + timedelta(days=1),
        scope_phase_ids=("01", "02"),
    )
    with pytest.raises(ExecutionPolicyError, match="unselected"):
        validate_authorizations_for_run(
            (future,), binding, now=datetime(2026, 7, 24, 1, tzinfo=UTC)
        )
