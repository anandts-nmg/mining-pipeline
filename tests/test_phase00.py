"""Phase 00 (Raw Files Archive) tests against synthetic fixtures."""

from __future__ import annotations

from buduunkhad.core import paths
from buduunkhad.core.gates import GateStatus
from buduunkhad.core.registers import read_checksum_register_csv
from buduunkhad.phases.base import RunContext
from buduunkhad.phases.phase00_archive import Phase00Archive


def _ctx(config, register, *, dry_run=False, override=False):
    return RunContext(
        config=config, register=register, run_id="test00", dry_run=dry_run, override=override
    )


def test_phase00_real_run(raw_archive):
    config, register, raw_root = raw_archive
    ctx = _ctx(config, register)
    phase = Phase00Archive()
    phase.prepare(ctx)
    result = phase.run(ctx)

    archive = paths.phase_dir(config.output_root, "00")
    prefix = config.register_prefix
    inv = archive / f"{prefix}_79Input_Master_Inventory.xlsx"
    integ = archive / f"{prefix}_Raw_Data_Integrity_Log.xlsx"
    checksum = archive / "SHA-256_Checksum_Register.csv"
    readme = archive / f"{prefix}_Source_Data_Readme.docx"
    for p in (inv, integ, checksum, readme):
        assert p.exists(), f"missing {p.name}"

    # checksum register has one row per raw file present in the synthetic archive
    checks = read_checksum_register_csv(checksum)
    assert len(checks) == len(register)

    # working copies materialised (e.g. the boundary KMZ into its group folder)
    boundary = ctx.record_by_no(config.boundary.input_no)
    wc = archive / boundary.evidence_group / boundary.filename
    assert wc.exists()

    # raw archive left untouched
    assert result.status == "ok"

    report = phase.qaqc(ctx)
    assert report.passed
    decision = phase.gate(report, ctx)
    assert decision.status is GateStatus.GO


def test_phase00_raw_is_untouched(raw_archive):
    config, register, raw_root = raw_archive
    from buduunkhad.core import raw_guard

    before = {r.relative_path: r.sha256 for r in raw_guard.build_checksum_records(raw_root)}
    ctx = _ctx(config, register)
    phase = Phase00Archive()
    phase.prepare(ctx)
    phase.run(ctx)
    after = raw_guard.verify_against(raw_root, before)
    assert after.ok, after.summary()


def test_phase00_dry_run_writes_empty_scaffolding(project):
    config, register, _tmp = project  # no raw_archive -> no data on disk
    ctx = _ctx(config, register, dry_run=True)
    phase = Phase00Archive()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "dry-run"

    archive = paths.phase_dir(config.output_root, "00")
    checksum = archive / "SHA-256_Checksum_Register.csv"
    assert checksum.exists()
    # header only, no rows
    assert read_checksum_register_csv(checksum) == {}
    # evidence-group subfolders created
    for group in config.evidence_groups:
        assert (archive / group.name).is_dir()


def test_phase00_archives_unregistered_supplementary_files(raw_archive):
    # Raw files NOT in the register (e.g. DataRoom register/explanation docs, folder readmes) must
    # still be archived, so the control archive mirrors the FULL checksummed raw set (not just the
    # register-listed inputs). Regression for the archive-certifies-more-than-it-safeguards gap.
    config, register, raw_root = raw_archive
    supp = raw_root / "ZZ_DataRoom" / "MasterRegister_Explanation.docx"
    supp.parent.mkdir(parents=True, exist_ok=True)
    supp.write_bytes(b"supplementary register doc not present in input_register")

    ctx = _ctx(config, register)
    phase = Phase00Archive()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "ok"

    archive = paths.phase_dir(config.output_root, "00")
    archived = (
        archive
        / Phase00Archive.SUPPLEMENTARY_DIR
        / "ZZ_DataRoom"
        / "MasterRegister_Explanation.docx"
    )
    assert archived.exists(), "supplementary (unregistered) raw file was not archived"
    assert archived.read_bytes() == supp.read_bytes()  # byte-identical copy
    assert phase._supplementary == 1
