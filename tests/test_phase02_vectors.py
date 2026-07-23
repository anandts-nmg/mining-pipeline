"""Phase-02 vector products: hydrology (whitebox) + lineament draft (scikit-image).

Happy paths are skipped when the optional dependency is absent (CI installs only [dev]);
the degradation paths are environment-independent and always run.
"""

from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from buduunkhad.core import hydrology, lineaments
from buduunkhad.core.gates import GateStatus
from buduunkhad.core.hydrology import HydrologyParams
from buduunkhad.core.lineaments import LineamentError, extract_lineaments
from buduunkhad.phases.base import RunContext
from buduunkhad.phases.phase00_archive import Phase00Archive
from buduunkhad.phases.phase01_data_audit import Phase01DataAudit
from buduunkhad.phases.phase02_remote_sensing import Phase02RemoteSensing


def _write_raster(path, arr, *, res=12.5, epsg=32647, nodata=None):
    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": arr.dtype.name,
        "crs": f"EPSG:{epsg}",
        "transform": from_origin(300000, 5100000, res, res),
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(arr, 1)
    return path


def _skimage_missing() -> bool:
    try:
        import skimage  # noqa: F401  # ty: ignore[unresolved-import]

        return False
    except ImportError:
        return True


@pytest.mark.skipif(_skimage_missing(), reason="scikit-image not installed")
def test_extract_lineaments_finds_straight_feature(tmp_path):
    # two azimuth hillshades sharing a strong straight diagonal band
    # the dark band must exceed the 2% percentile-stretch tail to survive normalization
    base = np.full((200, 200), 128, dtype="uint8")
    rr, cc = np.mgrid[0:200, 0:200]
    band = np.abs(rr - cc) < 6
    a = base.copy()
    a[band] = 20
    b = base.copy()
    b[band] = 30
    paths = [
        _write_raster(tmp_path / "hs_az315.tif", a),
        _write_raster(tmp_path / "hs_az045.tif", b),
    ]
    gdf = extract_lineaments(paths)
    assert len(gdf) >= 1
    row = gdf.iloc[0]
    assert row["length_m"] >= 500.0
    assert 0.0 <= row["azimuth_deg"] < 180.0
    assert "Machine draft" in row["validation_status"]
    assert gdf.crs is not None and gdf.crs.to_epsg() == 32647


def test_extract_lineaments_requires_two_hillshades(tmp_path):
    p = _write_raster(tmp_path / "hs.tif", np.full((50, 50), 100, dtype="uint8"))
    with pytest.raises(LineamentError):
        extract_lineaments([p])


@pytest.mark.skipif(hydrology.find_whitebox() is None, reason="whitebox not installed")
def test_build_hydrology_valley_dem(tmp_path):
    # a V-valley draining down-rows: streams along the valley, contours across the slope
    rr, cc = np.mgrid[0:100, 0:100]
    dem = (np.abs(cc - 50) * 2.0 + rr * 0.5).astype("float32")
    dem_path = _write_raster(tmp_path / "dem.tif", dem)
    wbt = hydrology.find_whitebox()
    contours, streams, basins = hydrology.build_hydrology(
        dem_path,
        tmp_path / "work",
        wbt=wbt,
        params=HydrologyParams(contour_interval_m=20.0, stream_threshold_cells=50),
    )
    assert len(contours) >= 1
    assert len(streams) >= 1
    assert len(basins) >= 1
    assert streams.crs is not None and streams.crs.to_epsg() == 32647


def test_phase02_vector_products_degrade_gracefully(raw_archive, monkeypatch):
    """Without whitebox/skimage the phase records notes + N/A QA items and stays GO."""
    monkeypatch.setenv("BUDUUNKHAD_GDAL_BIN", "")  # keep ASTER on its fallback too
    monkeypatch.setattr(hydrology, "find_whitebox", lambda: None)

    def _boom(*_a, **_k):
        raise LineamentError("scikit-image not installed (test)")

    monkeypatch.setattr(lineaments, "extract_lineaments", _boom)

    config, register, _raw = raw_archive
    ctx = RunContext(config=config, register=register, run_id="test02v", dry_run=False)
    Phase00Archive().run(ctx)
    p1 = Phase01DataAudit()
    p1.prepare(ctx)
    p1.run(ctx)
    phase = Phase02RemoteSensing()
    phase.prepare(ctx)
    result = phase.run(ctx)
    assert result.status == "ok"
    assert phase._hydrology_note.startswith("skipped")
    assert phase._lineaments_note.startswith("skipped")

    report = phase.qaqc(ctx)
    hydro = next(i for i in report.items if "Vector hydrology" in i.item)
    lin = next(i for i in report.items if "Lineament first-pass" in i.item)
    assert hydro.decision.value == "N/A"
    assert lin.decision.value == "N/A"
    assert phase.gate(report, ctx).status is GateStatus.GO
