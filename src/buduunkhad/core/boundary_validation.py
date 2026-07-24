"""Deterministic licence-boundary measurement and separate human review contracts.

The Phase 01 record proves which exact source and derivative bytes were measured and records
mechanical CRS, geometry, topology, area, perimeter, and buffer findings.  It never represents
scientific acceptance.  Human acceptance, when it occurs, is a separate immutable attestation
that references the sealed validation bytes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from buduunkhad.ai.fingerprint import sha256_value
from buduunkhad.core.run_artifacts import (
    ArtifactSealError,
    canonical_relative_path,
    require_regular_file_under,
    sha256_file,
)
from buduunkhad.core.run_storage import RunStorageError, validate_run_id
from buduunkhad.core.vector_io import BoundaryReadResult

BOUNDARY_VALIDATION_FORMAT_VERSION = "1.0.0"
BOUNDARY_REVIEW_FORMAT_VERSION = "1.0.0"
BOUNDARY_VALIDATOR_COMPONENT = "buduunkhad.phase01.boundary-validation-v1"

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class BoundaryValidationError(RuntimeError):
    """A boundary record or one of its bound files cannot be trusted."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        revalidate_instances="always",
        allow_inf_nan=False,
    )

    @classmethod
    def model_construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        del _fields_set, values
        raise TypeError("model_construct is unsupported; use validated construction")

    @classmethod
    def construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        del _fields_set, values
        raise TypeError("construct is unsupported; use validated construction")


class BoundFileIdentity(_StrictModel):
    """One regular file under its declared phase root."""

    path: str
    sha256: Sha256
    size_bytes: int = Field(ge=0)
    layer_name: NonEmpty | None = None

    _portable_path = field_validator("path")(canonical_relative_path)


class RegisteredBoundarySource(_StrictModel):
    input_no: int = Field(ge=1)
    evidence_group: NonEmpty
    filename: NonEmpty
    external_file_id: NonEmpty
    registered_external_size_bytes: int = Field(ge=0)


class BoundaryCrsValidation(_StrictModel):
    source_epsg: int = Field(gt=0)
    configured_source_epsg: int = Field(gt=0)
    source_crs_evidence: Literal["reader-reported", "configured-assumption"]
    source_crs_matches_configuration: bool
    source_coordinates_finite: bool
    source_coordinate_domain_valid: bool
    target_epsg: int = Field(gt=0)
    derivative_epsg: int = Field(gt=0)
    target_crs_matches_configuration: bool
    reprojection_applied: bool

    @model_validator(mode="after")
    def _coherent_crs(self) -> BoundaryCrsValidation:
        if self.source_crs_matches_configuration != (
            self.source_epsg == self.configured_source_epsg
        ):
            raise ValueError("boundary source CRS match result is inconsistent")
        if self.target_crs_matches_configuration != (self.derivative_epsg == self.target_epsg):
            raise ValueError("boundary target CRS match result is inconsistent")
        if self.reprojection_applied != (self.source_epsg != self.derivative_epsg):
            raise ValueError("boundary reprojection result is inconsistent")
        return self


class BoundaryTopologyValidation(_StrictModel):
    source_feature_count: int = Field(ge=0)
    derivative_feature_count: int = Field(ge=0)
    source_geometry_types: tuple[NonEmpty, ...]
    derivative_geometry_types: tuple[NonEmpty, ...]
    source_empty_feature_count: int = Field(ge=0)
    derivative_empty_feature_count: int = Field(ge=0)
    source_invalid_feature_count: int = Field(ge=0)
    derivative_invalid_feature_count: int = Field(ge=0)
    source_overlapping_feature_pair_count: int = Field(ge=0)
    derivative_overlapping_feature_pair_count: int = Field(ge=0)
    total_area_square_metres: float = Field(ge=0)
    total_perimeter_metres: float = Field(ge=0)

    @model_validator(mode="after")
    def _ordered_types(self) -> BoundaryTopologyValidation:
        for values in (self.source_geometry_types, self.derivative_geometry_types):
            if tuple(sorted(values)) != values or len(set(values)) != len(values):
                raise ValueError("boundary geometry types must be unique and ordered")
        return self


class BufferValidation(_StrictModel):
    distance_metres: int = Field(gt=0)
    feature_count: int = Field(ge=0)
    empty_feature_count: int = Field(ge=0)
    invalid_feature_count: int = Field(ge=0)
    contains_boundary: bool
    area_square_metres: float = Field(ge=0)
    perimeter_metres: float = Field(ge=0)


class _BoundaryValidationIdentity(_StrictModel):
    format_version: Literal["1.0.0"] = BOUNDARY_VALIDATION_FORMAT_VERSION
    processing_run_id: NonEmpty
    source_phase_id: Literal["00"] = "00"
    source_run_id: NonEmpty
    source: RegisteredBoundarySource
    source_artifact: BoundFileIdentity
    source_sidecars: tuple[BoundFileIdentity, ...] = ()
    source_container_format: NonEmpty
    selected_container_member: str | None = None
    parse_result: Literal["success"] = "success"
    crs: BoundaryCrsValidation
    topology: BoundaryTopologyValidation
    boundary_derivative: BoundFileIdentity
    buffer_derivative: BoundFileIdentity
    requested_buffer_distances_metres: tuple[int, ...] = Field(min_length=1)
    buffers: tuple[BufferValidation, ...] = Field(min_length=1)
    validator_component: Literal["buduunkhad.phase01.boundary-validation-v1"] = (
        BOUNDARY_VALIDATOR_COMPONENT
    )
    software_versions: tuple[NonEmpty, ...] = Field(min_length=1)
    deterministic_status: Literal["complete", "failed"]
    limitations: tuple[NonEmpty, ...] = Field(min_length=1)

    @field_validator("selected_container_member")
    @classmethod
    def _portable_member(cls, value: str | None) -> str | None:
        return canonical_relative_path(value) if value is not None else None

    @field_validator("processing_run_id", "source_run_id")
    @classmethod
    def _safe_run_id(cls, value: str) -> str:
        try:
            return validate_run_id(value)
        except RunStorageError as exc:
            raise ValueError(str(exc)) from exc

    @model_validator(mode="after")
    def _coherent_measurements(self) -> _BoundaryValidationIdentity:
        if tuple(
            sorted(self.source_sidecars, key=lambda item: item.path)
        ) != self.source_sidecars or len({item.path for item in self.source_sidecars}) != len(
            self.source_sidecars
        ):
            raise ValueError("boundary source sidecars must use deterministic path order")
        if self.source_artifact.layer_name is not None or any(
            item.layer_name is not None for item in self.source_sidecars
        ):
            raise ValueError("boundary source files cannot claim derivative layer identities")
        source_path = PurePosixPath(self.source_artifact.path)
        if (
            source_path.name != self.source.filename
            or not source_path.parts
            or source_path.parts[0] != self.source.evidence_group
        ):
            raise ValueError("boundary source artifact does not match its registered source")
        if (
            self.boundary_derivative.layer_name != "license_boundary"
            or self.buffer_derivative.layer_name != "project_buffers"
            or self.boundary_derivative.path == self.buffer_derivative.path
        ):
            raise ValueError("boundary derivative identities are invalid")
        source_is_kmz = PurePosixPath(self.source_artifact.path).suffix.casefold() == ".kmz"
        container_is_coherent = (
            self.source_container_format.casefold() == "kmz"
            and self.selected_container_member is not None
            if source_is_kmz
            else self.source_container_format.casefold() != "kmz"
            and self.selected_container_member is None
        )
        if not container_is_coherent:
            raise ValueError("boundary container provenance is inconsistent")
        distances = self.requested_buffer_distances_metres
        if tuple(sorted(set(distances))) != distances or any(value <= 0 for value in distances):
            raise ValueError("boundary buffer distances must be positive, unique, and ordered")
        if tuple(item.distance_metres for item in self.buffers) != distances:
            raise ValueError("boundary buffer results must exactly match requested distances")
        areas = tuple(item.area_square_metres for item in self.buffers)
        mechanically_complete = all(
            (
                self.crs.source_crs_matches_configuration,
                self.crs.source_coordinates_finite,
                self.crs.source_coordinate_domain_valid,
                self.crs.target_crs_matches_configuration,
                self.topology.source_feature_count > 0,
                self.topology.derivative_feature_count > 0,
                self.topology.source_feature_count == self.topology.derivative_feature_count,
                self.topology.source_empty_feature_count == 0,
                self.topology.derivative_empty_feature_count == 0,
                self.topology.source_invalid_feature_count == 0,
                self.topology.derivative_invalid_feature_count == 0,
                self.topology.source_overlapping_feature_pair_count == 0,
                self.topology.derivative_overlapping_feature_pair_count == 0,
                self.topology.total_area_square_metres > 0,
                self.topology.total_perimeter_metres > 0,
                set(self.topology.source_geometry_types) <= {"Polygon", "MultiPolygon"},
                set(self.topology.derivative_geometry_types) == {"MultiPolygon"},
                all(
                    item.feature_count == 1
                    and item.empty_feature_count == 0
                    and item.invalid_feature_count == 0
                    and item.contains_boundary
                    and item.area_square_metres > 0
                    and item.perimeter_metres > 0
                    for item in self.buffers
                ),
                all(right > left for left, right in zip(areas, areas[1:], strict=False)),
            )
        )
        expected = "complete" if mechanically_complete else "failed"
        if self.deterministic_status != expected:
            raise ValueError("boundary deterministic status does not match its measurements")
        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError("boundary limitations must be unique")
        if tuple(sorted(self.software_versions)) != self.software_versions or len(
            set(self.software_versions)
        ) != len(self.software_versions):
            raise ValueError("boundary software identities must be unique and ordered")
        return self


class BoundaryValidationRecord(_BoundaryValidationIdentity):
    """Self-consistent deterministic record; never a human acceptance decision."""

    validation_id: Sha256

    @model_validator(mode="after")
    def _sealed_identity(self) -> BoundaryValidationRecord:
        identity = _BoundaryValidationIdentity.model_validate(
            self.model_dump(mode="python", exclude={"validation_id"})
        )
        if self.validation_id != sha256_value(identity):
            raise ValueError("boundary validation identity is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> BoundaryValidationRecord:
        identity = _BoundaryValidationIdentity.model_validate(values)
        return cls(
            **identity.model_dump(mode="python"),
            validation_id=sha256_value(identity),
        )


class BoundaryReviewerRole(StrEnum):
    DATA_CUSTODIAN = "geospatial-data-custodian"
    QUALIFIED_REVIEWER = "qualified-geospatial-reviewer"


class BoundaryReviewDecision(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class _BoundaryReviewIdentity(_StrictModel):
    format_version: Literal["1.0.0"] = BOUNDARY_REVIEW_FORMAT_VERSION
    validation_id: Sha256
    validation_file_sha256: Sha256
    processing_run_id: NonEmpty
    reviewer: NonEmpty
    reviewer_role: BoundaryReviewerRole
    reviewer_authorization_id: NonEmpty
    reviewed_at: datetime
    decision: BoundaryReviewDecision
    rationale: NonEmpty
    limitations: tuple[NonEmpty, ...] = ()

    @model_validator(mode="after")
    def _truthful_review(self) -> _BoundaryReviewIdentity:
        try:
            validate_run_id(self.processing_run_id)
        except RunStorageError as exc:
            raise ValueError(str(exc)) from exc
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("boundary review time must be timezone-aware")
        if self.reviewed_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("boundary review time must be recorded in UTC")
        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError("boundary review limitations must be unique")
        return self


class BoundaryReviewAttestation(_BoundaryReviewIdentity):
    """One named role's review; authoritative use still requires a trusted resolver."""

    attestation_id: Sha256

    @model_validator(mode="after")
    def _sealed_identity(self) -> BoundaryReviewAttestation:
        identity = _BoundaryReviewIdentity.model_validate(
            self.model_dump(mode="python", exclude={"attestation_id"})
        )
        if self.attestation_id != sha256_value(identity):
            raise ValueError("boundary review attestation identity is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> BoundaryReviewAttestation:
        identity = _BoundaryReviewIdentity.model_validate(values)
        return cls(
            **identity.model_dump(mode="python"),
            attestation_id=sha256_value(identity),
        )


def create_boundary_validation_record(
    *,
    processing_run_id: str,
    source_run_id: str,
    source: RegisteredBoundarySource,
    source_phase_root: Path,
    source_artifact: Path,
    source_artifact_before: BoundFileIdentity,
    source_sidecars: tuple[Path, ...],
    source_sidecars_before: tuple[BoundFileIdentity, ...],
    phase_root: Path,
    boundary_derivative: Path,
    buffer_derivative: Path,
    read_result: BoundaryReadResult,
    derivative_gdf: Any,
    buffers_gdf: Any,
    configured_source_epsg: int,
    target_epsg: int,
    requested_buffer_distances_metres: tuple[int, ...],
) -> BoundaryValidationRecord:
    """Measure one successfully parsed boundary and bind all input/output bytes."""

    source_identity = _file_identity(source_phase_root, source_artifact)
    sidecars = tuple(
        sorted(
            (_file_identity(source_phase_root, path) for path in source_sidecars),
            key=lambda item: item.path,
        )
    )
    if source_identity != source_artifact_before or sidecars != source_sidecars_before:
        raise BoundaryValidationError("boundary source changed while it was being validated")
    boundary_identity = _file_identity(
        phase_root, boundary_derivative, layer_name="license_boundary"
    )
    buffer_identity = _file_identity(phase_root, buffer_derivative, layer_name="project_buffers")

    source_gdf = read_result.gdf
    source_types = _geometry_types(source_gdf)
    derivative_types = _geometry_types(derivative_gdf)
    source_finite, source_domain = _source_coordinate_checks(source_gdf, configured_source_epsg)
    merged = _merged_geometry(derivative_gdf)
    source_empty_count = sum(bool(item is None or item.is_empty) for item in source_gdf.geometry)
    derivative_empty_count = sum(
        bool(item is None or item.is_empty) for item in derivative_gdf.geometry
    )
    source_invalid_count = sum(
        bool(item is not None and not item.is_empty and not item.is_valid)
        for item in source_gdf.geometry
    )
    derivative_invalid_count = sum(
        bool(item is not None and not item.is_empty and not item.is_valid)
        for item in derivative_gdf.geometry
    )
    source_overlap_count = _overlapping_pair_count(source_gdf)
    derivative_overlap_count = _overlapping_pair_count(derivative_gdf)
    derivative_epsg = derivative_gdf.crs.to_epsg() if derivative_gdf.crs is not None else None
    if read_result.source_epsg is None or derivative_epsg is None:
        raise BoundaryValidationError("boundary CRS could not be expressed as an EPSG identity")

    buffer_rows = tuple(
        _measure_buffer(buffers_gdf, distance, merged)
        for distance in requested_buffer_distances_metres
    )
    topology = BoundaryTopologyValidation(
        source_feature_count=len(source_gdf),
        derivative_feature_count=len(derivative_gdf),
        source_geometry_types=source_types,
        derivative_geometry_types=derivative_types,
        source_empty_feature_count=source_empty_count,
        derivative_empty_feature_count=derivative_empty_count,
        source_invalid_feature_count=source_invalid_count,
        derivative_invalid_feature_count=derivative_invalid_count,
        source_overlapping_feature_pair_count=source_overlap_count,
        derivative_overlapping_feature_pair_count=derivative_overlap_count,
        total_area_square_metres=float(merged.area) if not merged.is_empty else 0.0,
        total_perimeter_metres=float(merged.length) if not merged.is_empty else 0.0,
    )
    crs = BoundaryCrsValidation(
        source_epsg=read_result.source_epsg,
        configured_source_epsg=configured_source_epsg,
        source_crs_evidence=read_result.crs_evidence,
        source_crs_matches_configuration=read_result.source_epsg == configured_source_epsg,
        source_coordinates_finite=source_finite,
        source_coordinate_domain_valid=source_domain,
        target_epsg=target_epsg,
        derivative_epsg=derivative_epsg,
        target_crs_matches_configuration=derivative_epsg == target_epsg,
        reprojection_applied=read_result.source_epsg != derivative_epsg,
    )
    areas = tuple(item.area_square_metres for item in buffer_rows)
    mechanically_complete = all(
        (
            crs.source_crs_matches_configuration,
            crs.source_coordinates_finite,
            crs.source_coordinate_domain_valid,
            crs.target_crs_matches_configuration,
            topology.source_feature_count > 0,
            topology.derivative_feature_count > 0,
            topology.source_feature_count == topology.derivative_feature_count,
            topology.source_empty_feature_count == 0,
            topology.derivative_empty_feature_count == 0,
            topology.source_invalid_feature_count == 0,
            topology.derivative_invalid_feature_count == 0,
            topology.source_overlapping_feature_pair_count == 0,
            topology.derivative_overlapping_feature_pair_count == 0,
            topology.total_area_square_metres > 0,
            topology.total_perimeter_metres > 0,
            set(topology.source_geometry_types) <= {"Polygon", "MultiPolygon"},
            set(topology.derivative_geometry_types) == {"MultiPolygon"},
            all(
                item.feature_count == 1
                and item.empty_feature_count == 0
                and item.invalid_feature_count == 0
                and item.contains_boundary
                and item.area_square_metres > 0
                and item.perimeter_metres > 0
                for item in buffer_rows
            ),
            all(right > left for left, right in zip(areas, areas[1:], strict=False)),
        )
    )
    return BoundaryValidationRecord.create(
        processing_run_id=processing_run_id,
        source_run_id=source_run_id,
        source=source,
        source_artifact=source_identity,
        source_sidecars=sidecars,
        source_container_format=read_result.container_format,
        selected_container_member=read_result.selected_member,
        crs=crs,
        topology=topology,
        boundary_derivative=boundary_identity,
        buffer_derivative=buffer_identity,
        requested_buffer_distances_metres=requested_buffer_distances_metres,
        buffers=buffer_rows,
        software_versions=_software_versions(),
        deterministic_status="complete" if mechanically_complete else "failed",
        limitations=(
            "Deterministic measurements do not constitute scientific or administrative acceptance.",
            "The licence boundary is administrative context and is not mineral evidence.",
            "METH-READY-005 remains unresolved until trusted acceptance records from both required reviewer roles are resolved.",
        ),
    )


def write_boundary_validation_record(record: BoundaryValidationRecord, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def load_boundary_validation_record(path: Path) -> BoundaryValidationRecord:
    """Load a record while rejecting duplicate JSON keys."""

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        return BoundaryValidationRecord.model_validate(value)
    except (OSError, UnicodeError, ValueError) as exc:
        raise BoundaryValidationError("boundary validation record is invalid") from exc


def verify_boundary_validation_files(
    record: BoundaryValidationRecord,
    *,
    source_phase_root: Path,
    phase_root: Path,
) -> None:
    """Revalidate every byte claim before a record is reused or reviewed."""

    try:
        for identity in (record.source_artifact, *record.source_sidecars):
            _verify_file_identity(source_phase_root, identity)
        _verify_file_identity(phase_root, record.boundary_derivative)
        _verify_file_identity(phase_root, record.buffer_derivative)
    except (ArtifactSealError, OSError) as exc:
        raise BoundaryValidationError("boundary validation file identity is invalid") from exc


def capture_bound_file_identity(root: Path, path: Path) -> BoundFileIdentity:
    """Capture a source identity for a later before/after mutation check."""

    return _file_identity(root, path)


def _file_identity(root: Path, path: Path, *, layer_name: str | None = None) -> BoundFileIdentity:
    safe = require_regular_file_under(root, path, description="boundary validation artifact")
    relative = safe.relative_to(Path(root).absolute().resolve()).as_posix()
    return BoundFileIdentity(
        path=relative,
        sha256=sha256_file(safe),
        size_bytes=safe.stat().st_size,
        layer_name=layer_name,
    )


def _verify_file_identity(root: Path, identity: BoundFileIdentity) -> None:
    path = Path(root) / identity.path
    safe = require_regular_file_under(root, path, description="boundary validation artifact")
    if safe.stat().st_size != identity.size_bytes or sha256_file(safe) != identity.sha256:
        raise BoundaryValidationError(
            f"boundary validation artifact bytes changed: {identity.path}"
        )


def _geometry_types(gdf: Any) -> tuple[str, ...]:
    return tuple(sorted({str(item) for item in gdf.geometry.geom_type.dropna()}))


def _merged_geometry(gdf: Any) -> Any:
    if len(gdf) == 0:
        from shapely.geometry import GeometryCollection

        return GeometryCollection()
    return (
        gdf.geometry.union_all() if hasattr(gdf.geometry, "union_all") else gdf.geometry.unary_union
    )


def _source_coordinate_checks(gdf: Any, expected_epsg: int) -> tuple[bool, bool]:
    import numpy as np
    from shapely import get_coordinates

    coordinates = get_coordinates(gdf.geometry.to_numpy())
    finite = bool(coordinates.size and np.isfinite(coordinates).all())
    if not finite:
        return False, False
    if expected_epsg == 4326:
        domain = bool(
            (coordinates[:, 0] >= -180).all()
            and (coordinates[:, 0] <= 180).all()
            and (coordinates[:, 1] >= -90).all()
            and (coordinates[:, 1] <= 90).all()
        )
    else:
        domain = True
    return finite, domain


def _overlapping_pair_count(gdf: Any) -> int:
    geometries = list(gdf.geometry)
    count = 0
    for index, left in enumerate(geometries):
        if left is None or left.is_empty:
            continue
        for right in geometries[index + 1 :]:
            if right is not None and not right.is_empty and left.intersection(right).area > 0:
                count += 1
    return count


def _measure_buffer(buffers_gdf: Any, distance: int, boundary: Any) -> BufferValidation:
    selected = buffers_gdf.loc[buffers_gdf["distance_m"] == distance]
    merged = _merged_geometry(selected)
    return BufferValidation(
        distance_metres=distance,
        feature_count=len(selected),
        empty_feature_count=sum(bool(item is None or item.is_empty) for item in selected.geometry),
        invalid_feature_count=sum(
            bool(item is not None and not item.is_empty and not item.is_valid)
            for item in selected.geometry
        ),
        contains_boundary=bool(not merged.is_empty and merged.covers(boundary)),
        area_square_metres=float(merged.area) if not merged.is_empty else 0.0,
        perimeter_metres=float(merged.length) if not merged.is_empty else 0.0,
    )


def _software_versions() -> tuple[str, ...]:
    values: list[str] = []
    for distribution in ("buduunkhad", "fiona", "geopandas", "pyproj", "shapely"):
        try:
            package_version = version(distribution)
        except PackageNotFoundError:
            package_version = "source-tree"
        values.append(f"{distribution}=={package_version}")
    return tuple(sorted(values))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value
