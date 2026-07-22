"""Deterministic registration of immutable raster source assets."""

from __future__ import annotations

import math
import mimetypes
from pathlib import Path
from typing import Literal

import rasterio
from rasterio.errors import RasterioError

from buduunkhad.ai.fingerprint import sha256_file, sha256_value
from buduunkhad.geospatial_ai.manifests import AffineRecord, SourceAssetRecord
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.render import render_pdf_page

_RASTER_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}
_DRIVER_MEDIA_TYPES = {
    "BMP": "image/bmp",
    "GTiff": "image/tiff",
    "JPEG": "image/jpeg",
    "PNG": "image/png",
}


class SourceAssetError(ValueError):
    """Source registration failed without modifying the source."""


def register_raster_source(
    path: Path,
    *,
    roots: StorageRoots,
    target_crs: str,
) -> SourceAssetRecord:
    source = roots.assert_snapshot_source(path)
    if source.suffix.casefold() not in _RASTER_EXTENSIONS:
        raise SourceAssetError(f"unsupported raster source type: {source.suffix}")
    digest = sha256_file(source)
    return _raster_record(
        source,
        digest=digest,
        relative_path=source.relative_to(roots.require_snapshot_root()).as_posix(),
        target_crs=target_crs,
    )


def register_pdf_page(
    path: Path,
    *,
    roots: StorageRoots,
    run_id: str,
    target_crs: str,
    page_number: int = 1,
    render_scale: float = 1.0,
) -> SourceAssetRecord:
    """Render one immutable snapshot PDF page into the run workspace."""

    source = roots.assert_snapshot_source(path)
    if source.suffix.casefold() != ".pdf":
        raise SourceAssetError("document rendering currently supports PDF sources")
    if page_number < 1 or not math.isfinite(render_scale) or render_scale <= 0:
        raise SourceAssetError("PDF page number and render scale must be positive")
    original_digest = sha256_file(source)
    identity = sha256_value(
        {
            "source_sha256": original_digest,
            "page_number": page_number,
            "render_scale": render_scale,
            "renderer": "pypdfium2",
        }
    )
    run_directory = roots.run_directory(run_id, create=True)
    rendered = roots.assert_writable(
        run_directory / "rendered-pages" / f"page-{identity[:32]}.png",
        run_id=run_id,
    )
    if rendered.exists():
        raise SourceAssetError("rendered document page already exists")
    render_pdf_page(source, rendered, page_number=page_number, scale=render_scale)
    return _raster_record(
        rendered,
        digest=sha256_file(rendered),
        relative_path=rendered.relative_to(run_directory).as_posix(),
        target_crs=target_crs,
        source_root_id="run-work",
        run_id=run_id,
        original_source_relative_path=source.relative_to(roots.require_snapshot_root()).as_posix(),
        original_source_sha256=original_digest,
        page_number=page_number,
        render_scale=render_scale,
    )


def _raster_record(
    source: Path,
    *,
    digest: str,
    relative_path: str,
    target_crs: str,
    source_root_id: Literal["snapshot", "run-work"] = "snapshot",
    run_id: str | None = None,
    original_source_relative_path: str | None = None,
    original_source_sha256: str | None = None,
    page_number: int | None = None,
    render_scale: float | None = None,
) -> SourceAssetRecord:
    try:
        with rasterio.open(source) as dataset:
            transform = dataset.transform
            source_crs = dataset.crs.to_string() if dataset.crs else None
            nodata, nodata_kind = _nodata_record(dataset.nodata)
            record = SourceAssetRecord(
                asset_id=f"source-{digest[:24]}",
                source_root_id=source_root_id,
                run_id=run_id,
                relative_path=relative_path,
                sha256=digest,
                size=source.stat().st_size,
                media_type=_DRIVER_MEDIA_TYPES.get(
                    dataset.driver,
                    mimetypes.guess_type(source.name)[0] or "application/octet-stream",
                ),
                width=dataset.width,
                height=dataset.height,
                band_count=dataset.count,
                dtype=dataset.dtypes[0],
                affine=AffineRecord(
                    a=transform.a,
                    b=transform.b,
                    c=transform.c,
                    d=transform.d,
                    e=transform.e,
                    f=transform.f,
                ),
                source_crs=source_crs,
                target_crs=target_crs,
                nodata=nodata,
                nodata_kind=nodata_kind,
                original_source_relative_path=original_source_relative_path,
                original_source_sha256=original_source_sha256,
                page_number=page_number,
                render_scale=render_scale,
            )
    except (RasterioError, OSError) as exc:
        raise SourceAssetError(f"raster source cannot be opened: {source.name}") from exc
    return record


def _nodata_record(
    value: float | int | None,
) -> tuple[float | None, Literal["none", "value", "nan", "positive-infinity", "negative-infinity"]]:
    if value is None:
        return None, "none"
    numeric = float(value)
    if math.isnan(numeric):
        return None, "nan"
    if numeric == math.inf:
        return None, "positive-infinity"
    if numeric == -math.inf:
        return None, "negative-infinity"
    return numeric, "value"


def verify_registered_source(record: SourceAssetRecord, *, roots: StorageRoots) -> Path:
    if record.source_root_id == "snapshot":
        source = roots.require_snapshot_root() / Path(record.relative_path)
        source = roots.assert_snapshot_source(source)
    else:
        if record.run_id is None:
            raise SourceAssetError("rendered work source has no run identity")
        run_directory = roots.run_directory(record.run_id)
        source = roots.assert_writable(
            run_directory / Path(record.relative_path), run_id=record.run_id
        ).resolve(strict=True)
        if record.original_source_relative_path is None:
            raise SourceAssetError("rendered work source has no original source path")
        original = roots.assert_snapshot_source(
            roots.require_snapshot_root() / record.original_source_relative_path
        )
        if sha256_file(original) != record.original_source_sha256:
            raise SourceAssetError("original document bytes changed after page rendering")
    if source.stat().st_size != record.size or sha256_file(source) != record.sha256:
        raise SourceAssetError("registered source bytes changed after request preparation")
    return source
