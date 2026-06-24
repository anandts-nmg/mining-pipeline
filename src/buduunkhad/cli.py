"""Typer CLI for the Buduunkhad pipeline.

buduunkhad list                 # show the phase registry
buduunkhad info                 # show project constants
buduunkhad validate             # check raw inputs are present
buduunkhad run --dry-run        # build the full tree + scaffolding (no data)
buduunkhad run --from 00 --to 01
buduunkhad phase00 / phase01 / ... --dry-run   # run a single phase
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import typer

from buduunkhad.core.raw_guard import RawIntegrityError
from buduunkhad.pipeline import (
    PHASE_CLASSES,
    MissingRawDataError,
    PathTooLongError,
    load_project,
    run_pipeline,
    validate_raw_inputs,
)

# Run-start failures that should surface as a clean red message + non-zero exit.
_RUN_ERRORS = (MissingRawDataError, PathTooLongError, RawIntegrityError)

app = typer.Typer(
    add_completion=False,
    help="Buduunkhad / XV-023222 exploration workflow pipeline (phases 00-99).",
    no_args_is_help=True,
)

_CONFIG_OPT = typer.Option("config/project.yaml", "--config", "-c", help="Path to project.yaml.")


def _echo_manifest(manifest) -> None:  # type: ignore[no-untyped-def]
    typer.echo(
        f"\nRun {manifest.run_id}  (dry_run={manifest.dry_run}, override={manifest.override})"
    )
    typer.echo("-" * 72)
    for p in manifest.phases:
        gate = p.gate_status or "-"
        line = f"  {p.phase_id}  {p.status:<16} gate={gate:<8} {p.name}"
        typer.echo(line)
        if p.error:
            typer.echo(f"        ! {p.error}")
    for w in manifest.warnings:
        typer.secho(f"  ! warning: {w}", fg="yellow")
    if manifest.stopped_at:
        typer.echo(f"\nStopped at phase {manifest.stopped_at}.")
    typer.echo(f"\nManifest + log: runs/{manifest.run_id}/")


@app.command("list")
def list_phases() -> None:
    """List the registered phases in workflow order."""
    typer.echo("Registered phases (00 -> 99):")
    for cls in PHASE_CLASSES:
        built = "BUILD" if cls.mode == "build" else "ORCH "
        typer.echo(f"  {cls.id}  [{built}]  {cls.name}")


@app.command("info")
def info(config: Path = _CONFIG_OPT) -> None:
    """Show project constants and resolved paths."""
    cfg, register = load_project(config)
    typer.echo(
        f"Project:        {cfg.project.name} ({cfg.project.project_code} / {cfg.project.license_code})"
    )
    typer.echo(f"Target CRS:     {cfg.crs.target_name} ({cfg.crs.target_authority})")
    typer.echo(f"Raw root:       {cfg.raw_root}")
    typer.echo(f"Output root:    {cfg.output_root}")
    typer.echo(f"Runs root:      {cfg.runs_root}")
    typer.echo(f"Register:       {cfg.register_path}  ({len(register)} inputs)")
    typer.echo(f"Buffers (m):    {cfg.boundary.buffers_m}")
    typer.echo(f"Master layers:  {len(cfg.master_gpkg_layers)}")


@app.command("validate")
def validate(config: Path = _CONFIG_OPT) -> None:
    """Check that every registered raw input is present under raw_root."""
    cfg, register = load_project(config)

    # Manifest coverage (provenance + size cross-check) when a manifest is configured.
    if cfg.manifest_path and cfg.manifest_path.exists():
        from buduunkhad.core.ingest import coverage, load_manifest

        manifest = load_manifest(cfg.manifest_path)
        cov = coverage(register, manifest, cfg.raw_root)
        typer.echo(
            f"Manifest: {len(manifest)} entries | local present {len(cov.present)}, "
            f"missing {len(cov.missing)}, size-mismatch {len(cov.size_mismatch)}"
        )
        for name, exp, got in cov.size_mismatch[:10]:
            typer.secho(f"  ~ size differs: {name} (manifest {exp}, local {got})", fg="yellow")

    missing = validate_raw_inputs(register, cfg.raw_root)
    if not missing:
        typer.secho(f"OK: all {len(register)} raw inputs present under {cfg.raw_root}", fg="green")
        raise typer.Exit(0)
    typer.secho(
        f"MISSING {len(missing)} / {len(register)} raw inputs under {cfg.raw_root}:", fg="red"
    )
    for name in missing:
        typer.echo(f"  - {name}")
    raise typer.Exit(1)


@app.command("publish")
def publish_deliverables(
    config: Path = _CONFIG_OPT,
    label: str = typer.Option(
        None, "--label", help="Version label for the published folder (default: timestamp)."
    ),
) -> None:
    """Copy Phase 0-1 deliverables (not raw working copies) to BUDUUNKHAD_PUBLISH_ROOT.

    Point BUDUUNKHAD_PUBLISH_ROOT at a destination folder (e.g. a Google
    Drive-for-Desktop path); deliverables are copied into a versioned subfolder there.
    """
    cfg, _register = load_project(config)
    publish_root = os.environ.get("BUDUUNKHAD_PUBLISH_ROOT")
    if not publish_root:
        typer.secho(
            "Set BUDUUNKHAD_PUBLISH_ROOT to a destination folder (e.g. a Google "
            "Drive-for-Desktop path) before publishing.",
            fg="red",
        )
        raise typer.Exit(2)
    from buduunkhad.core.publish import publish as do_publish

    label = label or datetime.now().strftime("%Y%m%dT%H%M%S")
    result = do_publish(cfg.output_root, Path(publish_root), label, runs_root=cfg.runs_root)
    typer.secho(f"Published {len(result.files)} deliverable(s) to:", fg="green")
    typer.echo(f"  {result.dest}")
    typer.echo(f"  (skipped {result.skipped_working_copies} raw working-copy file(s) by design)")
    typer.echo("Share that folder in Google Drive to give teammates access.")


@app.command("run")
def run(
    config: Path = _CONFIG_OPT,
    from_: str = typer.Option(None, "--from", help="First phase id (e.g. 00)."),
    to: str = typer.Option(None, "--to", help="Last phase id (e.g. 01)."),
    only: str = typer.Option(None, "--only", help="Comma-separated phase ids (e.g. 00,01)."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Build tree + scaffolding; no raw data needed."
    ),
    override: bool = typer.Option(
        False, "--override", help="Advance past a blocked decision gate (logged)."
    ),
) -> None:
    """Run the pipeline over the selected phases."""
    cfg, register = load_project(config)
    only_list = [s.strip() for s in only.split(",")] if only else None
    try:
        manifest = run_pipeline(
            cfg, register, from_=from_, to=to, only=only_list, dry_run=dry_run, override=override
        )
    except _RUN_ERRORS as exc:
        typer.secho(str(exc), fg="red")
        raise typer.Exit(2) from exc
    _echo_manifest(manifest)


def _make_phase_command(phase_id: str, phase_name: str):  # type: ignore[no-untyped-def]
    def _cmd(
        config: Path = _CONFIG_OPT,
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Build scaffolding; no raw data needed."
        ),
        override: bool = typer.Option(
            False, "--override", help="Advance past a blocked gate (logged)."
        ),
    ) -> None:
        cfg, register = load_project(config)
        try:
            manifest = run_pipeline(
                cfg, register, only=[phase_id], dry_run=dry_run, override=override
            )
        except _RUN_ERRORS as exc:
            typer.secho(str(exc), fg="red")
            raise typer.Exit(2) from exc
        _echo_manifest(manifest)

    _cmd.__doc__ = f"Run phase {phase_id} - {phase_name}."
    return _cmd


# Register one command per phase: phase00, phase01, ... phase99.
for _cls in PHASE_CLASSES:
    app.command(f"phase{_cls.id}")(_make_phase_command(_cls.id, _cls.name))


def main() -> None:  # pragma: no cover - console-script entry
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
