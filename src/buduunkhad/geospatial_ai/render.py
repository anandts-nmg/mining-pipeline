"""Deterministic local rendering for raster windows and optional PDF pages."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import rasterio
from rasterio.errors import RasterioError
from rasterio.windows import Window


class RenderingError(RuntimeError):
    """A local source could not be rendered safely."""


def render_raster_window(
    source: Path,
    destination: Path,
    *,
    window: Window,
    bands: Sequence[int] | None = None,
) -> tuple[float, Path | None]:
    """Render a source window to RGB PNG and optionally write its valid-data mask."""

    try:
        with rasterio.open(source) as dataset:
            indexes = tuple(bands or _default_bands(dataset.count))
            if any(index < 1 or index > dataset.count for index in indexes):
                raise RenderingError("render band index is outside the source raster")
            data = dataset.read(indexes=indexes, window=window, masked=True)
            mask = dataset.dataset_mask(window=window)
    except (RasterioError, OSError, ValueError) as exc:
        raise RenderingError("raster tile rendering failed") from exc
    rgb = _to_rgb(data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _write_png(destination, rgb)
    valid_fraction = float(np.count_nonzero(mask)) / float(mask.size)
    mask_path: Path | None = None
    if valid_fraction < 1.0:
        mask_path = destination.with_name(destination.stem + "_valid_mask.png")
        _write_png(mask_path, mask[np.newaxis, :, :])
    return valid_fraction, mask_path


def render_pdf_page(
    source: Path, destination: Path, *, page_number: int, scale: float = 1.0
) -> Path:
    """Render one PDF page when the optional local renderer is installed."""

    if page_number < 1 or scale <= 0:
        raise RenderingError("PDF page number and render scale must be positive")
    try:
        pdfium = importlib.import_module("pypdfium2")
    except ImportError as exc:
        raise RenderingError(
            "PDF rendering requires the optional 'documents' project extra"
        ) from exc
    try:
        document = pdfium.PdfDocument(str(source))
        page = document[page_number - 1]
        bitmap = page.render(scale=scale)
        destination.parent.mkdir(parents=True, exist_ok=True)
        bitmap.to_pil().save(destination, format="PNG")
    except Exception as exc:
        raise RenderingError("local PDF page rendering failed") from exc
    return destination


def _default_bands(count: int) -> tuple[int, ...]:
    if count < 1:
        raise RenderingError("raster has no bands")
    return (1, 2, 3) if count >= 3 else (1,)


def _to_rgb(data: np.ma.MaskedArray) -> np.ndarray:
    channels: list[np.ndarray] = []
    for band in data:
        values = np.asarray(band.filled(0))
        valid = np.asarray(~np.ma.getmaskarray(band), dtype=bool)
        if values.dtype == np.uint8:
            scaled = values.astype(np.uint8, copy=False)
        elif np.any(valid):
            minimum = float(np.min(values[valid]))
            maximum = float(np.max(values[valid]))
            if maximum == minimum:
                scaled = np.zeros(values.shape, dtype=np.uint8)
            else:
                scaled = np.clip((values - minimum) * 255.0 / (maximum - minimum), 0, 255).astype(
                    np.uint8
                )
        else:
            scaled = np.zeros(values.shape, dtype=np.uint8)
        scaled[~valid] = 0
        channels.append(scaled)
    if len(channels) == 1:
        channels *= 3
    return np.stack(channels[:3], axis=0)


def _write_png(path: Path, data: np.ndarray) -> None:
    profile = {
        "driver": "PNG",
        "height": int(data.shape[1]),
        "width": int(data.shape[2]),
        "count": int(data.shape[0]),
        "dtype": "uint8",
    }
    try:
        with rasterio.open(path, "w", **profile) as destination:
            destination.write(data.astype(np.uint8, copy=False))
    except (RasterioError, OSError) as exc:
        raise RenderingError("PNG tile writing failed") from exc
