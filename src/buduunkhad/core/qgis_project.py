"""Deterministic layered QGIS project (.qgz) generation — no PyQGIS required.

A .qgz is a zip archive holding a .qgs project XML. QGIS re-reads every layer from
its datasource on open, so a project file only needs: the project CRS, one
``<maplayer>`` entry per layer (OGR datasource + layer name), a matching
``<layer-tree-layer>`` in the layer tree (top-to-bottom render order), and an
optional embedded renderer for deterministic symbology. Datasource paths are
written *relative to the project file* so the whole output tree stays portable
(local folder, Drive copy, another machine).

This is Tier-1 deterministic work per the methodology: the master doc (§01) and the
Phase-2 basemap guide both deliver *layered* .qgz projects. Symbology defaults here
are a machine draft — cartographic refinement stays with the geologist.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

#: config geometry vocab -> QGIS maplayer ``geometry`` attribute
GEOMETRY_ATTR = {
    "Point": "Point",
    "LineString": "Line",
    "MultiLineString": "Line",
    "Polygon": "Polygon",
    "MultiPolygon": "Polygon",
    "None": "No geometry",
}


@dataclass(frozen=True)
class QgzLayer:
    """One vector layer entry in the generated project.

    ``source`` is the OGR datasource string relative to the .qgz location, e.g.
    ``../06_Master_GeoPackage_Schema/Master.gpkg|layername=license_boundary``.
    ``geometry`` uses the config vocabulary (keys of :data:`GEOMETRY_ATTR`).
    ``symbol`` is an optional ("fill"|"line", properties) pair for a deterministic
    single-symbol renderer; layers without one get QGIS defaults on open.
    """

    name: str
    source: str
    geometry: str
    symbol: tuple[str, dict[str, str]] | None = None
    visible: bool = True


def polygon_outline(color_rgba: str, width_mm: float, *, dash: bool = False):
    """A no-fill polygon outline symbol spec (color as 'r,g,b,a')."""
    return (
        "fill",
        {
            "color": "255,255,255,0",
            "style": "no",
            "outline_color": color_rgba,
            "outline_style": "dash" if dash else "solid",
            "outline_width": str(width_mm),
            "outline_width_unit": "MM",
            "joinstyle": "bevel",
        },
    )


def line_symbol(color_rgba: str, width_mm: float, *, dash: bool = False):
    """A simple line symbol spec (color as 'r,g,b,a')."""
    return (
        "line",
        {
            "line_color": color_rgba,
            "line_style": "dash" if dash else "solid",
            "line_width": str(width_mm),
            "line_width_unit": "MM",
            "joinstyle": "bevel",
            "capstyle": "square",
        },
    )


def _layer_id(name: str) -> str:
    """Deterministic QGIS layer id (uuid-free so re-runs produce identical XML)."""
    return f"{name}_buduunkhad"


def _srs_element(epsg: int) -> ET.Element:
    """Full spatialrefsys block - QGIS needs the WKT/proj4 definition to reconstruct
    the CRS on load (authid alone reads back as an invalid/empty CRS)."""
    from pyproj import CRS as PyCRS

    crs = PyCRS.from_epsg(epsg)
    srs = ET.Element("spatialrefsys", {"nativeFormat": "Wkt"})
    ET.SubElement(srs, "wkt").text = crs.to_wkt()
    ET.SubElement(srs, "proj4").text = crs.to_proj4()
    ET.SubElement(srs, "srid").text = str(epsg)
    ET.SubElement(srs, "authid").text = f"EPSG:{epsg}"
    ET.SubElement(srs, "description").text = crs.name
    ET.SubElement(srs, "geographicflag").text = "true" if crs.is_geographic else "false"
    return srs


def _renderer_element(symbol: tuple[str, dict[str, str]]) -> ET.Element:
    sym_type, props = symbol
    renderer = ET.Element(
        "renderer-v2",
        {"type": "singleSymbol", "forceraster": "0", "symbollevels": "0", "enableorderby": "0"},
    )
    symbols = ET.SubElement(renderer, "symbols")
    sym = ET.SubElement(
        symbols,
        "symbol",
        {"type": sym_type, "name": "0", "alpha": "1", "clip_to_extent": "1", "force_rhr": "0"},
    )
    cls = "SimpleFill" if sym_type == "fill" else "SimpleLine"
    layer = ET.SubElement(sym, "layer", {"class": cls, "enabled": "1", "locked": "0", "pass": "0"})
    for k, v in sorted(props.items()):
        ET.SubElement(layer, "prop", {"k": k, "v": v})
    ET.SubElement(renderer, "rotation")
    ET.SubElement(renderer, "sizescale")
    return renderer


def write_layered_qgz(
    path: Path,
    *,
    epsg: int,
    title: str,
    layers: list[QgzLayer],
    qgis_version: str = "3.34.0",
) -> Path:
    """Write a .qgz whose project contains ``layers`` top-to-bottom in tree order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    qgis = ET.Element("qgis", {"version": qgis_version, "projectname": title})
    ET.SubElement(qgis, "homePath", {"path": ""})
    ET.SubElement(qgis, "title").text = title
    project_crs = ET.SubElement(qgis, "projectCrs")
    project_crs.append(_srs_element(epsg))
    # QGIS only honours the <projectCrs> node when the legacy ProjectionsEnabled
    # property is set - without it the project opens with an unknown CRS.
    properties = ET.SubElement(qgis, "properties")
    spatial = ET.SubElement(properties, "SpatialRefSys")
    ET.SubElement(spatial, "ProjectionsEnabled", {"type": "int"}).text = "1"

    tree_group = ET.SubElement(qgis, "layer-tree-group")
    project_layers = ET.SubElement(qgis, "projectlayers")
    layer_order = ET.SubElement(qgis, "layerorder")

    for lyr in layers:
        geometry_attr = GEOMETRY_ATTR[lyr.geometry]
        lid = _layer_id(lyr.name)
        ET.SubElement(
            tree_group,
            "layer-tree-layer",
            {
                "name": lyr.name,
                "id": lid,
                "source": lyr.source,
                "providerKey": "ogr",
                "checked": "Qt::Checked" if lyr.visible else "Qt::Unchecked",
                "expanded": "1",
            },
        )
        maplayer = ET.SubElement(
            project_layers,
            "maplayer",
            {"type": "vector", "geometry": geometry_attr, "autoRefreshEnabled": "0"},
        )
        ET.SubElement(maplayer, "id").text = lid
        ET.SubElement(maplayer, "datasource").text = lyr.source
        ET.SubElement(maplayer, "layername").text = lyr.name
        srs = ET.SubElement(maplayer, "srs")
        srs.append(_srs_element(epsg))
        ET.SubElement(maplayer, "provider", {"encoding": "UTF-8"}).text = "ogr"
        if lyr.symbol is not None and geometry_attr != "No geometry":
            maplayer.append(_renderer_element(lyr.symbol))
        ET.SubElement(layer_order, "layer", {"id": lid})

    ET.indent(qgis)
    qgs_xml = ET.tostring(qgis, encoding="unicode", xml_declaration=True)
    if path.exists():
        path.unlink()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{path.stem}.qgs", qgs_xml)
    return path


def read_qgz_layers(path: Path) -> list[dict[str, str]]:
    """Parse a .qgz and return its maplayer entries (id / name / datasource / geometry).

    Used by tests and QA to verify tree/projectlayers consistency without QGIS.
    """
    path = Path(path)
    with zipfile.ZipFile(path) as zf:
        qgs_name = next(n for n in zf.namelist() if n.endswith(".qgs"))
        root = ET.fromstring(zf.read(qgs_name))
    out: list[dict[str, str]] = []
    for ml in root.iter("maplayer"):
        out.append(
            {
                "id": ml.findtext("id") or "",
                "name": ml.findtext("layername") or "",
                "datasource": ml.findtext("datasource") or "",
                "geometry": ml.get("geometry") or "",
            }
        )
    return out
