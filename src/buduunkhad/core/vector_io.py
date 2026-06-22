"""Vector I/O helpers: KMZ/KML boundary import and Master GeoPackage schema.

Kept out of ``crs.py`` so the heavy fiona/geopandas imports stay lazy and local to
the vector code paths.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from buduunkhad.config import GpkgLayer

_FIONA_GEOM = {"Polygon": "Polygon", "LineString": "LineString", "Point": "Point"}

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
    import fiona

    for drv in ("KML", "LIBKML"):
        fiona.drvsupport.supported_drivers[drv] = "rw"


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


def list_gpkg_layers(path: Path) -> list[str]:
    """Return the layer names present in a GeoPackage."""
    import fiona

    return list(fiona.listlayers(str(path)))


def write_layer(gdf, path: Path, layer: str, mode: str = "w") -> Path:  # type: ignore[no-untyped-def]
    """Write (``mode='w'``) or append (``mode='a'``) a GeoDataFrame as a GPKG layer.

    Appending targets an existing layer and leaves the rest of the GeoPackage's
    layers intact - used to populate a layer created empty in the master schema.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, layer=layer, driver="GPKG", mode=mode)
    return path
