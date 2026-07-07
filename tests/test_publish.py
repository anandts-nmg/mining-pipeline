"""Tests for the deliverable publish step (core.publish)."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from buduunkhad.core.publish import (
    PublishError,
    backup_raw_archive,
    collect_deliverables,
    latest_gate_per_phase,
    publish,
)


def _write_register(path: Path, rows: list[tuple[str, str, bytes]]) -> None:
    """rows = [(filename, relative_path, content)] -> a SHA-256 checksum register CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["filename", "relative_path", "sha256", "size_bytes"])
        for name, rel, content in rows:
            w.writerow([name, rel, hashlib.sha256(content).hexdigest(), len(content)])


def test_backup_raw_archive_copies_and_verifies(tmp_path):
    raw = tmp_path / "raw"
    (raw / "grpA").mkdir(parents=True)
    (raw / "grpA" / "a.tif").write_bytes(b"AAAA")
    (raw / "readme.txt").write_bytes(b"notes")
    reg = tmp_path / "SHA-256_Checksum_Register.csv"
    _write_register(reg, [("a.tif", "grpA/a.tif", b"AAAA"), ("readme.txt", "readme.txt", b"notes")])

    res = backup_raw_archive(raw, reg, tmp_path / "drive", "v01")

    assert res.dest == tmp_path / "drive" / "Raw_Archive_Backup_v01"
    assert res.files == 2 and res.verified == 2
    assert not res.missing and not res.mismatched
    assert (res.dest / "0_Raw_Data" / "grpA" / "a.tif").read_bytes() == b"AAAA"
    assert (res.dest / "SHA-256_Checksum_Register.csv").exists()  # register carried to root
    assert (res.dest / "README.md").exists()


def test_backup_raw_archive_detects_mismatch(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.bin").write_bytes(b"REAL")
    reg = tmp_path / "reg.csv"
    _write_register(reg, [("a.bin", "a.bin", b"WRONG")])  # register hash won't match the file
    with pytest.raises(PublishError):
        backup_raw_archive(raw, reg, tmp_path / "drive", "v01")


def test_backup_raw_archive_refuses_existing_label(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.bin").write_bytes(b"X")
    reg = tmp_path / "reg.csv"
    _write_register(reg, [("a.bin", "a.bin", b"X")])
    backup_raw_archive(raw, reg, tmp_path / "drive", "v01")
    with pytest.raises(PublishError):  # non-empty label dir must not be silently clobbered
        backup_raw_archive(raw, reg, tmp_path / "drive", "v01")
    # overwrite=True is allowed
    res = backup_raw_archive(raw, reg, tmp_path / "drive", "v01", overwrite=True)
    assert res.verified == 1


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


def _write_manifest(runs_root, run_id, dry_run, phases):
    d = runs_root / run_id
    d.mkdir(parents=True)
    (d / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "dry_run": dry_run,
                "phases": [
                    {"phase_id": pid, "gate": {"status": st, "provisional": prov}}
                    for pid, st, prov in phases
                ],
            }
        ),
        encoding="utf-8",
    )


def test_latest_gate_per_phase_ignores_dry_and_takes_most_recent(tmp_path):
    runs = tmp_path / "runs"
    # ascending timestamps: an early real run, then a dry run, then a newer real run for 02/03
    _write_manifest(runs, "20260101T000000", False, [("00", "go", False), ("01", "go", False)])
    _write_manifest(runs, "20260102T000000", True, [("02", "go", False)])  # dry -> ignored
    _write_manifest(runs, "20260103T000000", False, [("02", "go", True), ("03", "go", True)])

    gates = latest_gate_per_phase(runs)
    assert set(gates) == {"00", "01", "02", "03"}
    assert gates["00"]["status"] == "go" and not gates["00"]["provisional"]
    assert gates["02"]["provisional"] is True  # from the real run, not the dry one
    assert gates["02"]["run_id"] == "20260103T000000"


def test_publish_detects_name_collision(tmp_path):
    out = tmp_path / "out"
    # two distinct files under the same phase prefix with the same basename -> flatten collision
    (out / "01_a").mkdir(parents=True)
    (out / "01_a" / "dup.gpkg").write_bytes(b"SQLite format 3\x00a")
    (out / "01_b").mkdir(parents=True)
    (out / "01_b" / "dup.gpkg").write_bytes(b"SQLite format 3\x00b")
    with pytest.raises(PublishError):
        publish(out, tmp_path / "drive", "v1")
