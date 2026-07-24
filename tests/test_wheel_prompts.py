"""Non-editable wheel smoke test for packaged prompt resources."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


def test_installed_wheel_loads_packaged_prompt_registry(tmp_path: Path) -> None:
    wheel_value = os.environ.get("BUDUUNKHAD_TEST_WHEEL")
    if wheel_value is None:
        pytest.skip("exact wheel smoke test is activated by the post-build CI step")
    wheel = Path(wheel_value).resolve()
    expected_sha256 = os.environ.get("BUDUUNKHAD_TEST_WHEEL_SHA256")
    assert wheel.is_file()
    if expected_sha256 is not None:
        assert hashlib.sha256(wheel.read_bytes()).hexdigest() == expected_sha256
    target = tmp_path / "installed"
    outside = tmp_path / "outside-checkout"
    outside.mkdir()
    env = os.environ.copy()
    env.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
        }
    )
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    expected_resources = {
        "buduunkhad/core/evidence_manifest.py",
        "buduunkhad/prompt_data/registry.yaml",
        "buduunkhad/prompt_data/prompt-lock.yaml",
        "buduunkhad/prompt_data/fixtures/document_extraction/1.0.0/system.txt",
        "buduunkhad/prompt_data/fixtures/document_extraction/1.0.0/user.txt",
        "buduunkhad/prompt_data/fixtures/feature_critique/1.0.0/system.txt",
        "buduunkhad/prompt_data/fixtures/feature_critique/1.0.0/user.txt",
        "buduunkhad/prompt_data/vertical/geological_feature_proposal/1.0.0/system.txt",
        "buduunkhad/prompt_data/vertical/geological_feature_proposal/1.0.0/user.txt",
        "buduunkhad/prompt_data/vertical/legend_extraction/1.0.0/system.txt",
        "buduunkhad/prompt_data/vertical/legend_extraction/1.0.0/user.txt",
        "buduunkhad/prompt_data/vertical/map_feature_interpretation/1.0.0/system.txt",
        "buduunkhad/prompt_data/vertical/map_feature_interpretation/1.0.0/user.txt",
        "buduunkhad/prompt_data/vertical/feature_critique/1.0.0/system.txt",
        "buduunkhad/prompt_data/vertical/feature_critique/1.0.0/user.txt",
        "buduunkhad/schema_data/contracts.json",
        "buduunkhad/methodology_data/authority.yaml",
        "buduunkhad/methodology_data/automation_boundaries.yaml",
        "buduunkhad/methodology_data/automation_readiness.yaml",
        "buduunkhad/methodology_data/execution_policy.yaml",
        "buduunkhad/methodology_data/discrepancies.yaml",
        "buduunkhad/methodology_data/phase00.yaml",
        "buduunkhad/methodology_data/phase01.yaml",
        "buduunkhad/methodology_data/phase02.yaml",
        "buduunkhad/methodology_data/phase02_processing.yaml",
        "buduunkhad/methodology_data/phase03.yaml",
        "buduunkhad/methodology_data/phase04.yaml",
        "buduunkhad/methodology_data/phase04_migration.yaml",
        "buduunkhad/methodology_data/phase05.yaml",
    }
    assert expected_resources <= names
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-index",
            "--target",
            str(target),
            str(wheel),
        ],
        cwd=outside,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    smoke_env = env | {"PYTHONPATH": str(target)}
    target_repr = repr(str(target))
    script = f"""
from pathlib import Path
import buduunkhad
from buduunkhad.ai.prompts import PromptRegistry, default_schema_registry
from buduunkhad.core.evidence_manifest import (
    EVIDENCE_CATALOG_FORMAT_VERSION,
    EVIDENCE_MANIFEST_FORMAT_VERSION,
)
from buduunkhad.core.execution_policy import ExecutionMode, load_execution_policy
from buduunkhad.core.publication_manifest import PUBLICATION_MANIFEST_FORMAT_VERSION
from buduunkhad.core.run_storage import (
    RUN_MANIFEST_FORMAT_VERSION,
    SUPPORTED_RUN_MANIFEST_FORMAT_VERSIONS,
    SourcePhaseBinding,
)
from buduunkhad.geospatial_ai.methodology import (
    load_authority_registry,
    load_automation_readiness,
    load_discrepancy_registry,
    load_phase02_processing_contract,
    load_phase04_migration_contract,
    load_phase_methodology,
)

assert str(Path(buduunkhad.__file__).resolve()).startswith(str(Path({target_repr}).resolve()))
registry = PromptRegistry.load_packaged(schema_registry=default_schema_registry())
prompt = registry.get("fixture.document-extraction", "1.0.0")
critic = registry.get("fixture.feature-critique", "1.0.0")
vertical = registry.get("vertical.geological-feature-proposal", "1.0.0")
authority = load_authority_registry()
phase05 = load_phase_methodology("05")
phase03 = load_phase_methodology("03")
phase04 = load_phase_methodology("04")
discrepancies = load_discrepancy_registry()
phase04_migration = load_phase04_migration_contract()
readiness = load_automation_readiness()
execution_policy = load_execution_policy()
phase02_processing = load_phase02_processing_contract()
assert prompt.components[0].text
assert critic.components[0].text
assert vertical.components[0].text
assert authority.sources
assert phase05.phase_id == "05"
assert buduunkhad.__version__ == "0.8.1"
assert EVIDENCE_MANIFEST_FORMAT_VERSION == "1.0.0"
assert EVIDENCE_CATALOG_FORMAT_VERSION == "1.0.0"
assert RUN_MANIFEST_FORMAT_VERSION == "2.2.0"
assert SUPPORTED_RUN_MANIFEST_FORMAT_VERSIONS == {{"2.0.0", "2.1.0", "2.2.0"}}
assert PUBLICATION_MANIFEST_FORMAT_VERSION == "1.2.0"
assert execution_policy.phase_policies[4].default_real_mode is ExecutionMode.LEGACY_COMPARATOR
binding = SourcePhaseBinding(
    phase_id="00",
    source_run_id="source-run",
    source_manifest_sha256="a" * 64,
    source_phase_sha256="b" * 64,
)
assert binding.phase_id == "00"
assert "P03-EVIDENCE-AUTHORITY-001" in {{item.requirement_id for item in phase03.requirements}}
assert "P04-EVIDENCE-AUTHORITY-001" in {{item.requirement_id for item in phase04.requirements}}
assert len(discrepancies.discrepancies) == 69
assert any(
    item.discrepancy_id == "METH-DISC-033"
    for item in discrepancies.discrepancies
)
assert discrepancies.discrepancies[-1].discrepancy_id == "METH-DISC-069"
assert len(discrepancies.unresolved()) == 0
assert len(discrepancies.historical_unresolved()) == 22
assert len(readiness.obligations) == 7
assert phase02_processing.scientific_use == "support-evidence-only"
assert phase04_migration.status == "specified-not-integrated"
print(prompt.identity.sha256)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=outside,
        env=smoke_env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert len(result.stdout.strip()) == 64
