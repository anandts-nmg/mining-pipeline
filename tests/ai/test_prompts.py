from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from buduunkhad.ai.contracts import (
    DocumentExtraction,
    FrozenModel,
    PromptIdentity,
    SchemaIdentity,
    TaskType,
)
from buduunkhad.ai.fingerprint import sha256_file
from buduunkhad.ai.prompts import (
    PromptComponentRegistration,
    PromptDeprecatedError,
    PromptHashMismatchError,
    PromptRegistration,
    PromptRegistry,
    PromptRegistryError,
    PromptSchemaMismatchError,
    PromptStatus,
    PromptVersionDriftError,
    SchemaRegistration,
    SchemaRegistry,
    compute_prompt_hash,
    default_schema_registry,
)


def test_packaged_prompt_registry_loads_immutable_text() -> None:
    registry = PromptRegistry.load_packaged(schema_registry=default_schema_registry())
    prompt = registry.get("fixture.document-extraction", "1.0.0")
    assert prompt.task_type is TaskType.DOCUMENT_EXTRACTION
    assert prompt.status is PromptStatus.ENABLED
    with pytest.raises(AttributeError):
        prompt.components.append(prompt.components[0])  # ty: ignore[unresolved-attribute]
    with pytest.raises(ValidationError, match="frozen"):
        prompt.components[0].text = "mutated"  # ty: ignore[invalid-assignment]


def test_publicly_constructed_prompt_registry_is_not_a_trust_boundary() -> None:
    prompt = PromptRegistry.load_packaged(schema_registry=default_schema_registry()).get(
        "fixture.document-extraction", "1.0.0"
    )
    with pytest.raises(PromptRegistryError, match="load or load_packaged"):
        PromptRegistry((prompt,))


def test_resolved_prompt_rejects_unverified_text() -> None:
    prompt = PromptRegistry.load_packaged(schema_registry=default_schema_registry()).get(
        "fixture.document-extraction", "1.0.0"
    )
    component = prompt.components[0].model_copy(update={"text": "tampered"})
    with pytest.raises(ValidationError, match="component hash mismatch"):
        prompt.model_copy(update={"components": (component, *prompt.components[1:])})


def _write_registry(
    root: Path,
    *,
    component_text: str = "fixture",
    status: PromptStatus = PromptStatus.ENABLED,
    schema_identity: SchemaIdentity | None = None,
    write_lock: bool = True,
    lock_from: PromptRegistration | None = None,
    component_path: str = "fixture.txt",
) -> tuple[Path, Path, PromptRegistration]:
    schema = schema_identity or _document_schema_identity()
    component = root / "fixture.txt"
    component.write_text(component_text, encoding="utf-8")
    registration = PromptRegistration(
        prompt_id="fixture.test",
        version="1.0.0",
        task_type=TaskType.DOCUMENT_EXTRACTION,
        components=(
            PromptComponentRegistration(
                name="system",
                path=component_path,
                sha256=sha256_file(component),
            ),
        ),
        output_schema=schema,
        prompt_sha256="a" * 64,
        status=status,
    )
    registration = registration.model_copy(
        update={"prompt_sha256": compute_prompt_hash(registration)}
    )
    registry_path = root / "registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(
            {
                "registry_version": "1.0.0",
                "prompts": [registration.model_dump(mode="json")],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    lock_path = root / "prompt-lock.yaml"
    if write_lock:
        locked = lock_from or registration
        lock_path.write_text(
            yaml.safe_dump(
                {
                    "lock_version": "1.0.0",
                    "history": [
                        {
                            "prompt_id": locked.prompt_id,
                            "version": locked.version,
                            "prompt_sha256": locked.prompt_sha256,
                            "output_schema": locked.output_schema.model_dump(mode="json"),
                            "component_sha256": [
                                component.model_dump(mode="json") for component in locked.components
                            ],
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
    return registry_path, lock_path, registration


def _document_schema_identity() -> SchemaIdentity:
    registration = SchemaRegistration.for_model(
        DocumentExtraction,
        schema_id="buduunkhad.ai.document_extraction",
        version="1.0.0",
    )
    return registration.identity


def test_same_version_drift_fails_automatically(tmp_path: Path) -> None:
    old_root = tmp_path / "old"
    new_root = tmp_path / "new"
    old_root.mkdir()
    new_root.mkdir()
    _, _, old = _write_registry(old_root, component_text="old")
    path, lock, _ = _write_registry(new_root, component_text="changed", lock_from=old)
    with pytest.raises(PromptVersionDriftError, match="lock/history"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_registry_resolves_exact_identity_not_self_created_hash() -> None:
    registry = PromptRegistry.load_packaged(schema_registry=default_schema_registry())
    prompt = registry.get("fixture.document-extraction", "1.0.0")
    assert registry.resolve(prompt.identity) == prompt
    forged = prompt.identity.model_copy(update={"sha256": "f" * 64})
    with pytest.raises(PromptHashMismatchError, match="identity hash mismatch"):
        registry.resolve(forged)


def test_resolved_text_is_stable_after_source_file_changes(tmp_path: Path) -> None:
    path, lock, _ = _write_registry(tmp_path, component_text="verified")
    registry = PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)
    prompt = registry.get("fixture.test", "1.0.0")
    (tmp_path / "fixture.txt").write_text("changed later", encoding="utf-8")
    assert prompt.components[0].text == "verified"


def test_wrong_schema_with_recomputed_prompt_hash_fails(tmp_path: Path) -> None:
    wrong = SchemaIdentity(schema_id="wrong.schema", version="1.0.0", sha256="f" * 64)
    path, lock, _ = _write_registry(tmp_path, schema_identity=wrong)
    with pytest.raises(PromptSchemaMismatchError, match="not approved"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_wrong_current_schema_model_fails(tmp_path: Path) -> None:
    class DifferentOutput(FrozenModel):
        different: str

    path, lock, _ = _write_registry(tmp_path, schema_identity=_document_schema_identity())
    wrong_current = SchemaRegistry(
        (
            SchemaRegistration.for_model(
                DifferentOutput,
                schema_id="buduunkhad.ai.document_extraction",
                version="1.0.0",
            ),
        )
    )
    with pytest.raises(PromptSchemaMismatchError, match="hash mismatch"):
        PromptRegistry.load(path, schema_registry=wrong_current, lock_path=lock)


def test_missing_lock_history_fails_closed(tmp_path: Path) -> None:
    path, lock, _ = _write_registry(tmp_path, write_lock=False)
    with pytest.raises(PromptRegistryError, match="cannot read prompt lock"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_existing_lock_without_prompt_history_entry_fails_closed(tmp_path: Path) -> None:
    path, lock, _ = _write_registry(tmp_path)
    values = yaml.safe_load(lock.read_text(encoding="utf-8"))
    values["history"][0]["prompt_id"] = "fixture.other"
    lock.write_text(yaml.safe_dump(values, sort_keys=False), encoding="utf-8")
    with pytest.raises(PromptVersionDriftError, match="no lock/history entry"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_deprecated_prompt_rejects_new_selection_but_resolves_locked_history(
    tmp_path: Path,
) -> None:
    path, lock, registration = _write_registry(tmp_path, status=PromptStatus.DEPRECATED)
    registry = PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)
    with pytest.raises(PromptDeprecatedError):
        registry.get("fixture.test", "1.0.0")
    identity = PromptIdentity(
        prompt_id=registration.prompt_id,
        version=registration.version,
        sha256=registration.prompt_sha256,
    )
    with pytest.raises(PromptDeprecatedError):
        registry.resolve(identity)
    historical = registry.resolve_historical(identity)
    assert historical.status is PromptStatus.DEPRECATED
    assert historical.identity == identity


def test_duplicate_yaml_mapping_key_fails(tmp_path: Path) -> None:
    path, lock, _ = _write_registry(tmp_path)
    path.write_text("registry_version: 1.0.0\nregistry_version: 1.0.0\nprompts: []\n")
    with pytest.raises(PromptRegistryError, match="duplicate key"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


@pytest.mark.parametrize(
    ("target", "version"),
    [
        ("registry", "2.0.0"),
        ("registry", "1.1.0"),
        ("lock", "2.0.0"),
        ("lock", "1.0.1"),
    ],
)
def test_unknown_registry_and_lock_format_versions_fail(
    tmp_path: Path, target: str, version: str
) -> None:
    path, lock, _ = _write_registry(tmp_path)
    selected = path if target == "registry" else lock
    key = "registry_version" if target == "registry" else "lock_version"
    values = yaml.safe_load(selected.read_text(encoding="utf-8"))
    values[key] = version
    selected.write_text(yaml.safe_dump(values, sort_keys=False), encoding="utf-8")
    with pytest.raises(PromptRegistryError, match=key):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


@pytest.mark.parametrize("target", ["registry", "lock", "component"])
def test_invalid_utf8_is_wrapped_in_prompt_domain_error(tmp_path: Path, target: str) -> None:
    path, lock, _ = _write_registry(tmp_path)
    selected = {
        "registry": path,
        "lock": lock,
        "component": tmp_path / "fixture.txt",
    }[target]
    selected.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(PromptRegistryError, match="cannot read|invalid"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_malformed_yaml_fails_loudly(tmp_path: Path) -> None:
    path, lock, _ = _write_registry(tmp_path)
    path.write_text("registry_version: [unterminated\n", encoding="utf-8")
    with pytest.raises(PromptRegistryError, match="invalid prompt registry"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_duplicate_prompt_id_and_version_fails(tmp_path: Path) -> None:
    path, lock, registration = _write_registry(tmp_path)
    path.write_text(
        yaml.safe_dump(
            {
                "registry_version": "1.0.0",
                "prompts": [
                    registration.model_dump(mode="json"),
                    registration.model_dump(mode="json"),
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    with pytest.raises(PromptRegistryError, match="duplicate prompt registration"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_path_traversal_fails(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    path, lock, _ = _write_registry(tmp_path, component_path="../outside.txt")
    with pytest.raises(PromptRegistryError, match="leaves registry root"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_symlink_escape_fails(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-symlink.txt"
    outside.write_text("fixture", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        if sys.platform == "win32":
            pytest.skip(f"symlink creation is unavailable on this Windows host: {exc}")
        pytest.fail(f"Linux CI must support the security-sensitive symlink test: {exc}")
    assert link.is_symlink()
    path, lock, _ = _write_registry(tmp_path, component_path="link.txt")
    with pytest.raises(PromptRegistryError, match="leaves registry root"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_missing_component_fails_loudly(tmp_path: Path) -> None:
    path, lock, _ = _write_registry(tmp_path, component_path="missing.txt")
    with pytest.raises(PromptRegistryError, match="component not found"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)


def test_component_hash_mismatch_fails(tmp_path: Path) -> None:
    path, lock, _ = _write_registry(tmp_path)
    (tmp_path / "fixture.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(PromptHashMismatchError, match="component hash mismatch"):
        PromptRegistry.load(path, schema_registry=default_schema_registry(), lock_path=lock)
