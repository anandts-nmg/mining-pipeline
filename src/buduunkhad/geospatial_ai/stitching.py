"""Deterministic overlap de-duplication for tiled draft features."""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True, slots=True)
class StitchCandidate:
    feature_id: str
    confidence: float
    geometry: BaseGeometry


@dataclass(frozen=True, slots=True)
class StitchResult:
    kept: tuple[StitchCandidate, ...]
    duplicate_feature_ids: tuple[str, ...]


def deduplicate_candidates(
    candidates: tuple[StitchCandidate, ...],
    *,
    overlap_threshold: float,
) -> StitchResult:
    if not 0 < overlap_threshold <= 1:
        raise ValueError("overlap threshold must be greater than zero and at most one")
    ordered = sorted(candidates, key=lambda value: (-value.confidence, value.feature_id))
    kept: list[StitchCandidate] = []
    duplicates: list[str] = []
    for candidate in ordered:
        if any(_overlap(candidate.geometry, prior.geometry) >= overlap_threshold for prior in kept):
            duplicates.append(candidate.feature_id)
        else:
            kept.append(candidate)
    return StitchResult(kept=tuple(kept), duplicate_feature_ids=tuple(sorted(duplicates)))


def _overlap(left: BaseGeometry, right: BaseGeometry) -> float:
    if left.equals(right):
        return 1.0
    if left.area > 0 and right.area > 0:
        union = left.union(right).area
        return float(left.intersection(right).area / union) if union else 0.0
    denominator = max(left.length, right.length)
    return float(left.intersection(right).length / denominator) if denominator else 0.0
