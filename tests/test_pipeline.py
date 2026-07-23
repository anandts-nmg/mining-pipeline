"""Pipeline runner: selection, dry-run tree build, gates, manifest."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
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


def test_gate_can_require_pending_human_items_to_block() -> None:
    report = new_report("03", "Test")
    report.add("done", "ok", decision=Decision.PASS)
    report.add("todo", "human completes", decision=Decision.PENDING)

    blocked = evaluate_gate(report, pending_blocks=True)
    assert blocked.status is GateStatus.BLOCKED
    assert not blocked.provisional
    assert not blocked.can_advance

    overridden = evaluate_gate(report, pending_blocks=True, override=True)
    assert overridden.status is GateStatus.GO
    assert overridden.overridden
    assert "OVERRIDDEN" in overridden.reason

    strict = evaluate_gate(
        report,
        pending_blocks=True,
        override=True,
        pending_override_allowed=False,
    )
    assert strict.status is GateStatus.BLOCKED
    assert not strict.overridden


def test_gate_not_provisional_when_all_pass():
    report = new_report("00", "Test")
    report.add("done", "ok", decision=Decision.PASS)
    decision = evaluate_gate(report)
    assert decision.status is GateStatus.GO
    assert not decision.provisional


def test_dry_run_builds_full_tree_and_manifest(project):
    config, register, _tmp = project
    manifest = run_pipeline(config, register, dry_run=True)

    # every phase folder is finalized inside the run; dry-run never mutates the current view
    run_dir = config.runs_root / manifest.run_id
    for phase_id in PHASE_DIRS:
        assert (run_dir / "phases" / phase_id).is_dir()
    assert not any((config.output_root / name).exists() for name in PHASE_DIRS.values())

    # all 13 phases attempted in dry-run (stubs participate)
    assert len(manifest.phases) == 13
    assert manifest.stopped_at == ""

    # manifest written to disk
    man_path = config.runs_root / manifest.run_id / "run_manifest.json"
    assert man_path.exists()
    data = json.loads(man_path.read_text())
    assert data["dry_run"] is True
    assert data["manifest_format_version"] == "2.0.0"
    assert data["run_layout_version"] == "run-isolated-v1"
    assert len(data["phases"]) == 13
    assert all(not phase["output_artifacts"] for phase in data["phases"])
    assert all(phase["sealed_files"] for phase in data["phases"])


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


@pytest.mark.parametrize("override", [False, True])
def test_runner_stops_phase03_before_phase04_despite_operational_override(
    raw_archive, override: bool
):
    """The real runner must enforce Phase 03's non-overridable scientific handoff gate."""

    config, register, _raw = raw_archive
    run_id = f"strict-phase03-override-{str(override).lower()}"
    manifest = run_pipeline(
        config,
        register,
        only=["00", "01", "03", "04"],
        dry_run=False,
        override=override,
        run_id=run_id,
    )

    assert manifest.selected_phases == ["00", "01", "03", "04"]
    assert [phase.phase_id for phase in manifest.phases] == ["00", "01", "03"]
    assert manifest.stopped_at == "03"
    phase03 = manifest.phases[-1]
    assert phase03.gate_status == GateStatus.BLOCKED.value
    assert not phase03.gate_overridden
    assert phase03.qaqc_pending
    assert phase03.pending_human_review_or_qaqc_count > 0
    assert len([path for path in phase03.outputs if path.endswith("_Phase03_QAQC_Log.xlsx")]) == 1
    assert len([path for path in phase03.outputs if "Phase3_Technical_Processing_Log" in path]) == 1

    run_log = (config.runs_root / run_id / "logs" / "run.log").read_text(encoding="utf-8")
    assert "Phase 03 gate blocked advance" in run_log
    assert "use --override" not in run_log


def test_successful_run_manifest_seals_every_publishable_output_and_runner_qaqc(raw_archive):
    from buduunkhad.core.run_artifacts import sha256_file

    config, register, _raw = raw_archive
    manifest = run_pipeline(config, register, only=["00"], dry_run=False)
    phase = manifest.phases[0]

    qaqc_outputs = [path for path in phase.outputs if path.endswith("_Phase00_QAQC_Log.xlsx")]
    assert len(qaqc_outputs) == 1
    artifacts = {artifact.path: artifact for artifact in phase.output_artifacts}
    assert qaqc_outputs[0] in artifacts
    assert len(artifacts) == len(phase.output_artifacts)
    run_dir = config.runs_root / manifest.run_id
    for relative, artifact in artifacts.items():
        output = run_dir / Path(relative)
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
    assert written["sealed_files"] == [
        artifact.model_dump(mode="json") for artifact in phase.sealed_files
    ]
    assert set(artifacts) <= {artifact.path for artifact in phase.sealed_files}
    assert (config.output_root / PHASE_DIRS["00"]).is_dir()
    assert (config.output_root / ".buduunkhad-current-view.json").is_file()
    assert set(manifest.execution_identity) == {
        "source_inventory_sha256",
        "input_register_sha256",
        "project_configuration_sha256",
        "methodology_contract_sha256",
        "code_version",
        "parameters_sha256",
    }


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
    run_dir = config.runs_root / manifest.run_id
    assert (run_dir / "staging" / "05").is_dir()
    assert not (run_dir / "phases" / "05").exists()


def test_default_run_ids_are_uuidv7_and_distinct_in_the_same_second():
    from buduunkhad.core.run_storage import generate_run_id

    instant = datetime(2026, 7, 22, 8, 0, tzinfo=UTC)
    first = generate_run_id(now=instant, entropy="0" * 32)
    second = generate_run_id(now=instant, entropy="0" * 31 + "1")

    assert first != second
    assert uuid.UUID(first).version == 7
    assert uuid.UUID(second).version == 7


def test_project_execution_lock_rejects_a_second_writer(project):
    from buduunkhad.core.run_storage import ExecutionLockError, ProjectExecutionLock

    config, register, _tmp = project
    with (
        ProjectExecutionLock(config.runs_root, "first-run"),
        pytest.raises(ExecutionLockError, match="execution lock"),
    ):
        run_pipeline(config, register, only=["00"], dry_run=True, run_id="second-run")
    assert not (config.runs_root / "second-run").exists()


def test_pipeline_rejects_overlapping_execution_and_compatibility_roots(project):
    from buduunkhad.core.run_storage import RunStorageError

    config, register, _tmp = project
    unsafe_paths = config.paths.model_copy(update={"runs_root": config.paths.output_root})
    unsafe = config.model_copy(update={"paths": unsafe_paths})

    with pytest.raises(RunStorageError, match="must not overlap"):
        run_pipeline(unsafe, register, only=["00"], dry_run=True)


def test_resume_of_completed_run_verifies_and_does_not_repeat_outputs(raw_archive):
    config, register, _raw = raw_archive
    original = run_pipeline(config, register, only=["00"], dry_run=False)
    run_dir = config.runs_root / original.run_id
    artifact = run_dir / original.phases[0].output_artifacts[0].path
    before_bytes = artifact.read_bytes()
    before_manifest = (run_dir / "run_manifest.json").read_bytes()

    resumed = run_pipeline(
        config,
        register,
        only=["00"],
        dry_run=False,
        run_id=original.run_id,
        resume=True,
    )

    assert resumed.as_dict() == original.as_dict()
    assert artifact.read_bytes() == before_bytes
    assert (run_dir / "run_manifest.json").read_bytes() == before_manifest


def test_resume_rejects_mutation_after_sealing(raw_archive):
    from buduunkhad.pipeline import ResumeError

    config, register, _raw = raw_archive
    original = run_pipeline(config, register, only=["00"], dry_run=False)
    artifact = config.runs_root / original.run_id / original.phases[0].output_artifacts[0].path
    artifact.write_bytes(artifact.read_bytes() + b"tampered")

    with pytest.raises(ResumeError, match="sealed run artifact changed"):
        run_pipeline(
            config,
            register,
            only=["00"],
            dry_run=False,
            run_id=original.run_id,
            resume=True,
        )


def test_resume_detects_mutated_run_local_working_copy(raw_archive):
    from buduunkhad.pipeline import ResumeError

    config, register, _raw = raw_archive
    original = run_pipeline(config, register, only=["00"], dry_run=False)
    working_copy = next(
        artifact
        for artifact in original.phases[0].sealed_files
        if "01_Tectonic_Terrane_KMZ" in Path(artifact.path).parts
    )
    path = config.runs_root / original.run_id / working_copy.path
    path.write_bytes(path.read_bytes() + b"tampered")

    with pytest.raises(ResumeError, match="sealed run artifact changed"):
        run_pipeline(
            config,
            register,
            only=["00"],
            dry_run=False,
            run_id=original.run_id,
            resume=True,
        )


def test_resume_rejects_file_added_after_phase_sealing(raw_archive):
    from buduunkhad.pipeline import ResumeError

    config, register, _raw = raw_archive
    original = run_pipeline(config, register, only=["00"], dry_run=False)
    phase_dir = config.runs_root / original.run_id / "phases" / "00"
    (phase_dir / "unexpected.bin").write_bytes(b"not sealed")

    with pytest.raises(ResumeError, match="file inventory changed"):
        run_pipeline(
            config,
            register,
            only=["00"],
            dry_run=False,
            run_id=original.run_id,
            resume=True,
        )


def test_resume_discards_partial_stage_and_restarts_only_incomplete_phase(project, monkeypatch):
    from buduunkhad.phases.base import Phase, PhaseResult

    class InterruptedPhase(Phase):
        id = "00"
        name = "Interrupted synthetic phase"
        mode = "build"
        attempts = 0

        def run(self, ctx):
            type(self).attempts += 1
            output = ctx.phase_dir("00") / "result.csv"
            output.write_text(
                "partial" if type(self).attempts == 1 else "complete", encoding="utf-8"
            )
            if type(self).attempts == 1:
                raise RuntimeError("interrupted")
            return PhaseResult("00", status="dry-run", outputs=[output])

        def qaqc(self, ctx):
            del ctx
            report = new_report("00", self.name)
            report.add("complete", "fresh output", decision=Decision.PASS)
            return report

    monkeypatch.setattr("buduunkhad.pipeline.build_registry", lambda: [InterruptedPhase()])
    config, register, _tmp = project
    first = run_pipeline(config, register, only=["00"], dry_run=True, run_id="interrupted-run")
    run_dir = config.runs_root / first.run_id
    assert first.phases[0].status == "error"
    assert not first.phases[0].output_artifacts
    assert not (run_dir / "phases" / "00").exists()
    assert (run_dir / "staging" / "00" / "result.csv").read_text() == "partial"

    resumed = run_pipeline(
        config,
        register,
        only=["00"],
        dry_run=True,
        run_id=first.run_id,
        resume=True,
    )

    assert InterruptedPhase.attempts == 2
    assert len(resumed.phases) == 1
    assert resumed.phases[0].status == "dry-run"
    assert (run_dir / "phases" / "00" / "result.csv").read_text() == "complete"
    assert not (run_dir / "staging" / "00").exists()


def test_resume_rejects_methodology_contract_drift(project):
    from buduunkhad.pipeline import ResumeError

    config, register, _tmp = project
    original = run_pipeline(config, register, only=["00"], dry_run=True)
    methodology = config.base_dir / "config" / "methodology"
    methodology.mkdir()
    (methodology / "contract.yaml").write_text("version: 1\n", encoding="utf-8")

    with pytest.raises(ResumeError, match="resume identity differs"):
        run_pipeline(
            config,
            register,
            only=["00"],
            dry_run=True,
            run_id=original.run_id,
            resume=True,
        )


def test_resume_rejects_methodology_mirror_byte_drift(project):
    from buduunkhad.pipeline import ResumeError

    config, register, _tmp = project
    methodology = config.base_dir / "docs" / "methodology"
    methodology.mkdir(parents=True)
    mirror = methodology / "master.pdf"
    mirror.write_bytes(b"byte-bound methodology")
    original = run_pipeline(config, register, only=["00"], dry_run=True)
    mirror.write_bytes(b"changed methodology")

    with pytest.raises(ResumeError, match="resume identity differs"):
        run_pipeline(
            config,
            register,
            only=["00"],
            dry_run=True,
            run_id=original.run_id,
            resume=True,
        )


def test_initial_manifest_exists_before_first_phase_side_effect(project, monkeypatch):
    from buduunkhad.phases.base import Phase, PhaseResult

    class ManifestObservingPhase(Phase):
        id = "00"
        name = "Manifest observing phase"
        mode = "build"

        def run(self, ctx):
            data = json.loads((ctx.run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            assert data["run_id"] == ctx.run_id
            assert data["phases"] == []
            output = ctx.phase_dir("00") / "result.csv"
            output.write_text("complete", encoding="utf-8")
            return PhaseResult("00", status="dry-run", outputs=[output])

        def qaqc(self, ctx):
            del ctx
            report = new_report("00", self.name)
            report.add("complete", "fresh output", decision=Decision.PASS)
            return report

    monkeypatch.setattr("buduunkhad.pipeline.build_registry", lambda: [ManifestObservingPhase()])
    config, register, _tmp = project

    result = run_pipeline(config, register, only=["00"], dry_run=True)

    assert result.phases[0].status == "dry-run"


def test_compatibility_promotion_is_idempotent_for_one_sealed_phase(raw_archive):
    from buduunkhad.core.run_storage import RunLayout, promote_phase_to_current

    config, register, _raw = raw_archive
    manifest = run_pipeline(config, register, only=["00"], dry_run=False)
    phase = manifest.phases[0]
    layout = RunLayout(config.runs_root, manifest.run_id)
    current_record = config.output_root / ".buduunkhad-current-view.json"
    before = current_record.read_bytes()

    promoted = promote_phase_to_current(
        layout,
        "00",
        config.output_root,
        phase.sealed_files,
    )

    assert promoted == config.output_root / PHASE_DIRS["00"]
    assert current_record.read_bytes() == before
    for artifact in phase.output_artifacts:
        relative = Path(artifact.path).relative_to("phases", "00")
        assert (promoted / relative).is_file()


def test_compatibility_promotion_restores_previous_view_on_metadata_failure(
    raw_archive, monkeypatch
):
    from buduunkhad.core import run_storage
    from buduunkhad.core.run_storage import RunLayout, promote_phase_to_current

    config, register, _raw = raw_archive
    manifest = run_pipeline(config, register, only=["00"], dry_run=False)
    phase = manifest.phases[0]
    layout = RunLayout(config.runs_root, manifest.run_id)
    destination = config.output_root / PHASE_DIRS["00"]
    current_record = config.output_root / ".buduunkhad-current-view.json"
    previous_files = {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    }
    previous_record = current_record.read_bytes()

    def fail_current_view(*_args, **_kwargs):
        raise OSError("injected metadata failure")

    monkeypatch.setattr(run_storage, "_record_current_view", fail_current_view)

    with pytest.raises(OSError, match="injected metadata failure"):
        promote_phase_to_current(
            layout,
            "00",
            config.output_root,
            phase.sealed_files,
        )

    restored_files = {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    }
    assert restored_files == previous_files
    assert current_record.read_bytes() == previous_record
    assert not list(config.output_root.glob(".promote-*"))
    assert not list(config.output_root.glob(".previous-*"))


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
