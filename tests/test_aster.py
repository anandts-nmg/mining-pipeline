"""ASTER SOP-chain tests (core.aster) — pure functions on synthetic arrays + discovery.

The HDF4 extraction step needs a QGIS-bundled gdalwarp and real swath data, so it is not
unit-tested here; the Phase 02 tests assert the graceful method-note fallback instead.
"""

from __future__ import annotations

import numpy as np
import pytest
from affine import Affine
from rasterio.crs import CRS

from buduunkhad.core import aster
from buduunkhad.core.aster import (
    AsterParams,
    anomaly_threshold,
    compute_indices,
    polygonize_targets,
    score_targets,
    write_index_raster,
)


def _profile(shape=(10, 10), res=30.0):
    return {
        "crs": CRS.from_epsg(32647),
        "transform": Affine(res, 0, 300000, 0, -res, 5100000),
        "height": shape[0],
        "width": shape[1],
    }


def _bands(shape=(10, 10)):
    """A full band set: constant rasters so ratios are exact, with one NaN corner."""
    bands = {}
    for i, name in enumerate(aster.BAND_SUBDATASETS, start=2):
        arr = np.full(shape, float(i), dtype="float32")
        arr[0, 0] = np.nan  # swath-fill pixel propagates to every index
        bands[name] = arr
    return bands


def test_compute_indices_ratios_and_ndvi():
    bands = _bands()
    idx = compute_indices(bands)
    # every SOP index + NDVI present
    assert set(idx) == set(aster.RATIO_INDICES) | {"NDVI"}
    # exact ratio: Ferric = B02/B01
    expected = bands["B02"][1, 1] / bands["B01"][1, 1]
    assert idx["Ferric_Iron_B02_B01"][1, 1] == pytest.approx(expected)
    # NDVI = (B3N-B02)/(B3N+B02)
    b3n, b2 = bands["B3N"][1, 1], bands["B02"][1, 1]
    assert idx["NDVI"][1, 1] == pytest.approx((b3n - b2) / (b3n + b2))
    # NaN input propagates
    for arr in idx.values():
        assert np.isnan(arr[0, 0])


def test_anomaly_threshold_mean_plus_k_sigma():
    arr = np.array([[1.0, 2.0], [3.0, np.nan]], dtype="float32")
    mean, std, thr = anomaly_threshold(arr, k=1.5)
    assert mean == pytest.approx(2.0)
    assert thr == pytest.approx(mean + 1.5 * std)


def test_score_targets_weights_and_nodata():
    shape = (10, 10)
    bands = _bands(shape)
    idx = compute_indices(bands)
    # inject a hot block that exceeds every component's threshold
    for _short, (index_name, _w) in aster.SCORE_COMPONENTS.items():
        idx[index_name] = idx[index_name].copy()
        idx[index_name][2:6, 2:6] = 1000.0  # extreme anomaly
    binaries, score, stats = score_targets(idx, params=AsterParams())
    # all four components fire on the hot block -> score = 2+1+1+1 = 5
    assert score[3, 3] == 5
    # background (constant) pixels score 0
    assert score[8, 8] == 0
    # the NaN corner is nodata 255
    assert score[0, 0] == 255
    # stats rows carry thresholds per component
    assert {s["component"] for s in stats} == set(aster.SCORE_COMPONENTS)
    assert all(float(str(s["threshold"])) > float(str(s["mean"])) for s in stats)


def test_polygonize_targets_area_filter_and_confidence():
    params = AsterParams()  # min_area_ha=0.5, score_min=3
    score = np.zeros((10, 10), dtype="uint8")
    score[2:6, 2:6] = 5  # 4x4 px @30m = 1.44 ha -> kept, High
    score[8, 8] = 3  # 1 px = 0.09 ha -> dropped (noise)
    gdf = polygonize_targets(score, _profile(), params=params)
    assert len(gdf) == 1
    row = gdf.iloc[0]
    assert row["target_score"] == 5
    assert row["confidence"] == "High"
    assert row["area_ha"] == pytest.approx(1.44)
    assert row["validation_status"] == "Support evidence only"


def test_write_index_raster_float_and_uint8(tmp_path):
    from buduunkhad.core import raster_writers

    prof = _profile(shape=(8, 8))
    arr = np.full((8, 8), 1.5, dtype="float32")
    arr[0, 0] = np.nan
    out = write_index_raster(arr, prof, tmp_path / "idx.tif")
    import rasterio

    with rasterio.open(out) as ds:
        assert ds.nodata == -9999.0
        assert ds.read(1)[0, 0] == -9999.0
        assert ds.read(1)[1, 1] == pytest.approx(1.5)
    assert raster_writers.is_cog(out)

    score = np.zeros((8, 8), dtype="uint8")
    score[0, 0] = 255
    out2 = write_index_raster(score, prof, tmp_path / "score.tif")
    with rasterio.open(out2) as ds:
        assert ds.nodata == 255
        assert ds.dtypes[0] == "uint8"


def test_score_targets_stats_mask_changes_threshold_basis():
    """Thresholds from AOI-masked statistics (licence-area subset), applied full-scene."""
    shape = (10, 10)
    bands = _bands(shape)
    idx = compute_indices(bands)
    # AOI = left half; make the RIGHT half extremely hot so full-scene stats would differ
    aoi = np.zeros(shape, dtype=bool)
    aoi[:, :5] = True
    for _short, (index_name, _w) in aster.SCORE_COMPONENTS.items():
        arr = idx[index_name].copy()
        arr[:, 5:] = 1000.0
        idx[index_name] = arr
    masked = score_targets(idx, params=AsterParams(), stats_mask=aoi, stats_basis="licence subset")
    unmasked = score_targets(idx, params=AsterParams())
    # AOI stats exclude the hot half -> lower threshold than full-scene stats
    thr_masked = float(str(masked[2][0]["threshold"]))
    thr_full = float(str(unmasked[2][0]["threshold"]))
    assert thr_masked < thr_full
    assert masked[2][0]["threshold_basis"] == "licence subset"
    # threshold applied FULL-scene: the hot right half exceeds the AOI-based threshold
    assert masked[1][3, 7] > 0  # scored outside the AOI


def test_find_hdf4_gdalwarp_env_override(tmp_path, monkeypatch):
    # empty string explicitly disables discovery
    monkeypatch.setenv("BUDUUNKHAD_GDAL_BIN", "")
    assert aster.find_hdf4_gdalwarp() is None
    # a directory without gdalwarp.exe -> None
    monkeypatch.setenv("BUDUUNKHAD_GDAL_BIN", str(tmp_path))
    assert aster.find_hdf4_gdalwarp() is None
    # a directory containing gdalwarp.exe -> that exe
    exe = tmp_path / "gdalwarp.exe"
    exe.write_bytes(b"stub")
    assert aster.find_hdf4_gdalwarp() == exe
