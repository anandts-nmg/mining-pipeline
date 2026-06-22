"""Phase 01 (Data Audit & Master GIS Setup) tests against synthetic fixtures."""

from __future__ import annotations

from buduunkhad.core import paths, vector_io
from buduunkhad.core.gates import GateStatus
from buduunkhad.phases.base import RunContext
from buduunkhad.phases.phase00_archive import Phase00Archive
from buduunkhad.phases.phase01_data_audit import Phase01DataAudit

_PHASE1_REQUIRED_DELIVERABLES = {
    "XV-023222_Buduunkhad_Master_GIS_Database.gpkg",
    "XV-023222_Buduunkhad_Master_QGIS_Project.qgz",
    "XV-023222_Buduunkhad_Phase1_File_Inventory.xlsx",
    "XV-023222_Buduunkhad_CRS_Georeference_QAQC_Log.xlsx",
    "XV-023222_Buduunkhad_Data_Confidence_Ranking.xlsx",
    "XV-023222_Buduunkhad_Data_Gap_Register.xlsx",
    "XV-023222_Buduunkhad_Phase1_Master_GIS_Index_Map.pdf",
    "XV-023222_Buduunkhad_Phase1_Desktop_Study_Summary.docx",
    "XV-023222_Buduunkhad_Phase2_Ready_Dataset_List.xlsx",
}


def _ctx(config, register, *, dry_run=False):
    return RunContext(config=config, register=register, run_id="test01", dry_run=dry_run)


def _run_phase00(config, register):
    ctx = _ctx(config, register)
    p0 = Phase00Archive()
    p0.prepare(ctx)
    p0.run(ctx)


def _assert_phase1_deliverables(pdir):
    produced = {p.name for p in pdir.rglob("*") if p.is_file()}
    missing = _PHASE1_REQUIRED_DELIVERABLES - produced
    assert not missing, f"missing Phase 1 deliverables: {sorted(missing)}"


def test_phase01_real_run(raw_archive):
    config, register, _raw = raw_archive
    _run_phase00(config, register)  # materialise working copies

    ctx = _ctx(config, register)
    phase = Phase01DataAudit()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "ok"

    pdir = paths.phase_dir(config.output_root, "01")
    prefix = config.register_prefix

    # master gpkg with all 13 typed layers
    master = pdir / "06_Master_GeoPackage_Schema" / f"{prefix}_Master_GIS_Database.gpkg"
    assert master.exists()
    layers = set(vector_io.list_gpkg_layers(master))
    expected = {layer.name for layer in config.master_gpkg_layers}
    assert expected.issubset(layers)

    # boundary gpkg in EPSG:32647 with one feature
    import geopandas as gpd

    gpkg_dir = pdir / "05_KMZ_KML_to_GPKG"
    boundary_files = list(gpkg_dir.glob("*LicenseBoundary*EPSG32647*.gpkg"))
    assert boundary_files, "boundary gpkg not written"
    bgdf = gpd.read_file(boundary_files[0])
    assert bgdf.crs.to_epsg() == config.target_epsg
    assert len(bgdf) >= 1

    # buffer gpkg with 5 rings
    buffer_files = list(gpkg_dir.glob("*Buffer*EPSG32647*.gpkg"))
    assert buffer_files, "buffer gpkg not written"
    bufgdf = gpd.read_file(buffer_files[0])
    assert len(bufgdf) == len(config.boundary.buffers_m)

    # CRS/Georef QAQC log + confidence ranking + qgz
    assert (pdir / "03_CRS_Check" / f"{prefix}_CRS_Georeference_QAQC_Log.xlsx").exists()
    assert (pdir / "07_Data_Confidence_Ranking" / f"{prefix}_Data_Confidence_Ranking.xlsx").exists()
    assert (pdir / "08_Master_QGIS_Project_Setup" / f"{prefix}_Master_QGIS_Project.qgz").exists()
    _assert_phase1_deliverables(pdir)

    report = phase.qaqc(ctx)
    decision = phase.gate(report, ctx)
    assert decision.status is GateStatus.GO, decision.reason


def test_phase01_dry_run_creates_schema(project):
    config, register, _tmp = project
    ctx = _ctx(config, register, dry_run=True)
    phase = Phase01DataAudit()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "dry-run"

    pdir = paths.phase_dir(config.output_root, "01")
    master = (
        pdir / "06_Master_GeoPackage_Schema" / f"{config.register_prefix}_Master_GIS_Database.gpkg"
    )
    assert master.exists()
    layers = set(vector_io.list_gpkg_layers(master))
    assert {layer.name for layer in config.master_gpkg_layers}.issubset(layers)
    _assert_phase1_deliverables(pdir)
