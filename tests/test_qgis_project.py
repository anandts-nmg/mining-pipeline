"""core.qgis_project — deterministic layered .qgz generation."""

from __future__ import annotations

import zipfile
from xml.etree import ElementTree as ET

from buduunkhad.core.qgis_project import (
    QgzLayer,
    line_symbol,
    polygon_outline,
    read_qgz_layers,
    write_layered_qgz,
)


def _layers() -> list[QgzLayer]:
    return [
        QgzLayer(
            name="License Boundary (L23222)",
            source="../05_KMZ_KML_to_GPKG/boundary.gpkg|layername=license_boundary",
            geometry="MultiPolygon",
            symbol=polygon_outline("227,26,28,255", 0.8),
        ),
        QgzLayer(
            name="faults_structures_line",
            source="../06_Master_GeoPackage_Schema/master.gpkg|layername=faults_structures_line",
            geometry="LineString",
            symbol=line_symbol("0,0,0,255", 0.4, dash=True),
        ),
        QgzLayer(
            name="pXRF_reading_table",
            source="../06_Master_GeoPackage_Schema/master.gpkg|layername=pXRF_reading_table",
            geometry="None",
            visible=False,
        ),
    ]


def test_write_layered_qgz_roundtrip(tmp_path):
    qgz = write_layered_qgz(
        tmp_path / "project.qgz", epsg=32647, title="Test Master", layers=_layers()
    )
    entries = read_qgz_layers(qgz)
    assert [e["name"] for e in entries] == [
        "License Boundary (L23222)",
        "faults_structures_line",
        "pXRF_reading_table",
    ]
    assert len({e["id"] for e in entries}) == 3  # unique, deterministic ids
    assert entries[0]["geometry"] == "Polygon"
    assert entries[1]["geometry"] == "Line"
    assert entries[2]["geometry"] == "No geometry"
    assert all("|layername=" in e["datasource"] for e in entries)


def test_qgz_tree_projectlayers_and_order_consistent(tmp_path):
    qgz = write_layered_qgz(tmp_path / "p.qgz", epsg=32647, title="T", layers=_layers())
    with zipfile.ZipFile(qgz) as zf:
        root = ET.fromstring(zf.read(next(n for n in zf.namelist() if n.endswith(".qgs"))))

    assert root.find("projectCrs/spatialrefsys/authid") is not None
    assert root.findtext("projectCrs/spatialrefsys/authid") == "EPSG:32647"

    tree_ids = [n.get("id") for n in root.iter("layer-tree-layer")]
    maplayer_ids = [ml.findtext("id") for ml in root.iter("maplayer")]
    order_ids = [n.get("id") for n in root.find("layerorder").iter("layer")]  # type: ignore[union-attr]
    assert tree_ids == maplayer_ids == order_ids

    # visibility flag round-trips into the tree
    checked = {n.get("name"): n.get("checked") for n in root.iter("layer-tree-layer")}
    assert checked["pXRF_reading_table"] == "Qt::Unchecked"
    assert checked["faults_structures_line"] == "Qt::Checked"

    # symbology embedded for the styled layers only
    renderers = [ml.find("renderer-v2") for ml in root.iter("maplayer")]
    assert renderers[0] is not None and renderers[1] is not None
    assert renderers[2] is None


def test_write_layered_qgz_is_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    a = write_layered_qgz(first / "project.qgz", epsg=32647, title="T", layers=_layers())
    b = write_layered_qgz(second / "project.qgz", epsg=32647, title="T", layers=_layers())
    with zipfile.ZipFile(a) as za, zipfile.ZipFile(b) as zb:
        xa = za.read(next(n for n in za.namelist() if n.endswith(".qgs")))
        xb = zb.read(next(n for n in zb.namelist() if n.endswith(".qgs")))
    assert xa == xb
    assert a.read_bytes() == b.read_bytes()
