from __future__ import annotations

import hashlib
import shutil
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
    load_automation_readiness,
    load_discrepancy_registry,
    load_phase02_processing_contract,
    load_phase04_migration_contract,
    load_phase_methodology,
    load_phase_methodology_from_checkout,
)
from buduunkhad.repository_policy import APPROVED_METHODOLOGY_DOCUMENTS

REQUIRED_DISCREPANCY_IDS = {f"METH-DISC-{number:03d}" for number in range(1, 70)}
METHODOLOGY_SNAPSHOT_SHA256 = "05da887bef2d734a9e4507462b85bcbff37f833670cc0dd24d0ba0d7a15a8ecd"
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
    "methodology.master-v5-v6": (
        "13Rle5Bgj0vuKXeXnyy-mT5iLvzwvtloI",
        "XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v6_"
        "Phasewise_File_Processing_Output_Matrix.docx",
    ),
    "phase02.sentinel-qgis402-guide": (
        "1HDS0TItrqcyBmx-q7WbVS-rTibvqh347",
        "XV023222_Buduunkhad_Sentinel2_QGIS402_Detailed_Guide_v01.docx",
    ),
    "phase02.basemap-qgis402-guide": (
        "1sVmEgKaNWbsh9xEFQAuTy-THZYbHzMCA",
        "QGIS_4_0_2_Google_HighResolution_Basemap_Detailed_Guide.docx",
    ),
    "phase02.dem-qgis402-guide": (
        "1hc6mZrqSX1Jt-rUsRcp0XtIHGAckH3Xn",
        "XV023222_Buduunkhad_QGIS402_DEM_ALOS_PALSAR_ASTERGDEM_Detailed_Guide.docx",
    ),
    "phase06.guide": (
        "1cphSAinA-JsIduphfi5-FmFGNq1K7OWF",
        "Phase_6_Recon_Mapping_and_pXRF_Field_Screening_Detailed_Guide_MN.docx",
    ),
    "phase07.guide": (
        "13uu5wdWrop2XT05ikIJb-m7a2YgoXAEd",
        "Phase_7_Rock_Chip_Channel_Verification_Sampling_Guide_MN.docx",
    ),
    "phase08.guide": (
        "1vSZWXwpO1d36s42mT9WVx79sT35t44DV",
        "Phase_8_Orientation_Soil_StreamSediment_HeavyMineral_Check_Detailed_Guide_MN.docx",
    ),
    "phase09.guide": (
        "1zjPWbXfR11rMfqF_9L13D99g6u1PvNfm",
        "Phase_9_Systematic_Soil_Grid_Laboratory_QAQC_Detailed_Guide_MN.docx",
    ),
    "phase10.guide": (
        "1YRLm_4SXOvMz8BO1NRvVv7Jn7nIKGSAo",
        "Phase_10_Integrated_Interpretation_Final_Target_Ranking_Guide_MN.docx",
    ),
    "phase11.guide": (
        "1uUpG-5ySCVrgtjEh62ySulaszREWf6dN",
        "Phase_11_Follow_Up_Trench_Geophysics_Scout_Drill_Planning_Guide_MN.docx",
    ),
    "phase99.guide": (
        "1GlYTv_v4StNTv9fyag41g-WT0g4v27-O",
        "99_Final_Deliverables_Detailed_Guide_MN.docx",
    ),
}

NEW_SNAPSHOT_VERIFICATION_IDS = {
    "methodology.master-v5-v6",
    "phase02.sentinel-qgis402-guide",
    "phase02.basemap-qgis402-guide",
    "phase02.dem-qgis402-guide",
    "phase06.guide",
    "phase07.guide",
    "phase08.guide",
    "phase09.guide",
    "phase10.guide",
    "phase11.guide",
    "phase99.guide",
}


def test_methodology_authority_and_all_phase_records_are_typed() -> None:
    authority = load_authority_registry()
    assert authority.format_version == "1.3.0"
    assert authority.precedence == (
        "methodology.master-v9",
        "repository.methodology-contracts",
    )
    repository_root = Path(__file__).resolve().parents[1]
    tracked_output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repository_root,
    )
    tracked_paths = set(tracked_output.decode("utf-8").split("\0"))
    for source in authority.sources:
        if source.repository_path is not None:
            assert (repository_root / source.repository_path).exists()
            assert source.external_reference is None
        else:
            assert source.external_reference is not None
            assert source.external_reference.startswith("BUDUUNKHAD_WORKFLOW_DOCS_ROOT::")
        if source.repository_copy is not None:
            copy = repository_root / source.repository_copy
            assert copy.is_file() and not copy.is_symlink()
            assert source.repository_copy in tracked_paths
            assert source.repository_copy_sha256 == hashlib.sha256(copy.read_bytes()).hexdigest()
            assert source.repository_copy_size_bytes == copy.stat().st_size
            assert source.repository_snapshot_sha256 == METHODOLOGY_SNAPSHOT_SHA256
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
        # A registered identifier is not existence verification. Active unverified
        # documents need a follow-up action; an obsolete source may remain as history.
        if not source.existence_verified and source.authority_status != "obsolete":
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


def test_reviewed_drive_sources_have_complete_existence_evidence() -> None:
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
        expected_time = (
            "2026-07-20T03:14:02+00:00"
            if source_id in NEW_SNAPSHOT_VERIFICATION_IDS
            else "2026-07-17T07:55:05+00:00"
        )
        assert source.existence_verified_at.isoformat() == expected_time
        utc_offset = source.existence_verified_at.utcoffset()
        assert utc_offset is not None
        assert utc_offset.total_seconds() == 0
        if source_id in NEW_SNAPSHOT_VERIFICATION_IDS:
            assert source.existence_verified_by == "Codex read-only review"
            assert source.existence_evidence_reference == (
                "verified-local-snapshot-copy::"
                "05da887bef2d734a9e4507462b85bcbff37f833670cc0dd24d0ba0d7a15a8ecd"
            )
        else:
            assert source.existence_verified_by == "Anand Tsogtjargal"
            assert source.existence_evidence_reference == (
                "connected-google-drive-read-only-metadata-verification::2026-07-17T07:55:05Z"
            )
            expected_status = "reference-only" if source_id == "phase05.guide" else "adopted"
            assert source.authority_status == expected_status
            assert not source.remaining_actions


def test_repository_methodology_copies_match_the_exact_policy_catalog() -> None:
    authority = load_authority_registry()
    repository_copies = {
        source.repository_copy
        for source in authority.sources
        if source.repository_copy is not None
        and source.repository_copy.startswith("docs/methodology/")
    }
    approved_paths = {path.as_posix() for path in APPROVED_METHODOLOGY_DOCUMENTS}
    assert repository_copies == approved_paths
    repository_root = Path(__file__).resolve().parents[1]
    for source in authority.sources:
        if source.repository_copy is None:
            continue
        path = source.repository_copy
        assert (
            source.repository_copy_sha256
            == APPROVED_METHODOLOGY_DOCUMENTS[
                next(item for item in APPROVED_METHODOLOGY_DOCUMENTS if item.as_posix() == path)
            ]
        )
        assert source.repository_copy_size_bytes == (repository_root / path).stat().st_size
        assert source.repository_snapshot_sha256 == METHODOLOGY_SNAPSHOT_SHA256

    by_id = {source.source_id: source for source in authority.sources}
    assert by_id["methodology.master-v5-v6"].authority_status == "obsolete"
    assert by_id["phase02.aster-sop"].authority_status == "obsolete"
    assert by_id["phase05.guide"].authority_status == "reference-only"
    for source_id in (
        "phase02.sentinel-qgis402-guide",
        "phase02.basemap-qgis402-guide",
        "phase02.dem-qgis402-guide",
    ):
        assert by_id[source_id].authority_status == "reference-only"
    for phase in ("06", "07", "08", "09", "10", "11", "99"):
        assert by_id[f"phase{phase}.guide"].authority_status == "pending-review"


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


def test_repository_copy_requires_complete_portable_identity() -> None:
    base = {
        "source_id": "phase04.synthetic",
        "role": "phase-source",
        "external_reference": "BUDUUNKHAD_WORKFLOW_DOCS_ROOT::phase04-synthetic",
        "authority_status": "reference-only",
        "expected_document": "guide.docx",
        "repository_copy": "docs/methodology/phase_04/guide.docx",
        "existence_verified": False,
    }
    with pytest.raises(ValidationError, match="requires SHA-256"):
        MethodologySource.model_validate(base)
    with pytest.raises(ValidationError, match="below docs/methodology"):
        MethodologySource.model_validate(
            {
                **base,
                "repository_copy": "docs/methodology/../outside/guide.docx",
                "repository_copy_sha256": "a" * 64,
                "repository_copy_size_bytes": 1,
                "repository_snapshot_sha256": "b" * 64,
            }
        )
    source = MethodologySource.model_validate(
        {
            **base,
            "repository_copy_sha256": "a" * 64,
            "repository_copy_size_bytes": 1,
            "repository_snapshot_sha256": "b" * 64,
        }
    )
    assert source.repository_copy_size_bytes == 1


def test_discrepancy_register_is_the_complete_decision_history() -> None:
    registry = load_discrepancy_registry()
    identities = [item.discrepancy_id for item in registry.discrepancies]
    assert len(set(identities)) == len(identities)
    assert set(identities) == REQUIRED_DISCREPANCY_IDS
    assert identities == [f"METH-DISC-{number:03d}" for number in range(1, 70)]
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
            assert item.blocker_category is None
            assert not item.missing_evidence
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
        replacement = by_id[item.superseded_by]  # ty: ignore[invalid-argument-type]
        assert replacement.status in {"resolved", "unresolved"}
    cyclic = {
        "format_version": "1.4.0",
        "discrepancies": [
            _record("METH-DISC-901", status="superseded", superseded_by="METH-DISC-902"),
            _record("METH-DISC-902", status="superseded", superseded_by="METH-DISC-901"),
        ],
    }
    with pytest.raises(ValidationError, match="cyclic"):
        DiscrepancyRegistry.model_validate(cyclic)
    dangling = {
        "format_version": "1.4.0",
        "discrepancies": [
            _record("METH-DISC-901", status="superseded", superseded_by="METH-DISC-999"),
        ],
    }
    with pytest.raises(ValidationError, match="unknown record"):
        DiscrepancyRegistry.model_validate(dangling)


def test_unresolved_view_filters_without_erasing_history() -> None:
    registry = load_discrepancy_registry()
    open_items = registry.unresolved()
    assert not open_items
    historical = registry.historical_unresolved()
    assert {item.discrepancy_id for item in historical} == {
        "METH-DISC-002",
        "METH-DISC-003",
        "METH-DISC-004",
        "METH-DISC-005",
        "METH-DISC-029",
        "METH-DISC-030",
        "METH-DISC-031",
        "METH-DISC-033",
        "METH-DISC-034",
        "METH-DISC-035",
        "METH-DISC-036",
        "METH-DISC-037",
        "METH-DISC-038",
        "METH-DISC-039",
        "METH-DISC-040",
        "METH-DISC-041",
        "METH-DISC-042",
        "METH-DISC-043",
        "METH-DISC-044",
        "METH-DISC-045",
        "METH-DISC-046",
        "METH-DISC-047",
    }
    assert all(item.status == "unresolved" for item in historical)


def test_historical_resolutions_match_their_documented_states() -> None:
    registry = load_discrepancy_registry()
    by_id = {item.discrepancy_id: item for item in registry.discrepancies}
    input_count = by_id["METH-DISC-001"]
    assert input_count.status == "resolved"
    assert input_count.effective_version == "v0.1.0"
    assert "79" in input_count.resolution  # ty: ignore[unsupported-operator]
    scoring = by_id["METH-DISC-006"]
    assert scoring.status == "resolved"
    assert scoring.resolved_on == "2026-07-06"
    assert "Phase 10" in scoring.resolution  # ty: ignore[unsupported-operator]
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
    assert subjects["kompsat-fail-closed-exclusion"].resolves_discrepancy_ids == ("METH-DISC-029",)
    assert subjects["detected-content-handling-for-mislabeled-scans"].resolves_discrepancy_ids == (
        "METH-DISC-030",
    )
    assert subjects["phase-gate-provisional-advance"].status == "unresolved"
    assert subjects["phase03-non-overridable-scientific-handoff"].resolves_discrepancy_ids == (
        "METH-DISC-031",
    )


def test_duplicate_inventory_history_is_preserved_without_selecting_a_drive_copy() -> None:
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
    decision = next(
        item for item in registry.discrepancies if item.discrepancy_id == "METH-DISC-051"
    )
    assert decision.resolves_discrepancy_ids == ("METH-DISC-033",)
    assert "sole execution inventory contract" in decision.resolution  # ty: ignore[unsupported-operator]
    assert "designate neither one canonical" in decision.resolution  # ty: ignore[unsupported-operator]


def test_phase00_to_phase05_review_findings_preserve_history_and_current_status() -> None:
    registry = load_discrepancy_registry()
    by_id = {item.discrepancy_id: item for item in registry.discrepancies}
    expected_subjects = {
        "METH-DISC-034": "aster-sop-and-reference-evidence-binding",
        "METH-DISC-035": "sentinel-operator-guide-versus-registered-inputs",
        "METH-DISC-036": "basemap-guide-phase-label",
        "METH-DISC-037": "basemap-buffer-policy",
        "METH-DISC-038": "dem-parameter-authority",
        "METH-DISC-039": "phase01-generated-boundary-wording",
        "METH-DISC-040": "phase03-evidence-readiness-overstatement",
        "METH-DISC-041": "phase04-scoring-semantics-versus-guide",
        "METH-DISC-042": "phase05-guide-origin-and-operational-parameters",
        "METH-DISC-043": "inventory-status-versus-observed-files",
        "METH-DISC-044": "georeference-crs-residual-evidence-gaps",
        "METH-DISC-045": "aster-kompsat-technical-readiness",
        "METH-DISC-046": "licence-boundary-qaqc-completeness",
        "METH-DISC-047": "duplicate-qaqc-register-lineage",
    }
    for identity, subject in expected_subjects.items():
        item = by_id[identity]
        assert item.subject == subject
        assert item.status == "unresolved"
        assert item.required_approver and item.remaining_actions
        assert item.resolution is None and item.approver is None
    assert by_id["METH-DISC-041"].related_discrepancy_ids == (
        "METH-DISC-003",
        "METH-DISC-006",
    )
    assert "this chat" in by_id["METH-DISC-042"].statement
    assert "authoritative" in by_id["METH-DISC-040"].statement


def test_master_first_reconciliation_links_all_historical_policy_decisions() -> None:
    registry = load_discrepancy_registry()
    assert not registry.unresolved()
    by_id = {item.discrepancy_id: item for item in registry.discrepancies}
    expected_links = {
        "METH-DISC-048": "METH-DISC-004",
        "METH-DISC-049": "METH-DISC-029",
        "METH-DISC-050": "METH-DISC-030",
        "METH-DISC-051": "METH-DISC-033",
        "METH-DISC-052": "METH-DISC-037",
        "METH-DISC-053": "METH-DISC-038",
        "METH-DISC-054": "METH-DISC-043",
        "METH-DISC-055": "METH-DISC-044",
        "METH-DISC-056": "METH-DISC-045",
        "METH-DISC-057": "METH-DISC-046",
        "METH-DISC-058": "METH-DISC-047",
        "METH-DISC-059": "METH-DISC-002",
        "METH-DISC-060": "METH-DISC-003",
        "METH-DISC-061": "METH-DISC-005",
        "METH-DISC-062": "METH-DISC-031",
        "METH-DISC-063": "METH-DISC-034",
        "METH-DISC-064": "METH-DISC-035",
        "METH-DISC-065": "METH-DISC-036",
        "METH-DISC-066": "METH-DISC-039",
        "METH-DISC-067": "METH-DISC-040",
        "METH-DISC-068": "METH-DISC-041",
        "METH-DISC-069": "METH-DISC-042",
    }
    for decision_id, historical_id in expected_links.items():
        decision = by_id[decision_id]
        assert decision.status == "resolved"
        assert decision.resolves_discrepancy_ids == (historical_id,)
        assert decision.approver == "repository-owner directive"
        assert decision.resolved_on == "2026-07-22"
    for historical_id in (
        "METH-DISC-002",
        "METH-DISC-003",
        "METH-DISC-005",
        "METH-DISC-031",
        "METH-DISC-034",
        "METH-DISC-035",
        "METH-DISC-036",
        "METH-DISC-039",
        "METH-DISC-040",
        "METH-DISC-041",
        "METH-DISC-042",
    ):
        record = by_id[historical_id]
        assert record.status == "unresolved"
        assert record.resolution is None
        assert record.approver is None


def test_phase04_master_aligned_target_is_typed_and_separate_from_legacy() -> None:
    contract = load_phase04_migration_contract()
    assert contract.status == "specified-not-integrated"
    assert contract.legacy_comparator_status == "retained-regression-only"
    assert contract.target_geometry == "human-reviewed-prospect-polygons"
    assert contract.scoring_source == "phase04.guide"
    assert contract.class_band_source == "methodology.master-v9"
    assert contract.decision_sources == ("METH-DISC-060", "METH-DISC-068")
    assert sum(item.maximum_points for item in contract.criteria) == 100
    assert [
        (band.class_id, band.minimum_score, band.maximum_score) for band in contract.class_bands
    ] == [
        ("A", 75, 100),
        ("B", 55, 74),
        ("C", 35, 54),
        ("D", 0, 34),
    ]
    assert set(contract.blocking_readiness_ids) == {
        "METH-READY-004",
        "METH-READY-005",
        "METH-READY-006",
        "METH-READY-007",
    }
    assert any(
        "provenance-bound human reference set" in item for item in contract.activation_requirements
    )
    assert all(
        "six human reference prospects" not in item for item in contract.activation_requirements
    )
    assert any("cannot publish" in item for item in contract.ai_policy)

    changed = contract.model_dump(mode="python")
    changed["criteria"][0]["maximum_points"] = 19
    with pytest.raises(ValidationError, match="adopted desktop matrix"):
        type(contract).model_validate(changed)


def test_phase_source_references_fail_closed_when_unknown(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    methodology = tmp_path / "config" / "methodology"
    shutil.copytree(repository_root / "config" / "methodology", methodology)
    phase = methodology / "phase00.yaml"
    phase.write_text(
        phase.read_text(encoding="utf-8").replace(
            "METH-DISC-008",
            "METH-DISC-999",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(MethodologyError, match="unknown methodology sources"):
        load_phase_methodology_from_checkout(tmp_path, "00")


def test_readme_describes_current_phase_maturity_and_authority_location() -> None:
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
    assert "docs/methodology/" in readme


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
    assert implemented == {"00", "01", "02"}
    assert next(item for item in registry.boundaries if item.phase_id == "03").status == (
        "partially-implemented"
    )
    assert next(item for item in registry.boundaries if item.phase_id == "04").status == (
        "legacy-comparator"
    )
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

    phase02 = next(item for item in registry.boundaries if item.phase_id == "02")
    phase02_text = " ".join((*phase02.deterministic_authority, *phase02.blocking_dependencies))
    assert "frozen ASTER support-evidence chain" in phase02_text
    assert "adopted ASTER SOP chain" not in phase02_text


def test_operational_readiness_preserves_real_evidence_and_human_blockers() -> None:
    registry = load_automation_readiness()
    by_id = {item.obligation_id: item for item in registry.obligations}
    assert set(by_id) == {f"METH-READY-{number:03d}" for number in range(1, 8)}
    assert by_id["METH-READY-001"].status == "parked"
    assert by_id["METH-READY-002"].status == "excluded"
    assert not by_id["METH-READY-002"].blocks_phase_completion
    assert by_id["METH-READY-004"].blocks_phase_completion
    assert by_id["METH-READY-005"].blocks_phase_completion
    assert "qualified geospatial reviewer" in by_id["METH-READY-005"].required_human_authority
    combined = " ".join(
        text
        for item in registry.obligations
        for text in (
            item.decision,
            *item.required_evidence,
            *item.deterministic_next_steps,
        )
    )
    assert "scientific approval" not in combined.casefold()


def test_phase02_processing_decisions_are_exact_and_support_only() -> None:
    from buduunkhad.core.hydrology import HydrologyParams
    from buduunkhad.phases import phase02_remote_sensing

    contract = load_phase02_processing_contract()
    assert contract.scientific_use == "support-evidence-only"
    assert contract.decision_sources == ("METH-DISC-052", "METH-DISC-053")
    basemaps = {item.input_number: item for item in contract.basemap_assets}
    assert basemaps[75].operation == "reproject-full-extent"
    assert basemaps[75].clip_buffer_m is None
    assert basemaps[76].operation == "reproject-and-clip"
    assert basemaps[76].clip_buffer_m == 1000
    profiles = {item.input_number: item for item in contract.dem_profiles}
    primary = profiles[12]
    assert primary.clip_buffer_m == 5000
    assert primary.contour_interval_m == 20
    assert primary.stream_threshold_cells == 1000
    assert primary.minimum_basin_area_ha == 25
    assert primary.sink_treatment == "fill-depressions"
    assert profiles[9].vector_hydrology is False
    assert profiles[9].contour_interval_m is None

    # The versioned contract freezes the current support-only implementation rather than
    # creating a second, drifting parameter source.
    params = HydrologyParams()
    assert primary.clip_buffer_m == phase02_remote_sensing._DEM_CLIP_M
    assert basemaps[76].clip_buffer_m == phase02_remote_sensing._BASEMAP_CLIP_M
    assert params.contour_interval_m == primary.contour_interval_m
    assert params.stream_threshold_cells == primary.stream_threshold_cells
    assert params.min_basin_area_ha == primary.minimum_basin_area_ha


def test_resolution_links_fail_closed_and_preserve_append_only_history() -> None:
    unresolved = {
        "discrepancy_id": "METH-DISC-900",
        "subject": "synthetic-open-decision",
        "compared_sources": ["source-a", "source-b"],
        "statement": "Synthetic open item.",
        "operational_impact": "Synthetic only.",
        "status": "unresolved",
        "proposed_resolution": "Record a later linked decision.",
        "required_approver": "project-owner",
        "remaining_actions": ["Decide."],
        "affected_phases": ["03"],
        "blocker_category": "implementation",
        "missing_evidence": ["Decision."],
    }
    resolution = _record("METH-DISC-901", status="resolved")
    resolution["resolves_discrepancy_ids"] = ["METH-DISC-900"]
    registry = DiscrepancyRegistry.model_validate(
        {"format_version": "1.4.0", "discrepancies": [unresolved, resolution]}
    )
    assert not registry.unresolved()
    assert tuple(item.discrepancy_id for item in registry.historical_unresolved()) == (
        "METH-DISC-900",
    )

    dangling = dict(resolution)
    dangling["resolves_discrepancy_ids"] = ["METH-DISC-999"]
    with pytest.raises(ValidationError, match="unknown record"):
        DiscrepancyRegistry.model_validate(
            {"format_version": "1.4.0", "discrepancies": [unresolved, dangling]}
        )

    duplicate = dict(resolution)
    duplicate["resolves_discrepancy_ids"] = ["METH-DISC-900", "METH-DISC-900"]
    with pytest.raises(ValidationError, match="contains duplicates"):
        DiscrepancyRegistry.model_validate(
            {"format_version": "1.4.0", "discrepancies": [unresolved, duplicate]}
        )

    forward = dict(resolution)
    forward["discrepancy_id"] = "METH-DISC-899"
    with pytest.raises(ValidationError, match="only earlier"):
        DiscrepancyRegistry.model_validate(
            {"format_version": "1.4.0", "discrepancies": [forward, unresolved]}
        )


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
                "affected_phases": ["03"],
                "blocker_category": "implementation",
                "missing_evidence": ["Synthetic missing evidence."],
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
