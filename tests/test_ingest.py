"""Tests for the manifest-aware raw ingest layer (core.ingest)."""

from __future__ import annotations

import pytest

from buduunkhad.config import InputRecord
from buduunkhad.core.ingest import (
    DEFAULT_SIZE_THRESHOLD_MB,
    ManifestEntry,
    RawSource,
    coverage,
    load_manifest,
)


def _rec(filename: str, *, is_sidecar: bool = False, no: int = 1) -> InputRecord:
    return InputRecord(
        no=no,
        evidence_group="09_Remote_Sensing",
        filename=filename,
        file_type="raster",
        primary_phase="02",
        is_sidecar=is_sidecar,
    )


def test_load_manifest(project):
    config, _register, _tmp = project
    manifest = load_manifest(config.manifest_path)
    kmz = "MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz"
    assert kmz in manifest
    assert manifest[kmz].drive_file_id  # pinned to a Drive file id
    assert manifest[kmz].size_bytes == 3256
    # the KOMPSAT EULA is recorded but flagged absent from the canonical archive
    eula = manifest.get("KOMPSATEULAForm_3.1.pdf")
    assert eula is not None and not eula.present_in_archive


def test_resolve_by_basename(raw_archive):
    config, register, raw_root = raw_archive
    source = RawSource(raw_root)
    boundary = next(r for r in register if r.no == config.boundary.input_no)
    path = source.resolve(boundary)
    assert path is not None and path.exists() and path.name == boundary.filename


def test_tiered_policy():
    big_bytes = int((DEFAULT_SIZE_THRESHOLD_MB + 10) * 1024 * 1024)
    manifest = {
        "big.tif": ManifestEntry("big.tif", "id1", big_bytes, "09", "matched"),
        "small.jpg": ManifestEntry("small.jpg", "id2", 1024, "02", "matched"),
    }
    source = RawSource("does/not/exist", manifest)
    assert source.is_large(_rec("big.tif")) is True
    assert source.should_copy(_rec("big.tif")) is False
    assert source.should_copy(_rec("small.jpg")) is True
    # sidecars always travel with their parent, regardless of size
    assert source.should_copy(_rec("big.tif", is_sidecar=True)) is True


def test_provenance_keys():
    manifest = {"f.tif": ManifestEntry("f.tif", "drive99", 2048, "10_DEM", "matched")}
    source = RawSource("does/not/exist", manifest)
    prov = source.provenance(_rec("f.tif"))
    assert prov["drive_file_id"] == "drive99"
    assert prov["manifest_status"] == "matched"
    # a record absent from the manifest is clearly marked
    assert source.provenance(_rec("ghost.tif"))["manifest_status"] == "not-in-manifest"


def test_resolve_drive_mode_requires_fetcher(tmp_path):
    entry = ManifestEntry("f.bin", "drive123", 8, "09_Remote_Sensing", "matched")
    rec = _rec("f.bin")
    source = RawSource(tmp_path, {"f.bin": entry}, mode="drive")
    with pytest.raises(NotImplementedError):
        source.resolve(rec)

    def fake_fetch(e: ManifestEntry, dest):
        dest.write_bytes(b"x" * e.size_bytes)
        return dest

    fetched = RawSource(tmp_path, {"f.bin": entry}, mode="drive", fetcher=fake_fetch).resolve(rec)
    assert fetched is not None and fetched.exists()


def test_coverage(raw_archive):
    config, register, raw_root = raw_archive
    manifest = load_manifest(config.manifest_path)
    cov = coverage(register, manifest, raw_root)
    # the synthetic archive builds one file per register row -> none missing
    assert not cov.missing
    # synthetic placeholder sizes differ from the manifest's real Drive sizes
    assert cov.size_mismatch
