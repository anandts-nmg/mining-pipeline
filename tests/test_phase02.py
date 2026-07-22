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
    aster_notes = list((pdir / "02_ASTER_Workflow_v5" / "04_Index_Calculation").glob("*.md"))
    assert aster_notes
    aster_note = aster_notes[0].read_text(encoding="utf-8")
    assert "The exact master requires" in aster_note
    assert "unlocated and obsolete as authority" in aster_note
    assert "frozen support-evidence chain" in aster_note
    assert "geologist's QGIS SOP" not in aster_note
    assert "reference `ASTER_Project` outputs" not in aster_note
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


def test_phase02_aster_falls_back_to_method_note_without_gdal(raw_archive, monkeypatch):
    """With no HDF4-capable gdalwarp (BUDUUNKHAD_GDAL_BIN=''), #73 degrades to the method-note
    row — never a failure — and the QA/QC item reads N/A, keeping the gate GO."""
    monkeypatch.setenv("BUDUUNKHAD_GDAL_BIN", "")
    config, register, _raw = raw_archive
    ctx = _ctx(config, register)
    Phase00Archive().run(ctx)
    p1 = Phase01DataAudit()
    p1.prepare(ctx)
    p1.run(ctx)

    phase = Phase02RemoteSensing()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "ok"
    row = next(r for r in phase._rows if r["no"] == 73)
    assert row["decision"] == "Method-note"
    assert "No HDF4-capable GDAL" in str(row["note"])
    assert not phase._aster_processed

    report = phase.qaqc(ctx)
    aster_item = next(i for i in report.items if "ASTER alteration" in i.item)
    assert aster_item.decision.value == "N/A"
    assert phase.gate(report, ctx).status is GateStatus.GO


def test_phase02_sentinel_clip_margins_flagged_nodata(raw_archive):
    """#74/#77 Sentinel composites have no source nodata; the licence clip must flag margins
    with a nodata value (not leave them as valid 0.0). Regression for the v0.3.1 fix."""
    import numpy as np
    from rasterio.transform import from_origin

    config, register, _raw = raw_archive
    ctx = _ctx(config, register)
    Phase00Archive().run(ctx)
    p1 = Phase01DataAudit()
    p1.prepare(ctx)
    p1.run(ctx)

    # overwrite the #74/#77 working copies with float32 rasters that declare NO nodata
    for no in (74, 77):
        rec = ctx.record_by_no(no)
        wc = paths.phase_dir(config.output_root, "00") / rec.evidence_group / rec.filename
        wc.parent.mkdir(parents=True, exist_ok=True)
        profile = {
            "driver": "GTiff",
            "height": 24,
            "width": 24,
            "count": 1,
            "dtype": "float32",
            "crs": "EPSG:4326",
            "transform": from_origin(96.35, 45.65, 0.01, 0.01),
        }
        with rasterio.open(wc, "w", **profile) as ds:
            ds.write(np.zeros((24, 24), dtype="float32"), 1)

    phase = Phase02RemoteSensing()
    phase.prepare(ctx)
    phase.run(ctx)

    out_by_no = {r["no"]: r.get("output", "") for r in phase._rows}
    for no in (74, 77):
        matches = [p for p in phase._outputs if p.name == out_by_no.get(no)]
        assert matches, f"no export produced for Sentinel #{no}"
        with rasterio.open(matches[0]) as ds:
            assert ds.nodata == -9999.0, f"Sentinel #{no} clip margin not flagged nodata"


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
