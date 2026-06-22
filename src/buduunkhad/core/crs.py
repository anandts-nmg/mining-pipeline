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
                needs_reproject=(epsg != target_epsg),
            )
    except Exception as exc:  # noqa: BLE001 - report, don't crash the audit
        return RasterAudit(path=str(path), readable=False, error=f"{type(exc).__name__}: {exc}")


def reproject_raster(src: Path, dst: Path, dst_epsg: int = TARGET_EPSG) -> Path:
    """Reproject a raster to ``dst_epsg`` (default EPSG:32647), writing GeoTIFF."""
    import rasterio
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst_crs = f"EPSG:{dst_epsg}"
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
                    resampling=Resampling.bilinear,
                )
    return dst


def reproject_gdf(gdf, dst_epsg: int = TARGET_EPSG):  # type: ignore[no-untyped-def]
    """Reproject a GeoDataFrame to ``dst_epsg``; returns the reprojected frame.

    Raises if the source frame has no CRS (we never guess).
    """
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS; cannot reproject without a source CRS.")
    return gdf.to_crs(epsg=dst_epsg)
