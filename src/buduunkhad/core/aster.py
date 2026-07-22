"""ASTER L1B alteration processing (Phase 02 frozen support-evidence algorithm).

The exact master requires HDF import, band extraction, UTM47 projection, indices, separate raw
scores/classes/binary masks, and support-only QA/QC outputs. This module retains the repository's
historical numeric implementation for reproducibility: HDF4 band extraction → EPSG:32647 GCP
warp → common 30 m analysis grid → band-ratio alteration indices → mean + k·σ anomaly binaries
→ weighted porphyry target score → target polygons. The unlocated standalone ASTER SOP is
obsolete under METH-DISC-063, so this module does not claim independent reproduction of that
document or its historical reference outputs.

The HDF4 → GeoTIFF step needs a GDAL build with the **HDF4 driver**, which the pip rasterio
wheel lacks. We shell out to a QGIS-bundled ``gdalwarp`` (discovered via
``BUDUUNKHAD_GDAL_BIN`` or the standard QGIS/OSGeo4W install paths) for that one step and do
everything else in rasterio/numpy. Callers must degrade to the method note when
:func:`find_hdf4_gdalwarp` returns ``None`` or :class:`AsterError` is raised.

Every output is **support evidence only — not ore proof** (invariant #8). The parameters are
frozen repository constants from historical decisions METH-DISC-020/021, exposed on
:class:`AsterParams` so any future tuning requires an explicit versioned methodology decision.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

#: Bands the frozen index chain needs: band name -> (swath, subdataset).
BAND_SUBDATASETS: dict[str, tuple[str, str]] = {
    "B01": ("VNIR_Swath", "ImageData1"),
    "B02": ("VNIR_Swath", "ImageData2"),
    "B3N": ("VNIR_Swath", "ImageData3N"),
    "B04": ("SWIR_Swath", "ImageData4"),
    "B05": ("SWIR_Swath", "ImageData5"),
    "B06": ("SWIR_Swath", "ImageData6"),
    "B07": ("SWIR_Swath", "ImageData7"),
    "B08": ("SWIR_Swath", "ImageData8"),
    "B12": ("TIR_Swath", "ImageData12"),
    "B13": ("TIR_Swath", "ImageData13"),
    "B14": ("TIR_Swath", "ImageData14"),
}

#: Frozen ratio indices: output name -> (numerator band, denominator band).
#: Sericite/Illite (B05/B06) and Carbonate/Mg-OH (B07/B08) share formulas with Clay and
#: Chlorite respectively — computed once under the canonical name (noted in the QA register).
RATIO_INDICES: dict[str, tuple[str, str]] = {
    "Ferric_Iron_B02_B01": ("B02", "B01"),
    "Clay_AlOH_B05_B06": ("B05", "B06"),
    "Advanced_Argillic_B04_B06": ("B04", "B06"),
    "Chlorite_Epidote_MgOH_B07_B08": ("B07", "B08"),
    "Silica_B13_B12": ("B13", "B12"),
    "Quartz_Rich_B14_B12": ("B14", "B12"),
}

#: Frozen target-score components: short name -> (index name, weight).
SCORE_COMPONENTS: dict[str, tuple[str, int]] = {
    "clay": ("Clay_AlOH_B05_B06", 2),
    "ferric": ("Ferric_Iron_B02_B01", 1),
    "chlorite": ("Chlorite_Epidote_MgOH_B07_B08", 1),
    "silica": ("Silica_B13_B12", 1),
}

_SCORE_NODATA = 255


class AsterError(RuntimeError):
    """Raised when the ASTER chain cannot run (bad HDF, failed warp, missing bands)."""


@dataclass(frozen=True)
class AsterParams:
    """Frozen support defaults; changes require a versioned methodology decision."""

    epsg: int = 32647
    grid_res: float = 30.0  # frozen common analysis grid = SWIR resolution
    threshold_k: float = 1.5  # frozen anomaly threshold = mean + k*std
    score_min: int = 3  # frozen polygonization score floor
    min_area_ha: float = 0.5  # frozen support-layer noise filter


@dataclass
class AsterResult:
    band_files: list[Path] = field(default_factory=list)
    index_files: list[Path] = field(default_factory=list)
    score_files: list[Path] = field(default_factory=list)
    polygon_file: Path | None = None
    n_targets: int = 0
    stats_rows: list[dict[str, object]] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# HDF4-capable gdalwarp discovery
# --------------------------------------------------------------------------- #


def find_hdf4_gdalwarp() -> Path | None:
    """An HDF4-capable ``gdalwarp`` executable, or ``None``.

    Order: ``BUDUUNKHAD_GDAL_BIN`` (a directory containing gdalwarp, or the exe itself;
    set to an empty string to disable), then QGIS / OSGeo4W install locations.
    """
    env = os.environ.get("BUDUUNKHAD_GDAL_BIN")
    if env is not None:
        if not env.strip():
            return None  # explicitly disabled
        p = Path(env)
        exe = p if p.suffix else p / "gdalwarp.exe"
        return exe if exe.exists() else None
    candidates: list[Path] = []
    for root in (Path("C:/Program Files"), Path("C:/")):
        if root.exists():
            candidates.extend(root.glob("QGIS*/bin/gdalwarp.exe"))
            candidates.extend(root.glob("OSGeo4W*/bin/gdalwarp.exe"))
    return sorted(candidates)[-1] if candidates else None


def _gdal_env(gdalwarp: Path) -> dict[str, str]:
    """Subprocess env with PROJ/GDAL data dirs so CRS ops work outside the QGIS shell."""
    env = dict(os.environ)
    share = gdalwarp.parent.parent / "share"
    if (share / "proj").is_dir():
        env["PROJ_LIB"] = str(share / "proj")
    if (share / "gdal").is_dir():
        env["GDAL_DATA"] = str(share / "gdal")
    return env


def extract_bands(
    hdf_path: Path, out_dir: Path, gdalwarp: Path, *, epsg: int = 32647
) -> dict[str, Path]:
    """GCP-warp each required HDF4 swath band to an ``EPSG:<epsg>`` GeoTIFF.

    Verified against the geologist's QGIS export of the same scene: identical grid
    (size, pixel, corner coordinates). DN 0 is the swath fill -> nodata.
    """
    hdf_path = Path(hdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    env = _gdal_env(gdalwarp)
    out: dict[str, Path] = {}
    for band, (swath, sds) in BAND_SUBDATASETS.items():
        src = f'HDF4_EOS:EOS_SWATH:"{hdf_path}":{swath}:{sds}'
        dst = out_dir / f"{band}_EPSG{epsg}.tif"
        cmd = [
            str(gdalwarp),
            "-overwrite",
            "-t_srs",
            f"EPSG:{epsg}",
            "-r",
            "bilinear",
            "-srcnodata",
            "0",
            "-dstnodata",
            "0",
            "-co",
            "COMPRESS=DEFLATE",
            src,
            str(dst),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if proc.returncode != 0 or not dst.exists():
            raise AsterError(
                f"gdalwarp failed for {band} ({swath}:{sds}): "
                f"{(proc.stderr or proc.stdout).strip()[:300]}"
            )
        out[band] = dst
    return out


# --------------------------------------------------------------------------- #
# grid alignment + index math (pure rasterio/numpy)
# --------------------------------------------------------------------------- #


def read_aligned(band_files: dict[str, Path], *, ref_band: str = "B04"):  # type: ignore[no-untyped-def]
    """Read every band resampled (bilinear) onto the reference band's grid.

    Returns ``(arrays, profile)`` — float32 arrays with NaN where nodata, plus a rasterio
    profile describing the common grid. B04 (SWIR, 30 m) is the SOP's analysis grid.
    """
    import rasterio
    from rasterio.warp import Resampling, reproject

    with rasterio.open(band_files[ref_band]) as ref:
        profile = ref.profile.copy()
        ref_transform, ref_crs = ref.transform, ref.crs
        shape = (ref.height, ref.width)

    arrays: dict[str, np.ndarray] = {}
    for band, path in band_files.items():
        with rasterio.open(path) as src:
            if band == ref_band:
                data = src.read(1).astype("float32")
            else:
                data = np.zeros(shape, dtype="float32")
                reproject(
                    source=rasterio.band(src, 1),
                    destination=data,
                    dst_transform=ref_transform,
                    dst_crs=ref_crs,
                    resampling=Resampling.bilinear,
                    src_nodata=src.nodata,
                    dst_nodata=0.0,
                )
        data[data == 0.0] = np.nan  # DN 0 = swath fill
        arrays[band] = data
    return arrays, profile


def compute_indices(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Frozen band-ratio indices plus NDVI; Float32 with NaN where invalid."""
    out: dict[str, np.ndarray] = {}
    for name, (num, den) in RATIO_INDICES.items():
        a, b = arrays[num], arrays[den]
        with np.errstate(divide="ignore", invalid="ignore"):
            out[name] = np.where(np.isnan(a) | np.isnan(b) | (b == 0), np.nan, a / b).astype(
                "float32"
            )
    b3n, b2 = arrays["B3N"], arrays["B02"]
    with np.errstate(divide="ignore", invalid="ignore"):
        s = b3n + b2
        out["NDVI"] = np.where(
            np.isnan(b3n) | np.isnan(b2) | (s == 0), np.nan, (b3n - b2) / s
        ).astype("float32")
    return out


def anomaly_threshold(index: np.ndarray, *, k: float) -> tuple[float, float, float]:
    """Frozen statistical rule returning ``(mean, std, mean + k*std)``."""
    mean = float(np.nanmean(index))
    std = float(np.nanstd(index))
    return mean, std, mean + k * std


def aoi_mask(aoi_gdf, profile) -> np.ndarray:  # type: ignore[no-untyped-def]
    """Boolean mask (True inside the AOI geometries) on the profile's grid."""
    from rasterio.features import geometry_mask

    geoms = list(aoi_gdf.to_crs(profile["crs"]).geometry)
    return geometry_mask(
        geoms,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        invert=True,
    )


def score_targets(
    indices: dict[str, np.ndarray],
    *,
    params: AsterParams,
    stats_mask: np.ndarray | None = None,
    stats_basis: str = "full scene",
) -> tuple[dict[str, np.ndarray], np.ndarray, list[dict[str, object]]]:
    """Frozen anomaly binaries plus the weighted porphyry support score.

    ``stats_mask`` restricts the mean/σ **statistics** to an AOI. The frozen
    METH-DISC-021 basis is the licence-area subset (the 5 km buffer); the resulting threshold
    is still applied to the whole scene so the score keeps its district context.
    ``stats_basis`` labels the basis in the stats rows. Returns ``(binaries, score,
    stats_rows)``; score is uint8 with 255 = nodata (outside the imaged swath).
    """
    binaries: dict[str, np.ndarray] = {}
    stats: list[dict[str, object]] = []
    valid_all: np.ndarray | None = None
    for short, (index_name, weight) in SCORE_COMPONENTS.items():
        idx = indices[index_name]
        stats_arr = np.where(stats_mask, idx, np.nan) if stats_mask is not None else idx
        mean, std, thr = anomaly_threshold(stats_arr, k=params.threshold_k)
        binary = (idx > thr) & ~np.isnan(idx)
        binaries[short] = binary.astype("uint8")
        valid = ~np.isnan(idx)
        valid_all = valid if valid_all is None else (valid_all & valid)
        stats.append(
            {
                "component": short,
                "index": index_name,
                "weight": weight,
                "threshold_basis": stats_basis,
                "mean": round(mean, 6),
                "std": round(std, 6),
                "threshold": round(thr, 6),
                "anomaly_pixels": int(binary.sum()),
                "valid_pixels": int(valid.sum()),
            }
        )
    assert valid_all is not None  # SCORE_COMPONENTS is non-empty
    score = np.zeros(valid_all.shape, dtype="uint8")
    for short, (_index_name, weight) in SCORE_COMPONENTS.items():
        score += binaries[short] * weight
    score[~valid_all] = _SCORE_NODATA
    return binaries, score, stats


def polygonize_targets(
    score: np.ndarray,
    profile,  # type: ignore[no-untyped-def]
    *,
    params: AsterParams,
):  # type: ignore[no-untyped-def]
    """Support polygons from score >= the frozen ``params.score_min``.

    Returns a GeoDataFrame (possibly empty) with target_score / confidence / area_ha and the
    support-evidence stamps.
    """
    import geopandas as gpd
    from rasterio.features import shapes as rio_shapes
    from shapely.geometry import shape as shp_shape

    mask = (score >= params.score_min) & (score != _SCORE_NODATA)
    records: list[dict[str, object]] = []
    geoms = []  # shapely geometries (inferred; gpd stubs reject list[object])
    for geom, value in rio_shapes(score, mask=mask, transform=profile["transform"]):
        poly = shp_shape(geom)
        area_ha = poly.area / 10_000.0
        if area_ha < params.min_area_ha:
            continue
        s = int(value)
        records.append(
            {
                "target_score": s,
                "confidence": "High" if s >= 5 else "Moderate" if s >= 3 else "Low",
                "area_ha": round(area_ha, 3),
                "validation_status": "Support evidence only",
                "limitation": "Not ore proof; requires field/lab validation",
                "source": "ASTER L1B #73 — frozen repository band-ratio support scoring",
            }
        )
        geoms.append(poly)
    return gpd.GeoDataFrame(records, geometry=geoms, crs=profile["crs"])


# --------------------------------------------------------------------------- #
# raster writers (float index / uint8 score on the common grid)
# --------------------------------------------------------------------------- #


def write_index_raster(
    array: np.ndarray,
    profile,  # type: ignore[no-untyped-def]
    dst: Path,
    *,
    compress: str = "DEFLATE",
) -> Path:
    """Write a float32 index (NaN -> -9999 nodata) or uint8 binary/score raster as COG."""
    import rasterio

    from buduunkhad.core import raster_writers

    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    prof = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "crs": profile["crs"],
        "transform": profile["transform"],
    }
    if array.dtype == np.uint8:
        prof.update(dtype="uint8", nodata=_SCORE_NODATA)
        data = array
        predictor = None
    else:
        prof.update(dtype="float32", nodata=-9999.0)
        data = np.where(np.isnan(array), -9999.0, array).astype("float32")
        predictor = "3"
    tmp = dst.with_suffix(".tmp.tif")
    with rasterio.open(tmp, "w", **prof) as out:
        out.write(data, 1)
    try:
        raster_writers.write_cog(tmp, dst, compress=compress, predictor=predictor)
    finally:
        tmp.unlink(missing_ok=True)
    return dst
