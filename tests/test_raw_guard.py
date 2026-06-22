"""Tests for raw read-only enforcement and integrity verification."""

from __future__ import annotations

import pytest

from buduunkhad.core import raw_guard
from buduunkhad.core.raw_guard import RawReadOnlyError


def test_open_raw_refuses_write_modes(tmp_path):
    f = tmp_path / "raw.bin"
    f.write_bytes(b"abc")
    # read is fine
    with raw_guard.open_raw(f, "rb") as fh:
        assert fh.read() == b"abc"
    for mode in ("w", "wb", "a", "r+", "x"):
        with pytest.raises(RawReadOnlyError):
            raw_guard.open_raw(f, mode)


def test_open_raw_enforces_root(tmp_path):
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"x")
    with pytest.raises(RawReadOnlyError):
        raw_guard.open_raw(outside, "rb", raw_root=raw_root)


def test_assert_not_raw_write(tmp_path):
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    # inside raw -> refused
    with pytest.raises(RawReadOnlyError):
        raw_guard.assert_not_raw_write(raw_root / "a" / "b.tif", raw_root)
    # outside raw -> allowed (no exception)
    raw_guard.assert_not_raw_write(tmp_path / "outputs" / "b.tif", raw_root)


def test_compute_sha256_stable(tmp_path):
    f = tmp_path / "f.bin"
    f.write_bytes(b"hello world")
    digest = raw_guard.compute_sha256(f)
    # sha256("hello world")
    assert digest == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert raw_guard.compute_sha256(f) == digest


def test_build_and_verify_checksums(tmp_path):
    raw_root = tmp_path / "raw"
    (raw_root / "g").mkdir(parents=True)
    a = raw_root / "g" / "a.txt"
    b = raw_root / "g" / "b.txt"
    a.write_text("alpha")
    b.write_text("beta")

    records = raw_guard.build_checksum_records(raw_root)
    assert {r.filename for r in records} == {"a.txt", "b.txt"}
    expected = {r.relative_path: r.sha256 for r in records}

    # unchanged -> ok
    assert raw_guard.verify_against(raw_root, expected).ok

    # modify a file -> mismatch detected, integrity fails
    a.write_text("ALPHA-CHANGED")
    result = raw_guard.verify_against(raw_root, expected)
    assert not result.ok
    assert "g/a.txt" in result.mismatched

    # remove a file -> missing detected
    b.unlink()
    result2 = raw_guard.verify_against(raw_root, expected)
    assert "g/b.txt" in result2.missing
