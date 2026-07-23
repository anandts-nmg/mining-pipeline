"""Adversarial tests for exact accepted-evidence authority and byte binding."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import geopandas as gpd
import pytest
from pydantic import ValidationError
from shapely.geometry import LineString, Polygon

from buduunkhad.core.evidence_manifest import (
    EvidenceAuthorityResolver,
    EvidenceCatalogEntry,
    EvidenceExecutionMode,
    EvidenceLifecycleState,
    EvidenceManifest,
    EvidenceManifestError,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceRole,
    EvidenceSourceKind,
    register_phase03_promotion_evidence,
    register_pipeline_evidence,
)
from buduunkhad.core.run_artifacts import RunOutputArtifact, sha256_file
from buduunkhad.geospatial_ai.phase03_handoff import PromotedFeature, PromotionAuditEntry
from buduunkhad.pipeline import run_pipeline


def _sealed_pipeline_source(tmp_path: Path) -> tuple[Path, Path, Path]:
    runs_root = tmp_path / "runs"
    run_directory = runs_root / "source-run"
    phase_directory = run_directory / "phases" / "03"
    phase_directory.mkdir(parents=True)
    artifact = phase_directory / "support.gpkg"
    gpd.GeoDataFrame(  # ty: ignore[no-matching-overload]
        {"class": ["fault"], "geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 0)])]},
        crs="EPSG:32647",
    ).to_file(artifact, layer="support_polygon", driver="GPKG")
    seal = RunOutputArtifact(
        path="phases/03/support.gpkg",
        sha256=sha256_file(artifact),
        size_bytes=artifact.stat().st_size,
    )
    now = datetime(2026, 7, 23, tzinfo=UTC).isoformat()
    run_manifest = {
        "manifest_format_version": "2.1.0",
        "run_layout_version": "run-isolated-v1",
        "run_id": "source-run",
        "started_at": now,
        "finished_at": now,
        "dry_run": False,
        "override": False,
        "selected_phases": ["03"],
        "stopped_at": "03",
        "error": "",
        "warnings": [],
        "execution_identity": {},
        "evidence_manifests": [],
        "phases": [
            {
                "phase_id": "03",
                "name": "synthetic source",
                "mode": "orchestrate",
                "status": "ok",
                "outputs": [seal.path],
                "output_artifacts": [seal.model_dump(mode="json")],
                "sealed_files": [seal.model_dump(mode="json")],
                "qaqc_passed": True,
                "qaqc_pending": False,
                "pending_human_review_or_qaqc_count": 0,
                "gate": {
                    "status": "blocked",
                    "reason": "scientific handoff remains pending",
                    "overridden": False,
                    "provisional": False,
                },
                "error": "",
            }
        ],
    }
    authority = run_directory / "run_manifest.json"
    authority.write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")
    return runs_root, authority, artifact


def _record(authority: Path, artifact: Path, **updates: object) -> EvidenceRecord:
    values: dict[str, object] = {
        "evidence_id": "EV-pipeline-support",
        "source_kind": EvidenceSourceKind.PIPELINE_RUN,
        "source_run_id": "source-run",
        "source_authority_path": "run_manifest.json",
        "source_authority_sha256": sha256_file(authority),
        "artifact_path": "phases/03/support.gpkg",
        "artifact_sha256": sha256_file(artifact),
        "artifact_size_bytes": artifact.stat().st_size,
        "layer_name": "support_polygon",
        "target_layer_name": "geology_units_50k_polygon",
        "evidence_role": EvidenceRole.GEOLOGY,
        "origin": EvidenceOrigin.HUMAN_DIGITIZED,
        "lifecycle_state": EvidenceLifecycleState.SEALED_SUPPORT_EVIDENCE,
        "eligible_phases": ("03",),
        "eligible_modes": (EvidenceExecutionMode.SUPPORT_EVIDENCE,),
        "limitations": ("Synthetic support evidence for contract tests.",),
    }
    values.update(updates)
    return EvidenceRecord.model_validate(values)


def _manifest(record: EvidenceRecord) -> EvidenceManifest:
    return EvidenceManifest.create(records=(record,))


def _write_manifest(
    resolver: EvidenceAuthorityResolver,
    manifest: EvidenceManifest,
) -> Path:
    return resolver.write(
        manifest,
        registered_by="test-suite",
        registration_reason="Synthetic evidence authority regression fixture.",
    )


def test_pipeline_evidence_resolves_exact_run_artifact_and_layer(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )

    manifest = register_pipeline_evidence(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
        source_run_id="source-run",
        artifact_path="phases/03/support.gpkg",
        layer_name="support_polygon",
        evidence_role=EvidenceRole.GEOLOGY,
        origin=EvidenceOrigin.HUMAN_DIGITIZED,
        eligible_phases=("03",),
        eligible_modes=(EvidenceExecutionMode.SUPPORT_EVIDENCE,),
        target_layer_name="geology_units_50k_polygon",
        limitations=("Synthetic support evidence for contract tests.",),
        registered_by="test-suite",
        registration_reason="Exercise exact pipeline evidence registration.",
    )
    path = tmp_path / "evidence" / manifest.manifest_id / "evidence_manifest.json"
    selected = resolver.resolve_selected([manifest.manifest_id])

    assert path.parent.name == manifest.manifest_id
    assert len(selected) == 1
    assert selected[0].artifact == artifact.resolve()
    assert selected[0].record.evidence_role is EvidenceRole.GEOLOGY
    catalog_entry = json.loads(
        (tmp_path / "evidence" / "evidence_catalog.jsonl").read_text(encoding="utf-8")
    )
    assert selected[0].catalog_entry_id == catalog_entry["entry_id"]
    assert catalog_entry["registered_by"] == "test-suite"
    assert catalog_entry["registration_reason"]


def test_pipeline_evidence_keeps_run_manifest_v2_0_compatibility(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    data = json.loads(authority.read_text(encoding="utf-8"))
    data["manifest_format_version"] = "2.0.0"
    data.pop("evidence_manifests", None)
    data.pop("source_phases", None)
    authority.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )
    manifest = _manifest(_record(authority, artifact))

    _write_manifest(resolver, manifest)
    selected = resolver.resolve_selected([manifest.manifest_id])

    assert selected[0].record.source_run_id == "source-run"


def test_source_mutation_fails_even_when_manifest_identity_is_recomputed(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    record = _record(authority, artifact, artifact_sha256="f" * 64)
    recomputed = _manifest(record)
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )

    with pytest.raises(EvidenceManifestError, match="different seal|bytes changed"):
        _write_manifest(resolver, recomputed)


def test_post_registration_source_mutation_is_detected(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )
    _write_manifest(resolver, manifest)
    artifact.write_bytes(artifact.read_bytes() + b"changed")

    with pytest.raises(EvidenceManifestError, match="artifact bytes changed"):
        resolver.resolve_selected([manifest.manifest_id])


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("manifest_format_version", "9.9.9", "format is unsupported"),
        ("run_layout_version", "unsafe-layout", "layout is unsupported"),
        ("finished_at", "", "finished_at is missing"),
        ("dry_run", True, "dry runs cannot provide"),
        ("error", "interrupted", "failed or incomplete runs"),
    ],
)
def test_pipeline_evidence_rejects_malformed_source_run_contract(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    data = json.loads(authority.read_text(encoding="utf-8"))
    data[field] = value
    authority.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )

    with pytest.raises(EvidenceManifestError, match=message):
        _write_manifest(resolver, manifest)


def test_pipeline_evidence_rejects_duplicate_source_phase_records(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    data = json.loads(authority.read_text(encoding="utf-8"))
    data["phases"].append(dict(data["phases"][0]))
    authority.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )

    with pytest.raises(EvidenceManifestError, match="duplicated or unselected"):
        _write_manifest(resolver, manifest)


def test_manifest_byte_tampering_fails_before_source_resolution(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )
    path = _write_manifest(resolver, manifest)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["records"][0]["evidence_role"] = "structure"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceManifestError, match="invalid"):
        resolver.resolve_selected([manifest.manifest_id])


def test_unregistered_copied_manifest_never_becomes_authoritative(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    manifest = _manifest(_record(authority, artifact))
    package = tmp_path / "evidence" / manifest.manifest_id
    package.mkdir(parents=True)
    (package / "evidence_manifest.json").write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )

    with pytest.raises(EvidenceManifestError, match="authority catalog"):
        resolver.resolve_selected([manifest.manifest_id])


def test_catalog_tampering_is_detected(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )
    _write_manifest(resolver, manifest)
    catalog = tmp_path / "evidence" / "evidence_catalog.jsonl"
    value = json.loads(catalog.read_text(encoding="utf-8"))
    value["manifest_sha256"] = "f" * 64
    catalog.write_text(json.dumps(value) + "\n", encoding="utf-8")

    with pytest.raises(EvidenceManifestError, match="catalog is invalid"):
        resolver.resolve_selected([manifest.manifest_id])


def test_crsless_source_layer_fails_closed(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    artifact.unlink()
    gpd.GeoDataFrame(
        {"class": ["unknown"], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])]}
    ).to_file(artifact, layer="support_polygon", driver="GPKG")
    data = json.loads(authority.read_text(encoding="utf-8"))
    seal = RunOutputArtifact(
        path="phases/03/support.gpkg",
        sha256=sha256_file(artifact),
        size_bytes=artifact.stat().st_size,
    )
    data["phases"][0]["output_artifacts"] = [seal.model_dump(mode="json")]
    data["phases"][0]["sealed_files"] = [seal.model_dump(mode="json")]
    authority.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )

    with pytest.raises(EvidenceManifestError, match="lacks valid CRS"):
        _write_manifest(resolver, manifest)


def test_duplicate_physical_layer_claims_are_rejected(tmp_path: Path) -> None:
    _runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    first = _record(authority, artifact)
    second = _record(authority, artifact, evidence_id="EV-second-claim")

    with pytest.raises(ValidationError, match="one physical source layer"):
        EvidenceManifest.create(records=(first, second))


def test_duplicate_layer_across_registered_manifests_fails_selection(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    first = _manifest(_record(authority, artifact))
    second = _manifest(_record(authority, artifact, evidence_id="EV-second-claim"))
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )
    _write_manifest(resolver, first)
    _write_manifest(resolver, second)

    with pytest.raises(EvidenceManifestError, match="duplicate physical layer"):
        resolver.resolve_selected([first.manifest_id, second.manifest_id])


def test_duplicate_evidence_identity_across_manifests_fails_selection(tmp_path: Path) -> None:
    runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)
    first = _manifest(_record(authority, artifact))
    second = _manifest(
        _record(
            authority,
            artifact,
            limitations=("Different package metadata with the same forbidden evidence ID.",),
        )
    )
    resolver = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )
    _write_manifest(resolver, first)
    _write_manifest(resolver, second)

    with pytest.raises(EvidenceManifestError, match="duplicate evidence identity"):
        resolver.resolve_selected([first.manifest_id, second.manifest_id])


def test_phase04_rejects_roles_not_implemented_by_the_comparator(tmp_path: Path) -> None:
    _runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)

    with pytest.raises(ValidationError, match="only implemented manifest roles"):
        _record(
            authority,
            artifact,
            target_layer_name=None,
            evidence_role=EvidenceRole.GEOLOGY,
            eligible_phases=("04",),
            eligible_modes=(EvidenceExecutionMode.LEGACY_COMPARATOR,),
        )


def test_phase03_pipeline_evidence_requires_exact_target_layer(tmp_path: Path) -> None:
    _runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)

    with pytest.raises(ValidationError, match="does not own its exact Phase 03 target layer"):
        _record(authority, artifact, target_layer_name=None)


def test_phase03_evidence_role_must_own_target_layer(tmp_path: Path) -> None:
    _runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)

    with pytest.raises(ValidationError, match="does not own its exact Phase 03 target layer"):
        _record(
            authority,
            artifact,
            evidence_role=EvidenceRole.GEOLOGY,
            target_layer_name="prospectivity_target_zones_polygon",
        )


@pytest.mark.parametrize(
    ("role", "target"),
    [
        (EvidenceRole.GEOLOGY, "geology_units_50k_polygon"),
        (EvidenceRole.STRUCTURE, "faults_structures_line"),
        (EvidenceRole.OCCURRENCE, "mineral_occurrences_point"),
        (EvidenceRole.PROSPECT_TARGET, "prospectivity_target_zones_polygon"),
        (EvidenceRole.ACCESS, "source_material_route_line"),
    ],
)
def test_phase03_role_target_contract_accepts_canonical_ownership(
    tmp_path: Path,
    role: EvidenceRole,
    target: str,
) -> None:
    _runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)

    record = _record(authority, artifact, evidence_role=role, target_layer_name=target)

    assert record.evidence_role is role
    assert record.target_layer_name == target


def test_phase03_ai_handoff_can_never_be_selected_for_phase04() -> None:
    with pytest.raises(ValidationError, match="Phase 03 promotion evidence remains"):
        EvidenceRecord(
            evidence_id="EV-ai-handoff",
            source_kind=EvidenceSourceKind.PHASE03_PROMOTION,
            source_run_id="ai-run",
            source_authority_path="accepted.promotion-ledger.jsonl",
            source_authority_sha256="a" * 64,
            source_record_id="b" * 64,
            artifact_path="accepted.gpkg",
            artifact_sha256="c" * 64,
            artifact_size_bytes=1,
            layer_name="faults_structures_line",
            target_layer_name="faults_structures_line",
            evidence_role=EvidenceRole.STRUCTURE,
            origin=EvidenceOrigin.PHASE03_AI_HANDOFF,
            lifecycle_state=EvidenceLifecycleState.ACCEPTED_EVIDENCE,
            review_record_id="b" * 64,
            reviewers=("Qualified reviewer",),
            reviewed_at=datetime(2026, 7, 23, tzinfo=UTC),
            eligible_phases=("04",),
            eligible_modes=(EvidenceExecutionMode.LEGACY_COMPARATOR,),
        )


def test_phase03_promotion_role_and_target_must_match_its_output_layer() -> None:
    with pytest.raises(ValidationError, match="Phase 03 promotion evidence remains"):
        EvidenceRecord(
            evidence_id="EV-ai-wrong-role",
            source_kind=EvidenceSourceKind.PHASE03_PROMOTION,
            source_run_id="ai-run",
            source_authority_path="accepted.promotion-ledger.jsonl",
            source_authority_sha256="a" * 64,
            source_record_id="b" * 64,
            artifact_path="accepted.gpkg",
            artifact_sha256="c" * 64,
            artifact_size_bytes=1,
            layer_name="faults_structures_line",
            target_layer_name="faults_structures_line",
            evidence_role=EvidenceRole.GEOLOGY,
            origin=EvidenceOrigin.PHASE03_AI_HANDOFF,
            lifecycle_state=EvidenceLifecycleState.ACCEPTED_EVIDENCE,
            review_record_id="b" * 64,
            reviewers=("Qualified reviewer",),
            reviewed_at=datetime(2026, 7, 23, tzinfo=UTC),
            eligible_phases=("03",),
            eligible_modes=(EvidenceExecutionMode.SUPPORT_EVIDENCE,),
        )


def test_pipeline_source_cannot_self_claim_human_review(tmp_path: Path) -> None:
    _runs_root, authority, artifact = _sealed_pipeline_source(tmp_path)

    with pytest.raises(ValidationError, match="pipeline-run evidence is sealed support"):
        _record(
            authority,
            artifact,
            lifecycle_state=EvidenceLifecycleState.ACCEPTED_EVIDENCE,
            review_record_id="review-1",
            reviewers=("Reviewer",),
            reviewed_at=datetime(2026, 7, 23, tzinfo=UTC),
        )


def test_pipeline_records_selected_evidence_and_resume_revalidates_it(raw_archive) -> None:
    config, register, _raw = raw_archive
    runs_root, authority, artifact = _sealed_pipeline_source(config.runs_root.parent)
    assert runs_root == config.runs_root
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=config.runs_root,
        evidence_root=config.evidence_root,
        target_epsg=config.target_epsg,
    )
    _write_manifest(resolver, manifest)

    first = run_pipeline(
        config,
        register,
        only=["03"],
        dry_run=True,
        run_id="evidence-run",
        evidence_manifest_ids=[manifest.manifest_id],
    )
    assert [item.manifest_id for item in first.evidence_manifests] == [manifest.manifest_id]
    assert all(item.catalog_entry_id for item in first.evidence_manifests)
    assert "evidence_manifests_sha256" in first.execution_identity
    stored = json.loads(
        (config.runs_root / first.run_id / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert stored["evidence_manifests"] == [
        item.model_dump(mode="json") for item in first.evidence_manifests
    ]

    resumed = run_pipeline(
        config,
        register,
        only=["03"],
        dry_run=True,
        run_id=first.run_id,
        resume=True,
        evidence_manifest_ids=[manifest.manifest_id],
    )
    assert resumed.as_dict() == first.as_dict()


def test_resume_binds_exact_catalog_admission_event(raw_archive) -> None:
    config, register, _raw = raw_archive
    _runs_root, authority, artifact = _sealed_pipeline_source(config.runs_root.parent)
    manifest = _manifest(_record(authority, artifact))
    resolver = EvidenceAuthorityResolver(
        runs_root=config.runs_root,
        evidence_root=config.evidence_root,
        target_epsg=config.target_epsg,
    )
    _write_manifest(resolver, manifest)
    first = run_pipeline(
        config,
        register,
        only=["03"],
        dry_run=True,
        run_id="catalog-bound-run",
        evidence_manifest_ids=[manifest.manifest_id],
    )
    catalog = config.evidence_root / "evidence_catalog.jsonl"
    existing = EvidenceCatalogEntry.model_validate(json.loads(catalog.read_text(encoding="utf-8")))
    replacement = EvidenceCatalogEntry.create(
        previous_entry_sha256=None,
        manifest_id=existing.manifest_id,
        manifest_sha256=existing.manifest_sha256,
        registered_at=existing.registered_at + timedelta(microseconds=1),
        registered_by=existing.registered_by,
        registration_reason=existing.registration_reason,
        authorization_record_id=existing.authorization_record_id,
    )
    assert replacement.entry_id != existing.entry_id
    catalog.write_text(replacement.model_dump_json() + "\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="resume identity differs"):
        run_pipeline(
            config,
            register,
            only=["03"],
            dry_run=True,
            run_id=first.run_id,
            resume=True,
            evidence_manifest_ids=[manifest.manifest_id],
        )


def test_pipeline_rejects_evidence_irrelevant_to_selected_phase(raw_archive) -> None:
    config, register, _raw = raw_archive
    _runs_root, authority, artifact = _sealed_pipeline_source(config.runs_root.parent)
    manifest = _manifest(_record(authority, artifact))
    EvidenceAuthorityResolver(
        runs_root=config.runs_root,
        evidence_root=config.evidence_root,
        target_epsg=config.target_epsg,
    ).write(
        manifest,
        registered_by="test-suite",
        registration_reason="Synthetic irrelevant-evidence regression fixture.",
    )

    with pytest.raises(EvidenceManifestError, match="not eligible"):
        run_pipeline(
            config,
            register,
            only=["04"],
            dry_run=True,
            evidence_manifest_ids=[manifest.manifest_id],
        )


def test_phase03_promotion_registration_preserves_handoff_boundary(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    run_directory = runs_root / "ai-run"
    run_directory.mkdir(parents=True)
    output = run_directory / "accepted.gpkg"
    gpd.GeoDataFrame(  # ty: ignore[no-matching-overload]
        {
            "evidence_state": ["ACCEPTED_EVIDENCE"],
            "geometry": [Polygon([(0, 0), (5, 0), (5, 5), (0, 0)])],
        },
        crs="EPSG:32647",
    ).to_file(output, layer="geology_units_50k_polygon", driver="GPKG")
    gpd.GeoDataFrame(  # ty: ignore[no-matching-overload]
        {
            "evidence_state": ["ACCEPTED_EVIDENCE"],
            "geometry": [LineString([(0, 0), (5, 5)])],
        },
        crs="EPSG:32647",
    ).to_file(output, layer="faults_structures_line", driver="GPKG", mode="a")
    reviewed_at = datetime(2026, 7, 23, 2, tzinfo=UTC)
    feature = PromotedFeature(
        proposal_id="proposal-1",
        accepted_feature_id="accepted-1",
        output_layer="geology_units_50k_polygon",
        decision="accepted",
        reviewed_geometry_sha256="a" * 64,
        review_record_sha256="b" * 64,
        reviewer="Qualified geologist",
        reviewed_at=reviewed_at,
        review_note="Accepted as Phase 03 support evidence only.",
    )
    structure_reviewed_at = datetime(2026, 7, 23, 2, 30, tzinfo=UTC)
    structure_feature = PromotedFeature(
        proposal_id="proposal-2",
        accepted_feature_id="accepted-2",
        output_layer="faults_structures_line",
        decision="accepted",
        reviewed_geometry_sha256="1" * 64,
        review_record_sha256="2" * 64,
        reviewer="Second qualified geologist",
        reviewed_at=structure_reviewed_at,
        review_note="Accepted structure as Phase 03 support evidence only.",
    )
    audit = PromotionAuditEntry(
        audit_id="c" * 64,
        review_manifest_sha256="d" * 64,
        review_geopackage_sha256="e" * 64,
        review_package_id="f" * 64,
        run_id="ai-run",
        output_relative_path="accepted.gpkg",
        output_sha256=sha256_file(output),
        promoted_features=(feature, structure_feature),
        promoted_at=datetime(2026, 7, 23, 3, tzinfo=UTC),
    )
    ledger = run_directory / "accepted.promotion-ledger.jsonl"
    ledger.write_text(audit.model_dump_json() + "\n", encoding="utf-8")

    manifest = register_phase03_promotion_evidence(
        output=output,
        audit_ledger=ledger,
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    )
    selected = EvidenceAuthorityResolver(
        runs_root=runs_root,
        evidence_root=tmp_path / "evidence",
        target_epsg=32647,
    ).resolve_selected([manifest.manifest_id])

    assert len(selected) == 2
    records = {item.record.layer_name: item.record for item in selected}
    geology = records["geology_units_50k_polygon"]
    structure = records["faults_structures_line"]
    assert geology.origin is EvidenceOrigin.PHASE03_AI_HANDOFF
    assert geology.lifecycle_state is EvidenceLifecycleState.ACCEPTED_EVIDENCE
    assert geology.eligible_phases == ("03",)
    assert geology.authoritative_for_phase04 is False
    assert geology.reviewers == ("Qualified geologist",)
    assert geology.reviewed_at == reviewed_at
    assert structure.reviewers == ("Second qualified geologist",)
    assert structure.reviewed_at == structure_reviewed_at
