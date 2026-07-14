"""Deeply immutable, provider-neutral contracts for offline AI work."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Generic, Literal, Self, TypeAlias, TypeVar, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic.version import VERSION as PYDANTIC_VERSION

from buduunkhad.ai.fingerprint import (
    CanonicalizationError,
    canonical_json_text,
    canonical_value_from_text,
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
SemanticVersion = Annotated[
    str, StringConstraints(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
]
PixelCoordinate: TypeAlias = tuple[float, float]
MINIMUM_PYDANTIC_VERSION = (2, 7)


def ensure_supported_pydantic(version: str = PYDANTIC_VERSION) -> None:
    """Fail loudly if runtime validation semantics are below the supported floor."""
    match = re.match(r"^(\d+)\.(\d+)", version)
    if match is None or tuple(map(int, match.groups())) < MINIMUM_PYDANTIC_VERSION:
        raise RuntimeError(f"buduunkhad AI contracts require Pydantic >=2.7 (found {version})")


ensure_supported_pydantic()


class FrozenModel(BaseModel):
    """Strict base that revalidates copies and exposes only immutable fields."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    @classmethod
    def model_construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        """Prohibit Pydantic's deliberately unvalidated construction bypass."""
        del _fields_set, values
        raise TypeError("model_construct is unsupported; use constructor or model_validate")

    @classmethod
    def construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        """Prohibit the deprecated alias of unvalidated model construction."""
        del _fields_set, values
        raise TypeError("construct is unsupported; use constructor or model_validate")

    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        """Return a fully revalidated copy; Pydantic's unvalidated update is forbidden."""
        del deep  # every copy is reconstructed deeply from validated Python data
        values = {name: object.__getattribute__(self, name) for name in type(self).model_fields}
        if update:
            for key, value in update.items():
                if key not in type(self).model_fields:
                    raise ValueError(f"unknown update field: {key}")
                values[key] = value
        return type(self).model_validate(values)

    def copy(
        self,
        *,
        include: object = None,
        exclude: object = None,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        """Revalidate deprecated copy updates instead of using Pydantic's bypass."""
        if include is not None or exclude is not None:
            raise ValueError("copy include/exclude is unsupported for security-sensitive models")
        return self.model_copy(update=update, deep=deep)


class CanonicalJSONValue(FrozenModel):
    """Immutable canonical representation of an otherwise nested JSON-like value."""

    canonical_json: NonEmptyStr

    @classmethod
    def from_value(cls, value: object) -> CanonicalJSONValue:
        """Canonicalize a raw value, including a raw mapping named ``canonical_json``."""
        return cls(canonical_json=canonical_json_text(value))

    @classmethod
    def from_input(cls, value: object) -> CanonicalJSONValue:
        """Validate a stored record or canonicalize a raw public input.

        The exact one-field serialized model shape is reserved for stored records and
        is strictly validated. Callers whose *raw* mapping intentionally has a single
        ``canonical_json`` key must make that intent explicit with :meth:`from_value`.
        """
        if isinstance(value, cls):
            return value
        if type(value) is dict and set(value) == {"canonical_json"}:
            return cls.model_validate(value)
        return cls.from_value(value)

    def to_python(self) -> object:
        """Return a fresh decoded value; mutating it cannot mutate this record."""
        return canonical_value_from_text(self.canonical_json)

    @field_validator("canonical_json")
    @classmethod
    def _is_canonical(cls, value: str) -> str:
        canonical_value_from_text(value)
        return value


class NamedJSONValue(FrozenModel):
    name: NonEmptyStr
    value: CanonicalJSONValue

    @field_validator("value", mode="before")
    @classmethod
    def _freeze_value(cls, value: object) -> object:
        return CanonicalJSONValue.from_input(value)


def _freeze_named_values(value: object) -> tuple[NamedJSONValue, ...]:
    if type(value) is dict:
        items: list[NamedJSONValue] = []
        for key, item in value.items():
            if type(key) is not str:
                raise CanonicalizationError("named-value mapping keys must be strings")
            items.append(NamedJSONValue(name=key, value=item))
        result = tuple(items)
    elif type(value) in {tuple, list}:
        result = tuple(
            item if isinstance(item, NamedJSONValue) else NamedJSONValue.model_validate(item)
            for item in cast(Iterable[object], value)
        )
    else:
        raise ValueError("named values require a mapping or sequence")
    names = tuple(item.name for item in result)
    if len(set(names)) != len(names):
        raise ValueError("named values contain duplicate names")
    return tuple(sorted(result, key=lambda entry: entry.name))


class ReviewStatus(StrEnum):
    AI_DRAFT = "AI_DRAFT"
    AI_VALIDATED = "AI_VALIDATED"
    GEOLOGIST_APPROVED = "GEOLOGIST_APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskType(StrEnum):
    DOCUMENT_EXTRACTION = "document_extraction"
    IMAGE_RASTER_INTERPRETATION = "image_raster_interpretation"
    GEOLOGICAL_FEATURE_PROPOSAL = "geological_feature_proposal"
    FEATURE_CRITIQUE = "feature_critique"


class PageLocator(FrozenModel):
    kind: Literal["page"] = "page"
    page_number: int = Field(ge=1)


class RasterTileLocator(FrozenModel):
    kind: Literal["raster_tile"] = "raster_tile"
    tile_id: NonEmptyStr
    x_offset: int = Field(ge=0)
    y_offset: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class SourceFeatureLocator(FrozenModel):
    kind: Literal["source_feature"] = "source_feature"
    layer_name: NonEmptyStr
    feature_id: NonEmptyStr


SourceLocator = Annotated[
    PageLocator | RasterTileLocator | SourceFeatureLocator,
    Field(discriminator="kind"),
]


class SourceReference(FrozenModel):
    asset_id: NonEmptyStr
    sha256: Sha256
    locators: tuple[SourceLocator, ...] = Field(min_length=1)


def _validate_pixel_coordinate(point: PixelCoordinate) -> PixelCoordinate:
    if not all(math.isfinite(value) for value in point):
        raise ValueError("pixel coordinates must be finite")
    return point


class PixelPoint(FrozenModel):
    type: Literal["Point"] = "Point"
    coordinates: PixelCoordinate

    @field_validator("coordinates")
    @classmethod
    def _finite_coordinates(cls, value: PixelCoordinate) -> PixelCoordinate:
        return _validate_pixel_coordinate(value)


class PixelLineString(FrozenModel):
    type: Literal["LineString"] = "LineString"
    coordinates: tuple[PixelCoordinate, ...] = Field(min_length=2)

    @field_validator("coordinates")
    @classmethod
    def _finite_coordinates(cls, value: tuple[PixelCoordinate, ...]) -> tuple[PixelCoordinate, ...]:
        return tuple(_validate_pixel_coordinate(point) for point in value)


class PixelPolygon(FrozenModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: tuple[tuple[PixelCoordinate, ...], ...] = Field(min_length=1)

    @field_validator("coordinates")
    @classmethod
    def _closed_finite_rings(
        cls, value: tuple[tuple[PixelCoordinate, ...], ...]
    ) -> tuple[tuple[PixelCoordinate, ...], ...]:
        for ring in value:
            if len(ring) < 4:
                raise ValueError("pixel polygon rings require at least four coordinates")
            for point in ring:
                _validate_pixel_coordinate(point)
            if ring[0] != ring[-1]:
                raise ValueError("pixel polygon rings must be closed")
        return value


PixelGeometry = Annotated[
    PixelPoint | PixelLineString | PixelPolygon,
    Field(discriminator="type"),
]


class ConfidenceComponent(FrozenModel):
    name: NonEmptyStr
    score: float = Field(ge=0.0, le=1.0)
    rationale: NonEmptyStr


class ExtractedDocumentField(FrozenModel):
    field_name: NonEmptyStr
    value: CanonicalJSONValue
    confidence: float = Field(ge=0.0, le=1.0)
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    limitations: tuple[NonEmptyStr, ...]

    @field_validator("value", mode="before")
    @classmethod
    def _freeze_value(cls, value: object) -> object:
        return CanonicalJSONValue.from_input(value)


class DocumentExtraction(FrozenModel):
    document_id: NonEmptyStr
    fields: tuple[ExtractedDocumentField, ...]
    summary: NonEmptyStr
    limitations: tuple[NonEmptyStr, ...]


class RasterObservation(FrozenModel):
    observation_id: NonEmptyStr
    label: NonEmptyStr
    geometry: PixelGeometry
    attributes: tuple[NamedJSONValue, ...]
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: tuple[NonEmptyStr, ...]

    @field_validator("attributes", mode="before")
    @classmethod
    def _freeze_attributes(cls, value: object) -> tuple[NamedJSONValue, ...]:
        return _freeze_named_values(value)


class ImageRasterInterpretation(FrozenModel):
    source_reference: SourceReference
    observations: tuple[RasterObservation, ...]
    limitations: tuple[NonEmptyStr, ...]


class GeologicalFeatureProposal(FrozenModel):
    """AI proposal in source-image pixel space, never an approved feature."""

    feature_id: NonEmptyStr
    feature_type: NonEmptyStr
    geometry: PixelGeometry
    attributes: tuple[NamedJSONValue, ...]
    evidence_status: NonEmptyStr
    review_status: Literal[ReviewStatus.AI_DRAFT] = ReviewStatus.AI_DRAFT
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    confidence_components: tuple[ConfidenceComponent, ...] = Field(min_length=1)
    limitations: tuple[NonEmptyStr, ...]

    @field_validator("attributes", mode="before")
    @classmethod
    def _freeze_attributes(cls, value: object) -> tuple[NamedJSONValue, ...]:
        return _freeze_named_values(value)


class CritiqueVerdict(StrEnum):
    ACCEPT_FOR_VALIDATION = "ACCEPT_FOR_VALIDATION"
    REVISE = "REVISE"
    REJECT = "REJECT"


class FeatureCritique(FrozenModel):
    feature_id: NonEmptyStr
    verdict: CritiqueVerdict
    findings: tuple[NonEmptyStr, ...]
    confidence_components: tuple[ConfidenceComponent, ...] = Field(min_length=1)
    limitations: tuple[NonEmptyStr, ...]


class PromptIdentity(FrozenModel):
    prompt_id: NonEmptyStr
    version: SemanticVersion
    sha256: Sha256


class SchemaIdentity(FrozenModel):
    schema_id: NonEmptyStr
    version: SemanticVersion
    sha256: Sha256


class ProviderConfiguration(FrozenModel):
    provider: NonEmptyStr
    model: NonEmptyStr
    parameters: tuple[NamedJSONValue, ...]

    @field_validator("parameters", mode="before")
    @classmethod
    def _freeze_parameters(cls, value: object) -> tuple[NamedJSONValue, ...]:
        return _freeze_named_values(value)


class ArtifactSubjectIdentity(FrozenModel):
    artifact_id: NonEmptyStr
    artifact_version: int = Field(ge=1)
    content_sha256: Sha256
    generator_job_id: NonEmptyStr


class AIRequest(FrozenModel):
    request_id: NonEmptyStr
    job_id: NonEmptyStr
    run_id: NonEmptyStr
    phase_id: NonEmptyStr
    task_type: TaskType
    created_at: datetime
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    prompt: PromptIdentity
    output_schema: SchemaIdentity
    provider: ProviderConfiguration
    interpretation_parameters: tuple[NamedJSONValue, ...]
    subject: ArtifactSubjectIdentity | None = None

    @field_validator("interpretation_parameters", mode="before")
    @classmethod
    def _freeze_parameters(cls, value: object) -> tuple[NamedJSONValue, ...]:
        return _freeze_named_values(value)

    @field_validator("created_at")
    @classmethod
    def _aware_created_at(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")

    @model_validator(mode="after")
    def _critique_subject_consistency(self) -> AIRequest:
        if self.task_type is TaskType.FEATURE_CRITIQUE and self.subject is None:
            raise ValueError("feature critique requests require an artifact subject")
        if self.task_type is not TaskType.FEATURE_CRITIQUE and self.subject is not None:
            raise ValueError("only feature critique requests may contain an artifact subject")
        return self


class AIUsage(FrozenModel):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    requests: int = Field(default=1, ge=0)
    cost_usd: Decimal = Field(default=Decimal("0"), ge=0)


class AIResponseStatus(StrEnum):
    SUCCESS = "SUCCESS"
    REFUSED = "REFUSED"
    REFUSAL = "REFUSED"  # compatibility alias for the pre-hardening PR 1 draft
    INCOMPLETE = "INCOMPLETE"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    FAILURE = "FAILURE"


class IncompleteDetail(FrozenModel):
    reason: NonEmptyStr
    metadata: tuple[NamedJSONValue, ...] = ()

    @field_validator("metadata", mode="before")
    @classmethod
    def _freeze_metadata(cls, value: object) -> tuple[NamedJSONValue, ...]:
        return _freeze_named_values(value)


class FailureDetail(FrozenModel):
    code: NonEmptyStr
    message: NonEmptyStr
    retryable: bool


OutputT = TypeVar("OutputT", bound=FrozenModel)


class AIResponse(FrozenModel, Generic[OutputT]):
    request_id: NonEmptyStr
    job_id: NonEmptyStr
    run_id: NonEmptyStr
    phase_id: NonEmptyStr
    task_type: TaskType
    request_fingerprint: Sha256
    output_schema: SchemaIdentity
    status: AIResponseStatus
    provider: NonEmptyStr
    model: NonEmptyStr
    provider_response_id: NonEmptyStr
    created_at: datetime
    usage: AIUsage
    output: OutputT | None = None
    refusal_reason: NonEmptyStr | None = None
    incomplete: IncompleteDetail | None = None
    validation_errors: tuple[NonEmptyStr, ...] = ()
    failure: FailureDetail | None = None
    raw_output: CanonicalJSONValue | None = None

    @field_validator("created_at")
    @classmethod
    def _aware_created_at(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")

    @field_validator("raw_output", mode="before")
    @classmethod
    def _freeze_raw_output(cls, value: object) -> object:
        if value is None:
            return value
        return CanonicalJSONValue.from_input(value)

    @model_validator(mode="after")
    def _status_payload_consistency(self) -> AIResponse[OutputT]:
        if self.status is AIResponseStatus.SUCCESS:
            if self.output is None:
                raise ValueError("successful response requires output")
            if any(
                (
                    self.refusal_reason,
                    self.incomplete,
                    self.validation_errors,
                    self.failure,
                    self.raw_output,
                )
            ):
                raise ValueError("successful response cannot contain error details")
        elif self.output is not None:
            raise ValueError("non-success response cannot contain validated output")
        if self.status is AIResponseStatus.REFUSED and not self.refusal_reason:
            raise ValueError("refused response requires refusal_reason")
        if self.status is AIResponseStatus.INCOMPLETE and self.incomplete is None:
            raise ValueError("incomplete response requires incomplete details")
        if self.status is AIResponseStatus.INVALID_OUTPUT and (
            not self.validation_errors or self.raw_output is None
        ):
            raise ValueError("invalid output requires raw_output and validation_errors")
        if self.status is AIResponseStatus.FAILURE and self.failure is None:
            raise ValueError("failure response requires failure details")
        if self.status is not AIResponseStatus.REFUSED and self.refusal_reason is not None:
            raise ValueError("refusal_reason is only valid for REFUSED")
        if self.status is not AIResponseStatus.INCOMPLETE and self.incomplete is not None:
            raise ValueError("incomplete details are only valid for INCOMPLETE")
        if self.status is not AIResponseStatus.INVALID_OUTPUT and self.validation_errors:
            raise ValueError("validation_errors are only valid for INVALID_OUTPUT")
        if self.status is not AIResponseStatus.FAILURE and self.failure is not None:
            raise ValueError("failure details are only valid for FAILURE")
        if self.status is not AIResponseStatus.INVALID_OUTPUT and self.raw_output is not None:
            raise ValueError("raw_output is only valid for INVALID_OUTPUT")
        return self


class AIJobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    REFUSED = "REFUSED"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"


class AIJob(FrozenModel):
    job_id: NonEmptyStr
    run_id: NonEmptyStr
    phase_id: NonEmptyStr
    task_type: TaskType
    request_id: NonEmptyStr
    request_fingerprint: Sha256
    output_schema: SchemaIdentity
    provider: NonEmptyStr
    model: NonEmptyStr
    provider_parameters_sha256: Sha256
    status: AIJobStatus
    provider_response_id: NonEmptyStr | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    usage: AIUsage

    @field_validator("created_at", "started_at", "completed_at")
    @classmethod
    def _aware_timestamps(cls, value: datetime | None, info: object) -> datetime | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "timestamp")
        return require_aware_datetime(value, str(field_name))

    @model_validator(mode="after")
    def _status_and_timestamp_consistency(self) -> AIJob:
        if self.started_at is not None and self.started_at < self.created_at:
            raise ValueError("job cannot start before it is created")
        if self.completed_at is not None:
            if self.started_at is None:
                raise ValueError("completed job requires started_at")
            if self.completed_at < self.started_at:
                raise ValueError("job cannot complete before it starts")
        terminal = {
            AIJobStatus.SUCCEEDED,
            AIJobStatus.REFUSED,
            AIJobStatus.INCOMPLETE,
            AIJobStatus.FAILED,
        }
        if self.status is AIJobStatus.PENDING:
            if self.started_at is not None or self.completed_at is not None:
                raise ValueError("pending job cannot have start or completion timestamps")
            if self.provider_response_id is not None:
                raise ValueError("pending job cannot have a provider response")
        elif self.status is AIJobStatus.RUNNING:
            if self.started_at is None or self.completed_at is not None:
                raise ValueError("running job requires started_at and no completed_at")
            if self.provider_response_id is not None:
                raise ValueError("running job cannot have a provider response")
        elif self.status in terminal:
            if self.started_at is None or self.completed_at is None:
                raise ValueError("terminal job requires start and completion timestamps")
            if self.provider_response_id is None:
                raise ValueError("terminal job requires a provider response ID")
        return self


class ReviewActorType(StrEnum):
    DETERMINISTIC_VALIDATOR = "DETERMINISTIC_VALIDATOR"
    HUMAN_REVIEWER = "HUMAN_REVIEWER"
    AI_CRITIC = "AI_CRITIC"
    AI_PROVIDER = "AI_PROVIDER"


def require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value
