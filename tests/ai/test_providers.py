from __future__ import annotations

import hashlib
import importlib
import sys
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import Literal, cast

import pytest
from pydantic import Field, PrivateAttr, RootModel, computed_field, model_serializer

from buduunkhad.ai.contracts import (
    AIUsage,
    CanonicalJSONValue,
    FrozenModel,
    NamedJSONValue,
    ReviewStatus,
    TaskType,
)
from buduunkhad.ai.providers import (
    AIProviderError,
    AnthropicProvider,
    OpenAIProvider,
    ProviderCall,
    ProviderCredentialError,
    ProviderDependencyError,
    ProviderImage,
    ProviderResponseError,
    decode_provider_json,
    prohibit_provider_approval,
    validate_provider_output_contract,
)
from tests.support.providers import (
    AnthropicMessagesDouble,
    FailingResponsesDouble,
    OpenAIResponsesDouble,
    provider_client,
)


class SampleOutput(FrozenModel):
    title: str = Field(min_length=1)


class AliasedApproval(FrozenModel):
    review_status: ReviewStatus = Field(alias="state")


class ExcludedApproval(FrozenModel):
    review_status: ReviewStatus = Field(exclude=True)


class NestedApproval(FrozenModel):
    nested: ExcludedApproval


class ComputedApproval(FrozenModel):
    title: str

    @computed_field
    @property
    def reviewer_id(self) -> str:
        return "human-reviewer"


class PrivateApproval(FrozenModel):
    title: str
    _review_status: ReviewStatus = PrivateAttr(default=ReviewStatus.GEOLOGIST_APPROVED)


class RootApproval(RootModel[dict[str, str]]):
    pass


class CustomSerializedApproval(FrozenModel):
    review_status: ReviewStatus

    @model_serializer
    def serialize_model(self) -> dict[str, str]:
        return {"apparently_safe": "value"}


@dataclass(frozen=True)
class ApprovalDataclass:
    reviewer_name: str


class DataclassApproval(FrozenModel):
    payload: ApprovalDataclass


class CanonicalApproval(FrozenModel):
    payload: CanonicalJSONValue


class NamedApproval(FrozenModel):
    payload: NamedJSONValue


class CustomSerializedOutput(FrozenModel):
    title: str

    @model_serializer
    def serialize_model(self) -> dict[str, str]:
        return {"title": self.title}


class ComputedOutput(FrozenModel):
    title: str

    @computed_field
    @property
    def title_length(self) -> int:
        return len(self.title)


class ExcludedOutput(FrozenModel):
    title: str
    hidden: str = Field(exclude=True)


def _call(provider: str) -> ProviderCall:
    data = b"synthetic-image"
    return ProviderCall(
        request_id="request-1",
        request_fingerprint="a" * 64,
        task_type=TaskType.LEGEND_EXTRACTION,
        provider=cast(Literal["openai", "anthropic"], provider),
        model="synthetic-model",
        system_prompt="Return structured test data.",
        user_prompt="Read the synthetic image.",
        output_schema=CanonicalJSONValue.from_value(SampleOutput.model_json_schema()),
        images=(
            ProviderImage(
                tile_id="tile-1",
                media_type="image/png",
                sha256=hashlib.sha256(data).hexdigest(),
                data=data,
            ),
        ),
        timeout_seconds=30,
        max_output_tokens=100,
    )


def test_production_provider_exports_contain_only_live_neutral_boundary() -> None:
    providers = importlib.import_module("buduunkhad.ai.providers")
    assert not hasattr(providers, "FakeAIProvider")
    assert not hasattr(providers, "ReplayAIProvider")
    assert not (Path("src/buduunkhad/ai/providers") / "fake.py").exists()
    assert not (Path("src/buduunkhad/ai/providers") / "replay.py").exists()


def test_provider_sdks_are_not_imported_by_application_imports() -> None:
    assert "openai" not in sys.modules
    assert "anthropic" not in sys.modules


@pytest.mark.parametrize(
    ("provider", "environment_name"),
    [
        (OpenAIProvider(), "OPENAI_API_KEY"),
        (AnthropicProvider(), "ANTHROPIC_API_KEY"),
    ],
)
def test_missing_key_is_reported_only_when_execution_is_requested(
    provider: OpenAIProvider | AnthropicProvider,
    environment_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(environment_name, raising=False)
    with pytest.raises(ProviderCredentialError, match="optional ai execute command"):
        provider.execute(_call(provider.name))


@pytest.mark.parametrize(
    ("provider", "environment_name", "module_name"),
    [
        (OpenAIProvider(), "OPENAI_API_KEY", "openai"),
        (AnthropicProvider(), "ANTHROPIC_API_KEY", "anthropic"),
    ],
)
def test_missing_optional_dependency_has_a_domain_error(
    provider: OpenAIProvider | AnthropicProvider,
    environment_name: str,
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(environment_name, "synthetic-key-not-a-secret")
    original = importlib.import_module

    def import_module(name: str, package: str | None = None) -> object:
        if name == module_name:
            raise ImportError(name)
        return original(name, package)

    monkeypatch.setattr(importlib, "import_module", import_module)
    with pytest.raises(ProviderDependencyError, match="optional"):
        provider.execute(_call(provider.name))


def test_openai_injected_client_executes_without_sdk_or_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    responses = OpenAIResponsesDouble()
    result = OpenAIProvider(client=provider_client("responses", responses)).execute(_call("openai"))
    assert result.provider == "openai"
    assert result.response_id == "openai-response-1"
    assert result.payload.to_python() == {"title": "Synthetic"}
    assert result.usage == AIUsage(input_tokens=7, output_tokens=3, requests=1)
    assert responses.arguments is not None
    assert responses.arguments["model"] == "synthetic-model"
    request_input = responses.arguments["input"]
    assert isinstance(request_input, list)
    content = request_input[0]["content"]
    assert any("tile-1" in item.get("text", "") for item in content)


def test_anthropic_injected_client_executes_without_sdk_or_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    messages = AnthropicMessagesDouble()
    result = AnthropicProvider(client=provider_client("messages", messages)).execute(
        _call("anthropic")
    )
    assert result.provider == "anthropic"
    assert result.response_id == "anthropic-response-1"
    assert result.payload.to_python() == {"title": "Synthetic"}
    assert result.usage == AIUsage(input_tokens=8, output_tokens=4, requests=1)
    assert messages.arguments is not None
    assert messages.arguments["model"] == "synthetic-model"
    request_messages = messages.arguments["messages"]
    assert isinstance(request_messages, list)
    content = request_messages[0]["content"]
    assert any("tile-1" in item.get("text", "") for item in content)


@pytest.mark.parametrize("provider", [OpenAIProvider(), AnthropicProvider()])
def test_provider_rejects_a_package_for_the_other_provider(
    provider: OpenAIProvider | AnthropicProvider,
) -> None:
    other = "anthropic" if provider.name == "openai" else "openai"
    with pytest.raises(AIProviderError, match="does not match"):
        provider.execute(_call(other))


def test_provider_image_hash_is_calculated_from_actual_bytes() -> None:
    with pytest.raises(ValueError, match="approved SHA-256"):
        ProviderImage(
            tile_id="tile-1",
            media_type="image/png",
            sha256="0" * 64,
            data=b"changed",
        )


def test_provider_structured_json_rejects_duplicate_keys() -> None:
    with pytest.raises(ProviderResponseError, match="unique-key JSON"):
        decode_provider_json('{"title":"one","nested":{"x":1,"x":2}}')


@pytest.mark.parametrize(
    "value",
    [
        AliasedApproval(state=ReviewStatus.GEOLOGIST_APPROVED),
        ExcludedApproval(review_status=ReviewStatus.REJECTED),
        NestedApproval(nested=ExcludedApproval(review_status=ReviewStatus.SUPERSEDED)),
        ComputedApproval(title="safe"),
        PrivateApproval(title="safe"),
        RootApproval({"review_status": "GEOLOGIST_APPROVED"}),
        CustomSerializedApproval(review_status=ReviewStatus.GEOLOGIST_APPROVED),
        DataclassApproval(payload=ApprovalDataclass(reviewer_name="human")),
        CanonicalApproval(
            payload=CanonicalJSONValue.from_value({"nested": {"review_status": "SUPERSEDED"}})
        ),
        NamedApproval(
            payload=NamedJSONValue(
                name="approval",
                value=CanonicalJSONValue.from_value("GEOLOGIST_APPROVED"),
            )
        ),
        {"safe": [{"authorization": "human"}]},
        {"GEOLOGIST_APPROVED": "hidden-in-a-key"},
        ("AI_DRAFT", "REJECTED"),
    ],
)
def test_provider_output_cannot_hide_human_review_or_supersession(value: object) -> None:
    with pytest.raises(AIProviderError):
        prohibit_provider_approval(value)


def test_provider_output_contract_accepts_exact_standard_round_trip() -> None:
    output = SampleOutput(title="Synthetic")
    assert validate_provider_output_contract(output, SampleOutput) == output


@pytest.mark.parametrize(
    "output",
    [
        CustomSerializedOutput(title="Synthetic"),
        ComputedOutput(title="Synthetic"),
        ExcludedOutput(title="Synthetic", hidden="semantic"),
    ],
)
def test_ambiguous_provider_output_serialization_fails_closed(output: FrozenModel) -> None:
    with pytest.raises(AIProviderError):
        validate_provider_output_contract(output, type(output))


def test_provider_response_time_is_timezone_aware() -> None:
    responses = OpenAIResponsesDouble(
        response_id="response-1",
        input_tokens=1,
        output_tokens=1,
    )
    result = OpenAIProvider(client=provider_client("responses", responses)).execute(_call("openai"))
    assert result.created_at.tzinfo is UTC


def test_injected_provider_failure_does_not_expose_request_or_environment_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = "synthetic-private-provider-key"
    monkeypatch.setenv("OPENAI_API_KEY", key)

    with pytest.raises(AIProviderError) as caught:
        OpenAIProvider(client=provider_client("responses", FailingResponsesDouble(key))).execute(
            _call("openai")
        )
    assert key not in str(caught.value)
