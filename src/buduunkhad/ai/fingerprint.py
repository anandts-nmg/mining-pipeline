"""Strict canonical serialization for AI requests, content, prompts, and schemas."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path, PosixPath, PurePosixPath, PureWindowsPath, WindowsPath
from typing import TYPE_CHECKING, TypeVar, cast

from pydantic import BaseModel

from buduunkhad.ai.schema_identity import (
    LEGACY_SCHEMA_FINGERPRINT_ALGORITHM,
    SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
    semantic_schema_sha256,
)

if TYPE_CHECKING:
    from buduunkhad.ai.contracts import AIRequest, SchemaIdentity


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented canonically and unambiguously."""


class NaiveDatetimeError(CanonicalizationError):
    """Raised when canonicalization receives a datetime without a UTC offset."""


CanonicalNode = object
ModelT = TypeVar("ModelT", bound=BaseModel)


def canonical_json_bytes(value: object) -> bytes:
    """Return one unambiguous UTF-8 representation for every supported value."""
    node = _canonical_node(value, set())
    return _node_bytes(node)


def canonical_json_text(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def canonical_value_from_text(text: str) -> object:
    """Decode canonical text and prove that the supplied text itself is canonical."""
    try:
        node: object = json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except (json.JSONDecodeError, CanonicalizationError) as exc:
        raise CanonicalizationError(f"invalid canonical JSON: {exc}") from exc
    value = _decode_node(node)
    if canonical_json_text(value) != text:
        raise CanonicalizationError("canonical JSON text is not in canonical form")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def persisted_model_bytes(value: BaseModel) -> bytes:
    """Return deterministic persisted bytes without semantic time/number normalization."""
    decorators = type(value).__pydantic_decorators__
    if (
        type(value).model_dump_json is not BaseModel.model_dump_json
        or decorators.model_serializers
        or decorators.field_serializers
        or type(value).model_computed_fields
        or any(field.exclude for field in type(value).model_fields.values())
    ):
        # Custom serializers are valid only when their contract is explicitly consumed by
        # the caller. Security-sensitive artifact records use the standard serializer.
        raise CanonicalizationError("custom model serialization is unsupported for record digests")
    return value.model_dump_json(round_trip=True).encode("utf-8")


def persisted_model_sha256(value: BaseModel) -> str:
    return sha256_bytes(persisted_model_bytes(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_identity_for_model(
    model: type[ModelT], *, schema_id: str, version: str
) -> SchemaIdentity:
    """Build the current, framework-independent identity for a Pydantic model."""
    from buduunkhad.ai.contracts import SchemaIdentity

    return SchemaIdentity(
        schema_id=schema_id,
        version=version,
        sha256=semantic_schema_sha256(model.model_json_schema()),
        fingerprint_algorithm=SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
    )


def schema_identity_fingerprint_value(identity: SchemaIdentity) -> dict[str, str]:
    """Project an identity into higher-level hashes without rewriting legacy history."""

    value = {
        "schema_id": identity.schema_id,
        "version": identity.version,
        "sha256": identity.sha256,
    }
    if identity.fingerprint_algorithm != LEGACY_SCHEMA_FINGERPRINT_ALGORITHM:
        value["fingerprint_algorithm"] = identity.fingerprint_algorithm
    return value


def request_fingerprint(request: AIRequest) -> str:
    """Hash reproducibility inputs while excluding execution IDs and timestamps."""
    from buduunkhad.ai.contracts import AIRequest

    if not isinstance(request, AIRequest):
        raise CanonicalizationError("request_fingerprint requires an AIRequest")
    sources = []
    for source in request.source_references:
        sources.append(
            {
                "asset_id": source.asset_id,
                "sha256": source.sha256,
                "locators": tuple(sorted(source.locators, key=canonical_json_bytes)),
            }
        )
    sources.sort(key=canonical_json_bytes)
    payload = {
        "task_type": request.task_type,
        "sources": tuple(sources),
        "prompt": request.prompt,
        "schema": schema_identity_fingerprint_value(request.output_schema),
        "provider": request.provider,
        "interpretation_parameters": request.interpretation_parameters,
        "subject": request.subject,
    }
    return sha256_value(payload)


def _canonical_node(value: object, active: set[int]) -> CanonicalNode:
    if isinstance(value, Enum):
        member_name = object.__getattribute__(value, "_name_")
        declared = type(value).__members__.get(member_name)
        if declared is not value:
            raise CanonicalizationError("Enum value is not a declared member")
        return _canonical_node(object.__getattribute__(value, "_value_"), active)
    if value is None:
        return ["null"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is str:
        return ["str", value]
    if type(value) is int:
        return ["int", str(value)]
    if type(value) is Decimal:
        if not value.is_finite():
            raise CanonicalizationError("Decimal values must be finite")
        return ["decimal", _normalise_decimal(value)]
    if type(value) is float:
        if not math.isfinite(value):
            raise CanonicalizationError("float values must be finite")
        normalised = 0.0 if value == 0.0 else value
        return ["float", repr(normalised)]
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise NaiveDatetimeError("datetime values must be timezone-aware")
        try:
            utc_value = value.astimezone(UTC)
        except (OverflowError, ValueError) as exc:
            raise CanonicalizationError("datetime cannot be represented in UTC") from exc
        return ["datetime", utc_value.isoformat().replace("+00:00", "Z")]
    if type(value) is date:
        return ["date", value.isoformat()]
    if type(value) in {PurePosixPath, PureWindowsPath, PosixPath, WindowsPath}:
        return ["path", cast(PurePosixPath, value).as_posix()]
    if isinstance(value, BaseModel):
        with _active_container(value, active):
            fields = {
                name: object.__getattribute__(value, name) for name in type(value).model_fields
            }
            return _canonical_mapping(fields, active)
    if type(value) is dict:
        with _active_container(value, active):
            return _canonical_mapping(cast(Mapping[str, object], value), active)
    if type(value) is tuple:
        with _active_container(value, active):
            return ["tuple", [_canonical_node(item, active) for item in value]]
    if type(value) is list:
        with _active_container(value, active):
            return ["list", [_canonical_node(item, active) for item in value]]
    if type(value) in {set, frozenset}:
        with _active_container(value, active):
            members = [_canonical_node(item, active) for item in cast(Iterable[object], value)]
            members.sort(key=_node_bytes)
            encodings = tuple(_node_bytes(member) for member in members)
            if len(set(encodings)) != len(encodings):
                raise CanonicalizationError("set contains duplicate canonical members")
            return ["set", members]
    raise CanonicalizationError(f"unsupported canonical value type: {type(value).__name__}")


class _active_container:
    def __init__(self, value: object, active: set[int]) -> None:
        self._identity = id(value)
        self._active = active

    def __enter__(self) -> None:
        if self._identity in self._active:
            raise CanonicalizationError("canonical value contains a reference cycle")
        self._active.add(self._identity)

    def __exit__(self, *_args: object) -> None:
        self._active.remove(self._identity)


def _canonical_mapping(value: Mapping[str, object], active: set[int]) -> CanonicalNode:
    entries: list[list[object]] = []
    seen: set[str] = set()
    for key, item in value.items():
        if type(key) is not str:
            raise CanonicalizationError(
                f"mapping keys must be strings, received {type(key).__name__}"
            )
        if key in seen:
            raise CanonicalizationError(f"duplicate mapping key: {key}")
        seen.add(key)
        entries.append([key, _canonical_node(item, active)])
    entries.sort(key=_mapping_entry_key)
    return ["mapping", entries]


def _mapping_entry_key(entry: list[object]) -> str:
    key = entry[0]
    if type(key) is not str:
        raise CanonicalizationError("canonical mapping entry key is not a string")
    return key


def _decode_node(node: object) -> object:
    if not isinstance(node, list) or not node or not isinstance(node[0], str):
        raise CanonicalizationError("invalid canonical node")
    tag = node[0]
    if tag == "null" and len(node) == 1:
        return None
    if tag == "bool" and len(node) == 2 and isinstance(node[1], bool):
        return node[1]
    if tag == "str" and len(node) == 2 and isinstance(node[1], str):
        return node[1]
    if tag == "int" and len(node) == 2 and isinstance(node[1], str):
        try:
            return int(node[1])
        except ValueError as exc:
            raise CanonicalizationError("invalid canonical integer") from exc
    if tag == "decimal" and len(node) == 2 and isinstance(node[1], str):
        try:
            return Decimal(node[1])
        except ArithmeticError as exc:
            raise CanonicalizationError("invalid canonical Decimal") from exc
    if tag == "float" and len(node) == 2 and isinstance(node[1], str):
        try:
            float_value = float(node[1])
        except ValueError as exc:
            raise CanonicalizationError("invalid canonical float") from exc
        if not math.isfinite(float_value):
            raise CanonicalizationError("canonical float must be finite")
        return float_value
    if tag == "datetime" and len(node) == 2 and isinstance(node[1], str):
        try:
            datetime_value = datetime.fromisoformat(node[1].replace("Z", "+00:00"))
        except ValueError as exc:
            raise CanonicalizationError("invalid canonical datetime") from exc
        if datetime_value.tzinfo is None or datetime_value.utcoffset() is None:
            raise NaiveDatetimeError("canonical datetime must be timezone-aware")
        return datetime_value
    if tag == "date" and len(node) == 2 and isinstance(node[1], str):
        try:
            return date.fromisoformat(node[1])
        except ValueError as exc:
            raise CanonicalizationError("invalid canonical date") from exc
    if tag == "path" and len(node) == 2 and isinstance(node[1], str):
        return Path(node[1])
    if tag in {"tuple", "list", "set"} and len(node) == 2 and isinstance(node[1], list):
        values = tuple(_decode_node(item) for item in node[1])
        if tag == "tuple":
            return values
        if tag == "list":
            return list(values)
        try:
            set_result = frozenset(values)
        except TypeError as exc:
            raise CanonicalizationError("canonical set contains an unhashable member") from exc
        if len(set_result) != len(values):
            raise CanonicalizationError("canonical set contains duplicate members")
        return set_result
    if tag == "mapping" and len(node) == 2 and isinstance(node[1], list):
        mapping_result: dict[str, object] = {}
        for entry in node[1]:
            if not isinstance(entry, list) or len(entry) != 2 or not isinstance(entry[0], str):
                raise CanonicalizationError("invalid canonical mapping entry")
            if entry[0] in mapping_result:
                raise CanonicalizationError(f"duplicate canonical mapping key: {entry[0]}")
            mapping_result[entry[0]] = _decode_node(entry[1])
        return mapping_result
    raise CanonicalizationError(f"invalid canonical node tag or shape: {tag}")


def _normalise_decimal(value: Decimal) -> str:
    sign, raw_digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        raise CanonicalizationError("Decimal values must be finite")
    digits = list(raw_digits)
    if not digits or not any(digits):
        # Signed zero has one declared canonical identity.
        return "0"
    while digits and digits[-1] == 0:
        digits.pop()
        exponent += 1
    coefficient = "".join(chr(ord("0") + digit) for digit in digits)
    prefix = "-" if sign else ""
    return f"{prefix}{coefficient}e{exponent}"


def _node_bytes(node: object) -> bytes:
    return json.dumps(
        node,
        sort_keys=False,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalizationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result
