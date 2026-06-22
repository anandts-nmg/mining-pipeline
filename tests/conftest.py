"""Shared pytest fixtures.

The whole pipeline is exercised against tiny synthetic fixtures so no real data is
ever required: a temp project (copied config + register) and a synthetic raw
archive with valid mini-GeoTIFFs for raster inputs, a real KMZ for the boundary,
and small placeholder bytes for everything else.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from buduunkhad.config import load_config, load_register

REPO_ROOT = Path(__file__).resolve().parents[1]


_TEST_BASE = Path.home() / ".bkt_tests"


def _short_workdir() -> Path:
    """A short-path temp dir.

    Some real input filenames are very long; combined with a deep default pytest
    temp path they can exceed the Windows 260-char MAX_PATH limit, which breaks
    GDAL raster creation. Rooting fixtures near the home directory keeps paths short.
    """
    _TEST_BASE.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=_TEST_BASE))


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_base():
    """Sweep the short-path temp base before and after the session.

    Per-test cleanup can leave a dir behind when GDAL still holds a file lock on
    Windows (released only at process exit). Sweeping at session start removes any
    straggler from a previous run, so the steady state is at most one stale dir.
    """
    shutil.rmtree(_TEST_BASE, ignore_errors=True)
    yield
    import gc

    gc.collect()
    shutil.rmtree(_TEST_BASE, ignore_errors=True)


# --------------------------------------------------------------------------- #
# synthetic file builders
# --------------------------------------------------------------------------- #


def make_geotiff(path: Path, epsg: int = 4326, size: int = 10) -> Path:
    """Write a tiny valid single-band GeoTIFF."""
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.arange(size * size, dtype="uint8").reshape(size, size)
    # place it roughly over the Buduunkhad area (~96.5E, 45.5N) for EPSG:4326
    transform = from_origin(96.5, 45.6, 0.01, 0.01)
    profile = {
        "driver": "GTiff",
        "height": size,
        "width": size,
        "count": 1,
        "dtype": "uint8",
        "crs": f"EPSG:{epsg}",
        "transform": transform,
        "nodata": 0,
    }
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(data, 1)
    return path


def make_boundary_kmz(path: Path) -> Path:
    """Write a KMZ containing a single WGS84 polygon (a small square)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    coords = [
        (96.40, 45.40),
        (96.60, 45.40),
        (96.60, 45.60),
        (96.40, 45.60),
        (96.40, 45.40),
    ]
    coord_str = " ".join(f"{lon},{lat},0" for lon, lat in coords)
    kml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>\n'
        "<Placemark><name>L23222</name><Polygon><outerBoundaryIs><LinearRing>\n"
        f"<coordinates>{coord_str}</coordinates>\n"
        "</LinearRing></outerBoundaryIs></Polygon></Placemark>\n"
        "</Document></kml>\n"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml)
    return path


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def project():
    """A temp project: real config + register copied in, paths rooted at a short dir."""
    work = _short_workdir()
    cfg_dir = work / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "config" / "project.yaml", cfg_dir / "project.yaml")
    shutil.copy(REPO_ROOT / "config" / "input_register.csv", cfg_dir / "input_register.csv")

    config = load_config(cfg_dir / "project.yaml")
    register = load_register(config.register_path)
    try:
        yield config, register, work
    finally:
        shutil.rmtree(work, ignore_errors=True)


@pytest.fixture
def raw_archive(project):
    """Populate raw_root with synthetic files for all 78 register entries."""
    config, register, _tmp = project
    raw_root = config.raw_root
    for rec in register:
        dest = raw_root / rec.evidence_group / rec.filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rec.no == config.boundary.input_no:
            make_boundary_kmz(dest)
        elif rec.file_type == "raster":
            # alternate native CRS so the audit sees both reproject/no-reproject
            epsg = config.target_epsg if rec.no % 2 == 0 else 4326
            make_geotiff(dest, epsg=epsg)
        else:
            dest.write_bytes(f"synthetic placeholder for #{rec.no} {rec.filename}".encode())
    return config, register, raw_root
