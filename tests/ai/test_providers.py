from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    RootModel,
    computed_field,
    field_validator,
    model_serializer,
)

from buduunkhad.ai.contracts import (
    AIJob,
    AIJobStatus,
    AIRequest,
    AIResponseStatus,
    AIUsage,
    CanonicalJSONValue,
    FailureDetail,
    FrozenModel,
    IncompleteDetail,
    NamedJSONValue,
    PageLocator,
    PromptIdentity,
    ProviderConfiguration,
    ReviewStatus,
    SchemaIdentity,
    SourceReference,
    TaskType,
)
from buduunkhad.ai.fingerprint import (
    canonical_json_text,
    request_fingerprint,
    schema_identity_for_model,
    sha256_value,
)
from buduunkhad.ai.providers import (
    AIProviderError,
    FakeAIProvider,
    FakeMode,
    ReplayAIProvider,
    ReplayFixtureCorruptError,
    ReplayFixtureIncompatibleError,
    ReplayFixtureInternallyInconsistentError,
    ReplayFixtureMissingError,
    fake_response_id,
)
from buduunkhad.ai.providers.base import validation_error_details

SHA_A = "a" * 64
NOW = datetime(2026, 1, 1, tzinfo=UTC)


class SampleOutput(FrozenModel):
    title: str = Field(min_length=1)


class AliasedApproval(FrozenModel):
    review_status: ReviewStatus = Field(alias="state")


class ExcludedApproval(FrozenModel):
    review_status: ReviewStatus = Field(exclude=True)


class NestedApproval(FrozenModel):
    nested: ExcludedApproval


class ExtraApprovalState(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str


class ExtraApproval(FrozenModel):
    nested: ExtraApprovalState


class CustomSerializedApproval(FrozenModel):
    review_status: ReviewStatus

    @model_serializer
    def _hide_review_state(self) -> dict[str, str]:
        return {"apparently_safe": "value"}


class ComputedApproval(FrozenModel):
    title: str

    @computed_field
    @property
    def reviewer_id(self) -> str:
        return "human-reviewer"


class PrivateApproval(FrozenModel):
    title: str
    _review_status: ReviewStatus = PrivateAttr(default=ReviewStatus.GEOLOGIST_APPROVED)


class RootApproval(RootModel[str]):
    pass


class MappingKeyApproval(FrozenModel):
    payload: dict[str, str]


class CollectionApproval(FrozenModel):
    payload: tuple[str, ...]


class CanonicalApproval(FrozenModel):
    payload: CanonicalJSONValue


class NamedCanonicalApproval(FrozenModel):
    payload: NamedJSONValue


@dataclass(frozen=True)
class ApprovalDataclass:
    reviewer_id: str


class DataclassApproval(FrozenModel):
    payload: ApprovalDataclass


class _UnsupportedContainer:
    def __init__(self, value: str) -> None:
        self.value = value


class UnsupportedContainerApproval(FrozenModel):
    payload: object

    @field_validator("payload", mode="before")
    @classmethod
    def _custom_container(cls, value: object) -> object:
        if isinstance(value, dict):
            return _UnsupportedContainer(str(value.get("value", "safe")))
        return value


class SafeCustomSerializer(FrozenModel):
    title: str

    @model_serializer
    def _custom(self) -> dict[str, str]:
        return {"title": self.title}


class SafeComputedField(FrozenModel):
    title: str

    @computed_field
    @property
    def title_length(self) -> int:
        return len(self.title)


class SafeExcludedField(FrozenModel):
    title: str
    hidden_semantic_value: str = Field(exclude=True)


class NestedSafeExcludedField(FrozenModel):
    nested: SafeExcludedField


def _request(provider: str, output_model: type[FrozenModel] = SampleOutput) -> AIRequest:
    schema = schema_identity_for_model(
        output_model,
        schema_id=f"fixture.{output_model.__name__.lower()}",
        version="1.0.0",
    )
    assert isinstance(schema, SchemaIdentity)
    return AIRequest.model_validate(
        {
            "request_id": "request-1",
            "job_id": "job-1",
            "run_id": "run-1",
            "phase_id": "phase-00",
            "task_type": TaskType.DOCUMENT_EXTRACTION,
            "created_at": NOW,
            "source_references": (
                SourceReference(
                    asset_id="synthetic",
                    sha256=SHA_A,
                    locators=(PageLocator(page_number=1),),
                ),
            ),
            "prompt": PromptIdentity(prompt_id="fixture", version="1.0.0", sha256=SHA_A),
            "output_schema": schema,
            "provider": ProviderConfiguration.model_validate(
                {"provider": provider, "model": "offline", "parameters": {}}
            ),
            "interpretation_parameters": {},
        }
    )


class _ExecutionResolver:
    def __init__(self, request: AIRequest, job: AIJob) -> None:
        self.request = request
        self.job = job

    def resolve_request(self, request_id: str) -> AIRequest:
        if request_id != self.request.request_id:
            raise LookupError(request_id)
        return self.request

    def resolve_job(self, job_id: str) -> AIJob:
        if job_id != self.job.job_id:
            raise LookupError(job_id)
        return self.job


_RESPONSE_JOB_STATUS = {
    AIResponseStatus.SUCCESS: AIJobStatus.SUCCEEDED,
    AIResponseStatus.REFUSED: AIJobStatus.REFUSED,
    AIResponseStatus.INCOMPLETE: AIJobStatus.INCOMPLETE,
    AIResponseStatus.INVALID_OUTPUT: AIJobStatus.FAILED,
    AIResponseStatus.FAILURE: AIJobStatus.FAILED,
}


def _execution_resolver(
    request: AIRequest,
    *,
    response_id: str,
    response_status: AIResponseStatus,
    usage: AIUsage | None = None,
) -> _ExecutionResolver:
    job = AIJob(
        job_id=request.job_id,
        run_id=request.run_id,
        phase_id=request.phase_id,
        task_type=request.task_type,
        request_id=request.request_id,
        request_fingerprint=request_fingerprint(request),
        output_schema=request.output_schema,
        provider=request.provider.provider,
        model=request.provider.model,
        provider_parameters_sha256=sha256_value(request.provider.parameters),
        status=_RESPONSE_JOB_STATUS[response_status],
        provider_response_id=response_id,
        created_at=NOW,
        started_at=NOW,
        completed_at=NOW,
        usage=usage or AIUsage(),
    )
    return _ExecutionResolver(request, job)


def _fake_generate(
    provider: FakeAIProvider,
    request: AIRequest,
    output_model: type[FrozenModel],
):
    status = {
        FakeMode.SUCCESS: AIResponseStatus.SUCCESS,
        FakeMode.REFUSED: AIResponseStatus.REFUSED,
        FakeMode.INCOMPLETE: AIResponseStatus.INCOMPLETE,
        FakeMode.INVALID_OUTPUT: AIResponseStatus.INVALID_OUTPUT,
        FakeMode.FAILURE: AIResponseStatus.FAILURE,
    }[provider.mode]
    resolver = _execution_resolver(
        request,
        response_id=fake_response_id(request),
        response_status=status,
    )
    return provider.generate(request, output_model, resolver=resolver)


def _replay_generate(
    provider: ReplayAIProvider,
    request: AIRequest,
    output_model: type[FrozenModel],
    *,
    status: AIResponseStatus = AIResponseStatus.SUCCESS,
):
    resolver = _execution_resolver(
        request,
        response_id="replay-response-1",
        response_status=status,
    )
    return provider.generate(request, output_model, resolver=resolver)


def _write_replay(
    directory: Path,
    request: AIRequest,
    *,
    status: AIResponseStatus = AIResponseStatus.SUCCESS,
    output: object = None,
    fingerprint: str | None = None,
    schema_hash: str | None = None,
    fixture_version: str = "1.0.0",
    validation_errors: tuple[str, ...] | None = None,
    created_at: datetime = NOW,
) -> Path:
    actual_fingerprint = request_fingerprint(request)
    path = directory / f"{actual_fingerprint}.json"
    values: dict[str, object] = {
        "fixture_version": fixture_version,
        "request_fingerprint": fingerprint or actual_fingerprint,
        "schema_sha256": schema_hash or request.output_schema.sha256,
        "status": status.value,
        "provider_response_id": "replay-response-1",
        "created_at": created_at.isoformat(),
        "usage": AIUsage().model_dump(mode="json"),
    }
    if status is AIResponseStatus.SUCCESS:
        values["output"] = output if output is not None else {"title": "Synthetic title"}
    elif status is AIResponseStatus.REFUSED:
        values["refusal_reason"] = "policy refusal"
    elif status is AIResponseStatus.INCOMPLETE:
        values["incomplete"] = IncompleteDetail(reason="truncated").model_dump(mode="json")
    elif status is AIResponseStatus.INVALID_OUTPUT:
        invalid = output if output is not None else {}
        values["output"] = invalid
        values["validation_errors"] = list(
            validation_errors
            if validation_errors is not None
            else validation_error_details(SampleOutput, invalid)
        )
    elif status is AIResponseStatus.FAILURE:
        values["failure"] = FailureDetail(
            code="PROVIDER_FAILURE", message="synthetic failure", retryable=False
        ).model_dump(mode="json")
    path.write_text(json.dumps(values), encoding="utf-8")
    return path


def test_fake_success_is_deterministic_and_schema_bound() -> None:
    request = _request("fake")
    provider = FakeAIProvider(payload={"title": "Synthetic title"}, created_at=NOW)
    first = _fake_generate(provider, request, SampleOutput)
    assert first == _fake_generate(provider, request, SampleOutput)
    assert first.output_schema == request.output_schema
    assert first.request_id == request.request_id
    assert first.job_id == request.job_id


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (FakeMode.REFUSED, AIResponseStatus.REFUSED),
        (FakeMode.INCOMPLETE, AIResponseStatus.INCOMPLETE),
        (FakeMode.INVALID_OUTPUT, AIResponseStatus.INVALID_OUTPUT),
        (FakeMode.FAILURE, AIResponseStatus.FAILURE),
    ],
)
def test_fake_non_success_states_are_distinct(mode: FakeMode, expected: AIResponseStatus) -> None:
    request = _request("fake")
    response = _fake_generate(FakeAIProvider(mode=mode, payload={}), request, SampleOutput)
    assert response.status is expected
    assert response.output is None
    assert (response.raw_output is not None) is (expected is AIResponseStatus.INVALID_OUTPUT)


def test_fake_cannot_label_valid_payload_invalid_or_invalid_payload_successful() -> None:
    with pytest.raises(AIProviderError, match="unexpectedly validates"):
        request = _request("fake")
        _fake_generate(
            FakeAIProvider(mode=FakeMode.INVALID_OUTPUT, payload={"title": "valid"}),
            request,
            SampleOutput,
        )
    with pytest.raises(AIProviderError, match="incompatible"):
        request = _request("fake")
        _fake_generate(FakeAIProvider(payload={}), request, SampleOutput)


APPROVAL_CASES = (
    (AliasedApproval, {"state": "GEOLOGIST_APPROVED"}),
    (ExcludedApproval, {"review_status": "GEOLOGIST_APPROVED"}),
    (NestedApproval, {"nested": {"review_status": "GEOLOGIST_APPROVED"}}),
    (ExtraApproval, {"nested": {"title": "safe", "reviewer_id": "human-reviewer"}}),
    (CustomSerializedApproval, {"review_status": "GEOLOGIST_APPROVED"}),
    (ComputedApproval, {"title": "safe"}),
    (PrivateApproval, {"title": "safe"}),
    (cast(type[FrozenModel], RootApproval), "GEOLOGIST_APPROVED"),
    (MappingKeyApproval, {"payload": {"GEOLOGIST_APPROVED": "hidden"}}),
    (CollectionApproval, {"payload": ["safe", "SUPERSEDED"]}),
    (
        CanonicalApproval,
        {"payload": {"canonical_json": canonical_json_text({"reviewer_id": "human-reviewer"})}},
    ),
    (
        NamedCanonicalApproval,
        {
            "payload": {
                "name": "apparently_safe",
                "value": {"canonical_json": canonical_json_text({"supersession_id": "forged"})},
            }
        },
    ),
    (DataclassApproval, {"payload": {"reviewer_id": "human-reviewer"}}),
    (UnsupportedContainerApproval, {"payload": {"value": "safe"}}),
)


@pytest.mark.parametrize(("output_model", "payload"), APPROVAL_CASES)
def test_fake_rejects_hidden_aliased_excluded_and_nested_approval(
    output_model: type[FrozenModel], payload: object
) -> None:
    with pytest.raises(
        AIProviderError,
        match="review|approval|lifecycle|AI_DRAFT|computed|custom|unsupported",
    ):
        request = _request("fake", output_model)
        _fake_generate(FakeAIProvider(payload=payload), request, output_model)


@pytest.mark.parametrize(
    "status",
    [
        AIResponseStatus.SUCCESS,
        AIResponseStatus.REFUSED,
        AIResponseStatus.INCOMPLETE,
        AIResponseStatus.INVALID_OUTPUT,
        AIResponseStatus.FAILURE,
    ],
)
def test_replay_represents_every_response_state(tmp_path: Path, status: AIResponseStatus) -> None:
    request = _request("replay")
    _write_replay(tmp_path, request, status=status)
    response = _replay_generate(ReplayAIProvider(tmp_path), request, SampleOutput, status=status)
    assert response.status is status
    assert (response.output is not None) is (status is AIResponseStatus.SUCCESS)


def test_replay_missing_corrupt_invalid_utf8_and_incompatible_are_distinct(
    tmp_path: Path,
) -> None:
    request = _request("replay")
    provider = ReplayAIProvider(tmp_path)
    with pytest.raises(ReplayFixtureMissingError):
        _replay_generate(provider, request, SampleOutput)
    path = tmp_path / f"{request_fingerprint(request)}.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ReplayFixtureCorruptError):
        _replay_generate(provider, request, SampleOutput)
    path.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(ReplayFixtureCorruptError):
        _replay_generate(provider, request, SampleOutput)
    _write_replay(tmp_path, request, schema_hash="f" * 64)
    with pytest.raises(ReplayFixtureIncompatibleError, match="schema hash"):
        _replay_generate(provider, request, SampleOutput)


@pytest.mark.parametrize("fixture_version", ["2.0.0", "1.1.0", "1.0.1"])
def test_replay_rejects_unknown_persisted_versions(tmp_path: Path, fixture_version: str) -> None:
    request = _request("replay")
    _write_replay(tmp_path, request, fixture_version=fixture_version)
    with pytest.raises(ReplayFixtureInternallyInconsistentError, match="fixture_version"):
        _replay_generate(ReplayAIProvider(tmp_path), request, SampleOutput)


@pytest.mark.parametrize("nested", [False, True])
def test_replay_rejects_duplicate_json_keys_recursively(tmp_path: Path, nested: bool) -> None:
    request = _request("replay")
    path = _write_replay(tmp_path, request)
    valid = path.read_text(encoding="utf-8")
    if nested:
        duplicate = valid.replace('"usage": {', '"usage": {"requests": 1, "requests": 1,')
    else:
        duplicate = valid[:-1] + ',"status":"SUCCESS"}'
    path.write_text(duplicate, encoding="utf-8")
    with pytest.raises(ReplayFixtureCorruptError, match="duplicate JSON key"):
        _replay_generate(ReplayAIProvider(tmp_path), request, SampleOutput)


def test_replay_revalidates_state_and_current_validation_descriptions(tmp_path: Path) -> None:
    request = _request("replay")
    _write_replay(
        tmp_path,
        request,
        status=AIResponseStatus.INVALID_OUTPUT,
        validation_errors=("fabricated stale description",),
    )
    with pytest.raises(ReplayFixtureInternallyInconsistentError, match="current schema"):
        _replay_generate(
            ReplayAIProvider(tmp_path),
            request,
            SampleOutput,
            status=AIResponseStatus.INVALID_OUTPUT,
        )
    _write_replay(tmp_path, request, status=AIResponseStatus.INVALID_OUTPUT)
    assert (
        _replay_generate(
            ReplayAIProvider(tmp_path),
            request,
            SampleOutput,
            status=AIResponseStatus.INVALID_OUTPUT,
        ).status
        is AIResponseStatus.INVALID_OUTPUT
    )


def test_replay_validity_labels_cannot_contradict_current_schema(tmp_path: Path) -> None:
    request = _request("replay")
    _write_replay(
        tmp_path,
        request,
        status=AIResponseStatus.INVALID_OUTPUT,
        output={"title": "valid"},
        validation_errors=("fabricated",),
    )
    with pytest.raises(ReplayFixtureInternallyInconsistentError, match="labels it INVALID_OUTPUT"):
        _replay_generate(
            ReplayAIProvider(tmp_path),
            request,
            SampleOutput,
            status=AIResponseStatus.INVALID_OUTPUT,
        )
    _write_replay(tmp_path, request, output={"wrong": "field"})
    with pytest.raises(ReplayFixtureIncompatibleError, match="success output"):
        _replay_generate(ReplayAIProvider(tmp_path), request, SampleOutput)


@pytest.mark.parametrize(("output_model", "payload"), APPROVAL_CASES)
def test_replay_rejects_hidden_aliased_excluded_and_nested_approval(
    tmp_path: Path,
    output_model: type[FrozenModel],
    payload: object,
) -> None:
    request = _request("replay", output_model)
    _write_replay(tmp_path, request, output=payload)
    with pytest.raises(
        AIProviderError,
        match="review|approval|lifecycle|AI_DRAFT|computed|custom|unsupported",
    ):
        _replay_generate(ReplayAIProvider(tmp_path), request, output_model)


def test_replay_fingerprint_mismatch_is_incompatible(tmp_path: Path) -> None:
    request = _request("replay")
    _write_replay(tmp_path, request, fingerprint="e" * 64)
    with pytest.raises(ReplayFixtureIncompatibleError, match="fingerprint mismatch"):
        _replay_generate(ReplayAIProvider(tmp_path), request, SampleOutput)


@pytest.mark.parametrize(
    ("output_model", "payload", "message"),
    [
        (SafeCustomSerializer, {"title": "safe"}, "custom"),
        (SafeComputedField, {"title": "safe"}, "computed"),
        (
            SafeExcludedField,
            {"title": "safe", "hidden_semantic_value": "meaningful"},
            "exclude",
        ),
        (
            NestedSafeExcludedField,
            {"nested": {"title": "safe", "hidden_semantic_value": "meaningful"}},
            "exclude",
        ),
    ],
)
def test_fake_success_requires_standard_exact_output_serialization(
    output_model: type[FrozenModel],
    payload: object,
    message: str,
) -> None:
    request = _request("fake", output_model)
    with pytest.raises(AIProviderError, match=message):
        _fake_generate(FakeAIProvider(payload=payload, created_at=NOW), request, output_model)


@pytest.mark.parametrize(
    ("output_model", "payload", "message"),
    [
        (SafeCustomSerializer, {"title": "safe"}, "custom"),
        (SafeComputedField, {"title": "safe"}, "computed"),
        (
            SafeExcludedField,
            {"title": "safe", "hidden_semantic_value": "meaningful"},
            "exclude",
        ),
        (
            NestedSafeExcludedField,
            {"nested": {"title": "safe", "hidden_semantic_value": "meaningful"}},
            "exclude",
        ),
    ],
)
def test_replay_success_requires_standard_exact_output_serialization(
    tmp_path: Path,
    output_model: type[FrozenModel],
    payload: object,
    message: str,
) -> None:
    request = _request("replay", output_model)
    _write_replay(tmp_path, request, output=payload)
    with pytest.raises(AIProviderError, match=message):
        _replay_generate(ReplayAIProvider(tmp_path), request, output_model)


def test_fake_default_response_time_comes_from_authoritative_job_not_fixed_epoch() -> None:
    request = _request("fake")
    response = _fake_generate(FakeAIProvider(payload={"title": "safe"}), request, SampleOutput)
    assert response.created_at == NOW
    assert response.created_at.year == 2026


def test_fake_response_usage_comes_from_the_authoritative_job() -> None:
    request = _request("fake")
    usage = AIUsage(input_tokens=7, output_tokens=3, requests=1)
    resolver = _execution_resolver(
        request,
        response_id=fake_response_id(request),
        response_status=AIResponseStatus.SUCCESS,
        usage=usage,
    )
    response = FakeAIProvider(payload={"title": "safe"}, created_at=NOW).generate(
        request,
        SampleOutput,
        resolver=resolver,
    )
    assert response.usage == usage


def test_replay_usage_must_match_the_authoritative_job(tmp_path: Path) -> None:
    request = _request("replay")
    _write_replay(tmp_path, request)
    resolver = _execution_resolver(
        request,
        response_id="replay-response-1",
        response_status=AIResponseStatus.SUCCESS,
        usage=AIUsage(input_tokens=1),
    )
    with pytest.raises(ReplayFixtureIncompatibleError, match="usage"):
        ReplayAIProvider(tmp_path).generate(request, SampleOutput, resolver=resolver)


def test_fake_generation_rejects_response_outside_authoritative_job_interval() -> None:
    request = _request("fake")
    resolver = _execution_resolver(
        request,
        response_id=fake_response_id(request),
        response_status=AIResponseStatus.SUCCESS,
    )
    provider = FakeAIProvider(
        payload={"title": "safe"},
        created_at=NOW - timedelta(seconds=1),
    )
    with pytest.raises(AIProviderError, match="causal order"):
        provider.generate(request, SampleOutput, resolver=resolver)


def test_replay_generation_rejects_response_outside_authoritative_job_interval(
    tmp_path: Path,
) -> None:
    request = _request("replay")
    _write_replay(tmp_path, request, created_at=NOW - timedelta(seconds=1))
    with pytest.raises(AIProviderError, match="causal order"):
        _replay_generate(ReplayAIProvider(tmp_path), request, SampleOutput)


def test_provider_generation_rejects_non_authoritative_request_object() -> None:
    request = _request("fake")
    resolver = _execution_resolver(
        request,
        response_id=fake_response_id(request),
        response_status=AIResponseStatus.SUCCESS,
    )
    forged = request.model_copy(update={"created_at": NOW - timedelta(seconds=1)})
    with pytest.raises(AIProviderError, match="differs from the authoritative"):
        FakeAIProvider(payload={"title": "safe"}, created_at=NOW).generate(
            forged,
            SampleOutput,
            resolver=resolver,
        )
