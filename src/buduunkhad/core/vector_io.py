"""Vector I/O helpers: KMZ/KML boundary import and Master GeoPackage schema.

Kept out of ``crs.py`` so the heavy fiona/geopandas imports stay lazy and local to
the vector code paths.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from buduunkhad.config import GpkgLayer

_FIONA_GEOM = {
    "Polygon": "Polygon",
    "MultiPolygon": "MultiPolygon",
    "LineString": "LineString",
    "MultiLineString": "MultiLineString",
    "Point": "Point",
    "MultiPoint": "MultiPoint",
}

# Minimal generic attribute schema for the (empty) master GIS layers.
_LAYER_PROPS: dict[str, str] = {
    "id": "int",
    "name": "str:254",
    "source_input": "str:254",
    "confidence": "str:32",
    "notes": "str:254",
}

# Attribute-only schema for the pXRF reading table.
_PXRF_PROPS: dict[str, str] = {
    "reading_id": "int",
    "sample_id": "str:64",
    "instrument": "str:64",
    "element": "str:16",
    "value_ppm": "float",
    "unit": "str:16",
    "datetime": "str:32",
    "operator": "str:64",
    "notes": "str:254",
}


def _enable_kml_drivers() -> None:
    from typing import cast

    from fiona.drvsupport import supported_drivers

    # fiona's typed stub constrains the keys to a fixed Literal set of driver names
    # that omits KML/LIBKML (both valid at runtime), so treat it as a plain mapping.
    drivers = cast(dict[str, str], supported_drivers)
    for drv in ("KML", "LIBKML"):
        drivers[drv] = "rw"


def read_boundary(path: Path, assume_epsg: int = 4326):  # type: ignore[no-untyped-def]
    """Read a KMZ/KML (or any OGR-readable) boundary into a GeoDataFrame.

    KMZ is unzipped to a temp dir and the contained KML is read. KML carries no
    CRS, so we assume ``assume_epsg`` (WGS84) when none is present. Returns a
    GeoDataFrame with a defined CRS.
    """
    _enable_kml_drivers()
    path = Path(path)

    if path.suffix.lower() == ".kmz":
        with TemporaryDirectory() as tmp, zipfile.ZipFile(path) as zf:
            kmls = [n for n in zf.namelist() if n.lower().endswith(".kml")]
            if not kmls:
                raise ValueError(f"No .kml found inside KMZ: {path}")
            # Prefer doc.kml if present.
            target = next((n for n in kmls if n.lower().endswith("doc.kml")), kmls[0])
            zf.extract(target, tmp)
            gdf = _read_vector(Path(tmp) / target)
    else:
        gdf = _read_vector(path)

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=assume_epsg)
    return gdf


def _read_vector(path: Path):  # type: ignore[no-untyped-def]
    import geopandas as gpd

    try:
        return gpd.read_file(path, engine="fiona")
    except Exception:
        return gpd.read_file(path)


def create_master_gpkg(path: Path, layers: list[GpkgLayer], epsg: int) -> Path:
    """Create a GeoPackage with empty, typed layers (spatial + aspatial) in ``epsg``.

    Spatial layers get the generic attribute schema and the layer's geometry type;
    aspatial layers (``geometry == 'None'``) get a tabular schema.
    """
    import fiona
    from pyproj import CRS as PyCRS

    path = Path(path)
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)

    crs_wkt = PyCRS.from_epsg(epsg).to_wkt()
    # Each layer is created with mode "w": on a multi-layer driver (GPKG) fiona
    # adds the layer to the existing datasource rather than truncating it. (Append
    # mode "a" only works on an existing layer, so it cannot create new ones here.)
    for layer in layers:
        if layer.is_spatial:
            schema = {"geometry": _FIONA_GEOM[layer.geometry], "properties": dict(_LAYER_PROPS)}
            with fiona.open(
                path, "w", driver="GPKG", layer=layer.name, schema=schema, crs_wkt=crs_wkt
            ):
                pass
        else:
            schema = {"geometry": "None", "properties": dict(_PXRF_PROPS)}
            with fiona.open(path, "w", driver="GPKG", layer=layer.name, schema=schema):
                pass
    return path


def create_evidence_gpkg(
    path: Path,
    layers: list[tuple[str, str]],
    props: dict[str, str],
    epsg: int,
) -> Path:
    """Create a GeoPackage of empty, typed spatial layers sharing one property schema.

    ``layers`` is a list of ``(layer_name, geometry_type)`` where geometry_type is one
    of the keys in :data:`_FIONA_GEOM` (``Point`` / ``LineString`` / ``Polygon`` / their
    Multi- variants). Every layer carries the same ``props`` attribute schema (used for
    Phase 03's 17-layer evidence package: the 13 provenance fields + ``feature_id`` = 14 columns).
    """
    import fiona
    from pyproj import CRS as PyCRS

    path = Path(path)
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)

    crs_wkt = PyCRS.from_epsg(epsg).to_wkt()
    for name, geometry in layers:
        schema = {"geometry": _FIONA_GEOM[geometry], "properties": dict(props)}
        with fiona.open(path, "w", driver="GPKG", layer=name, schema=schema, crs_wkt=crs_wkt):
            pass
    return path


def buffer_rings(boundary_gdf, distances_m: list[int], epsg: int):  # type: ignore[no-untyped-def]
    """Build a multi-ring buffer GeoDataFrame off ``boundary_gdf``.

    Returns a GeoDataFrame with one row per distance (ascending), a ``distance_m``
    column and the buffered geometry, in ``EPSG:<epsg>``. The boundary geometry is
    dissolved first so overlapping parts produce a single ring per distance.
    """
    import geopandas as gpd

    merged = (
        boundary_gdf.geometry.union_all()
        if hasattr(boundary_gdf.geometry, "union_all")
        else boundary_gdf.geometry.unary_union
    )
    rings = [{"distance_m": dist, "geometry": merged.buffer(dist)} for dist in sorted(distances_m)]
    return gpd.GeoDataFrame(rings, crs=f"EPSG:{epsg}")


def xlsx_points_to_gdf(path: Path, source_epsg: int = 4326, target_epsg: int = 32647):  # type: ignore[no-untyped-def]
    """Read an XLSX point table, detect coordinate columns, build a reprojected GeoDataFrame.

    Detects lon/lat / x/y / easting-northing column pairs case-insensitively, then classifies
    by coordinate MAGNITUDE (not label): |x|<=180 and |y|<=90 are geographic (``source_epsg``,
    WGS84) and reprojected to ``target_epsg``; metre-scale magnitudes are taken as already in
    ``target_epsg`` (so a UTM easting/northing table is never mis-reprojected to (inf, inf)).
    Returns ``None`` gracefully — never raises — when the workbook is unreadable, empty, or has
    no detectable coordinate column pair (e.g. a synthetic placeholder); the caller notes + skips.
    """
    try:
        import geopandas as gpd
        import pandas as pd
    except Exception:
        return None

    path = Path(path)
    if not path.exists():
        return None
    try:
        df = pd.read_excel(path)
    except Exception:
        return None
    if df is None or df.empty:
        return None

    lower = {str(c).strip().lower(): c for c in df.columns}
    x_col = next(
        (lower[k] for k in ("lon", "long", "longitude", "x", "easting", "east") if k in lower), None
    )
    y_col = next(
        (lower[k] for k in ("lat", "latitude", "y", "northing", "north") if k in lower), None
    )
    if x_col is None or y_col is None:
        return None

    coords = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if coords.empty:
        return None
    # Trust the coordinate MAGNITUDE, not the column label: degrees (|x|<=180, |y|<=90)
    # are geographic (source_epsg / WGS84); metre-scale magnitudes are projected and taken
    # to be already in target_epsg. This stops a UTM easting/northing table being mislabeled
    # as lon/lat and reprojected to (inf, inf).
    geographic = coords[x_col].abs().max() <= 180 and coords[y_col].abs().max() <= 90
    detected_epsg = source_epsg if geographic else target_epsg
    attrs = df.loc[coords.index].reset_index(drop=True)
    gdf = gpd.GeoDataFrame(
        attrs,
        geometry=gpd.points_from_xy(
            coords[x_col].reset_index(drop=True), coords[y_col].reset_index(drop=True)
        ),
        crs=f"EPSG:{detected_epsg}",
    )
    if detected_epsg != target_epsg:
        gdf = gdf.to_crs(epsg=target_epsg)
    return gdf


def list_gpkg_layers(path: Path) -> list[str]:
    """Return the layer names present in a GeoPackage."""
    import fiona

    return list(fiona.listlayers(str(path)))


def read_layer(path: Path, layer: str):  # type: ignore[no-untyped-def]
    """Read one layer of a GeoPackage into a GeoDataFrame (used to load Phase 1 AOIs)."""
    import geopandas as gpd

    return gpd.read_file(Path(path), layer=layer)


def write_layer(gdf, path: Path, layer: str, mode: str = "w") -> Path:  # type: ignore[no-untyped-def]
    """Write (``mode='w'``) or append (``mode='a'``) a GeoDataFrame as a GPKG layer.

    Appending targets an existing layer and leaves the rest of the GeoPackage's
    layers intact - used to populate a layer created empty in the master schema.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, layer=layer, driver="GPKG", mode=mode)
    return path
