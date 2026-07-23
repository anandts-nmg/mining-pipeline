"""Hash-bound authority for evidence consumed by Phase 03 and Phase 04.

Directory proximity is discovery only.  An evidence record becomes executable only after this
module resolves its exact source authority, artifact bytes, GeoPackage layer, lifecycle, role,
and phase eligibility.  The manifest provides integrity and provenance reconciliation; it is not
an external authentication or scientific-approval mechanism.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self, cast

import fiona
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from pyproj import CRS
from pyproj.exceptions import CRSError

from buduunkhad.ai.fingerprint import sha256_value
from buduunkhad.core.run_artifacts import (
    ArtifactSealError,
    canonical_relative_path,
    has_symlink_component,
    require_regular_file_under,
    sha256_file,
)
from buduunkhad.core.run_storage import (
    RunLayout,
    RunStorageError,
    resolve_source_phase,
    validate_run_id,
)

EVIDENCE_MANIFEST_FORMAT_VERSION = "1.0.0"
EVIDENCE_MANIFEST_FILENAME = "evidence_manifest.json"
EVIDENCE_CATALOG_FILENAME = "evidence_catalog.jsonl"
EVIDENCE_CATALOG_FORMAT_VERSION = "1.0.0"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PhaseId = Literal["03", "04"]


class EvidenceManifestError(ValueError):
    """Evidence authority cannot be resolved without ambiguity or mutation."""


class EvidenceSourceKind(StrEnum):
    PIPELINE_RUN = "pipeline-run-v2"
    PHASE03_PROMOTION = "phase03-promotion-v1"


class EvidenceOrigin(StrEnum):
    DETERMINISTIC_PIPELINE = "deterministic-pipeline"
    HUMAN_DIGITIZED = "human-digitized"
    PHASE03_AI_HANDOFF = "phase03-ai-handoff"


class EvidenceLifecycleState(StrEnum):
    SEALED_SUPPORT_EVIDENCE = "SEALED_SUPPORT_EVIDENCE"
    ACCEPTED_EVIDENCE = "ACCEPTED_EVIDENCE"


class EvidenceRole(StrEnum):
    GEOLOGY = "geology"
    STRUCTURE = "structure"
    OCCURRENCE = "occurrence"
    ALTERATION_SUPPORT = "alteration-support"
    GEOCHEMICAL_ANOMALY = "geochemical-anomaly"
    ACCESS = "access"
    DEPOSIT_MODEL = "deposit-model"
    PROSPECT_TARGET = "prospect-target"


class EvidenceExecutionMode(StrEnum):
    SUPPORT_EVIDENCE = "support-evidence"
    LEGACY_COMPARATOR = "legacy-comparator"


PHASE03_TARGET_ROLES: dict[str, frozenset[EvidenceRole]] = {
    "tectonic_terrane_context_polygon": frozenset({EvidenceRole.GEOLOGY}),
    "metallogenic_zones_polygon": frozenset({EvidenceRole.GEOLOGY}),
    "ore_district_node_context_polygon": frozenset({EvidenceRole.GEOLOGY}),
    "geology_units_200k_polygon": frozenset({EvidenceRole.GEOLOGY}),
    "geology_units_50k_polygon": frozenset({EvidenceRole.GEOLOGY}),
    "faults_structures_line": frozenset({EvidenceRole.STRUCTURE}),
    "intrusive_contacts_line": frozenset({EvidenceRole.STRUCTURE}),
    "dyke_vein_line": frozenset({EvidenceRole.STRUCTURE}),
    "mineral_occurrences_point": frozenset({EvidenceRole.OCCURRENCE}),
    "prospectivity_target_zones_polygon": frozenset({EvidenceRole.PROSPECT_TARGET}),
    "source_material_observation_point": frozenset({EvidenceRole.OCCURRENCE}),
    "source_material_route_line": frozenset({EvidenceRole.ACCESS}),
    "source_material_trench_pit_point": frozenset({EvidenceRole.OCCURRENCE}),
}


def phase03_target_accepts(target_layer: str, role: EvidenceRole) -> bool:
    """Return whether one exact role may populate one externally writable Phase 03 layer."""

    return role in PHASE03_TARGET_ROLES.get(target_layer, frozenset())


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

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


class EvidenceRecord(_StrictModel):
    """One exact source layer and its permitted pipeline use."""

    evidence_id: NonEmpty
    source_kind: EvidenceSourceKind
    source_run_id: NonEmpty
    source_authority_path: str
    source_authority_sha256: Sha256
    source_record_id: NonEmpty | None = None
    artifact_path: str
    artifact_sha256: Sha256
    artifact_size_bytes: int = Field(ge=0)
    layer_name: NonEmpty
    target_layer_name: NonEmpty | None = None
    evidence_role: EvidenceRole
    origin: EvidenceOrigin
    lifecycle_state: EvidenceLifecycleState
    review_record_id: NonEmpty | None = None
    reviewers: tuple[NonEmpty, ...] = ()
    reviewed_at: datetime | None = None
    eligible_phases: tuple[PhaseId, ...] = Field(min_length=1)
    eligible_modes: tuple[EvidenceExecutionMode, ...] = Field(min_length=1)
    authoritative_for_phase04: Literal[False] = False
    limitations: tuple[NonEmpty, ...] = ()

    _authority_path_is_portable = field_validator("source_authority_path")(canonical_relative_path)
    _artifact_path_is_portable = field_validator("artifact_path")(canonical_relative_path)

    @field_validator("evidence_id")
    @classmethod
    def _safe_evidence_id(cls, value: str) -> str:
        if _IDENTIFIER.fullmatch(value) is None:
            raise ValueError("evidence ID must be one safe portable identifier")
        return value

    @field_validator("source_run_id")
    @classmethod
    def _safe_run_id(cls, value: str) -> str:
        try:
            return validate_run_id(value)
        except RunStorageError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("reviewed_at")
    @classmethod
    def _aware_review_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("reviewed_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _consistent_authority(self) -> EvidenceRecord:
        if len(set(self.eligible_phases)) != len(self.eligible_phases):
            raise ValueError("eligible phases must be unique")
        if len(set(self.eligible_modes)) != len(self.eligible_modes):
            raise ValueError("eligible execution modes must be unique")
        if tuple(sorted(self.eligible_phases)) != self.eligible_phases:
            raise ValueError("eligible phases must use deterministic order")
        if tuple(sorted(self.eligible_modes, key=lambda item: item.value)) != self.eligible_modes:
            raise ValueError("eligible execution modes must use deterministic order")
        if tuple(sorted(self.reviewers)) != self.reviewers or len(set(self.reviewers)) != len(
            self.reviewers
        ):
            raise ValueError("reviewer identities must be unique and deterministically ordered")
        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError("evidence limitations must be unique")
        review_fields = (self.review_record_id, self.reviewed_at)
        if self.lifecycle_state is EvidenceLifecycleState.ACCEPTED_EVIDENCE:
            if any(value is None for value in review_fields) or not self.reviewers:
                raise ValueError("accepted evidence requires its complete human-review binding")
        elif any(value is not None for value in review_fields) or self.reviewers:
            raise ValueError("sealed support evidence cannot claim human-review facts")
        if self.source_kind is EvidenceSourceKind.PHASE03_PROMOTION:
            promotion_mapping = _PHASE03_PROMOTION_LAYER_ROLES.get(self.layer_name)
            expected = (
                self.origin is EvidenceOrigin.PHASE03_AI_HANDOFF
                and self.lifecycle_state is EvidenceLifecycleState.ACCEPTED_EVIDENCE
                and self.source_record_id is not None
                and self.eligible_phases == ("03",)
                and self.eligible_modes == (EvidenceExecutionMode.SUPPORT_EVIDENCE,)
                and promotion_mapping == (self.evidence_role, self.target_layer_name)
            )
            if not expected:
                raise ValueError(
                    "Phase 03 promotion evidence remains accepted handoff evidence for Phase 03 only"
                )
        elif self.origin is EvidenceOrigin.PHASE03_AI_HANDOFF:
            raise ValueError("Phase 03 AI handoff evidence requires its promotion-ledger authority")
        elif self.lifecycle_state is not EvidenceLifecycleState.SEALED_SUPPORT_EVIDENCE:
            raise ValueError(
                "pipeline-run evidence is sealed support evidence, not a human-review claim"
            )
        if "04" in self.eligible_phases and EvidenceExecutionMode.LEGACY_COMPARATOR not in (
            self.eligible_modes
        ):
            raise ValueError(
                "Phase 04 evidence must be explicitly limited to legacy-comparator mode"
            )
        if "03" in self.eligible_phases and EvidenceExecutionMode.SUPPORT_EVIDENCE not in (
            self.eligible_modes
        ):
            raise ValueError("Phase 03 evidence must be explicitly eligible as support evidence")
        expected_modes: set[str] = set()
        if "03" in self.eligible_phases:
            expected_modes.add(EvidenceExecutionMode.SUPPORT_EVIDENCE.value)
        if "04" in self.eligible_phases:
            expected_modes.add(EvidenceExecutionMode.LEGACY_COMPARATOR.value)
        if {item.value for item in self.eligible_modes} != expected_modes:
            raise ValueError("evidence execution modes must exactly match eligible phases")
        if "04" in self.eligible_phases and self.evidence_role not in {
            EvidenceRole.ALTERATION_SUPPORT,
            EvidenceRole.GEOCHEMICAL_ANOMALY,
        }:
            raise ValueError("the Phase 04 comparator accepts only implemented manifest roles")
        if (
            "03" in self.eligible_phases
            and self.source_kind is EvidenceSourceKind.PIPELINE_RUN
            and (
                self.target_layer_name is None
                or not phase03_target_accepts(self.target_layer_name, self.evidence_role)
            )
        ):
            raise ValueError(
                "pipeline support evidence role does not own its exact Phase 03 target layer"
            )
        return self


class _EvidenceManifestIdentity(_StrictModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    records: tuple[EvidenceRecord, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_claims(self) -> _EvidenceManifestIdentity:
        ids = [record.evidence_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence identities must be unique")
        if tuple(sorted(ids)) != tuple(ids):
            raise ValueError("evidence records must use deterministic identity order")
        layer_claims = [
            (record.source_run_id, record.artifact_path, record.layer_name)
            for record in self.records
        ]
        if len(layer_claims) != len(set(layer_claims)):
            raise ValueError("one physical source layer may have only one evidence claim")
        return self


class EvidenceManifest(_EvidenceManifestIdentity):
    manifest_id: Sha256

    @model_validator(mode="after")
    def _sealed_identity(self) -> EvidenceManifest:
        identity = _EvidenceManifestIdentity.model_validate(
            self.model_dump(mode="python", exclude={"manifest_id"})
        )
        if self.manifest_id != sha256_value(identity):
            raise ValueError("evidence manifest identity is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        records: tuple[EvidenceRecord, ...],
    ) -> EvidenceManifest:
        identity = _EvidenceManifestIdentity(records=records)
        return cls(**identity.model_dump(mode="python"), manifest_id=sha256_value(identity))


class EvidenceManifestBinding(_StrictModel):
    manifest_id: Sha256
    manifest_sha256: Sha256
    catalog_entry_id: Sha256


class _EvidenceCatalogEntryIdentity(_StrictModel):
    format_version: Literal["1.0.0"] = "1.0.0"
    previous_entry_sha256: Sha256 | None = None
    manifest_id: Sha256
    manifest_sha256: Sha256
    registered_at: datetime
    registered_by: NonEmpty
    registration_reason: NonEmpty
    authorization_record_id: NonEmpty | None = None
    registration_component: Literal["buduunkhad.evidence.register"] = "buduunkhad.evidence.register"

    @field_validator("registered_at")
    @classmethod
    def _aware_registration_time(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("evidence registration timestamp must be timezone-aware")
        return value


class EvidenceCatalogEntry(_EvidenceCatalogEntryIdentity):
    entry_id: Sha256

    @model_validator(mode="after")
    def _sealed_entry(self) -> EvidenceCatalogEntry:
        identity = _EvidenceCatalogEntryIdentity.model_validate(
            self.model_dump(mode="python", exclude={"entry_id"})
        )
        if self.entry_id != sha256_value(identity):
            raise ValueError("evidence catalog entry identity is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        previous_entry_sha256: str | None,
        manifest_id: str,
        manifest_sha256: str,
        registered_at: datetime,
        registered_by: str,
        registration_reason: str,
        authorization_record_id: str | None,
    ) -> EvidenceCatalogEntry:
        identity = _EvidenceCatalogEntryIdentity(
            previous_entry_sha256=previous_entry_sha256,
            manifest_id=manifest_id,
            manifest_sha256=manifest_sha256,
            registered_at=registered_at,
            registered_by=registered_by,
            registration_reason=registration_reason,
            authorization_record_id=authorization_record_id,
        )
        return cls(**identity.model_dump(mode="python"), entry_id=sha256_value(identity))


@dataclass(frozen=True)
class ResolvedEvidence:
    """One revalidated record and its current exact local artifact."""

    manifest_id: str
    manifest_sha256: str
    catalog_entry_id: str
    record: EvidenceRecord
    artifact: Path

    def verify_current_artifact(self) -> None:
        """Fail if selected bytes are missing, linked, or changed since resolution."""

        if has_symlink_component(self.artifact) or not self.artifact.is_file():
            raise EvidenceManifestError(
                f"resolved evidence artifact is missing or unsafe: {self.record.evidence_id}"
            )
        if (
            self.artifact.stat().st_size != self.record.artifact_size_bytes
            or sha256_file(self.artifact) != self.record.artifact_sha256
        ):
            raise EvidenceManifestError(
                f"resolved evidence artifact changed while in use: {self.record.evidence_id}"
            )


class EvidenceAuthorityResolver:
    """Resolve selected manifest IDs through their underlying immutable source records."""

    def __init__(self, *, runs_root: Path, evidence_root: Path, target_epsg: int) -> None:
        self.runs_root = Path(runs_root).absolute()
        self.evidence_root = Path(evidence_root).absolute()
        self.target_epsg = target_epsg
        for name, root in (("runs root", self.runs_root), ("evidence root", self.evidence_root)):
            if has_symlink_component(root):
                raise EvidenceManifestError(f"{name} must not use a symlink: {root}")
        runs = self.runs_root.resolve(strict=False)
        evidence = self.evidence_root.resolve(strict=False)
        if runs == evidence or runs in evidence.parents or evidence in runs.parents:
            raise EvidenceManifestError("runs root and evidence root must not overlap")

    def resolve_selected(
        self, manifest_ids: tuple[str, ...] | list[str]
    ) -> tuple[ResolvedEvidence, ...]:
        if len(manifest_ids) != len(set(manifest_ids)):
            raise EvidenceManifestError("selected evidence manifest identities must be unique")
        resolved: list[ResolvedEvidence] = []
        claimed_layers: set[tuple[str, str, str]] = set()
        claimed_evidence_ids: set[str] = set()
        for manifest_id in sorted(manifest_ids):
            manifest, manifest_sha, catalog_entry = self.load(manifest_id)
            for record in manifest.records:
                if record.evidence_id in claimed_evidence_ids:
                    raise EvidenceManifestError(
                        "selected evidence manifests contain a duplicate evidence identity"
                    )
                claimed_evidence_ids.add(record.evidence_id)
                claim = (record.source_run_id, record.artifact_path, record.layer_name)
                if claim in claimed_layers:
                    raise EvidenceManifestError(
                        "selected evidence manifests contain a duplicate physical layer claim"
                    )
                claimed_layers.add(claim)
                artifact = self._resolve_record(record)
                resolved.append(
                    ResolvedEvidence(
                        manifest_id=manifest.manifest_id,
                        manifest_sha256=manifest_sha,
                        catalog_entry_id=catalog_entry.entry_id,
                        record=record,
                        artifact=artifact,
                    )
                )
        return tuple(sorted(resolved, key=lambda item: item.record.evidence_id))

    def load(self, manifest_id: str) -> tuple[EvidenceManifest, str, EvidenceCatalogEntry]:
        manifest, digest = self._load_package(manifest_id)
        entries = self._load_catalog()
        matches = [entry for entry in entries if entry.manifest_id == manifest_id]
        if len(matches) != 1 or matches[0].manifest_sha256 != digest:
            raise EvidenceManifestError(
                "evidence manifest is not registered exactly once in the authority catalog"
            )
        return manifest, digest, matches[0]

    def _load_package(self, manifest_id: str) -> tuple[EvidenceManifest, str]:
        if re.fullmatch(r"[0-9a-f]{64}", manifest_id) is None:
            raise EvidenceManifestError("evidence manifest ID must be lowercase SHA-256")
        path = self.evidence_root / manifest_id / EVIDENCE_MANIFEST_FILENAME
        try:
            safe = require_regular_file_under(
                self.evidence_root, path, description="evidence manifest"
            )
            value = _load_json_object(safe)
            manifest = EvidenceManifest.model_validate(value)
        except (ArtifactSealError, OSError, UnicodeError, ValueError) as exc:
            raise EvidenceManifestError(f"evidence manifest is invalid: {manifest_id}") from exc
        if manifest.manifest_id != manifest_id or safe.parent.name != manifest_id:
            raise EvidenceManifestError("evidence manifest identity does not match its directory")
        return manifest, sha256_file(safe)

    def verify_manifest(self, manifest: EvidenceManifest) -> tuple[ResolvedEvidence, ...]:
        resolved = [
            ResolvedEvidence(
                manifest_id=manifest.manifest_id,
                manifest_sha256="",
                catalog_entry_id="",
                record=record,
                artifact=self._resolve_record(record),
            )
            for record in manifest.records
        ]
        return tuple(resolved)

    def write(
        self,
        manifest: EvidenceManifest,
        *,
        registered_by: str,
        registration_reason: str,
        authorization_record_id: str | None = None,
    ) -> Path:
        """Validate source authority, then atomically persist one immutable manifest package."""

        self.verify_manifest(manifest)
        root = self.evidence_root
        if root.exists() and (root.is_symlink() or has_symlink_component(root)):
            raise EvidenceManifestError(f"evidence root must not use a symlink: {root}")
        root.mkdir(parents=True, exist_ok=True)
        destination = root / manifest.manifest_id
        payload = manifest.model_dump_json(indent=2).encode("utf-8") + b"\n"
        if destination.exists():
            path = destination / EVIDENCE_MANIFEST_FILENAME
            existing, digest = self._load_package(manifest.manifest_id)
            if existing != manifest or path.read_bytes() != payload:
                raise EvidenceManifestError("existing evidence manifest package differs")
        else:
            temporary = root / f".{manifest.manifest_id}.{uuid.uuid4().hex}.tmp"
            try:
                temporary.mkdir()
                manifest_path = temporary / EVIDENCE_MANIFEST_FILENAME
                manifest_path.write_bytes(payload)
                os.replace(temporary, destination)
            finally:
                if temporary.exists():
                    manifest_path = temporary / EVIDENCE_MANIFEST_FILENAME
                    if manifest_path.exists():
                        manifest_path.unlink()
                    temporary.rmdir()
            digest = sha256_file(destination / EVIDENCE_MANIFEST_FILENAME)
        self._register_catalog_binding(
            manifest.manifest_id,
            digest,
            registered_by=registered_by,
            registration_reason=registration_reason,
            authorization_record_id=authorization_record_id,
        )
        return destination / EVIDENCE_MANIFEST_FILENAME

    def _load_catalog(self) -> tuple[EvidenceCatalogEntry, ...]:
        path = self.evidence_root / EVIDENCE_CATALOG_FILENAME
        try:
            safe = require_regular_file_under(
                self.evidence_root, path, description="evidence authority catalog"
            )
            lines = safe.read_text(encoding="utf-8").splitlines()
            entries = tuple(
                EvidenceCatalogEntry.model_validate(
                    json.loads(line, object_pairs_hook=_unique_object)
                )
                for line in lines
                if line.strip()
            )
        except (ArtifactSealError, OSError, UnicodeError, ValueError) as exc:
            raise EvidenceManifestError("evidence authority catalog is invalid") from exc
        previous: str | None = None
        manifests: set[str] = set()
        for entry in entries:
            if entry.previous_entry_sha256 != previous:
                raise EvidenceManifestError("evidence authority catalog hash chain is invalid")
            if entry.manifest_id in manifests:
                raise EvidenceManifestError("evidence manifest is registered more than once")
            manifests.add(entry.manifest_id)
            previous = entry.entry_id
        return entries

    def _register_catalog_binding(
        self,
        manifest_id: str,
        manifest_sha256: str,
        *,
        registered_by: str,
        registration_reason: str,
        authorization_record_id: str | None,
    ) -> None:
        catalog = self.evidence_root / EVIDENCE_CATALOG_FILENAME
        lock = self.evidence_root / ".evidence-catalog.lock"
        with _exclusive_catalog_lock(lock):
            entries = self._load_catalog() if catalog.exists() else ()
            matches = [entry for entry in entries if entry.manifest_id == manifest_id]
            if matches:
                if (
                    len(matches) != 1
                    or matches[0].manifest_sha256 != manifest_sha256
                    or matches[0].registered_by != registered_by
                    or matches[0].registration_reason != registration_reason
                    or matches[0].authorization_record_id != authorization_record_id
                ):
                    raise EvidenceManifestError(
                        "existing evidence catalog binding conflicts with the manifest"
                    )
                return
            entry = EvidenceCatalogEntry.create(
                previous_entry_sha256=entries[-1].entry_id if entries else None,
                manifest_id=manifest_id,
                manifest_sha256=manifest_sha256,
                registered_at=datetime.now(UTC),
                registered_by=registered_by,
                registration_reason=registration_reason,
                authorization_record_id=authorization_record_id,
            )
            try:
                with catalog.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(entry.model_dump_json() + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
            except OSError as exc:
                raise EvidenceManifestError("evidence catalog registration failed") from exc
            self._load_catalog()

    def _resolve_record(self, record: EvidenceRecord) -> Path:
        run = RunLayout(self.runs_root, record.source_run_id)
        run_directory = run.run_dir
        if run_directory.name != record.source_run_id:
            raise EvidenceManifestError("evidence source run identity is invalid")
        try:
            authority = require_regular_file_under(
                run_directory,
                run_directory / Path(record.source_authority_path),
                description="evidence source authority",
            )
            artifact = require_regular_file_under(
                run_directory,
                run_directory / Path(record.artifact_path),
                description="evidence source artifact",
            )
        except ArtifactSealError as exc:
            raise EvidenceManifestError(str(exc)) from exc
        if sha256_file(authority) != record.source_authority_sha256:
            raise EvidenceManifestError("evidence source authority bytes changed")
        if (
            artifact.stat().st_size != record.artifact_size_bytes
            or sha256_file(artifact) != record.artifact_sha256
        ):
            raise EvidenceManifestError("evidence source artifact bytes changed")
        if record.source_kind is EvidenceSourceKind.PIPELINE_RUN:
            self._verify_pipeline_source(run, authority, artifact, record)
        else:
            self._verify_phase03_promotion(run, authority, artifact, record)
        self._verify_layer(artifact, record.layer_name)
        return artifact

    def _verify_pipeline_source(
        self,
        run: RunLayout,
        authority: Path,
        artifact: Path,
        record: EvidenceRecord,
    ) -> None:
        if record.source_authority_path != "run_manifest.json" or authority != run.manifest_path:
            raise EvidenceManifestError("pipeline evidence must bind the source run manifest")
        relative = artifact.relative_to(run.run_dir.resolve()).as_posix()
        parts = Path(relative).parts
        if len(parts) < 3 or parts[0] != "phases":
            raise EvidenceManifestError(
                "pipeline evidence artifact is not owned by one source phase"
            )
        phase_id = parts[1]
        try:
            source = resolve_source_phase(
                self.runs_root,
                phase_id,
                record.source_run_id,
                require_advance=False,
                require_qaqc_passed=True,
            )
        except RunStorageError as exc:
            raise EvidenceManifestError(str(exc)) from exc
        matches = [item for item in source.output_artifacts if item.path == relative]
        if len(matches) != 1:
            raise EvidenceManifestError("evidence artifact must resolve to one source phase output")
        output = matches[0]
        if (
            output.sha256 != record.artifact_sha256
            or output.size_bytes != record.artifact_size_bytes
        ):
            raise EvidenceManifestError(
                "evidence source phase is incomplete or has a different seal"
            )

    def _verify_phase03_promotion(
        self,
        run: RunLayout,
        authority: Path,
        artifact: Path,
        record: EvidenceRecord,
    ) -> None:
        from buduunkhad.geospatial_ai.phase03_handoff import PromotionAuditEntry

        expected_authority = Path(record.artifact_path).with_suffix(".promotion-ledger.jsonl")
        if Path(record.source_authority_path) != expected_authority:
            raise EvidenceManifestError("Phase 03 evidence must bind its matching promotion ledger")
        try:
            lines = authority.read_text(encoding="utf-8").splitlines()
            entries = tuple(
                PromotionAuditEntry.model_validate(
                    json.loads(line, object_pairs_hook=_unique_object)
                )
                for line in lines
                if line.strip()
            )
        except (OSError, UnicodeError, ValueError) as exc:
            raise EvidenceManifestError("Phase 03 promotion ledger is invalid") from exc
        if len(entries) != 1:
            raise EvidenceManifestError("Phase 03 promotion ledger must contain one sealed event")
        entry = entries[0]
        layer_features = tuple(
            item for item in entry.promoted_features if item.output_layer == record.layer_name
        )
        if not layer_features:
            raise EvidenceManifestError(
                "Phase 03 promotion layer has no matching reviewed feature authority"
            )
        reviewers = tuple(sorted({item.reviewer for item in layer_features}))
        latest_review = max(item.reviewed_at for item in layer_features)
        if (
            entry.audit_id != record.source_record_id
            or entry.audit_id != record.review_record_id
            or entry.run_id != record.source_run_id
            or entry.output_relative_path != artifact.relative_to(run.run_dir.resolve()).as_posix()
            or entry.output_sha256 != record.artifact_sha256
            or reviewers != tuple(sorted(record.reviewers))
            or latest_review != record.reviewed_at
        ):
            raise EvidenceManifestError("Phase 03 promotion evidence differs from its audit event")

    def _verify_layer(self, artifact: Path, layer_name: str) -> None:
        if artifact.suffix.casefold() != ".gpkg":
            raise EvidenceManifestError("geospatial evidence artifacts must be GeoPackages")
        try:
            layers = fiona.listlayers(artifact)
            if layers.count(layer_name) != 1:
                raise EvidenceManifestError("evidence layer must exist exactly once")
            with fiona.open(artifact, layer=layer_name) as collection:
                if len(collection) == 0:
                    raise EvidenceManifestError("evidence layer must contain at least one feature")
                crs_value = collection.crs_wkt or collection.crs
                actual = CRS.from_user_input(crs_value)
        except EvidenceManifestError:
            raise
        except (CRSError, OSError, TypeError, ValueError) as exc:
            raise EvidenceManifestError(
                "evidence layer is unreadable or lacks valid CRS evidence"
            ) from exc
        # A declared, parseable source CRS is sufficient at this authority boundary. The phase
        # owns deterministic reprojection and records the target CRS; CRS-less layers fail above.
        del actual


def evidence_bindings(
    resolved: tuple[ResolvedEvidence, ...],
) -> tuple[EvidenceManifestBinding, ...]:
    """Return one deterministic binding for each selected manifest."""

    by_id: dict[str, tuple[str, str]] = {}
    for item in resolved:
        identity = (item.manifest_sha256, item.catalog_entry_id)
        previous = by_id.setdefault(item.manifest_id, identity)
        if previous != identity:
            raise EvidenceManifestError(
                "one evidence manifest has conflicting byte or catalog identities"
            )
    return tuple(
        EvidenceManifestBinding(
            manifest_id=manifest_id,
            manifest_sha256=identity[0],
            catalog_entry_id=identity[1],
        )
        for manifest_id, identity in sorted(by_id.items())
    )


_PHASE03_PROMOTION_LAYER_ROLES: dict[str, tuple[EvidenceRole, str | None]] = {
    "geology_units_50k_polygon": (EvidenceRole.GEOLOGY, "geology_units_50k_polygon"),
    "faults_structures_line": (EvidenceRole.STRUCTURE, "faults_structures_line"),
    "intrusive_contacts_line": (EvidenceRole.STRUCTURE, "intrusive_contacts_line"),
    "dyke_vein_line": (EvidenceRole.STRUCTURE, "dyke_vein_line"),
    "mineral_occurrences_point": (EvidenceRole.OCCURRENCE, "mineral_occurrences_point"),
    "ai_accepted_alteration_zones_polygon": (EvidenceRole.ALTERATION_SUPPORT, None),
    "prospectivity_target_zones_polygon": (EvidenceRole.PROSPECT_TARGET, None),
}


def register_phase03_promotion_evidence(
    *,
    output: Path,
    audit_ledger: Path,
    runs_root: Path,
    evidence_root: Path,
    target_epsg: int,
) -> EvidenceManifest:
    """Register a verified Phase 03 promotion as Phase-03-only accepted evidence."""

    from buduunkhad.geospatial_ai.phase03_handoff import PromotionAuditEntry

    runs = Path(runs_root).resolve(strict=True)
    try:
        relative_output = Path(output).resolve(strict=True).relative_to(runs)
        relative_audit = Path(audit_ledger).resolve(strict=True).relative_to(runs)
    except ValueError as exc:
        raise EvidenceManifestError(
            "Phase 03 promotion is outside the configured runs root"
        ) from exc
    if not relative_output.parts or relative_output.parts[0] != relative_audit.parts[0]:
        raise EvidenceManifestError("Phase 03 promotion output and ledger belong to different runs")
    run_id = validate_run_id(relative_output.parts[0])
    run_directory = runs / run_id
    try:
        output_path = require_regular_file_under(
            run_directory, output, description="Phase 03 promoted evidence"
        )
        audit_path = require_regular_file_under(
            run_directory, audit_ledger, description="Phase 03 promotion ledger"
        )
        lines = audit_path.read_text(encoding="utf-8").splitlines()
        entries = tuple(
            PromotionAuditEntry.model_validate(json.loads(line, object_pairs_hook=_unique_object))
            for line in lines
            if line.strip()
        )
    except (ArtifactSealError, OSError, UnicodeError, ValueError) as exc:
        raise EvidenceManifestError("Phase 03 promotion authority is invalid") from exc
    if len(entries) != 1:
        raise EvidenceManifestError("Phase 03 promotion ledger must contain one sealed event")
    entry = entries[0]
    if (
        entry.run_id != run_id
        or entry.output_relative_path != output_path.relative_to(run_directory).as_posix()
        or entry.output_sha256 != sha256_file(output_path)
    ):
        raise EvidenceManifestError("Phase 03 promotion output differs from its audit event")
    records: list[EvidenceRecord] = []
    try:
        layers = fiona.listlayers(output_path)
        for layer_name in sorted(layers):
            specification = _PHASE03_PROMOTION_LAYER_ROLES.get(layer_name)
            if specification is None:
                raise EvidenceManifestError(
                    f"Phase 03 promotion layer has no evidence-role mapping: {layer_name}"
                )
            with fiona.open(output_path, layer=layer_name) as collection:
                if len(collection) == 0:
                    continue
            layer_features = tuple(
                item for item in entry.promoted_features if item.output_layer == layer_name
            )
            if not layer_features:
                raise EvidenceManifestError(
                    f"Phase 03 promotion layer lacks reviewed feature authority: {layer_name}"
                )
            reviewers = tuple(sorted({item.reviewer for item in layer_features}))
            reviewed_at = max(item.reviewed_at for item in layer_features)
            role, target = specification
            records.append(
                EvidenceRecord(
                    evidence_id=f"EV-{sha256_value((entry.audit_id, layer_name))[:24]}",
                    source_kind=EvidenceSourceKind.PHASE03_PROMOTION,
                    source_run_id=run_id,
                    source_authority_path=audit_path.relative_to(run_directory).as_posix(),
                    source_authority_sha256=sha256_file(audit_path),
                    source_record_id=entry.audit_id,
                    artifact_path=output_path.relative_to(run_directory).as_posix(),
                    artifact_sha256=entry.output_sha256,
                    artifact_size_bytes=output_path.stat().st_size,
                    layer_name=layer_name,
                    target_layer_name=target,
                    evidence_role=role,
                    origin=EvidenceOrigin.PHASE03_AI_HANDOFF,
                    lifecycle_state=EvidenceLifecycleState.ACCEPTED_EVIDENCE,
                    review_record_id=entry.audit_id,
                    reviewers=reviewers,
                    reviewed_at=reviewed_at,
                    eligible_phases=("03",),
                    eligible_modes=(EvidenceExecutionMode.SUPPORT_EVIDENCE,),
                    authoritative_for_phase04=False,
                    limitations=(
                        "Human-reviewed AI proposal; accepted evidence is not scientific approval.",
                    ),
                )
            )
    except (OSError, ValueError) as exc:
        raise EvidenceManifestError("Phase 03 promoted GeoPackage is invalid") from exc
    if not records:
        raise EvidenceManifestError("Phase 03 promotion contains no non-empty evidence layers")
    manifest = EvidenceManifest.create(
        records=tuple(sorted(records, key=lambda item: item.evidence_id))
    )
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=evidence_root,
        target_epsg=target_epsg,
    )
    resolver.write(
        manifest,
        registered_by="buduunkhad.phase03_handoff",
        registration_reason=f"Register accepted Phase 03 promotion audit {entry.audit_id}",
        authorization_record_id=entry.audit_id,
    )
    return manifest


def register_pipeline_evidence(
    *,
    runs_root: Path,
    evidence_root: Path,
    target_epsg: int,
    source_run_id: str,
    artifact_path: str,
    layer_name: str,
    evidence_role: EvidenceRole,
    origin: EvidenceOrigin,
    eligible_phases: tuple[PhaseId, ...],
    eligible_modes: tuple[EvidenceExecutionMode, ...],
    target_layer_name: str | None = None,
    evidence_id: str | None = None,
    limitations: tuple[str, ...] = (),
    registered_by: str,
    registration_reason: str,
) -> EvidenceManifest:
    """Register one sealed pipeline output layer as support evidence without review claims."""

    run_id = validate_run_id(source_run_id)
    portable_artifact = canonical_relative_path(artifact_path)
    run_directory = Path(runs_root).absolute() / run_id
    authority = run_directory / "run_manifest.json"
    artifact = run_directory / Path(portable_artifact)
    try:
        authority = require_regular_file_under(
            run_directory, authority, description="evidence source run manifest"
        )
        artifact = require_regular_file_under(
            run_directory, artifact, description="evidence source artifact"
        )
    except ArtifactSealError as exc:
        raise EvidenceManifestError(str(exc)) from exc
    identity = evidence_id or f"EV-{sha256_value((run_id, portable_artifact, layer_name))[:24]}"
    record = EvidenceRecord(
        evidence_id=identity,
        source_kind=EvidenceSourceKind.PIPELINE_RUN,
        source_run_id=run_id,
        source_authority_path="run_manifest.json",
        source_authority_sha256=sha256_file(authority),
        artifact_path=portable_artifact,
        artifact_sha256=sha256_file(artifact),
        artifact_size_bytes=artifact.stat().st_size,
        layer_name=layer_name,
        target_layer_name=target_layer_name,
        evidence_role=evidence_role,
        origin=origin,
        lifecycle_state=EvidenceLifecycleState.SEALED_SUPPORT_EVIDENCE,
        eligible_phases=eligible_phases,
        eligible_modes=eligible_modes,
        limitations=limitations,
    )
    manifest = EvidenceManifest.create(records=(record,))
    EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=evidence_root,
        target_epsg=target_epsg,
    ).write(
        manifest,
        registered_by=registered_by,
        registration_reason=registration_reason,
    )
    return manifest


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvidenceManifestError(f"JSON authority is invalid: {path}") from exc
    if not isinstance(value, dict):
        raise EvidenceManifestError(f"JSON authority root must be an object: {path}")
    return cast(dict[str, object], value)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


@contextmanager
def _exclusive_catalog_lock(path: Path) -> Iterator[None]:
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise EvidenceManifestError(
            "another evidence registration is active or a stale lock requires inspection"
        ) from exc
    except OSError as exc:
        raise EvidenceManifestError("evidence catalog lock could not be created") from exc
    try:
        os.close(descriptor)
        descriptor = -1
        yield
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise EvidenceManifestError("evidence catalog lock could not be removed") from exc
