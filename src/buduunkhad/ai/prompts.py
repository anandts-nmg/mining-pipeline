"""Immutable, schema-bound, lock-verified prompt registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TypeVar

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from buduunkhad.ai.contracts import (
    DocumentExtraction,
    FeatureCritique,
    FrozenModel,
    NonEmptyStr,
    PromptIdentity,
    SchemaIdentity,
    SemanticVersion,
    Sha256,
    TaskType,
)
from buduunkhad.ai.fingerprint import (
    schema_identity_fingerprint_value,
    schema_identity_for_model,
    sha256_bytes,
    sha256_value,
)
from buduunkhad.ai.schema_identity import (
    LEGACY_SCHEMA_FINGERPRINT_ALGORITHM,
    SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
    SchemaContractRecord,
    SchemaFingerprintError,
    load_packaged_schema_contracts,
)


class PromptRegistryError(ValueError):
    """Base class for invalid prompt registrations and selections."""


class PromptHashMismatchError(PromptRegistryError):
    pass


class PromptVersionDriftError(PromptRegistryError):
    pass


class PromptSchemaMismatchError(PromptRegistryError):
    pass


class PromptDeprecatedError(PromptRegistryError):
    pass


class PromptStatus(StrEnum):
    ENABLED = "enabled"
    DEPRECATED = "deprecated"


class PromptComponentRegistration(FrozenModel):
    name: NonEmptyStr
    path: NonEmptyStr
    sha256: Sha256


class PromptRegistration(FrozenModel):
    prompt_id: NonEmptyStr
    version: SemanticVersion
    task_type: TaskType
    components: tuple[PromptComponentRegistration, ...] = Field(min_length=1)
    output_schema: SchemaIdentity
    prompt_sha256: Sha256
    status: PromptStatus


class PromptRegistryFile(FrozenModel):
    registry_version: Literal["1.0.0"]
    prompts: tuple[PromptRegistration, ...]


class PromptLockEntry(FrozenModel):
    prompt_id: NonEmptyStr
    version: SemanticVersion
    prompt_sha256: Sha256
    output_schema: SchemaIdentity
    component_sha256: tuple[PromptComponentRegistration, ...] = Field(min_length=1)


class PromptLockFile(FrozenModel):
    lock_version: Literal["1.0.0"]
    history: tuple[PromptLockEntry, ...] = Field(min_length=1)


class ResolvedPromptComponent(FrozenModel):
    name: NonEmptyStr
    text: str
    sha256: Sha256


class ResolvedPrompt(FrozenModel):
    prompt_id: NonEmptyStr
    version: SemanticVersion
    task_type: TaskType
    components: tuple[ResolvedPromptComponent, ...] = Field(min_length=1)
    output_schema: SchemaIdentity
    prompt_sha256: Sha256
    status: PromptStatus

    @model_validator(mode="after")
    def _verified_content(self) -> ResolvedPrompt:
        names = tuple(component.name for component in self.components)
        if len(set(names)) != len(names):
            raise ValueError("resolved prompt contains duplicate component names")
        for component in self.components:
            actual = sha256_bytes(component.text.encode("utf-8"))
            if actual != component.sha256:
                raise ValueError(f"resolved prompt component hash mismatch: {component.name}")
        actual_prompt_hash = _prompt_content_hash(
            prompt_id=self.prompt_id,
            version=self.version,
            task_type=self.task_type,
            components=tuple((component.name, component.sha256) for component in self.components),
            output_schema=self.output_schema,
        )
        if actual_prompt_hash != self.prompt_sha256:
            raise ValueError("resolved prompt aggregate hash mismatch")
        return self

    @property
    def identity(self) -> PromptIdentity:
        return PromptIdentity(
            prompt_id=self.prompt_id,
            version=self.version,
            sha256=self.prompt_sha256,
        )


@dataclass(frozen=True, slots=True)
class SchemaRegistration:
    identity: SchemaIdentity
    output_model: type[FrozenModel]
    legacy_identities: tuple[SchemaIdentity, ...] = ()

    def __post_init__(self) -> None:
        if self.identity.fingerprint_algorithm != SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM:
            raise PromptSchemaMismatchError(
                "current schema registrations must use semantic identity"
            )
        current = schema_identity_for_model(
            self.output_model,
            schema_id=self.identity.schema_id,
            version=self.identity.version,
        )
        if current != self.identity:
            raise PromptSchemaMismatchError(
                f"schema registration hash is not current: "
                f"{self.identity.schema_id}@{self.identity.version}"
            )
        seen: set[str] = set()
        for legacy in self.legacy_identities:
            if legacy.fingerprint_algorithm != LEGACY_SCHEMA_FINGERPRINT_ALGORITHM:
                raise PromptSchemaMismatchError(
                    "legacy schema aliases must use the legacy algorithm"
                )
            if (legacy.schema_id, legacy.version) != (
                self.identity.schema_id,
                self.identity.version,
            ):
                raise PromptSchemaMismatchError(
                    "legacy schema alias identity does not match registration"
                )
            if legacy.sha256 in seen:
                raise PromptSchemaMismatchError("duplicate legacy schema alias")
            seen.add(legacy.sha256)

    @classmethod
    def for_model(
        cls,
        output_model: type[FrozenModel],
        *,
        schema_id: str,
        version: str,
        expected_sha256: str | None = None,
        legacy_sha256: tuple[str, ...] = (),
    ) -> SchemaRegistration:
        identity = schema_identity_for_model(
            output_model,
            schema_id=schema_id,
            version=version,
        )
        if not isinstance(identity, SchemaIdentity):  # narrow the local import-cycle return type
            raise TypeError("schema identity construction failed")
        if expected_sha256 is not None and identity.sha256 != expected_sha256:
            raise PromptSchemaMismatchError(
                f"semantic schema contract mismatch: {schema_id}@{version}"
            )
        aliases = tuple(
            SchemaIdentity(schema_id=schema_id, version=version, sha256=digest)
            for digest in legacy_sha256
        )
        return cls(identity=identity, output_model=output_model, legacy_identities=aliases)

    def accepts(self, identity: SchemaIdentity) -> bool:
        """Accept only the current identity or an exact registered historical identity."""

        return identity == self.identity or identity in self.legacy_identities


class SchemaRegistry:
    """Approved current schema registrations, immutable after construction."""

    def __init__(self, registrations: tuple[SchemaRegistration, ...]) -> None:
        entries: dict[tuple[str, str], SchemaRegistration] = {}
        for registration in registrations:
            key = (registration.identity.schema_id, registration.identity.version)
            if key in entries:
                raise PromptSchemaMismatchError(f"duplicate schema registration: {key[0]}@{key[1]}")
            current = schema_identity_for_model(
                registration.output_model,
                schema_id=registration.identity.schema_id,
                version=registration.identity.version,
            )
            if current != registration.identity:
                raise PromptSchemaMismatchError(
                    f"schema registration hash is not current: {key[0]}@{key[1]}"
                )
            entries[key] = registration
        self._entries = MappingProxyType(entries)

    def resolve(self, identity: SchemaIdentity) -> SchemaRegistration:
        key = (identity.schema_id, identity.version)
        try:
            registration = self._entries[key]
        except KeyError as exc:
            raise PromptSchemaMismatchError(
                f"schema is not approved: {identity.schema_id}@{identity.version}"
            ) from exc
        if not registration.accepts(identity):
            raise PromptSchemaMismatchError(
                f"schema hash mismatch: {identity.schema_id}@{identity.version}"
            )
        current = schema_identity_for_model(
            registration.output_model,
            schema_id=identity.schema_id,
            version=identity.version,
        )
        if current != registration.identity:
            raise PromptSchemaMismatchError(
                f"schema registration is no longer current: {identity.schema_id}@{identity.version}"
            )
        return registration


def default_schema_registry() -> SchemaRegistry:
    from buduunkhad.geospatial_ai.schemas import (
        FeatureCritiqueBatch,
        GeologicalFeatureProposalBatch,
        LegendExtraction,
        MapFeatureInterpretation,
    )

    try:
        contracts = load_packaged_schema_contracts()
    except SchemaFingerprintError as exc:
        raise PromptSchemaMismatchError("packaged schema identity contracts are invalid") from exc
    registrations = (
        _contract_registration(
            DocumentExtraction,
            schema_id="buduunkhad.ai.document_extraction",
            version="1.0.0",
            contracts=contracts,
        ),
        _contract_registration(
            FeatureCritique,
            schema_id="buduunkhad.ai.feature_critique",
            version="1.0.0",
            contracts=contracts,
        ),
        _contract_registration(
            LegendExtraction,
            schema_id="buduunkhad.ai.legend_extraction",
            version="1.0.0",
            contracts=contracts,
        ),
        _contract_registration(
            MapFeatureInterpretation,
            schema_id="buduunkhad.ai.map_feature_interpretation",
            version="1.0.0",
            contracts=contracts,
        ),
        _contract_registration(
            GeologicalFeatureProposalBatch,
            schema_id="buduunkhad.ai.geological_feature_proposal_batch",
            version="1.0.0",
            contracts=contracts,
        ),
        _contract_registration(
            FeatureCritiqueBatch,
            schema_id="buduunkhad.ai.feature_critique_batch",
            version="1.0.0",
            contracts=contracts,
        ),
    )
    registered_keys = {
        (registration.identity.schema_id, registration.identity.version)
        for registration in registrations
    }
    if set(contracts) != registered_keys:
        raise PromptSchemaMismatchError("packaged schema contract catalogue has unused entries")
    return SchemaRegistry(registrations)


def _contract_registration(
    output_model: type[FrozenModel],
    *,
    schema_id: str,
    version: str,
    contracts: Mapping[tuple[str, str], SchemaContractRecord],
) -> SchemaRegistration:
    try:
        contract = contracts[(schema_id, version)]
    except KeyError as exc:
        raise PromptSchemaMismatchError(
            f"schema has no checked contract: {schema_id}@{version}"
        ) from exc
    return SchemaRegistration.for_model(
        output_model,
        schema_id=schema_id,
        version=version,
        expected_sha256=contract.sha256,
        legacy_sha256=contract.legacy_sha256,
    )


def compute_prompt_hash(registration: PromptRegistration) -> str:
    """Hash prompt content identity; lifecycle status and paths are excluded."""
    return _prompt_content_hash(
        prompt_id=registration.prompt_id,
        version=registration.version,
        task_type=registration.task_type,
        components=tuple(
            (component.name, component.sha256) for component in registration.components
        ),
        output_schema=registration.output_schema,
    )


def _prompt_content_hash(
    *,
    prompt_id: str,
    version: str,
    task_type: TaskType,
    components: tuple[tuple[str, str], ...],
    output_schema: SchemaIdentity,
) -> str:
    return sha256_value(
        {
            "prompt_id": prompt_id,
            "version": version,
            "task_type": task_type,
            "components": tuple(sorted(components, key=lambda item: item[0])),
            "output_schema": schema_identity_fingerprint_value(output_schema),
        }
    )


_VERIFIED_REGISTRY_TOKEN = object()


class PromptRegistry:
    """Verified prompt text indexed by prompt ID and semantic version."""

    def __init__(
        self,
        prompts: tuple[ResolvedPrompt, ...],
        *,
        _verified_token: object | None = None,
    ) -> None:
        if _verified_token is not _VERIFIED_REGISTRY_TOKEN:
            raise PromptRegistryError("PromptRegistry must be created by load or load_packaged")
        entries: dict[tuple[str, str], ResolvedPrompt] = {}
        for prompt in prompts:
            key = (prompt.prompt_id, prompt.version)
            if key in entries:
                raise PromptRegistryError(f"duplicate prompt registration: {key[0]}@{key[1]}")
            entries[key] = prompt
        self._prompts = MappingProxyType(entries)

    @classmethod
    def load(
        cls,
        registry_path: Path,
        *,
        schema_registry: SchemaRegistry,
        lock_path: Path | None = None,
    ) -> PromptRegistry:
        path = Path(registry_path)
        lock = Path(lock_path) if lock_path is not None else path.with_name("prompt-lock.yaml")
        manifest = _load_yaml_model(path, PromptRegistryFile, "prompt registry")
        history = _load_yaml_model(lock, PromptLockFile, "prompt lock")
        lock_entries = _unique_lock_entries(history.history)
        root = path.parent.resolve()
        resolved: list[ResolvedPrompt] = []
        seen: set[tuple[str, str]] = set()
        for registration in manifest.prompts:
            key = (registration.prompt_id, registration.version)
            if key in seen:
                raise PromptRegistryError(f"duplicate prompt registration: {key[0]}@{key[1]}")
            seen.add(key)
            schema_registry.resolve(registration.output_schema)
            components = _resolve_components(root, registration)
            actual_prompt_hash = compute_prompt_hash(registration)
            if actual_prompt_hash != registration.prompt_sha256:
                raise PromptHashMismatchError(
                    f"prompt hash mismatch for {registration.prompt_id}@{registration.version}"
                )
            _verify_lock(registration, lock_entries)
            resolved.append(
                ResolvedPrompt(
                    prompt_id=registration.prompt_id,
                    version=registration.version,
                    task_type=registration.task_type,
                    components=components,
                    output_schema=registration.output_schema,
                    prompt_sha256=registration.prompt_sha256,
                    status=registration.status,
                )
            )
        return cls(tuple(resolved), _verified_token=_VERIFIED_REGISTRY_TOKEN)

    @classmethod
    def load_packaged(cls, *, schema_registry: SchemaRegistry) -> PromptRegistry:
        package_root = resources.files("buduunkhad.prompt_data")
        registry_resource = package_root.joinpath("registry.yaml")
        lock_resource = package_root.joinpath("prompt-lock.yaml")
        with (
            resources.as_file(registry_resource) as registry_path,
            resources.as_file(lock_resource) as lock_path,
        ):
            return cls.load(
                registry_path,
                schema_registry=schema_registry,
                lock_path=lock_path,
            )

    def get(
        self,
        prompt_id: str,
        version: str,
        *,
        allow_deprecated: bool = False,
    ) -> ResolvedPrompt:
        try:
            prompt = self._prompts[(prompt_id, version)]
        except KeyError as exc:
            raise PromptRegistryError(f"prompt not registered: {prompt_id}@{version}") from exc
        if prompt.status is PromptStatus.DEPRECATED and not allow_deprecated:
            raise PromptDeprecatedError(f"prompt is deprecated: {prompt_id}@{version}")
        return prompt

    def resolve(
        self,
        identity: PromptIdentity,
        *,
        allow_deprecated: bool = False,
    ) -> ResolvedPrompt:
        prompt = self.get(
            identity.prompt_id,
            identity.version,
            allow_deprecated=allow_deprecated,
        )
        if prompt.identity != identity:
            raise PromptHashMismatchError(
                f"prompt identity hash mismatch: {identity.prompt_id}@{identity.version}"
            )
        return prompt

    def resolve_historical(self, identity: PromptIdentity) -> ResolvedPrompt:
        """Resolve an exact locked identity for persisted history, including deprecations."""
        return self.resolve(identity, allow_deprecated=True)


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: MappingNode, deep: bool = False
) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


YamlModelT = TypeVar("YamlModelT", bound=BaseModel)


def _load_yaml_model(path: Path, model: type[YamlModelT], label: str) -> YamlModelT:
    try:
        with path.open(encoding="utf-8") as stream:
            raw: object = yaml.load(stream, Loader=_UniqueKeyLoader)
        return model.model_validate(raw)
    except (OSError, UnicodeError) as exc:
        raise PromptRegistryError(f"cannot read {label} {path}: {exc}") from exc
    except (ValidationError, yaml.YAMLError, TypeError) as exc:
        raise PromptRegistryError(f"invalid {label} {path}: {exc}") from exc


def _resolve_components(
    root: Path, registration: PromptRegistration
) -> tuple[ResolvedPromptComponent, ...]:
    result: list[ResolvedPromptComponent] = []
    names: set[str] = set()
    for component in registration.components:
        if component.name in names:
            raise PromptRegistryError(
                f"duplicate prompt component: {registration.prompt_id}:{component.name}"
            )
        names.add(component.name)
        component_path = (root / component.path).resolve()
        try:
            component_path.relative_to(root)
        except ValueError as exc:
            raise PromptRegistryError(
                f"prompt component leaves registry root: {component.path}"
            ) from exc
        if not component_path.is_file():
            raise PromptRegistryError(f"prompt component not found: {component.path}")
        try:
            content = component_path.read_bytes()
            text = content.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise PromptRegistryError(f"cannot read prompt component: {component.path}") from exc
        actual = sha256_bytes(content)
        if actual != component.sha256:
            raise PromptHashMismatchError(
                f"component hash mismatch for {registration.prompt_id}@"
                f"{registration.version}:{component.name}"
            )
        result.append(
            ResolvedPromptComponent(name=component.name, text=text, sha256=component.sha256)
        )
    return tuple(sorted(result, key=lambda item: item.name))


def _unique_lock_entries(
    history: tuple[PromptLockEntry, ...],
) -> dict[tuple[str, str], PromptLockEntry]:
    result: dict[tuple[str, str], PromptLockEntry] = {}
    for entry in history:
        key = (entry.prompt_id, entry.version)
        if key in result:
            raise PromptRegistryError(f"duplicate prompt lock entry: {key[0]}@{key[1]}")
        result[key] = entry
    return result


def _verify_lock(
    registration: PromptRegistration,
    lock_entries: dict[tuple[str, str], PromptLockEntry],
) -> None:
    key = (registration.prompt_id, registration.version)
    try:
        locked = lock_entries[key]
    except KeyError as exc:
        raise PromptVersionDriftError(
            f"prompt has no lock/history entry: {key[0]}@{key[1]}"
        ) from exc
    expected_components = tuple(
        sorted(registration.components, key=lambda component: component.name)
    )
    locked_components = tuple(sorted(locked.component_sha256, key=lambda component: component.name))
    if (
        locked.prompt_sha256 != registration.prompt_sha256
        or locked.output_schema != registration.output_schema
        or locked_components != expected_components
    ):
        raise PromptVersionDriftError(f"prompt {key[0]}@{key[1]} differs from its lock/history")
