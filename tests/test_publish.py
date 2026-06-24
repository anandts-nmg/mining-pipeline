"""Tests for the deliverable publish step (core.publish)."""

from __future__ import annotations

from pathlib import Path

from buduunkhad.core.publish import collect_deliverables, publish


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


def test_collect_excludes_working_copies(tmp_path):
    _make_output(tmp_path)
    names = {p.name for p in collect_deliverables(tmp_path)}
    assert "XV-023222_Buduunkhad_Master_GIS_Database.gpkg" in names
    assert "SHA-256_Checksum_Register.csv" in names
    assert "XV-023222_Buduunkhad_Inventory.xlsx" in names
    assert "big_raster.tif" not in names  # raw working copy excluded
    assert "meta.txt" not in names  # non-deliverable extension excluded


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
    assert "big_raster.tif" not in copied  # never publish raw working copies
