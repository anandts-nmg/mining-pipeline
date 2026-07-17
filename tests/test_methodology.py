from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from buduunkhad.geospatial_ai.methodology import (
    HISTORICAL_UNKNOWN,
    DiscrepancyRegistry,
    MethodologyDiscrepancy,
    MethodologyError,
    load_authority_registry,
    load_automation_boundaries,
    load_discrepancy_registry,
    load_phase_methodology,
    load_phase_methodology_from_checkout,
)

REQUIRED_DISCREPANCY_IDS = {f"METH-DISC-{number:03d}" for number in range(1, 33)}


def test_methodology_authority_and_all_phase_records_are_typed() -> None:
    authority = load_authority_registry()
    assert authority.format_version == "1.1.0"
    source_ids = {source.source_id for source in authority.sources}
    assert "agents.repository-authority" in source_ids
    assert authority.precedence[0] == "agents.repository-authority"
    repository_root = Path(__file__).resolve().parents[1]
    for source in authority.sources:
        if source.repository_path is not None:
            assert (repository_root / source.repository_path).exists()
            assert source.external_reference is None
        else:
            assert source.external_reference is not None
            assert source.external_reference.startswith("BUDUUNKHAD_WORKFLOW_DOCS_ROOT::")
        if source.repository_copy is not None:
            assert (repository_root / source.repository_copy).exists()
    requirement_ids: set[str] = set()
    for number in range(6):
        phase = load_phase_methodology(f"{number:02d}")
        assert phase.phase_id == f"{number:02d}"
        assert phase.requirements
        for requirement in phase.requirements:
            assert requirement.requirement_id not in requirement_ids
            requirement_ids.add(requirement.requirement_id)
            assert requirement.source_refs


def test_external_authority_identifiers_cover_the_deleted_operational_guides() -> None:
    authority = load_authority_registry()
    by_id = {source.source_id: source for source in authority.sources}
    for expected in (
        "phase02.aster-sop",
        "phase05.flight-template-matrice400",
        "phase05.flight-planning-dji-terra",
        "phase06.guide",
        "phase07.guide",
        "phase08.guide",
        "phase09.guide",
        "phase10.guide",
        "phase11.guide",
        "phase99.guide",
    ):
        source = by_id[expected]
        assert source.external_reference is not None
        assert source.expected_document
        # A registered identifier is not existence verification; unverified external
        # documents must say so and carry a follow-up action.
        if not source.existence_verified:
            assert source.remaining_actions


def test_discrepancy_register_is_the_complete_decision_history() -> None:
    registry = load_discrepancy_registry()
    identities = [item.discrepancy_id for item in registry.discrepancies]
    assert len(set(identities)) == len(identities)
    assert set(identities) == REQUIRED_DISCREPANCY_IDS
    assert all(
        item.status in {"unresolved", "resolved", "superseded", "withdrawn"}
        for item in registry.discrepancies
    )


def test_status_aware_requirements_hold_for_every_record() -> None:
    registry = load_discrepancy_registry()
    for item in registry.discrepancies:
        if item.status == "unresolved":
            assert item.proposed_resolution
            assert item.required_approver
            assert item.remaining_actions
            assert item.resolution is None and item.approver is None
        elif item.status in {"resolved", "superseded"}:
            assert item.resolution and item.rationale
            assert item.approver and item.resolved_on and item.effective_version
            assert item.implementation_evidence or item.remaining_actions
        else:
            assert item.status == "withdrawn"
            assert item.withdrawal_reason


def test_supersession_links_are_valid_and_acyclic() -> None:
    registry = load_discrepancy_registry()
    by_id = {item.discrepancy_id: item for item in registry.discrepancies}
    superseded = [item for item in registry.discrepancies if item.status == "superseded"]
    assert superseded  # the 25 km buffer re-decision must remain on record
    for item in superseded:
        assert item.superseded_by in by_id
        replacement = by_id[item.superseded_by]  # type: ignore[index]
        assert replacement.status in {"resolved", "unresolved"}
    cyclic = {
        "format_version": "1.1.0",
        "discrepancies": [
            _record("METH-DISC-901", status="superseded", superseded_by="METH-DISC-902"),
            _record("METH-DISC-902", status="superseded", superseded_by="METH-DISC-901"),
        ],
    }
    with pytest.raises(ValidationError, match="cyclic"):
        DiscrepancyRegistry.model_validate(cyclic)
    dangling = {
        "format_version": "1.1.0",
        "discrepancies": [
            _record("METH-DISC-901", status="superseded", superseded_by="METH-DISC-999"),
        ],
    }
    with pytest.raises(ValidationError, match="unknown record"):
        DiscrepancyRegistry.model_validate(dangling)


def test_unresolved_view_filters_without_erasing_history() -> None:
    registry = load_discrepancy_registry()
    open_items = registry.unresolved()
    assert open_items
    assert all(item.status == "unresolved" for item in open_items)
    assert set(open_items) <= set(registry.discrepancies)
    assert len(registry.discrepancies) > len(open_items)  # resolved history stays present


def test_historical_resolutions_match_their_documented_states() -> None:
    registry = load_discrepancy_registry()
    by_id = {item.discrepancy_id: item for item in registry.discrepancies}
    input_count = by_id["METH-DISC-001"]
    assert input_count.status == "resolved"
    assert input_count.effective_version == "v0.1.0"
    assert "79" in input_count.resolution  # type: ignore[operator]
    scoring = by_id["METH-DISC-006"]
    assert scoring.status == "resolved"
    assert scoring.resolved_on == "2026-07-06"
    assert "Phase 10" in scoring.resolution  # type: ignore[operator]
    artefact_call = by_id["METH-DISC-017"]
    assert artefact_call.status == "superseded"
    assert artefact_call.superseded_by == "METH-DISC-018"
    assert by_id["METH-DISC-018"].status == "resolved"
    # Migrated historical decisions stay traceable and never invent approvers.
    migrated = [item for item in registry.discrepancies if item.migration_source]
    assert migrated
    for item in migrated:
        if item.status in {"resolved", "superseded"}:
            assert item.approver == HISTORICAL_UNKNOWN or item.approver


def test_handoff_and_operational_decisions_remain_discoverable() -> None:
    registry = load_discrepancy_registry()
    sources = " ".join(item.migration_source or "" for item in registry.discrepancies)
    for token in ("H-1", "H-2", "H-3", "H-4"):
        assert token in sources
    subjects = {item.subject: item for item in registry.discrepancies}
    assert subjects["aster-alteration-scoring-scheme"].status == "resolved"
    assert subjects["aster-threshold-statistics-basis"].status == "resolved"
    assert subjects["kompsat-eula-licence-gap"].status == "unresolved"
    assert subjects["bmp-content-in-jpg-raw-scans"].status == "unresolved"
    assert subjects["phase-gate-provisional-advance"].status == "unresolved"


def test_registry_loading_is_deterministic() -> None:
    first = load_discrepancy_registry()
    second = load_discrepancy_registry()
    assert first == second
    assert first.model_dump() == second.model_dump()
    assert [item.discrepancy_id for item in first.discrepancies] == [
        item.discrepancy_id for item in second.discrepancies
    ]


def test_automation_boundaries_cover_every_phase_without_maturity_estimates() -> None:
    registry = load_automation_boundaries()
    phase_ids = {item.phase_id for item in registry.boundaries}
    assert phase_ids == {f"{value:02d}" for value in range(12)} | {"99"}
    implemented = {item.phase_id for item in registry.boundaries if item.status == "implemented"}
    assert implemented == {"00", "01", "02", "03", "04"}
    for item in registry.boundaries:
        assert item.deterministic_authority
        assert item.human_review_boundary
        assert item.ai_prohibited
        assert item.migration_source
        text = " ".join(
            (
                *item.deterministic_authority,
                *item.human_review_boundary,
                *item.ai_permitted,
                *item.ai_prohibited,
                *item.blocking_dependencies,
            )
        )
        assert "%" not in text  # estimates were intentionally not migrated


def test_methodology_yaml_rejects_duplicate_keys(tmp_path: Path) -> None:
    methodology = tmp_path / "config" / "methodology"
    methodology.mkdir(parents=True)
    (methodology / "phase00.yaml").write_text(
        "format_version: 1.0.0\nphase_id: '00'\nphase_id: '01'\nrequirements: []\n",
        encoding="utf-8",
    )
    with pytest.raises(MethodologyError, match="invalid"):
        load_phase_methodology_from_checkout(tmp_path, "00")


def _record(identity: str, *, status: str, superseded_by: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "discrepancy_id": identity,
        "subject": "synthetic-supersession-check",
        "compared_sources": ["source-a", "source-b"],
        "statement": "Synthetic record for registry link validation.",
        "operational_impact": "None; test data only.",
        "status": status,
        "resolution": "Synthetic resolution.",
        "rationale": "Synthetic rationale.",
        "approver": HISTORICAL_UNKNOWN,
        "resolved_on": HISTORICAL_UNKNOWN,
        "effective_version": "v0.0.0",
        "implementation_evidence": "Synthetic evidence.",
    }
    if superseded_by is not None:
        payload["superseded_by"] = superseded_by
    return payload


def test_unresolved_records_reject_adopted_resolution_fields() -> None:
    with pytest.raises(ValidationError, match="adopted-resolution"):
        MethodologyDiscrepancy.model_validate(
            {
                "discrepancy_id": "METH-DISC-900",
                "subject": "synthetic",
                "compared_sources": ["a", "b"],
                "statement": "Synthetic.",
                "operational_impact": "None.",
                "status": "unresolved",
                "proposed_resolution": "Synthetic proposal.",
                "required_approver": "project-owner",
                "remaining_actions": ["Do the thing."],
                "resolution": "Cannot be here.",
            }
        )
    with pytest.raises(ValidationError, match="remaining actions"):
        MethodologyDiscrepancy.model_validate(
            {
                "discrepancy_id": "METH-DISC-900",
                "subject": "synthetic",
                "compared_sources": ["a", "b"],
                "statement": "Synthetic.",
                "operational_impact": "None.",
                "status": "unresolved",
                "proposed_resolution": "Synthetic proposal.",
                "required_approver": "project-owner",
            }
        )
    with pytest.raises(ValidationError, match="withdrawal reason"):
        MethodologyDiscrepancy.model_validate(
            {
                "discrepancy_id": "METH-DISC-900",
                "subject": "synthetic",
                "compared_sources": ["a", "b"],
                "statement": "Synthetic.",
                "operational_impact": "None.",
                "status": "withdrawn",
            }
        )
