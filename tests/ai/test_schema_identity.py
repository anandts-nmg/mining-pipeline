from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from buduunkhad.ai.contracts import (
    AIRequest,
    DocumentExtraction,
    FeatureCritique,
    PageLocator,
    PromptIdentity,
    ProviderConfiguration,
    SchemaIdentity,
    SourceReference,
    TaskType,
)
from buduunkhad.ai.fingerprint import request_fingerprint, schema_identity_fingerprint_value
from buduunkhad.ai.prompts import (
    PromptRegistry,
    PromptSchemaMismatchError,
    default_schema_registry,
)
from buduunkhad.ai.schema_identity import (
    LEGACY_SCHEMA_FINGERPRINT_ALGORITHM,
    SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
    SchemaFingerprintError,
    load_packaged_schema_contracts,
    semantic_schema_document,
    semantic_schema_sha256,
)
from buduunkhad.geospatial_ai.schemas import (
    FeatureCritiqueBatch,
    GeologicalFeatureProposalBatch,
    LegendExtraction,
    MapFeatureInterpretation,
)

DOCUMENT_SCHEMA_ID = "buduunkhad.ai.document_extraction"
DOCUMENT_SCHEMA_VERSION = "1.0.0"
DOCUMENT_SEMANTIC_SHA256 = "45f056f872672825181c98ce57d2d6cd036296bb11256b980e4109477d11c490"
DOCUMENT_LEGACY_SHA256 = "07648e6fb2ab8366064869571d8e4d0169b2121d049cb88b4af4ed70f6323f5f"


def _fixture(name: str) -> object:
    path = Path(__file__).parents[1] / "fixtures" / "schema_identity" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _contract_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["a", "b"]},
            "name": {"type": "string", "minLength": 1},
            "nested": {
                "type": "object",
                "properties": {"code": {"type": "integer", "minimum": 0}},
                "required": ["code"],
                "additionalProperties": False,
            },
            "values": {"type": "array", "items": {"type": "number"}, "minItems": 1},
        },
        "required": ["kind", "name", "nested", "values"],
        "additionalProperties": False,
    }


def _changed(path: tuple[str, ...], value: object) -> dict[str, object]:
    schema = deepcopy(_contract_schema())
    target: dict[str, object] = schema
    for key in path[:-1]:
        nested = target[key]
        assert isinstance(nested, dict)
        target = nested
    target[path[-1]] = value
    return schema


def _legacy_document_identity() -> SchemaIdentity:
    return SchemaIdentity(
        schema_id=DOCUMENT_SCHEMA_ID,
        version=DOCUMENT_SCHEMA_VERSION,
        sha256=DOCUMENT_LEGACY_SHA256,
    )


def test_document_extraction_has_the_checked_semantic_identity_on_every_supported_runtime() -> None:
    # This exact assertion executes under both Pydantic 2.7.4 minimum-dependency jobs and
    # the current dependency jobs.  The raw generator tree may differ; its semantic identity may not.
    assert semantic_schema_sha256(DocumentExtraction.model_json_schema()) == (
        DOCUMENT_SEMANTIC_SHA256
    )
    registration = default_schema_registry().resolve(
        SchemaIdentity(
            schema_id=DOCUMENT_SCHEMA_ID,
            version=DOCUMENT_SCHEMA_VERSION,
            sha256=DOCUMENT_SEMANTIC_SHA256,
            fingerprint_algorithm=SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
        )
    )
    assert registration.output_model is DocumentExtraction


def test_static_pydantic_style_representations_have_one_semantic_identity() -> None:
    current = _fixture("representational_current.json")
    older_style = _fixture("representational_pydantic_2_7_style.json")
    assert semantic_schema_document(current) == semantic_schema_document(older_style)
    assert semantic_schema_sha256(current) == semantic_schema_sha256(older_style)


def test_definition_order_generated_titles_and_internal_ref_names_are_non_semantic() -> None:
    left = {
        "$defs": {
            "FirstName": {"title": "First", "type": "string", "minLength": 1},
            "Unused": {"type": "number"},
        },
        "title": "C:/checkout/generated/Root",
        "type": "object",
        "properties": {"value": {"$ref": "#/$defs/FirstName"}},
        "required": ["value"],
        "additionalProperties": False,
    }
    right = {
        "additionalProperties": False,
        "required": ["value"],
        "properties": {"value": {"$ref": "#/$defs/RenamedByFramework"}},
        "type": "object",
        "title": "/tmp/other/generated/Root",
        "$defs": {
            "UnusedMoved": {"type": "boolean"},
            "RenamedByFramework": {
                "description": "Different framework annotation.",
                "minLength": 1,
                "type": "string",
            },
        },
    }
    assert semantic_schema_sha256(left) == semantic_schema_sha256(right)


def test_discriminator_and_union_identity_is_independent_of_ref_and_branch_order() -> None:
    left = {
        "$defs": {
            "A": {
                "type": "object",
                "properties": {"kind": {"const": "a"}, "value": {"type": "string"}},
                "required": ["kind", "value"],
            },
            "B": {
                "type": "object",
                "properties": {"kind": {"const": "b"}, "value": {"type": "integer"}},
                "required": ["kind", "value"],
            },
        },
        "oneOf": [{"$ref": "#/$defs/A"}, {"$ref": "#/$defs/B"}],
        "discriminator": {
            "propertyName": "kind",
            "mapping": {"a": "#/$defs/A", "b": "#/$defs/B"},
        },
    }
    right = {
        "$defs": {
            "Bee": deepcopy(left["$defs"]["B"]),  # type: ignore[index]
            "Aye": deepcopy(left["$defs"]["A"]),  # type: ignore[index]
        },
        "discriminator": {
            "mapping": {"b": "#/$defs/Bee", "a": "#/$defs/Aye"},
            "propertyName": "kind",
        },
        "oneOf": [{"$ref": "#/$defs/Bee"}, {"$ref": "#/$defs/Aye"}],
    }
    assert semantic_schema_sha256(left) == semantic_schema_sha256(right)
    wrong_mapping = deepcopy(right)
    wrong_mapping["discriminator"]["mapping"]["a"] = "#/$defs/Bee"  # type: ignore[index]
    assert semantic_schema_sha256(left) != semantic_schema_sha256(wrong_mapping)


@pytest.mark.parametrize(
    "changed",
    [
        pytest.param(
            _changed(("properties", "added"), {"type": "string"}),
            id="field-addition",
        ),
        pytest.param(
            {
                **_contract_schema(),
                "properties": {
                    key: value
                    for key, value in _contract_schema()["properties"].items()  # type: ignore[union-attr]
                    if key != "name"
                },
                "required": ["kind", "nested", "values"],
            },
            id="field-removal",
        ),
        pytest.param(
            {**_contract_schema(), "required": ["kind", "nested", "values"]},
            id="required-to-optional",
        ),
        pytest.param(_changed(("properties", "name", "type"), "integer"), id="type"),
        pytest.param(
            _changed(
                ("properties", "name"),
                {"anyOf": [{"type": "string"}, {"type": "null"}], "minLength": 1},
            ),
            id="nullability",
        ),
        pytest.param(
            _changed(("properties", "kind", "enum"), ["a", "b", "c"]),
            id="enum",
        ),
        pytest.param(
            _changed(
                ("properties", "nested", "properties", "code", "maximum"),
                10,
            ),
            id="nested-object",
        ),
        pytest.param(
            _changed(("properties", "values", "items"), {"type": "string"}),
            id="array-items",
        ),
        pytest.param(
            _changed(("properties", "name", "minLength"), 2),
            id="relevant-constraint",
        ),
        pytest.param(
            _changed(("properties", "name", "pattern"), "^[A-Z]+$"),
            id="pattern-constraint",
        ),
        pytest.param(
            {**_contract_schema(), "additionalProperties": True},
            id="additional-properties",
        ),
    ],
)
def test_meaningful_contract_changes_change_the_fingerprint(changed: dict[str, object]) -> None:
    assert semantic_schema_sha256(changed) != semantic_schema_sha256(_contract_schema())


def test_annotations_defaults_key_order_and_unordered_arrays_do_not_change_identity() -> None:
    left = _contract_schema()
    right = deepcopy(left)
    right["title"] = "Generated title changed"
    right["description"] = "Whitespace and wording changed."
    right["default"] = {"framework": "metadata"}
    right["required"] = list(reversed(right["required"]))  # type: ignore[arg-type]
    right["properties"] = dict(reversed(list(right["properties"].items())))  # type: ignore[union-attr]
    assert semantic_schema_sha256(left) == semantic_schema_sha256(right)
    assert len({semantic_schema_sha256(right) for _ in range(20)}) == 1


def test_boolean_and_composition_schemas_have_explicit_semantics() -> None:
    assert semantic_schema_document(True) is True
    assert semantic_schema_sha256(True) != semantic_schema_sha256(False)
    assert semantic_schema_sha256({"type": ["string"]}) == semantic_schema_sha256(
        {"type": "string"}
    )
    assert semantic_schema_sha256({"allOf": [{"type": "string"}]}) == semantic_schema_sha256(
        {"type": "string"}
    )
    left = {
        "allOf": [{"type": "object"}, {"required": ["value"]}],
        "anyOf": [{"type": "string"}, {"type": "integer"}],
        "oneOf": [{"const": "a"}, {"const": "b"}],
    }
    right = {
        "oneOf": [{"enum": ["b"]}, {"enum": ["a"]}],
        "anyOf": [{"type": "integer"}, {"type": "string"}],
        "allOf": [{"required": ["value"]}, {"type": "object"}],
    }
    assert semantic_schema_sha256(left) == semantic_schema_sha256(right)


def test_matching_const_and_enum_reduce_to_the_constant() -> None:
    constant_only = {"type": "string", "const": "a"}
    expected = semantic_schema_sha256(constant_only)
    assert semantic_schema_sha256({"type": "string", "enum": ["a"]}) == expected
    assert semantic_schema_sha256({"type": "string", "const": "a", "enum": ["a"]}) == expected
    assert semantic_schema_sha256({"type": "string", "const": "a", "enum": ["a", "b"]}) == expected
    # The conjunctive reduction keeps only the constant — no enum alternative survives.
    assert semantic_schema_document({"type": "string", "const": "a", "enum": ["a", "b"]}) == {
        "const": "a",
        "type": "string",
    }
    assert semantic_schema_sha256({"const": 1, "enum": [1.0]}) == semantic_schema_sha256(
        {"const": 1}
    )


@pytest.mark.parametrize(
    ("schema", "message"),
    [
        pytest.param({"const": "c", "enum": ["a", "b"]}, "member", id="not-a-member"),
        pytest.param({"const": True, "enum": [1]}, "member", id="bool-is-not-number"),
        pytest.param({"const": "1", "enum": [1]}, "member", id="string-is-not-number"),
        pytest.param({"const": 2, "enum": [1.0, 3]}, "member", id="number-outside-enum"),
        pytest.param({"const": "a", "enum": []}, "empty", id="empty-enum"),
        pytest.param({"const": "a", "enum": ["a", "a"]}, "duplicate", id="duplicate-enum"),
    ],
)
def test_conflicting_or_malformed_const_enum_pairs_fail_closed(
    schema: object,
    message: str,
) -> None:
    with pytest.raises(SchemaFingerprintError, match=message):
        semantic_schema_sha256(schema)


def _with_pydantic_2_7_style_literals(node: object) -> object:
    """Synthesize the const-plus-singleton-enum dual emission for every constant node."""

    if isinstance(node, dict):
        rebuilt = {key: _with_pydantic_2_7_style_literals(item) for key, item in node.items()}
        if "const" in rebuilt and "enum" not in rebuilt:
            rebuilt["enum"] = [deepcopy(rebuilt["const"])]
        return rebuilt
    if isinstance(node, list):
        return [_with_pydantic_2_7_style_literals(item) for item in node]
    return node


def _count_const_enum_pairs(node: object) -> int:
    if isinstance(node, dict):
        total = sum(_count_const_enum_pairs(item) for item in node.values())
        return total + (1 if "const" in node and "enum" in node else 0)
    if isinstance(node, list):
        return sum(_count_const_enum_pairs(item) for item in node)
    return 0


def test_synthetic_dual_literal_emission_matches_every_checked_contract() -> None:
    models: dict[str, type[BaseModel]] = {
        "buduunkhad.ai.document_extraction": DocumentExtraction,
        "buduunkhad.ai.feature_critique": FeatureCritique,
        "buduunkhad.ai.legend_extraction": LegendExtraction,
        "buduunkhad.ai.map_feature_interpretation": MapFeatureInterpretation,
        "buduunkhad.ai.geological_feature_proposal_batch": GeologicalFeatureProposalBatch,
        "buduunkhad.ai.feature_critique_batch": FeatureCritiqueBatch,
    }
    dual_nodes = 0
    for (schema_id, _version), record in load_packaged_schema_contracts().items():
        dual = _with_pydantic_2_7_style_literals(models[schema_id].model_json_schema())
        # Older Pydantic already emits the pairs; on newer Pydantic the transform adds them.
        dual_nodes += _count_const_enum_pairs(dual)
        assert semantic_schema_sha256(dual) == record.sha256
    assert dual_nodes  # the dual-emission representation class must actually be exercised


def test_default_schema_registry_constructs_under_synthetic_dual_emission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dual = _with_pydantic_2_7_style_literals(DocumentExtraction.model_json_schema())
    monkeypatch.setattr(
        DocumentExtraction,
        "model_json_schema",
        classmethod(lambda cls, **kwargs: deepcopy(dual)),
    )
    registration = default_schema_registry().resolve(
        SchemaIdentity(
            schema_id=DOCUMENT_SCHEMA_ID,
            version=DOCUMENT_SCHEMA_VERSION,
            sha256=DOCUMENT_SEMANTIC_SHA256,
            fingerprint_algorithm=SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
        )
    )
    assert registration.output_model is DocumentExtraction
    assert registration.accepts(_legacy_document_identity())


@pytest.mark.parametrize(
    ("schema", "message"),
    [
        ([], "schema root must be an object"),
        ({"$defs": {}, "definitions": {}}, "both"),
        ({"$ref": "https://example.invalid/schema"}, "only local"),
        ({"$ref": "#/$defs/Missing", "$defs": {}}, "unresolvable"),
        (
            {"$ref": "#/$defs/Recursive", "$defs": {"Recursive": {"$ref": "#/$defs/Recursive"}}},
            "cyclic",
        ),
        ({"type": "string", "unknownValidationKeyword": 1}, "unsupported"),
        ({"type": "framework-object"}, "unsupported JSON Schema type"),
        ({"required": ["a", "a"]}, "duplicate"),
        ({"enum": [1, 1.0]}, "duplicate"),
        ({"properties": {"x": {"$defs": {"Nested": {"type": "string"}}}}}, "nested"),
    ],
)
def test_malformed_or_ambiguous_schema_constructs_fail_closed(
    schema: object,
    message: str,
) -> None:
    with pytest.raises(SchemaFingerprintError, match=message):
        semantic_schema_sha256(schema)


def test_exact_legacy_identity_resolves_but_unknown_or_cross_bound_aliases_fail() -> None:
    schemas = default_schema_registry()
    registration = schemas.resolve(_legacy_document_identity())
    assert registration.identity.sha256 == DOCUMENT_SEMANTIC_SHA256
    assert registration.accepts(_legacy_document_identity())

    with pytest.raises(PromptSchemaMismatchError, match="hash mismatch"):
        schemas.resolve(_legacy_document_identity().model_copy(update={"sha256": "f" * 64}))
    with pytest.raises(PromptSchemaMismatchError, match="not approved"):
        schemas.resolve(
            _legacy_document_identity().model_copy(update={"schema_id": "wrong.schema"})
        )
    with pytest.raises(PromptSchemaMismatchError, match="not approved"):
        schemas.resolve(_legacy_document_identity().model_copy(update={"version": "2.0.0"}))


def test_algorithm_confusion_and_downgrade_fail_closed() -> None:
    schemas = default_schema_registry()
    semantic_as_legacy = SchemaIdentity(
        schema_id=DOCUMENT_SCHEMA_ID,
        version=DOCUMENT_SCHEMA_VERSION,
        sha256=DOCUMENT_SEMANTIC_SHA256,
        fingerprint_algorithm=LEGACY_SCHEMA_FINGERPRINT_ALGORITHM,
    )
    legacy_as_semantic = SchemaIdentity(
        schema_id=DOCUMENT_SCHEMA_ID,
        version=DOCUMENT_SCHEMA_VERSION,
        sha256=DOCUMENT_LEGACY_SHA256,
        fingerprint_algorithm=SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
    )
    with pytest.raises(PromptSchemaMismatchError, match="hash mismatch"):
        schemas.resolve(semantic_as_legacy)
    with pytest.raises(PromptSchemaMismatchError, match="hash mismatch"):
        schemas.resolve(legacy_as_semantic)
    with pytest.raises(ValidationError, match="fingerprint_algorithm"):
        SchemaIdentity.model_validate(
            {
                "schema_id": DOCUMENT_SCHEMA_ID,
                "version": DOCUMENT_SCHEMA_VERSION,
                "sha256": DOCUMENT_SEMANTIC_SHA256,
                "fingerprint_algorithm": "unknown-schema-algorithm",
            }
        )


def test_legacy_prompt_and_request_fingerprints_remain_reloadable_without_reinterpretation() -> (
    None
):
    schemas = default_schema_registry()
    prompts = PromptRegistry.load_packaged(schema_registry=schemas)
    prompt = prompts.get("fixture.document-extraction", "1.0.0")
    assert prompt.output_schema == _legacy_document_identity()
    assert schema_identity_fingerprint_value(prompt.output_schema) == {
        "schema_id": DOCUMENT_SCHEMA_ID,
        "version": DOCUMENT_SCHEMA_VERSION,
        "sha256": DOCUMENT_LEGACY_SHA256,
    }
    request = AIRequest(
        request_id="legacy-request",
        job_id="legacy-job",
        run_id="legacy-run",
        phase_id="00",
        task_type=TaskType.DOCUMENT_EXTRACTION,
        created_at=datetime(2026, 7, 16, tzinfo=UTC),
        source_references=(
            SourceReference(
                asset_id="synthetic-document",
                sha256="a" * 64,
                locators=(PageLocator(page_number=1),),
            ),
        ),
        prompt=PromptIdentity(prompt_id="fixture", version="1.0.0", sha256="b" * 64),
        output_schema=prompt.output_schema,
        provider=ProviderConfiguration(provider="disabled", model="not-selected", parameters=()),
        interpretation_parameters=(),
    )
    reloaded = AIRequest.model_validate_json(request.model_dump_json())
    assert request_fingerprint(reloaded) == request_fingerprint(request)
    semantic = request.model_copy(
        update={"output_schema": schemas.resolve(prompt.output_schema).identity}
    )
    assert request_fingerprint(semantic) != request_fingerprint(request)
