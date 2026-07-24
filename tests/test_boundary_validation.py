"""Adversarial tests for Phase 01's deterministic boundary record."""

from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from buduunkhad.ai.fingerprint import sha256_value
from buduunkhad.core import paths, vector_io
from buduunkhad.core.boundary_validation import (
    BoundaryReviewAttestation,
    BoundaryReviewDecision,
    BoundaryReviewerRole,
    BoundaryValidationError,
    BoundaryValidationRecord,
    load_boundary_validation_record,
    verify_boundary_validation_files,
)
from buduunkhad.phases.base import RunContext
from buduunkhad.phases.phase00_archive import Phase00Archive
from buduunkhad.phases.phase01_data_audit import Phase01DataAudit


def _run_boundary(raw_archive):
    config, register, _raw = raw_archive
    ctx = RunContext(config=config, register=register, run_id="boundary-validation-test")
    phase00 = Phase00Archive()
    phase00.prepare(ctx)
    phase00.run(ctx)
    phase01 = Phase01DataAudit()
    phase01.prepare(ctx)
    phase01.run(ctx)
    phase01_root = paths.phase_dir(config.output_root, "01")
    record_path = (
        phase01_root
        / "03_CRS_Check"
        / f"{config.register_prefix}_Licence_Boundary_Validation_Record.json"
    )
    return config, register, ctx, phase01_root, record_path


def test_boundary_record_binds_source_derivatives_and_measurements(raw_archive) -> None:
    config, _register, ctx, phase01_root, record_path = _run_boundary(raw_archive)
    record = load_boundary_validation_record(record_path)

    assert record.format_version == "1.0.0"
    assert record.processing_run_id == ctx.run_id
    assert record.source_run_id == ctx.run_id
    assert record.source.input_no == 8
    assert record.source.external_file_id == "1WA4jpRS2ng3pvtzpE_9M7iBV97S397VD"
    assert record.source_artifact.path.endswith("_raw.kmz")
    assert record.boundary_derivative.layer_name == "license_boundary"
    assert record.buffer_derivative.layer_name == "project_buffers"
    assert record.crs.source_coordinates_finite
    assert record.crs.source_coordinate_domain_valid
    assert record.topology.source_invalid_feature_count == 0
    assert record.topology.derivative_invalid_feature_count == 0
    assert record.topology.source_overlapping_feature_pair_count == 0
    assert record.topology.derivative_overlapping_feature_pair_count == 0
    assert record.deterministic_status == "complete"
    assert all("accept" not in field for field in type(record).model_fields)

    verify_boundary_validation_files(
        record,
        source_phase_root=paths.phase_dir(config.output_root, "00"),
        phase_root=phase01_root,
    )


def test_recomputed_boundary_validation_id_cannot_hide_measurement_inconsistency(
    raw_archive,
) -> None:
    _config, _register, _ctx, _phase01_root, record_path = _run_boundary(raw_archive)
    record = load_boundary_validation_record(record_path)
    value = record.model_dump(mode="python")
    value["deterministic_status"] = "failed"
    value["validation_id"] = sha256_value(
        {key: item for key, item in value.items() if key != "validation_id"}
    )

    with pytest.raises(ValidationError, match="deterministic status"):
        BoundaryValidationRecord.model_validate(value)


def test_boundary_source_mutation_after_measurement_is_detected(raw_archive) -> None:
    config, _register, _ctx, phase01_root, record_path = _run_boundary(raw_archive)
    record = load_boundary_validation_record(record_path)
    source = paths.phase_dir(config.output_root, "00") / record.source_artifact.path
    source.write_bytes(source.read_bytes() + b"changed")

    with pytest.raises(BoundaryValidationError, match="artifact bytes changed"):
        verify_boundary_validation_files(
            record,
            source_phase_root=paths.phase_dir(config.output_root, "00"),
            phase_root=phase01_root,
        )


def test_boundary_derivative_mutation_after_measurement_is_detected(raw_archive) -> None:
    config, _register, _ctx, phase01_root, record_path = _run_boundary(raw_archive)
    record = load_boundary_validation_record(record_path)
    derivative = phase01_root / record.buffer_derivative.path
    derivative.write_bytes(derivative.read_bytes() + b"changed")

    with pytest.raises(BoundaryValidationError, match="artifact bytes changed"):
        verify_boundary_validation_files(
            record,
            source_phase_root=paths.phase_dir(config.output_root, "00"),
            phase_root=phase01_root,
        )


def test_boundary_source_mutation_during_parse_is_detected(raw_archive, monkeypatch) -> None:
    config, register, _raw = raw_archive
    ctx = RunContext(config=config, register=register, run_id="boundary-copy-window-test")
    phase00 = Phase00Archive()
    phase00.prepare(ctx)
    phase00.run(ctx)
    phase01 = Phase01DataAudit()
    phase01.prepare(ctx)
    original = vector_io.read_boundary_with_provenance

    def read_then_mutate(path, assume_epsg=4326):
        result = original(path, assume_epsg=assume_epsg)
        path.write_bytes(path.read_bytes() + b"changed-during-boundary-validation")
        return result

    monkeypatch.setattr(vector_io, "read_boundary_with_provenance", read_then_mutate)
    with pytest.raises(BoundaryValidationError, match="changed while it was being validated"):
        phase01.run(ctx)


def test_boundary_review_requires_complete_named_utc_evidence(raw_archive) -> None:
    _config, _register, _ctx, _phase01_root, record_path = _run_boundary(raw_archive)
    record = load_boundary_validation_record(record_path)

    attestation = BoundaryReviewAttestation.create(
        validation_id=record.validation_id,
        validation_file_sha256="a" * 64,
        processing_run_id=record.processing_run_id,
        reviewer="Qualified Reviewer",
        reviewer_role=BoundaryReviewerRole.QUALIFIED_REVIEWER,
        reviewer_authorization_id="reviewer-auth-001",
        reviewed_at=datetime(2026, 7, 24, 8, 0, tzinfo=UTC),
        decision=BoundaryReviewDecision.ACCEPTED,
        rationale="Reviewed the deterministic measurements and source overlay.",
    )
    assert attestation.attestation_id

    value = attestation.model_dump(mode="python", exclude={"attestation_id"})
    value["reviewed_at"] = datetime(2026, 7, 24, 8, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        BoundaryReviewAttestation.create(**value)


def test_boundary_record_rejects_duplicate_json_keys(tmp_path) -> None:
    path = tmp_path / "record.json"
    path.write_text('{"format_version":"1.0.0","format_version":"1.0.0"}', encoding="utf-8")

    with pytest.raises(BoundaryValidationError, match="record is invalid"):
        load_boundary_validation_record(path)


def test_kmz_boundary_reader_rejects_ambiguous_and_unsafe_members(tmp_path) -> None:
    ambiguous = tmp_path / "ambiguous.kmz"
    with zipfile.ZipFile(ambiguous, "w") as archive:
        archive.writestr("one.kml", "<kml/>")
        archive.writestr("two.kml", "<kml/>")
    with pytest.raises(ValueError, match="ambiguous KML"):
        vector_io.read_boundary_with_provenance(ambiguous)

    unsafe = tmp_path / "unsafe.kmz"
    with zipfile.ZipFile(unsafe, "w") as archive:
        archive.writestr("../doc.kml", "<kml/>")
    with pytest.raises(ValueError, match="unsafe KML member"):
        vector_io.read_boundary_with_provenance(unsafe)


def test_boundary_review_attestation_identity_rejects_tampering(raw_archive) -> None:
    _config, _register, _ctx, _phase01_root, record_path = _run_boundary(raw_archive)
    record = load_boundary_validation_record(record_path)
    attestation = BoundaryReviewAttestation.create(
        validation_id=record.validation_id,
        validation_file_sha256="b" * 64,
        processing_run_id=record.processing_run_id,
        reviewer="Data Custodian",
        reviewer_role=BoundaryReviewerRole.DATA_CUSTODIAN,
        reviewer_authorization_id="custodian-auth-001",
        reviewed_at=datetime(2026, 7, 24, 8, 0, tzinfo=UTC),
        decision=BoundaryReviewDecision.REJECTED,
        rationale="Synthetic negative review.",
    )
    value = json.loads(attestation.model_dump_json())
    value["decision"] = "accepted"
    with pytest.raises(ValidationError, match="identity is invalid"):
        BoundaryReviewAttestation.model_validate(value)
