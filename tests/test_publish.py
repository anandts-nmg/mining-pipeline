"""Tests for the deliverable publish step (core.publish)."""

from __future__ import annotations

from pathlib import Path

import pytest

from buduunkhad.core.publish import PublishError, collect_deliverables, publish


def _make_output(root: Path) -> None:
    """A minimal output tree: deliverables + a raw working copy that must be excluded."""
    arch = root / "00_Raw_Files_Archive"
    arch.mkdir(parents=True)
    (arch / "SHA-256_Checksum_Register.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (arch / "XV-023222_Buduunkhad_Inventory.xlsx").write_bytes(b"PK\x03\x04stub")
    # raw working copies live in evidence-group folders -> excluded
    wc = arch / "07_Basemap_Sentinel2_ASTER"
    wc.mkdir()
    (wc / "big_raster.tif").write_bytes(b"\x00" * 4096)
    (wc / "meta.txt").write_text("x", encoding="utf-8")  # non-deliverable suffix
    # phase 01 deliverable
    gpkg_dir = root / "01_Phase_1_Data_Audit_and_Master_GIS_Setup" / "06_Master_GeoPackage_Schema"
    gpkg_dir.mkdir(parents=True)
    (gpkg_dir / "XV-023222_Buduunkhad_Master_GIS_Database.gpkg").write_bytes(b"SQLite format 3\x00")
    # phase 02 derived COG (in a processing folder, not a working-copy dir) -> published
    p02 = root / "02_Phase_2_Remote_Sensing_Preprocessing" / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS"
    deriv = p02 / "04_Terrain_Derivatives"
    deriv.mkdir(parents=True)
    (deriv / "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif").write_bytes(b"II*\x00cog")
    # phase 03 evidence GPKG -> published, grouped under Phase03/
    p03 = (
        root
        / "03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis"
        / "09_Geological_Evidence_Layers_GPKG"
    )
    p03.mkdir(parents=True)
    (p03 / "XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg").write_bytes(
        b"SQLite format 3\x00"
    )


def test_collect_excludes_working_copies(tmp_path):
    _make_output(tmp_path)
    names = {p.name for p in collect_deliverables(tmp_path)}
    assert "XV-023222_Buduunkhad_Master_GIS_Database.gpkg" in names
    assert "SHA-256_Checksum_Register.csv" in names
    assert "XV-023222_Buduunkhad_Inventory.xlsx" in names
    assert "big_raster.tif" not in names  # raw working copy excluded
    assert "meta.txt" not in names  # non-deliverable extension excluded
    assert "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif" in names  # derived COG included
    assert "XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg" in names  # phase 03 included


def test_publish_copies_versioned_with_index(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    _make_output(out)
    result = publish(out, tmp_path / "drive", "v0.1.0")

    assert result.dest.exists() and result.dest.name.endswith("v0.1.0")
    assert (result.dest / "INDEX.md").exists()
    assert result.skipped_working_copies >= 1

    copied = {p.name for p in result.dest.rglob("*") if p.is_file()}
    assert "XV-023222_Buduunkhad_Master_GIS_Database.gpkg" in copied
    assert "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif" in copied  # derived COG published
    assert "big_raster.tif" not in copied  # never publish raw working copies

    # deliverables are grouped by two-digit phase prefix into PhaseNN/ (short, reader-friendly)
    assert (result.dest / "Phase01" / "XV-023222_Buduunkhad_Master_GIS_Database.gpkg").exists()
    assert (
        result.dest / "Phase02" / "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif"
    ).exists()
    assert (
        result.dest / "Phase03" / "XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg"
    ).exists()


def test_publish_refuses_existing_nonempty_label(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    _make_output(out)
    drive = tmp_path / "drive"
    publish(out, drive, "v1")
    # re-publishing the same label would silently merge/overwrite -> must refuse
    with pytest.raises(PublishError):
        publish(out, drive, "v1")


def test_publish_detects_name_collision(tmp_path):
    out = tmp_path / "out"
    # two distinct files under the same phase prefix with the same basename -> flatten collision
    (out / "01_a").mkdir(parents=True)
    (out / "01_a" / "dup.gpkg").write_bytes(b"SQLite format 3\x00a")
    (out / "01_b").mkdir(parents=True)
    (out / "01_b" / "dup.gpkg").write_bytes(b"SQLite format 3\x00b")
    with pytest.raises(PublishError):
        publish(out, tmp_path / "drive", "v1")
