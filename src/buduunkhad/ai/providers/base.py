"""Provider-neutral protocol and offline provider safety checks."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path, PurePath
from typing import Protocol, TypeVar, cast

from pydantic import AliasChoices, AliasPath, BaseModel, ValidationError

from buduunkhad.ai.contracts import (
    AIJob,
    AIRequest,
    AIResponse,
    CanonicalJSONValue,
    FrozenModel,
    ReviewStatus,
)
from buduunkhad.ai.fingerprint import persisted_model_bytes, request_fingerprint, sha256_value

OutputT = TypeVar("OutputT", bound=FrozenModel)


class AIProviderError(RuntimeError):
    """Base provider failure."""


class AIProvider(Protocol):
    """Minimal typed interface implemented by offline and future providers."""

    @property
    def name(self) -> str: ...

    def generate(
        self,
        request: AIRequest,
        output_model: type[OutputT],
        *,
        resolver: ProviderExecutionResolver,
    ) -> AIResponse[OutputT]: ...


class ProviderExecutionResolver(Protocol):
    def resolve_request(self, request_id: str) -> AIRequest: ...

    def resolve_job(self, job_id: str) -> AIJob: ...


_HUMAN_REVIEW_FIELDS = {
    "approved_by",
    "approval",
    "authorization",
    "geologist_approved",
    "review_note",
    "reviewed_at",
    "reviewer_authorization",
    "reviewer_id",
    "reviewer_name",
    "superseded",
    "superseded_at",
    "supersession",
    "supersession_id",
}
_FORBIDDEN_REVIEW_VALUES = {
    ReviewStatus.AI_VALIDATED.value,
    ReviewStatus.GEOLOGIST_APPROVED.value,
    ReviewStatus.REJECTED.value,
    ReviewStatus.SUPERSEDED.value,
}


def prohibit_provider_approval(value: object) -> None:
    """Reject provider values that encode review, approval, or supersession authority.

    This walks declared Pydantic fields and their live values. It therefore does not
    depend on aliases, ``exclude=True``, or a model's custom serializer.
    """
    _inspect_provider_value(value, set(), field_names=())


def validation_error_details(output_model: type[FrozenModel], payload: object) -> tuple[str, ...]:
    """Return stable validation details derived from the current output schema."""
    try:
        output_model.model_validate(payload)
    except ValidationError as exc:
        return tuple(
            f"{json.dumps(error['loc'], separators=(',', ':'))}:{error['type']}:{error['msg']}"
            for error in exc.errors()
        )
    return ()


def validate_provider_execution(
    request: AIRequest,
    *,
    resolver: ProviderExecutionResolver,
    provider: str,
    response_created_at: datetime,
) -> AIJob:
    """Resolve the authoritative request/job and enforce the provider causal interval."""
    authoritative_request = resolver.resolve_request(request.request_id)
    if persisted_model_bytes(authoritative_request) != persisted_model_bytes(request):
        raise AIProviderError("provider request differs from the authoritative record")
    job = resolver.resolve_job(request.job_id)
    if (
        job.request_id != request.request_id
        or job.request_fingerprint != request_fingerprint(request)
        or (job.run_id, job.phase_id, job.task_type)
        != (request.run_id, request.phase_id, request.task_type)
        or job.output_schema != request.output_schema
        or (job.provider, job.model) != (provider, request.provider.model)
        or job.provider_parameters_sha256 != sha256_value(request.provider.parameters)
    ):
        raise AIProviderError("provider job is not bound to the authoritative request")
    if request.provider.provider != provider:
        raise AIProviderError("request provider does not match provider implementation")
    if job.started_at is None:
        raise AIProviderError("provider job has not started")
    if not (request.created_at <= job.created_at <= job.started_at <= response_created_at):
        raise AIProviderError("request/job/response timestamps violate causal order")
    if job.completed_at is not None and response_created_at > job.completed_at:
        raise AIProviderError("provider response postdates job completion")
    return job


def validate_provider_output_contract(
    output: OutputT,
    output_model: type[OutputT],
) -> OutputT:
    """Prove the supported output contract: declared fields, standard JSON, exact reload."""
    if type(output) is not output_model:
        raise AIProviderError("provider output is not the exact bound schema model")
    decorators = output_model.__pydantic_decorators__
    if decorators.model_serializers or decorators.field_serializers:
        raise AIProviderError("provider output models cannot define custom serializers")
    if output_model.model_computed_fields:
        raise AIProviderError("provider output models cannot define computed fields")
    if any(field.exclude for field in output_model.model_fields.values()):
        raise AIProviderError("provider output models cannot exclude semantic fields")
    serialized = output.model_dump_json(round_trip=True)
    try:
        reloaded = output_model.model_validate_json(serialized)
    except ValidationError as exc:
        raise AIProviderError("provider output does not round-trip through its schema") from exc
    if type(reloaded) is not output_model or persisted_model_bytes(
        reloaded
    ) != persisted_model_bytes(output):
        raise AIProviderError("provider output changes during schema round-trip")
    return reloaded


def _inspect_provider_value(
    value: object,
    active: set[int],
    *,
    field_names: tuple[str, ...],
) -> None:
    _check_review_value(value, field_names)
    if isinstance(value, CanonicalJSONValue):
        _inspect_provider_value(value.to_python(), active, field_names=field_names)
        return
    if isinstance(value, BaseModel):
        decorators = type(value).__pydantic_decorators__
        if decorators.model_serializers or decorators.field_serializers:
            raise AIProviderError("custom-serialized provider values are unsupported")
        if type(value).model_computed_fields:
            raise AIProviderError("computed provider values are unsupported")
        _enter(value, active)
        try:
            declared_names = set(type(value).model_fields)
            for name, field in type(value).model_fields.items():
                if field.exclude:
                    raise AIProviderError("excluded semantic provider fields are unsupported")
                aliases = (
                    name,
                    *_field_aliases(
                        field.alias,
                        field.validation_alias,
                        field.serialization_alias,
                    ),
                )
                field_value = object.__getattribute__(value, name)
                _inspect_provider_value(field_value, active, field_names=aliases)
            extra = object.__getattribute__(value, "__pydantic_extra__")
            if extra:
                if type(extra) is not dict:
                    raise AIProviderError("custom Pydantic extra containers are unsupported")
                for name, extra_value in extra.items():
                    if type(name) is not str:
                        raise AIProviderError("provider model extra keys must be exact strings")
                    _inspect_provider_value(extra_value, active, field_names=(name,))
                raise AIProviderError("undeclared Pydantic provider fields are unsupported")
            instance_values = object.__getattribute__(value, "__dict__")
            if type(instance_values) is not dict:
                raise AIProviderError("custom Pydantic instance containers are unsupported")
            for name, instance_value in instance_values.items():
                if name not in declared_names:
                    _inspect_provider_value(instance_value, active, field_names=(name,))
                    raise AIProviderError("undeclared provider instance state is unsupported")
            private = object.__getattribute__(value, "__pydantic_private__")
            if private:
                for name, private_value in private.items():
                    _inspect_provider_value(private_value, active, field_names=(name,))
        finally:
            active.remove(id(value))
        return
    if type(value) is dict:
        _enter(value, active)
        try:
            for key, item in value.items():
                if type(key) is not str:
                    raise AIProviderError("provider mapping keys must be exact strings")
                _inspect_provider_value(key, active, field_names=())
                names = (key,)
                _inspect_provider_value(item, active, field_names=names)
        finally:
            active.remove(id(value))
        return
    if type(value) in {tuple, list, set, frozenset}:
        _enter(value, active)
        try:
            for item in cast(Iterable[object], value):
                _inspect_provider_value(item, active, field_names=())
        finally:
            active.remove(id(value))
        return
    if is_dataclass(value) and not isinstance(value, type):
        _enter(value, active)
        try:
            dataclass_names: set[str] = set()
            for data_field in dataclass_fields(value):
                dataclass_names.add(data_field.name)
                field_value = object.__getattribute__(value, data_field.name)
                _inspect_provider_value(field_value, active, field_names=(data_field.name,))
            try:
                instance_values = object.__getattribute__(value, "__dict__")
            except AttributeError:
                instance_values = {}
            if type(instance_values) is not dict:
                raise AIProviderError("custom dataclass instance containers are unsupported")
            for name, instance_value in instance_values.items():
                if name not in dataclass_names:
                    _inspect_provider_value(instance_value, active, field_names=(name,))
        finally:
            active.remove(id(value))
        return
    if type(value) in {type(None), bool, int, float, str, bytes, Decimal, date, datetime}:
        return
    if isinstance(value, Enum):
        _inspect_provider_value(value.value, active, field_names=field_names)
        return
    if isinstance(value, (Path, PurePath)):
        return
    raise AIProviderError(f"unsupported provider value type: {type(value).__name__}")


def _check_review_value(value: object, field_names: tuple[str, ...]) -> None:
    normalized = {name.casefold().lstrip("_") for name in field_names}
    if "review_status" in normalized:
        status = value.value if isinstance(value, ReviewStatus) else value
        if status != ReviewStatus.AI_DRAFT.value:
            raise AIProviderError("AI/provider output can create only AI_DRAFT content")
    human_field = normalized & _HUMAN_REVIEW_FIELDS or any(
        token in name
        for name in normalized
        for token in ("approval", "authorization", "reviewer", "supersess")
    )
    if human_field and value is not None:
        raise AIProviderError("AI/provider output cannot contain human review or supersession data")
    status_value = value.value if isinstance(value, ReviewStatus) else value
    if isinstance(status_value, str) and status_value in _FORBIDDEN_REVIEW_VALUES:
        raise AIProviderError("AI/provider output cannot create review lifecycle state")


def _field_aliases(*aliases: object) -> tuple[str, ...]:
    result: list[str] = []
    for alias in aliases:
        if isinstance(alias, str):
            result.append(alias)
        elif isinstance(alias, AliasChoices):
            for choice in alias.choices:
                result.extend(_field_aliases(choice))
        elif isinstance(alias, AliasPath):
            result.extend(str(part) for part in alias.path)
    return tuple(result)


def _enter(value: object, active: set[int]) -> None:
    identity = id(value)
    if identity in active:
        raise AIProviderError("provider payload contains a reference cycle")
    active.add(identity)
