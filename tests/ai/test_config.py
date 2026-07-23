import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from buduunkhad.config import (
    AIConfig,
    AIProviderSelection,
    ExecutionProfile,
    ProjectConfig,
    load_config,
)


def test_unchanged_project_yaml_loads_with_offline_legacy_defaults() -> None:
    config = load_config(Path("config/project.yaml"))
    assert config.ai.profile is ExecutionProfile.LEGACY
    assert config.ai.enabled is False
    assert config.ai.provider is AIProviderSelection.DISABLED
    assert config.ai.external_data_allowed is False
    assert config.ai.max_cost_per_run_usd == Decimal("0")
    assert config.ai.max_requests_per_run == 1
    assert config.ai.max_output_tokens == 4096
    assert config.ai.concurrency == 1


def test_legacy_serialization_shape_excludes_ai_by_default() -> None:
    config = load_config(Path("config/project.yaml"))
    snapshot_path = Path("tests/fixtures/legacy_project_config.json")
    expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
    python_dump = _normalize_legacy_dump(config.model_dump())
    json_dump = _normalize_legacy_dump(json.loads(config.model_dump_json()))
    assert python_dump == expected
    assert json_dump == expected
    exact_snapshot = (
        Path("tests/fixtures/legacy_project_config_dump.json").read_text(encoding="utf-8").strip()
    )
    normalized_json_text = json.dumps(
        json_dump,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    assert normalized_json_text == exact_snapshot
    ai_v1 = config.model_dump(context={"config_serialization_version": "ai-v1"})
    assert ai_v1["ai"]["profile"] == "legacy"


def test_project_yaml_bytes_remain_at_the_legacy_baseline() -> None:
    content = Path("config/project.yaml").read_bytes()
    assert hashlib.sha256(content).hexdigest() == (
        "7d4796c895db32e1f3e5e637379dc0126673e4e0fd4595372ad02c4cd9200296"
    )


def test_hybrid_configuration_is_optional_and_typed() -> None:
    config = load_config(Path("config/project.yaml"))
    hybrid = config.ai.model_copy(
        update={
            "profile": ExecutionProfile.HYBRID,
            "enabled": True,
            "provider": AIProviderSelection.OPENAI,
            "provider_model": "synthetic-model",
            "external_data_allowed": True,
            "source_egress_policy": "require-explicit-approval",
            "max_cost_per_run_usd": Decimal("1"),
        }
    )
    assert hybrid.profile is ExecutionProfile.HYBRID
    assert hybrid.external_data_allowed is True
    assert hybrid.provider is AIProviderSelection.OPENAI


def test_ai_config_copy_and_reload_paths_revalidate_security_fields() -> None:
    ai = load_config(Path("config/project.yaml")).ai
    for operation in (
        lambda: ai.model_copy(update={"concurrency": 0}),
        lambda: ai.copy(update={"concurrency": 0}),
        lambda: type(ai).model_validate(ai.model_dump() | {"concurrency": 0}),
        lambda: type(ai).model_validate_json(
            json.dumps(ai.model_dump(mode="json") | {"concurrency": 0})
        ),
    ):
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            operation()


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"enabled": True}, "legacy execution"),
        ({"external_data_allowed": True}, "legacy execution"),
        ({"provider": AIProviderSelection.OPENAI}, "legacy execution"),
        (
            {
                "review_policy": {
                    "require_named_reviewer": False,
                    "high_risk_requires_geologist": True,
                    "production_geometry_requires_approval": True,
                }
            },
            "safeguards",
        ),
    ],
)
def test_project_config_revalidates_security_sensitive_ai_updates_on_every_public_path(
    update: dict[str, object],
    message: str,
) -> None:
    config = load_config(Path("config/project.yaml"))
    ai_values = config.ai.model_dump(mode="python") | update
    project_values = config.model_dump(
        mode="python", context={"config_serialization_version": "ai-v1"}
    )
    project_values["ai"] = ai_values
    json_values = config.model_dump(mode="json", context={"config_serialization_version": "ai-v1"})
    json_values["ai"] = AIConfig.model_validate(config.ai).model_dump(mode="json") | update
    operations = (
        lambda: config.model_copy(update={"ai": ai_values}),
        lambda: config.copy(update={"ai": ai_values}),
        lambda: ProjectConfig.model_validate(project_values),
        lambda: ProjectConfig.model_validate_json(json.dumps(json_values)),
    )
    for operation in operations:
        with pytest.raises(ValidationError, match=message):
            operation()


def test_project_config_unvalidated_construction_apis_fail_explicitly() -> None:
    with pytest.raises(TypeError, match="model_construct"):
        ProjectConfig.model_construct()
    with pytest.raises(TypeError, match="construct"):
        ProjectConfig.construct()


def test_project_config_revalidates_tampered_existing_nested_ai_instance() -> None:
    config = load_config(Path("config/project.yaml")).model_copy()
    tampered_ai = config.ai.model_copy()
    object.__setattr__(tampered_ai, "external_data_allowed", True)
    object.__setattr__(config, "ai", tampered_ai)
    with pytest.raises(ValidationError, match="legacy execution"):
        ProjectConfig.model_validate(config)


def test_only_live_provider_choices_are_user_configurable() -> None:
    assert {item.value for item in AIProviderSelection} == {
        "disabled",
        "openai",
        "anthropic",
    }


def test_unknown_ai_serialization_version_fails() -> None:
    config = load_config(Path("config/project.yaml"))
    with pytest.raises(ValueError, match="unsupported config serialization version"):
        config.model_dump(context={"config_serialization_version": "ai-v2"})


def _normalize_legacy_dump(value: object) -> object:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        result = {key: _normalize_legacy_dump(item) for key, item in value.items()}
        if "base_dir" in result:
            result["base_dir"] = "__REPOSITORY_ROOT__"
        return result
    if isinstance(value, list):
        return [_normalize_legacy_dump(item) for item in value]
    if isinstance(value, str):
        return value.replace("\\", "/")
    return value
