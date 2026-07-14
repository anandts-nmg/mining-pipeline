"""Strict, deterministic file-backed replay provider."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal, TypeVar, cast

from pydantic import Field, ValidationError, field_validator, model_validator

from buduunkhad.ai.contracts import (
    AIJobStatus,
    AIRequest,
    AIResponse,
    AIResponseStatus,
    AIUsage,
    CanonicalJSONValue,
    FailureDetail,
    FrozenModel,
    IncompleteDetail,
    NonEmptyStr,
    Sha256,
    require_aware_datetime,
)
from buduunkhad.ai.fingerprint import request_fingerprint, schema_identity_for_model
from buduunkhad.ai.providers.base import (
    AIProviderError,
    ProviderExecutionResolver,
    prohibit_provider_approval,
    validate_provider_execution,
    validate_provider_output_contract,
    validation_error_details,
)

OutputT = TypeVar("OutputT", bound=FrozenModel)


class ReplayFixtureError(AIProviderError):
    pass


class ReplayFixtureMissingError(ReplayFixtureError):
    pass


class ReplayFixtureCorruptError(ReplayFixtureError):
    pass


class ReplayFixtureIncompatibleError(ReplayFixtureError):
    pass


class ReplayFixtureInternallyInconsistentError(ReplayFixtureError):
    pass


class ReplayFixture(FrozenModel):
    fixture_version: Literal["1.0.0"]
    request_fingerprint: Sha256
    schema_sha256: Sha256
    status: AIResponseStatus
    provider_response_id: NonEmptyStr
    created_at: datetime
    usage: AIUsage
    output: CanonicalJSONValue | None = None
    refusal_reason: NonEmptyStr | None = None
    incomplete: IncompleteDetail | None = None
    validation_errors: tuple[NonEmptyStr, ...] = Field(default_factory=tuple)
    failure: FailureDetail | None = None

    @field_validator("output", mode="before")
    @classmethod
    def _freeze_output(cls, value: object) -> object:
        if value is None:
            return value
        return CanonicalJSONValue.from_input(value)

    @field_validator("created_at")
    @classmethod
    def _aware_created_at(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")

    @model_validator(mode="after")
    def _fixture_consistency(self) -> ReplayFixture:
        if self.status is AIResponseStatus.SUCCESS:
            if self.output is None:
                raise ValueError("successful replay fixture requires output")
            if any((self.refusal_reason, self.incomplete, self.validation_errors, self.failure)):
                raise ValueError("successful replay fixture cannot contain error details")
        if self.status is AIResponseStatus.REFUSED and not self.refusal_reason:
            raise ValueError("refused replay fixture requires refusal_reason")
        if self.status is AIResponseStatus.INCOMPLETE and self.incomplete is None:
            raise ValueError("incomplete replay fixture requires incomplete details")
        if self.status is AIResponseStatus.INVALID_OUTPUT and (
            self.output is None or not self.validation_errors
        ):
            raise ValueError("invalid replay fixture requires output and validation errors")
        if (
            self.status
            not in {
                AIResponseStatus.SUCCESS,
                AIResponseStatus.INVALID_OUTPUT,
            }
            and self.output is not None
        ):
            raise ValueError("only success or invalid-output fixtures may contain output")
        if self.status is AIResponseStatus.FAILURE and self.failure is None:
            raise ValueError("failure replay fixture requires failure details")
        if self.status is not AIResponseStatus.REFUSED and self.refusal_reason is not None:
            raise ValueError("refusal_reason is only valid for REFUSED")
        if self.status is not AIResponseStatus.INCOMPLETE and self.incomplete is not None:
            raise ValueError("incomplete details are only valid for INCOMPLETE")
        if self.status is not AIResponseStatus.INVALID_OUTPUT and self.validation_errors:
            raise ValueError("validation_errors are only valid for INVALID_OUTPUT")
        if self.status is not AIResponseStatus.FAILURE and self.failure is not None:
            raise ValueError("failure details are only valid for FAILURE")
        return self


class ReplayAIProvider:
    """Offline provider loading ``<request fingerprint>.json`` fixtures."""

    def __init__(self, fixture_directory: Path) -> None:
        self.fixture_directory = Path(fixture_directory)

    @property
    def name(self) -> str:
        return "replay"

    def generate(
        self,
        request: AIRequest,
        output_model: type[OutputT],
        *,
        resolver: ProviderExecutionResolver,
    ) -> AIResponse[OutputT]:
        fingerprint = request_fingerprint(request)
        fixture = self._load_fixture(fingerprint)
        job = validate_provider_execution(
            request,
            resolver=resolver,
            provider=self.name,
            response_created_at=fixture.created_at,
        )
        if (
            job.provider_response_id is not None
            and job.provider_response_id != fixture.provider_response_id
        ):
            raise ReplayFixtureIncompatibleError(
                "replay response identity differs from authoritative job"
            )
        expected_job_status = {
            AIResponseStatus.SUCCESS: AIJobStatus.SUCCEEDED,
            AIResponseStatus.REFUSED: AIJobStatus.REFUSED,
            AIResponseStatus.INCOMPLETE: AIJobStatus.INCOMPLETE,
            AIResponseStatus.INVALID_OUTPUT: AIJobStatus.FAILED,
            AIResponseStatus.FAILURE: AIJobStatus.FAILED,
        }[fixture.status]
        if job.status is not expected_job_status:
            raise ReplayFixtureIncompatibleError(
                "replay response state differs from authoritative job"
            )
        if job.usage != fixture.usage:
            raise ReplayFixtureIncompatibleError(
                "replay response usage differs from authoritative job"
            )
        current_schema = schema_identity_for_model(
            output_model,
            schema_id=request.output_schema.schema_id,
            version=request.output_schema.version,
        )
        if current_schema != request.output_schema:
            raise ReplayFixtureIncompatibleError(
                "request schema identity does not match the current Pydantic schema"
            )
        if fixture.schema_sha256 != request.output_schema.sha256:
            raise ReplayFixtureIncompatibleError(
                "replay fixture schema hash does not match the current Pydantic schema"
            )
        if fixture.request_fingerprint != fingerprint:
            raise ReplayFixtureIncompatibleError("replay fixture request fingerprint mismatch")

        prohibit_provider_approval(fixture)
        output: OutputT | None = None
        raw = fixture.output.to_python() if fixture.output is not None else None
        if raw is not None:
            prohibit_provider_approval(raw)
        if fixture.status is AIResponseStatus.SUCCESS:
            try:
                output = output_model.model_validate(raw)
            except ValidationError as exc:
                raise ReplayFixtureIncompatibleError(
                    f"replay success output is incompatible with the current schema: {exc}"
                ) from exc
            prohibit_provider_approval(output)
            output = validate_provider_output_contract(output, output_model)
        elif fixture.status is AIResponseStatus.INVALID_OUTPUT:
            current_errors = validation_error_details(output_model, raw)
            if not current_errors:
                raise ReplayFixtureInternallyInconsistentError(
                    "replay payload is valid but fixture labels it INVALID_OUTPUT"
                )
            if current_errors != fixture.validation_errors:
                raise ReplayFixtureInternallyInconsistentError(
                    "replay validation details do not match current schema validation"
                )

        return _validated_response(
            output_model,
            {
                "request_id": request.request_id,
                "job_id": request.job_id,
                "run_id": request.run_id,
                "phase_id": request.phase_id,
                "task_type": request.task_type,
                "request_fingerprint": fingerprint,
                "output_schema": request.output_schema,
                "status": fixture.status,
                "provider": self.name,
                "model": request.provider.model,
                "provider_response_id": fixture.provider_response_id,
                "created_at": fixture.created_at,
                "usage": fixture.usage,
                "output": output,
                "refusal_reason": fixture.refusal_reason,
                "incomplete": fixture.incomplete,
                "validation_errors": fixture.validation_errors,
                "failure": fixture.failure,
                "raw_output": raw if fixture.status is AIResponseStatus.INVALID_OUTPUT else None,
            },
        )

    def _load_fixture(self, fingerprint: str) -> ReplayFixture:
        path = self.fixture_directory / f"{fingerprint}.json"
        if not path.is_file():
            raise ReplayFixtureMissingError(f"replay fixture not found: {path.name}")
        try:
            text = path.read_text(encoding="utf-8")
            raw: object = json.loads(text, object_pairs_hook=_unique_json_object)
        except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateJSONKeyError) as exc:
            raise ReplayFixtureCorruptError(
                f"cannot read replay fixture {path.name}: {exc}"
            ) from exc
        try:
            return ReplayFixture.model_validate(raw)
        except ValidationError as exc:
            raise ReplayFixtureInternallyInconsistentError(
                f"inconsistent replay fixture {path.name}: {exc}"
            ) from exc


def _validated_response(
    output_model: type[OutputT], values: dict[str, object]
) -> AIResponse[OutputT]:
    # Pydantic intentionally supports runtime generic specialization; type checkers do not.
    response_type = AIResponse[output_model]  # type: ignore[valid-type]
    return cast(AIResponse[OutputT], response_type.model_validate(values))


class _DuplicateJSONKeyError(ValueError):
    pass


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
