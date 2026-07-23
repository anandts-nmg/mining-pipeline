"""Offline Phase 03 review packaging and deterministic evidence promotion.

The handoff deliberately keeps three lifecycles separate: the provider proposal remains
``AI_DRAFT``; a named human records a review decision in an editable working layer; and only a
separate promotion operation writes ``ACCEPTED_EVIDENCE``.  Neither operation mutates the source
draft or the legacy Phase 03 evidence GeoPackage.
"""

from __future__ import annotations

import json
import math
import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, cast

import fiona
from pydantic import Field, field_validator, model_validator
from pyproj import CRS
from pyproj.exceptions import CRSError
from shapely import from_wkb
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry

from buduunkhad.ai.contracts import (
    FrozenModel,
    PromptIdentity,
    ReviewStatus,
    SchemaIdentity,
    SourceReference,
    TaskType,
    require_aware_datetime,
)
from buduunkhad.ai.fingerprint import sha256_bytes, sha256_file, sha256_value
from buduunkhad.core.qgis_project import (
    QgzLayer,
    line_symbol,
    point_symbol,
    polygon_outline,
    write_layered_qgz,
)
from buduunkhad.geospatial_ai.geometry_validation import GeometryRepairRecord, validate_geometry
from buduunkhad.geospatial_ai.ledger import AIJobLedger, LedgerJobView, LedgerStatus
from buduunkhad.geospatial_ai.manifests import (
    RequestPackageManifest,
    SourceAssetRecord,
    TileRecord,
    ValidatedResponseRecord,
)
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.pixel_world import transformed_source_extent
from buduunkhad.geospatial_ai.requests import (
    load_request_package,
    validate_package_ledger,
    verify_package_source,
)
from buduunkhad.geospatial_ai.responses import load_validated_response
from buduunkhad.geospatial_ai.schemas import DraftLayerName

REVIEW_FORMAT_VERSION = "1.0.0"
PROPOSAL_SCHEMA_VERSION = "1.0.0"
REVIEW_GPKG_NAME = "phase03-ai-review.gpkg"
REVIEW_QGZ_NAME = "phase03-ai-review.qgz"
REVIEW_MANIFEST_NAME = "review-manifest.json"
REVIEW_INSTRUCTIONS_NAME = "REVIEW_INSTRUCTIONS.md"


class Phase03HandoffError(ValueError):
    """A draft, review package, or promotion violates the Phase 03 handoff contract."""


class Phase03ReviewDecision(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    ACCEPTED_WITH_EDITS = "accepted_with_edits"
    REJECTED = "rejected"


class Phase03ReviewState(StrEnum):
    PENDING = "PENDING"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"


class Phase03EvidenceState(StrEnum):
    NOT_ACCEPTED = "NOT_ACCEPTED"
    ACCEPTED_EVIDENCE = "ACCEPTED_EVIDENCE"


class ResponseExecutionOrigin(StrEnum):
    LIVE_EXECUTION = "live_execution"
    SAVED_RESPONSE = "saved_response"


class ReviewProposalDigest(FrozenModel):
    proposal_id: str
    draft_layer: DraftLayerName
    original_record_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class _ReviewPackageIdentity(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    run_id: str
    job_id: str
    phase_id: Literal["03"] = "03"
    draft_relative_path: str
    draft_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_package_relative_path: str
    request_package_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    validated_response_relative_path: str
    validated_response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_asset_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_crs: Literal["EPSG:32647"] = "EPSG:32647"
    provider: str
    model: str
    response_id: str
    response_origin: ResponseExecutionOrigin
    prompt: PromptIdentity
    schema_identity: SchemaIdentity
    proposal_schema_version: Literal["1.0.0"] = "1.0.0"
    review_gpkg_relative_path: str = REVIEW_GPKG_NAME
    qgis_project_relative_path: str = REVIEW_QGZ_NAME
    qgis_project_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_findings_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    existing_evidence_relative_path: str | None = None
    existing_evidence_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_preview_files: tuple[tuple[str, str], ...]
    proposals: tuple[ReviewProposalDigest, ...] = Field(min_length=1)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _aware_created_at(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")

    @model_validator(mode="after")
    def _complete_existing_evidence(self) -> _ReviewPackageIdentity:
        if (self.existing_evidence_relative_path is None) != (
            self.existing_evidence_sha256 is None
        ):
            raise ValueError("existing evidence path and digest must be recorded together")
        identities = tuple(item.proposal_id for item in self.proposals)
        if len(set(identities)) != len(identities):
            raise ValueError("review manifest contains duplicate proposal identities")
        return self


class ReviewPackageManifest(_ReviewPackageIdentity):
    package_id: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _sealed_identity(self) -> ReviewPackageManifest:
        identity = _ReviewPackageIdentity.model_validate(
            self.model_dump(mode="python", exclude={"package_id"})
        )
        if self.package_id != sha256_value(identity):
            raise ValueError("review manifest package identity is invalid")
        return self


class PromotedFeature(FrozenModel):
    proposal_id: str
    accepted_feature_id: str
    output_layer: str
    decision: Literal["accepted", "accepted_with_edits"]
    reviewed_geometry_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_record_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer: str
    reviewed_at: datetime
    review_note: str

    @field_validator("reviewed_at")
    @classmethod
    def _aware_reviewed_at(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "reviewed_at")


class PromotionAuditEntry(FrozenModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    promotion_contract_version: Literal["1.0.0"] = "1.0.0"
    audit_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_entry_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_geopackage_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_package_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    run_id: str
    output_relative_path: str
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    promoted_features: tuple[PromotedFeature, ...] = Field(min_length=1)
    promoted_at: datetime

    @field_validator("promoted_at")
    @classmethod
    def _aware_promoted_at(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "promoted_at")


class PromotionResult(FrozenModel):
    output: Path
    audit_ledger: Path
    promoted_feature_ids: tuple[str, ...]
    created: bool


@dataclass(frozen=True)
class _Authority:
    run_directory: Path
    package_directory: Path
    package: RequestPackageManifest
    response_path: Path
    response: ValidatedResponseRecord
    ledger_view: LedgerJobView
    response_origin: ResponseExecutionOrigin


@dataclass(frozen=True)
class _DraftRecord:
    layer: DraftLayerName
    geometry: BaseGeometry
    properties: dict[str, object]


@dataclass(frozen=True)
class _ReviewedRecord:
    layer: DraftLayerName
    geometry: BaseGeometry
    properties: dict[str, object]
    decision: Phase03ReviewDecision
    reviewed_geometry_sha256: str


_EXPECTED_GEOMETRIES: dict[DraftLayerName, str] = {
    DraftLayerName.GEOLOGY_UNITS: "Polygon",
    DraftLayerName.FAULTS_STRUCTURES: "LineString",
    DraftLayerName.INTRUSIVE_CONTACTS: "LineString",
    DraftLayerName.DYKES_VEINS: "LineString",
    DraftLayerName.MINERAL_OCCURRENCES: "Point",
    DraftLayerName.ALTERATION_ZONES: "Polygon",
    DraftLayerName.PROSPECT_PROPOSALS: "Polygon",
}

_OUTPUT_LAYERS: dict[DraftLayerName, tuple[str, str]] = {
    DraftLayerName.GEOLOGY_UNITS: ("geology_units_50k_polygon", "BUD-GEO50"),
    DraftLayerName.FAULTS_STRUCTURES: ("faults_structures_line", "BUD-STR"),
    DraftLayerName.INTRUSIVE_CONTACTS: ("intrusive_contacts_line", "BUD-INT"),
    DraftLayerName.DYKES_VEINS: ("dyke_vein_line", "BUD-DYK"),
    DraftLayerName.MINERAL_OCCURRENCES: ("mineral_occurrences_point", "BUD-MIN"),
    DraftLayerName.ALTERATION_ZONES: ("ai_accepted_alteration_zones_polygon", "BUD-ALT"),
    DraftLayerName.PROSPECT_PROPOSALS: ("prospectivity_target_zones_polygon", "BUD-TGT"),
}

_REVIEW_PROPERTIES: dict[str, str] = {
    "proposal_id": "str",
    "draft_layer": "str",
    "feature_type": "str",
    "legend_code": "str",
    "proposal_state": "str",
    "review_state": "str",
    "evidence_state": "str",
    "review_decision": "str",
    "reviewer": "str",
    "reviewed_at": "str",
    "review_note": "str",
    "accepted_id": "str",
    "run_id": "str",
    "phase_id": "str",
    "job_id": "str",
    "source_id": "str",
    "source_sha": "str",
    "source_refs": "str",
    "tile_ids": "str",
    "request_fp": "str",
    "response_id": "str",
    "response_sha": "str",
    "response_origin": "str",
    "provider": "str",
    "model": "str",
    "prompt_id": "str",
    "prompt_ver": "str",
    "prompt_sha": "str",
    "schema_id": "str",
    "schema_ver": "str",
    "schema_sha": "str",
    "proposal_schema": "str",
    "pixel_json": "str",
    "ai_original_wkb": "str",
    "draft_output_wkb": "str",
    "original_geom_sha": "str",
    "reviewed_geom_sha": "str",
    "reviewed_geom_prov": "str",
    "attributes": "str",
    "confidence": "float",
    "conf_json": "str",
    "evidence": "str",
    "limitations": "str",
    "risk_level": "str",
    "validation": "str",
    "repair_status": "str",
    "repair_json": "str",
    "content_sha": "str",
    "draft_record_sha": "str",
}

_MUTABLE_REVIEW_FIELDS = frozenset(
    {"review_state", "review_decision", "reviewer", "reviewed_at", "review_note"}
)

_ACCEPTED_PROPERTIES: dict[str, str] = {
    "feature_id": "str",
    "proposal_id": "str",
    "feature_type": "str",
    "legend_code": "str",
    "processing_phase": "str",
    "source_raw_input_no": "str",
    "source_raw_filename": "str",
    "source_group": "str",
    "source_scale": "str",
    "geometry_type": "str",
    "evidence_type": "str",
    "validation_status": "str",
    "confidence": "str",
    "limitation": "str",
    "processing_version": "str",
    "reviewer": "str",
    "review_date": "str",
    "proposal_state": "str",
    "review_state": "str",
    "evidence_state": "str",
    "review_decision": "str",
    "reviewed_at": "str",
    "review_note": "str",
    "source_asset_id": "str",
    "source_sha256": "str",
    "source_references_json": "str",
    "source_tile_ids_json": "str",
    "request_fingerprint": "str",
    "response_id": "str",
    "response_sha256": "str",
    "response_origin": "str",
    "provider": "str",
    "model": "str",
    "prompt_id": "str",
    "prompt_version": "str",
    "prompt_sha256": "str",
    "schema_id": "str",
    "schema_version": "str",
    "schema_sha256": "str",
    "proposal_schema_version": "str",
    "original_pixel_geometry": "str",
    "original_geometry_wkb": "str",
    "draft_output_wkb": "str",
    "reviewed_geometry_sha256": "str",
    "reviewed_geometry_provenance": "str",
    "repair_status": "str",
    "repair_json": "str",
    "draft_geometry_validation_status": "str",
    "attributes_json": "str",
    "confidence_components_json": "str",
    "evidence_json": "str",
    "limitations_json": "str",
    "risk_level": "str",
    "content_sha256": "str",
}


def import_ai_draft_review_package(
    draft: Path,
    review_package: Path,
    *,
    roots: StorageRoots,
    run_id: str,
    expected_target_crs: str,
    existing_evidence: Path | None = None,
    now: datetime | None = None,
) -> ReviewPackageManifest:
    """Resolve one processed draft and create an isolated, editable review package."""

    if expected_target_crs != "EPSG:32647":
        raise Phase03HandoffError("Phase 03 review packages require EPSG:32647")
    draft_path = roots.assert_run_artifact(draft, run_id=run_id)
    authority = _resolve_authority(draft_path, roots=roots, run_id=run_id)
    records, findings = _load_and_validate_draft(
        draft_path,
        authority=authority,
        expected_target_crs=expected_target_crs,
    )
    destination = roots.assert_writable(review_package, run_id=run_id)
    if destination.exists():
        manifest = load_review_package(destination, roots=roots)
        _validate_existing_review_package(
            destination,
            manifest,
            draft_path=draft_path,
            authority=authority,
        )
        return manifest
    destination.parent.mkdir(parents=True, exist_ok=True)
    if existing_evidence is not None:
        existing_evidence = existing_evidence.expanduser().resolve(strict=True)
        if not existing_evidence.is_file():
            raise Phase03HandoffError("existing Phase 03 evidence must be a regular file")
    timestamp = now or datetime.now(UTC)
    timestamp = require_aware_datetime(timestamp, "created_at")
    with TemporaryDirectory(prefix="phase03-review-", dir=destination.parent) as temporary:
        temporary_path = roots.assert_writable(Path(temporary), run_id=run_id)
        review_gpkg = temporary_path / REVIEW_GPKG_NAME
        original_digests = _write_review_geopackage(
            review_gpkg,
            records=records,
            findings=findings,
            authority=authority,
        )
        preview_files = _copy_source_previews(
            temporary_path,
            authority=authority,
            records=records,
        )
        existing_relative: str | None = None
        existing_sha: str | None = None
        copied_existing: Path | None = None
        if existing_evidence is not None:
            existing_directory = temporary_path / "existing"
            existing_directory.mkdir()
            copied_existing = existing_directory / "phase03-existing-evidence.gpkg"
            before = sha256_file(existing_evidence)
            shutil.copy2(existing_evidence, copied_existing)
            after = sha256_file(existing_evidence)
            if before != after or sha256_file(copied_existing) != before:
                raise Phase03HandoffError("existing evidence changed while it was copied")
            existing_relative = copied_existing.relative_to(temporary_path).as_posix()
            existing_sha = before
        qgis_project = temporary_path / REVIEW_QGZ_NAME
        _write_review_project(
            qgis_project,
            review_gpkg=review_gpkg,
            source_previews=tuple(temporary_path / item[0] for item in preview_files),
            existing_evidence=copied_existing,
            source=authority.package.source,
        )
        _write_review_instructions(temporary_path / REVIEW_INSTRUCTIONS_NAME)
        proposals = tuple(
            ReviewProposalDigest(
                proposal_id=str(record.properties["proposal_id"]),
                draft_layer=record.layer,
                original_record_sha256=original_digests[str(record.properties["proposal_id"])],
            )
            for record in sorted(
                records,
                key=lambda item: (item.layer.value, str(item.properties["proposal_id"])),
            )
        )
        identity = _ReviewPackageIdentity(
            run_id=run_id,
            job_id=authority.package.request.job_id,
            draft_relative_path=draft_path.relative_to(authority.run_directory).as_posix(),
            draft_sha256=sha256_file(draft_path),
            request_package_relative_path=authority.package_directory.relative_to(
                authority.run_directory
            ).as_posix(),
            request_package_sha256=sha256_file(
                authority.package_directory / "request-package.json"
            ),
            validated_response_relative_path=authority.response_path.relative_to(
                authority.run_directory
            ).as_posix(),
            validated_response_sha256=sha256_file(authority.response_path),
            request_fingerprint=authority.package.request_fingerprint,
            source_asset_id=authority.package.source.asset_id,
            source_sha256=authority.package.source.sha256,
            provider=authority.response.provider,
            model=authority.response.model,
            response_id=authority.response.response_id,
            response_origin=authority.response_origin,
            prompt=authority.package.prompt,
            schema_identity=authority.package.schema_identity,
            qgis_project_sha256=sha256_file(qgis_project),
            validation_findings_sha256=_validation_findings_digest(review_gpkg),
            existing_evidence_relative_path=existing_relative,
            existing_evidence_sha256=existing_sha,
            source_preview_files=preview_files,
            proposals=proposals,
            created_at=timestamp,
        )
        manifest = ReviewPackageManifest(
            **identity.model_dump(mode="python"),
            package_id=sha256_value(identity),
        )
        (temporary_path / REVIEW_MANIFEST_NAME).write_text(
            manifest.model_dump_json(indent=2), encoding="utf-8", newline="\n"
        )
        Path(temporary).replace(destination)
    return manifest


def promote_reviewed_evidence(
    review_package: Path,
    output: Path,
    *,
    roots: StorageRoots,
    now: datetime | None = None,
) -> PromotionResult:
    """Promote explicitly accepted review rows into an immutable standalone evidence package."""

    package_directory = roots.assert_run_artifact(review_package)
    if not package_directory.is_dir():
        raise Phase03HandoffError("review package must be a directory")
    manifest = load_review_package(package_directory, roots=roots)
    output_path = roots.assert_writable(output, run_id=manifest.run_id)
    if output_path.suffix.casefold() != ".gpkg":
        raise Phase03HandoffError("promotion output must be a GeoPackage")
    audit_path = roots.assert_writable(
        output_path.with_suffix(".promotion-ledger.jsonl"), run_id=manifest.run_id
    )
    authority = _resolve_authority(
        roots.assert_run_artifact(
            roots.run_directory(manifest.run_id) / manifest.draft_relative_path,
            run_id=manifest.run_id,
        ),
        roots=roots,
        run_id=manifest.run_id,
    )
    _validate_existing_review_package(
        package_directory,
        manifest,
        draft_path=roots.run_directory(manifest.run_id) / manifest.draft_relative_path,
        authority=authority,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = roots.assert_writable(
        output_path.with_suffix(".promotion.lock"), run_id=manifest.run_id
    )
    with _exclusive_promotion_lock(lock_path):
        review_gpkg = _package_file(package_directory, manifest.review_gpkg_relative_path)
        review_gpkg_sha = sha256_file(review_gpkg)
        reviewed = _load_reviewed_records(package_directory, manifest, authority=authority)
        if sha256_file(review_gpkg) != review_gpkg_sha:
            raise Phase03HandoffError("review GeoPackage changed during promotion")
        promotable = tuple(
            record
            for record in reviewed
            if record.decision
            in {Phase03ReviewDecision.ACCEPTED, Phase03ReviewDecision.ACCEPTED_WITH_EDITS}
        )
        if not promotable:
            raise Phase03HandoffError("review package contains no explicitly accepted proposals")
        promoted = tuple(_promoted_identity(record, manifest) for record in promotable)
        review_manifest_sha = sha256_file(package_directory / REVIEW_MANIFEST_NAME)
        if output_path.exists() or audit_path.exists():
            return _validate_idempotent_promotion(
                output_path,
                audit_path,
                manifest=manifest,
                promoted=promoted,
                review_manifest_sha=review_manifest_sha,
                review_gpkg_sha=review_gpkg_sha,
            )
        timestamp = now or datetime.now(UTC)
        timestamp = require_aware_datetime(timestamp, "promoted_at")
        latest_review = max(
            datetime.fromisoformat(str(record.properties["reviewed_at"])) for record in promotable
        )
        if timestamp < latest_review:
            raise Phase03HandoffError("promotion timestamp predates an accepted human review")
        with TemporaryDirectory(prefix="phase03-promotion-", dir=output_path.parent) as temporary:
            temporary_path = roots.assert_writable(Path(temporary), run_id=manifest.run_id)
            staged_output = temporary_path / output_path.name
            _write_promoted_geopackage(
                staged_output,
                records=promotable,
                promoted=promoted,
                manifest=manifest,
                authority=authority,
            )
            output_sha = sha256_file(staged_output)
            output_relative = output_path.relative_to(
                roots.run_directory(manifest.run_id)
            ).as_posix()
            audit_id = sha256_value(
                {
                    "review_package_id": manifest.package_id,
                    "review_manifest_sha256": review_manifest_sha,
                    "review_geopackage_sha256": review_gpkg_sha,
                    "output_relative_path": output_relative,
                    "promoted_features": promoted,
                }
            )
            audit = PromotionAuditEntry(
                audit_id=audit_id,
                review_manifest_sha256=review_manifest_sha,
                review_geopackage_sha256=review_gpkg_sha,
                review_package_id=manifest.package_id,
                run_id=manifest.run_id,
                output_relative_path=output_relative,
                output_sha256=output_sha,
                promoted_features=promoted,
                promoted_at=timestamp,
            )
            staged_audit = temporary_path / audit_path.name
            staged_audit.write_text(audit.model_dump_json() + "\n", encoding="utf-8", newline="\n")
            _commit_staged_promotion(
                staged_output,
                staged_audit,
                output=output_path,
                audit_path=audit_path,
            )
    return PromotionResult(
        output=output_path,
        audit_ledger=audit_path,
        promoted_feature_ids=tuple(item.accepted_feature_id for item in promoted),
        created=True,
    )


def load_review_package(review_package: Path, *, roots: StorageRoots) -> ReviewPackageManifest:
    package_directory = roots.assert_run_artifact(review_package)
    if not package_directory.is_dir():
        raise Phase03HandoffError("review package must be a directory")
    try:
        manifest = ReviewPackageManifest.model_validate(
            _load_unique_json(package_directory / REVIEW_MANIFEST_NAME)
        )
    except ValueError as exc:
        raise Phase03HandoffError("review package manifest is invalid") from exc
    roots.assert_run_artifact(package_directory, run_id=manifest.run_id)
    return manifest


def _resolve_authority(draft: Path, *, roots: StorageRoots, run_id: str) -> _Authority:
    run_directory = roots.run_directory(run_id)
    draft_path = roots.assert_run_artifact(draft, run_id=run_id)
    job_id = draft_path.stem.removesuffix("_AI_DRAFT")
    if not job_id or draft_path.name != f"{job_id}_AI_DRAFT.gpkg":
        raise Phase03HandoffError("draft path does not use the validated workflow identity")
    ledger = AIJobLedger(run_directory / "ai_jobs.sqlite", roots=roots, run_id=run_id)
    try:
        view = ledger.inspect(job_id)
    except (OSError, RuntimeError, ValueError) as exc:
        raise Phase03HandoffError(
            "draft does not resolve to an authoritative processed job"
        ) from exc
    if view.status is not LedgerStatus.PROCESSED:
        raise Phase03HandoffError("draft job is not in the processed ledger state")
    if view.job.phase_id != "03" or view.job.task_type is not TaskType.GEOLOGICAL_FEATURE_PROPOSAL:
        raise Phase03HandoffError("draft job is not a Phase 03 geological feature proposal")
    processed = view.events[-1]
    expected_relative = draft_path.relative_to(run_directory).as_posix()
    if (
        processed.status is not LedgerStatus.PROCESSED
        or processed.response_file != expected_relative
        or processed.response_sha256 != sha256_file(draft_path)
    ):
        raise Phase03HandoffError("draft bytes differ from the append-only processed ledger event")
    package_directory = _find_request_package(run_directory, job_id)
    package = load_request_package(package_directory)
    verify_package_source(package, roots=roots)
    if validate_package_ledger(package, ledger, package_directory) != view:
        raise Phase03HandoffError("request package ledger view changed during resolution")
    ingested = next(
        (
            event
            for event in view.events
            if event.status is LedgerStatus.INGESTED and event.response_file is not None
        ),
        None,
    )
    if ingested is None or ingested.response_sha256 is None:
        raise Phase03HandoffError("processed draft has no authoritative ingested response")
    response_relative = ingested.response_file
    assert response_relative is not None
    response_path = roots.assert_run_artifact(run_directory / response_relative, run_id=run_id)
    if sha256_file(response_path) != ingested.response_sha256:
        raise Phase03HandoffError("validated response bytes differ from the job ledger")
    response = load_validated_response(response_path)
    comparisons = (
        response.job_id == job_id,
        response.run_id == run_id,
        response.phase_id == "03",
        response.request_id == package.request.request_id,
        response.request_fingerprint == package.request_fingerprint,
        response.task_type is TaskType.GEOLOGICAL_FEATURE_PROPOSAL,
        response.prompt == package.prompt,
        response.schema_identity == package.schema_identity,
        response.provider == package.request.provider.provider,
        response.model == package.request.provider.model,
    )
    if not all(comparisons):
        raise Phase03HandoffError("validated response is not bound to the processed draft request")
    origin = (
        ResponseExecutionOrigin.LIVE_EXECUTION
        if any(event.status is LedgerStatus.SUCCEEDED for event in view.events)
        else ResponseExecutionOrigin.SAVED_RESPONSE
    )
    return _Authority(
        run_directory=run_directory,
        package_directory=package_directory,
        package=package,
        response_path=response_path,
        response=response,
        ledger_view=view,
        response_origin=origin,
    )


def _find_request_package(run_directory: Path, job_id: str) -> Path:
    candidates: list[Path] = []
    requests = run_directory / "requests"
    if requests.exists():
        for manifest_path in sorted(requests.glob("*/request-package.json")):
            try:
                value = _load_unique_json(manifest_path)
            except Phase03HandoffError:
                continue
            request = value.get("request") if isinstance(value, dict) else None
            if isinstance(request, dict) and request.get("job_id") == job_id:
                candidates.append(manifest_path.parent)
    if len(candidates) != 1:
        raise Phase03HandoffError("processed draft must resolve to exactly one request package")
    return candidates[0]


def _load_and_validate_draft(
    draft: Path,
    *,
    authority: _Authority,
    expected_target_crs: str,
) -> tuple[tuple[_DraftRecord, ...], tuple[dict[str, object], ...]]:
    expected_layers = {item.value for item in DraftLayerName} | {"validation_findings"}
    if set(fiona.listlayers(draft)) != expected_layers:
        raise Phase03HandoffError("draft GeoPackage has missing or unsupported layers")
    records: list[_DraftRecord] = []
    identities: set[str] = set()
    for layer in DraftLayerName:
        with fiona.open(draft, layer=layer.value) as collection:
            _require_collection_crs(collection, expected_target_crs)
            for raw in collection:
                geometry = _shape_feature_geometry(raw["geometry"], "draft proposal")
                properties = dict(raw["properties"])
                _validate_draft_record(
                    layer,
                    geometry,
                    properties,
                    authority=authority,
                )
                proposal_id = str(properties["feature_id"])
                if proposal_id in identities:
                    raise Phase03HandoffError("draft contains duplicate proposal identities")
                identities.add(proposal_id)
                review_properties = _review_properties(
                    layer,
                    geometry,
                    properties,
                    authority=authority,
                )
                records.append(
                    _DraftRecord(
                        layer=layer,
                        geometry=geometry,
                        properties=review_properties,
                    )
                )
    findings: list[dict[str, object]] = []
    with fiona.open(draft, layer="validation_findings") as collection:
        _require_collection_crs(collection, expected_target_crs)
        for raw in collection:
            item = {
                "geometry": raw["geometry"],
                "properties": dict(raw["properties"]),
            }
            feature_id = str(item["properties"].get("feature_id", ""))
            if feature_id not in identities:
                raise Phase03HandoffError("validation finding references an unknown proposal")
            findings.append(item)
    if not records:
        raise Phase03HandoffError("draft contains no geological proposals")
    return tuple(records), tuple(findings)


def _validate_draft_record(
    layer: DraftLayerName,
    geometry: BaseGeometry,
    properties: dict[str, object],
    *,
    authority: _Authority,
) -> None:
    required = {
        "feature_id",
        "feature_type",
        "legend_code",
        "run_id",
        "phase_id",
        "job_id",
        "source_id",
        "source_sha",
        "source_refs",
        "tile_ids",
        "prompt_id",
        "prompt_ver",
        "prompt_sha",
        "schema_id",
        "schema_ver",
        "schema_sha",
        "provider",
        "model",
        "response_id",
        "pixel_json",
        "original_wkb",
        "output_wkb",
        "geom_status",
        "repair_status",
        "repair_json",
        "content_sha",
        "review_status",
    }
    if not required <= properties.keys():
        raise Phase03HandoffError("draft feature has incomplete provenance")
    package = authority.package
    response = authority.response
    comparisons = (
        properties["run_id"] == package.request.run_id,
        properties["phase_id"] == "03",
        properties["job_id"] == package.request.job_id,
        properties["source_id"] == package.source.asset_id,
        properties["source_sha"] == package.source.sha256,
        properties["prompt_id"] == package.prompt.prompt_id,
        properties["prompt_ver"] == package.prompt.version,
        properties["prompt_sha"] == package.prompt.sha256,
        properties["schema_id"] == package.schema_identity.schema_id,
        properties["schema_ver"] == package.schema_identity.version,
        properties["schema_sha"] == package.schema_identity.sha256,
        properties["provider"] == response.provider,
        properties["model"] == response.model,
        properties["response_id"] == response.response_id,
        properties["review_status"] == ReviewStatus.AI_DRAFT.value,
    )
    if not all(comparisons):
        raise Phase03HandoffError("draft feature provenance is inconsistent with authority")
    if (
        geometry.is_empty
        or not geometry.is_valid
        or not all(math.isfinite(value) for value in geometry.bounds)
    ):
        raise Phase03HandoffError("draft feature geometry is invalid")
    if geometry.geom_type not in _accepted_geometry_types(_EXPECTED_GEOMETRIES[layer]):
        raise Phase03HandoffError(f"unsupported geometry type for {layer.value}")
    if geometry.wkb.hex() != str(properties["output_wkb"]).lower():
        raise Phase03HandoffError("draft feature geometry differs from its stored output WKB")
    try:
        original = from_wkb(bytes.fromhex(str(properties["original_wkb"])))
    except (TypeError, ValueError) as exc:
        raise Phase03HandoffError("draft original geometry record is invalid") from exc
    if original.is_empty or original.geom_type not in _accepted_geometry_types(
        _EXPECTED_GEOMETRIES[layer]
    ):
        raise Phase03HandoffError("draft original geometry has an unsupported type")
    status = str(properties["geom_status"])
    repair_status = str(properties["repair_status"])
    repair_json = str(properties["repair_json"] or "")
    if status not in {"valid", "valid-with-findings", "repaired"}:
        raise Phase03HandoffError("draft feature did not pass deterministic geometry validation")
    if repair_status == "not-repaired":
        if repair_json or status == "repaired":
            raise Phase03HandoffError("draft repair provenance is inconsistent")
    elif repair_status == "repaired":
        try:
            repair = GeometryRepairRecord.model_validate_json(repair_json)
        except ValueError as exc:
            raise Phase03HandoffError("draft repair record is invalid") from exc
        if status != "repaired" or repair.repaired_geometry_sha256 != sha256_bytes(geometry.wkb):
            raise Phase03HandoffError("draft repaired geometry does not match its repair record")
    else:
        raise Phase03HandoffError("draft has an unsupported repair status")
    _validate_json_field(properties, "pixel_json")
    _validate_json_field(properties, "tile_ids")
    _validate_json_field(properties, "source_refs")
    for name in ("attributes", "conf_json", "evidence", "limitations"):
        if name in properties:
            _validate_json_field(properties, name)
    _validate_source_references(str(properties["source_refs"]), package)
    content_sha = str(properties["content_sha"])
    if len(content_sha) != 64 or any(char not in "0123456789abcdef" for char in content_sha):
        raise Phase03HandoffError("draft content digest is invalid")


def _review_properties(
    layer: DraftLayerName,
    geometry: BaseGeometry,
    draft: dict[str, object],
    *,
    authority: _Authority,
) -> dict[str, object]:
    original_wkb = str(draft["original_wkb"])
    base = {
        "proposal_id": str(draft["feature_id"]),
        "draft_layer": layer.value,
        "feature_type": str(draft["feature_type"]),
        "legend_code": str(draft["legend_code"] or ""),
        "proposal_state": ReviewStatus.AI_DRAFT.value,
        "review_state": Phase03ReviewState.PENDING.value,
        "evidence_state": Phase03EvidenceState.NOT_ACCEPTED.value,
        "review_decision": Phase03ReviewDecision.PENDING.value,
        "reviewer": "",
        "reviewed_at": "",
        "review_note": "",
        "accepted_id": "",
        "run_id": str(draft["run_id"]),
        "phase_id": str(draft["phase_id"]),
        "job_id": str(draft["job_id"]),
        "source_id": str(draft["source_id"]),
        "source_sha": str(draft["source_sha"]),
        "source_refs": str(draft["source_refs"]),
        "tile_ids": str(draft["tile_ids"]),
        "request_fp": authority.package.request_fingerprint,
        "response_id": authority.response.response_id,
        "response_sha": sha256_file(authority.response_path),
        "response_origin": authority.response_origin.value,
        "provider": authority.response.provider,
        "model": authority.response.model,
        "prompt_id": authority.package.prompt.prompt_id,
        "prompt_ver": authority.package.prompt.version,
        "prompt_sha": authority.package.prompt.sha256,
        "schema_id": authority.package.schema_identity.schema_id,
        "schema_ver": authority.package.schema_identity.version,
        "schema_sha": authority.package.schema_identity.sha256,
        "proposal_schema": PROPOSAL_SCHEMA_VERSION,
        "pixel_json": str(draft["pixel_json"]),
        "ai_original_wkb": original_wkb,
        "draft_output_wkb": geometry.wkb.hex(),
        "original_geom_sha": sha256_bytes(bytes.fromhex(original_wkb)),
        "reviewed_geom_sha": sha256_bytes(geometry.wkb),
        "reviewed_geom_prov": "unreviewed copy of deterministic draft output",
        "attributes": str(draft.get("attributes", "{}")),
        "confidence": _float_value(draft.get("confidence", 0.0), "confidence"),
        "conf_json": str(draft.get("conf_json", "[]")),
        "evidence": str(draft.get("evidence", "[]")),
        "limitations": str(draft.get("limitations", "[]")),
        "risk_level": str(draft.get("risk_level", "")),
        "validation": str(draft["geom_status"]),
        "repair_status": str(draft["repair_status"]),
        "repair_json": str(draft["repair_json"] or ""),
        "content_sha": str(draft["content_sha"]),
        "draft_record_sha": "",
    }
    base["draft_record_sha"] = _record_sha(geometry, base, exclude={"draft_record_sha"})
    return base


def _write_review_geopackage(
    path: Path,
    *,
    records: tuple[_DraftRecord, ...],
    findings: tuple[dict[str, object], ...],
    authority: _Authority,
) -> dict[str, str]:
    crs_wkt = CRS.from_epsg(32647).to_wkt()
    by_layer: dict[DraftLayerName, list[_DraftRecord]] = {layer: [] for layer in DraftLayerName}
    for record in records:
        by_layer[record.layer].append(record)
    original_digests: dict[str, str] = {}
    schema = {"geometry": "Unknown", "properties": _REVIEW_PROPERTIES}
    for layer in DraftLayerName:
        for prefix in ("original", "review"):
            with fiona.open(
                path,
                mode="w",
                driver="GPKG",
                layer=f"{prefix}_{layer.value}",
                schema=schema,
                crs_wkt=crs_wkt,
            ) as collection:
                for record in by_layer[layer]:
                    collection.write(
                        {"geometry": mapping(record.geometry), "properties": record.properties}
                    )
                    if prefix == "original":
                        proposal_id = str(record.properties["proposal_id"])
                        original_digests[proposal_id] = _record_sha(
                            record.geometry, record.properties
                        )
    finding_schema = {
        "geometry": "Point",
        "properties": {
            "feature_id": "str",
            "code": "str",
            "severity": "str",
            "message": "str",
        },
    }
    with fiona.open(
        path,
        mode="w",
        driver="GPKG",
        layer="validation_findings",
        schema=finding_schema,
        crs_wkt=crs_wkt,
    ) as collection:
        for finding in findings:
            collection.write(finding)
    return original_digests


def _copy_source_previews(
    destination: Path,
    *,
    authority: _Authority,
    records: tuple[_DraftRecord, ...],
) -> tuple[tuple[str, str], ...]:
    tile_ids = {
        tile_id
        for record in records
        for tile_id in _json_string_list(str(record.properties["tile_ids"]), "tile_ids")
    }
    tiles = {tile.tile_id: tile for tile in authority.package.tile_manifest.tiles}
    if not tile_ids or not tile_ids <= tiles.keys():
        raise Phase03HandoffError("review proposals do not resolve to authoritative source tiles")
    source_directory = destination / "source"
    source_directory.mkdir()
    source_crs = authority.package.source.source_crs
    if source_crs is None:
        raise Phase03HandoffError("review source has no CRS for portable QGIS previews")
    crs = CRS.from_user_input(source_crs)
    if crs.to_epsg() is None:
        raise Phase03HandoffError("review source CRS has no EPSG identity for QGIS previews")
    copied: list[tuple[str, str]] = []
    for tile_id in sorted(tile_ids):
        tile = tiles[tile_id]
        source = _package_file(authority.package_directory, tile.image_relative_path)
        image = source_directory / f"{tile.tile_id}.png"
        shutil.copy2(source, image)
        if sha256_file(image) != tile.image_sha256:
            raise Phase03HandoffError("source preview copy differs from the request package")
        world = image.with_suffix(".pgw")
        world.write_text(
            _world_file(authority.package.source, tile), encoding="ascii", newline="\n"
        )
        projection = image.with_suffix(".prj")
        projection.write_text(crs.to_wkt(), encoding="utf-8", newline="\n")
        for item in (image, world, projection):
            copied.append((item.relative_to(destination).as_posix(), sha256_file(item)))
    return tuple(copied)


def _world_file(source: SourceAssetRecord, tile: TileRecord) -> str:
    affine = source.affine
    c = affine.c + affine.a * tile.x_offset + affine.b * tile.y_offset
    f = affine.f + affine.d * tile.x_offset + affine.e * tile.y_offset
    center_x = c + (affine.a + affine.b) / 2
    center_y = f + (affine.d + affine.e) / 2
    return (
        "\n".join(
            format(value, ".17g")
            for value in (affine.a, affine.d, affine.b, affine.e, center_x, center_y)
        )
        + "\n"
    )


def _write_review_project(
    path: Path,
    *,
    review_gpkg: Path,
    source_previews: tuple[Path, ...],
    existing_evidence: Path | None,
    source: SourceAssetRecord,
) -> None:
    source_epsg = CRS.from_user_input(source.source_crs).to_epsg() if source.source_crs else None
    if source_epsg is None:
        raise Phase03HandoffError("source preview CRS cannot be represented in QGIS")
    layers: list[QgzLayer] = []
    for preview in source_previews:
        if preview.suffix.casefold() != ".png":
            continue
        layers.append(
            QgzLayer(
                name=f"Source {preview.stem}",
                source=_relative(path.parent, preview),
                geometry="Raster",
                group="01_Source",
                provider="gdal",
                visible=True,
                epsg=source_epsg,
                read_only=True,
            )
        )
    if existing_evidence is not None:
        for layer_name in sorted(fiona.listlayers(existing_evidence)):
            with fiona.open(existing_evidence, layer=layer_name) as collection:
                schema = collection.schema
                geometry_name = None if schema is None else schema.get("geometry")
                if geometry_name is None:
                    raise Phase03HandoffError(
                        f"Existing evidence layer {layer_name!r} has no geometry schema."
                    )
                geometry = _qgis_geometry(geometry_name)
            layers.append(
                QgzLayer(
                    name=f"Existing {layer_name}",
                    source=(f"{_relative(path.parent, existing_evidence)}|layername={layer_name}"),
                    geometry=geometry,
                    group="02_Existing_Evidence",
                    provider="ogr",
                    visible=False,
                    read_only=True,
                )
            )
    review_relative = _relative(path.parent, review_gpkg)
    for layer in DraftLayerName:
        geometry = _EXPECTED_GEOMETRIES[layer]
        layers.append(
            QgzLayer(
                name=f"Original AI_DRAFT {layer.value}",
                source=f"{review_relative}|layername=original_{layer.value}",
                geometry=geometry,
                symbol=_style(layer, "draft"),
                group="03_AI_DRAFT",
                visible=False,
                read_only=True,
            )
        )
        layers.append(
            QgzLayer(
                name=f"Pending Review {layer.value}",
                source=f"{review_relative}|layername=review_{layer.value}",
                geometry=geometry,
                symbol=_style(layer, "draft"),
                group="03_AI_DRAFT",
                subset_string="\"review_decision\" = 'pending'",
                visible=True,
            )
        )
    layers.append(
        QgzLayer(
            name="Validation Findings",
            source=f"{review_relative}|layername=validation_findings",
            geometry="Point",
            symbol=point_symbol("255,0,255,255", 2.5),
            group="04_Validation_Findings",
            visible=True,
            read_only=True,
        )
    )
    for layer in DraftLayerName:
        geometry = _EXPECTED_GEOMETRIES[layer]
        source_value = f"{review_relative}|layername=review_{layer.value}"
        layers.append(
            QgzLayer(
                name=f"Accepted {layer.value}",
                source=source_value,
                geometry=geometry,
                symbol=_style(layer, "accepted"),
                group="05_Human_Accepted",
                subset_string=("\"review_decision\" IN ('accepted','accepted_with_edits')"),
                visible=True,
            )
        )
        layers.append(
            QgzLayer(
                name=f"Rejected {layer.value}",
                source=source_value,
                geometry=geometry,
                symbol=_style(layer, "rejected"),
                group="06_Human_Rejected",
                subset_string="\"review_decision\" = 'rejected'",
                visible=False,
            )
        )
    write_layered_qgz(
        path,
        epsg=32647,
        title="Buduunkhad Phase 03 AI Draft Review",
        layers=layers,
    )


def _style(layer: DraftLayerName, state: str):
    geometry = _EXPECTED_GEOMETRIES[layer]
    if state == "accepted":
        color = "0,150,70,255"
        dash = False
    elif state == "rejected":
        color = "160,160,160,255"
        dash = True
    else:
        color = "230,0,180,255"
        dash = True
    if geometry == "Point":
        return point_symbol(color, 3.0)
    if geometry == "LineString":
        return line_symbol(color, 0.7, dash=dash)
    return polygon_outline(color, 0.7, dash=dash)


def _write_review_instructions(path: Path) -> None:
    path.write_text(
        "# Phase 03 AI draft review\n\n"
        "Edit only layers named `Pending Review ...`. Keep the `Original AI_DRAFT ...` layers "
        "unchanged; promotion verifies their exact record digests.\n\n"
        "For each reviewed feature set `review_state` to `HUMAN_REVIEWED`, set "
        "`review_decision` to `accepted`, `accepted_with_edits`, or `rejected`, and provide "
        "`reviewer`, an aware ISO-8601 `reviewed_at`, and a non-empty `review_note`. Geometry "
        "may be edited only in the working review layer. Use `accepted_with_edits` whenever "
        "its exact geometry differs from the draft output.\n\n"
        "Promotion creates a separate accepted-evidence GeoPackage. It does not alter this "
        "package, the original draft, the legacy Phase 03 evidence package, or any external "
        "publication destination.\n",
        encoding="utf-8",
        newline="\n",
    )


def _validate_existing_review_package(
    package_directory: Path,
    manifest: ReviewPackageManifest,
    *,
    draft_path: Path,
    authority: _Authority,
) -> None:
    authoritative_records, authoritative_findings = _load_and_validate_draft(
        draft_path,
        authority=authority,
        expected_target_crs=manifest.target_crs,
    )
    authoritative_proposals = tuple(
        ReviewProposalDigest(
            proposal_id=str(record.properties["proposal_id"]),
            draft_layer=record.layer,
            original_record_sha256=_record_sha(record.geometry, record.properties),
        )
        for record in sorted(
            authoritative_records,
            key=lambda item: (item.layer.value, str(item.properties["proposal_id"])),
        )
    )
    if (
        manifest.run_id != authority.package.request.run_id
        or manifest.job_id != authority.package.request.job_id
        or manifest.draft_relative_path
        != draft_path.relative_to(authority.run_directory).as_posix()
        or manifest.draft_sha256 != sha256_file(draft_path)
        or manifest.request_package_relative_path
        != authority.package_directory.relative_to(authority.run_directory).as_posix()
        or manifest.request_fingerprint != authority.package.request_fingerprint
        or manifest.request_package_sha256
        != sha256_file(authority.package_directory / "request-package.json")
        or manifest.validated_response_relative_path
        != authority.response_path.relative_to(authority.run_directory).as_posix()
        or manifest.validated_response_sha256 != sha256_file(authority.response_path)
        or manifest.source_asset_id != authority.package.source.asset_id
        or manifest.source_sha256 != authority.package.source.sha256
        or manifest.provider != authority.response.provider
        or manifest.model != authority.response.model
        or manifest.response_id != authority.response.response_id
        or manifest.response_origin is not authority.response_origin
        or manifest.prompt != authority.package.prompt
        or manifest.schema_identity != authority.package.schema_identity
        or manifest.proposals != authoritative_proposals
        or manifest.validation_findings_sha256
        != _validation_findings_digest_from_records(authoritative_findings)
    ):
        raise Phase03HandoffError("review package no longer matches authoritative provenance")
    gpkg = _package_file(package_directory, manifest.review_gpkg_relative_path)
    qgz = _package_file(package_directory, manifest.qgis_project_relative_path)
    if (
        not gpkg.is_file()
        or not qgz.is_file()
        or sha256_file(qgz) != manifest.qgis_project_sha256
        or _validation_findings_digest(gpkg) != manifest.validation_findings_sha256
    ):
        raise Phase03HandoffError("review package is incomplete")
    expected = {item.proposal_id: item for item in manifest.proposals}
    found: set[str] = set()
    for layer in DraftLayerName:
        with fiona.open(gpkg, layer=f"original_{layer.value}") as collection:
            _require_collection_crs(collection, manifest.target_crs)
            for raw in collection:
                geometry = _shape_feature_geometry(raw["geometry"], "original proposal")
                properties = dict(raw["properties"])
                proposal_id = str(properties.get("proposal_id", ""))
                record = expected.get(proposal_id)
                if (
                    record is None
                    or record.draft_layer is not layer
                    or _record_sha(geometry, properties) != record.original_record_sha256
                ):
                    raise Phase03HandoffError("original AI proposal records were modified")
                found.add(proposal_id)
    if found != expected.keys():
        raise Phase03HandoffError("review package original proposal set is incomplete")
    for relative, digest in manifest.source_preview_files:
        preview = _package_file(package_directory, relative)
        if not preview.is_file() or sha256_file(preview) != digest:
            raise Phase03HandoffError("review source preview changed after import")
    if manifest.existing_evidence_relative_path:
        existing = _package_file(package_directory, manifest.existing_evidence_relative_path)
        if not existing.is_file() or sha256_file(existing) != manifest.existing_evidence_sha256:
            raise Phase03HandoffError("review existing-evidence reference changed after import")


def _load_reviewed_records(
    package_directory: Path,
    manifest: ReviewPackageManifest,
    *,
    authority: _Authority,
) -> tuple[_ReviewedRecord, ...]:
    gpkg = _package_file(package_directory, manifest.review_gpkg_relative_path)
    originals = _original_properties(gpkg)
    extent = transformed_source_extent(authority.package.source)
    reviewed: list[_ReviewedRecord] = []
    seen: set[str] = set()
    for layer in DraftLayerName:
        with fiona.open(gpkg, layer=f"review_{layer.value}") as collection:
            _require_collection_crs(collection, manifest.target_crs)
            for raw in collection:
                geometry = _shape_feature_geometry(raw["geometry"], "reviewed proposal")
                properties = dict(raw["properties"])
                proposal_id = str(properties.get("proposal_id", ""))
                original = originals.get(proposal_id)
                if original is None or original[0] is not layer or proposal_id in seen:
                    raise Phase03HandoffError("review layer proposal identities are inconsistent")
                seen.add(proposal_id)
                _require_immutable_review_fields(properties, original[2])
                try:
                    decision = Phase03ReviewDecision(str(properties["review_decision"]))
                except ValueError as exc:
                    raise Phase03HandoffError("review decision is unsupported") from exc
                expected_review_state = (
                    Phase03ReviewState.PENDING
                    if decision is Phase03ReviewDecision.PENDING
                    else Phase03ReviewState.HUMAN_REVIEWED
                )
                if properties.get("review_state") != expected_review_state.value:
                    raise Phase03HandoffError(
                        "review state is inconsistent with the recorded human decision"
                    )
                reviewed_sha = sha256_bytes(geometry.wkb)
                if decision is not Phase03ReviewDecision.PENDING:
                    _require_reviewer(properties, manifest)
                if decision in {
                    Phase03ReviewDecision.ACCEPTED,
                    Phase03ReviewDecision.ACCEPTED_WITH_EDITS,
                }:
                    _validate_review_geometry(geometry, layer=layer, extent=extent)
                    changed = reviewed_sha != sha256_bytes(original[1].wkb)
                    if decision is Phase03ReviewDecision.ACCEPTED and changed:
                        raise Phase03HandoffError("edited geometry must use accepted_with_edits")
                    if decision is Phase03ReviewDecision.ACCEPTED_WITH_EDITS and not changed:
                        raise Phase03HandoffError(
                            "accepted_with_edits requires an exact geometry change"
                        )
                reviewed.append(
                    _ReviewedRecord(
                        layer=layer,
                        geometry=geometry,
                        properties=properties,
                        decision=decision,
                        reviewed_geometry_sha256=reviewed_sha,
                    )
                )
    if seen != {item.proposal_id for item in manifest.proposals}:
        raise Phase03HandoffError("review working layers do not match the original proposal set")
    return tuple(
        sorted(reviewed, key=lambda item: (item.layer.value, item.properties["proposal_id"]))
    )


def _original_properties(
    gpkg: Path,
) -> dict[str, tuple[DraftLayerName, BaseGeometry, dict[str, object]]]:
    result: dict[str, tuple[DraftLayerName, BaseGeometry, dict[str, object]]] = {}
    for layer in DraftLayerName:
        with fiona.open(gpkg, layer=f"original_{layer.value}") as collection:
            for raw in collection:
                properties = dict(raw["properties"])
                proposal_id = str(properties["proposal_id"])
                result[proposal_id] = (
                    layer,
                    _shape_feature_geometry(raw["geometry"], "original proposal"),
                    properties,
                )
    return result


def _require_immutable_review_fields(
    reviewed: dict[str, object], original: dict[str, object]
) -> None:
    for field, value in original.items():
        if field in _MUTABLE_REVIEW_FIELDS:
            continue
        if reviewed.get(field) != value:
            raise Phase03HandoffError(f"review changed immutable proposal field: {field}")


def _require_reviewer(properties: dict[str, object], manifest: ReviewPackageManifest) -> None:
    raw_reviewer = str(properties.get("reviewer", ""))
    raw_note = str(properties.get("review_note", ""))
    reviewer = raw_reviewer.strip()
    note = raw_note.strip()
    value = str(properties.get("reviewed_at", "")).strip()
    if not reviewer or not note or not value:
        raise Phase03HandoffError("reviewed decisions require reviewer, timestamp, and note")
    if raw_reviewer != reviewer or raw_note != note:
        raise Phase03HandoffError("reviewer and review note must not have surrounding whitespace")
    if len(reviewer) > 256 or len(note) > 4096:
        raise Phase03HandoffError("reviewer or review note exceeds the persisted contract limit")
    if len(value) > 64:
        raise Phase03HandoffError("review timestamp exceeds the persisted contract limit")
    try:
        reviewed_at = require_aware_datetime(datetime.fromisoformat(value), "reviewed_at")
    except ValueError as exc:
        raise Phase03HandoffError("review timestamp must be an aware ISO-8601 datetime") from exc
    if reviewed_at < manifest.created_at:
        raise Phase03HandoffError("review timestamp predates review-package creation")


def _promoted_identity(record: _ReviewedRecord, manifest: ReviewPackageManifest) -> PromotedFeature:
    if record.decision is Phase03ReviewDecision.ACCEPTED:
        promoted_decision: Literal["accepted", "accepted_with_edits"] = "accepted"
    elif record.decision is Phase03ReviewDecision.ACCEPTED_WITH_EDITS:
        promoted_decision = "accepted_with_edits"
    else:
        raise Phase03HandoffError("only accepted review decisions can be promoted")
    output_layer, prefix = _OUTPUT_LAYERS[record.layer]
    identity = sha256_value(
        {
            "proposal_id": record.properties["proposal_id"],
            "draft_record_sha256": record.properties["draft_record_sha"],
            "request_fingerprint": manifest.request_fingerprint,
            "source_sha256": manifest.source_sha256,
            "draft_layer": record.layer.value,
        }
    )
    return PromotedFeature(
        proposal_id=str(record.properties["proposal_id"]),
        accepted_feature_id=f"{prefix}-{identity[:12].upper()}",
        output_layer=output_layer,
        decision=promoted_decision,
        reviewed_geometry_sha256=record.reviewed_geometry_sha256,
        review_record_sha256=sha256_value(
            {
                "proposal_id": record.properties["proposal_id"],
                "decision": record.decision.value,
                "reviewer": record.properties["reviewer"],
                "reviewed_at": record.properties["reviewed_at"],
                "review_note": record.properties["review_note"],
                "reviewed_geometry_sha256": record.reviewed_geometry_sha256,
            }
        ),
        reviewer=str(record.properties["reviewer"]),
        reviewed_at=datetime.fromisoformat(str(record.properties["reviewed_at"])),
        review_note=str(record.properties["review_note"]),
    )


def _write_promoted_geopackage(
    path: Path,
    *,
    records: tuple[_ReviewedRecord, ...],
    promoted: tuple[PromotedFeature, ...],
    manifest: ReviewPackageManifest,
    authority: _Authority,
) -> None:
    crs_wkt = CRS.from_epsg(32647).to_wkt()
    by_proposal = {item.proposal_id: item for item in promoted}
    by_layer: dict[str, list[_ReviewedRecord]] = {
        layer_name: [] for layer_name, _prefix in _OUTPUT_LAYERS.values()
    }
    for record in records:
        by_layer[_OUTPUT_LAYERS[record.layer][0]].append(record)
    schema = {"geometry": "Unknown", "properties": _ACCEPTED_PROPERTIES}
    for layer_name in sorted(by_layer):
        with fiona.open(
            path,
            mode="w",
            driver="GPKG",
            layer=layer_name,
            schema=schema,
            crs_wkt=crs_wkt,
        ) as collection:
            for record in by_layer[layer_name]:
                identity = by_proposal[str(record.properties["proposal_id"])]
                collection.write(
                    {
                        "geometry": mapping(record.geometry),
                        "properties": _accepted_properties(
                            record,
                            identity=identity,
                            manifest=manifest,
                            authority=authority,
                        ),
                    }
                )


def _accepted_properties(
    record: _ReviewedRecord,
    *,
    identity: PromotedFeature,
    manifest: ReviewPackageManifest,
    authority: _Authority,
) -> dict[str, object]:
    properties = record.properties
    reviewed_at = str(properties["reviewed_at"])
    limitations_json = str(properties["limitations"])
    values: dict[str, object] = {
        "feature_id": identity.accepted_feature_id,
        "proposal_id": identity.proposal_id,
        "feature_type": str(properties["feature_type"]),
        "legend_code": str(properties["legend_code"]),
        "processing_phase": "03",
        "source_raw_input_no": "",
        "source_raw_filename": Path(authority.package.source.relative_path).name,
        "source_group": "AI hybrid review",
        "source_scale": "",
        "geometry_type": record.geometry.geom_type.lower(),
        "evidence_type": record.layer.value,
        "validation_status": "Human reviewed AI proposal",
        "confidence": format(_float_value(properties["confidence"], "confidence"), ".17g"),
        "limitation": limitations_json,
        "processing_version": "v01",
        "reviewer": str(properties["reviewer"]),
        "review_date": datetime.fromisoformat(reviewed_at).date().isoformat(),
        "proposal_state": ReviewStatus.AI_DRAFT.value,
        "review_state": Phase03ReviewState.HUMAN_REVIEWED.value,
        "evidence_state": Phase03EvidenceState.ACCEPTED_EVIDENCE.value,
        "review_decision": record.decision.value,
        "reviewed_at": reviewed_at,
        "review_note": str(properties["review_note"]),
        "source_asset_id": manifest.source_asset_id,
        "source_sha256": manifest.source_sha256,
        "source_references_json": str(properties["source_refs"]),
        "source_tile_ids_json": str(properties["tile_ids"]),
        "request_fingerprint": manifest.request_fingerprint,
        "response_id": manifest.response_id,
        "response_sha256": manifest.validated_response_sha256,
        "response_origin": manifest.response_origin.value,
        "provider": manifest.provider,
        "model": manifest.model,
        "prompt_id": manifest.prompt.prompt_id,
        "prompt_version": manifest.prompt.version,
        "prompt_sha256": manifest.prompt.sha256,
        "schema_id": manifest.schema_identity.schema_id,
        "schema_version": manifest.schema_identity.version,
        "schema_sha256": manifest.schema_identity.sha256,
        "proposal_schema_version": manifest.proposal_schema_version,
        "original_pixel_geometry": str(properties["pixel_json"]),
        "original_geometry_wkb": str(properties["ai_original_wkb"]),
        "draft_output_wkb": str(properties["draft_output_wkb"]),
        "reviewed_geometry_sha256": record.reviewed_geometry_sha256,
        "reviewed_geometry_provenance": (
            "human-edited geometry from review working layer"
            if record.decision is Phase03ReviewDecision.ACCEPTED_WITH_EDITS
            else "exact deterministic draft output accepted by human reviewer"
        ),
        "repair_status": str(properties["repair_status"]),
        "repair_json": str(properties["repair_json"]),
        "draft_geometry_validation_status": str(properties["validation"]),
        "attributes_json": str(properties["attributes"]),
        "confidence_components_json": str(properties["conf_json"]),
        "evidence_json": str(properties["evidence"]),
        "limitations_json": limitations_json,
        "risk_level": str(properties["risk_level"]),
        "content_sha256": "",
    }
    values["content_sha256"] = sha256_value(
        {
            "accepted_feature_id": identity.accepted_feature_id,
            "geometry_wkb": record.geometry.wkb.hex(),
            "properties": {key: value for key, value in values.items() if key != "content_sha256"},
        }
    )
    return values


def _validate_idempotent_promotion(
    output: Path,
    audit_path: Path,
    *,
    manifest: ReviewPackageManifest,
    promoted: tuple[PromotedFeature, ...],
    review_manifest_sha: str,
    review_gpkg_sha: str,
) -> PromotionResult:
    if not output.is_file() or not audit_path.is_file():
        raise Phase03HandoffError("promotion output and audit ledger are incomplete")
    entries = _load_audit_entries(audit_path)
    if len(entries) != 1:
        raise Phase03HandoffError("promotion ledger has an unsupported event history")
    entry = entries[0]
    if (
        entry.review_package_id != manifest.package_id
        or entry.review_manifest_sha256 != review_manifest_sha
        or entry.review_geopackage_sha256 != review_gpkg_sha
        or entry.promoted_features != promoted
        or entry.output_sha256 != sha256_file(output)
    ):
        raise Phase03HandoffError("existing promotion differs from the current reviewed decisions")
    return PromotionResult(
        output=output,
        audit_ledger=audit_path,
        promoted_feature_ids=tuple(item.accepted_feature_id for item in promoted),
        created=False,
    )


@contextmanager
def _exclusive_promotion_lock(path: Path) -> Iterator[None]:
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise Phase03HandoffError(
            "another promotion is active or a prior promotion lock requires inspection"
        ) from exc
    except OSError as exc:
        raise Phase03HandoffError("promotion lock could not be created") from exc
    try:
        os.write(descriptor, b"phase03 promotion in progress\n")
        os.close(descriptor)
        descriptor = -1
        yield
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise Phase03HandoffError("promotion lock could not be removed safely") from exc


def _commit_staged_promotion(
    staged_output: Path,
    staged_audit: Path,
    *,
    output: Path,
    audit_path: Path,
) -> None:
    if output.exists() or audit_path.exists():
        raise Phase03HandoffError("promotion destination changed while the output was staged")
    staged_output.replace(output)
    try:
        staged_audit.replace(audit_path)
    except BaseException:
        cleanup_errors: list[OSError] = []
        for created in (audit_path, output):
            try:
                created.unlink(missing_ok=True)
            except OSError as exc:
                cleanup_errors.append(exc)
        if cleanup_errors:
            raise Phase03HandoffError(
                "promotion commit failed and partial output requires manual inspection"
            ) from cleanup_errors[0]
        raise


def _load_audit_entries(path: Path) -> tuple[PromotionAuditEntry, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        entries = tuple(
            PromotionAuditEntry.model_validate(json.loads(line, object_pairs_hook=_unique_object))
            for line in lines
            if line.strip()
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise Phase03HandoffError("promotion audit ledger is invalid") from exc
    previous: str | None = None
    for entry in entries:
        if entry.previous_entry_sha256 != previous:
            raise Phase03HandoffError("promotion audit hash chain is invalid")
        previous = sha256_value(entry)
    return entries


def _validate_source_references(value: str, package: RequestPackageManifest) -> None:
    try:
        raw = json.loads(value, object_pairs_hook=_unique_object)
        references = tuple(SourceReference.model_validate(item) for item in raw)
    except (TypeError, ValueError) as exc:
        raise Phase03HandoffError("draft source references are invalid") from exc
    authority = {item.asset_id: item for item in package.request.source_references}
    if not references:
        raise Phase03HandoffError("draft feature has no source references")
    for reference in references:
        expected = authority.get(reference.asset_id)
        if expected is None or expected.sha256 != reference.sha256:
            raise Phase03HandoffError("draft source identity is not authoritative")
        expected_locators = {item.model_dump_json() for item in expected.locators}
        if any(item.model_dump_json() not in expected_locators for item in reference.locators):
            raise Phase03HandoffError("draft source locator was not requested")


def _validate_json_field(properties: dict[str, object], name: str) -> None:
    try:
        json.loads(str(properties[name]), object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise Phase03HandoffError(f"draft {name} JSON is invalid") from exc


def _json_string_list(value: str, name: str) -> tuple[str, ...]:
    try:
        result = json.loads(value, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise Phase03HandoffError(f"review {name} JSON is invalid") from exc
    if not isinstance(result, list) or any(not isinstance(item, str) for item in result):
        raise Phase03HandoffError(f"review {name} must contain a JSON string list")
    return tuple(result)


def _require_collection_crs(collection: object, expected: str) -> None:
    crs_wkt = getattr(collection, "crs_wkt", None)
    crs_value = crs_wkt or getattr(collection, "crs", None)
    try:
        actual = CRS.from_user_input(crs_value)
    except (CRSError, TypeError, ValueError) as exc:
        raise Phase03HandoffError("GeoPackage layer has no valid CRS") from exc
    if actual != CRS.from_user_input(expected):
        raise Phase03HandoffError(f"GeoPackage layer must use {expected}")


def _shape_feature_geometry(value: object, label: str) -> BaseGeometry:
    if value is None:
        raise Phase03HandoffError(f"{label} has no geometry")
    try:
        return shape(cast(Any, value))
    except (AttributeError, TypeError, ValueError) as exc:
        raise Phase03HandoffError(f"{label} geometry is unreadable") from exc


def _validate_review_geometry(
    geometry: BaseGeometry,
    *,
    layer: DraftLayerName,
    extent: BaseGeometry,
) -> None:
    expected = _EXPECTED_GEOMETRIES[layer]
    validated, result = validate_geometry(
        geometry,
        expected_geometry=expected,
        extent=extent,
    )
    if not result.valid or validated.wkb != geometry.wkb:
        raise Phase03HandoffError("accepted review geometry failed validation")
    components = getattr(geometry, "geoms", ())
    for component in components:
        validated_component, component_result = validate_geometry(
            component,
            expected_geometry=expected,
            extent=extent,
        )
        if not component_result.valid or validated_component.wkb != component.wkb:
            raise Phase03HandoffError(
                "accepted review multi-geometry contains an invalid component"
            )


def _accepted_geometry_types(expected: str) -> frozenset[str]:
    return {
        "Point": frozenset({"Point", "MultiPoint"}),
        "LineString": frozenset({"LineString", "MultiLineString"}),
        "Polygon": frozenset({"Polygon", "MultiPolygon"}),
    }[expected]


def _qgis_geometry(value: str) -> str:
    normalized = value.removeprefix("3D ")
    if normalized in {"Point", "MultiPoint"}:
        return "Point"
    if normalized in {"LineString", "MultiLineString"}:
        return "LineString"
    if normalized in {"Polygon", "MultiPolygon"}:
        return "Polygon"
    return "None"


def _record_sha(
    geometry: BaseGeometry,
    properties: dict[str, object],
    *,
    exclude: set[str] | None = None,
) -> str:
    excluded = exclude or set()
    return sha256_value(
        {
            "geometry_wkb": geometry.wkb.hex(),
            "properties": {
                key: value for key, value in sorted(properties.items()) if key not in excluded
            },
        }
    )


def _validation_findings_digest(path: Path) -> str:
    findings: list[dict[str, object]] = []
    with fiona.open(path, layer="validation_findings") as collection:
        _require_collection_crs(collection, "EPSG:32647")
        for raw in collection:
            findings.append(
                {
                    "geometry": raw["geometry"],
                    "properties": dict(raw["properties"]),
                }
            )
    return _validation_findings_digest_from_records(tuple(findings))


def _validation_findings_digest_from_records(
    findings: tuple[dict[str, object], ...],
) -> str:
    digests: list[str] = []
    for finding in findings:
        geometry_value = finding.get("geometry")
        properties = finding.get("properties")
        if geometry_value is None or not isinstance(properties, dict):
            raise Phase03HandoffError("validation finding record is incomplete")
        geometry = _shape_feature_geometry(geometry_value, "validation finding")
        digests.append(_record_sha(geometry, cast(dict[str, object], properties)))
    return sha256_value(tuple(sorted(digests)))


def _float_value(value: object, field_name: str) -> float:
    if type(value) is int:
        return float(value)
    if type(value) is float:
        return value
    if type(value) is str:
        try:
            return float(value)
        except ValueError as exc:
            raise Phase03HandoffError(f"{field_name} is not numeric") from exc
    raise Phase03HandoffError(f"{field_name} is not numeric")


def _package_file(package_directory: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise Phase03HandoffError("review package contains a path escape")
    candidate = (package_directory / relative).resolve(strict=True)
    if not candidate.is_relative_to(package_directory.resolve(strict=True)):
        raise Phase03HandoffError("review package path resolves outside its directory")
    return candidate


def _load_unique_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise Phase03HandoffError(f"JSON is unreadable or invalid: {path.name}") from exc


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _relative(base: Path, target: Path) -> str:
    return os.path.relpath(target.resolve(), base.resolve()).replace("\\", "/")
