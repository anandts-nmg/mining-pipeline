"""Deterministic geometry validation and optional recorded repair."""

from __future__ import annotations

import math
from collections.abc import Iterable

from pydantic import Field
from shapely import make_valid
from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

from buduunkhad.ai.contracts import FrozenModel
from buduunkhad.ai.fingerprint import sha256_bytes


class GeometryValidationError(ValueError):
    """Geometry validation or deterministic repair failed."""


class ValidationFinding(FrozenModel):
    code: str
    message: str
    severity: str


class GeometryRepairRecord(FrozenModel):
    algorithm: str
    tolerance: float = Field(ge=0)
    original_geometry_sha256: str
    repaired_geometry_sha256: str
    area_before: float
    area_after: float
    length_before: float
    length_after: float
    maximum_displacement: float


class GeometryValidationResult(FrozenModel):
    valid: bool
    status: str
    geometry_sha256: str
    findings: tuple[ValidationFinding, ...]
    repair: GeometryRepairRecord | None = None


def validate_geometry(
    geometry: BaseGeometry,
    *,
    expected_geometry: str,
    extent: BaseGeometry,
    license_boundary: BaseGeometry | None = None,
    topology_exclusions: Iterable[BaseGeometry] = (),
    repair: bool = False,
    repair_tolerance: float = 0.0,
) -> tuple[BaseGeometry, GeometryValidationResult]:
    if repair_tolerance != 0:
        raise GeometryValidationError("shapely.make_valid does not accept a repair tolerance")
    findings = _findings(
        geometry,
        expected_geometry=expected_geometry,
        extent=extent,
        license_boundary=license_boundary,
        topology_exclusions=topology_exclusions,
    )
    has_errors = any(finding.severity == "error" for finding in findings)
    if not has_errors:
        digest = _geometry_hash(geometry)
        return geometry, GeometryValidationResult(
            valid=True,
            status="valid-with-findings" if findings else "valid",
            geometry_sha256=digest,
            findings=tuple(findings),
        )
    if not repair:
        return geometry, GeometryValidationResult(
            valid=False,
            status="invalid",
            geometry_sha256=_geometry_hash(geometry),
            findings=tuple(findings),
        )
    repaired = make_valid(geometry)
    repaired_findings = _findings(
        repaired,
        expected_geometry=expected_geometry,
        extent=extent,
        license_boundary=license_boundary,
        topology_exclusions=topology_exclusions,
    )
    record = GeometryRepairRecord(
        algorithm="shapely.make_valid",
        tolerance=repair_tolerance,
        original_geometry_sha256=_geometry_hash(geometry),
        repaired_geometry_sha256=_geometry_hash(repaired),
        area_before=float(geometry.area),
        area_after=float(repaired.area),
        length_before=float(geometry.length),
        length_after=float(repaired.length),
        maximum_displacement=float(geometry.hausdorff_distance(repaired)),
    )
    repair_has_errors = any(finding.severity == "error" for finding in repaired_findings)
    return repaired, GeometryValidationResult(
        valid=not repair_has_errors,
        status="repaired" if not repair_has_errors else "repair-failed",
        geometry_sha256=_geometry_hash(repaired),
        findings=tuple(repaired_findings or findings),
        repair=record,
    )


def _findings(
    geometry: BaseGeometry,
    *,
    expected_geometry: str,
    extent: BaseGeometry,
    license_boundary: BaseGeometry | None,
    topology_exclusions: Iterable[BaseGeometry],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if geometry.is_empty:
        findings.append(
            ValidationFinding(code="empty", message="geometry is empty", severity="error")
        )
        return findings
    if geometry.geom_type not in _accepted_types(expected_geometry):
        findings.append(
            ValidationFinding(
                code="geometry-type",
                message=f"expected {expected_geometry}, received {geometry.geom_type}",
                severity="error",
            )
        )
    if not all(math.isfinite(value) for value in geometry.bounds):
        findings.append(
            ValidationFinding(
                code="non-finite", message="geometry extent is non-finite", severity="error"
            )
        )
    if not geometry.is_valid:
        findings.append(
            ValidationFinding(
                code="invalid",
                message=explain_validity(geometry),
                severity="error",
            )
        )
    if isinstance(geometry, LineString):
        coordinates = tuple(geometry.coords)
        if len(set(coordinates)) < 2:
            findings.append(
                ValidationFinding(
                    code="degenerate-line",
                    message="line has fewer than two unique vertices",
                    severity="error",
                )
            )
        if _has_consecutive_duplicates(coordinates):
            findings.append(
                ValidationFinding(
                    code="duplicate-vertex",
                    message="line has duplicate consecutive vertices",
                    severity="error",
                )
            )
    if isinstance(geometry, Polygon):
        rings = (geometry.exterior, *geometry.interiors)
        for ring in rings:
            coordinates = tuple(ring.coords)
            if not coordinates or coordinates[0] != coordinates[-1]:
                findings.append(
                    ValidationFinding(
                        code="open-ring", message="polygon ring is not closed", severity="error"
                    )
                )
            if len(set(coordinates[:-1])) < 3:
                findings.append(
                    ValidationFinding(
                        code="degenerate-ring",
                        message="polygon ring has fewer than three unique vertices",
                        severity="error",
                    )
                )
            if _has_consecutive_duplicates(coordinates[:-1]):
                findings.append(
                    ValidationFinding(
                        code="duplicate-vertex",
                        message="polygon ring has duplicate consecutive vertices",
                        severity="error",
                    )
                )
    if not extent.covers(geometry):
        findings.append(
            ValidationFinding(
                code="source-extent",
                message="geometry extends beyond the source raster",
                severity="error",
            )
        )
    if license_boundary is not None and not license_boundary.intersects(geometry):
        findings.append(
            ValidationFinding(
                code="license-boundary",
                message="geometry does not intersect the configured licence boundary",
                severity="warning",
            )
        )
    for excluded in topology_exclusions:
        if geometry.intersects(excluded):
            findings.append(
                ValidationFinding(
                    code="topology-overlap",
                    message="geometry violates a configured no-overlap rule",
                    severity="error",
                )
            )
            break
    return findings


def _accepted_types(expected: str) -> frozenset[str]:
    values = {
        "Point": frozenset({"Point", "MultiPoint"}),
        "LineString": frozenset({"LineString", "MultiLineString"}),
        "Polygon": frozenset({"Polygon", "MultiPolygon"}),
        "Unknown": frozenset(
            {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}
        ),
    }
    try:
        return values[expected]
    except KeyError as exc:
        raise GeometryValidationError(f"unsupported expected geometry type: {expected}") from exc


def _geometry_hash(geometry: BaseGeometry) -> str:
    return sha256_bytes(geometry.wkb)


def _has_consecutive_duplicates(coordinates: tuple[tuple[float, ...], ...]) -> bool:
    return any(left == right for left, right in zip(coordinates, coordinates[1:], strict=False))
