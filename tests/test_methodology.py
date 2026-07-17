from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from buduunkhad.geospatial_ai.methodology import (
    HISTORICAL_UNKNOWN,
    DiscrepancyRegistry,
    MethodologyDiscrepancy,
    MethodologyError,
    MethodologySource,
    load_authority_registry,
    load_automation_boundaries,
    load_discrepancy_registry,
    load_phase_methodology,
    load_phase_methodology_from_checkout,
)

REQUIRED_DISCREPANCY_IDS = {f"METH-DISC-{number:03d}" for number in range(1, 34)}
VERIFIED_EXTERNAL_SOURCES = {
    "methodology.master-v9": (
        "1ECwfhr6ucFRE8LABo0C9WDzUDOE6oHzb",
        "XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v9_25km_"
        "Clickable_TOC_PageNumbers.docx",
    ),
    "phase01.guide": (
        "1Ff9rAshnm1kihhh3uOxz6N5Kh6rUFX8Z",
        "XV-023222_Buduunkhad_Phase1_Methodology.docx",
    ),
    "phase02.guide": (
        "1bFjeFQz2BWzrOP38oPMutlh-nSBw3QLD",
        "Phase_2_Remote_Sensing_Preprocessing_Guide_MN.docx",
    ),
    "phase03.guide": (
        "1Ttxau5QEOkCc1LbrCuS8jA9wV3JPaLyl",
        "Phase_3_Geological_Metallogenic_and_CMCS_Synthesis_Guide_MN.docx",
    ),
    "phase04.guide": (
        "1er5vXLXDX9_s4paZC81xDxbB8mU6UR3e",
        "Phase_4_Preliminary_Prospect_Delineation_and_Ranking_Guide_MN.docx",
    ),
    "phase05.guide": (
        "13RbcciT0bvK5HqT05JFqiTUf92QViVMm",
        "Phase_5_Drone_LiDAR_Photogrammetry_Detailed_Guide_MN.docx",
    ),
}


def test_methodology_authority_and_all_phase_records_are_typed() -> None:
    authority = load_authority_registry()
    assert authority.format_version == "1.1.0"
    source_ids = {source.source_id for source in authority.sources}
    assert "agents.repository-authority" in source_ids
    assert authority.precedence[0] == "agents.repository-authority"
    repository_root = Path(__file__).resolve().parents[1]
    tracked_output = subprocess.check_output(["git", "ls-files", "-z"], cwd=repository_root)
    tracked_paths = set(tracked_output.decode("utf-8").split("\0"))
    for source in authority.sources:
        if source.repository_path is not None:
            assert (repository_root / source.repository_path).exists()
            assert source.external_reference is None
        else:
            assert source.external_reference is not None
            assert source.external_reference.startswith("BUDUUNKHAD_WORKFLOW_DOCS_ROOT::")
        if source.repository_copy is not None:
            assert (repository_root / source.repository_copy).exists()
            assert source.repository_copy in tracked_paths
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


def test_external_authority_can_record_evidence_without_changing_authority() -> None:
    source = MethodologySource.model_validate(
        {
            "source_id": "phase04.synthetic",
            "role": "phase-source",
            "external_reference": "BUDUUNKHAD_WORKFLOW_DOCS_ROOT::phase04-synthetic",
            "authority_status": "adopted",
            "existence_verified": True,
            "external_file_id": "drive-file-id-123",
            "existence_verified_at": "2026-07-17T12:00:00+08:00",
            "existence_verified_by": "methodology-custodian",
            "existence_evidence_reference": "verification-log::phase04-20260717",
        }
    )

    assert source.authority_status == "adopted"
    assert source.external_file_id == "drive-file-id-123"
    assert source.existence_verified_at is not None
    assert source.existence_verified_at.utcoffset() is not None


def test_external_existence_verification_requires_complete_evidence() -> None:
    base = {
        "source_id": "phase04.synthetic",
        "role": "phase-source",
        "external_reference": "BUDUUNKHAD_WORKFLOW_DOCS_ROOT::phase04-synthetic",
        "authority_status": "adopted",
        "existence_verified": True,
    }
    with pytest.raises(ValidationError, match="file ID, timestamp, verifier"):
        MethodologySource.model_validate(base)
    with pytest.raises(ValidationError, match="timezone-aware"):
        MethodologySource.model_validate(
            {
                **base,
                "external_file_id": "drive-file-id-123",
                "existence_verified_at": "2026-07-17T12:00:00",
                "existence_verified_by": "methodology-custodian",
                "existence_evidence_reference": "verification-log::phase04-20260717",
            }
        )


def test_six_connected_drive_sources_have_complete_existence_evidence() -> None:
    authority = load_authority_registry()
    by_id = {source.source_id: source for source in authority.sources}
    verified_external_ids = {
        source.source_id
        for source in authority.sources
        if source.external_reference is not None and source.existence_verified
    }
    assert verified_external_ids == set(VERIFIED_EXTERNAL_SOURCES)

    for source_id, (drive_id, expected_document) in VERIFIED_EXTERNAL_SOURCES.items():
        source = by_id[source_id]
        assert source.expected_document == expected_document
        assert source.external_file_id == drive_id
        assert source.existence_verified is True
        assert source.existence_verified_at is not None
        assert source.existence_verified_at.isoformat() == "2026-07-17T07:55:05+00:00"
        utc_offset = source.existence_verified_at.utcoffset()
        assert utc_offset is not None
        assert utc_offset.total_seconds() == 0
        assert source.existence_verified_by == "Anand Tsogtjargal"
        assert source.existence_evidence_reference == (
            "connected-google-drive-read-only-metadata-verification::2026-07-17T07:55:05Z"
        )
        assert source.authority_status == "adopted"
        assert not source.remaining_actions


def test_unverified_external_id_does_not_claim_existence() -> None:
    source = MethodologySource.model_validate(
        {
            "source_id": "phase04.synthetic",
            "role": "phase-source",
            "external_reference": "BUDUUNKHAD_WORKFLOW_DOCS_ROOT::phase04-synthetic",
            "authority_status": "adopted",
            "existence_verified": False,
            "external_file_id": "drive-file-id-123",
        }
    )
    assert source.external_file_id == "drive-file-id-123"
    assert source.existence_verified is False
    with pytest.raises(ValidationError, match="unverified methodology"):
        MethodologySource.model_validate(
            {
                **source.model_dump(),
                "existence_verified_at": "2026-07-17T12:00:00+08:00",
            }
        )


def test_discrepancy_register_is_the_complete_decision_history() -> None:
    registry = load_discrepancy_registry()
    identities = [item.discrepancy_id for item in registry.discrepancies]
    assert len(set(identities)) == len(identities)
    assert set(identities) == REQUIRED_DISCREPANCY_IDS
    assert identities == [f"METH-DISC-{number:03d}" for number in range(1, 34)]
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


def test_duplicate_inventory_authority_remains_unresolved() -> None:
    registry = load_discrepancy_registry()
    duplicate = next(
        item for item in registry.discrepancies if item.discrepancy_id == "METH-DISC-033"
    )

    assert duplicate.status == "unresolved"
    assert duplicate.compared_sources == (
        "google-drive-file-id:1teePLWFbSOk9ftV4DKdL2Jb5S_fV2Wa9",
        "google-drive-file-id:1ZBxGzYplF_CcoicdQ6AUrTgNOFNRThqS",
    )
    assert "An identical filename alone" in duplicate.statement
    assert "timestamps without lineage evidence" in duplicate.statement
    assert "identical filenames and timestamps" not in duplicate.statement.casefold()
    assert "wrong inventory" in duplicate.operational_impact
    assert duplicate.proposed_resolution is not None
    assert "parent-folder context" in duplicate.proposed_resolution
    assert "bytes and content" in duplicate.proposed_resolution
    assert "internal metadata" in duplicate.proposed_resolution
    assert "lineage" in duplicate.proposed_resolution
    assert duplicate.required_approver == "methodology-owner or project-owner"
    assert duplicate.resolution is None
    assert duplicate.approver is None


def test_readme_describes_current_phase_maturity_without_tracking_more_markdown() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    readme = (repository_root / "README.txt").read_text(encoding="utf-8")
    assert "Phases 00-04 have substantial deterministic implementations." in readme
    assert "Phase 03 remains\nscientifically incomplete" in readme
    assert "Phase 04 remains a legacy comparator" in readme
    assert "deterministic end-to-end implementations" not in readme

    tracked = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=repository_root)
        .decode("utf-8")
        .split("\0")
    )
    tracked_markdown = sorted(
        path
        for path in tracked
        if Path(path).suffix.casefold() in {".md", ".markdown", ".mdown", ".mdwn"}
    )
    assert tracked_markdown == ["AGENTS.md"]


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
