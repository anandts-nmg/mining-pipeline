"""Inspectable, keyless request-package preparation and verification."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

from buduunkhad.ai.contracts import (
    AIRequest,
    ArtifactSubjectIdentity,
    CanonicalJSONValue,
    NamedJSONValue,
    ProviderConfiguration,
    RasterTileLocator,
    SourceReference,
    TaskType,
)
from buduunkhad.ai.fingerprint import request_fingerprint, sha256_file, sha256_value
from buduunkhad.ai.prompts import PromptRegistry, default_schema_registry
from buduunkhad.ai.schema_identity import (
    LEGACY_SCHEMA_FINGERPRINT_ALGORITHM,
    SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM,
    SchemaFingerprintError,
    semantic_schema_sha256,
)
from buduunkhad.geospatial_ai.ledger import (
    AIJobLedger,
    LedgerJobCreate,
    LedgerJobView,
)
from buduunkhad.geospatial_ai.manifests import (
    EgressDecision,
    EgressDecisionStatus,
    PackageEgressApproval,
    PromptTextComponent,
    RequestPackageManifest,
)
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.source_assets import (
    register_pdf_page,
    register_raster_source,
    verify_registered_source,
)
from buduunkhad.geospatial_ai.tiles import (
    TileParameters,
    create_tiles,
    validate_tile_manifest,
)

PreparedProvider = Literal["disabled", "openai", "anthropic"]

_PROMPTS: dict[TaskType, str] = {
    TaskType.LEGEND_EXTRACTION: "vertical.legend-extraction",
    TaskType.MAP_FEATURE_INTERPRETATION: "vertical.map-feature-interpretation",
    TaskType.GEOLOGICAL_FEATURE_PROPOSAL: "vertical.geological-feature-proposal",
    TaskType.FEATURE_CRITIQUE: "vertical.feature-critique",
}


class RequestPackageError(ValueError):
    """A request package is incomplete, changed, or inconsistent."""


def prepare_request_package(
    source_path: Path,
    *,
    roots: StorageRoots,
    run_id: str,
    task_type: TaskType,
    target_crs: str,
    provider: PreparedProvider = "disabled",
    model: str | None = None,
    tile_parameters: TileParameters | None = None,
    egress: EgressDecision | None = None,
    phase_id: str = "03",
    subject: ArtifactSubjectIdentity | None = None,
    estimated_cost_usd: Decimal = Decimal("0"),
    page_number: int = 1,
    render_scale: float = 1.0,
    now: datetime | None = None,
) -> tuple[Path, RequestPackageManifest]:
    if task_type not in _PROMPTS:
        raise RequestPackageError(f"task is not supported by the vertical slice: {task_type}")
    if provider not in {"disabled", "openai", "anthropic"}:
        raise RequestPackageError(f"unsupported provider selection: {provider}")
    if provider == "disabled" and model is not None:
        raise RequestPackageError("disabled provider cannot define a model")
    if provider != "disabled" and (not model or not model.strip()):
        raise RequestPackageError("live-provider preparation requires a model name")
    if task_type is TaskType.FEATURE_CRITIQUE and subject is None:
        raise RequestPackageError("independent critique preparation requires a subject identity")
    if egress is not None and egress.status is EgressDecisionStatus.APPROVED:
        raise RequestPackageError("egress approval must be recorded after package inspection")
    timestamp = now or datetime.now(UTC)
    run_directory = roots.run_directory(run_id, create=True)
    source = (
        register_pdf_page(
            source_path,
            roots=roots,
            run_id=run_id,
            target_crs=target_crs,
            page_number=page_number,
            render_scale=render_scale,
        )
        if source_path.suffix.casefold() == ".pdf"
        else register_raster_source(source_path, roots=roots, target_crs=target_crs)
    )
    package_directory = roots.assert_writable(
        run_directory / "requests" / f"{task_type.value}-{source.sha256[:16]}",
        run_id=run_id,
    )
    if package_directory.exists() and any(package_directory.iterdir()):
        raise RequestPackageError("request package already exists and cannot be overwritten")
    package_directory.mkdir(parents=True, exist_ok=True)
    tile_manifest = create_tiles(
        source,
        parameters=tile_parameters or TileParameters(),
        package_directory=package_directory,
        roots=roots,
        run_id=run_id,
    )
    schemas = default_schema_registry()
    prompt = PromptRegistry.load_packaged(schema_registry=schemas).get(_PROMPTS[task_type], "1.0.0")
    schema = schemas.resolve(prompt.output_schema)
    source_reference = SourceReference(
        asset_id=source.asset_id,
        sha256=source.sha256,
        locators=tuple(
            RasterTileLocator(
                tile_id=tile.tile_id,
                x_offset=tile.x_offset,
                y_offset=tile.y_offset,
                width=tile.width,
                height=tile.height,
            )
            for tile in tile_manifest.tiles
        ),
    )
    preliminary = AIRequest(
        request_id="request-pending",
        job_id="job-pending",
        run_id=run_id,
        phase_id=phase_id,
        task_type=task_type,
        created_at=timestamp,
        source_references=(source_reference,),
        prompt=prompt.identity,
        output_schema=schema.identity,
        provider=ProviderConfiguration(
            provider=provider,
            model=model or "not-selected",
            parameters=(
                NamedJSONValue(
                    name="execution_envelope_version",
                    value=CanonicalJSONValue.from_value("1.0.0"),
                ),
                NamedJSONValue(
                    name="response_format",
                    value=CanonicalJSONValue.from_value("json_schema"),
                ),
            ),
        ),
        interpretation_parameters=(
            NamedJSONValue(
                name="tile_height",
                value=CanonicalJSONValue.from_value(tile_manifest.tile_height),
            ),
            NamedJSONValue(
                name="tile_overlap",
                value=CanonicalJSONValue.from_value(tile_manifest.overlap),
            ),
            NamedJSONValue(
                name="tile_width",
                value=CanonicalJSONValue.from_value(tile_manifest.tile_width),
            ),
        ),
        subject=subject,
    )
    fingerprint = request_fingerprint(preliminary)
    request = preliminary.model_copy(
        update={
            "request_id": f"request-{fingerprint[:24]}",
            "job_id": f"job-{sha256_value({'run_id': run_id, 'fingerprint': fingerprint})[:24]}",
        }
    )
    if request_fingerprint(request) != fingerprint:
        raise RequestPackageError("request identity fields unexpectedly changed its fingerprint")
    prompt_components = tuple(
        PromptTextComponent(name=component.name, text=component.text, sha256=component.sha256)
        for component in prompt.components
    )
    estimated_bytes = sum(
        (package_directory / tile.image_relative_path).stat().st_size
        for tile in tile_manifest.tiles
    ) + sum(len(component.text.encode("utf-8")) for component in prompt_components)
    package = RequestPackageManifest(
        request=request,
        request_fingerprint=fingerprint,
        prompt=prompt.identity,
        prompt_components=prompt_components,
        schema_identity=schema.identity,
        output_schema_json=CanonicalJSONValue.from_value(schema.output_model.model_json_schema()),
        source=source,
        tile_manifest=tile_manifest,
        egress=egress or EgressDecision(),
        estimated_request_bytes=estimated_bytes,
        estimated_cost_usd=estimated_cost_usd,
        execution_instructions=(
            "Inspect request-package.json and every tile before execution.",
            "Execution requires explicit AI enablement and source-egress approval.",
            "A saved response may be ingested later without claiming local provider execution.",
            "All returned geometry must remain in the named tile's pixel coordinates.",
        ),
        created_at=timestamp,
    )
    _write_package(package_directory, package)
    ledger = AIJobLedger(run_directory / "ai_jobs.sqlite", roots=roots, run_id=run_id)
    ledger.add_job(
        _expected_ledger_job(
            package,
            package_manifest_sha256=sha256_file(package_directory / "request-package.json"),
        )
    )
    return package_directory, package


def load_request_package(package_directory: Path) -> RequestPackageManifest:
    package_root = package_directory.resolve(strict=True)
    path = _package_file(package_root, "request-package.json")
    value = _load_unique_json(path)
    try:
        package = RequestPackageManifest.model_validate(value)
    except ValueError as exc:
        raise RequestPackageError("request package manifest is invalid") from exc
    approval_candidate = package_root / "egress-approval.json"
    if approval_candidate.exists():
        approval_path = _package_file(package_root, "egress-approval.json")
        if package.egress.status is EgressDecisionStatus.APPROVED:
            raise RequestPackageError("request package contains conflicting egress approvals")
        try:
            approval_record = PackageEgressApproval.model_validate(_load_unique_json(approval_path))
        except ValueError as exc:
            raise RequestPackageError("request package egress approval is invalid") from exc
        if approval_record.package_manifest_sha256 != sha256_file(path):
            raise RequestPackageError("egress approval does not bind the current request package")
        package = package.model_copy(update={"egress": approval_record.decision})
    if request_fingerprint(package.request) != package.request_fingerprint:
        raise RequestPackageError("request package fingerprint is invalid")
    if (
        package.prompt != package.request.prompt
        or package.schema_identity != package.request.output_schema
    ):
        raise RequestPackageError("request package prompt or schema binding is inconsistent")
    schemas = default_schema_registry()
    registration = schemas.resolve(package.schema_identity)
    prompt = PromptRegistry.load_packaged(schema_registry=schemas).resolve(package.prompt)
    if not registration.accepts(prompt.output_schema):
        raise RequestPackageError("request package prompt is not bound to its schema")
    expected_components = tuple(
        PromptTextComponent(name=item.name, text=item.text, sha256=item.sha256)
        for item in prompt.components
    )
    if package.prompt_components != expected_components:
        raise RequestPackageError("request package prompt text differs from the locked registry")
    _validate_package_schema(package, registration.identity.sha256)
    if package.tile_manifest.source != package.source:
        raise RequestPackageError("request package tile/source records are inconsistent")
    try:
        validate_tile_manifest(package.tile_manifest)
    except ValueError as exc:
        raise RequestPackageError("request package tile manifest is invalid") from exc
    expected_source_reference = SourceReference(
        asset_id=package.source.asset_id,
        sha256=package.source.sha256,
        locators=tuple(
            RasterTileLocator(
                tile_id=tile.tile_id,
                x_offset=tile.x_offset,
                y_offset=tile.y_offset,
                width=tile.width,
                height=tile.height,
            )
            for tile in package.tile_manifest.tiles
        ),
    )
    if package.request.source_references != (expected_source_reference,):
        raise RequestPackageError("request sources differ from the deterministic tile manifest")
    _validate_auxiliary_package_files(package_directory, package)
    for tile in package.tile_manifest.tiles:
        image = _package_file(package_root, tile.image_relative_path)
        if not image.is_file() or sha256_file(image) != tile.image_sha256:
            raise RequestPackageError(f"request tile changed after preparation: {tile.tile_id}")
        if tile.valid_mask_relative_path:
            mask = _package_file(package_root, tile.valid_mask_relative_path)
            if not mask.is_file() or sha256_file(mask) != tile.valid_mask_sha256:
                raise RequestPackageError(
                    f"request tile mask changed after preparation: {tile.tile_id}"
                )
    actual_bytes = sum(
        _package_file(package_root, tile.image_relative_path).stat().st_size
        for tile in package.tile_manifest.tiles
    ) + sum(len(component.text.encode("utf-8")) for component in package.prompt_components)
    if actual_bytes != package.estimated_request_bytes:
        raise RequestPackageError("request package size estimate differs from its actual payload")
    return package


def _validate_package_schema(
    package: RequestPackageManifest,
    expected_semantic_sha256: str,
) -> None:
    stored_schema = package.output_schema_json.to_python()
    try:
        semantic_sha256 = semantic_schema_sha256(stored_schema)
    except SchemaFingerprintError as exc:
        raise RequestPackageError(
            "request package schema JSON is unsupported or malformed"
        ) from exc
    if semantic_sha256 != expected_semantic_sha256:
        raise RequestPackageError("request package schema JSON differs from the registered model")
    identity = package.schema_identity
    if identity.fingerprint_algorithm == SEMANTIC_SCHEMA_FINGERPRINT_ALGORITHM:
        if semantic_sha256 != identity.sha256:
            raise RequestPackageError("request package semantic schema fingerprint is invalid")
    elif identity.fingerprint_algorithm == LEGACY_SCHEMA_FINGERPRINT_ALGORITHM:
        if sha256_value(stored_schema) != identity.sha256:
            raise RequestPackageError("request package legacy schema fingerprint is invalid")
    else:  # SchemaIdentity validation currently makes this unreachable; keep the boundary closed.
        raise RequestPackageError("request package schema fingerprint algorithm is unsupported")


def approve_request_package_egress(
    package_directory: Path,
    *,
    roots: StorageRoots,
    approved_by: str,
    note: str,
    approved_at: datetime | None = None,
) -> Path:
    """Append one local source-egress decision after the package has been inspected."""

    package_directory = roots.assert_run_artifact(package_directory)
    package = load_request_package(package_directory)
    if package.egress.status is EgressDecisionStatus.APPROVED:
        raise RequestPackageError("request package already has an egress approval")
    run_directory = roots.run_directory(package.request.run_id)
    package_path = package_directory.resolve(strict=True)
    if not package_path.is_relative_to(run_directory):
        raise RequestPackageError("request package is outside its run directory")
    decision = EgressDecision(
        status=EgressDecisionStatus.APPROVED,
        approved_by=approved_by,
        approved_at=approved_at or datetime.now(UTC),
        note=note,
    )
    destination = roots.assert_writable(
        package_path / "egress-approval.json",
        run_id=package.request.run_id,
    )
    if destination.exists():
        raise RequestPackageError("request package egress approval is immutable")
    approval = PackageEgressApproval(
        package_manifest_sha256=sha256_file(package_path / "request-package.json"),
        decision=decision,
    )
    destination.write_text(approval.model_dump_json(indent=2), encoding="utf-8", newline="\n")
    return destination


def verify_package_source(package: RequestPackageManifest, *, roots: StorageRoots) -> Path:
    return verify_registered_source(package.source, roots=roots)


def validate_package_ledger(
    package: RequestPackageManifest,
    ledger: AIJobLedger,
    package_directory: Path,
) -> LedgerJobView:
    view = ledger.inspect(package.request.job_id)
    expected = _expected_ledger_job(
        package,
        package_manifest_sha256=sha256_file(package_directory / "request-package.json"),
    )
    if view.job != expected:
        raise RequestPackageError("request package differs from its append-only ledger job")
    return view


def _write_package(directory: Path, package: RequestPackageManifest) -> None:
    (directory / "request-package.json").write_text(
        package.model_dump_json(indent=2), encoding="utf-8", newline="\n"
    )
    (directory / "source-asset.json").write_text(
        package.source.model_dump_json(indent=2), encoding="utf-8", newline="\n"
    )
    (directory / "tile-manifest.json").write_text(
        package.tile_manifest.model_dump_json(indent=2), encoding="utf-8", newline="\n"
    )
    (directory / "execution-instructions.txt").write_text(
        "\n".join(package.execution_instructions) + "\n", encoding="utf-8", newline="\n"
    )


def _expected_ledger_job(
    package: RequestPackageManifest,
    *,
    package_manifest_sha256: str,
) -> LedgerJobCreate:
    request = package.request
    return LedgerJobCreate(
        job_id=request.job_id,
        run_id=request.run_id,
        phase_id=request.phase_id,
        task_type=request.task_type,
        request_fingerprint=package.request_fingerprint,
        package_manifest_sha256=package_manifest_sha256,
        source_assets=((package.source.asset_id, package.source.sha256),),
        prompt=package.prompt,
        schema_identity=package.schema_identity,
        provider=request.provider.provider,
        model=request.provider.model,
        created_at=request.created_at,
    )


def _validate_auxiliary_package_files(
    directory: Path,
    package: RequestPackageManifest,
) -> None:
    root = directory.resolve(strict=True)
    try:
        source = type(package.source).model_validate(
            _load_unique_json(_package_file(root, "source-asset.json"))
        )
        tile_manifest = type(package.tile_manifest).model_validate(
            _load_unique_json(_package_file(root, "tile-manifest.json"))
        )
        instructions = _package_file(root, "execution-instructions.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        raise RequestPackageError("request package auxiliary records are invalid") from exc
    if source != package.source or tile_manifest != package.tile_manifest:
        raise RequestPackageError("request package auxiliary records differ from its manifest")
    if instructions != "\n".join(package.execution_instructions) + "\n":
        raise RequestPackageError("request package execution instructions were modified")


def _package_file(package_root: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise RequestPackageError("request package contains an unsafe relative file path")
    path = (package_root / relative).resolve(strict=True)
    if not path.is_relative_to(package_root) or not path.is_file():
        raise RequestPackageError("request package file escapes its package directory")
    return path


def _load_unique_json(path: Path) -> object:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text, object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RequestPackageError(f"JSON file is unreadable or invalid: {path.name}") from exc


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value
