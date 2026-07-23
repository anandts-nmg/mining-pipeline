"""Clip-to-AOI and Cloud-Optimized-GeoTIFF writers for Phase 02 deliverables.

Kept out of ``crs.py`` so the heavy rasterio import stays lazy and the CRS module
stays focused on audit/transform. Phase 02 routes every raster through
clip -> reproject -> COG; these are the clip and COG-write primitives.

The COG driver (verified available: rasterio 1.5 / GDAL 3.12) writes internal tiling,
internal overviews and compression in one ``rasterio.shutil.copy`` step.
"""

from __future__ import annotations

from pathlib import Path

#: COG internal tile/block size in pixels. A raster smaller than this legitimately
#: has *no* internal overviews yet is still a valid COG - :func:`is_cog` accounts for that.
COG_BLOCKSIZE = 512


def clip_to_aoi_raster(src: Path, dst: Path, aoi_geom_native, *, nodata=None) -> Path | None:
    """Clip a raster to ``aoi_geom_native`` (a shapely geometry **already in the
    raster's CRS**), writing a plain GeoTIFF. Preserves dtype/band-count/nodata.

    Returns the destination path, or ``None`` if the AOI does not overlap the raster
    (``rasterio.mask`` raises ``ValueError`` for a disjoint geometry when ``crop=True``).
    """
    import rasterio
    from rasterio.mask import mask as rio_mask
    from shapely.geometry import mapping

    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src) as ds:
        nd = nodata if nodata is not None else ds.nodata
        try:
            data, transform = rio_mask(ds, [mapping(aoi_geom_native)], crop=True, nodata=nd)
        except ValueError:
            return None  # "Input shapes do not overlap raster"
        profile = ds.profile.copy()
        profile.update(
            height=data.shape[1], width=data.shape[2], transform=transform, driver="GTiff"
        )
        if nd is not None:
            profile.update(nodata=nd)
        with rasterio.open(dst, "w", **profile) as out:
            out.write(data)
    return dst


def write_cog(
    src: Path,
    dst: Path,
    *,
    compress: str,
    predictor: str | None = None,
    overview_resampling: str = "NEAREST",
    blocksize: int = COG_BLOCKSIZE,
) -> Path:
    """Convert a GeoTIFF to a Cloud-Optimized GeoTIFF (tiled + internal overviews +
    compression). ``predictor`` is passed to GDAL as a string ('2' int, '3' float)."""
    import rasterio.shutil as rio_shutil  # ty: ignore[unresolved-import]

    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    opts: dict[str, str] = {
        "driver": "COG",
        "BLOCKSIZE": str(blocksize),
        "COMPRESS": compress,
        "OVERVIEW_RESAMPLING": overview_resampling,
    }
    if predictor is not None:
        opts["PREDICTOR"] = str(predictor)
    rio_shutil.copy(src, dst, **opts)
    return dst


def is_cog(path: Path, *, blocksize: int = COG_BLOCKSIZE) -> bool:
    """True if ``path`` is a valid COG: COG layout + internal tiling.

    Validity is the COG layout marker; internal overviews are required **only** when the
    raster is larger than one block (a sub-blocksize image is a valid COG with no overviews,
    so small clipped rasters and tiny test fixtures don't false-fail).
    """
    import rasterio

    with rasterio.open(Path(path)) as ds:
        if ds.tags(ns="IMAGE_STRUCTURE").get("LAYOUT", "") != "COG":
            return False
        if min(ds.width, ds.height) > blocksize and not ds.overviews(1):
            return False
    return True


def predictor_for(dtype: str | None) -> str | None:
    """GDAL PREDICTOR for a dtype: '3' for float, '2' for multi-byte int, None for byte."""
    if not dtype:
        return None
    d = dtype.lower()
    if d.startswith("float"):
        return "3"
    if d in ("uint8", "int8", "byte"):
        return None
    if d.startswith(("int", "uint")):
        return "2"
    return None


def subset_cog_bands(path: Path, keep: list[int]) -> Path:
    """Rewrite a COG in place keeping only the 1-based bands in ``keep`` (CRS/geotransform preserved).

    For received composites that bundle more bands than the deliverable should expose — e.g. a
    Sentinel-2 "lithology index" stack that ships raw-reflectance bands alongside the named ratio
    bands. Compression/predictor are chosen from the dtype, matching the other COG writers.
    """
    import tempfile

    import rasterio

    path = Path(path)
    with rasterio.open(path) as ds:
        profile = ds.profile.copy()
        dtype = ds.dtypes[0]
        data = [ds.read(i) for i in keep]
    profile.update(count=len(keep), driver="GTiff")
    with tempfile.TemporaryDirectory() as tmp:
        plain = Path(tmp) / "subset.tif"
        with rasterio.open(plain, "w", **profile) as out:
            for j, arr in enumerate(data, start=1):
                out.write(arr, j)
        write_cog(plain, path, compress="DEFLATE", predictor=predictor_for(dtype))
    return path
