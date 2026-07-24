"""Tests for the run-start hardening: path-length pre-flight + raw-integrity baseline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import pytest

from buduunkhad.core import raw_guard, registers, winpath
from buduunkhad.core.execution_policy import (
    AuthorizationAction,
    ExecutionAuthorization,
    ExecutionMode,
    ExecutionPolicyError,
)
from buduunkhad.core.raw_guard import RawIntegrityError
from buduunkhad.pipeline import (
    PathTooLongError,
    _sha256_json,
    baseline_checksum_path,
    preflight_path_lengths,
    run_pipeline,
)

LOG = logging.getLogger("test")


# --------------------------------------------------------------------------- #
# winpath helpers
# --------------------------------------------------------------------------- #


def test_long_paths_enabled_returns_tristate():
    assert winpath.long_paths_enabled() in (True, False, None)


def test_overlength_paths_flags_only_long():
    drive = "C:/" if winpath.is_windows() else "/"
    long_p = drive + "a" * 300
    short_p = drive + "x.txt"
    hits = winpath.overlength_paths([long_p, short_p], limit=260)
    assert hits, "expected the 300-char path to be flagged"
    assert all(length >= 260 for _, length in hits)
    assert all("x.txt" not in p for p, _ in hits)


def test_extended_length_path():
    if winpath.is_windows():
        assert winpath.extended_length_path("C:/temp/x").startswith("\\\\?\\")
    else:
        # no-op off Windows
        assert "?" not in winpath.extended_length_path("/tmp/x")


# --------------------------------------------------------------------------- #
# path-length pre-flight
# --------------------------------------------------------------------------- #


def test_preflight_blocks_real_run_when_disabled(project):
    config, register, _tmp = project
    with pytest.raises(PathTooLongError):
        preflight_path_lengths(config, register, dry_run=False, logger=LOG, limit=10, enabled=False)


def test_preflight_warns_in_dry_run(project):
    config, register, _tmp = project
    warns = preflight_path_lengths(
        config, register, dry_run=True, logger=LOG, limit=10, enabled=False
    )
    assert warns and "exceed" in warns[0]


def test_preflight_skipped_when_enabled(project):
    config, register, _tmp = project
    # even with an impossibly small limit, long paths being enabled means no block
    assert (
        preflight_path_lengths(config, register, dry_run=False, logger=LOG, limit=10, enabled=True)
        == []
    )


# --------------------------------------------------------------------------- #
# raw-integrity baseline
# --------------------------------------------------------------------------- #


def test_raw_integrity_requires_exact_data_custodian_transition(raw_archive):
    config, register, raw_root = raw_archive

    # first real run of Phase 00 writes the SHA-256 baseline
    run_pipeline(config, register, only=["00"], dry_run=False)
    assert baseline_checksum_path(config).exists()

    # tamper a raw file
    target = next(raw_root.rglob("*.tif"))
    target.write_bytes(b"TAMPERED CONTENT")

    # a subsequent real run detects the drift and stops loudly
    with pytest.raises(RawIntegrityError):
        run_pipeline(config, register, only=["00"], dry_run=False)

    with pytest.raises(ExecutionPolicyError, match="--override is retired"):
        run_pipeline(config, register, only=["00"], dry_run=False, override=True)

    old = registers.read_checksum_register_csv(baseline_checksum_path(config))
    current = {
        item.relative_path: item.sha256
        for item in raw_guard.build_checksum_records(config.raw_root)
    }
    authorization = ExecutionAuthorization.create(
        action=AuthorizationAction.RAW_IDENTITY_TRANSITION,
        actor="data-custodian-test",
        authorization_reference="TEST-RAW-001",
        reason="Synthetic test authorizes the exact changed archive identity.",
        subject="raw-archive",
        old_identity_sha256=_sha256_json(old),
        new_identity_sha256=_sha256_json(current),
        recorded_at=datetime.now(UTC),
        scope_phase_ids=("00",),
        validity="until-superseded",
        resulting_permitted_mode=ExecutionMode.AUTHORITATIVE,
    )
    authorization_path = config.base_dir / "raw-transition.json"
    authorization_path.write_text(authorization.model_dump_json(indent=2) + "\n", encoding="utf-8")
    manifest = run_pipeline(
        config,
        register,
        only=["00"],
        dry_run=False,
        authorization_paths=[authorization_path],
    )
    assert manifest.phases[0].phase_id == "00"
    assert manifest.used_authorization_ids == [authorization.authorization_id]
    assert manifest.phases[0].authorization_ids == [authorization.authorization_id]


def test_first_real_run_has_no_baseline(raw_archive):
    config, register, _raw = raw_archive
    # no baseline yet -> integrity check is a no-op and the run proceeds
    manifest = run_pipeline(config, register, only=["00"], dry_run=False)
    assert manifest.stopped_at == ""
