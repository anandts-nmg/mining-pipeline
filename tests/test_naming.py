"""Tests for the output-naming convention."""

from __future__ import annotations

import pytest

from buduunkhad.core import naming

DATA_PREFIX = "XV023222_Buduunkhad"
REG_PREFIX = "XV-023222_Buduunkhad"


def test_version_tag():
    assert naming.version_tag(1) == "v01"
    assert naming.version_tag(12) == "v12"
    with pytest.raises(ValueError):
        naming.version_tag(0)


def test_epsg_tag():
    assert naming.epsg_tag(32647) == "EPSG32647"


def test_buffer_param():
    assert naming.buffer_param([500, 1000, 5000, 10000, 20000]) == "Buffer_500m_1km_5km_10km_20km"
    assert naming.buffer_param([250]) == "Buffer_250m"


def test_data_name_boundary_matches_methodology():
    name = naming.data_name(
        DATA_PREFIX,
        "L23222_LicenseBoundary",
        crs_or_param=naming.epsg_tag(32647),
        version=1,
        ext="gpkg",
    )
    assert name == "XV023222_Buduunkhad_L23222_LicenseBoundary_EPSG32647_v01.gpkg"


def test_data_name_buffer_no_version():
    param = f"{naming.buffer_param([500, 1000, 5000, 10000, 20000])}_{naming.epsg_tag(32647)}"
    name = naming.data_name(DATA_PREFIX, "Project", crs_or_param=param, version=None, ext="gpkg")
    assert name == "XV023222_Buduunkhad_Project_Buffer_500m_1km_5km_10km_20km_EPSG32647.gpkg"


def test_register_name_matches_methodology():
    name = naming.register_name(REG_PREFIX, "78Input_Master_Inventory", ext="xlsx")
    assert name == "XV-023222_Buduunkhad_78Input_Master_Inventory.xlsx"


def test_draft_suffix():
    name = naming.data_name(
        DATA_PREFIX, "Target", crs_or_param="EPSG32647", version=2, ext="gpkg", draft=True
    )
    assert name == "XV023222_Buduunkhad_Target_EPSG32647_v02_DRAFT.gpkg"


def test_ext_normalisation():
    assert naming.data_name(DATA_PREFIX, "X", version=1, ext=".tif").endswith("_v01.tif")
