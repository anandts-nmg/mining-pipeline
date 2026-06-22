"""Phase 02 (Remote Sensing Preprocessing) tests against synthetic fixtures."""

from __future__ import annotations

from buduunkhad.core import crs as crs_mod
from buduunkhad.core import paths
from buduunkhad.core.gates import GateStatus
from buduunkhad.phases.base import RunContext
from buduunkhad.phases.phase00_archive import Phase00Archive
from buduunkhad.phases.phase02_remote_sensing import Phase02RemoteSensing


def _ctx(config, register, *, dry_run=False):
    return RunContext(config=config, register=register, run_id="test02", dry_run=dry_run)


def test_phase02_real_run(raw_archive):
    config, register, _raw = raw_archive
    ctx = _ctx(config, register)
    Phase00Archive().run(ctx)  # materialise working copies

    phase = Phase02RemoteSensing()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "ok"

    pdir = paths.phase_dir(config.output_root, "02")
    reproj = list((pdir / "02_Reprojected_EPSG32647").glob("*.tif"))
    assert len(reproj) == 15  # all raster-type inputs in 9-46, 73-78

    # reprojected rasters are in EPSG:32647
    audit = crs_mod.audit_raster(reproj[0])
    assert audit.epsg == config.target_epsg

    # two DEM elevations -> 4 derivatives each (hillshade/slope/aspect/flow)
    deriv = list((pdir / "03_DEM_Derivatives").glob("*.tif"))
    assert len(deriv) == 8
    kinds = {"Hillshade", "SlopeDeg", "Aspect", "FlowAccumulation"}
    for kind in kinds:
        assert any(kind in p.name for p in deriv), f"missing {kind} derivative"

    # QA/QC log + orchestrated method notes
    assert (pdir / "06_QAQC" / f"{config.register_prefix}_RemoteSensing_QAQC_Log.xlsx").exists()
    assert list((pdir / "04_Indices_Composites").glob("*.md"))
    assert list((pdir / "05_KOMPSAT_Ortho_Pansharpen").glob("*.md"))

    report = phase.qaqc(ctx)
    decision = phase.gate(report, ctx)
    assert decision.status is GateStatus.GO, decision.reason


def test_phase02_dry_run(project):
    config, register, _tmp = project
    ctx = _ctx(config, register, dry_run=True)
    phase = Phase02RemoteSensing()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "dry-run"

    pdir = paths.phase_dir(config.output_root, "02")
    assert (pdir / "06_QAQC" / f"{config.register_prefix}_RemoteSensing_QAQC_Log.xlsx").exists()
    # no derivatives produced without data
    assert not list((pdir / "03_DEM_Derivatives").glob("*.tif"))
    # method notes still scaffolded
    assert list((pdir / "04_Indices_Composites").glob("*.md"))
