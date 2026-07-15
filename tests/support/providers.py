"""Minimal deterministic provider double used only by contract unit tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import TypeVar, cast

from pydantic import ValidationError

from buduunkhad.ai.contracts import (
    AIRequest,
    AIResponse,
    AIResponseStatus,
    AIUsage,
    FrozenModel,
)
from buduunkhad.ai.fingerprint import request_fingerprint, schema_identity_for_model, sha256_value
from buduunkhad.ai.providers.base import (
    AIProviderError,
    ProviderCall,
    ProviderExecutionResolver,
    ProviderExecutionResult,
    prohibit_provider_approval,
    validate_provider_execution,
    validate_provider_output_contract,
)

OutputT = TypeVar("OutputT", bound=FrozenModel)


class OpenAIResponsesDouble:
    def __init__(
        self,
        *,
        response_id: str = "openai-response-1",
        input_tokens: int = 7,
        output_tokens: int = 3,
    ) -> None:
        self.arguments: dict[str, object] | None = None
        self.response_id = response_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def create(self, **kwargs: object) -> object:
        self.arguments = kwargs
        return SimpleNamespace(
            id=self.response_id,
            output_text=json.dumps({"title": "Synthetic"}),
            usage=SimpleNamespace(
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
            ),
        )


class AnthropicMessagesDouble:
    def __init__(self) -> None:
        self.arguments: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        self.arguments = kwargs
        return SimpleNamespace(
            id="anthropic-response-1",
            content=[SimpleNamespace(text=json.dumps({"title": "Synthetic"}))],
            usage=SimpleNamespace(input_tokens=8, output_tokens=4),
        )


class FailingResponsesDouble:
    def __init__(self, message: str) -> None:
        self.message = message

    def create(self, **kwargs: object) -> object:
        del kwargs
        raise RuntimeError(self.message)


def provider_client(endpoint_name: str, endpoint: object) -> object:
    return SimpleNamespace(**{endpoint_name: endpoint})


class CapturingLiveProvider:
    """Capture one provider-neutral call and return a supplied canonical payload."""

    name = "openai"

    def __init__(self, payload: object, *, created_at: datetime) -> None:
        self.payload = payload
        self.created_at = created_at
        self.call: ProviderCall | None = None

    def execute(self, call: ProviderCall) -> ProviderExecutionResult:
        self.call = call
        return ProviderExecutionResult.from_payload(
            provider="openai",
            model=call.model,
            response_id="captured-test-response",
            created_at=self.created_at,
            payload=self.payload,
            usage=AIUsage(input_tokens=100, output_tokens=50, requests=1),
        )


class DeterministicTestProvider:
    """Return one schema-validated payload without network or production exports."""

    def __init__(self, payload: object, *, created_at: datetime | None = None) -> None:
        self.payload = payload
        self.created_at = created_at

    @property
    def name(self) -> str:
        return "test-double"

    def generate(
        self,
        request: AIRequest,
        output_model: type[OutputT],
        *,
        resolver: ProviderExecutionResolver,
    ) -> AIResponse[OutputT]:
        created_at = self.created_at or datetime.now(UTC)
        job = validate_provider_execution(
            request,
            resolver=resolver,
            provider=request.provider.provider,
            response_created_at=created_at,
        )
        expected_schema = schema_identity_for_model(
            output_model,
            schema_id=request.output_schema.schema_id,
            version=request.output_schema.version,
        )
        if expected_schema != request.output_schema:
            raise AIProviderError("test response schema differs from request")
        try:
            output = output_model.model_validate(self.payload)
        except ValidationError as exc:
            raise AIProviderError("test payload is incompatible with output schema") from exc
        prohibit_provider_approval(output)
        validated = validate_provider_output_contract(output, output_model)
        response_id = test_response_id(request)
        if job.provider_response_id != response_id:
            raise AIProviderError("test response identity differs from authoritative job")
        response_type = AIResponse[output_model]  # type: ignore[valid-type]
        return cast(
            AIResponse[OutputT],
            response_type.model_validate(
                {
                    "request_id": request.request_id,
                    "job_id": request.job_id,
                    "run_id": request.run_id,
                    "phase_id": request.phase_id,
                    "task_type": request.task_type,
                    "request_fingerprint": request_fingerprint(request),
                    "output_schema": request.output_schema,
                    "status": AIResponseStatus.SUCCESS,
                    "provider": request.provider.provider,
                    "model": request.provider.model,
                    "provider_response_id": response_id,
                    "created_at": created_at,
                    "usage": AIUsage(),
                    "output": validated,
                }
            ),
        )


def test_response_id(request: AIRequest) -> str:
    return (
        "test-"
        + sha256_value({"request": request_fingerprint(request), "job": request.job_id})[:24]
    )
