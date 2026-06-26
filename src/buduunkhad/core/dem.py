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


def terrain_ruggedness_index(z: np.ndarray) -> np.ndarray:
    """Riley (1999) Terrain Ruggedness Index: sqrt(sum of squared 8-neighbour diffs)."""
    zp = np.pad(z.astype("float64"), 1, mode="edge")
    rows, cols = z.shape
    center = zp[1:-1, 1:-1]
    ss = np.zeros_like(center)
    for dr, dc in _NBRS:
        nb = zp[1 + dr : 1 + dr + rows, 1 + dc : 1 + dc + cols]
        ss += (nb - center) ** 2
    return np.sqrt(ss).astype("float32")


def curvature(z: np.ndarray, xres: float, yres: float) -> tuple[np.ndarray, np.ndarray]:
    """Zevenbergen-Thorne (1987) profile and plan curvature (float32, flat cells -> 0)."""
    cell = (abs(xres) + abs(yres)) / 2.0
    zp = np.pad(z.astype("float64"), 1, mode="edge")
    z1, z2, z3 = zp[:-2, :-2], zp[:-2, 1:-1], zp[:-2, 2:]
    z4, z5, z6 = zp[1:-1, :-2], zp[1:-1, 1:-1], zp[1:-1, 2:]
    z7, z8, z9 = zp[2:, :-2], zp[2:, 1:-1], zp[2:, 2:]
    d = ((z4 + z6) / 2.0 - z5) / cell**2
    e = ((z2 + z8) / 2.0 - z5) / cell**2
    f = (-z1 + z3 + z7 - z9) / (4.0 * cell**2)
    g = (-z4 + z6) / (2.0 * cell)
    h = (z2 - z8) / (2.0 * cell)
    denom = g**2 + h**2
    with np.errstate(divide="ignore", invalid="ignore"):
        prof = np.where(denom > 0, -2.0 * (d * g**2 + e * h**2 + f * g * h) / denom, 0.0)
        plan = np.where(denom > 0, 2.0 * (d * h**2 + e * g**2 - f * g * h) / denom, 0.0)
    return prof.astype("float32"), plan.astype("float32")


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


def _write_cog(
    path: Path,
    array: np.ndarray,
    base_profile: dict,
    *,
    dtype: str,
    nodata,
    predictor: str | None,
    overview_resampling: str,
) -> Path:
    """Write ``array`` as a COG. The profile is built **fresh** (crs/transform/size only)
    so a source DEM's compression/predictor can never leak onto a derivative."""
    import tempfile

    import rasterio

    from buduunkhad.core import raster_writers

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prof = {
        k: base_profile[k] for k in ("crs", "transform", "width", "height") if k in base_profile
    }
    prof.update(count=1, dtype=dtype, driver="GTiff", nodata=nodata)
    with tempfile.TemporaryDirectory() as tmp:
        tmpf = Path(tmp) / "deriv.tif"
        with rasterio.open(tmpf, "w", **prof) as ds:
            ds.write(array.astype(dtype), 1)
        raster_writers.write_cog(
            tmpf,
            path,
            compress="DEFLATE",
            predictor=predictor,
            overview_resampling=overview_resampling,
        )
    return path


def derive_terrain(dem_path: Path, outputs: dict[str, Path]) -> tuple[list[Path], list[str]]:
    """Compute terrain derivatives from a (clipped, reprojected) DEM and write COGs.

    ``outputs`` maps derivative keys to destination paths. Supported keys:
    ``hillshade`` (az 315), ``hillshade_az<NNN>`` (e.g. ``hillshade_az045``), ``slope``,
    ``aspect``, ``tri``, ``profile_curvature``, ``plan_curvature``, ``flow``.
    NaNs (from masked nodata) are filled with the mean so gradients stay finite.
    Returns ``(written_paths, skipped_notes)`` - ``flow`` is skipped (and noted, never
    silently) for DEMs above :data:`MAX_CELLS_FOR_FLOW`.
    """
    z, xres, yres, profile = _read_elevation(dem_path)
    if np.isnan(z).any():
        mean = np.nanmean(z)
        z = np.where(np.isnan(z), mean if np.isfinite(mean) else 0.0, z)

    written: list[Path] = []
    skipped: list[str] = []
    _curv: tuple[np.ndarray, np.ndarray] | None = None

    def _float(path: Path, arr: np.ndarray) -> None:
        written.append(
            _write_cog(
                path,
                arr,
                profile,
                dtype="float32",
                nodata=-9999.0,
                predictor="3",
                overview_resampling="AVERAGE",
            )
        )

    for key, path in outputs.items():
        if key == "hillshade" or key.startswith("hillshade_az"):
            az = 315.0 if key == "hillshade" else float(key.rsplit("az", 1)[1])
            written.append(
                _write_cog(
                    path,
                    hillshade(z, xres, yres, azimuth=az),
                    profile,
                    dtype="uint8",
                    nodata=0,
                    predictor=None,
                    overview_resampling="NEAREST",
                )
            )
        elif key == "slope":
            _float(path, slope_degrees(z, xres, yres))
        elif key == "aspect":
            _float(path, aspect_degrees(z, xres, yres))
        elif key == "tri":
            _float(path, terrain_ruggedness_index(z))
        elif key in ("profile_curvature", "plan_curvature"):
            if _curv is None:
                _curv = curvature(z, xres, yres)
            _float(path, _curv[0] if key == "profile_curvature" else _curv[1])
        elif key == "flow":
            if z.size <= MAX_CELLS_FOR_FLOW:
                _float(path, flow_accumulation_d8(z))
            else:
                skipped.append(f"flow skipped: {z.size} cells > {MAX_CELLS_FOR_FLOW}")
    return written, skipped
