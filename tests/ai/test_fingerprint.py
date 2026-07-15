from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from enum import Enum, StrEnum
from pathlib import PurePosixPath, PureWindowsPath

import pytest

from buduunkhad.ai.contracts import (
    AIRequest,
    AIUsage,
    PageLocator,
    PromptIdentity,
    ProviderConfiguration,
    SchemaIdentity,
    SourceReference,
    TaskType,
)
from buduunkhad.ai.fingerprint import (
    CanonicalizationError,
    NaiveDatetimeError,
    canonical_json_bytes,
    canonical_json_text,
    canonical_value_from_text,
    request_fingerprint,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
NOW = datetime(2026, 1, 1, tzinfo=UTC)


class PlainEnum(Enum):
    VALUE = "declared"


class StringEnum(StrEnum):
    VALUE = "declared"


def _request(*, reverse: bool = False, request_id: str = "request-1") -> AIRequest:
    provider_parameters = (
        {"temperature": 0, "seed": 42} if not reverse else {"seed": 42, "temperature": 0}
    )
    interpretation = (
        {"language": "en", "include_tables": True}
        if not reverse
        else {"include_tables": True, "language": "en"}
    )
    sources = (
        SourceReference(
            asset_id="b-source",
            sha256=SHA_B,
            locators=(PageLocator(page_number=2),),
        ),
        SourceReference(
            asset_id="a-source",
            sha256=SHA_A,
            locators=(PageLocator(page_number=1),),
        ),
    )
    return AIRequest.model_validate(
        {
            "request_id": request_id,
            "job_id": f"job-{request_id}",
            "run_id": "run-1",
            "phase_id": "phase-00",
            "task_type": TaskType.DOCUMENT_EXTRACTION,
            "created_at": NOW,
            "source_references": tuple(reversed(sources)) if reverse else sources,
            "prompt": PromptIdentity(prompt_id="fixture", version="1.0.0", sha256=SHA_A),
            "output_schema": SchemaIdentity(schema_id="fixture", version="1.0.0", sha256=SHA_B),
            "provider": ProviderConfiguration.model_validate(
                {
                    "provider": "test-provider",
                    "model": "test-model",
                    "parameters": provider_parameters,
                }
            ),
            "interpretation_parameters": interpretation,
        }
    )


def test_request_fingerprint_is_order_stable_and_excludes_execution_identity() -> None:
    assert request_fingerprint(_request()) == request_fingerprint(_request(reverse=True))
    changed_id = _request(request_id="request-2").model_copy(
        update={"job_id": "job-2", "run_id": "run-2", "created_at": NOW + timedelta(days=1)}
    )
    assert request_fingerprint(_request()) == request_fingerprint(changed_id)


def test_decimal_and_aware_datetime_equivalence_is_normalized() -> None:
    assert canonical_json_bytes(Decimal("1.0")) == canonical_json_bytes(Decimal("1.00"))
    utc = datetime(2026, 1, 1, tzinfo=UTC)
    offset = datetime(2026, 1, 1, 8, tzinfo=timezone(timedelta(hours=8)))
    assert canonical_json_bytes(utc) == canonical_json_bytes(offset)


def test_date_datetime_and_string_are_distinct_and_enums_use_values() -> None:
    encoded_date = canonical_json_bytes(date(2026, 1, 1))
    assert encoded_date != canonical_json_bytes("2026-01-01")
    assert encoded_date != canonical_json_bytes(datetime(2026, 1, 1, tzinfo=UTC))
    assert canonical_json_bytes(PlainEnum.VALUE) == canonical_json_bytes(StringEnum.VALUE)


def test_platform_paths_and_collection_semantics_are_declared() -> None:
    assert canonical_json_bytes(PureWindowsPath(r"folder\file.txt")) == canonical_json_bytes(
        PurePosixPath("folder/file.txt")
    )
    assert canonical_json_bytes((1, 2)) != canonical_json_bytes((2, 1))
    assert canonical_json_bytes([1, 2]) != canonical_json_bytes((1, 2))
    assert canonical_json_bytes({1, 2, 3}) == canonical_json_bytes({3, 2, 1})
    assert canonical_json_bytes(frozenset({1, 2})) == canonical_json_bytes({2, 1})


def test_pydantic_payload_round_trips_through_one_canonical_implementation() -> None:
    model = AIUsage(input_tokens=2, output_tokens=3, cost_usd=Decimal("1.2300"))
    text = canonical_json_text(model)
    decoded = canonical_value_from_text(text)
    assert decoded == model.model_dump(mode="python")
    assert canonical_json_text(decoded) == text


def test_stored_text_must_itself_be_canonical_json() -> None:
    canonical = canonical_json_text({"a": 1, "b": 2})
    assert canonical_value_from_text(canonical) == {"a": 1, "b": 2}
    with pytest.raises(CanonicalizationError, match="not in canonical form"):
        canonical_value_from_text(canonical.replace(",", ", "))


def test_duplicate_canonical_set_members_are_rejected() -> None:
    value = {PureWindowsPath("same"), PurePosixPath("same")}
    assert len(value) == 2
    with pytest.raises(CanonicalizationError, match="duplicate canonical members"):
        canonical_json_bytes(value)


@pytest.mark.parametrize(
    "value",
    [
        {1: "integer key"},
        {1: "integer", "1": "string collision"},
        float("nan"),
        float("inf"),
        Decimal("NaN"),
        b"unsupported",
        object(),
    ],
)
def test_ambiguous_or_unsupported_values_fail_explicitly(value: object) -> None:
    with pytest.raises(CanonicalizationError):
        canonical_json_bytes(value)


def test_direct_and_indirect_cycles_raise_domain_error() -> None:
    direct: list[object] = []
    direct.append(direct)
    indirect_list: list[object] = []
    indirect: dict[str, object] = {"list": indirect_list}
    indirect_list.append(indirect)
    for value in (direct, indirect):
        with pytest.raises(CanonicalizationError, match="reference cycle"):
            canonical_json_bytes(value)


def test_naive_datetime_has_dedicated_failure() -> None:
    with pytest.raises(NaiveDatetimeError, match="timezone-aware"):
        canonical_json_bytes(datetime(2026, 1, 1))


def test_decimal_canonicalization_is_context_independent_exact_and_exponent_bounded() -> None:
    value = Decimal("123456789012345678901234567890.123450000")
    encodings: list[bytes] = []
    for precision in (10, 28, 50):
        with localcontext() as context:
            context.prec = precision
            encodings.append(canonical_json_bytes(value))
    assert len(set(encodings)) == 1
    assert canonical_json_bytes(Decimal("1.2300")) == canonical_json_bytes(Decimal("1.23"))
    assert canonical_json_bytes(Decimal("0")) == canonical_json_bytes(Decimal("-0"))
    assert canonical_json_bytes(Decimal("1e-1000000")) != canonical_json_bytes(Decimal("0"))
    assert canonical_json_bytes(Decimal("1e-1000000")) != canonical_json_bytes(
        Decimal("2e-1000000")
    )
    assert len(canonical_json_bytes(Decimal("1e-1000000"))) < 64
    assert len(canonical_json_bytes(Decimal("1e1000000"))) < 64


def test_decimal_values_beyond_default_context_precision_remain_distinct() -> None:
    first = Decimal("1.1234567890123456789012345678901")
    second = Decimal("1.1234567890123456789012345678902")
    assert canonical_json_bytes(first) != canonical_json_bytes(second)


def test_decimal_named_parameters_keep_request_fingerprints_exact() -> None:
    base = _request()

    def with_decimal(value: Decimal) -> AIRequest:
        provider = base.provider.model_copy(update={"parameters": {"threshold": value}})
        return base.model_copy(
            update={
                "provider": provider,
                "interpretation_parameters": {"threshold": value},
            }
        )

    assert request_fingerprint(with_decimal(Decimal("1.2300"))) == request_fingerprint(
        with_decimal(Decimal("1.23"))
    )
    assert request_fingerprint(
        with_decimal(Decimal("1.1234567890123456789012345678901"))
    ) != request_fingerprint(with_decimal(Decimal("1.1234567890123456789012345678902")))


class _MaliciousInt(int):
    def __str__(self) -> str:
        raise AssertionError("attacker-controlled str called")

    def __repr__(self) -> str:
        raise AssertionError("attacker-controlled repr called")

    def __int__(self) -> int:
        raise AssertionError("attacker-controlled int called")

    def __float__(self) -> float:
        raise AssertionError("attacker-controlled float called")


class _MaliciousFloat(float):
    def __str__(self) -> str:
        raise AssertionError("attacker-controlled str called")

    def __repr__(self) -> str:
        raise AssertionError("attacker-controlled repr called")

    def __float__(self) -> float:
        raise AssertionError("attacker-controlled float called")


class _MaliciousDate(date):
    def isoformat(self) -> str:
        raise AssertionError("attacker-controlled isoformat called")


class _MaliciousDatetime(datetime):
    def astimezone(self, tz=None):
        raise AssertionError("attacker-controlled astimezone called")


class _MaliciousPath(PurePosixPath):
    def as_posix(self) -> str:
        raise AssertionError("attacker-controlled path conversion called")

    def __str__(self) -> str:
        raise AssertionError("attacker-controlled str called")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: _MaliciousInt(1),
        lambda: _MaliciousFloat(1.0),
        lambda: _MaliciousDate(2026, 1, 1),
        lambda: _MaliciousDatetime(2026, 1, 1, tzinfo=UTC),
        lambda: _MaliciousPath("safe"),
    ],
    ids=("int", "float", "date", "datetime", "path"),
)
def test_scalar_subclasses_fail_without_invoking_attacker_hooks(factory) -> None:
    with pytest.raises(CanonicalizationError, match="unsupported"):
        canonical_json_bytes(factory())


def test_aware_datetime_utc_underflow_is_wrapped_as_canonicalization_error() -> None:
    extreme = datetime.min.replace(tzinfo=timezone(timedelta(hours=14)))
    with pytest.raises(CanonicalizationError, match="represented in UTC"):
        canonical_json_bytes(extreme)
