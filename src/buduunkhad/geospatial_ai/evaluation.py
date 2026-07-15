"""Offline evaluation of AI_DRAFT layers against an external reference dataset."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

import fiona
from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from buduunkhad.geospatial_ai.path_safety import StorageRoots


class EvaluationError(ValueError):
    """Candidate or reference data cannot be evaluated safely."""


class EvaluationSettings(BaseModel):
    """Explicit spatial matching settings; no geological threshold is implicit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    match_distance: float = Field(ge=0)
    line_buffer: float = Field(ge=0)
    minimum_iou: float = Field(ge=0, le=1)


class LayerMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    layer: str
    candidate_count: int
    reference_count: int
    valid_geometry_rate: float
    matched_candidate_count: int
    matched_reference_count: int
    precision: float
    recall: float
    mean_line_overlap: float | None = None
    mean_hausdorff_distance: float | None = None
    mean_polygon_iou: float | None = None
    mean_position_error: float | None = None
    unmatched_candidate_ids: tuple[str, ...]
    unmatched_reference_ids: tuple[str, ...]


class EvaluationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate_path: str
    reference_path: str
    settings: EvaluationSettings
    layers: tuple[LayerMetrics, ...]


@dataclass(frozen=True)
class _Feature:
    identity: str
    geometry: BaseGeometry


def evaluate_geopackages(
    candidate_path: Path,
    reference_path: Path,
    *,
    layers: tuple[str, ...],
    settings: EvaluationSettings,
    roots: StorageRoots,
    run_id: str,
) -> tuple[Path, Path]:
    """Evaluate selected layers and write deterministic JSON and CSV reports."""

    candidate = roots.assert_writable(candidate_path, run_id=run_id).resolve(strict=True)
    reference = roots.assert_evaluation_source(reference_path)
    output_directory = roots.assert_writable(
        roots.run_directory(run_id) / "evaluation", run_id=run_id
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    reports = tuple(
        _evaluate_layer(
            layer,
            _read_layer(candidate, layer),
            _read_layer(reference, layer),
            settings,
        )
        for layer in layers
    )
    report = EvaluationReport(
        candidate_path=candidate.relative_to(roots.run_directory(run_id)).as_posix(),
        reference_path=reference.relative_to(roots.require_eval_root()).as_posix(),
        settings=settings,
        layers=reports,
    )
    json_path = output_directory / "evaluation.json"
    csv_path = output_directory / "evaluation.csv"
    if json_path.exists() or csv_path.exists():
        raise EvaluationError("evaluation report already exists")
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(LayerMetrics.model_fields))
        writer.writeheader()
        for metrics in reports:
            row = metrics.model_dump(mode="json")
            row["unmatched_candidate_ids"] = json.dumps(row["unmatched_candidate_ids"])
            row["unmatched_reference_ids"] = json.dumps(row["unmatched_reference_ids"])
            writer.writerow(row)
    return json_path, csv_path


def _read_layer(path: Path, layer: str) -> tuple[_Feature, ...]:
    try:
        with fiona.open(path, layer=layer) as collection:
            features = []
            for index, record in enumerate(collection):
                geometry_data = record["geometry"]
                geometry = (
                    shape({"type": "GeometryCollection", "geometries": []})
                    if geometry_data is None
                    else shape(geometry_data)
                )
                properties = record["properties"]
                identity = str(
                    properties.get("feature_id")
                    or properties.get("id")
                    or record.get("id")
                    or index
                )
                features.append(_Feature(identity=identity, geometry=geometry))
    except (OSError, ValueError) as exc:
        raise EvaluationError(f"cannot read evaluation layer {layer!r}") from exc
    return tuple(features)


def _evaluate_layer(
    layer: str,
    candidates: tuple[_Feature, ...],
    references: tuple[_Feature, ...],
    settings: EvaluationSettings,
) -> LayerMetrics:
    valid = sum(not item.geometry.is_empty and item.geometry.is_valid for item in candidates)
    pairs = _match(candidates, references, settings)
    matched_candidates = {candidate_index for candidate_index, _, _ in pairs}
    matched_references = {reference_index for _, reference_index, _ in pairs}
    line_overlaps: list[float] = []
    hausdorff: list[float] = []
    polygon_iou: list[float] = []
    position_errors: list[float] = []
    for candidate_index, reference_index, distance in pairs:
        candidate = candidates[candidate_index].geometry
        reference = references[reference_index].geometry
        if _is_line(candidate) and _is_line(reference):
            buffered = reference.buffer(settings.line_buffer)
            denominator = candidate.length
            line_overlaps.append(
                candidate.intersection(buffered).length / denominator if denominator else 0
            )
            hausdorff.append(candidate.hausdorff_distance(reference))
        elif _is_polygon(candidate) and _is_polygon(reference):
            union = candidate.union(reference).area
            polygon_iou.append(candidate.intersection(reference).area / union if union else 0)
            hausdorff.append(candidate.hausdorff_distance(reference))
        else:
            position_errors.append(distance)
    candidate_count = len(candidates)
    reference_count = len(references)
    return LayerMetrics(
        layer=layer,
        candidate_count=candidate_count,
        reference_count=reference_count,
        valid_geometry_rate=valid / candidate_count if candidate_count else 1.0,
        matched_candidate_count=len(matched_candidates),
        matched_reference_count=len(matched_references),
        precision=len(matched_candidates) / candidate_count if candidate_count else 1.0,
        recall=len(matched_references) / reference_count if reference_count else 1.0,
        mean_line_overlap=_mean(line_overlaps),
        mean_hausdorff_distance=_mean(hausdorff),
        mean_polygon_iou=_mean(polygon_iou),
        mean_position_error=_mean(position_errors),
        unmatched_candidate_ids=tuple(
            item.identity
            for index, item in enumerate(candidates)
            if index not in matched_candidates
        ),
        unmatched_reference_ids=tuple(
            item.identity
            for index, item in enumerate(references)
            if index not in matched_references
        ),
    )


def _match(
    candidates: tuple[_Feature, ...],
    references: tuple[_Feature, ...],
    settings: EvaluationSettings,
) -> tuple[tuple[int, int, float], ...]:
    options: list[tuple[float, int, int]] = []
    for candidate_index, candidate in enumerate(candidates):
        for reference_index, reference in enumerate(references):
            if candidate.geometry.is_empty or reference.geometry.is_empty:
                continue
            distance = candidate.geometry.centroid.distance(reference.geometry.centroid)
            if _is_polygon(candidate.geometry) and _is_polygon(reference.geometry):
                union = candidate.geometry.union(reference.geometry).area
                iou = (
                    candidate.geometry.intersection(reference.geometry).area / union if union else 0
                )
                eligible = iou >= settings.minimum_iou
            else:
                eligible = (
                    candidate.geometry.distance(reference.geometry) <= settings.match_distance
                )
            if eligible:
                options.append((distance, candidate_index, reference_index))
    used_candidates: set[int] = set()
    used_references: set[int] = set()
    matches: list[tuple[int, int, float]] = []
    for distance, candidate_index, reference_index in sorted(options):
        if candidate_index in used_candidates or reference_index in used_references:
            continue
        if not math.isfinite(distance):
            raise EvaluationError("non-finite evaluation distance")
        used_candidates.add(candidate_index)
        used_references.add(reference_index)
        matches.append((candidate_index, reference_index, distance))
    return tuple(matches)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _is_line(geometry: BaseGeometry) -> bool:
    return geometry.geom_type in {"LineString", "MultiLineString"}


def _is_polygon(geometry: BaseGeometry) -> bool:
    return geometry.geom_type in {"Polygon", "MultiPolygon"}
