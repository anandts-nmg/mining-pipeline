from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from buduunkhad.cli import app
from buduunkhad.geospatial_ai.readiness import (
    build_methodology_readiness_report,
    render_methodology_readiness_report,
)


def test_master_first_readiness_report_is_deterministic_and_truthful() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    manifest = repository_root / "config" / "raw_manifest.csv"

    first = build_methodology_readiness_report(manifest)
    second = build_methodology_readiness_report(manifest)
    assert first == second
    assert render_methodology_readiness_report(first) == render_methodology_readiness_report(second)
    assert first.discrepancy_total == 69
    assert first.unresolved_count == 0
    assert first.historical_unresolved_record_count == 22
    assert len(first.obligations) == 7
    assert all(obligation.affected_phases for obligation in first.obligations)
    assert all(obligation.required_evidence for obligation in first.obligations)
    assert [item.model_dump() for item in first.missing_registered_inputs] == [
        {
            "input_number": 23,
            "filename": "KOMPSATEULAForm_3.1.pdf",
            "manifest_status": "MISSING_in_0_Raw_Data",
            "drive_file_id": None,
        }
    ]
    assert (
        first.interpretation
        == "resolved methodology decisions plus operational prerequisites; not scientific "
        "approval or a gate decision"
    )
    assert first.phase04_target_status == "specified-not-integrated"
    assert any(
        "provenance-bound human reference set" in item
        for item in first.phase04_activation_requirements
    )
    assert all(
        "six human reference prospects" not in item
        for item in first.phase04_activation_requirements
    )


def test_readiness_report_groups_open_obligations_by_phase() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    report = build_methodology_readiness_report(repository_root / "config" / "raw_manifest.csv")
    phases = {item.phase_id: item for item in report.phases}
    assert "METH-READY-004" in phases["03"].obligation_ids
    assert phases["03"].implementation_status == "partially-implemented"
    assert phases["03"].status == "blocked-operational-obligations"
    assert "METH-READY-001" in phases["05"].obligation_ids
    assert phases["05"].implementation_status == "stub"
    assert phases["05"].status == "parked"
    assert phases["04"].implementation_status == "legacy-comparator"
    assert phases["06"].implementation_status == "stub"
    assert phases["06"].status == "no-open-operational-obligations"
    assert not phases["06"].obligation_ids


def test_methodology_status_cli_uses_configured_manifest_without_raw_access(project) -> None:
    _config, _register, work = project
    result = CliRunner().invoke(
        app,
        ["methodology-status", "--config", str(work / "config" / "project.yaml")],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["unresolved_count"] == 0
    assert payload["historical_unresolved_record_count"] == 22
    assert payload["obligations"][0]["obligation_id"] == "METH-READY-001"
    assert payload["missing_registered_inputs"][0]["input_number"] == 23
    assert "raw_root" not in result.stdout
    assert "BUDUUNKHAD" not in result.stdout
