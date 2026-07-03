"""Tests for config + register loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from buduunkhad.config import RAW_ROOT_ENV
from buduunkhad.core.paths import PHASE_DIRS


def test_config_loads(project):
    config, register, _tmp = project
    assert config.project.project_code == "XV-023222"
    assert config.project.license_code == "L23222"
    assert config.target_epsg == 32647
    assert config.data_prefix == "XV023222_Buduunkhad"
    assert config.register_prefix == "XV-023222_Buduunkhad"
    assert config.boundary.input_no == 8
    assert config.boundary.buffers_m == [500, 1000, 5000, 10000, 20000]


def test_register_is_complete(project):
    _config, register, _tmp = project
    # 78 methodology inputs + the SAS hand-interpreted 1:25k scan reconciled from
    # the real archive = 79, numbered contiguously from 1.
    assert len(register) == 79
    assert sorted(r.no for r in register) == list(range(1, 80))


def test_register_groups_match(project):
    config, register, _tmp = project
    from collections import Counter

    counts = Counter(r.evidence_group for r in register)
    for group in config.evidence_groups:
        assert counts[group.name] == group.count


def test_register_groups_cross_validation(project):
    from buduunkhad.config import _validate_register_groups

    config, register, _tmp = project
    _validate_register_groups(register, config.evidence_groups)  # real data agrees -> no raise
    with pytest.raises(ValueError):
        # one row short -> a per-group count no longer matches project.yaml
        _validate_register_groups(register[:-1], config.evidence_groups)


def _write_register(path: Path, rows: list[str]) -> None:
    header = "no,evidence_group,filename,file_type,primary_phase,methodology_action,is_sidecar,parent_file"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


def test_register_rejects_duplicate_filename(tmp_path):
    from buduunkhad.config import load_register

    reg = tmp_path / "r.csv"
    _write_register(reg, ["1,G,dup.tif,raster,02,,,", "2,G,dup.tif,raster,02,,,"])
    with pytest.raises(ValueError):
        load_register(reg)


def test_manifest_rejects_duplicate_filename(tmp_path):
    from buduunkhad.core.ingest import load_manifest

    m = tmp_path / "m.csv"
    m.write_text(
        "no,evidence_group,filename,file_type,is_sidecar,parent_file,"
        "drive_file_id,drive_size_bytes,drive_theme_folder,match_status\n"
        "1,G,dup.jpg,image_scan,false,,ID1,10,T,matched\n"
        "2,G,dup.jpg,image_scan,false,,ID2,20,T,matched\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_manifest(m)


def test_register_sidecar_parents_exist(project):
    _config, register, _tmp = project
    names = {r.filename for r in register}
    for r in register:
        if r.is_sidecar and r.parent_file:
            assert r.parent_file in names


def test_master_gpkg_layers(project):
    config, _register, _tmp = project
    names = {layer.name for layer in config.master_gpkg_layers}
    assert "license_boundary" in names
    assert "pXRF_reading_table" in names
    assert len(config.master_gpkg_layers) == 13
    # exactly one aspatial layer
    aspatial = [layer for layer in config.master_gpkg_layers if not layer.is_spatial]
    assert [layer.name for layer in aspatial] == ["pXRF_reading_table"]


def test_raw_root_env_override(project, monkeypatch):
    config, _register, _tmp = project
    # default: resolves under the project base dir
    assert config.raw_root.name == "00_Raw_Files_Archive"
    # override: a per-machine path (e.g. a Drive-for-Desktop folder) wins
    target = Path.home() / "drive_stub" / "0. Raw Data"
    monkeypatch.setenv(RAW_ROOT_ENV, str(target))
    assert config.raw_root == target


def test_phase_dirs_cover_workflow():
    assert PHASE_DIRS["00"] == "00_Raw_Files_Archive"
    assert PHASE_DIRS["01"] == "01_Phase_1_Data_Audit_and_Master_GIS_Setup"
    assert PHASE_DIRS["99"] == "99_Final_Deliverables"
    assert len(PHASE_DIRS) == 13
