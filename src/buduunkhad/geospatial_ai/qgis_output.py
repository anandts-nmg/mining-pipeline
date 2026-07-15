"""Portable QGIS project generation for source imagery and AI_DRAFT layers."""

from __future__ import annotations

import os
from pathlib import Path

from buduunkhad.core.qgis_project import (
    QgzLayer,
    line_symbol,
    point_symbol,
    polygon_outline,
    write_layered_qgz,
)
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.schemas import DraftLayerName

_STYLES = {
    DraftLayerName.GEOLOGY_UNITS: polygon_outline("80,130,180,255", 0.5),
    DraftLayerName.FAULTS_STRUCTURES: line_symbol("215,25,28,255", 0.6),
    DraftLayerName.INTRUSIVE_CONTACTS: line_symbol("120,60,160,255", 0.5, dash=True),
    DraftLayerName.DYKES_VEINS: line_symbol("255,140,0,255", 0.5),
    DraftLayerName.MINERAL_OCCURRENCES: point_symbol("255,215,0,255", 3.0),
    DraftLayerName.ALTERATION_ZONES: polygon_outline("255,165,0,255", 0.5, dash=True),
    DraftLayerName.PROSPECT_PROPOSALS: polygon_outline("220,0,0,255", 0.8, dash=True),
}


def write_ai_draft_qgz(
    path: Path,
    *,
    gpkg: Path,
    source_raster: Path,
    epsg: int,
    roots: StorageRoots,
    run_id: str,
) -> Path:
    project = roots.assert_writable(path, run_id=run_id)
    if project.exists():
        raise ValueError("AI_DRAFT QGIS project already exists")
    relative_gpkg = _relative(project.parent, gpkg)
    relative_source = _relative(project.parent, source_raster)
    layers = [
        QgzLayer(
            name="Source Imagery",
            source=relative_source,
            geometry="Raster",
            group="Source Imagery",
            provider="gdal",
            visible=True,
        )
    ]
    geometry = {
        DraftLayerName.GEOLOGY_UNITS: "Polygon",
        DraftLayerName.FAULTS_STRUCTURES: "LineString",
        DraftLayerName.INTRUSIVE_CONTACTS: "LineString",
        DraftLayerName.DYKES_VEINS: "LineString",
        DraftLayerName.MINERAL_OCCURRENCES: "Point",
        DraftLayerName.ALTERATION_ZONES: "Polygon",
        DraftLayerName.PROSPECT_PROPOSALS: "Polygon",
    }
    for layer in DraftLayerName:
        layers.append(
            QgzLayer(
                name=layer.value,
                source=f"{relative_gpkg}|layername={layer.value}",
                geometry=geometry[layer],
                symbol=_STYLES[layer],
                group="AI Draft",
                provider="ogr",
                visible=True,
            )
        )
    layers.append(
        QgzLayer(
            name="validation_findings",
            source=f"{relative_gpkg}|layername=validation_findings",
            geometry="Point",
            symbol=point_symbol("255,0,255,255", 2.5),
            group="AI Validation",
            provider="ogr",
            visible=True,
        )
    )
    return write_layered_qgz(
        project,
        epsg=epsg,
        title=f"Buduunkhad {run_id} AI_DRAFT",
        layers=layers,
    )


def _relative(base: Path, target: Path) -> str:
    return os.path.relpath(target.resolve(), base.resolve()).replace("\\", "/")
