"""First-pass lineament extraction from multi-azimuth hillshades (deterministic CV).

Canny edge detection on each azimuth hillshade, a multi-azimuth consensus stack (an edge must
appear under >= 2 illumination directions — single-azimuth edges are mostly illumination
artefacts), then a probabilistic Hough transform to straight segments, georeferenced via the
raster transform and filtered by length.

**Every output is a MACHINE DRAFT of an interpretive product** — the parameters are
deterministic, but "is this line a fault or a road?" is geology. Outputs are stamped
"Machine draft — requires geologist review" and must never feed scoring without that review.
scikit-image is an optional ``[dem]``-extra dependency; callers degrade gracefully (skip with
a note) when :class:`LineamentError` is raised.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np

DRAFT_VALIDATION = "Machine draft — requires geologist review"
DRAFT_LIMITATION = (
    "Automated edge/Hough extraction; may include roads/rivers/artefacts — not a structural "
    "interpretation until reviewed; never ore proof"
)


class LineamentError(RuntimeError):
    """Raised when lineament extraction cannot run (scikit-image missing, bad inputs)."""


@dataclass(frozen=True)
class LineamentParams:
    canny_sigma: float = 2.0
    min_azimuth_support: int = 2  # edge must appear under >= this many illumination azimuths
    hough_threshold: int = 10
    hough_line_length_px: int = 40  # ~500 m at 12.5 m pixels
    hough_line_gap_px: int = 3
    min_length_m: float = 500.0


def extract_lineaments(hillshade_paths: list[Path], *, params: LineamentParams = LineamentParams()):
    """Draft lineament segments from >= 2 co-registered azimuth hillshades.

    Returns a GeoDataFrame of LineStrings (length_m, azimuth_deg, n_azimuths + draft stamps)
    in the hillshades' CRS.
    """
    try:
        from skimage.feature import canny  # ty: ignore[unresolved-import]
        from skimage.transform import (  # ty: ignore[unresolved-import]
            probabilistic_hough_line,
        )
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise LineamentError("scikit-image not installed (pip install scikit-image)") from exc

    import geopandas as gpd
    import rasterio
    from affine import Affine
    from shapely.geometry import LineString

    if len(hillshade_paths) < 2:
        raise LineamentError(f"need >= 2 azimuth hillshades, got {len(hillshade_paths)}")

    edge_stack: np.ndarray | None = None
    transform: Affine | None = None
    crs = None
    shape: tuple[int, int] | None = None
    for path in sorted(hillshade_paths):
        with rasterio.open(path) as ds:
            arr = ds.read(1).astype("float32")
            nodata = ds.nodata
            if transform is None:
                transform, crs, shape = ds.transform, ds.crs, arr.shape
            elif arr.shape != shape:
                raise LineamentError(f"hillshade grids differ: {path.name} is {arr.shape}")
        invalid = np.isnan(arr) if nodata is None else (arr == nodata) | np.isnan(arr)
        arr[invalid] = float(np.nanmedian(arr[~invalid])) if (~invalid).any() else 0.0
        lo, hi = np.percentile(arr, (2, 98))
        norm = np.clip((arr - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
        edges = canny(norm, sigma=params.canny_sigma)
        edges[invalid] = False
        edge_stack = edges.astype("uint8") if edge_stack is None else edge_stack + edges

    assert edge_stack is not None
    assert transform is not None
    consensus = edge_stack >= params.min_azimuth_support
    segments = probabilistic_hough_line(
        consensus,
        threshold=params.hough_threshold,
        line_length=params.hough_line_length_px,
        line_gap=params.hough_line_gap_px,
    )

    records: list[dict[str, object]] = []
    geoms = []
    for (c0, r0), (c1, r1) in segments:
        x0, y0 = cast(tuple[float, float], transform * (c0 + 0.5, r0 + 0.5))
        x1, y1 = cast(tuple[float, float], transform * (c1 + 0.5, r1 + 0.5))
        line = LineString([(x0, y0), (x1, y1)])
        if line.length < params.min_length_m:
            continue
        azimuth = (math.degrees(math.atan2(x1 - x0, y1 - y0))) % 180.0
        records.append(
            {
                "length_m": round(line.length, 1),
                "azimuth_deg": round(azimuth, 1),
                "n_azimuths": int(len(hillshade_paths)),
                "validation_status": DRAFT_VALIDATION,
                "limitation": DRAFT_LIMITATION,
                "source": "multi-azimuth hillshade Canny+Hough (deterministic first pass)",
            }
        )
        geoms.append(line)
    return gpd.GeoDataFrame(records, geometry=geoms, crs=crs)  # ty: ignore[no-matching-overload]
