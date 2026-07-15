from __future__ import annotations

from pathlib import Path

import pytest

from buduunkhad.geospatial_ai.methodology import (
    MethodologyError,
    load_authority_registry,
    load_discrepancy_registry,
    load_phase_methodology,
    load_phase_methodology_from_checkout,
)


def test_methodology_authority_and_all_phase_records_are_typed() -> None:
    authority = load_authority_registry()
    source_ids = {source.source_id for source in authority.sources}
    assert "agents.repository-authority" in source_ids
    assert authority.precedence[0] == "agents.repository-authority"
    requirement_ids: set[str] = set()
    for number in range(6):
        phase = load_phase_methodology(f"{number:02d}")
        assert phase.phase_id == f"{number:02d}"
        assert phase.requirements
        for requirement in phase.requirements:
            assert requirement.requirement_id not in requirement_ids
            requirement_ids.add(requirement.requirement_id)
            assert requirement.source_refs


def test_required_methodology_discrepancies_remain_explicit_and_unresolved() -> None:
    registry = load_discrepancy_registry()
    assert {item.discrepancy_id for item in registry.discrepancies} == {
        "METH-DISC-001",
        "METH-DISC-002",
        "METH-DISC-003",
        "METH-DISC-004",
    }
    subjects = {item.subject for item in registry.discrepancies}
    assert subjects == {
        "methodology-input-count",
        "methodology-version-label",
        "phase04-delineation-method",
        "phase05-implementation-status",
    }
    assert all(item.status == "unresolved" for item in registry.discrepancies)
    assert all(item.resolution is None and item.approver is None for item in registry.discrepancies)


def test_methodology_yaml_rejects_duplicate_keys(tmp_path: Path) -> None:
    methodology = tmp_path / "config" / "methodology"
    methodology.mkdir(parents=True)
    (methodology / "phase00.yaml").write_text(
        "format_version: 1.0.0\nphase_id: '00'\nphase_id: '01'\nrequirements: []\n",
        encoding="utf-8",
    )
    with pytest.raises(MethodologyError, match="invalid"):
        load_phase_methodology_from_checkout(tmp_path, "00")
