"""Stable deterministic image-tile creation for registered raster sources."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator
from rasterio.windows import Window

from buduunkhad.ai.fingerprint import sha256_file, sha256_value
from buduunkhad.geospatial_ai.manifests import SourceAssetRecord, TileRecord, TileSetManifest
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.render import render_raster_window
from buduunkhad.geospatial_ai.source_assets import verify_registered_source

_RENDERING_VERSION = "png-per-tile-minmax-v1"


class TileParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    width: int = Field(default=1024, gt=0)
    height: int = Field(default=1024, gt=0)
    overlap: int = Field(default=128, ge=0)
    bands: tuple[int, ...] = ()

    @model_validator(mode="after")
    def _valid_overlap(self) -> TileParameters:
        if self.overlap >= min(self.width, self.height):
            raise ValueError("tile overlap must be smaller than tile dimensions")
        return self


def create_tiles(
    source: SourceAssetRecord,
    *,
    parameters: TileParameters,
    package_directory: Path,
    roots: StorageRoots,
    run_id: str,
) -> TileSetManifest:
    source_path = verify_registered_source(source, roots=roots)
    output = roots.assert_writable(package_directory, run_id=run_id)
    tile_directory = roots.assert_writable(output / "tiles", run_id=run_id)
    tile_directory.mkdir(parents=True, exist_ok=True)
    tiles: list[TileRecord] = []
    for y_offset in _starts(source.height, parameters.height, parameters.overlap):
        height = min(parameters.height, source.height - y_offset)
        for x_offset in _starts(source.width, parameters.width, parameters.overlap):
            width = min(parameters.width, source.width - x_offset)
            band_identity = (
                "bands:" + ",".join(str(value) for value in parameters.bands)
                if parameters.bands
                else "bands:auto-rgb"
            )
            tile_id = tile_identity(
                source_sha256=source.sha256,
                band_identity=band_identity,
                x_offset=x_offset,
                y_offset=y_offset,
                width=width,
                height=height,
                overlap=parameters.overlap,
            )
            image = tile_directory / f"{tile_id}.png"
            valid_fraction, mask = render_raster_window(
                source_path,
                image,
                window=Window.from_slices(
                    (y_offset, y_offset + height),
                    (x_offset, x_offset + width),
                ),
                bands=parameters.bands or None,
            )
            tiles.append(
                TileRecord(
                    tile_id=tile_id,
                    source_asset_id=source.asset_id,
                    source_sha256=source.sha256,
                    band_identity=band_identity,
                    x_offset=x_offset,
                    y_offset=y_offset,
                    width=width,
                    height=height,
                    overlap=parameters.overlap,
                    image_relative_path=image.relative_to(output).as_posix(),
                    image_sha256=sha256_file(image),
                    valid_mask_relative_path=mask.relative_to(output).as_posix() if mask else None,
                    valid_mask_sha256=sha256_file(mask) if mask else None,
                    valid_fraction=valid_fraction,
                )
            )
    return TileSetManifest(
        source=source,
        tile_width=parameters.width,
        tile_height=parameters.height,
        overlap=parameters.overlap,
        rendering=(("format", "png"), ("scaling", _RENDERING_VERSION)),
        tiles=tuple(tiles),
    )


def _starts(length: int, tile_size: int, overlap: int) -> tuple[int, ...]:
    step = tile_size - overlap
    return tuple(range(0, length, step))


def tile_identity(
    *,
    source_sha256: str,
    band_identity: str,
    x_offset: int,
    y_offset: int,
    width: int,
    height: int,
    overlap: int,
) -> str:
    return (
        "tile-"
        + sha256_value(
            {
                "source_sha256": source_sha256,
                "band_identity": band_identity,
                "bounds": (x_offset, y_offset, width, height),
                "rendering": (_RENDERING_VERSION, overlap),
            }
        )[:32]
    )


def validate_tile_manifest(manifest: TileSetManifest) -> None:
    """Recompute the deterministic tiling plan and every stable tile identity."""

    if manifest.rendering != (("format", "png"), ("scaling", _RENDERING_VERSION)):
        raise ValueError("tile manifest uses unsupported rendering parameters")
    parameters = TileParameters(
        width=manifest.tile_width,
        height=manifest.tile_height,
        overlap=manifest.overlap,
    )
    expected_bounds = tuple(
        (
            x_offset,
            y_offset,
            min(parameters.width, manifest.source.width - x_offset),
            min(parameters.height, manifest.source.height - y_offset),
        )
        for y_offset in _starts(manifest.source.height, parameters.height, parameters.overlap)
        for x_offset in _starts(manifest.source.width, parameters.width, parameters.overlap)
    )
    actual_bounds = tuple(
        (tile.x_offset, tile.y_offset, tile.width, tile.height) for tile in manifest.tiles
    )
    if actual_bounds != expected_bounds:
        raise ValueError("tile manifest does not match the deterministic source tiling plan")
    band_identities = {tile.band_identity for tile in manifest.tiles}
    if len(band_identities) != 1:
        raise ValueError("tile manifest contains inconsistent band identities")
    paths: set[str] = set()
    identities: set[str] = set()
    for tile in manifest.tiles:
        if (
            tile.source_asset_id != manifest.source.asset_id
            or tile.source_sha256 != manifest.source.sha256
            or tile.overlap != manifest.overlap
        ):
            raise ValueError("tile manifest source binding is inconsistent")
        expected_identity = tile_identity(
            source_sha256=tile.source_sha256,
            band_identity=tile.band_identity,
            x_offset=tile.x_offset,
            y_offset=tile.y_offset,
            width=tile.width,
            height=tile.height,
            overlap=tile.overlap,
        )
        if tile.tile_id != expected_identity:
            raise ValueError("tile manifest contains an invalid stable tile identity")
        relative_paths = (tile.image_relative_path, tile.valid_mask_relative_path)
        for value in relative_paths:
            if value is None:
                continue
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or value in paths:
                raise ValueError("tile manifest contains an unsafe or duplicate relative path")
            paths.add(value)
        if tile.tile_id in identities:
            raise ValueError("tile manifest contains duplicate tile identities")
        identities.add(tile.tile_id)
