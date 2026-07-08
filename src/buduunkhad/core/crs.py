"""CRS audit and reprojection to the standard deliverable CRS (EPSG:32647).

Invariant #4: all deliverables are EPSG:32647, but the native/source CRS is always
recorded, never silently dropped.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

TARGET_EPSG = 32647


@dataclass(frozen=True)
class RasterAudit:
    """Result of auditing a single raster file."""

    path: str
    readable: bool
    driver: str | None = None
    crs: str | None = None
    epsg: int | None = None
    width: int | None = None
    height: int | None = None
    band_count: int | None = None
    dtype: str | None = None
    nodata: float | None = None
    res_x: float | None = None
    res_y: float | None = None
    bounds: tuple[float, float, float, float] | None = None
    #: grid is axis-aligned / north-up (no rotation/shear terms in the transform) - the
    #: deterministic "pixel alignment" check the methodology Phase-1 raster audit requires
    pixel_aligned: bool | None = None
    needs_reproject: bool | None = None
    error: str | None = None

    def as_row(self) -> dict[str, object]:
        return asdict(self)


def audit_raster(path: Path, target_epsg: int = TARGET_EPSG) -> RasterAudit:
    """Audit a raster's CRS / resolution / extent / nodata / band count.

    Never raises on a bad/unreadable raster - failures are captured in the
    returned :class:`RasterAudit` so a whole-archive audit can continue.
    """
    import rasterio  # imported lazily so non-raster code paths don't need GDAL

    path = Path(path)
    try:
        with rasterio.open(path) as ds:
            crs = ds.crs
            epsg = crs.to_epsg() if crs else None
            res_x, res_y = ds.res
            b = ds.bounds
            return RasterAudit(
                path=str(path),
                readable=True,
                driver=ds.driver,
                crs=crs.to_wkt() if crs else None,
                epsg=epsg,
                width=ds.width,
                height=ds.height,
                band_count=ds.count,
                dtype=ds.dtypes[0] if ds.dtypes else None,
                nodata=ds.nodata,
                res_x=res_x,
                res_y=res_y,
                bounds=(b.left, b.bottom, b.right, b.top),
                pixel_aligned=(ds.transform.b == 0.0 and ds.transform.d == 0.0),
                needs_reproject=(epsg != target_epsg),
            )
    except Exception as exc:  # noqa: BLE001 - report, don't crash the audit
        return RasterAudit(path=str(path), readable=False, error=f"{type(exc).__name__}: {exc}")


def reproject_raster(
    src: Path, dst: Path, dst_epsg: int = TARGET_EPSG, *, resampling: str = "bilinear"
) -> Path:
    """Reproject a raster to ``dst_epsg`` (default EPSG:32647), writing GeoTIFF.

    ``resampling`` is a :class:`rasterio.warp.Resampling` name ('bilinear' for
    continuous data, 'nearest' for categorical/classified rasters).
    """
    import rasterio
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst_crs = f"EPSG:{dst_epsg}"
    rs = Resampling[resampling]
    with rasterio.open(src) as ds:
        transform, width, height = calculate_default_transform(
            ds.crs, dst_crs, ds.width, ds.height, *ds.bounds
        )
        profile = ds.profile.copy()
        profile.update(crs=dst_crs, transform=transform, width=width, height=height, driver="GTiff")
        with rasterio.open(dst, "w", **profile) as out:
            for i in range(1, ds.count + 1):
                reproject(
                    source=rasterio.band(ds, i),
                    destination=rasterio.band(out, i),
                    src_transform=ds.transform,
                    src_crs=ds.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    src_nodata=ds.nodata,
                    dst_nodata=ds.nodata,
                    resampling=rs,
                )
    return dst


def reproject_clip_cog(
    src: Path,
    dst: Path,
    aoi_gdf=None,  # type: ignore[no-untyped-def]
    *,
    dst_epsg: int = TARGET_EPSG,
    cog_compress: str = "DEFLATE",
    cog_predictor: str | None = None,
    cog_overview_resampling: str = "NEAREST",
    resampling: str = "bilinear",
    nodata_fallback: float | None = None,
) -> tuple[Path | None, bool]:
    """Clip ``src`` to ``aoi_gdf`` (in the source CRS), reproject to ``dst_epsg``, write a COG.

    ``aoi_gdf`` is a GeoDataFrame clip boundary in any CRS; it is reprojected to the
    source raster's native CRS so the clip happens before reprojection (avoids double
    interpolation). Pass ``aoi_gdf=None`` to reproject + COG with no clip.

    Returns ``(dst, clip_applied)``; returns ``(None, False)`` when the AOI does not
    overlap the raster (the caller records a Skip rather than failing the gate).
    """
    import tempfile

    import rasterio

    from buduunkhad.core import raster_writers

    src = Path(src)
    dst = Path(dst)
    with rasterio.open(src) as ds:
        src_crs = ds.crs
        src_epsg = src_crs.to_epsg() if src_crs else None
        nodata = ds.nodata
    if nodata is None:
        nodata = nodata_fallback

    # geopandas.to_crs wants an EPSG/WKT, not a rasterio CRS object
    clip_crs = src_epsg if src_epsg is not None else (src_crs.to_wkt() if src_crs else None)

    with tempfile.TemporaryDirectory() as tmp:
        to_cog = src
        clip_applied = False
        if aoi_gdf is not None:
            aoi_src = aoi_gdf.to_crs(clip_crs) if clip_crs is not None else aoi_gdf
            geom = (
                aoi_src.geometry.union_all()
                if hasattr(aoi_src.geometry, "union_all")
                else aoi_src.geometry.unary_union
            )
            clipped = Path(tmp) / "clip.tif"
            if raster_writers.clip_to_aoi_raster(src, clipped, geom, nodata=nodata) is None:
                return None, False
            to_cog = clipped
            clip_applied = True

        if src_epsg != dst_epsg:
            reproj = Path(tmp) / "reproj.tif"
            reproject_raster(to_cog, reproj, dst_epsg=dst_epsg, resampling=resampling)
            to_cog = reproj

        raster_writers.write_cog(
            to_cog,
            dst,
            compress=cog_compress,
            predictor=cog_predictor,
            overview_resampling=cog_overview_resampling,
        )
    return dst, clip_applied


def reproject_gdf(gdf, dst_epsg: int = TARGET_EPSG):  # type: ignore[no-untyped-def]
    """Reproject a GeoDataFrame to ``dst_epsg``; returns the reprojected frame.

    Raises if the source frame has no CRS (we never guess).
    """
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS; cannot reproject without a source CRS.")
    return gdf.to_crs(epsg=dst_epsg)
