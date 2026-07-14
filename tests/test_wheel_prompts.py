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

assert str(Path(buduunkhad.__file__).resolve()).startswith(str(Path({target_repr}).resolve()))
registry = PromptRegistry.load_packaged(schema_registry=default_schema_registry())
prompt = registry.get("fixture.document-extraction", "1.0.0")
critic = registry.get("fixture.feature-critique", "1.0.0")
assert prompt.components[0].text
assert critic.components[0].text
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
