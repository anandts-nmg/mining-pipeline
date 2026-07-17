"""Pipeline runner: selection, dry-run tree build, gates, manifest."""

from __future__ import annotations

import json
from pathlib import Path

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


def test_only_ignores_empty_trailing_token():
    # A trailing comma in --only yields an empty id; it must be dropped, NOT resolved to Phase 00.
    reg = build_registry()
    assert [p.id for p in select_phases(reg, only=["02", ""])] == ["02"]
    # an all-empty selection is a hard error rather than a silent no-op / full run
    with pytest.raises(ValueError):
        select_phases(reg, only=[""])
    with pytest.raises(ValueError):
        select_phases(reg, only=[])  # e.g. `--only ,` -> [] must NOT leak into a full run


def test_unknown_from_to_raises():
    reg = build_registry()
    with pytest.raises(ValueError):
        select_phases(reg, from_="77")
    with pytest.raises(ValueError):
        select_phases(reg, to="88")


def test_bad_selection_creates_no_run_dir(project):
    # An invalid selection must fail before the run dir/logger are created (no orphan dir).
    config, register, _tmp = project
    with pytest.raises(ValueError):
        run_pipeline(config, register, only=["77"], dry_run=True)
    assert not list(config.runs_root.glob("*")), "orphan run dir created on bad selection"


def test_manifest_written_on_startup_abort(project):
    # A real run with no data aborts, but must still leave a machine-readable manifest.
    import json as _json

    config, register, _tmp = project  # raw_root empty
    with pytest.raises(MissingRawDataError):
        run_pipeline(config, register, only=["00"], dry_run=False)
    manifests = list(config.runs_root.glob("*/run_manifest.json"))
    assert manifests, "no run_manifest.json written on aborted run"
    data = _json.loads(manifests[-1].read_text(encoding="utf-8"))
    assert data["error"], "startup error not recorded in manifest"


def test_gate_provisional_on_pending():
    report = new_report("03", "Test")
    report.add("done", "ok", decision=Decision.PASS)
    report.add("todo", "human completes", decision=Decision.PENDING)
    decision = evaluate_gate(report)
    assert decision.status is GateStatus.GO
    assert decision.provisional
    assert "PENDING" in decision.reason


def test_gate_not_provisional_when_all_pass():
    report = new_report("00", "Test")
    report.add("done", "ok", decision=Decision.PASS)
    decision = evaluate_gate(report)
    assert decision.status is GateStatus.GO
    assert not decision.provisional


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
    assert all(not phase["output_artifacts"] for phase in data["phases"])


def test_manifest_surfaces_qaqc_pending_alongside_passed(raw_archive):
    # qaqc_passed means "nothing failed" and is True even with PENDING items; the manifest must
    # carry the companion qaqc_pending signal so a consumer can tell "passed" from "complete".
    # Phase 00's real run always leaves the source-note/owner item PENDING for the operator.
    config, register, _raw = raw_archive
    manifest = run_pipeline(config, register, only=["00"], dry_run=False)

    p00 = next(p for p in manifest.phases if p.phase_id == "00")
    assert p00.qaqc_passed is True  # no failures
    assert p00.qaqc_pending is True  # but human-completion items remain
    assert p00.qaqc_pending == p00.gate_provisional  # both derive from has_pending

    # the field is machine-readable in the written manifest, not just on the dataclass
    man_path = config.runs_root / manifest.run_id / "run_manifest.json"
    data = json.loads(man_path.read_text(encoding="utf-8"))
    d00 = next(p for p in data["phases"] if p["phase_id"] == "00")
    assert d00["qaqc_passed"] is True
    assert d00["qaqc_pending"] is True
    assert d00["pending_human_review_or_qaqc_count"] > 0


def test_successful_run_manifest_seals_every_publishable_output_and_runner_qaqc(raw_archive):
    from buduunkhad.core.run_artifacts import sha256_file

    config, register, _raw = raw_archive
    manifest = run_pipeline(config, register, only=["00"], dry_run=False)
    phase = manifest.phases[0]

    qaqc_outputs = [path for path in phase.outputs if path.endswith("_Phase00_QAQC_Log.xlsx")]
    assert len(qaqc_outputs) == 1
    artifacts = {artifact.path: artifact for artifact in phase.output_artifacts}
    qaqc_relative = Path(qaqc_outputs[0]).resolve().relative_to(config.output_root.resolve())
    assert qaqc_relative.as_posix() in artifacts
    assert len(artifacts) == len(phase.output_artifacts)
    for relative, artifact in artifacts.items():
        output = config.output_root / Path(relative)
        assert artifact.sha256 == sha256_file(output)
        assert artifact.sha256 == artifact.sha256.lower()
        assert artifact.size_bytes == output.stat().st_size

    written = json.loads(
        (config.runs_root / manifest.run_id / "run_manifest.json").read_text(encoding="utf-8")
    )["phases"][0]
    assert written["outputs"] == phase.outputs
    assert written["output_artifacts"] == [
        artifact.model_dump(mode="json") for artifact in phase.output_artifacts
    ]


def test_run_artifact_sealing_rejects_duplicate_portable_paths(tmp_path):
    from buduunkhad.core.run_artifacts import ArtifactSealError, seal_output_artifacts

    output = tmp_path / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"master")

    with pytest.raises(ArtifactSealError, match="duplicated"):
        seal_output_artifacts(tmp_path, [output, output])


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


def test_missing_data_message_flags_incomplete_walk(raw_archive):
    # When the walk finds some inputs yet is missing several the manifest records as PRESENT
    # (the cloud virtual-FS under-enumeration failure mode, e.g. Drive for Desktop), the error
    # must diagnose that — advise a real local copy + show the walk-vs-manifest count — not just
    # report "missing".
    config, register, raw_root = raw_archive
    for r in [r for r in register if r.file_type == "raster"][:4]:
        (raw_root / r.evidence_group / r.filename).unlink()
    with pytest.raises(MissingRawDataError) as exc:
        run_pipeline(config, register, only=["00"], dry_run=False)
    text = str(exc.value).lower()
    assert "manifest" in text  # names the manifest cross-check
    assert "local" in text  # advises a real local copy
    assert "found" in text  # surfaces the walk-vs-manifest count


def test_stub_phase_real_run_records_not_implemented(raw_archive):
    config, register, _raw = raw_archive
    # Phase 05 is still a stub -> real run raises NotImplementedError (Phases 00-04 are built).
    manifest = run_pipeline(config, register, only=["05"], dry_run=False)
    assert manifest.stopped_at == "05"
    assert manifest.phases[0].status == "not-implemented"
    assert manifest.phases[0].output_artifacts == []
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
