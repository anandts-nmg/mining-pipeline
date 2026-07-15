"""Persisted manifests for sources, tiles, request packages, and responses."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from buduunkhad.ai.contracts import (
    AIRequest,
    AIUsage,
    CanonicalJSONValue,
    FrozenModel,
    NonEmptyStr,
    PromptIdentity,
    SchemaIdentity,
    TaskType,
    require_aware_datetime,
)


class AffineRecord(FrozenModel):
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float

    @model_validator(mode="after")
    def _finite_and_invertible(self) -> AffineRecord:
        values = (self.a, self.b, self.c, self.d, self.e, self.f)
        determinant = self.a * self.e - self.b * self.d
        if not all(math.isfinite(value) for value in values):
            raise ValueError("source affine values must be finite")
        if not math.isfinite(determinant) or determinant == 0:
            raise ValueError("source affine transform must be invertible")
        return self


class SourceAssetRecord(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    asset_id: str
    source_root_id: Literal["snapshot", "run-work"] = "snapshot"
    run_id: str | None = None
    relative_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size: int = Field(ge=0)
    media_type: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    band_count: int = Field(gt=0)
    dtype: str
    affine: AffineRecord
    source_crs: str | None
    target_crs: str
    nodata: float | None
    nodata_kind: Literal["none", "value", "nan", "positive-infinity", "negative-infinity"]
    original_source_relative_path: str | None = None
    original_source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    page_number: int | None = Field(default=None, ge=1)
    render_scale: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _source_role_is_complete(self) -> SourceAssetRecord:
        derived_values = (
            self.original_source_relative_path,
            self.original_source_sha256,
            self.page_number,
            self.render_scale,
        )
        if self.source_root_id == "run-work":
            if not self.run_id or any(value is None for value in derived_values):
                raise ValueError("rendered work sources require complete source-page provenance")
        elif self.run_id is not None or any(value is not None for value in derived_values):
            raise ValueError("snapshot raster sources cannot contain rendered-page provenance")
        if self.nodata_kind == "value":
            if self.nodata is None or not math.isfinite(self.nodata):
                raise ValueError("finite NoData kind requires a finite value")
        elif self.nodata is not None:
            raise ValueError("non-finite or absent NoData kinds cannot contain a numeric value")
        return self


class TileRecord(FrozenModel):
    tile_id: str
    source_asset_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    band_identity: str
    x_offset: int = Field(ge=0)
    y_offset: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    overlap: int = Field(ge=0)
    image_relative_path: str
    image_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    valid_mask_relative_path: str | None = None
    valid_mask_sha256: str | None = None
    valid_fraction: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def _mask_identity_is_complete(self) -> TileRecord:
        if (self.valid_mask_relative_path is None) != (self.valid_mask_sha256 is None):
            raise ValueError("tile mask path and SHA-256 must be recorded together")
        return self


class TileSetManifest(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    source: SourceAssetRecord
    tile_width: int
    tile_height: int
    overlap: int
    rendering: tuple[tuple[str, str], ...]
    tiles: tuple[TileRecord, ...]


class EgressDecisionStatus(StrEnum):
    NOT_APPROVED = "not-approved"
    APPROVED = "approved"


class EgressDecision(FrozenModel):
    status: EgressDecisionStatus = EgressDecisionStatus.NOT_APPROVED
    approved_by: str | None = None
    approved_at: datetime | None = None
    note: str | None = None

    @field_validator("approved_at")
    @classmethod
    def _aware_approval_time(cls, value: datetime | None) -> datetime | None:
        return require_aware_datetime(value, "approved_at") if value is not None else None

    @model_validator(mode="after")
    def _complete_decision(self) -> EgressDecision:
        if self.status is EgressDecisionStatus.APPROVED:
            if not self.approved_by or self.approved_at is None or not self.note:
                raise ValueError("approved egress requires approver, time, and note")
        elif any((self.approved_by, self.approved_at, self.note)):
            raise ValueError("unapproved egress cannot contain approval details")
        return self


class PackageEgressApproval(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    package_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: EgressDecision

    @model_validator(mode="after")
    def _must_be_approved(self) -> PackageEgressApproval:
        if self.decision.status is not EgressDecisionStatus.APPROVED:
            raise ValueError("package egress record must contain an approval")
        return self


class PromptTextComponent(FrozenModel):
    name: str
    text: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RequestPackageManifest(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    request: AIRequest
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt: PromptIdentity
    prompt_components: tuple[PromptTextComponent, ...]
    schema_identity: SchemaIdentity
    output_schema_json: CanonicalJSONValue
    source: SourceAssetRecord
    tile_manifest: TileSetManifest
    egress: EgressDecision
    estimated_request_bytes: int = Field(ge=0)
    estimated_cost_usd: Decimal = Field(default=Decimal("0"), ge=0)
    execution_instructions: tuple[str, ...]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _aware_creation_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")

    @field_validator("output_schema_json", mode="before")
    @classmethod
    def _canonical_schema(cls, value: object) -> object:
        return CanonicalJSONValue.from_input(value)


class ResponseOrigin(StrEnum):
    LIVE_EXECUTION = "live-execution"
    EXTERNAL_SUPPLIED = "external-supplied"


class SavedProviderResponse(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    origin: ResponseOrigin
    provider: Literal["openai", "anthropic"]
    model: NonEmptyStr
    response_id: NonEmptyStr
    request_id: NonEmptyStr
    job_id: NonEmptyStr
    run_id: NonEmptyStr
    phase_id: NonEmptyStr
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    task_type: TaskType
    prompt: PromptIdentity
    schema_identity: SchemaIdentity
    payload: CanonicalJSONValue
    usage: AIUsage = Field(default_factory=AIUsage)
    received_at: datetime

    @field_validator("received_at")
    @classmethod
    def _aware_received_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "received_at")

    @field_validator("payload", mode="before")
    @classmethod
    def _canonical_payload(cls, value: object) -> object:
        return CanonicalJSONValue.from_input(value)


class ValidatedResponseRecord(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    imported_without_current_execution: bool
    provider: Literal["openai", "anthropic"]
    model: NonEmptyStr
    response_id: NonEmptyStr
    request_id: NonEmptyStr
    job_id: NonEmptyStr
    run_id: NonEmptyStr
    phase_id: NonEmptyStr
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    task_type: TaskType
    prompt: PromptIdentity
    schema_identity: SchemaIdentity
    payload: CanonicalJSONValue
    usage: AIUsage
    validated_at: datetime

    @field_validator("validated_at")
    @classmethod
    def _aware_validation_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "validated_at")
