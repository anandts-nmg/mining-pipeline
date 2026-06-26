"""Unit tests for the Phase 02 clip + reproject + COG primitives (controlled fixtures)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from buduunkhad.core import crs as crs_mod
from buduunkhad.core import dem, raster_writers


def _raster(
    path: Path,
    *,
    epsg: int,
    size: int,
    res: float,
    origin: tuple[float, float],
    dtype: str = "float32",
    nodata: float = -9999.0,
) -> Path:
    data = np.fromfunction(lambda r, c: r + c, (size, size)).astype(dtype)
    profile = {
        "driver": "GTiff",
        "height": size,
        "width": size,
        "count": 1,
        "dtype": dtype,
        "crs": f"EPSG:{epsg}",
        "transform": from_origin(origin[0], origin[1], res, res),
        "nodata": nodata,
    }
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(data, 1)
    return path


def _aoi(bounds: tuple[float, float, float, float], epsg: int):
    import geopandas as gpd
    from shapely.geometry import box

    return gpd.GeoDataFrame({"id": [1]}, geometry=[box(*bounds)], crs=f"EPSG:{epsg}")


def test_predictor_for():
    assert raster_writers.predictor_for("float32") == "3"
    assert raster_writers.predictor_for("int16") == "2"
    assert raster_writers.predictor_for("uint16") == "2"
    assert raster_writers.predictor_for("uint8") is None
    assert raster_writers.predictor_for(None) is None


def test_reproject_clip_cog_clips_and_reprojects(tmp_path):
    # 4326 raster covering 96.40-96.60 E, 45.40-45.60 N
    src = _raster(tmp_path / "src.tif", epsg=4326, size=20, res=0.01, origin=(96.40, 45.60))
    aoi = _aoi((96.45, 45.45, 96.55, 45.55), 4326)  # interior box -> strict subset
    dst = tmp_path / "out.tif"

    out, clipped = crs_mod.reproject_clip_cog(
        src, dst, aoi, dst_epsg=32647, cog_compress="DEFLATE", cog_predictor="3"
    )
    assert out == dst and clipped is True
    assert raster_writers.is_cog(dst)
    with rasterio.open(src) as s, rasterio.open(dst) as d:
        assert d.crs.to_epsg() == 32647
        # clipped to the interior -> fewer pixels than the full source
        assert d.width * d.height < s.width * s.height


def test_reproject_clip_cog_no_overlap_returns_none(tmp_path):
    src = _raster(tmp_path / "src.tif", epsg=4326, size=20, res=0.01, origin=(96.40, 45.60))
    far = _aoi((10.0, 10.0, 10.1, 10.1), 4326)  # disjoint
    out, clipped = crs_mod.reproject_clip_cog(
        src, tmp_path / "out.tif", far, dst_epsg=32647, cog_compress="DEFLATE"
    )
    assert out is None and clipped is False


def test_cog_overviews_present_when_larger_than_blocksize(tmp_path):
    # > blocksize so the COG driver actually builds internal overviews
    n = raster_writers.COG_BLOCKSIZE + 200
    src = _raster(tmp_path / "big.tif", epsg=32647, size=n, res=30.0, origin=(300000.0, 5200000.0))
    aoi = _aoi((300000.0, 5200000.0 - n * 30, 300000.0 + n * 30, 5200000.0), 32647)
    out, clipped = crs_mod.reproject_clip_cog(
        src,
        tmp_path / "big_cog.tif",
        aoi,
        dst_epsg=32647,
        cog_compress="DEFLATE",
        cog_predictor="3",
        cog_overview_resampling="AVERAGE",
    )
    assert out is not None and clipped is True
    assert raster_writers.is_cog(out)
    with rasterio.open(out) as ds:
        assert ds.overviews(1), "expected internal overviews for a > blocksize raster"


def test_small_cog_is_valid_without_overviews(tmp_path):
    src = _raster(tmp_path / "s.tif", epsg=32647, size=16, res=30.0, origin=(300000.0, 5100000.0))
    dst = raster_writers.write_cog(src, tmp_path / "s_cog.tif", compress="DEFLATE", predictor="3")
    assert raster_writers.is_cog(dst)  # valid COG even with no overviews (< blocksize)


def test_derive_terrain_writes_cogs_and_reports_skips(tmp_path):
    dem_path = _raster(
        tmp_path / "dem.tif", epsg=32647, size=40, res=30.0, origin=(300000.0, 5100000.0)
    )
    outs = {
        k: tmp_path / f"{k}.tif"
        for k in (
            "hillshade",
            "hillshade_az045",
            "slope",
            "aspect",
            "tri",
            "profile_curvature",
            "plan_curvature",
            "flow",
        )
    }
    written, skipped = dem.derive_terrain(dem_path, outs)
    assert len(written) == len(outs)
    assert not skipped  # 40x40 is well under MAX_CELLS_FOR_FLOW
    for p in written:
        assert raster_writers.is_cog(p)
    with rasterio.open(outs["hillshade"]) as ds:
        assert ds.dtypes[0] == "uint8"  # rendered relief, no float predictor leakage
    with rasterio.open(outs["slope"]) as ds:
        assert ds.dtypes[0] == "float32"


def test_derive_terrain_flow_skip_is_noted(tmp_path, monkeypatch):
    monkeypatch.setattr(dem, "MAX_CELLS_FOR_FLOW", 100)  # force the skip path
    dem_path = _raster(
        tmp_path / "dem.tif", epsg=32647, size=40, res=30.0, origin=(300000.0, 5100000.0)
    )
    written, skipped = dem.derive_terrain(dem_path, {"flow": tmp_path / "flow.tif"})
    assert not written
    assert skipped and "flow skipped" in skipped[0]


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-q"])
