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
    assert bgdf.crs is not None
    assert bgdf.crs.to_epsg() == config.target_epsg
    assert len(bgdf) >= 1

    # buffer gpkg with 5 rings
    buffer_files = list(gpkg_dir.glob("*Buffer*EPSG32647*.gpkg"))
    assert buffer_files, "buffer gpkg not written"
    bufgdf = gpd.read_file(buffer_files[0])
    assert len(bufgdf) == len(config.boundary.buffers_m)

    # 1A.3/1B.3 source-traceability fields on both vector deliverables
    provenance = {
        "source_raw_input_no",
        "source_raw_filename",
        "processing_phase",
        "processing_software",
        "processing_action",
        "output_filename",
        "qaqc_status",
        "validation_status",
        "limitation",
    }
    for gdf, label in ((bgdf, "boundary"), (bufgdf, "buffers")):
        missing = provenance - set(gdf.columns)
        assert not missing, f"{label} missing provenance fields: {missing}"
    assert bgdf.iloc[0]["source_raw_input_no"] == str(config.boundary.input_no)
    assert bgdf.iloc[0]["processing_phase"] == "01"
    assert bgdf.iloc[0]["validation_status"] == "Historical only"
    assert bufgdf.iloc[0]["output_filename"] == buffer_files[0].name

    # CRS/Georef QAQC log + confidence ranking + qgz
    crs_log = pdir / "03_CRS_Check" / f"{prefix}_CRS_Georeference_QAQC_Log.xlsx"
    assert crs_log.exists()

    # the log carries the methodology's extent / pixel-alignment / sidecar checks
    import pandas as pd

    log_df = pd.read_excel(crs_log)
    for col in ("extent", "pixel_aligned", "sidecar_status"):
        assert col in log_df.columns, f"CRS log missing '{col}' column"
    assert len(log_df) >= 1
    # synthetic fixture rasters are north-up GeoTIFFs -> all audited as aligned
    assert log_df["pixel_aligned"].astype(bool).all()
    assert log_df["extent"].astype(str).str.contains(",").all()
    assert (pdir / "07_Data_Confidence_Ranking" / f"{prefix}_Data_Confidence_Ranking.xlsx").exists()

    # layered master QGIS project: boundary + buffers on top of the 13 schema layers,
    # with datasources relative to the .qgz that resolve on disk
    from buduunkhad.core.qgis_project import read_qgz_layers

    qgz = pdir / "08_Master_QGIS_Project_Setup" / f"{prefix}_Master_QGIS_Project.qgz"
    assert qgz.exists()
    entries = read_qgz_layers(qgz)
    assert len(entries) == 2 + len(config.master_gpkg_layers)
    assert entries[0]["name"].startswith("License Boundary")
    assert entries[1]["name"].startswith("Project Buffers")
    for e in entries:
        rel = e["datasource"].split("|", 1)[0]
        assert (qgz.parent / rel).resolve().exists(), f"datasource does not resolve: {rel}"
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

    # dry-run project carries the schema layers only (no boundary/buffers yet)
    from buduunkhad.core.qgis_project import read_qgz_layers

    qgz = (
        pdir / "08_Master_QGIS_Project_Setup" / f"{config.register_prefix}_Master_QGIS_Project.qgz"
    )
    assert qgz.exists()
    assert len(read_qgz_layers(qgz)) == len(config.master_gpkg_layers)
    _assert_phase1_deliverables(pdir)
