"""Phase 02 (Remote Sensing Preprocessing) tests against synthetic fixtures.

Phase 02 clips to Phase 01's AOIs (5 km / 1 km buffers + licence boundary), so the
real-run test runs Phase 00 (working copies) and Phase 01 (buffers + boundary) first.
"""

from __future__ import annotations

import rasterio

from buduunkhad.core import paths, raster_writers
from buduunkhad.core.gates import GateStatus
from buduunkhad.phases.base import RunContext
from buduunkhad.phases.phase00_archive import Phase00Archive
from buduunkhad.phases.phase01_data_audit import Phase01DataAudit
from buduunkhad.phases.phase02_remote_sensing import Phase02RemoteSensing


def _ctx(config, register, *, dry_run=False):
    return RunContext(config=config, register=register, run_id="test02", dry_run=dry_run)


def test_phase02_real_run(raw_archive):
    config, register, _raw = raw_archive
    ctx = _ctx(config, register)
    Phase00Archive().run(ctx)  # materialise working copies
    p1 = Phase01DataAudit()
    p1.prepare(ctx)
    p1.run(ctx)  # produce the buffer + licence-boundary AOIs Phase 02 clips to

    phase = Phase02RemoteSensing()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "ok"

    pdir = paths.phase_dir(config.output_root, "02")

    # DEM terrain derivatives (multi-azimuth hillshade, slope, aspect, TRI, curvature, flow)
    deriv_dir = pdir / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS" / "04_Terrain_Derivatives"
    names = " ".join(p.name for p in deriv_dir.glob("*.tif"))
    for kind in (
        "Hillshade_Az315",
        "Hillshade_Az045",
        "SlopeDeg",
        "Aspect",
        "TerrainRuggedness",
        "ProfileCurvature",
        "PlanCurvature",
        "FlowAccumulation",
    ):
        assert kind in names, f"missing {kind} derivative"

    # every produced raster is a valid COG
    assert phase._outputs, "no COG outputs produced"
    for p in phase._outputs:
        assert raster_writers.is_cog(p), f"{p.name} is not a valid COG"

    # NumObservations (#10) clip margins must be tagged nodata, not left as a valid 0 count
    num_obs = list(deriv_dir.glob("*NumObservations*.tif"))
    if num_obs:
        with rasterio.open(num_obs[0]) as ds:
            assert ds.nodata == 255, f"{num_obs[0].name} missing nodata=255"

    # QA/QC log + the master-named QA/QC report + terrain index + method notes
    assert (
        pdir / "06_RemoteSensing_QAQC" / f"{config.register_prefix}_RemoteSensing_QAQC_Log.xlsx"
    ).exists()
    assert list((pdir / "06_RemoteSensing_QAQC").glob("*RemoteSensing_QAQC_Report*.docx"))
    assert list(
        (pdir / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS" / "04_Terrain_Derivatives").glob(
            "*Terrain_Derivatives_Index*.xlsx"
        )
    )
    assert list((pdir / "01_Sentinel2_SNAP13" / "04_Indices").glob("*.md"))
    assert list((pdir / "02_ASTER_Workflow_v5" / "04_Index_Calculation").glob("*.md"))
    assert list((pdir / "03_KOMPSAT2_ILWIS368_QGIS" / "04_Orthorectification").glob("*.md"))

    # KOMPSAT bands + ASTER HDF are method-note rows (not processed in-pipeline)
    decisions = {r["no"]: r["decision"] for r in phase._rows}
    assert decisions[73] == "Method-note"
    assert decisions[24] == "Method-note"
    # support-evidence flag stamped on every row
    assert all(r["validation_status"] == "Support evidence only" for r in phase._rows)

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
    assert (
        pdir / "06_RemoteSensing_QAQC" / f"{config.register_prefix}_RemoteSensing_QAQC_Log.xlsx"
    ).exists()
    # no derivatives produced without data
    assert not list(
        (pdir / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS" / "04_Terrain_Derivatives").glob("*.tif")
    )
    # method notes + handover artifacts still scaffolded
    assert list((pdir / "01_Sentinel2_SNAP13" / "04_Indices").glob("*.md"))
    assert list((pdir / "06_RemoteSensing_QAQC").glob("*RemoteSensing_QAQC_Report*.docx"))
