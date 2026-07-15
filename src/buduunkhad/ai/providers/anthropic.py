"""Optional Anthropic vision adapter with lazy SDK and credential loading."""

from __future__ import annotations

import base64
import importlib
import os
from datetime import UTC, datetime
from typing import Protocol, cast

from buduunkhad.ai.contracts import AIUsage
from buduunkhad.ai.providers.base import (
    AIProviderError,
    ProviderCall,
    ProviderCredentialError,
    ProviderDependencyError,
    ProviderExecutionResult,
    ProviderResponseError,
    decode_provider_json,
)


class AnthropicProvider:
    """Execute an approved request through the optional Anthropic Messages client."""

    def __init__(self, *, client: object | None = None) -> None:
        self._injected_client = client

    @property
    def name(self) -> str:
        return "anthropic"

    def execute(self, call: ProviderCall) -> ProviderExecutionResult:
        if call.provider != self.name:
            raise AIProviderError("prepared request provider does not match Anthropic")
        client = cast(
            _AnthropicClient,
            self._injected_client
            if self._injected_client is not None
            else _create_client(call.timeout_seconds),
        )
        content: list[dict[str, object]] = [{"type": "text", "text": call.user_prompt}]
        for image in call.images:
            content.append(
                {
                    "type": "text",
                    "text": f"Approved tile {image.tile_id}; image SHA-256 {image.sha256}",
                }
            )
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image.media_type,
                        "data": base64.b64encode(image.data).decode("ascii"),
                    },
                }
            )
        execution_failed = False
        try:
            response = client.messages.create(
                model=call.model,
                max_tokens=call.max_output_tokens,
                system=call.system_prompt,
                messages=[{"role": "user", "content": content}],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": call.output_schema.to_python(),
                    }
                },
                timeout=call.timeout_seconds,
            )
        except Exception:  # SDK boundary: deliberately discard potentially sensitive details.
            execution_failed = True
        if execution_failed:
            raise AIProviderError("Anthropic execution failed")
        response_id = getattr(response, "id", None)
        if not isinstance(response_id, str) or not response_id.strip():
            raise ProviderResponseError("Anthropic response did not contain a response ID")
        output_text = _output_text(response)
        return ProviderExecutionResult.from_payload(
            provider="anthropic",
            model=call.model,
            response_id=response_id,
            created_at=datetime.now(UTC),
            payload=decode_provider_json(output_text),
            usage=_usage(response),
        )


def _create_client(timeout_seconds: float) -> object:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ProviderCredentialError(
            "ANTHROPIC_API_KEY is required only for the optional ai execute command"
        )
    try:
        module = importlib.import_module("anthropic")
        client_class = module.Anthropic
    except (ImportError, AttributeError) as exc:
        raise ProviderDependencyError(
            "Anthropic execution requires the optional 'anthropic' project extra"
        ) from exc
    construction_failed = False
    try:
        return client_class(api_key=api_key, timeout=timeout_seconds)
    except Exception:
        construction_failed = True
    if construction_failed:
        raise AIProviderError("Anthropic client construction failed")
    raise AssertionError("unreachable")


def _output_text(response: object) -> str:
    content = getattr(response, "content", None)
    if not isinstance(content, list):
        raise ProviderResponseError("Anthropic response content is malformed")
    texts: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            texts.append(text)
    combined = "".join(texts).strip()
    if not combined:
        raise ProviderResponseError("Anthropic response did not contain structured output text")
    return combined


def _usage(response: object) -> AIUsage:
    value = getattr(response, "usage", None)
    input_tokens = getattr(value, "input_tokens", 0) if value is not None else 0
    output_tokens = getattr(value, "output_tokens", 0) if value is not None else 0
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        raise ProviderResponseError("Anthropic response usage is malformed")
    return AIUsage(input_tokens=input_tokens, output_tokens=output_tokens, requests=1)


class _MessagesEndpoint(Protocol):
    def create(self, **kwargs: object) -> object: ...


class _AnthropicClient(Protocol):
    messages: _MessagesEndpoint
