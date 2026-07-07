"""DEM vector hydrology — contours, drainage network, watersheds (WhiteboxTools).

Closes the Doc A p.39 "Terrain_Derivatives (vector)" gap that was previously a method note:
fill depressions → D8 pointer/accumulation → stream raster (cell threshold) → vector streams,
basins → watershed polygons, plus vector contours. WhiteboxTools is the optional ``[dem]``
extra already declared in ``pyproject.toml``; callers must degrade gracefully (keep the
method note) when :func:`find_whitebox` returns ``None`` or :class:`HydrologyError` is raised.

Support evidence only — never ore proof (invariant #8).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class HydrologyError(RuntimeError):
    """Raised when the hydrology chain cannot run (whitebox missing/failed, bad DEM)."""


@dataclass(frozen=True)
class HydrologyParams:
    """Deterministic defaults; the stream threshold follows the DEM guide's 12.5 m row
    (500–2000 cells → 1000)."""

    contour_interval_m: float = 20.0
    stream_threshold_cells: int = 1000
    #: WBT ``Basins`` gives every edge-draining pixel cluster its own basin on a clipped DEM
    #: (~140k slivers on the 5 km clip); keep only hydrologically meaningful watersheds.
    min_basin_area_ha: float = 25.0


def find_whitebox():  # type: ignore[no-untyped-def]
    """A ready ``WhiteboxTools`` instance, or ``None`` when unavailable.

    ``whitebox`` is an optional dependency and downloads its binary on first use — any
    import/init failure means "not available" rather than an error.
    """
    try:
        import whitebox  # pyright: ignore[reportMissingImports]

        wbt = whitebox.WhiteboxTools()
        wbt.set_verbose_mode(False)
        return wbt
    except Exception:  # noqa: BLE001 - optional dependency, any failure -> unavailable
        return None


def build_hydrology(
    dem_path: Path,
    workdir: Path,
    *,
    wbt,  # type: ignore[no-untyped-def]
    params: HydrologyParams = HydrologyParams(),
):  # type: ignore[no-untyped-def]
    """Contour lines, stream lines and watershed polygons from a (clipped) DEM.

    Returns ``(contours_gdf, streams_gdf, basins_gdf)`` — GeoDataFrames in the DEM's CRS.
    WhiteboxTools writes intermediates (filled DEM, D8 pointer/accumulation, stream raster,
    basin raster, shapefiles) into ``workdir``; the caller writes the GPKG deliverables.
    """
    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.features import shapes as rio_shapes
    from shapely.geometry import shape as shp_shape

    dem_path = Path(dem_path).resolve()
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dem_path) as ds:
        crs = ds.crs

    filled = workdir / "dem_filled.tif"
    d8ptr = workdir / "d8_pointer.tif"
    facc = workdir / "flow_accum.tif"
    streams_r = workdir / "streams.tif"
    basins_r = workdir / "basins.tif"
    streams_shp = workdir / "streams.shp"
    contours_shp = workdir / "contours.shp"

    def _run(tool: str, ret: int, out: Path) -> None:
        if ret != 0 or not out.exists():
            raise HydrologyError(f"WhiteboxTools {tool} failed (ret={ret}, missing {out.name})")

    _run("FillDepressions", wbt.fill_depressions(str(dem_path), str(filled)), filled)
    _run("D8Pointer", wbt.d8_pointer(str(filled), str(d8ptr)), d8ptr)
    _run(
        "D8FlowAccumulation",
        wbt.d8_flow_accumulation(str(filled), str(facc), out_type="cells"),
        facc,
    )
    _run(
        "ExtractStreams",
        wbt.extract_streams(str(facc), str(streams_r), float(params.stream_threshold_cells)),
        streams_r,
    )
    _run(
        "RasterStreamsToVector",
        wbt.raster_streams_to_vector(str(streams_r), str(d8ptr), str(streams_shp)),
        streams_shp,
    )
    _run("Basins", wbt.basins(str(d8ptr), str(basins_r)), basins_r)
    _run(
        "ContoursFromRaster",
        wbt.contours_from_raster(
            str(filled), str(contours_shp), interval=params.contour_interval_m
        ),
        contours_shp,
    )

    # WBT shapefiles often lack a .prj — assign the DEM CRS explicitly.
    streams = gpd.read_file(streams_shp).set_crs(crs, allow_override=True)
    contours = gpd.read_file(contours_shp).set_crs(crs, allow_override=True)

    # basins raster -> polygons (drop the raster nodata region)
    with rasterio.open(basins_r) as ds:
        arr = ds.read(1)
        nodata = ds.nodata
        transform = ds.transform
    mask = np.isfinite(arr) if nodata is None else (arr != nodata) & np.isfinite(arr)
    records: list[dict[str, object]] = []
    geoms = []
    for geom, value in rio_shapes(arr.astype("float32"), mask=mask, transform=transform):
        records.append({"basin_id": int(value)})
        geoms.append(shp_shape(geom))
    basins = gpd.GeoDataFrame(records, geometry=geoms, crs=crs)
    # dissolve pixel-polygons of the same basin into single watershed polygons, then drop the
    # edge-draining slivers (see HydrologyParams.min_basin_area_ha)
    if len(basins):
        basins = basins.dissolve(by="basin_id", as_index=False)
        basins["area_ha"] = (basins.geometry.area / 10_000.0).round(2)
        basins = basins[basins["area_ha"] >= params.min_basin_area_ha].reset_index(drop=True)

    return contours, streams, basins
