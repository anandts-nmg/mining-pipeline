"""Versioned, framework-independent JSON Schema identity.

The semantic fingerprint deliberately covers validation behavior, not JSON Schema
annotations emitted by a particular Pydantic release.  It supports the strict subset
used by the repository's structured-output models and fails closed for unknown or
ambiguous constructs.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from importlib import resources
from types import MappingProxyType
from typing import Literal, TypeAlias, cast

SchemaFingerprintAlgorithm: TypeAlias = Literal[
    "pydantic-model-json-schema-v1",
    "buduunkhad-json-schema-semantic-v1",
]
LEGACY_SCHEMA_FINGERPRINT_ALGORITHM: SchemaFingerprintAlgorithm = "pydantic-model-json-schema-v1"
SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM: SchemaFingerprintAlgorithm = (
    "buduunkhad-json-schema-semantic-v1"
)
SUPPORTED_SCHEMA_FINGERPRINT_ALGORITHMS = frozenset(
    {
        LEGACY_SCHEMA_FINGERPRINT_ALGORITHM,
        SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
    }
)


class SchemaFingerprintError(ValueError):
    """A schema cannot be assigned an unambiguous supported identity."""


@dataclass(frozen=True, slots=True)
class SchemaContractRecord:
    """One approved schema/version identity and its exact historical aliases."""

    schema_id: str
    version: str
    sha256: str
    legacy_sha256: tuple[str, ...]


JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
SemanticNode: TypeAlias = object

_ANNOTATION_KEYWORDS = frozenset(
    {
        "$comment",
        "default",
        "deprecated",
        "description",
        "examples",
        "readOnly",
        "title",
        "writeOnly",
    }
)
_STRING_KEYWORDS = frozenset(
    {
        "contentEncoding",
        "contentMediaType",
        "format",
        "pattern",
    }
)
_NON_NEGATIVE_INTEGER_KEYWORDS = frozenset(
    {
        "maxContains",
        "maxItems",
        "maxLength",
        "maxProperties",
        "minContains",
        "minItems",
        "minLength",
        "minProperties",
    }
)
_NUMERIC_KEYWORDS = frozenset(
    {
        "exclusiveMaximum",
        "exclusiveMinimum",
        "maximum",
        "minimum",
        "multipleOf",
    }
)
_SINGLE_SCHEMA_KEYWORDS = frozenset(
    {
        "additionalProperties",
        "contains",
        "contentSchema",
        "else",
        "if",
        "items",
        "not",
        "propertyNames",
        "then",
        "unevaluatedProperties",
    }
)
_SCHEMA_ARRAY_KEYWORDS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
_BOOLEAN_KEYWORDS = frozenset({"uniqueItems"})
_JSON_SCHEMA_TYPES = frozenset(
    {"array", "boolean", "integer", "null", "number", "object", "string"}
)
_KNOWN_SCHEMA_KEYWORDS = frozenset(
    {
        "$defs",
        "$ref",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "contains",
        "contentEncoding",
        "contentMediaType",
        "contentSchema",
        "dependentRequired",
        "dependentSchemas",
        "discriminator",
        "else",
        "enum",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "format",
        "if",
        "items",
        "maxContains",
        "maxItems",
        "maxLength",
        "maxProperties",
        "maximum",
        "minContains",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "multipleOf",
        "not",
        "oneOf",
        "pattern",
        "patternProperties",
        "prefixItems",
        "properties",
        "propertyNames",
        "required",
        "then",
        "type",
        "unevaluatedProperties",
        "uniqueItems",
    }
    | _ANNOTATION_KEYWORDS
)


def semantic_schema_document(schema: object) -> SemanticNode:
    """Return the semantic-v1 identity document for a JSON Schema.

    Internal definitions are resolved by meaning, so definition ordering and names do
    not affect the result.  Reference cycles are intentionally unsupported because
    silently assigning them an incomplete identity would weaken the contract.
    """

    if type(schema) is bool:
        return schema
    root = _require_mapping(schema, "schema root")
    definitions = _root_definitions(root)
    return _normalise_schema(root, definitions=definitions, reference_stack=(), is_root=True)


def semantic_schema_sha256(schema: object) -> str:
    """Hash a schema using ``buduunkhad-json-schema-semantic-v1``."""

    document = {
        "algorithm": SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
        "schema": semantic_schema_document(schema),
    }
    encoded = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_packaged_schema_contracts() -> Mapping[tuple[str, str], SchemaContractRecord]:
    """Load and strictly validate the checked-in semantic identity catalogue."""

    resource = resources.files("buduunkhad.schema_data").joinpath("contracts.json")
    try:
        raw = json.loads(resource.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaFingerprintError) as exc:
        raise SchemaFingerprintError("cannot load packaged schema identity contracts") from exc
    root = _require_exact_mapping(
        raw,
        required={"fingerprint_algorithm", "format_version", "schemas"},
        label="schema contract catalogue",
    )
    if root["format_version"] != "1.0.0":
        raise SchemaFingerprintError("unsupported schema contract catalogue format")
    if root["fingerprint_algorithm"] != SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM:
        raise SchemaFingerprintError("schema contract catalogue uses an unsupported algorithm")
    schemas = _require_sequence(root["schemas"], "schema contract catalogue schemas")
    result: dict[tuple[str, str], SchemaContractRecord] = {}
    for index, item in enumerate(schemas):
        entry = _require_exact_mapping(
            item,
            required={"legacy_fingerprints", "schema_id", "sha256", "version"},
            label=f"schema contract {index}",
        )
        schema_id = _non_empty_string(entry["schema_id"], "schema_id")
        version = _non_empty_string(entry["version"], "version")
        digest = _sha256_string(entry["sha256"], "semantic schema fingerprint")
        aliases = _require_sequence(entry["legacy_fingerprints"], "legacy_fingerprints")
        legacy: list[str] = []
        for alias_index, alias_value in enumerate(aliases):
            alias = _require_exact_mapping(
                alias_value,
                required={"fingerprint_algorithm", "sha256"},
                label=f"legacy fingerprint {alias_index}",
            )
            if alias["fingerprint_algorithm"] != LEGACY_SCHEMA_FINGERPRINT_ALGORITHM:
                raise SchemaFingerprintError("legacy schema alias uses an unsupported algorithm")
            legacy.append(_sha256_string(alias["sha256"], "legacy schema fingerprint"))
        if len(set(legacy)) != len(legacy):
            raise SchemaFingerprintError(f"duplicate legacy fingerprints: {schema_id}@{version}")
        key = (schema_id, version)
        if key in result:
            raise SchemaFingerprintError(f"duplicate schema contract: {schema_id}@{version}")
        result[key] = SchemaContractRecord(
            schema_id=schema_id,
            version=version,
            sha256=digest,
            legacy_sha256=tuple(legacy),
        )
    if not result:
        raise SchemaFingerprintError("schema contract catalogue cannot be empty")
    return MappingProxyType(result)


def _root_definitions(root: Mapping[str, object]) -> Mapping[str, object]:
    modern = root.get("$defs")
    legacy = root.get("definitions")
    if modern is not None and legacy is not None:
        raise SchemaFingerprintError("schema cannot contain both $defs and definitions")
    raw = modern if modern is not None else legacy
    if raw is None:
        return {}
    definitions = _require_mapping(raw, "schema definitions")
    for name, definition in definitions.items():
        if not name:
            raise SchemaFingerprintError("schema definition names cannot be empty")
        _require_schema(definition, f"definition {name!r}")
    return definitions


def _normalise_schema(
    schema: object,
    *,
    definitions: Mapping[str, object],
    reference_stack: tuple[str, ...],
    is_root: bool = False,
) -> SemanticNode:
    if type(schema) is bool:
        return schema
    value = _require_mapping(schema, "schema")
    if not is_root and ("$defs" in value or "definitions" in value):
        raise SchemaFingerprintError("nested schema definitions are unsupported")
    unknown = sorted(
        key
        for key in value
        if key not in _KNOWN_SCHEMA_KEYWORDS
        and key != "definitions"
        and not key.startswith("x-pydantic-")
    )
    if unknown:
        raise SchemaFingerprintError(f"unsupported JSON Schema keywords: {', '.join(unknown)}")

    semantic_items = {
        key: item
        for key, item in value.items()
        if key not in _ANNOTATION_KEYWORDS
        and key not in {"$defs", "definitions", "$ref"}
        and not key.startswith("x-pydantic-")
    }
    result = _normalise_schema_keywords(
        semantic_items,
        definitions=definitions,
        reference_stack=reference_stack,
    )

    if "$ref" not in value:
        if len(result) == 1:
            for keyword in ("allOf", "anyOf", "oneOf"):
                branches = result.get(keyword)
                if type(branches) is list and len(branches) == 1:
                    return branches[0]
        return result
    target = _normalise_reference(
        value["$ref"],
        definitions=definitions,
        reference_stack=reference_stack,
    )
    if not result:
        return target
    branches = sorted((target, result), key=_semantic_bytes)
    return {"allOf": branches}


def _normalise_schema_keywords(
    value: Mapping[str, object],
    *,
    definitions: Mapping[str, object],
    reference_stack: tuple[str, ...],
) -> dict[str, SemanticNode]:
    result: dict[str, SemanticNode] = {}
    for key in sorted(value):
        item = value[key]
        if key == "type":
            result[key] = _normalise_type(item)
        elif key == "required":
            result[key] = _sorted_unique_strings(item, "required")
        elif key == "enum":
            if "const" in value:
                continue  # reduced to the constant by the const branch
            enum_values = _normalise_enum(item)
            if len(enum_values) == 1:
                result["const"] = enum_values[0]
            else:
                result[key] = enum_values
        elif key == "const":
            constant = _normalise_literal(item)
            if "enum" in value:
                # const and enum apply conjunctively: a member constant reduces the
                # accepted values to the constant alone (older Pydantic emits both
                # for single-value Literal fields); a non-member cannot validate.
                members = {_semantic_bytes(member) for member in _normalise_enum(value["enum"])}
                if _semantic_bytes(constant) not in members:
                    raise SchemaFingerprintError("const is not a member of the enum values")
            result[key] = constant
        elif key in {"properties", "patternProperties", "dependentSchemas"}:
            result[key] = _normalise_schema_mapping(
                item,
                label=key,
                definitions=definitions,
                reference_stack=reference_stack,
            )
        elif key == "dependentRequired":
            result[key] = _normalise_dependent_required(item)
        elif key in _SINGLE_SCHEMA_KEYWORDS:
            result[key] = _normalise_schema(
                item,
                definitions=definitions,
                reference_stack=reference_stack,
            )
        elif key in _SCHEMA_ARRAY_KEYWORDS:
            result[key] = _normalise_schema_array(
                item,
                label=key,
                definitions=definitions,
                reference_stack=reference_stack,
                ordered=key == "prefixItems",
            )
        elif key == "discriminator":
            result[key] = _normalise_discriminator(
                item,
                definitions=definitions,
                reference_stack=reference_stack,
            )
        elif key in _STRING_KEYWORDS:
            if type(item) is not str:
                raise SchemaFingerprintError(f"{key} must be a string")
            result[key] = item
        elif key in _NON_NEGATIVE_INTEGER_KEYWORDS:
            if type(item) is not int or item < 0:
                raise SchemaFingerprintError(f"{key} must be a non-negative integer")
            result[key] = item
        elif key in _NUMERIC_KEYWORDS:
            result[key] = _normalise_number(item, key)
        elif key in _BOOLEAN_KEYWORDS:
            if type(item) is not bool:
                raise SchemaFingerprintError(f"{key} must be a boolean")
            result[key] = item
        else:
            raise SchemaFingerprintError(f"unsupported JSON Schema keyword: {key}")
    return result


def _normalise_reference(
    reference: object,
    *,
    definitions: Mapping[str, object],
    reference_stack: tuple[str, ...],
) -> SemanticNode:
    if type(reference) is not str:
        raise SchemaFingerprintError("$ref must be a string")
    prefix = "#/$defs/" if reference.startswith("#/$defs/") else "#/definitions/"
    if not reference.startswith(prefix):
        raise SchemaFingerprintError("only local top-level definition references are supported")
    encoded_name = reference[len(prefix) :]
    if not encoded_name or "/" in encoded_name:
        raise SchemaFingerprintError("$ref must address one top-level definition")
    name = encoded_name.replace("~1", "/").replace("~0", "~")
    if name in reference_stack:
        cycle = " -> ".join((*reference_stack, name))
        raise SchemaFingerprintError(f"cyclic schema reference is unsupported: {cycle}")
    try:
        target = definitions[name]
    except KeyError as exc:
        raise SchemaFingerprintError(f"unresolvable schema reference: {reference}") from exc
    return _normalise_schema(
        target,
        definitions=definitions,
        reference_stack=(*reference_stack, name),
    )


def _normalise_type(value: object) -> SemanticNode:
    if type(value) is str:
        if value not in _JSON_SCHEMA_TYPES:
            raise SchemaFingerprintError(f"unsupported JSON Schema type: {value}")
        return value
    values = _sorted_unique_strings(value, "type")
    if not values:
        raise SchemaFingerprintError("type array cannot be empty")
    string_values = cast(list[str], values)
    unknown = sorted(set(string_values) - _JSON_SCHEMA_TYPES)
    if unknown:
        raise SchemaFingerprintError(f"unsupported JSON Schema types: {', '.join(unknown)}")
    return string_values[0] if len(string_values) == 1 else string_values


def _normalise_enum(value: object) -> list[SemanticNode]:
    values = _require_sequence(value, "enum")
    if not values:
        raise SchemaFingerprintError("enum cannot be empty")
    normalised = [_normalise_literal(item) for item in values]
    normalised.sort(key=_semantic_bytes)
    encodings = [_semantic_bytes(item) for item in normalised]
    if len(set(encodings)) != len(encodings):
        raise SchemaFingerprintError("enum contains duplicate semantic values")
    return normalised


def _normalise_schema_mapping(
    value: object,
    *,
    label: str,
    definitions: Mapping[str, object],
    reference_stack: tuple[str, ...],
) -> dict[str, SemanticNode]:
    mapping = _require_mapping(value, label)
    return {
        key: _normalise_schema(
            mapping[key],
            definitions=definitions,
            reference_stack=reference_stack,
        )
        for key in sorted(mapping)
    }


def _normalise_schema_array(
    value: object,
    *,
    label: str,
    definitions: Mapping[str, object],
    reference_stack: tuple[str, ...],
    ordered: bool,
) -> list[SemanticNode]:
    values = _require_sequence(value, label)
    if not values:
        raise SchemaFingerprintError(f"{label} cannot be empty")
    normalised = [
        _normalise_schema(
            item,
            definitions=definitions,
            reference_stack=reference_stack,
        )
        for item in values
    ]
    if not ordered:
        normalised.sort(key=_semantic_bytes)
    return normalised


def _normalise_dependent_required(value: object) -> dict[str, SemanticNode]:
    mapping = _require_mapping(value, "dependentRequired")
    return {
        key: _sorted_unique_strings(mapping[key], f"dependentRequired[{key!r}]")
        for key in sorted(mapping)
    }


def _normalise_discriminator(
    value: object,
    *,
    definitions: Mapping[str, object],
    reference_stack: tuple[str, ...],
) -> dict[str, SemanticNode]:
    mapping = _require_mapping(value, "discriminator")
    unknown = sorted(set(mapping) - {"mapping", "propertyName"})
    if unknown:
        raise SchemaFingerprintError(f"unsupported discriminator keys: {', '.join(unknown)}")
    property_name = mapping.get("propertyName")
    if type(property_name) is not str or not property_name:
        raise SchemaFingerprintError("discriminator propertyName must be a non-empty string")
    result: dict[str, SemanticNode] = {"propertyName": property_name}
    raw_targets = mapping.get("mapping")
    if raw_targets is not None:
        targets = _require_mapping(raw_targets, "discriminator mapping")
        result["mapping"] = {
            key: _normalise_reference(
                targets[key],
                definitions=definitions,
                reference_stack=reference_stack,
            )
            for key in sorted(targets)
        }
    return result


def _normalise_literal(value: object) -> SemanticNode:
    if value is None or type(value) in {bool, str}:
        return cast(None | bool | str, value)
    if type(value) in {int, float}:
        return _normalise_number(value, "JSON literal")
    if type(value) is list:
        return {"$array": [_normalise_literal(item) for item in cast(list[object], value)]}
    if type(value) is dict:
        mapping = _require_mapping(value, "JSON literal object")
        return {
            "$object": [
                {"key": key, "value": _normalise_literal(mapping[key])} for key in sorted(mapping)
            ]
        }
    raise SchemaFingerprintError(f"unsupported JSON literal type: {type(value).__name__}")


def _normalise_number(value: object, label: str) -> dict[str, JSONValue]:
    if type(value) is int:
        decimal = Decimal(value)
    elif type(value) is float:
        number = value
        if not math.isfinite(number):
            raise SchemaFingerprintError(f"{label} must be finite")
        decimal = Decimal(str(number))
    else:
        raise SchemaFingerprintError(f"{label} must be a JSON number")
    return {"$number": _decimal_text(decimal)}


def _decimal_text(value: Decimal) -> str:
    sign, raw_digits, exponent = value.as_tuple()
    if not isinstance(exponent, int):
        raise SchemaFingerprintError("schema numbers must be finite")
    digits = list(raw_digits)
    if not digits or not any(digits):
        return "0"
    while digits[-1] == 0:
        digits.pop()
        exponent += 1
    coefficient = "".join(str(digit) for digit in digits)
    return f"{'-' if sign else ''}{coefficient}e{exponent}"


def _sorted_unique_strings(value: object, label: str) -> list[SemanticNode]:
    values = _require_sequence(value, label)
    if not all(type(item) is str for item in values):
        raise SchemaFingerprintError(f"{label} must contain only strings")
    strings = sorted(cast(Sequence[str], values))
    if len(set(strings)) != len(strings):
        raise SchemaFingerprintError(f"{label} contains duplicate values")
    return cast(list[SemanticNode], strings)


def _require_schema(value: object, label: str) -> None:
    if type(value) not in {dict, bool}:
        raise SchemaFingerprintError(f"{label} must be an object or boolean schema")


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise SchemaFingerprintError(f"{label} must be an object")
    mapping = cast(dict[object, object], value)
    if not all(type(key) is str for key in mapping):
        raise SchemaFingerprintError(f"{label} keys must be strings")
    return cast(Mapping[str, object], mapping)


def _require_sequence(value: object, label: str) -> list[object]:
    if type(value) is not list:
        raise SchemaFingerprintError(f"{label} must be an array")
    return cast(list[object], value)


def _semantic_bytes(value: SemanticNode) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SchemaFingerprintError(f"duplicate JSON key in schema contract catalogue: {key}")
        result[key] = value
    return result


def _require_exact_mapping(
    value: object,
    *,
    required: set[str],
    label: str,
) -> Mapping[str, object]:
    mapping = _require_mapping(value, label)
    actual = set(mapping)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        raise SchemaFingerprintError(f"{label} has invalid fields: {'; '.join(details)}")
    return mapping


def _non_empty_string(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise SchemaFingerprintError(f"{label} must be a non-empty string")
    return value


def _sha256_string(value: object, label: str) -> str:
    digest = _non_empty_string(value, label)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise SchemaFingerprintError(f"{label} must be a lowercase SHA-256")
    return digest
