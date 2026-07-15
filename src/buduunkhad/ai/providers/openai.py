"""Optional OpenAI vision adapter with lazy SDK and credential loading."""

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


class OpenAIProvider:
    """Execute an approved request through the optional OpenAI Responses client.

    ``client`` is intentionally injectable so unit tests exercise the complete
    serialization boundary without constructing an SDK client or opening a socket.
    """

    def __init__(self, *, client: object | None = None) -> None:
        self._injected_client = client

    @property
    def name(self) -> str:
        return "openai"

    def execute(self, call: ProviderCall) -> ProviderExecutionResult:
        if call.provider != self.name:
            raise AIProviderError("prepared request provider does not match OpenAI")
        client = cast(
            _OpenAIClient,
            self._injected_client
            if self._injected_client is not None
            else _create_client(call.timeout_seconds),
        )
        content: list[dict[str, object]] = [{"type": "input_text", "text": call.user_prompt}]
        for image in call.images:
            encoded = base64.b64encode(image.data).decode("ascii")
            content.append(
                {
                    "type": "input_text",
                    "text": f"Approved tile {image.tile_id}; image SHA-256 {image.sha256}",
                }
            )
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{image.media_type};base64,{encoded}",
                }
            )
        execution_failed = False
        try:
            response = client.responses.create(
                model=call.model,
                instructions=call.system_prompt,
                input=[{"role": "user", "content": content}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "buduunkhad_geospatial_output",
                        "schema": call.output_schema.to_python(),
                        "strict": True,
                    }
                },
                max_output_tokens=call.max_output_tokens,
                timeout=call.timeout_seconds,
            )
        except Exception:  # SDK boundary: deliberately discard potentially sensitive details.
            execution_failed = True
        if execution_failed:
            raise AIProviderError("OpenAI execution failed")
        output_text = getattr(response, "output_text", None)
        response_id = getattr(response, "id", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise ProviderResponseError("OpenAI response did not contain structured output text")
        if not isinstance(response_id, str) or not response_id.strip():
            raise ProviderResponseError("OpenAI response did not contain a response ID")
        usage = _usage(response)
        return ProviderExecutionResult.from_payload(
            provider="openai",
            model=call.model,
            response_id=response_id,
            created_at=datetime.now(UTC),
            payload=decode_provider_json(output_text),
            usage=usage,
        )


def _create_client(timeout_seconds: float) -> object:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ProviderCredentialError(
            "OPENAI_API_KEY is required only for the optional ai execute command"
        )
    try:
        module = importlib.import_module("openai")
        client_class = module.OpenAI
    except (ImportError, AttributeError) as exc:
        raise ProviderDependencyError(
            "OpenAI execution requires the optional 'openai' project extra"
        ) from exc
    construction_failed = False
    try:
        return client_class(api_key=api_key, timeout=timeout_seconds)
    except Exception:
        construction_failed = True
    if construction_failed:
        raise AIProviderError("OpenAI client construction failed")
    raise AssertionError("unreachable")


def _usage(response: object) -> AIUsage:
    value = getattr(response, "usage", None)
    input_tokens = getattr(value, "input_tokens", 0) if value is not None else 0
    output_tokens = getattr(value, "output_tokens", 0) if value is not None else 0
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        raise ProviderResponseError("OpenAI response usage is malformed")
    return AIUsage(input_tokens=input_tokens, output_tokens=output_tokens, requests=1)


class _ResponsesEndpoint(Protocol):
    def create(self, **kwargs: object) -> object: ...


class _OpenAIClient(Protocol):
    responses: _ResponsesEndpoint
