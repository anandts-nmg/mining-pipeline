"""Deterministic tile-pixel to source/world coordinate conversion."""

from __future__ import annotations

import math

from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry

from buduunkhad.ai.contracts import PixelGeometry, PixelLineString, PixelPoint, PixelPolygon
from buduunkhad.geospatial_ai.manifests import SourceAssetRecord, TileRecord


class PixelWorldError(ValueError):
    """Pixel geometry cannot be transformed without ambiguity or clamping."""


def tile_pixel_to_world(
    x: float,
    y: float,
    *,
    tile: TileRecord,
    source: SourceAssetRecord,
) -> tuple[float, float]:
    if not math.isfinite(x) or not math.isfinite(y):
        raise PixelWorldError("pixel coordinate is non-finite")
    if not (0 <= x <= tile.width and 0 <= y <= tile.height):
        raise PixelWorldError("pixel coordinate lies outside its source tile")
    source_x = tile.x_offset + x
    source_y = tile.y_offset + y
    if not (0 <= source_x <= source.width and 0 <= source_y <= source.height):
        raise PixelWorldError("pixel coordinate lies outside the source raster")
    affine = source.affine
    determinant = affine.a * affine.e - affine.b * affine.d
    if not math.isfinite(determinant) or determinant == 0:
        raise PixelWorldError("source affine transform is singular or unsafe")
    map_x = affine.a * source_x + affine.b * source_y + affine.c
    map_y = affine.d * source_x + affine.e * source_y + affine.f
    if not math.isfinite(map_x) or not math.isfinite(map_y):
        raise PixelWorldError("source affine transform produced non-finite coordinates")
    if source.source_crs is None:
        raise PixelWorldError("source raster has no CRS")
    try:
        source_crs = CRS.from_user_input(source.source_crs)
        target_crs = CRS.from_user_input(source.target_crs)
    except Exception as exc:
        raise PixelWorldError("source or target CRS is unsupported") from exc
    try:
        if source_crs == target_crs:
            world_x, world_y = map_x, map_y
        else:
            transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
            world_x, world_y = transformer.transform(map_x, map_y, errcheck=True)
    except Exception as exc:
        raise PixelWorldError("CRS transformation failed") from exc
    if not math.isfinite(world_x) or not math.isfinite(world_y):
        raise PixelWorldError("CRS transformation produced non-finite coordinates")
    return float(world_x), float(world_y)


def transform_pixel_geometry(
    geometry: PixelGeometry,
    *,
    tile: TileRecord,
    source: SourceAssetRecord,
) -> BaseGeometry:
    def convert(point: tuple[float, float]) -> tuple[float, float]:
        return tile_pixel_to_world(point[0], point[1], tile=tile, source=source)

    if isinstance(geometry, PixelPoint):
        return Point(convert(geometry.coordinates))
    if isinstance(geometry, PixelLineString):
        coordinates = tuple(convert(point) for point in geometry.coordinates)
        if len(set(coordinates)) < 2:
            raise PixelWorldError("line geometry is degenerate after transformation")
        return LineString(coordinates)
    if isinstance(geometry, PixelPolygon):
        rings = tuple(tuple(convert(point) for point in ring) for ring in geometry.coordinates)
        if any(len(set(ring[:-1])) < 3 for ring in rings):
            raise PixelWorldError("polygon geometry is degenerate after transformation")
        return Polygon(rings[0], holes=rings[1:])
    raise PixelWorldError(f"unsupported pixel geometry: {type(geometry).__name__}")


def transformed_source_extent(source: SourceAssetRecord) -> Polygon:
    """Return the target-CRS footprint of the complete source raster."""

    synthetic = TileRecord(
        tile_id="source-extent",
        source_asset_id=source.asset_id,
        source_sha256=source.sha256,
        band_identity="extent",
        x_offset=0,
        y_offset=0,
        width=source.width,
        height=source.height,
        overlap=0,
        image_relative_path="extent",
        image_sha256="0" * 64,
        valid_fraction=1,
    )
    ring = (
        tile_pixel_to_world(0, 0, tile=synthetic, source=source),
        tile_pixel_to_world(source.width, 0, tile=synthetic, source=source),
        tile_pixel_to_world(source.width, source.height, tile=synthetic, source=source),
        tile_pixel_to_world(0, source.height, tile=synthetic, source=source),
        tile_pixel_to_world(0, 0, tile=synthetic, source=source),
    )
    return Polygon(ring)
