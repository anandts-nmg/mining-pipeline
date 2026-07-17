"""Tests for the deliverable publish step (core.publish)."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from buduunkhad.core.publication_manifest import (
    AGGREGATION_NOTICE,
    PUBLICATION_MANIFEST_FORMAT_VERSION,
    CompatibilityRunManifest,
    PublicationManifest,
    PublicationProjectReference,
    PublishedOutput,
    PublishedPhase,
    publication_id_for,
    publication_status_for,
)
from buduunkhad.core.publish import (
    PublishError,
    _package_file_claims,
    backup_raw_archive,
    collect_deliverables,
    latest_gate_per_phase,
    load_publication_manifest,
    publish,
    verify_publication_package,
)


def _recompute_publication_id(data: dict[str, object]) -> None:
    phases = tuple(PublishedPhase.model_validate(value) for value in data["phases"])  # type: ignore[union-attr]
    project = PublicationProjectReference.model_validate(data["project"])
    compatibility = CompatibilityRunManifest.model_validate(data["compatibility_run_manifest"])
    data["publication_id"] = publication_id_for(
        project=project,
        package_version=str(data["package_version"]),
        git_commit_sha=data["git_commit_sha"] if isinstance(data["git_commit_sha"], str) else None,
        phases=phases,
        package_status=data["package_status"],  # type: ignore[arg-type]
        compatibility_run_manifest=compatibility,
        superseded_publication_id=(
            data["superseded_publication_id"]
            if isinstance(data["superseded_publication_id"], str)
            else None
        ),
    )


def _tamper_manifest(
    package: Path, mutate: Callable[[dict[str, object]], None], *, recompute_id: bool = True
) -> None:
    path = package / "publication_manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    if recompute_id:
        _recompute_publication_id(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _create_symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as exc:
        pytest.skip(f"operating system cannot create the required symlink: {exc}")


def _contract_phase(
    phase_id: str,
    *,
    published_path: str | None = None,
    source_path: str | None = None,
    legacy: bool = False,
) -> PublishedPhase:
    run_id = f"run-{phase_id}"
    return PublishedPhase(
        phase_id=phase_id,
        source_run_id=run_id,
        source_started_at="2026-01-01T00:00:00+00:00",
        source_finished_at="2026-01-01T00:01:00+00:00",
        source_run_manifest_path=f"source_run_manifests/{run_id}/run_manifest.json",
        source_run_manifest_sha256=phase_id[0] * 64,
        execution_status="ok",
        gate_state="go",
        gate_provisional=False,
        human_review_or_qaqc_pending=False,
        pending_human_review_or_qaqc_count=0,
        source_binding_mode="LEGACY_PATH_ONLY" if legacy else "SHA256_BOUND",
        outputs=(
            PublishedOutput(
                path=published_path or f"Phase{phase_id}/shared.csv",
                sha256="a" * 64,
                size_bytes=7,
                source_path=source_path or f"{phase_id}_Anything/shared.csv",
                source_sha256=None if legacy else "a" * 64,
                source_size_bytes=None if legacy else 7,
            ),
        ),
    )


def test_published_phase_rejects_duplicate_paths_inside_one_phase() -> None:
    phase = _contract_phase("01")
    with pytest.raises(ValueError, match="duplicate output paths"):
        PublishedPhase.model_validate(
            phase.model_dump() | {"outputs": [phase.outputs[0], phase.outputs[0]]}
        )


@pytest.mark.parametrize(
    "published_path",
    ["Phase02/evidence.gpkg", "shared/evidence.gpkg", "Phase010/evidence.gpkg"],
)
def test_published_phase_rejects_wrong_or_misleading_package_directory(
    published_path: str,
) -> None:
    with pytest.raises(ValueError, match="published output path does not belong to Phase01"):
        _contract_phase("01", published_path=published_path)


@pytest.mark.parametrize("legacy", [False, True])
def test_published_phase_rejects_source_path_owned_by_another_phase(legacy: bool) -> None:
    with pytest.raises(ValueError, match="source output path does not belong to Phase02"):
        _contract_phase(
            "02",
            source_path="01_Phase_1_Data_Audit/shared.csv",
            legacy=legacy,
        )


@pytest.mark.parametrize("phase_id", [*(f"{value:02d}" for value in range(12)), "99"])
def test_published_phase_accepts_all_registered_phase_path_conventions(phase_id: str) -> None:
    phase = _contract_phase(phase_id)
    assert phase.outputs[0].path == f"Phase{phase_id}/shared.csv"
    assert phase.outputs[0].source_path == f"{phase_id}_Anything/shared.csv"


def test_manifest_rejects_identical_bytes_claimed_at_one_path_by_two_phases() -> None:
    phase01 = _contract_phase("01")
    phase02 = _contract_phase("02")
    duplicate_output = phase02.outputs[0].model_copy(update={"path": phase01.outputs[0].path})
    tampered_phase02 = phase02.model_copy(update={"outputs": (duplicate_output,)})
    phases = (phase01, tampered_phase02)
    compatibility = CompatibilityRunManifest(
        run_id=phase01.source_run_id,
        path="run_manifest.json",
        sha256=phase01.source_run_manifest_sha256,
    )
    status = publication_status_for(phases)
    project = PublicationProjectReference(
        configuration_reference="config/project.yaml",
        configuration_sha256="f" * 64,
    )
    recomputed_id = publication_id_for(
        project=project,
        package_version="0.8.1",
        git_commit_sha=None,
        phases=phases,
        package_status=status,
        compatibility_run_manifest=compatibility,
        superseded_publication_id=None,
    )
    data = {
        "manifest_format_version": PUBLICATION_MANIFEST_FORMAT_VERSION,
        "project": project,
        "package_version": "0.8.1",
        "git_commit_sha": None,
        "published_at": "2026-01-01T00:00:00+00:00",
        "publication_id": recomputed_id,
        "included_phase_ids": ("01", "02"),
        "phases": tuple(phase.model_dump() for phase in phases),
        "package_status": status,
        "compatibility_run_manifest": compatibility,
        "aggregation_notice": AGGREGATION_NOTICE,
        "superseded_publication_id": None,
    }

    assert phase01.outputs[0].sha256 == tampered_phase02.outputs[0].sha256
    assert phase01.outputs[0].size_bytes == tampered_phase02.outputs[0].size_bytes
    with pytest.raises(ValueError, match="publication output paths must be globally unique"):
        PublicationManifest.model_validate(data)


def test_verifier_claim_inventory_rejects_collision_before_allowlisting() -> None:
    phase = _contract_phase("01")
    compatibility = CompatibilityRunManifest(
        run_id=phase.source_run_id,
        path="run_manifest.json",
        sha256=phase.source_run_manifest_sha256,
    )
    project = PublicationProjectReference(
        configuration_reference="config/project.yaml",
        configuration_sha256="f" * 64,
    )
    status = publication_status_for((phase,))
    manifest = PublicationManifest(
        manifest_format_version=PUBLICATION_MANIFEST_FORMAT_VERSION,
        project=project,
        package_version="0.8.1",
        git_commit_sha=None,
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        publication_id=publication_id_for(
            project=project,
            package_version="0.8.1",
            git_commit_sha=None,
            phases=(phase,),
            package_status=status,
            compatibility_run_manifest=compatibility,
            superseded_publication_id=None,
        ),
        included_phase_ids=("01",),
        phases=(phase,),
        package_status=status,
        compatibility_run_manifest=compatibility,
        aggregation_notice=AGGREGATION_NOTICE,
    )
    colliding_output = phase.outputs[0].model_copy(update={"path": phase.source_run_manifest_path})
    colliding_phase = phase.model_copy(update={"outputs": (colliding_output,)})
    malformed = manifest.model_copy(update={"phases": (colliding_phase,)})

    with pytest.raises(PublishError, match="publication package path has conflicting claims"):
        _package_file_claims(malformed)


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
    legacy: bool = False,
) -> None:
    grouped: dict[str, list[Path]] = {}
    for path in collect_deliverables(output_root):
        top = path.relative_to(output_root).parts[0]
        grouped.setdefault(top[:2], []).append(path)
    by_run: dict[str, list[dict[str, object]]] = {}
    for phase_id, paths in grouped.items():
        run_id = (phase_runs or {}).get(phase_id, "20260101T000000")
        phase: dict[str, object] = {
            "phase_id": phase_id,
            "status": "ok",
            "outputs": [str(path.resolve()) for path in sorted(paths)],
            "qaqc_passed": True,
            "qaqc_pending": phase_id in (pending or set()),
            "pending_human_review_or_qaqc_count": (1 if phase_id in (pending or set()) else 0),
            "gate": {
                "status": (gate_states or {}).get(phase_id, "go"),
                "provisional": phase_id in (provisional or set()),
            },
        }
        if not legacy:
            phase["output_artifacts"] = [
                {
                    "path": path.relative_to(output_root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "size_bytes": path.stat().st_size,
                }
                for path in sorted(paths)
            ]
        by_run.setdefault(run_id, []).append(phase)
    for run_id, phases in by_run.items():
        directory = runs_root / run_id
        directory.mkdir(parents=True)
        (directory / "run_manifest.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "started_at": "2026-01-01T00:00:00+00:00",
                    "finished_at": "2026-01-01T00:01:00+00:00",
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
    recorded = load_publication_manifest(result.dest).phases[0].outputs[0]
    assert recorded.source_sha256 == hashlib.sha256(qgz.read_bytes()).hexdigest()
    assert recorded.sha256 == hashlib.sha256(published.read_bytes()).hexdigest()
    assert recorded.source_sha256 != recorded.sha256
    assert recorded.transformation_id == "qgz-flat-datasource-rewrite-v1"


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


def _write_manifest(runs_root, run_id, dry_run, phases, *, finished_at=None):
    d = runs_root / run_id
    d.mkdir(parents=True)
    completion = (
        finished_at or datetime.strptime(run_id, "%Y%m%dT%H%M%S").replace(tzinfo=UTC).isoformat()
    )
    (d / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "finished_at": completion,
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


def test_latest_gate_helper_uses_recorded_time_not_custom_run_id_order(tmp_path):
    runs = tmp_path / "runs"
    _write_manifest(
        runs,
        "zzz-older",
        False,
        [("04", "blocked", True)],
        finished_at="2026-01-01T00:00:00+00:00",
    )
    _write_manifest(
        runs,
        "aaa-newer",
        False,
        [("04", "go", False)],
        finished_at="2026-02-01T00:00:00+00:00",
    )

    assert latest_gate_per_phase(runs)["04"]["run_id"] == "aaa-newer"


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
    assert manifest.phases[0].source_binding_mode == "SHA256_BOUND"
    assert manifest.phases[0].outputs[0].source_sha256 == manifest.phases[0].outputs[0].sha256
    assert (
        manifest.phases[0].outputs[0].source_size_bytes == manifest.phases[0].outputs[0].size_bytes
    )
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
    assert manifest.phases[0].pending_human_review_or_qaqc_count == 1
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


def test_source_output_changed_after_run_is_rejected(tmp_path):
    out = tmp_path / "out"
    output = out / "04_Phase" / "ranking.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"sealed")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    output.write_bytes(b"changed")

    with pytest.raises(PublishError, match="no SHA256-bound source run exactly matches"):
        publish(out, tmp_path / "staging", "changed-source", runs_root=runs)


def test_source_output_changed_during_copy_is_rejected(tmp_path, monkeypatch):
    out = tmp_path / "out"
    output = out / "04_Phase" / "ranking.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"sealed")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    original_copy2 = shutil.copy2

    def copy_then_mutate(source, target, *args, **kwargs):  # type: ignore[no-untyped-def]
        copied = original_copy2(source, target, *args, **kwargs)
        if Path(source).resolve() == output.resolve():
            output.write_bytes(b"changed-during-copy")
        return copied

    monkeypatch.setattr("buduunkhad.core.publish.shutil.copy2", copy_then_mutate)

    with pytest.raises(PublishError, match="source output changed while publishing"):
        publish(out, tmp_path / "staging", "copy-race", runs_root=runs)
    assert not (
        tmp_path / "staging" / "Buduunkhad_Deliverables_copy-race" / "publication_manifest.json"
    ).exists()


def test_incorrect_source_artifact_size_is_rejected(tmp_path):
    out = tmp_path / "out"
    output = out / "02_Phase" / "derived.tif"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"II*\x00payload")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    path = next(runs.glob("*/run_manifest.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    data["phases"][0]["output_artifacts"][0]["size_bytes"] += 1
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    with pytest.raises(PublishError, match="no SHA256-bound source run exactly matches"):
        publish(out, tmp_path / "staging", "wrong-size", runs_root=runs)


def test_sha256_source_selection_ignores_nonchronological_run_ids(tmp_path):
    out = tmp_path / "out"
    output = out / "04_Phase" / "ranking.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"current")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, phase_runs={"04": "aaa-current"})
    output.write_bytes(b"stale")
    _bind_publication_outputs(runs, out, phase_runs={"04": "zzz-stale"})
    output.write_bytes(b"current")

    result = publish(out, tmp_path / "staging", "content-selected", runs_root=runs)

    assert load_publication_manifest(result.dest).phases[0].source_run_id == "aaa-current"


def test_sha256_artifact_paths_remain_portable_when_output_root_moves(tmp_path):
    original = tmp_path / "original-output"
    output = original / "04_Phase" / "ranking.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"ranking")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, original)
    moved = tmp_path / "moved-output"
    original.rename(moved)

    result = publish(moved, tmp_path / "staging", "moved", runs_root=runs)

    manifest = verify_publication_package(result.dest)
    assert manifest.phases[0].source_binding_mode == "SHA256_BOUND"
    assert manifest.phases[0].outputs[0].source_path == "04_Phase/ranking.csv"


def test_ambiguous_matching_runs_require_explicit_selector(tmp_path):
    out = tmp_path / "out"
    output = out / "03_Phase" / "evidence.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"same")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, phase_runs={"03": "run-a"})
    _bind_publication_outputs(runs, out, phase_runs={"03": "run-b"})

    with pytest.raises(PublishError, match="matches multiple source runs"):
        publish(out, tmp_path / "staging-one", "ambiguous", runs_root=runs)

    result = publish(
        out,
        tmp_path / "staging-two",
        "selected",
        runs_root=runs,
        source_runs={"03": "run-b"},
    )
    assert load_publication_manifest(result.dest).phases[0].source_run_id == "run-b"


def test_internal_run_id_must_match_directory_name(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"master")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, phase_runs={"01": "actual-run"})
    manifest_path = runs / "actual-run" / "run_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["run_id"] = "claimed-run"
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    with pytest.raises(PublishError, match="does not match its directory"):
        publish(out, tmp_path / "staging", "mismatch", runs_root=runs)


def test_legacy_manifest_is_path_only_and_can_never_be_approved(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"legacy")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, legacy=True, gate_states={"01": "APPROVED"})

    result = publish(out, tmp_path / "staging", "legacy", runs_root=runs)
    manifest = load_publication_manifest(result.dest)

    assert manifest.phases[0].source_binding_mode == "LEGACY_PATH_ONLY"
    assert manifest.phases[0].outputs[0].source_sha256 is None
    assert manifest.package_status == "PROVISIONAL"
    index = (result.dest / "INDEX.md").read_text(encoding="utf-8")
    assert "**Integrity limitation:**" in index
    assert "cannot be APPROVED" in index


def test_legacy_manifest_may_omit_historical_runner_qaqc_inventory(tmp_path):
    out = tmp_path / "out"
    phase_dir = out / "01_Phase"
    phase_dir.mkdir(parents=True)
    (phase_dir / "master.csv").write_bytes(b"legacy")
    (phase_dir / "BUD_Phase01_QAQC_Log.xlsx").write_bytes(b"legacy-qaqc")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, legacy=True)
    source_manifest = next(runs.glob("*/run_manifest.json"))
    data = json.loads(source_manifest.read_text(encoding="utf-8"))
    data["phases"][0]["outputs"] = [
        value for value in data["phases"][0]["outputs"] if not value.endswith("_QAQC_Log.xlsx")
    ]
    source_manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = publish(out, tmp_path / "staging", "old-runner", runs_root=runs)

    manifest = verify_publication_package(result.dest)
    assert manifest.phases[0].source_binding_mode == "LEGACY_PATH_ONLY"
    assert {output.path for output in manifest.phases[0].outputs} == {
        "Phase01/BUD_Phase01_QAQC_Log.xlsx",
        "Phase01/master.csv",
    }


def test_explicit_null_artifact_inventory_cannot_downgrade_to_legacy(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"sealed")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    source_manifest = next(runs.glob("*/run_manifest.json"))
    data = json.loads(source_manifest.read_text(encoding="utf-8"))
    data["phases"][0]["output_artifacts"] = None
    source_manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    with pytest.raises(PublishError, match="output_artifacts is invalid"):
        publish(out, tmp_path / "staging", "null-inventory", runs_root=runs)


def test_pending_count_tampering_fails_even_with_recomputed_publication_id(tmp_path):
    out = tmp_path / "out"
    output = out / "03_Phase" / "evidence.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"evidence")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, pending={"03"})
    result = publish(out, tmp_path / "staging", "pending-tamper", runs_root=runs)

    def mutate(data: dict[str, object]) -> None:
        data["phases"][0]["pending_human_review_or_qaqc_count"] = 9  # type: ignore[index]

    _tamper_manifest(result.dest, mutate)
    with pytest.raises(PublishError, match="gate provenance mismatch"):
        verify_publication_package(result.dest)


def test_source_artifact_metadata_tampering_fails_with_recomputed_id(tmp_path):
    out = tmp_path / "out"
    output = out / "02_Phase" / "derived.tif"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"derived")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    result = publish(out, tmp_path / "staging", "artifact-tamper", runs_root=runs)
    manifest = load_publication_manifest(result.dest)
    source_copy = result.dest / manifest.phases[0].source_run_manifest_path
    source_data = json.loads(source_copy.read_text(encoding="utf-8"))
    source_data["phases"][0]["output_artifacts"][0]["sha256"] = "f" * 64
    changed_bytes = (json.dumps(source_data, indent=2) + "\n").encode()
    source_copy.write_bytes(changed_bytes)
    (result.dest / "run_manifest.json").write_bytes(changed_bytes)
    changed_hash = hashlib.sha256(changed_bytes).hexdigest()

    def mutate(data: dict[str, object]) -> None:
        data["phases"][0]["source_run_manifest_sha256"] = changed_hash  # type: ignore[index]
        data["compatibility_run_manifest"]["sha256"] = changed_hash  # type: ignore[index]

    _tamper_manifest(result.dest, mutate)
    with pytest.raises(PublishError, match="source artifact identity mismatch"):
        verify_publication_package(result.dest)


def test_output_symlink_escape_is_rejected(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    external = tmp_path / "outside.csv"
    external.write_bytes(b"outside")
    _create_symlink_or_skip(output, external)
    runs = tmp_path / "runs"
    runs.mkdir()

    with pytest.raises(PublishError, match="symlink"):
        publish(out, tmp_path / "staging", "output-link", runs_root=runs)


def test_source_run_manifest_symlink_escape_is_rejected(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"master")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    manifest_path = next(runs.glob("*/run_manifest.json"))
    external = tmp_path / "outside-manifest.json"
    external.write_bytes(manifest_path.read_bytes())
    manifest_path.unlink()
    _create_symlink_or_skip(manifest_path, external)

    with pytest.raises(PublishError, match="symlink"):
        publish(out, tmp_path / "staging", "manifest-link", runs_root=runs)


def test_verification_rejects_substituted_output_symlink(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"master")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    result = publish(out, tmp_path / "staging", "package-link", runs_root=runs)
    published = result.dest / "Phase01" / "master.csv"
    external = tmp_path / "same-bytes.csv"
    external.write_bytes(published.read_bytes())
    published.unlink()
    _create_symlink_or_skip(published, external)

    with pytest.raises(PublishError, match="symlink"):
        verify_publication_package(result.dest)


def test_index_change_and_unexpected_file_are_rejected(tmp_path):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"master")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    first = publish(out, tmp_path / "one", "index", runs_root=runs)
    (first.dest / "INDEX.md").write_text("misleading status", encoding="utf-8")
    with pytest.raises(PublishError, match="INDEX.md"):
        verify_publication_package(first.dest)

    second = publish(out, tmp_path / "two", "extra", runs_root=runs)
    (second.dest / "unrecorded-report.pdf").write_bytes(b"unrecorded")
    with pytest.raises(PublishError, match="unexpected file"):
        verify_publication_package(second.dest)


def test_compatibility_manifest_change_is_rejected(tmp_path):
    out = tmp_path / "out"
    output = out / "04_Phase" / "ranking.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"ranking")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    result = publish(out, tmp_path / "staging", "compat-tamper", runs_root=runs)
    (result.dest / "run_manifest.json").write_text("{}", encoding="utf-8")

    with pytest.raises(PublishError, match="compatibility root"):
        verify_publication_package(result.dest)


def test_unrelated_dry_run_is_never_the_compatibility_manifest(tmp_path):
    out = tmp_path / "out"
    output = out / "04_Phase" / "ranking.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"ranking")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out, phase_runs={"04": "aaa-selected"})
    dry_dir = runs / "zzz-dry-run"
    dry_dir.mkdir(parents=True)
    (dry_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_id": "zzz-dry-run",
                "started_at": "2026-07-17T10:00:00+00:00",
                "finished_at": "2026-07-17T10:01:00+00:00",
                "dry_run": True,
                "phases": [],
            }
        ),
        encoding="utf-8",
    )

    result = publish(out, tmp_path / "staging", "compat-source", runs_root=runs)
    manifest = load_publication_manifest(result.dest)
    assert manifest.compatibility_run_manifest.run_id == "aaa-selected"
    assert json.loads((result.dest / "run_manifest.json").read_text())["run_id"] == "aaa-selected"


def test_publication_roots_must_not_overlap(tmp_path):
    out = tmp_path / "workspace" / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"master")
    runs = tmp_path / "workspace" / "runs"
    _bind_publication_outputs(runs, out)

    with pytest.raises(PublishError, match="must not overlap"):
        publish(out, tmp_path / "workspace", "recursive", runs_root=runs)


def test_publication_identity_changes_for_every_recorded_identity_group(tmp_path, monkeypatch):
    out = tmp_path / "out"
    output = out / "01_Phase" / "master.csv"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"master")
    runs = tmp_path / "runs"
    _bind_publication_outputs(runs, out)
    monkeypatch.setattr("buduunkhad.core.publish._git_commit_sha", lambda _root: "a" * 40)
    result = publish(out, tmp_path / "staging", "identity", runs_root=runs)
    manifest = load_publication_manifest(result.dest)
    phase = manifest.phases[0]
    output_record = phase.outputs[0]

    variants = [
        {"project": manifest.project.model_copy(update={"configuration_sha256": "b" * 64})},
        {"package_version": "9.9.9"},
        {"git_commit_sha": "c" * 40},
        {
            "phases": (
                phase.model_copy(
                    update={
                        "outputs": (
                            output_record.model_copy(update={"source_path": "01_Phase/other.csv"}),
                        )
                    }
                ),
            )
        },
        {"phases": (phase.model_copy(update={"source_run_id": "different-run"}),)},
        {"phases": (phase.model_copy(update={"source_binding_mode": "LEGACY_PATH_ONLY"}),)},
        {"phases": (phase.model_copy(update={"gate_state": "different-gate"}),)},
        {
            "phases": (
                phase.model_copy(
                    update={
                        "outputs": (
                            output_record.model_copy(
                                update={
                                    "sha256": "1" * 64,
                                    "source_sha256": "1" * 64,
                                }
                            ),
                        )
                    }
                ),
            )
        },
        {
            "phases": (
                phase.model_copy(
                    update={
                        "outputs": (
                            output_record.model_copy(
                                update={"transformation_id": "qgz-flat-datasource-rewrite-v1"}
                            ),
                        )
                    }
                ),
            )
        },
        {
            "compatibility_run_manifest": manifest.compatibility_run_manifest.model_copy(
                update={"sha256": "d" * 64}
            )
        },
        {"superseded_publication_id": f"pub-{'e' * 32}"},
    ]
    for update in variants:
        changed = publication_id_for(
            project=update.get("project", manifest.project),
            package_version=update.get("package_version", manifest.package_version),
            git_commit_sha=update.get("git_commit_sha", manifest.git_commit_sha),
            phases=update.get("phases", manifest.phases),
            package_status=manifest.package_status,
            compatibility_run_manifest=update.get(
                "compatibility_run_manifest", manifest.compatibility_run_manifest
            ),
            superseded_publication_id=update.get(
                "superseded_publication_id", manifest.superseded_publication_id
            ),
        )
        assert changed != manifest.publication_id


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
    assert manifest.phases[0].source_binding_mode == "SHA256_BOUND"
    assert any(
        output.source_path.endswith("_Phase00_QAQC_Log.xlsx")
        for output in manifest.phases[0].outputs
    )
    assert manifest.phases[0].human_review_or_qaqc_pending is True
    assert manifest.package_status == "HUMAN_REVIEW_PENDING"


def test_package_version_authorities_are_synchronized():
    import tomllib

    from buduunkhad import __version__

    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == __version__ == "0.8.1"


def test_publish_cli_keeps_existing_options_and_adds_repeatable_source_run_selector():
    from click import unstyle
    from typer.testing import CliRunner

    from buduunkhad.cli import app

    result = CliRunner().invoke(app, ["publish", "--help"])
    help_text = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--label" in help_text
    assert "--supersedes" in help_text
    assert "--source-run" in help_text
