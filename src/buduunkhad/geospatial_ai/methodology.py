"""Typed access to versioned methodology authority and discrepancy records."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MethodologyError(ValueError):
    """A methodology authority resource is malformed or unavailable."""


class MethodologySource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    repository_path: str
    role: str


class MethodologyRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    requirement_id: str
    statement: str
    source_refs: tuple[str, ...] = Field(min_length=1)
    status: str


class PhaseMethodology(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    phase_id: str = Field(pattern=r"^0[0-5]$")
    requirements: tuple[MethodologyRequirement, ...]

    @model_validator(mode="after")
    def _unique_requirement_ids(self) -> PhaseMethodology:
        identities = tuple(item.requirement_id for item in self.requirements)
        if len(set(identities)) != len(identities):
            raise ValueError("phase methodology contains duplicate stable requirement IDs")
        return self


class AuthorityRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    sources: tuple[MethodologySource, ...]
    precedence: tuple[str, ...]


class MethodologyDiscrepancy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    discrepancy_id: str
    subject: str
    compared_sources: tuple[str, ...] = Field(min_length=2)
    statement: str
    operational_impact: str
    status: str
    resolution: str | None
    approver: str | None
    effective_version: str | None

    @model_validator(mode="after")
    def _unresolved_has_no_approval(self) -> MethodologyDiscrepancy:
        if self.status == "unresolved" and any(
            (self.resolution, self.approver, self.effective_version)
        ):
            raise ValueError("unresolved discrepancies cannot contain an adopted resolution")
        return self


class DiscrepancyRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: Literal["1.0.0"]
    discrepancies: tuple[MethodologyDiscrepancy, ...]


def load_phase_methodology(phase_id: str) -> PhaseMethodology:
    if phase_id not in {f"{value:02d}" for value in range(6)}:
        raise MethodologyError(f"unsupported methodology phase: {phase_id}")
    return PhaseMethodology.model_validate(_load_packaged_yaml(f"phase{phase_id}.yaml"))


def load_authority_registry() -> AuthorityRegistry:
    return AuthorityRegistry.model_validate(_load_packaged_yaml("authority.yaml"))


def load_discrepancy_registry() -> DiscrepancyRegistry:
    registry = DiscrepancyRegistry.model_validate(_load_packaged_yaml("discrepancies.yaml"))
    identities = tuple(item.discrepancy_id for item in registry.discrepancies)
    if len(set(identities)) != len(identities):
        raise MethodologyError("methodology discrepancies contain duplicate stable IDs")
    return registry


def _load_packaged_yaml(filename: str) -> object:
    try:
        resource = resources.files("buduunkhad").joinpath("methodology_data", filename)
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeError, OSError):
        try:
            checkout = Path(__file__).parents[3] / "config" / "methodology" / filename
            text = checkout.read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeError, OSError) as exc:
            raise MethodologyError(
                f"packaged methodology resource is unavailable: {filename}"
            ) from exc
    try:
        return _parse_yaml(text)
    except yaml.YAMLError as exc:
        raise MethodologyError(f"packaged methodology YAML is invalid: {filename}") from exc


def load_phase_methodology_from_checkout(root: Path, phase_id: str) -> PhaseMethodology:
    path = root / "config" / "methodology" / f"phase{phase_id}.yaml"
    try:
        return PhaseMethodology.model_validate(_parse_yaml(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
        raise MethodologyError(f"methodology file is invalid: {path}") from exc


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    value: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in value:
            raise yaml.constructor.ConstructorError(
                "while constructing a methodology mapping",
                node.start_mark,
                f"duplicate key: {key!r}",
                key_node.start_mark,
            )
        value[key] = loader.construct_object(value_node, deep=deep)
    return value


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _parse_yaml(text: str) -> object:
    return yaml.load(text, Loader=_UniqueKeyLoader)
