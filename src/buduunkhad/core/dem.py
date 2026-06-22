"""DEM terrain derivatives (hillshade, slope, aspect, D8 flow accumulation).

Pure-numpy implementations (Horn's 3x3 method for gradients) so Phase 02 produces
real terrain layers with no heavy optional dependency. Flow accumulation is a
straightforward D8 (steepest-descent, processed in descending-elevation order, no
depression filling) - good for the foundation; swap in WhiteboxTools/richdem (the
``[dem]`` extra) for large production DEMs.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

# Above this many cells the Python D8 loop is too slow; skip with a note instead.
MAX_CELLS_FOR_FLOW = 4_000_000

_NBRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
_SQRT2 = math.sqrt(2.0)
_NBR_DIST = [_SQRT2, 1.0, _SQRT2, 1.0, 1.0, _SQRT2, 1.0, _SQRT2]


def _horn_gradients(z: np.ndarray, xres: float, yres: float) -> tuple[np.ndarray, np.ndarray]:
    """Horn's 3x3 finite-difference gradients (edges replicated)."""
    zp = np.pad(z.astype("float64"), 1, mode="edge")
    a, b, c = zp[:-2, :-2], zp[:-2, 1:-1], zp[:-2, 2:]
    d, f = zp[1:-1, :-2], zp[1:-1, 2:]
    g, h, i = zp[2:, :-2], zp[2:, 1:-1], zp[2:, 2:]
    dzdx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8.0 * abs(xres))
    dzdy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8.0 * abs(yres))
    return dzdx, dzdy


def slope_degrees(z: np.ndarray, xres: float, yres: float, z_factor: float = 1.0) -> np.ndarray:
    dzdx, dzdy = _horn_gradients(z, xres, yres)
    rise_run = np.hypot(dzdx, dzdy) * z_factor
    return np.degrees(np.arctan(rise_run)).astype("float32")


def aspect_degrees(z: np.ndarray, xres: float, yres: float) -> np.ndarray:
    """Compass aspect in degrees (0=N, 90=E ...); flat cells -> -1."""
    dzdx, dzdy = _horn_gradients(z, xres, yres)
    aspect = np.degrees(np.arctan2(dzdy, -dzdx))
    aspect = np.where(
        aspect < 0, 90.0 - aspect, np.where(aspect > 90.0, 450.0 - aspect, 90.0 - aspect)
    )
    flat = (dzdx == 0) & (dzdy == 0)
    aspect = np.where(flat, -1.0, aspect)
    return aspect.astype("float32")


def hillshade(
    z: np.ndarray,
    xres: float,
    yres: float,
    *,
    azimuth: float = 315.0,
    altitude: float = 45.0,
    z_factor: float = 1.0,
) -> np.ndarray:
    """Shaded relief (0-255 uint8)."""
    dzdx, dzdy = _horn_gradients(z, xres, yres)
    slope_rad = np.arctan(z_factor * np.hypot(dzdx, dzdy))
    aspect_rad = np.arctan2(dzdy, -dzdx)
    zenith_rad = math.radians(90.0 - altitude)
    azimuth_rad = math.radians(360.0 - azimuth + 90.0)
    shaded = np.cos(zenith_rad) * np.cos(slope_rad) + np.sin(zenith_rad) * np.sin(
        slope_rad
    ) * np.cos(azimuth_rad - aspect_rad)
    return np.clip(shaded * 255.0, 0, 255).astype("uint8")


def flow_accumulation_d8(z: np.ndarray) -> np.ndarray:
    """D8 flow accumulation (cell counts), steepest-descent, no depression filling."""
    rows, cols = z.shape
    zf = z.astype("float64")
    acc = np.ones((rows, cols), dtype="float64")
    order = np.argsort(zf, axis=None)[::-1]  # highest elevation first
    for flat in order:
        r, c = divmod(int(flat), cols)
        here = zf[r, c]
        best_slope = 0.0
        best: tuple[int, int] | None = None
        for k, (dr, dc) in enumerate(_NBRS):
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and zf[rr, cc] < here:
                s = (here - zf[rr, cc]) / _NBR_DIST[k]
                if s > best_slope:
                    best_slope = s
                    best = (rr, cc)
        if best is not None:
            acc[best] += acc[r, c]
    return acc.astype("float32")


# --------------------------------------------------------------------------- #
# raster IO orchestration
# --------------------------------------------------------------------------- #


def _read_elevation(path: Path):  # type: ignore[no-untyped-def]
    import rasterio

    with rasterio.open(path) as ds:
        band = ds.read(1, masked=True).astype("float64").filled(np.nan)
        xres, yres = ds.res
        profile = ds.profile.copy()
    return band, xres, yres, profile


def _write(path: Path, array: np.ndarray, profile: dict, dtype: str, nodata) -> Path:
    import rasterio

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = profile.copy()
    out.update(count=1, dtype=dtype, driver="GTiff", nodata=nodata)
    with rasterio.open(path, "w", **out) as ds:
        ds.write(array.astype(dtype), 1)
    return path


def derive_terrain(dem_path: Path, outputs: dict[str, Path]) -> list[Path]:
    """Compute terrain derivatives from a (reprojected) DEM and write GeoTIFFs.

    ``outputs`` maps any of ``hillshade|slope|aspect|flow`` to a destination path.
    NaNs (from masked nodata) are filled with the mean so gradients stay finite.
    Returns the paths actually written (``flow`` is skipped for very large DEMs).
    """
    z, xres, yres, profile = _read_elevation(dem_path)
    if np.isnan(z).any():
        mean = np.nanmean(z)
        z = np.where(np.isnan(z), mean if np.isfinite(mean) else 0.0, z)

    written: list[Path] = []
    if "hillshade" in outputs:
        written.append(_write(outputs["hillshade"], hillshade(z, xres, yres), profile, "uint8", 0))
    if "slope" in outputs:
        written.append(
            _write(outputs["slope"], slope_degrees(z, xres, yres), profile, "float32", -9999.0)
        )
    if "aspect" in outputs:
        written.append(
            _write(outputs["aspect"], aspect_degrees(z, xres, yres), profile, "float32", -9999.0)
        )
    if "flow" in outputs and z.size <= MAX_CELLS_FOR_FLOW:
        written.append(
            _write(outputs["flow"], flow_accumulation_d8(z), profile, "float32", -9999.0)
        )
    return written
