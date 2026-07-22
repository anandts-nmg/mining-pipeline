"""Vector I/O helpers: KMZ/KML boundary import and Master GeoPackage schema.

Kept out of ``crs.py`` so the heavy fiona/geopandas imports stay lazy and local to
the vector code paths.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal

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


@dataclass(frozen=True)
class PointIngestResult:
    """Point-table data plus the exact coordinate handling applied during ingest."""

    gdf: Any
    x_column: Any
    y_column: Any
    coordinate_mode: Literal["geographic", "projected"]
    source_epsg: int
    target_epsg: int
    reprojection_applied: bool
    input_row_count: int
    accepted_row_count: int
    rejected_row_count: int

    @property
    def crs_description(self) -> str:
        action = (
            f"reprojected to EPSG:{self.target_epsg}"
            if self.reprojection_applied
            else "no reprojection"
        )
        return (
            f"{self.coordinate_mode} coordinates; configured source CRS "
            f"EPSG:{self.source_epsg}; {action}"
        )


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


def make_grid(aoi_gdf, cell_m: float, epsg: int):  # type: ignore[no-untyped-def]
    """Build a square fishnet of ``cell_m``-sided cells over ``aoi_gdf``'s extent, keeping only
    cells that intersect the (dissolved) AOI. Returns a GeoDataFrame with a ``grid_id`` column
    in ``EPSG:<epsg>`` (used by Phase 04's evidence-scoring grid).
    """
    import math

    import geopandas as gpd
    from shapely.geometry import box

    merged = (
        aoi_gdf.geometry.union_all()
        if hasattr(aoi_gdf.geometry, "union_all")
        else aoi_gdf.geometry.unary_union
    )
    minx, miny, maxx, maxy = merged.bounds
    nx = max(1, math.ceil((maxx - minx) / cell_m))
    ny = max(1, math.ceil((maxy - miny) / cell_m))
    cells = []
    gid = 0
    for i in range(nx):
        x0 = minx + i * cell_m
        for j in range(ny):
            y0 = miny + j * cell_m
            cell = box(x0, y0, x0 + cell_m, y0 + cell_m)
            if cell.intersects(merged):
                cells.append({"grid_id": f"G{gid:05d}", "geometry": cell})
                gid += 1
    return gpd.GeoDataFrame(cells, geometry="geometry", crs=f"EPSG:{epsg}")


def dissolve_adjacent(gdf):  # type: ignore[no-untyped-def]
    """Merge touching/overlapping geometries into contiguous clusters. Unions everything, then
    explodes into one row per connected part with a ``cluster_id`` column, in the input CRS.
    Returns an empty copy unchanged.
    """
    import geopandas as gpd

    if gdf is None or len(gdf) == 0:
        return gdf.copy() if gdf is not None else gdf
    merged = (
        gdf.geometry.union_all() if hasattr(gdf.geometry, "union_all") else gdf.geometry.unary_union
    )
    parts = gpd.GeoSeries([merged], crs=gdf.crs).explode(index_parts=False).reset_index(drop=True)
    return gpd.GeoDataFrame(
        {"cluster_id": list(range(len(parts))), "geometry": list(parts)},
        geometry="geometry",
        crs=gdf.crs,
    )


def nearest_distance(gdf, target_gdf):  # type: ignore[no-untyped-def]
    """Elementwise distance (metres, in ``gdf``'s CRS) from each geometry in ``gdf`` to the
    nearest geometry in ``target_gdf`` (dissolved to one geometry). Returns a pandas Series
    aligned to ``gdf.index``; an empty/None target yields all-NaN.
    """
    import pandas as pd

    if target_gdf is None or len(target_gdf) == 0:
        return pd.Series([float("nan")] * len(gdf), index=gdf.index)
    merged = (
        target_gdf.geometry.union_all()
        if hasattr(target_gdf.geometry, "union_all")
        else target_gdf.geometry.unary_union
    )
    return gdf.geometry.distance(merged)


# Degrees-minutes-seconds like 96°41'16" or 45°59'26.8"N (seconds/hemisphere optional).
_DMS_RE = re.compile(
    r"(?P<deg>-?\d+(?:\.\d+)?)\s*[°ºd]\s*"
    r"(?:(?P<min>\d+(?:\.\d+)?)\s*['′m]\s*)?"
    r"(?:(?P<sec>\d+(?:\.\d+)?)\s*[\"″s]?\s*)?"
    r"(?P<hemi>[NSEWnsew])?"
)


def _to_decimal_degrees(value):  # type: ignore[no-untyped-def]
    """Coerce a coordinate cell to a float. Numeric values pass through; a DMS string such
    as ``96°41'16"`` (e.g. a Mongolian register's Уртраг/Өргөрөг columns) is parsed to decimal
    degrees, honouring a leading sign or an N/S/E/W hemisphere. Returns ``None`` when unparseable.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    m = _DMS_RE.search(str(value).strip())
    if not m or not m.group("deg"):
        return None
    deg = float(m.group("deg"))
    dd = abs(deg) + float(m.group("min") or 0) / 60 + float(m.group("sec") or 0) / 3600
    negative = deg < 0 or (m.group("hemi") or "").upper() in ("S", "W")
    return -dd if negative else dd


def xlsx_points_with_provenance(
    path: Path,
    source_epsg: int = 4326,
    target_epsg: int = 32647,
    *,
    projected_epsg: int | None = None,
) -> PointIngestResult | None:
    """Read an XLSX point table and retain truthful coordinate-ingest provenance.

    Detects lon/lat / x/y / easting-northing column pairs case-insensitively — including the
    Mongolian register headers Уртраг (lon) / Өргөрөг (lat) — and parses DMS strings like
    ``96°41'16"`` to decimal degrees. Coordinate magnitude distinguishes geographic from projected
    values, but it never establishes a projected CRS: callers must provide ``projected_epsg`` for
    metre-scale coordinates. Mixed geographic/projected rows fail closed. Returns ``None`` when the
    workbook is unreadable, empty, or has no detectable coordinate column pair.
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
    x_keys = ("lon", "long", "longitude", "x", "easting", "east", "уртраг")
    y_keys = ("lat", "latitude", "y", "northing", "north", "өргөрөг")
    x_col = next((lower[k] for k in x_keys if k in lower), None)
    y_col = next((lower[k] for k in y_keys if k in lower), None)
    if x_col is None or y_col is None:
        return None

    # Coerce to numbers, parsing DMS strings (e.g. 96°41'16") to decimal degrees, then drop bad rows.
    coords = pd.DataFrame(
        {"x": df[x_col].map(_to_decimal_degrees), "y": df[y_col].map(_to_decimal_degrees)}
    ).dropna()
    if coords.empty:
        return None
    geographic_rows = (coords["x"].abs() <= 180) & (coords["y"].abs() <= 90)
    if geographic_rows.any() and not geographic_rows.all():
        raise ValueError("point table mixes geographic and projected coordinate magnitudes")

    geographic = bool(geographic_rows.all())
    if geographic:
        coordinate_mode: Literal["geographic", "projected"] = "geographic"
        detected_epsg = source_epsg
    else:
        coordinate_mode = "projected"
        if projected_epsg is None:
            raise ValueError("projected point coordinates require an explicit projected_epsg")
        detected_epsg = projected_epsg

    attrs = df.loc[coords.index].reset_index(drop=True)
    gdf = gpd.GeoDataFrame(
        attrs,
        geometry=gpd.points_from_xy(
            coords["x"].reset_index(drop=True), coords["y"].reset_index(drop=True)
        ),
        crs=f"EPSG:{detected_epsg}",
    )
    reprojection_applied = detected_epsg != target_epsg
    if reprojection_applied:
        gdf = gdf.to_crs(epsg=target_epsg)
    return PointIngestResult(
        gdf=gdf,
        x_column=x_col,
        y_column=y_col,
        coordinate_mode=coordinate_mode,
        source_epsg=detected_epsg,
        target_epsg=target_epsg,
        reprojection_applied=reprojection_applied,
        input_row_count=len(df),
        accepted_row_count=len(coords),
        rejected_row_count=len(df) - len(coords),
    )


def xlsx_points_to_gdf(
    path: Path,
    source_epsg: int = 4326,
    target_epsg: int = 32647,
    *,
    projected_epsg: int | None = None,
):  # type: ignore[no-untyped-def]
    """Return only the GeoDataFrame; projected coordinates still require explicit CRS input."""

    result = xlsx_points_with_provenance(
        path,
        source_epsg=source_epsg,
        target_epsg=target_epsg,
        projected_epsg=projected_epsg,
    )
    return None if result is None else result.gdf


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
