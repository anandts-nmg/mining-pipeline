"""Deterministic in-memory AI provider for unit tests and dry runs."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TypeVar, cast

from buduunkhad.ai.contracts import (
    AIJobStatus,
    AIRequest,
    AIResponse,
    AIResponseStatus,
    FailureDetail,
    FrozenModel,
    IncompleteDetail,
)
from buduunkhad.ai.fingerprint import request_fingerprint, schema_identity_for_model, sha256_value
from buduunkhad.ai.providers.base import (
    AIProviderError,
    ProviderExecutionResolver,
    prohibit_provider_approval,
    validate_provider_execution,
    validate_provider_output_contract,
    validation_error_details,
)

OutputT = TypeVar("OutputT", bound=FrozenModel)


class FakeMode(StrEnum):
    SUCCESS = "success"
    REFUSED = "refused"
    REFUSAL = "refused"
    INCOMPLETE = "incomplete"
    INVALID_OUTPUT = "invalid_output"
    FAILURE = "failure"


class FakeAIProvider:
    """Offline provider whose mode and payload are explicit test inputs."""

    def __init__(
        self,
        *,
        mode: FakeMode = FakeMode.SUCCESS,
        payload: object = None,
        reason: str = "fake provider outcome",
        created_at: datetime | None = None,
    ) -> None:
        self.mode = mode
        self.payload = payload
        self.reason = reason
        self.created_at = created_at

    @property
    def name(self) -> str:
        return "fake"

    def generate(
        self,
        request: AIRequest,
        output_model: type[OutputT],
        *,
        resolver: ProviderExecutionResolver,
    ) -> AIResponse[OutputT]:
        resolved_job = resolver.resolve_job(request.job_id)
        created_at = self.created_at or resolved_job.started_at
        if created_at is None:
            raise AIProviderError("fake provider requires a started authoritative job")
        job = validate_provider_execution(
            request,
            resolver=resolver,
            provider=self.name,
            response_created_at=created_at,
        )
        current_schema = schema_identity_for_model(
            output_model,
            schema_id=request.output_schema.schema_id,
            version=request.output_schema.version,
        )
        if current_schema != request.output_schema:
            raise AIProviderError("request schema identity does not match the current output model")
        prohibit_provider_approval(self.payload)
        fingerprint = request_fingerprint(request)
        response_id = fake_response_id(request)
        if job.provider_response_id is not None and job.provider_response_id != response_id:
            raise AIProviderError("fake response identity differs from authoritative job")
        expected_job_status = {
            FakeMode.SUCCESS: AIJobStatus.SUCCEEDED,
            FakeMode.REFUSED: AIJobStatus.REFUSED,
            FakeMode.INCOMPLETE: AIJobStatus.INCOMPLETE,
            FakeMode.INVALID_OUTPUT: AIJobStatus.FAILED,
            FakeMode.FAILURE: AIJobStatus.FAILED,
        }[self.mode]
        if job.status is not expected_job_status:
            raise AIProviderError("fake response state differs from authoritative job")
        common = {
            "request_id": request.request_id,
            "job_id": request.job_id,
            "run_id": request.run_id,
            "phase_id": request.phase_id,
            "task_type": request.task_type,
            "request_fingerprint": fingerprint,
            "output_schema": request.output_schema,
            "provider": self.name,
            "model": request.provider.model,
            "provider_response_id": response_id,
            "created_at": created_at,
            "usage": job.usage,
        }
        if self.mode is FakeMode.REFUSED:
            return _validated_response(
                output_model,
                {
                    **common,
                    "status": AIResponseStatus.REFUSED,
                    "refusal_reason": self.reason,
                },
            )
        if self.mode is FakeMode.INCOMPLETE:
            return _validated_response(
                output_model,
                {
                    **common,
                    "status": AIResponseStatus.INCOMPLETE,
                    "incomplete": IncompleteDetail(reason=self.reason),
                },
            )
        if self.mode is FakeMode.FAILURE:
            return _validated_response(
                output_model,
                {
                    **common,
                    "status": AIResponseStatus.FAILURE,
                    "failure": FailureDetail(
                        code="FAKE_FAILURE", message=self.reason, retryable=False
                    ),
                },
            )
        if self.mode is FakeMode.INVALID_OUTPUT:
            errors = validation_error_details(output_model, self.payload)
            if not errors:
                raise AIProviderError("fake invalid-output payload unexpectedly validates")
            return _validated_response(
                output_model,
                {
                    **common,
                    "status": AIResponseStatus.INVALID_OUTPUT,
                    "validation_errors": errors,
                    "raw_output": self.payload,
                },
            )
        try:
            output = output_model.model_validate(self.payload)
        except ValueError as exc:
            raise AIProviderError(f"fake success payload is incompatible: {exc}") from exc
        prohibit_provider_approval(output)
        output = validate_provider_output_contract(output, output_model)
        return _validated_response(
            output_model,
            {
                **common,
                "status": AIResponseStatus.SUCCESS,
                "output": output,
            },
        )


def fake_response_id(request: AIRequest) -> str:
    """Return the deterministic identity a fake response will use for a request."""
    fingerprint = request_fingerprint(request)
    response_identity = sha256_value((fingerprint, request.request_id, request.job_id))
    return f"fake-{response_identity[:16]}"


def _validated_response(
    output_model: type[OutputT], values: dict[str, object]
) -> AIResponse[OutputT]:
    # Pydantic intentionally supports runtime generic specialization; type checkers do not.
    response_type = AIResponse[output_model]  # type: ignore[valid-type]
    return cast(AIResponse[OutputT], response_type.model_validate(values))
