"""Unit tests for the DEM terrain-derivative math."""

from __future__ import annotations

import numpy as np

from buduunkhad.core import dem


def test_slope_flat_is_zero():
    z = np.full((8, 8), 100.0)
    slope = dem.slope_degrees(z, 1.0, 1.0)
    assert np.allclose(slope, 0.0)


def test_slope_tilted_plane_is_45deg():
    # z increases by 1 per cell east -> gradient 1 -> 45 degrees
    z = np.tile(np.arange(12, dtype="float64"), (12, 1))
    slope = dem.slope_degrees(z, 1.0, 1.0)
    assert np.allclose(slope[3:9, 3:9], 45.0, atol=0.01)


def test_hillshade_range_and_shape():
    z = np.random.default_rng(0).random((16, 16)) * 50
    hs = dem.hillshade(z, 1.0, 1.0)
    assert hs.shape == (16, 16)
    assert hs.dtype == np.uint8
    assert hs.min() >= 0 and hs.max() <= 255


def test_aspect_flat_is_negative_one():
    z = np.full((6, 6), 7.0)
    aspect = dem.aspect_degrees(z, 1.0, 1.0)
    assert np.allclose(aspect, -1.0)


def test_flow_accumulation_drains_downhill():
    rows, cols = 10, 10
    # higher at the top, lower at the bottom -> every column drains straight down
    z = np.fromfunction(lambda r, c: rows - r, (rows, cols), dtype="float64")
    acc = dem.flow_accumulation_d8(z)
    assert acc.shape == (rows, cols)
    assert acc.dtype == np.float32
    assert acc.min() >= 1.0
    # the bottom of each column collects all cells above it
    assert acc.max() >= rows


def test_tri_flat_is_zero_and_responds_to_relief():
    flat = np.full((8, 8), 5.0)
    assert np.allclose(dem.terrain_ruggedness_index(flat), 0.0)
    rough = np.random.default_rng(0).random((12, 12)) * 100
    tri = dem.terrain_ruggedness_index(rough)
    assert tri.dtype == np.float32 and tri[2:10, 2:10].max() > 0


def test_curvature_flat_is_zero():
    z = np.full((8, 8), 5.0)
    prof, plan = dem.curvature(z, 30.0, 30.0)
    assert prof.dtype == np.float32 and plan.dtype == np.float32
    assert np.allclose(prof, 0.0) and np.allclose(plan, 0.0)


def test_derive_terrain_remasks_nodata(tmp_path):
    """A DEM block flagged nodata must stay nodata on slope (float) and hillshade (uint8)."""
    import rasterio
    from rasterio.transform import from_origin

    sentinel = -9999.0
    size = 20
    z = np.fromfunction(lambda r, c: (r + c).astype("float64"), (size, size))
    # mask a 4x4 interior block (away from edges so it is not just a Horn artefact)
    z[8:12, 8:12] = sentinel
    masked_idx = np.zeros((size, size), dtype=bool)
    masked_idx[8:12, 8:12] = True

    dem_path = tmp_path / "dem.tif"
    profile = {
        "driver": "GTiff",
        "height": size,
        "width": size,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32647",
        "transform": from_origin(300000.0, 5100000.0, 30.0, 30.0),
        "nodata": sentinel,
    }
    with rasterio.open(dem_path, "w", **profile) as ds:
        ds.write(z.astype("float32"), 1)

    outs = {"slope": tmp_path / "slope.tif", "hillshade": tmp_path / "hillshade.tif"}
    written, skipped = dem.derive_terrain(dem_path, outs)
    assert len(written) == 2 and not skipped

    for key in ("slope", "hillshade"):
        with rasterio.open(outs[key]) as ds:
            band = ds.read(1, masked=True)
            assert band.mask[masked_idx].all(), f"{key} did not re-mask the nodata block"
            # valid data must survive elsewhere (the whole raster is not masked away)
            assert not band.mask.all()
