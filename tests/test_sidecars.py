"""Tests for sidecar detection and bundle copying."""

from __future__ import annotations

import pytest

from buduunkhad.core import sidecars


def test_is_sidecar():
    assert sidecars.is_sidecar("X.tfw")
    assert sidecars.is_sidecar("X.tif.aux.xml")
    assert sidecars.is_sidecar("X.tif.ovr")
    assert sidecars.is_sidecar("MSC_123_PN00_1G.rpc")
    assert sidecars.is_sidecar("MSC_123_PN00_1G.txt")
    assert not sidecars.is_sidecar("X.tif")
    assert not sidecars.is_sidecar("X.jpg")


def test_parent_filename():
    assert sidecars.parent_filename("X.tfw") == "X.tif"
    assert sidecars.parent_filename("X.jgw") == "X.jpg"
    assert sidecars.parent_filename("X.tif.aux.xml") == "X.tif"
    assert sidecars.parent_filename("X.tif.ovr") == "X.tif"
    # rpc/eph/txt have no extension-only rule -> None (looked up via the register)
    assert sidecars.parent_filename("X.rpc") is None


def test_find_sidecars(tmp_path):
    parent = tmp_path / "scene.tif"
    parent.write_bytes(b"raster")
    for sc in ("scene.tfw", "scene.tif.aux.xml", "scene.tif.ovr"):
        (tmp_path / sc).write_bytes(b"side")
    (tmp_path / "other.tif").write_bytes(b"nope")
    (tmp_path / "other.tfw").write_bytes(b"nope")

    found = {p.name for p in sidecars.find_sidecars(parent)}
    assert found == {"scene.tfw", "scene.tif.aux.xml", "scene.tif.ovr"}


def test_copy_bundle_copies_parent_and_sidecars(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    parent = src / "scene.tif"
    parent.write_bytes(b"raster-bytes")
    (src / "scene.tfw").write_bytes(b"world")
    (src / "scene.tif.aux.xml").write_bytes(b"aux")

    dst = tmp_path / "dst"
    bundle = sidecars.copy_bundle(parent, dst)

    assert bundle.parent.name == "scene.tif"
    assert {p.name for p in bundle.sidecars} == {"scene.tfw", "scene.tif.aux.xml"}
    assert (dst / "scene.tif").read_bytes() == b"raster-bytes"
    # source untouched
    assert parent.read_bytes() == b"raster-bytes"
    assert (src / "scene.tfw").exists()


def test_copy_bundle_refuses_overwrite(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    parent = src / "scene.tif"
    parent.write_bytes(b"x")
    dst = tmp_path / "dst"
    sidecars.copy_bundle(parent, dst)
    with pytest.raises(FileExistsError):
        sidecars.copy_bundle(parent, dst, overwrite=False)
    # overwrite=True is fine
    sidecars.copy_bundle(parent, dst, overwrite=True)
