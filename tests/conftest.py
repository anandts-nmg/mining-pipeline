"""Shared pytest fixtures.

The whole pipeline is exercised against tiny synthetic fixtures so no real data is
ever required: a temp project (copied config + register) and a synthetic raw
archive with valid mini-GeoTIFFs for raster inputs, a real KMZ for the boundary,
and small placeholder bytes for everything else.
"""

from __future__ import annotations

import _socket
import http.client
import os
import shutil
import socket
import tempfile
import urllib.request
import zipfile
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


class UnexpectedNetworkAccess(RuntimeError):
    """Raised when ordinary tests attempt any DNS or network socket operation."""


def _deny_network(*args: object, **kwargs: object) -> None:
    raise UnexpectedNetworkAccess(f"network access is disabled during tests: {args}, {kwargs}")


_SYSTEM_SOCKET = socket.socket
_NETWORK_TARGETS = (
    (socket, "socket"),
    (socket, "SocketType"),
    (socket, "create_connection"),
    (socket, "create_server"),
    (socket, "socketpair"),
    (socket, "getaddrinfo"),
    (socket, "gethostbyname"),
    (socket, "gethostbyname_ex"),
    (socket, "gethostbyaddr"),
    (socket, "getnameinfo"),
    (socket, "getfqdn"),
    (urllib.request, "urlopen"),
    (http.client.HTTPConnection, "connect"),
    (http.client.HTTPConnection, "request"),
    (http.client.HTTPSConnection, "connect"),
) + tuple(
    (_socket, name)
    for name in (
        "socket",
        "SocketType",
        "socketpair",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
    )
    if hasattr(_socket, name)
)
_NETWORK_ORIGINALS: tuple[tuple[object, str, object], ...] = tuple(
    (owner, name, getattr(owner, name)) for owner, name in _NETWORK_TARGETS
)
_CONFIGURE_DEPTH = 0


class _DeniedSocket(_SYSTEM_SOCKET):
    """Remain subclassable by ``ssl`` while denying every socket instance."""

    def __new__(cls, *args: object, **kwargs: object) -> _DeniedSocket:
        _deny_network(*args, **kwargs)
        raise AssertionError("unreachable")


def _install_network_denial() -> None:
    _socket.socket = _DeniedSocket  # type: ignore[attr-defined]
    if hasattr(_socket, "SocketType"):
        _socket.SocketType = _DeniedSocket  # type: ignore[attr-defined]
    if hasattr(_socket, "socketpair"):
        _socket.socketpair = _deny_network  # type: ignore[attr-defined]
    for name in (
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
    ):
        if hasattr(_socket, name):
            setattr(_socket, name, _deny_network)
    socket.socket = _DeniedSocket
    socket.SocketType = _DeniedSocket  # type: ignore[misc]
    socket.create_connection = _deny_network  # type: ignore[assignment]
    socket.create_server = _deny_network  # type: ignore[assignment]
    socket.socketpair = _deny_network  # type: ignore[assignment]
    socket.getaddrinfo = _deny_network  # type: ignore[assignment]
    socket.gethostbyname = _deny_network  # type: ignore[assignment]
    socket.gethostbyname_ex = _deny_network  # type: ignore[assignment]
    socket.gethostbyaddr = _deny_network  # type: ignore[assignment]
    socket.getnameinfo = _deny_network  # type: ignore[assignment]
    socket.getfqdn = _deny_network  # type: ignore[assignment]
    urllib.request.urlopen = _deny_network  # type: ignore[assignment]
    http.client.HTTPConnection.connect = _deny_network  # type: ignore[assignment]
    http.client.HTTPConnection.request = _deny_network  # type: ignore[assignment]
    http.client.HTTPSConnection.connect = _deny_network  # type: ignore[assignment]


def _restore_network_originals() -> None:
    for owner, name, original in _NETWORK_ORIGINALS:
        setattr(owner, name, original)


# Activate while conftest itself is importing, before application or test modules load.
_install_network_denial()


def pytest_configure() -> None:
    """Activate before test-module collection while leaving subprocess pipes untouched."""
    global _CONFIGURE_DEPTH
    _CONFIGURE_DEPTH += 1
    _install_network_denial()


def pytest_unconfigure() -> None:
    """Restore process globals after the outermost pytest session."""
    global _CONFIGURE_DEPTH
    _CONFIGURE_DEPTH = max(0, _CONFIGURE_DEPTH - 1)
    if _CONFIGURE_DEPTH:
        _install_network_denial()
    else:
        _restore_network_originals()


@pytest.fixture(autouse=True)
def _reassert_network_denial() -> Iterator[None]:
    """Prevent one test's mutation from weakening the next test's guard."""
    _install_network_denial()
    yield
    _install_network_denial()


_TEST_BASE_ROOT = Path.home() / ".bkt_tests"
_SESSION_BASE = _TEST_BASE_ROOT / f"s{os.getpid():x}"


def _short_workdir() -> Path:
    """A short-path temp dir.

    Some real input filenames are very long; combined with a deep default pytest
    temp path they can exceed the Windows 260-char MAX_PATH limit, which breaks
    GDAL raster creation. Rooting fixtures near the home directory keeps paths short.
    """
    _SESSION_BASE.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=_SESSION_BASE))


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_base() -> Iterator[None]:
    """Clean only this pytest session's short-path temporary root.

    Per-test cleanup can leave a dir behind when GDAL still holds a file lock on
    Windows (released only at process exit). Other concurrent sessions own sibling
    directories and are never removed here.
    """
    _SESSION_BASE.mkdir(parents=True, exist_ok=True)
    yield
    import gc

    gc.collect()
    shutil.rmtree(_SESSION_BASE, ignore_errors=True)
    with suppress(OSError):
        _TEST_BASE_ROOT.rmdir()


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
    from buduunkhad.config import load_config, load_register

    work = _short_workdir()
    cfg_dir = work / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "config" / "project.yaml", cfg_dir / "project.yaml")
    shutil.copy(REPO_ROOT / "config" / "input_register.csv", cfg_dir / "input_register.csv")
    shutil.copy(REPO_ROOT / "config" / "raw_manifest.csv", cfg_dir / "raw_manifest.csv")

    config = load_config(cfg_dir / "project.yaml")
    register = load_register(config.register_path)
    try:
        yield config, register, work
    finally:
        shutil.rmtree(work, ignore_errors=True)


@pytest.fixture
def raw_archive(project):
    """Populate raw_root with synthetic files for all 79 register entries."""
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
