"""Additive keyless AI-to-QGIS command group.

Heavy geospatial and provider modules are imported only inside commands so ordinary
configuration loading, legacy runs, and dry runs remain unchanged and offline.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import typer

ai_app = typer.Typer(
    add_completion=False,
    help="Prepare, ingest, process, and evaluate inspectable AI_DRAFT GIS work.",
    no_args_is_help=True,
)

phase03_ai_app = typer.Typer(
    add_completion=False,
    help="Package validated AI_DRAFT geometry for human Phase 03 review and promotion.",
    no_args_is_help=True,
)
ai_app.add_typer(phase03_ai_app, name="phase03")


def _context(config_path: Path):  # type: ignore[no-untyped-def]
    from buduunkhad.config import load_config
    from buduunkhad.geospatial_ai.path_safety import StorageRoots

    config = load_config(config_path)
    return config, StorageRoots.from_environment(raw_root=config.raw_root)


def _abort(exc: Exception) -> None:
    typer.secho(str(exc), fg="red", err=True)
    raise typer.Exit(2) from exc


@ai_app.command("snapshot-create")
def snapshot_create(
    run_id: str = typer.Option(..., "--run-id"),
    source_root: Path = typer.Option(..., "--source-root", exists=True, file_okay=False),
    source_root_id: str = typer.Option(..., "--source-root-id"),
    manifest: Path | None = typer.Option(None, "--manifest"),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Create a write-once checksum manifest for a configured protected source root."""

    from buduunkhad.geospatial_ai.snapshots import create_snapshot_manifest

    try:
        _config, roots = _context(config)
        destination = (
            manifest or roots.run_directory(run_id, create=True) / "snapshot-manifest.json"
        )
        result = create_snapshot_manifest(
            source_root,
            destination,
            source_root_id=source_root_id,  # type: ignore[arg-type]
            roots=roots,
            run_id=run_id,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"Created immutable manifest with {len(result.entries)} entries: {destination}")


@ai_app.command("snapshot-verify")
def snapshot_verify(
    source_root: Path = typer.Option(..., "--source-root", exists=True, file_okay=False),
    source_root_id: str = typer.Option(..., "--source-root-id"),
    manifest: Path = typer.Option(..., "--manifest", exists=True, dir_okay=False),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Re-hash a protected source tree against an immutable snapshot manifest."""

    from buduunkhad.geospatial_ai.snapshots import verify_snapshot_manifest

    try:
        _config, roots = _context(config)
        result = verify_snapshot_manifest(
            source_root,
            manifest,
            source_root_id=source_root_id,  # type: ignore[arg-type]
            roots=roots,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    if not result.valid:
        typer.secho(result.model_dump_json(indent=2), fg="red")
        raise typer.Exit(1)
    typer.secho("Snapshot verification passed.", fg="green")


@ai_app.command("prepare")
def prepare(
    source: Path = typer.Option(..., "--source", exists=True, dir_okay=False),
    run_id: str = typer.Option(..., "--run-id"),
    task: str = typer.Option("geological-feature-proposal", "--task"),
    provider: str = typer.Option("disabled", "--provider"),
    model: str | None = typer.Option(None, "--model"),
    tile_size: int = typer.Option(1024, "--tile-size", min=1),
    overlap: int = typer.Option(128, "--overlap", min=0),
    page_number: int = typer.Option(1, "--page-number", min=1),
    render_scale: float = typer.Option(1.0, "--render-scale", min=0.01),
    estimated_cost: float = typer.Option(0.0, "--estimated-cost", min=0),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Render a source and create an inspectable request package without executing AI."""

    from buduunkhad.ai.contracts import TaskType
    from buduunkhad.geospatial_ai.requests import prepare_request_package
    from buduunkhad.geospatial_ai.tiles import TileParameters

    try:
        project, roots = _context(config)
        directory, package = prepare_request_package(
            source,
            roots=roots,
            run_id=run_id,
            task_type=TaskType(task.replace("-", "_")),
            target_crs=project.crs.target_authority,
            provider=provider,  # type: ignore[arg-type]
            model=model,
            tile_parameters=TileParameters(width=tile_size, height=tile_size, overlap=overlap),
            estimated_cost_usd=Decimal(str(estimated_cost)),
            page_number=page_number,
            render_scale=render_scale,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"Prepared request package: {directory}")
    typer.echo(f"Fingerprint: {package.request_fingerprint}")
    typer.echo("No provider was contacted.")


@ai_app.command("approve-egress")
def approve_egress(
    package: Path = typer.Option(..., "--package", exists=True, file_okay=False),
    approved_by: str = typer.Option(..., "--approved-by"),
    note: str = typer.Option(..., "--note"),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Record one source-egress approval after inspecting an exact prepared package."""

    from buduunkhad.geospatial_ai.requests import approve_request_package_egress

    try:
        _project, roots = _context(config)
        output = approve_request_package_egress(
            package,
            roots=roots,
            approved_by=approved_by,
            note=note,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"Recorded immutable source-egress approval: {output}")


@ai_app.command("execute")
def execute(
    package: Path = typer.Option(..., "--package", exists=True, file_okay=False),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Execute one approved prepared package through the configured optional provider."""

    from buduunkhad.geospatial_ai.execution import execute_request_package

    try:
        project, roots = _context(config)
        output = execute_request_package(package, config=project.ai, roots=roots)
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"Saved provider response: {output}")


@ai_app.command("ingest-response")
def ingest_response(
    package: Path = typer.Option(..., "--package", exists=True, file_okay=False),
    response: Path = typer.Option(..., "--response", exists=True, dir_okay=False),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Validate an externally supplied response without claiming local provider execution."""

    from buduunkhad.geospatial_ai.responses import ingest_saved_response

    try:
        _project, roots = _context(config)
        output, record = ingest_saved_response(package, response, roots=roots)
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"Validated saved response: {output}")
    typer.echo(f"Imported without current execution: {record.imported_without_current_execution}")


@ai_app.command("process-response")
def process_response(
    package: Path = typer.Option(..., "--package", exists=True, file_okay=False),
    response: Path = typer.Option(..., "--response", exists=True, dir_okay=False),
    repair: bool = typer.Option(False, "--repair"),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Transform a validated response into an AI_DRAFT GeoPackage and QGIS project."""

    from buduunkhad.geospatial_ai.draft_gpkg import process_validated_response
    from buduunkhad.geospatial_ai.qgis_output import write_ai_draft_qgz
    from buduunkhad.geospatial_ai.requests import load_request_package, verify_package_source

    try:
        project, roots = _context(config)
        manifest = load_request_package(package)
        gpkg = process_validated_response(
            package,
            response,
            roots=roots,
            expected_target_crs=project.crs.target_authority,
            repair=repair,
        )
        source = verify_package_source(manifest, roots=roots)
        qgz = write_ai_draft_qgz(
            gpkg.with_suffix(".qgz"),
            gpkg=gpkg,
            source_raster=source,
            epsg=project.target_epsg,
            roots=roots,
            run_id=manifest.request.run_id,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"AI_DRAFT GeoPackage: {gpkg}")
    typer.echo(f"Portable QGIS project: {qgz}")


@ai_app.command("evaluate")
def evaluate(
    run_id: str = typer.Option(..., "--run-id"),
    candidate: Path = typer.Option(..., "--candidate", exists=True, dir_okay=False),
    reference: Path = typer.Option(..., "--reference", exists=True, dir_okay=False),
    layers: str = typer.Option(..., "--layers", help="Comma-separated layer names."),
    match_distance: float = typer.Option(..., "--match-distance", min=0),
    line_buffer: float = typer.Option(..., "--line-buffer", min=0),
    minimum_iou: float = typer.Option(..., "--minimum-iou", min=0, max=1),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Compare draft layers with an untracked reference dataset under the eval root."""

    from buduunkhad.geospatial_ai.evaluation import EvaluationSettings, evaluate_geopackages

    selected = tuple(item.strip() for item in layers.split(",") if item.strip())
    if not selected:
        _abort(ValueError("at least one evaluation layer is required"))
    try:
        _project, roots = _context(config)
        json_path, csv_path = evaluate_geopackages(
            candidate,
            reference,
            layers=selected,
            settings=EvaluationSettings(
                match_distance=match_distance,
                line_buffer=line_buffer,
                minimum_iou=minimum_iou,
            ),
            roots=roots,
            run_id=run_id,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"Evaluation JSON: {json_path}")
    typer.echo(f"Evaluation CSV: {csv_path}")


@ai_app.command("inspect-job")
def inspect_job(
    run_id: str = typer.Option(..., "--run-id"),
    job_id: str = typer.Option(..., "--job-id"),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Inspect append-only execution-bookkeeping events for one job."""

    from buduunkhad.geospatial_ai.ledger import AIJobLedger

    try:
        _project, roots = _context(config)
        run_directory = roots.run_directory(run_id)
        ledger = AIJobLedger(run_directory / "ai_jobs.sqlite", roots=roots, run_id=run_id)
        view = ledger.inspect(job_id)
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(view.model_dump_json(indent=2))


@phase03_ai_app.command("import-ai-draft")
def phase03_import_ai_draft(
    run_id: str = typer.Option(..., "--run-id"),
    draft: Path = typer.Option(..., "--draft", exists=True, dir_okay=False),
    review_package: Path = typer.Option(..., "--review-package", file_okay=False),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Create an isolated Phase 03 QGIS review package from one authoritative AI draft."""

    from buduunkhad.core import naming, paths
    from buduunkhad.geospatial_ai.phase03_handoff import import_ai_draft_review_package

    try:
        project, roots = _context(config)
        evidence_directory = (
            paths.phase_dir(project.output_root, "03") / "09_Geological_Evidence_Layers_GPKG"
        )
        expected_name = naming.data_name(
            project.data_prefix,
            "Geological_Evidence_Layers",
            version=1,
            ext="gpkg",
        )
        existing = evidence_directory / expected_name
        manifest = import_ai_draft_review_package(
            draft,
            review_package,
            roots=roots,
            run_id=run_id,
            expected_target_crs=project.crs.target_authority,
            existing_evidence=existing if existing.is_file() else None,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    typer.echo(f"Phase 03 review package: {review_package}")
    typer.echo(f"Review package ID: {manifest.package_id}")
    typer.echo("Original AI_DRAFT and authoritative Phase 03 evidence were not modified.")


@phase03_ai_app.command("promote-reviewed")
def phase03_promote_reviewed(
    review_package: Path = typer.Option(..., "--review-package", exists=True, file_okay=False),
    output: Path = typer.Option(..., "--output", dir_okay=False),
    config: Path = typer.Option("config/project.yaml", "--config", "-c"),
) -> None:
    """Promote only explicitly accepted human-reviewed features into standalone evidence."""

    from buduunkhad.geospatial_ai.phase03_handoff import promote_reviewed_evidence

    try:
        _project, roots = _context(config)
        result = promote_reviewed_evidence(
            review_package,
            output,
            roots=roots,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        _abort(exc)
    action = "Created" if result.created else "Verified existing"
    typer.echo(f"{action} accepted Phase 03 evidence: {result.output}")
    typer.echo(f"Promoted features: {len(result.promoted_feature_ids)}")
    typer.echo(f"Append-only promotion audit: {result.audit_ledger}")
