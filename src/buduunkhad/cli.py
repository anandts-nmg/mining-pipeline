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

from buduunkhad.ai_cli import ai_app
from buduunkhad.core.raw_guard import RawIntegrityError
from buduunkhad.pipeline import (
    PHASE_CLASSES,
    MissingRawDataError,
    PathTooLongError,
    SelectionError,
    load_project,
    run_pipeline,
    validate_raw_inputs,
)

# Run-start failures that should surface as a clean red message + non-zero exit.
_RUN_ERRORS = (MissingRawDataError, PathTooLongError, RawIntegrityError, SelectionError)

app = typer.Typer(
    add_completion=False,
    help="Buduunkhad / XV-023222 exploration workflow pipeline (phases 00-99).",
    no_args_is_help=True,
)
app.add_typer(ai_app, name="ai")

_CONFIG_OPT = typer.Option("config/project.yaml", "--config", "-c", help="Path to project.yaml.")


def _echo_manifest(manifest) -> None:  # type: ignore[no-untyped-def]
    typer.echo(
        f"\nRun {manifest.run_id}  (dry_run={manifest.dry_run}, override={manifest.override})"
    )
    typer.echo("-" * 72)
    for p in manifest.phases:
        gate = p.gate_status or "-"
        if p.gate_provisional:
            gate = f"{gate} (provisional)"
        line = f"  {p.phase_id}  {p.status:<16} gate={gate:<20} {p.name}"
        typer.echo(line)
        if p.gate_provisional and p.gate_reason:
            typer.echo(f"        · {p.gate_reason}")
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

    # Partition into acknowledged gaps (manifest-flagged absent, e.g. #23 EULA) vs unexpected
    # ones, mirroring run_pipeline: acknowledged -> yellow + exit 0; unexpected -> red + exit 1.
    acknowledged: set[str] = set()
    if cfg.manifest_path and cfg.manifest_path.exists():
        from buduunkhad.core.ingest import acknowledged_absent, load_manifest

        acknowledged = acknowledged_absent(load_manifest(cfg.manifest_path))
    ack = [m for m in missing if m in acknowledged]
    unexpected = [m for m in missing if m not in acknowledged]

    if ack:
        typer.secho(f"{len(ack)} acknowledged data gap(s) (manifest-flagged absent):", fg="yellow")
        for name in ack:
            typer.echo(f"  ~ {name}")
    if unexpected:
        typer.secho(
            f"MISSING {len(unexpected)} / {len(register)} raw inputs under {cfg.raw_root}:",
            fg="red",
        )
        for name in unexpected:
            typer.echo(f"  - {name}")
        raise typer.Exit(1)
    typer.secho(
        f"OK: all raw inputs present or acknowledged-absent under {cfg.raw_root}", fg="green"
    )
    raise typer.Exit(0)


@app.command("publish")
def publish_deliverables(
    config: Path = _CONFIG_OPT,
    label: str = typer.Option(
        None, "--label", help="Version label for the published folder (default: timestamp)."
    ),
    supersedes: str | None = typer.Option(
        None,
        "--supersedes",
        help="Publication ID explicitly superseded by this package.",
    ),
    source_run: list[str] | None = typer.Option(
        None,
        "--source-run",
        help="Select an exact source run as PHASE=RUN_ID; repeat for multiple phases.",
    ),
) -> None:
    """Copy every built phase's deliverables (not raw working copies) to BUDUUNKHAD_PUBLISH_ROOT.

    Walks the whole output_root and publishes deliverables under a ``PhaseNN/`` folder each,
    excluding raw working copies. Point BUDUUNKHAD_PUBLISH_ROOT at a destination folder (e.g. a
    Google Drive-for-Desktop path); deliverables are copied into a versioned subfolder there.
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
    from buduunkhad.core.publish import PublishError
    from buduunkhad.core.publish import publish as do_publish

    label = label or datetime.now().strftime("%Y%m%dT%H%M%S")
    source_runs: dict[str, str] = {}
    for selector in source_run or []:
        phase_id, separator, run_id = selector.partition("=")
        if (
            separator != "="
            or phase_id not in {phase.id for phase in PHASE_CLASSES}
            or not run_id
            or phase_id in source_runs
        ):
            typer.secho(
                "Each --source-run must be a unique registered PHASE=RUN_ID selector.", fg="red"
            )
            raise typer.Exit(2)
        source_runs[phase_id] = run_id
    try:
        result = do_publish(
            cfg.output_root,
            Path(publish_root),
            label,
            runs_root=cfg.runs_root,
            project_config_path=config,
            superseded_publication_id=supersedes,
            source_runs=source_runs,
        )
    except PublishError as exc:
        typer.secho(str(exc), fg="red")
        raise typer.Exit(2) from exc
    typer.secho(f"Published {len(result.files)} deliverable(s) to:", fg="green")
    typer.echo(f"  {result.dest}")
    typer.echo(f"  (skipped {result.skipped_working_copies} raw working-copy file(s) by design)")
    typer.echo("Share that folder in Google Drive to give teammates access.")


@app.command("backup-raw")
def backup_raw(
    config: Path = _CONFIG_OPT,
    label: str = typer.Option("v01", "--label", help="Version label for the raw backup folder."),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite an existing backup with this label."
    ),
) -> None:
    """Back up the COMPLETE raw archive to BUDUUNKHAD_PUBLISH_ROOT, checksum-verified.

    Creates ``Raw_Archive_Backup_<label>/`` with the full raw tree under ``0_Raw_Data/`` plus the
    Phase-00 checksum register + integrity artifacts, then re-hashes every file against the
    register. Unlike ``publish`` (deliverables only), this deliberately backs up the raw data so
    teammates have an immutable, verifiable copy separate from the working source. Raw stays
    read-only. Run Phase 00 first — it produces the checksum register.
    """
    from buduunkhad.core import paths
    from buduunkhad.core.publish import PublishError, backup_raw_archive
    from buduunkhad.pipeline import baseline_checksum_path

    cfg, _register = load_project(config)
    publish_root = os.environ.get("BUDUUNKHAD_PUBLISH_ROOT")
    if not publish_root:
        typer.secho(
            "Set BUDUUNKHAD_PUBLISH_ROOT to a destination folder (e.g. a Google "
            "Drive-for-Desktop path) before backing up.",
            fg="red",
        )
        raise typer.Exit(2)
    register_csv = baseline_checksum_path(cfg)
    p00 = paths.phase_dir(cfg.output_root, "00")
    prefix = cfg.register_prefix
    integrity = [
        p00 / f"{prefix}_79Input_Master_Inventory.xlsx",
        p00 / f"{prefix}_Raw_Data_Integrity_Log.xlsx",
        p00 / f"{prefix}_Source_Data_Readme.docx",
    ]
    try:
        res = backup_raw_archive(
            cfg.raw_root,
            register_csv,
            Path(publish_root),
            label,
            integrity_files=integrity,
            overwrite=overwrite,
        )
    except PublishError as exc:
        typer.secho(str(exc), fg="red")
        raise typer.Exit(1) from exc
    typer.secho(
        f"Raw backup: {res.files} file(s), {res.verified} verified byte-identical.", fg="green"
    )
    typer.echo(f"  {res.dest}")
    typer.echo("Share that folder in Google Drive to give teammates a verified, immutable copy.")


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
    only_list = [s.strip() for s in only.split(",") if s.strip()] if only else None
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
