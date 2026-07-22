"""Deterministic, offline methodology-readiness reporting.

The report exposes unresolved authority/evidence obligations and registered raw-input
gaps without opening raw data or pretending that an available file is scientifically
accepted. It is a planning view, not a gate decision or approval record.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from buduunkhad.core.ingest import load_manifest
from buduunkhad.geospatial_ai.methodology import (
    AutomationStatus,
    ReadinessStatus,
    load_authority_registry,
    load_automation_boundaries,
    load_automation_readiness,
    load_discrepancy_registry,
    load_phase04_migration_contract,
)

PhaseReadinessStatus = Literal[
    "no-open-operational-obligations",
    "conditional-data-gaps",
    "blocked-operational-obligations",
    "parked",
]


class ReadinessObligation(BaseModel):
    """One operational prerequisite or conservative exclusion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    obligation_id: str = Field(pattern=r"^METH-READY-\d{3}$")
    subject: str
    affected_phases: tuple[str, ...]
    status: ReadinessStatus
    blocks_phase_completion: bool
    decision: str
    required_evidence: tuple[str, ...]
    deterministic_next_steps: tuple[str, ...]
    required_human_authority: tuple[str, ...]


class MissingRegisteredInput(BaseModel):
    """One input that the canonical manifest records as absent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_number: int | None
    filename: str
    manifest_status: str
    drive_file_id: str | None


class PhaseReadiness(BaseModel):
    """Open methodology obligations associated with one workflow phase."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    phase_id: str = Field(pattern=r"^(?:0[0-9]|1[01]|99)$")
    implementation_status: AutomationStatus
    status: PhaseReadinessStatus
    obligation_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _status_matches_contents(self) -> PhaseReadiness:
        if not self.obligation_ids and self.status != "no-open-operational-obligations":
            raise ValueError("phase readiness status requires operational obligations")
        if self.obligation_ids and self.status == "no-open-operational-obligations":
            raise ValueError("phase readiness obligations require a non-ready status")
        return self


class MethodologyReadinessReport(BaseModel):
    """Machine-readable master-first reconciliation and missing-input summary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"] = "1.0.0"
    authority_source_id: Literal["methodology.master-v9"] = "methodology.master-v9"
    authority_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    discrepancy_total: int = Field(ge=0)
    unresolved_count: int = Field(ge=0)
    historical_unresolved_record_count: int = Field(ge=0)
    resolved_count: int = Field(ge=0)
    superseded_count: int = Field(ge=0)
    withdrawn_count: int = Field(ge=0)
    obligations: tuple[ReadinessObligation, ...]
    missing_registered_inputs: tuple[MissingRegisteredInput, ...]
    phases: tuple[PhaseReadiness, ...]
    phase04_target_status: Literal["specified-not-integrated"]
    phase04_activation_requirements: tuple[str, ...]
    interpretation: Literal[
        "resolved methodology decisions plus operational prerequisites; not scientific "
        "approval or a gate decision"
    ] = (
        "resolved methodology decisions plus operational prerequisites; not scientific "
        "approval or a gate decision"
    )


def build_methodology_readiness_report(manifest_path: Path) -> MethodologyReadinessReport:
    """Build a stable report from packaged authority records and the canonical manifest."""

    authority = load_authority_registry()
    master = next(
        source for source in authority.sources if source.source_id == "methodology.master-v9"
    )
    if master.repository_copy_sha256 is None:
        raise ValueError("master methodology has no byte-bound repository identity")

    registry = load_discrepancy_registry()
    automation = load_automation_boundaries()
    readiness = load_automation_readiness()
    phase04_target = load_phase04_migration_contract()
    unresolved = registry.unresolved()
    obligations = tuple(
        ReadinessObligation(
            obligation_id=item.obligation_id,
            subject=item.subject,
            affected_phases=item.affected_phases,
            status=item.status,
            blocks_phase_completion=item.blocks_phase_completion,
            decision=item.decision,
            required_evidence=item.required_evidence,
            deterministic_next_steps=item.deterministic_next_steps,
            required_human_authority=item.required_human_authority,
        )
        for item in readiness.obligations
    )

    phase_ids = tuple(f"{value:02d}" for value in range(12)) + ("99",)
    implementation_statuses: dict[str, AutomationStatus] = {
        item.phase_id: item.status for item in automation.boundaries
    }
    phase_records: list[PhaseReadiness] = []
    for phase_id in phase_ids:
        phase_obligations = tuple(
            item for item in readiness.obligations if phase_id in item.affected_phases
        )
        status: PhaseReadinessStatus
        if any(item.status == "parked" for item in phase_obligations):
            status = "parked"
        elif any(item.blocks_phase_completion for item in phase_obligations):
            status = "blocked-operational-obligations"
        elif phase_obligations:
            status = "conditional-data-gaps"
        else:
            status = "no-open-operational-obligations"
        phase_records.append(
            PhaseReadiness(
                phase_id=phase_id,
                implementation_status=implementation_statuses[phase_id],
                status=status,
                obligation_ids=tuple(item.obligation_id for item in phase_obligations),
            )
        )

    manifest = load_manifest(manifest_path)
    missing_inputs = tuple(
        MissingRegisteredInput(
            input_number=entry.no,
            filename=entry.filename,
            manifest_status=entry.status,
            drive_file_id=entry.drive_file_id or None,
        )
        for entry in sorted(
            (entry for entry in manifest.values() if not entry.present_in_archive),
            key=lambda entry: (entry.no is None, entry.no or 0, entry.filename),
        )
    )

    counts = {
        status: sum(item.status == status for item in registry.discrepancies)
        for status in ("unresolved", "resolved", "superseded", "withdrawn")
    }
    return MethodologyReadinessReport(
        authority_sha256=master.repository_copy_sha256,
        discrepancy_total=len(registry.discrepancies),
        unresolved_count=len(unresolved),
        historical_unresolved_record_count=counts["unresolved"],
        resolved_count=counts["resolved"],
        superseded_count=counts["superseded"],
        withdrawn_count=counts["withdrawn"],
        obligations=obligations,
        missing_registered_inputs=missing_inputs,
        phases=tuple(phase_records),
        phase04_target_status=phase04_target.status,
        phase04_activation_requirements=phase04_target.activation_requirements,
    )


def render_methodology_readiness_report(report: MethodologyReadinessReport) -> str:
    """Render stable human-inspectable JSON without timestamps or machine paths."""

    return (
        json.dumps(
            report.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
