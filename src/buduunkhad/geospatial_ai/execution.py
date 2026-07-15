"""Explicit optional live-provider execution of an already prepared package."""

from __future__ import annotations

import json
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from buduunkhad.ai.fingerprint import sha256_file
from buduunkhad.ai.providers import (
    AIProvider,
    AnthropicProvider,
    OpenAIProvider,
    ProviderCall,
    ProviderCredentialError,
    ProviderDependencyError,
    ProviderImage,
)
from buduunkhad.config import (
    AIConfig,
    AIProviderSelection,
    ExecutionProfile,
    SourceEgressPolicy,
)
from buduunkhad.geospatial_ai.ledger import AIJobLedger, LedgerStatus
from buduunkhad.geospatial_ai.manifests import (
    EgressDecisionStatus,
    RequestPackageManifest,
    ResponseOrigin,
    SavedProviderResponse,
    TileRecord,
)
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.requests import (
    RequestPackageError,
    load_request_package,
    validate_package_ledger,
    verify_package_source,
)


class LiveExecutionError(RuntimeError):
    """Prepared request execution was blocked or failed safely."""


def execute_request_package(
    package_directory: Path,
    *,
    config: AIConfig,
    roots: StorageRoots,
    provider: AIProvider | None = None,
    now: datetime | None = None,
) -> Path:
    package_directory = roots.assert_run_artifact(package_directory)
    package = load_request_package(package_directory)
    _validate_execution_policy(
        package.request.provider.provider, package.request.provider.model, config
    )
    if package.egress.status is not EgressDecisionStatus.APPROVED:
        raise LiveExecutionError("request package has no explicit source-egress approval")
    verify_package_source(package, roots=roots)
    run_directory = roots.run_directory(package.request.run_id)
    package_resolved = package_directory.resolve(strict=True)
    if not package_resolved.is_relative_to(run_directory):
        raise LiveExecutionError("request package is outside its run directory")
    ledger = AIJobLedger(
        run_directory / "ai_jobs.sqlite", roots=roots, run_id=package.request.run_id
    )
    validate_package_ledger(package, ledger, package_directory)
    if package.estimated_cost_usd <= 0:
        raise LiveExecutionError("live execution requires a positive inspected cost estimate")
    images = tuple(_load_image(package_directory, tile) for tile in package.tile_manifest.tiles)
    components = {component.name: component.text for component in package.prompt_components}
    if set(components) != {"system", "user"}:
        raise LiveExecutionError("prepared prompt must contain exact system and user components")
    call = ProviderCall(
        request_id=package.request.request_id,
        request_fingerprint=package.request_fingerprint,
        task_type=package.request.task_type,
        provider=cast(Literal["openai", "anthropic"], config.provider.value),
        model=config.provider_model or "",
        system_prompt=components["system"],
        user_prompt=_execution_user_prompt(package, components["user"]),
        output_schema=package.output_schema_json,
        images=images,
        timeout_seconds=config.request_timeout_seconds,
        max_output_tokens=config.max_output_tokens,
    )
    adapter = provider or _provider(config.provider)
    timestamp = now or datetime.now(UTC)
    ledger.transition(
        package.request.job_id,
        LedgerStatus.RUNNING,
        occurred_at=timestamp,
        estimated_cost_usd=package.estimated_cost_usd,
        max_concurrency=config.concurrency,
        max_requests=config.max_requests_per_run,
        max_total_estimated_cost_usd=config.max_cost_per_run_usd,
    )
    try:
        result = adapter.execute(call)
        if (result.provider, result.model) != (config.provider.value, config.provider_model):
            raise LiveExecutionError(
                "provider result identity differs from execution configuration"
            )
        if result.created_at < timestamp:
            raise LiveExecutionError("provider result predates the current execution attempt")
        response = SavedProviderResponse(
            origin=ResponseOrigin.LIVE_EXECUTION,
            provider=result.provider,
            model=result.model,
            response_id=result.response_id,
            request_id=package.request.request_id,
            job_id=package.request.job_id,
            run_id=package.request.run_id,
            phase_id=package.request.phase_id,
            request_fingerprint=package.request_fingerprint,
            task_type=package.request.task_type,
            prompt=package.prompt,
            schema_identity=package.schema_identity,
            payload=result.payload,
            usage=result.usage,
            received_at=result.created_at,
        )
        output = roots.assert_writable(
            run_directory / "responses" / f"{package.request.job_id}.json",
            run_id=package.request.run_id,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise LiveExecutionError("provider response file already exists")
        output.write_text(response.model_dump_json(indent=2), encoding="utf-8", newline="\n")
        ledger.transition(
            package.request.job_id,
            LedgerStatus.SUCCEEDED,
            occurred_at=result.created_at,
            response_file=output.relative_to(run_directory).as_posix(),
            response_sha256=sha256_file(output),
            usage=result.usage,
            estimated_cost_usd=package.estimated_cost_usd,
        )
    except Exception as exc:
        with suppress(Exception):
            ledger.transition(
                package.request.job_id,
                LedgerStatus.FAILED,
                occurred_at=datetime.now(UTC),
                error_category=type(exc).__name__,
            )
        if isinstance(exc, (LiveExecutionError, ProviderCredentialError, ProviderDependencyError)):
            raise
        raise LiveExecutionError("live provider execution failed") from exc
    return output


def _validate_execution_policy(provider: str, model: str, config: AIConfig) -> None:
    if not config.enabled:
        raise LiveExecutionError("AI execution is disabled")
    if config.profile is ExecutionProfile.LEGACY:
        raise LiveExecutionError("live provider execution is unavailable in the legacy profile")
    if config.provider is AIProviderSelection.DISABLED:
        raise LiveExecutionError("no live provider is selected")
    if provider != config.provider.value or model != config.provider_model:
        raise LiveExecutionError("prepared provider/model differs from current configuration")
    if not config.external_data_allowed:
        raise LiveExecutionError("external data egress is disabled")
    if config.source_egress_policy is not SourceEgressPolicy.REQUIRE_EXPLICIT_APPROVAL:
        raise LiveExecutionError("source-egress policy does not require explicit approval")


def _provider(selection: AIProviderSelection) -> AIProvider:
    if selection is AIProviderSelection.OPENAI:
        return OpenAIProvider()
    if selection is AIProviderSelection.ANTHROPIC:
        return AnthropicProvider()
    raise LiveExecutionError("no live provider is selected")


def _load_image(package_directory: Path, tile: TileRecord) -> ProviderImage:
    try:
        relative_path = tile.image_relative_path
        tile_id = tile.tile_id
        digest = tile.image_sha256
        path = package_directory / relative_path
        data = path.read_bytes()
    except (AttributeError, OSError, TypeError) as exc:
        raise RequestPackageError("prepared tile cannot be loaded") from exc
    return ProviderImage(tile_id=tile_id, media_type="image/png", sha256=digest, data=data)


def _execution_user_prompt(
    package: RequestPackageManifest,
    locked_user_prompt: str,
) -> str:
    """Bind the locked task instruction to exact source/tile identities sent live."""

    context = {
        "envelope_version": "1.0.0",
        "request_fingerprint": package.request_fingerprint,
        "request": package.request.model_dump(mode="json"),
        "tiles": [
            {
                "tile_id": tile.tile_id,
                "source_asset_id": package.source.asset_id,
                "source_sha256": package.source.sha256,
                "image_sha256": tile.image_sha256,
                "x_offset": tile.x_offset,
                "y_offset": tile.y_offset,
                "width": tile.width,
                "height": tile.height,
            }
            for tile in package.tile_manifest.tiles
        ],
    }
    encoded = json.dumps(context, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return f"{locked_user_prompt}\n\nREQUEST_CONTEXT_JSON\n{encoded}"
