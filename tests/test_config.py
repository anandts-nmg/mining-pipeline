"""Tests for config + register loading and validation."""

from __future__ import annotations

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


def test_phase_dirs_cover_workflow():
    assert PHASE_DIRS["00"] == "00_Raw_Files_Archive"
    assert PHASE_DIRS["01"] == "01_Phase_1_Data_Audit_and_Master_GIS_Setup"
    assert PHASE_DIRS["99"] == "99_Final_Deliverables"
    assert len(PHASE_DIRS) == 13
