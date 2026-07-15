"""Saved-response ingestion without pretending a provider ran in this process."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError

from buduunkhad.ai.contracts import CanonicalJSONValue, SourceReference
from buduunkhad.ai.fingerprint import sha256_file
from buduunkhad.ai.prompts import PromptRegistry, default_schema_registry
from buduunkhad.ai.providers.base import (
    prohibit_provider_approval,
    validate_provider_output_contract,
)
from buduunkhad.geospatial_ai.ledger import AIJobLedger, LedgerStatus
from buduunkhad.geospatial_ai.manifests import SavedProviderResponse, ValidatedResponseRecord
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.requests import (
    load_request_package,
    validate_package_ledger,
    verify_package_source,
)


class ResponseIngestionError(ValueError):
    """A saved response is corrupt, unbound, or schema-incompatible."""


def ingest_saved_response(
    package_directory: Path,
    response_path: Path,
    *,
    roots: StorageRoots,
    now: datetime | None = None,
) -> tuple[Path, ValidatedResponseRecord]:
    package_directory = roots.assert_run_artifact(package_directory)
    package = load_request_package(package_directory)
    verify_package_source(package, roots=roots)
    response = _load_response(response_path)
    comparisons = (
        ("provider", response.provider, package.request.provider.provider),
        ("model", response.model, package.request.provider.model),
        ("request ID", response.request_id, package.request.request_id),
        ("job ID", response.job_id, package.request.job_id),
        ("run ID", response.run_id, package.request.run_id),
        ("phase ID", response.phase_id, package.request.phase_id),
        ("request fingerprint", response.request_fingerprint, package.request_fingerprint),
        ("task", response.task_type, package.request.task_type),
        ("prompt", response.prompt, package.prompt),
        ("schema", response.schema_identity, package.schema_identity),
    )
    for label, actual, expected in comparisons:
        if actual != expected:
            raise ResponseIngestionError(f"saved response {label} mismatch")
    if response.received_at < package.request.created_at:
        raise ResponseIngestionError("saved response predates its request")
    schemas = default_schema_registry()
    prompt = PromptRegistry.load_packaged(schema_registry=schemas).resolve(response.prompt)
    if prompt.output_schema != response.schema_identity:
        raise ResponseIngestionError("saved response prompt/schema binding is invalid")
    registration = schemas.resolve(response.schema_identity)
    payload = response.payload.to_python()
    try:
        output = registration.output_model.model_validate(payload)
    except ValidationError as exc:
        raise ResponseIngestionError(
            "saved response payload fails the current output schema"
        ) from exc
    prohibit_provider_approval(output)
    validate_provider_output_contract(output, registration.output_model)
    validate_output_source_references(output, package.request.source_references)
    validated_at = now or datetime.now(UTC)
    if validated_at < response.received_at:
        raise ResponseIngestionError("response validation predates response receipt")
    run_directory = roots.run_directory(package.request.run_id)
    ledger = AIJobLedger(
        run_directory / "ai_jobs.sqlite", roots=roots, run_id=package.request.run_id
    )
    view = validate_package_ledger(package, ledger, package_directory)
    if view.status not in {LedgerStatus.PREPARED, LedgerStatus.SUCCEEDED}:
        raise ResponseIngestionError(f"job cannot ingest a response from state {view.status.value}")
    if validated_at < view.events[-1].occurred_at:
        raise ResponseIngestionError("response ingestion predates the current job state")
    validated = ValidatedResponseRecord(
        # A file-ingestion operation never claims that it made the remote call. The
        # execution ledger separately records whether this run executed a provider.
        imported_without_current_execution=True,
        provider=response.provider,
        model=response.model,
        response_id=response.response_id,
        request_id=response.request_id,
        job_id=response.job_id,
        run_id=response.run_id,
        phase_id=response.phase_id,
        request_fingerprint=response.request_fingerprint,
        task_type=response.task_type,
        prompt=response.prompt,
        schema_identity=response.schema_identity,
        payload=response.payload,
        usage=response.usage,
        validated_at=validated_at,
    )
    destination = roots.assert_writable(
        run_directory / "validated-responses" / f"{package.request.job_id}.json",
        run_id=package.request.run_id,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ResponseIngestionError("validated response already exists")
    destination.write_text(validated.model_dump_json(indent=2), encoding="utf-8", newline="\n")
    ledger.transition(
        package.request.job_id,
        LedgerStatus.INGESTED,
        occurred_at=validated.validated_at,
        response_file=destination.relative_to(run_directory).as_posix(),
        response_sha256=sha256_file(destination),
        usage=response.usage,
    )
    return destination, validated


def load_validated_response(path: Path) -> ValidatedResponseRecord:
    try:
        return ValidatedResponseRecord.model_validate(_load_unique_json(path))
    except ValueError as exc:
        raise ResponseIngestionError("validated response record is invalid") from exc


def _load_response(path: Path) -> SavedProviderResponse:
    try:
        return SavedProviderResponse.model_validate(_load_unique_json(path))
    except ValueError as exc:
        raise ResponseIngestionError("saved provider response is invalid") from exc


def validate_output_source_references(
    output: BaseModel,
    requested: tuple[SourceReference, ...],
) -> None:
    authority = {source.asset_id: source for source in requested}
    found = _collect_source_references(output)
    if not found:
        raise ResponseIngestionError("schema-bound response contains no source references")
    for source in found:
        registered = authority.get(source.asset_id)
        if registered is None or registered.sha256 != source.sha256:
            raise ResponseIngestionError("response contains an unregistered source identity")
        allowed_locators = {locator.model_dump_json() for locator in registered.locators}
        if any(locator.model_dump_json() not in allowed_locators for locator in source.locators):
            raise ResponseIngestionError("response contains an unrequested source locator")


def _collect_source_references(value: object) -> tuple[SourceReference, ...]:
    found: list[SourceReference] = []
    active: set[int] = set()

    def visit(item: object) -> None:
        if isinstance(item, SourceReference):
            found.append(item)
            return
        if isinstance(item, CanonicalJSONValue):
            visit(item.to_python())
            return
        if isinstance(item, Mapping) and {"asset_id", "sha256", "locators"} <= set(item):
            try:
                source = SourceReference.model_validate(
                    {key: item[key] for key in ("asset_id", "sha256", "locators")}
                )
            except ValueError as exc:
                raise ResponseIngestionError(
                    "response contains a malformed source reference"
                ) from exc
            found.append(source)
            return
        if item is None or type(item) in {bool, int, float, str, bytes}:
            return
        container = isinstance(item, (BaseModel, Mapping, tuple, list, set, frozenset))
        container = container or (is_dataclass(item) and not isinstance(item, type))
        if not container:
            return
        identity = id(item)
        if identity in active:
            raise ResponseIngestionError("response payload contains a reference cycle")
        active.add(identity)
        try:
            if isinstance(item, BaseModel):
                for field_name in type(item).model_fields:
                    visit(object.__getattribute__(item, field_name))
            elif isinstance(item, Mapping):
                for key, nested in item.items():
                    visit(key)
                    visit(nested)
            elif isinstance(item, (tuple, list, set, frozenset)):
                for nested in item:
                    visit(nested)
            else:
                for field in dataclass_fields(item):  # type: ignore[arg-type]
                    visit(object.__getattribute__(item, field.name))
        finally:
            active.remove(identity)

    visit(value)
    return tuple(found)


def _load_unique_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ResponseIngestionError(
            f"response JSON is unreadable or invalid: {path.name}"
        ) from exc


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value
