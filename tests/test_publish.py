"""Tests for the deliverable publish step (core.publish)."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from buduunkhad.core.publish import (
    PublishError,
    backup_raw_archive,
    collect_deliverables,
    latest_gate_per_phase,
    load_publication_manifest,
    publish,
    verify_publication_package,
)


def _write_register(path: Path, rows: list[tuple[str, str, bytes]]) -> None:
    """rows = [(filename, relative_path, content)] -> a SHA-256 checksum register CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["filename", "relative_path", "sha256", "size_bytes"])
        for name, rel, content in rows:
            w.writerow([name, rel, hashlib.sha256(content).hexdigest(), len(content)])


def test_backup_raw_archive_copies_and_verifies(tmp_path):
    raw = tmp_path / "raw"
    (raw / "grpA").mkdir(parents=True)
    (raw / "grpA" / "a.tif").write_bytes(b"AAAA")
    (raw / "readme.txt").write_bytes(b"notes")
    reg = tmp_path / "SHA-256_Checksum_Register.csv"
    _write_register(reg, [("a.tif", "grpA/a.tif", b"AAAA"), ("readme.txt", "readme.txt", b"notes")])

    res = backup_raw_archive(raw, reg, tmp_path / "drive", "v01")

    assert res.dest == tmp_path / "drive" / "Raw_Archive_Backup_v01"
    assert res.files == 2 and res.verified == 2
    assert not res.missing and not res.mismatched
    assert (res.dest / "0_Raw_Data" / "grpA" / "a.tif").read_bytes() == b"AAAA"
    assert (res.dest / "SHA-256_Checksum_Register.csv").exists()  # register carried to root
    assert (res.dest / "README.md").exists()


def test_backup_raw_archive_detects_mismatch(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.bin").write_bytes(b"REAL")
    reg = tmp_path / "reg.csv"
    _write_register(reg, [("a.bin", "a.bin", b"WRONG")])  # register hash won't match the file
    with pytest.raises(PublishError):
        backup_raw_archive(raw, reg, tmp_path / "drive", "v01")


def test_backup_raw_archive_refuses_existing_label(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.bin").write_bytes(b"X")
    reg = tmp_path / "reg.csv"
    _write_register(reg, [("a.bin", "a.bin", b"X")])
    backup_raw_archive(raw, reg, tmp_path / "drive", "v01")
    with pytest.raises(PublishError):  # non-empty label dir must not be silently clobbered
        backup_raw_archive(raw, reg, tmp_path / "drive", "v01")
    # overwrite=True is allowed
    res = backup_raw_archive(raw, reg, tmp_path / "drive", "v01", overwrite=True)
    assert res.verified == 1


def _make_output(root: Path) -> None:
    """A minimal output tree: deliverables + a raw working copy that must be excluded."""
    arch = root / "00_Raw_Files_Archive"
    arch.mkdir(parents=True)
    (arch / "SHA-256_Checksum_Register.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (arch / "XV-023222_Buduunkhad_Inventory.xlsx").write_bytes(b"PK\x03\x04stub")
    # raw working copies live in evidence-group folders -> excluded
    wc = arch / "07_Basemap_Sentinel2_ASTER"
    wc.mkdir()
    (wc / "big_raster.tif").write_bytes(b"\x00" * 4096)
    (wc / "meta.txt").write_text("x", encoding="utf-8")  # non-deliverable suffix
    # phase 01 deliverable
    gpkg_dir = root / "01_Phase_1_Data_Audit_and_Master_GIS_Setup" / "06_Master_GeoPackage_Schema"
    gpkg_dir.mkdir(parents=True)
    (gpkg_dir / "XV-023222_Buduunkhad_Master_GIS_Database.gpkg").write_bytes(b"SQLite format 3\x00")
    # phase 02 derived COG (in a processing folder, not a working-copy dir) -> published
    p02 = root / "02_Phase_2_Remote_Sensing_Preprocessing" / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS"
    deriv = p02 / "04_Terrain_Derivatives"
    deriv.mkdir(parents=True)
    (deriv / "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif").write_bytes(b"II*\x00cog")
    # phase 03 evidence GPKG -> published, grouped under Phase03/
    p03 = (
        root
        / "03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis"
        / "09_Geological_Evidence_Layers_GPKG"
    )
    p03.mkdir(parents=True)
    (p03 / "XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg").write_bytes(
        b"SQLite format 3\x00"
    )


def _bind_publication_outputs(
    runs_root: Path,
    output_root: Path,
    *,
    phase_runs: dict[str, str] | None = None,
    provisional: set[str] | None = None,
    pending: set[str] | None = None,
    gate_states: dict[str, str] | None = None,
) -> None:
    grouped: dict[str, list[Path]] = {}
    for path in collect_deliverables(output_root):
        top = path.relative_to(output_root).parts[0]
        grouped.setdefault(top[:2], []).append(path)
    by_run: dict[str, list[dict[str, object]]] = {}
    for phase_id, paths in grouped.items():
        run_id = (phase_runs or {}).get(phase_id, "20260101T000000")
        by_run.setdefault(run_id, []).append(
            {
                "phase_id": phase_id,
                "status": "ok",
                "outputs": [str(path.resolve()) for path in sorted(paths)],
                "qaqc_passed": True,
                "qaqc_pending": phase_id in (pending or set()),
                "gate": {
                    "status": (gate_states or {}).get(phase_id, "go"),
                    "provisional": phase_id in (provisional or set()),
                },
            }
        )
    for run_id, phases in by_run.items():
        directory = runs_root / run_id
        directory.mkdir(parents=True)
        (directory / "run_manifest.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "dry_run": False,
                    "phases": sorted(phases, key=lambda phase: str(phase["phase_id"])),
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def test_collect_excludes_working_copies(tmp_path):
    _make_output(tmp_path)
    names = {p.name for p in collect_deliverables(tmp_path)}
    assert "XV-023222_Buduunkhad_Master_GIS_Database.gpkg" in names
    assert "SHA-256_Checksum_Register.csv" in names
    assert "XV-023222_Buduunkhad_Inventory.xlsx" in names
    assert "big_raster.tif" not in names  # raw working copy excluded
    assert "meta.txt" not in names  # non-deliverable extension excluded
    assert "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif" in names  # derived COG included
    assert "XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg" in names  # phase 03 included


def test_publish_copies_versioned_with_index(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    _make_output(out)
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    result = publish(out, tmp_path / "drive", "v0.1.0", runs_root=runs)

    assert result.dest.exists() and result.dest.name.endswith("v0.1.0")
    assert (result.dest / "INDEX.md").exists()
    assert (result.dest / "publication_manifest.json").exists()
    assert result.skipped_working_copies >= 1

    copied = {p.name for p in result.dest.rglob("*") if p.is_file()}
    assert "XV-023222_Buduunkhad_Master_GIS_Database.gpkg" in copied
    assert "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif" in copied  # derived COG published
    assert "big_raster.tif" not in copied  # never publish raw working copies

    # deliverables are grouped by two-digit phase prefix into PhaseNN/ (short, reader-friendly)
    assert (result.dest / "Phase01" / "XV-023222_Buduunkhad_Master_GIS_Database.gpkg").exists()
    assert (
        result.dest / "Phase02" / "XV023222_Buduunkhad_DEM_Hillshade_EPSG32647_v01.tif"
    ).exists()
    assert (
        result.dest / "Phase03" / "XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg"
    ).exists()


def test_publish_flattens_qgz_datasources(tmp_path):
    """The published .qgz must resolve its layers in the flat PhaseNN/ layout."""
    from buduunkhad.core.qgis_project import QgzLayer, read_qgz_layers, write_layered_qgz

    out = tmp_path / "out"
    (out / "01_Phase_1_Data_Audit_and_Master_GIS_Setup" / "08_Master_QGIS_Project_Setup").mkdir(
        parents=True
    )
    qgz = (
        out
        / "01_Phase_1_Data_Audit_and_Master_GIS_Setup"
        / "08_Master_QGIS_Project_Setup"
        / "XV-023222_Buduunkhad_Master_QGIS_Project.qgz"
    )
    write_layered_qgz(
        qgz,
        epsg=32647,
        title="T",
        layers=[
            QgzLayer(
                name="license_boundary",
                source="../05_KMZ_KML_to_GPKG/boundary.gpkg|layername=license_boundary",
                geometry="MultiPolygon",
            )
        ],
    )
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    result = publish(out, tmp_path / "drive", "vTEST", runs_root=runs)
    published = next(p for p in result.files if p.suffix == ".qgz")
    entries = read_qgz_layers(published)
    assert entries[0]["datasource"] == "./boundary.gpkg|layername=license_boundary"


def test_publish_refuses_existing_nonempty_label(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    _make_output(out)
    drive = tmp_path / "drive"
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    publish(out, drive, "v1", runs_root=runs)
    # re-publishing the same label would silently merge/overwrite -> must refuse
    with pytest.raises(PublishError):
        publish(out, drive, "v1", runs_root=runs)


def _write_manifest(runs_root, run_id, dry_run, phases):
    d = runs_root / run_id
    d.mkdir(parents=True)
    (d / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "dry_run": dry_run,
                "phases": [
                    {"phase_id": pid, "gate": {"status": st, "provisional": prov}}
                    for pid, st, prov in phases
                ],
            }
        ),
        encoding="utf-8",
    )


def test_latest_gate_per_phase_ignores_dry_and_takes_most_recent(tmp_path):
    runs = tmp_path / "runs"
    # ascending timestamps: an early real run, then a dry run, then a newer real run for 02/03
    _write_manifest(runs, "20260101T000000", False, [("00", "go", False), ("01", "go", False)])
    _write_manifest(runs, "20260102T000000", True, [("02", "go", False)])  # dry -> ignored
    _write_manifest(runs, "20260103T000000", False, [("02", "go", True), ("03", "go", True)])

    gates = latest_gate_per_phase(runs)
    assert set(gates) == {"00", "01", "02", "03"}
    assert gates["00"]["status"] == "go" and not gates["00"]["provisional"]
    assert gates["02"]["provisional"] is True  # from the real run, not the dry one
    assert gates["02"]["run_id"] == "20260103T000000"


def test_publish_detects_name_collision(tmp_path):
    out = tmp_path / "out"
    # two distinct files under the same phase prefix with the same basename -> flatten collision
    (out / "01_a").mkdir(parents=True)
    (out / "01_a" / "dup.gpkg").write_bytes(b"SQLite format 3\x00a")
    (out / "01_b").mkdir(parents=True)
    (out / "01_b" / "dup.gpkg").write_bytes(b"SQLite format 3\x00b")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    with pytest.raises(PublishError):
        publish(out, tmp_path / "drive", "v1", runs_root=runs)


def test_single_phase_publication_has_bound_provenance(tmp_path, monkeypatch):
    out = tmp_path / "out"
    deliverable = out / "04_Phase_4" / "ranking.csv"
    deliverable.parent.mkdir(parents=True)
    deliverable.write_text("candidate,score\nA,75\n", encoding="utf-8")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    monkeypatch.setattr("buduunkhad.core.publish._git_commit_sha", lambda _root: "a" * 40)

    result = publish(
        out,
        tmp_path / "staging",
        "single",
        runs_root=runs,
        published_at=datetime(2026, 7, 17, tzinfo=UTC),
    )
    manifest = load_publication_manifest(result.dest)

    assert manifest.included_phase_ids == ("04",)
    assert manifest.phases[0].source_run_id == "20260101T000000"
    assert manifest.phases[0].outputs[0].path == "Phase04/ranking.csv"
    assert manifest.package_status == "PROVISIONAL"  # automated GO is not approval
    assert verify_publication_package(result.dest) == manifest


def test_multi_phase_publication_keeps_distinct_source_runs(tmp_path):
    out = tmp_path / "out"
    for phase_id in ("01", "04"):
        path = out / f"{phase_id}_Phase" / f"phase{phase_id}.csv"
        path.parent.mkdir(parents=True)
        path.write_text(phase_id, encoding="utf-8")
    runs = tmp_path / "runs"
    _bind_publication_outputs(
        runs,
        out,
        phase_runs={"01": "20260101T010101", "04": "20260202T020202"},
    )

    result = publish(out, tmp_path / "staging", "multi", runs_root=runs)
    manifest = load_publication_manifest(result.dest)

    assert {phase.phase_id: phase.source_run_id for phase in manifest.phases} == {
        "01": "20260101T010101",
        "04": "20260202T020202",
    }
    assert len({phase.source_run_manifest_sha256 for phase in manifest.phases}) == 2
    index = (result.dest / "INDEX.md").read_text(encoding="utf-8")
    assert "does not make them one scientific execution or one approval event" in index
    assert "run 20260101T010101" in index and "run 20260202T020202" in index


def test_pending_or_provisional_phase_marks_package_nonapproved(tmp_path):
    out = tmp_path / "out"
    for phase_id in ("03", "04"):
        path = out / f"{phase_id}_Phase" / f"phase{phase_id}.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}", encoding="utf-8")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, provisional={"04"}, pending={"03"})

    result = publish(out, tmp_path / "staging", "pending", runs_root=runs)
    manifest = load_publication_manifest(result.dest)

    assert manifest.package_status == "HUMAN_REVIEW_PENDING"
    assert manifest.phases[0].pending_human_review_or_qaqc_count is None
    index = (result.dest / "INDEX.md").read_text(encoding="utf-8")
    assert "**Package status:** HUMAN_REVIEW_PENDING" in index
    assert "human review / QA/QC pending" in index


def test_publish_fails_when_source_run_output_is_missing(tmp_path):
    out = tmp_path / "out"
    output = out / "02_Phase" / "derived.tif"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"II*\x00")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    output.unlink()

    with pytest.raises(PublishError, match="missing output"):
        publish(out, tmp_path / "staging", "missing", runs_root=runs)


def test_publication_verification_detects_output_tampering(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "evidence.gpkg"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"SQLite format 3\x00original")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    result = publish(out, tmp_path / "staging", "tamper", runs_root=runs)

    (result.dest / "Phase01" / "evidence.gpkg").write_bytes(b"changed")
    with pytest.raises(PublishError, match="missing or changed"):
        verify_publication_package(result.dest)


def test_git_metadata_unavailable_is_recorded_truthfully(tmp_path, monkeypatch):
    out = tmp_path / "out"
    output = out / "00_Phase" / "inventory.csv"
    output.parent.mkdir(parents=True)
    output.write_text("id\n1\n", encoding="utf-8")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    monkeypatch.setattr("buduunkhad.core.publish._git_commit_sha", lambda _root: None)

    result = publish(out, tmp_path / "staging", "unknown-git", runs_root=runs)

    assert load_publication_manifest(result.dest).git_commit_sha is None


def test_publication_id_is_stable_for_identical_identity_inputs(tmp_path, monkeypatch):
    out = tmp_path / "out"
    output = out / "03_Phase" / "evidence.csv"
    output.parent.mkdir(parents=True)
    output.write_text("feature_id\nA\n", encoding="utf-8")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    monkeypatch.setattr("buduunkhad.core.publish._git_commit_sha", lambda _root: "b" * 40)

    first = publish(
        out,
        tmp_path / "one",
        "same",
        runs_root=runs,
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    second = publish(
        out,
        tmp_path / "two",
        "different-label",
        runs_root=runs,
        published_at=datetime(2026, 2, 2, tzinfo=UTC),
    )

    assert (
        load_publication_manifest(first.dest).publication_id
        == load_publication_manifest(second.dest).publication_id
    )


def test_publication_manifest_paths_are_relative_and_label_cannot_escape(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.gpkg"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"SQLite format 3\x00")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    result = publish(out, tmp_path / "staging", "relative", runs_root=runs)

    manifest = load_publication_manifest(result.dest)
    recorded_paths = [
        *(phase.source_run_manifest_path for phase in manifest.phases),
        *(output.path for phase in manifest.phases for output in phase.outputs),
    ]
    assert all(
        not Path(path).is_absolute() and ".." not in Path(path).parts for path in recorded_paths
    )
    with pytest.raises(PublishError, match="path-safe"):
        publish(out, tmp_path / "staging", "../escape", runs_root=runs)


def test_publication_manifest_leaks_no_paths_roots_or_credentials(tmp_path, monkeypatch):
    out = tmp_path / "machine" / "outputs"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_text("ok\n", encoding="utf-8")
    runs = tmp_path / "machine" / "runs"
    _bind_publication_outputs(runs, out)
    secrets = {
        "BUDUUNKHAD_RAW_ROOT": str(tmp_path / "private-raw"),
        "BUDUUNKHAD_SNAPSHOT_ROOT": str(tmp_path / "private-snapshot"),
        "OPENAI" + "_API_KEY": "synthetic-redacted-value",
        "AWS_SECRET" + "_ACCESS_KEY": "synthetic-redacted-aws-value",
    }
    for key, value in secrets.items():
        monkeypatch.setenv(key, value)

    result = publish(out, tmp_path / "staging", "clean", runs_root=runs)
    public_text = (result.dest / "publication_manifest.json").read_text(encoding="utf-8")
    public_text += (result.dest / "INDEX.md").read_text(encoding="utf-8")

    assert str(tmp_path) not in public_text
    assert all(value not in public_text for value in secrets.values())


def test_existing_run_manifest_is_copied_byte_for_byte(tmp_path):
    out = tmp_path / "out"
    output = out / "04_Phase" / "ranking.csv"
    output.parent.mkdir(parents=True)
    output.write_text("score\n75\n", encoding="utf-8")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    source_manifest = next(runs.glob("*/run_manifest.json"))
    before = source_manifest.read_bytes()

    result = publish(out, tmp_path / "staging", "compat", runs_root=runs)
    manifest = load_publication_manifest(result.dest)

    assert source_manifest.read_bytes() == before
    assert (result.dest / "run_manifest.json").read_bytes() == before
    copied_source = result.dest / manifest.phases[0].source_run_manifest_path
    assert copied_source.read_bytes() == before


def test_explicit_superseded_publication_id_is_recorded(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_text("ok\n", encoding="utf-8")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    superseded = f"pub-{'c' * 32}"

    result = publish(
        out,
        tmp_path / "staging",
        "replacement",
        runs_root=runs,
        superseded_publication_id=superseded,
    )

    assert load_publication_manifest(result.dest).superseded_publication_id == superseded


def test_publish_accepts_current_pipeline_run_manifest_contract(raw_archive):
    from buduunkhad.pipeline import run_pipeline

    config, register, _raw = raw_archive
    run_pipeline(config, register, only=["00"], dry_run=False)

    result = publish(
        config.output_root,
        config.base_dir / "publication-staging",
        "phase00",
        runs_root=config.runs_root,
        project_config_path=config.base_dir / "config" / "project.yaml",
    )

    manifest = verify_publication_package(result.dest)
    assert manifest.included_phase_ids == ("00",)
    assert manifest.phases[0].human_review_or_qaqc_pending is True
    assert manifest.package_status == "HUMAN_REVIEW_PENDING"


def test_package_version_authorities_are_synchronized():
    import tomllib

    from buduunkhad import __version__

    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == __version__ == "0.8.1"
