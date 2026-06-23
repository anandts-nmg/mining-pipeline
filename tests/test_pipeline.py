"""Pipeline runner: selection, dry-run tree build, gates, manifest."""

from __future__ import annotations

import json

import pytest

from buduunkhad.core.gates import GateStatus, evaluate_gate
from buduunkhad.core.paths import PHASE_DIRS
from buduunkhad.core.qaqc import Decision, new_report
from buduunkhad.pipeline import (
    MissingRawDataError,
    build_registry,
    run_pipeline,
    select_phases,
    validate_raw_inputs,
)


def test_registry_is_ordered_and_complete():
    reg = build_registry()
    assert [p.id for p in reg] == list(PHASE_DIRS.keys())
    assert reg[0].id == "00"
    assert reg[-1].id == "99"


def test_select_phases_range_and_only():
    reg = build_registry()
    assert [p.id for p in select_phases(reg, from_="00", to="01")] == ["00", "01"]
    assert [p.id for p in select_phases(reg, only=["01", "03"])] == ["01", "03"]
    with pytest.raises(ValueError):
        select_phases(reg, only=["77"])
    with pytest.raises(ValueError):
        select_phases(reg, from_="05", to="02")


def test_dry_run_builds_full_tree_and_manifest(project):
    config, register, _tmp = project
    manifest = run_pipeline(config, register, dry_run=True)

    # every phase folder exists
    for name in PHASE_DIRS.values():
        assert (config.output_root / name).is_dir()

    # all 13 phases attempted in dry-run (stubs participate)
    assert len(manifest.phases) == 13
    assert manifest.stopped_at == ""

    # manifest written to disk
    man_path = config.runs_root / manifest.run_id / "run_manifest.json"
    assert man_path.exists()
    data = json.loads(man_path.read_text())
    assert data["dry_run"] is True
    assert len(data["phases"]) == 13


def test_real_run_without_data_fails_loudly(project):
    config, register, _tmp = project  # raw_root empty
    missing = validate_raw_inputs(register, config.raw_root)
    assert len(missing) == len(register)
    with pytest.raises(MissingRawDataError):
        run_pipeline(config, register, only=["00"], dry_run=False)


def test_acknowledged_gap_does_not_block(raw_archive):
    # the manifest flags the KOMPSAT EULA as absent from the canonical archive;
    # removing it locally should be tolerated (recorded, not a hard failure).
    config, register, raw_root = raw_archive
    eula = next(r for r in register if r.filename == "KOMPSATEULAForm_3.1.pdf")
    (raw_root / eula.evidence_group / eula.filename).unlink()

    manifest = run_pipeline(config, register, only=["00"], dry_run=False)

    p00 = next(p for p in manifest.phases if p.phase_id == "00")
    assert p00.gate_status == "go"
    assert any("acknowledged" in w.lower() for w in manifest.warnings)


def test_unexpected_missing_still_fails(raw_archive):
    # a file NOT flagged absent in the manifest is a real gap and must stop the run.
    config, register, raw_root = raw_archive
    boundary = next(r for r in register if r.no == config.boundary.input_no)
    (raw_root / boundary.evidence_group / boundary.filename).unlink()
    with pytest.raises(MissingRawDataError):
        run_pipeline(config, register, only=["00"], dry_run=False)


def test_stub_phase_real_run_records_not_implemented(raw_archive):
    config, register, _raw = raw_archive
    # Phase 03 is still an orchestrate stub -> real run raises NotImplementedError.
    manifest = run_pipeline(config, register, only=["03"], dry_run=False)
    assert manifest.stopped_at == "03"
    assert manifest.phases[0].status == "not-implemented"
    assert "build pending" in manifest.phases[0].error


def test_gate_blocks_then_override():
    report = new_report("01", "Test")
    report.add("check", "must pass", decision=Decision.FAIL)
    blocked = evaluate_gate(report, override=False)
    assert blocked.status is GateStatus.BLOCKED
    assert not blocked.can_advance

    overridden = evaluate_gate(report, override=True)
    assert overridden.status is GateStatus.GO
    assert overridden.overridden
    assert overridden.can_advance


def test_gate_go_on_clean_report():
    report = new_report("00", "Test")
    report.add("check", "ok", decision=Decision.PASS)
    decision = evaluate_gate(report)
    assert decision.status is GateStatus.GO


def test_empty_report_is_blocked():
    report = new_report("00", "Test")
    decision = evaluate_gate(report)
    assert decision.status is GateStatus.BLOCKED
