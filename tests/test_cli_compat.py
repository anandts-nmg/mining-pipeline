"""Behavioral compatibility checks for the unchanged Typer CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from buduunkhad.cli import app
from buduunkhad.config import OUTPUT_ROOT_ENV, RAW_ROOT_ENV

runner = CliRunner()


def test_help_lists_stable_core_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("run", "list", "info", "validate", "phase00", "phase99"):
        assert command in result.stdout


def test_ai_help_is_additive_and_keeps_execution_steps_separate() -> None:
    result = runner.invoke(app, ["ai", "--help"])
    assert result.exit_code == 0
    for command in (
        "snapshot-create",
        "snapshot-verify",
        "prepare",
        "approve-egress",
        "execute",
        "ingest-response",
        "process-response",
        "evaluate",
        "inspect-job",
    ):
        assert command in result.stdout

    phase03 = runner.invoke(app, ["ai", "phase03", "--help"])
    assert phase03.exit_code == 0
    assert "import-ai-draft" in phase03.stdout
    assert "promote-reviewed" in phase03.stdout


def test_list_and_info_preserve_legacy_contract(project) -> None:
    config, _register, work = project
    config_path = work / "config" / "project.yaml"
    listed = runner.invoke(app, ["list"])
    assert listed.exit_code == 0
    assert "Registered phases (00 -> 99)" in listed.stdout
    assert "00  [BUILD]" in listed.stdout
    info = runner.invoke(app, ["info", "--config", str(config_path)])
    assert info.exit_code == 0
    assert config.project.project_code in info.stdout
    assert config.crs.target_authority in info.stdout
    assert "79 inputs" in info.stdout


def test_validate_synthetic_configuration(raw_archive) -> None:
    _config, _register, _raw_root = raw_archive
    config_path = _raw_root.parent.parent / "config" / "project.yaml"
    result = runner.invoke(app, ["validate", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "all 79 raw inputs present" in result.stdout


def test_run_dry_run_uses_legacy_defaults(project) -> None:
    _config, _register, work = project
    config_path = work / "config" / "project.yaml"
    result = runner.invoke(app, ["run", "--config", str(config_path), "--dry-run"])
    assert result.exit_code == 0
    assert "dry_run=True" in result.stdout
    assert "00  dry-run" in result.stdout
    assert "05  dry-run" in result.stdout


def test_info_honors_existing_environment_path_overrides(project, monkeypatch) -> None:
    _config, _register, work = project
    config_path = work / "config" / "project.yaml"
    raw_override = Path(work) / "env-raw"
    output_override = Path(work) / "env-output"
    monkeypatch.setenv(RAW_ROOT_ENV, str(raw_override))
    monkeypatch.setenv(OUTPUT_ROOT_ENV, str(output_override))
    result = runner.invoke(app, ["info", "--config", str(config_path)])
    assert result.exit_code == 0
    assert str(raw_override) in result.stdout
    assert str(output_override) in result.stdout
