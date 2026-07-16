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
        "buduunkhad/methodology_data/discrepancies.yaml",
        "buduunkhad/methodology_data/phase00.yaml",
        "buduunkhad/methodology_data/phase01.yaml",
        "buduunkhad/methodology_data/phase02.yaml",
        "buduunkhad/methodology_data/phase03.yaml",
        "buduunkhad/methodology_data/phase04.yaml",
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
from buduunkhad.geospatial_ai.methodology import (
    load_authority_registry,
    load_discrepancy_registry,
    load_phase_methodology,
)

assert str(Path(buduunkhad.__file__).resolve()).startswith(str(Path({target_repr}).resolve()))
registry = PromptRegistry.load_packaged(schema_registry=default_schema_registry())
prompt = registry.get("fixture.document-extraction", "1.0.0")
critic = registry.get("fixture.feature-critique", "1.0.0")
vertical = registry.get("vertical.geological-feature-proposal", "1.0.0")
authority = load_authority_registry()
phase05 = load_phase_methodology("05")
discrepancies = load_discrepancy_registry()
assert prompt.components[0].text
assert critic.components[0].text
assert vertical.components[0].text
assert authority.sources
assert phase05.phase_id == "05"
assert len(discrepancies.discrepancies) == 4
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
