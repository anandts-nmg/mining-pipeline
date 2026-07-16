"""Synthetic, keyless Phase 03 AI-draft review and promotion tests."""

from __future__ import annotations

import copy
import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import fiona
import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.affinity import translate
from shapely.geometry import GeometryCollection, Polygon, mapping, shape
from typer.testing import CliRunner

from buduunkhad.ai.contracts import AIUsage, RasterTileLocator, TaskType
from buduunkhad.ai.fingerprint import sha256_file
from buduunkhad.cli import app
from buduunkhad.geospatial_ai.draft_gpkg import process_validated_response
from buduunkhad.geospatial_ai.manifests import (
    ResponseOrigin,
    SavedProviderResponse,
)
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.phase03_handoff import (
    Phase03EvidenceState,
    Phase03HandoffError,
    Phase03ReviewDecision,
    Phase03ReviewState,
    import_ai_draft_review_package,
    promote_reviewed_evidence,
)
from buduunkhad.geospatial_ai.requests import prepare_request_package
from buduunkhad.geospatial_ai.responses import ingest_saved_response
from buduunkhad.geospatial_ai.schemas import DraftLayerName
from buduunkhad.geospatial_ai.tiles import TileParameters

FIXTURE = Path("tests/fixtures/ai_vertical_slice_response.json")


@dataclass(frozen=True)
class HandoffCase:
    roots: StorageRoots
    run_id: str
    draft: Path
    review_directory: Path
    source: Path
    existing_evidence: Path


def _roots(tmp_path: Path) -> StorageRoots:
    paths = {
        name: tmp_path / name for name in ("raw", "workflow", "snapshot", "work", "eval", "publish")
    }
    for path in paths.values():
        path.mkdir(parents=True)
    return StorageRoots(
        raw_root=paths["raw"],
        workflow_docs_root=paths["workflow"],
        snapshot_root=paths["snapshot"],
        work_root=paths["work"],
        eval_root=paths["eval"],
        publish_root=paths["publish"],
    )


def _raster(path: Path, *, target_crs: str) -> Path:
    projected = target_crs == "EPSG:32647"
    transform = (
        from_origin(500_000, 5_200_000, 10, 10)
        if projected
        else from_origin(96.5, 45.6, 0.01, 0.01)
    )
    data = np.arange(3 * 12 * 12, dtype=np.uint8).reshape(3, 12, 12)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=12,
        height=12,
        count=3,
        dtype="uint8",
        crs=target_crs,
        transform=transform,
    ) as dataset:
        dataset.write(data)
    return path


def _existing_evidence(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = {"geometry": "Polygon", "properties": {"feature_id": "str"}}
    with fiona.open(
        path,
        "w",
        driver="GPKG",
        layer="geology_units_50k_polygon",
        schema=schema,
        crs="EPSG:32647",
    ) as collection:
        collection.write(
            {
                "geometry": mapping(
                    Polygon(
                        [
                            (499_900, 5_199_900),
                            (500_200, 5_199_900),
                            (500_200, 5_200_100),
                            (499_900, 5_200_100),
                            (499_900, 5_199_900),
                        ]
                    )
                ),
                "properties": {"feature_id": "EXISTING-1"},
            }
        )
    return path


def _build_case(
    tmp_path: Path,
    *,
    run_id: str = "phase03-handoff",
    target_crs: str = "EPSG:32647",
    mutate_payload=None,  # type: ignore[no-untyped-def]
    repair: bool = False,
) -> HandoffCase:
    roots = _roots(tmp_path)
    source = _raster(roots.require_snapshot_root() / "synthetic-map.tif", target_crs=target_crs)
    package_directory, package = prepare_request_package(
        source,
        roots=roots,
        run_id=run_id,
        task_type=TaskType.GEOLOGICAL_FEATURE_PROPOSAL,
        target_crs=target_crs,
        provider="openai",
        model="synthetic-model",
        tile_parameters=TileParameters(width=8, height=8, overlap=2),
        now=datetime(2026, 7, 16, 0, 0, tzinfo=UTC),
    )
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if mutate_payload is not None:
        mutate_payload(payload)
    first_tile = package.tile_manifest.tiles[0]
    source_reference = package.request.source_references[0]
    locator = next(
        item
        for item in source_reference.locators
        if isinstance(item, RasterTileLocator) and item.tile_id == first_tile.tile_id
    )
    reference = {
        "asset_id": source_reference.asset_id,
        "sha256": source_reference.sha256,
        "locators": [locator.model_dump(mode="json")],
    }
    for proposal in payload["proposals"]:
        proposal["geometry_tile_id"] = first_tile.tile_id
        proposal["source_references"] = [reference]
    response = SavedProviderResponse(
        origin=ResponseOrigin.EXTERNAL_SUPPLIED,
        provider="openai",
        model="synthetic-model",
        response_id="saved-response-phase03",
        request_id=package.request.request_id,
        job_id=package.request.job_id,
        run_id=run_id,
        phase_id="03",
        request_fingerprint=package.request_fingerprint,
        task_type=package.request.task_type,
        prompt=package.prompt,
        schema_identity=package.schema_identity,
        payload=payload,
        usage=AIUsage(input_tokens=10, output_tokens=20, requests=1),
        received_at=datetime(2026, 7, 16, 0, 1, tzinfo=UTC),
    )
    response_path = roots.run_directory(run_id) / "external" / "response.json"
    response_path.parent.mkdir()
    response_path.write_text(response.model_dump_json(indent=2), encoding="utf-8")
    validated_path, _validated = ingest_saved_response(
        package_directory,
        response_path,
        roots=roots,
        now=datetime(2026, 7, 16, 0, 2, tzinfo=UTC),
    )
    draft = process_validated_response(
        package_directory,
        validated_path,
        roots=roots,
        expected_target_crs=target_crs,
        repair=repair,
    )
    existing = _existing_evidence(tmp_path / "existing-evidence.gpkg")
    return HandoffCase(
        roots=roots,
        run_id=run_id,
        draft=draft,
        review_directory=roots.run_directory(run_id) / "phase03-review" / "review-1",
        source=source,
        existing_evidence=existing,
    )


@pytest.fixture
def handoff_case(tmp_path: Path) -> HandoffCase:
    return _build_case(tmp_path)


def _import(case: HandoffCase):  # type: ignore[no-untyped-def]
    return import_ai_draft_review_package(
        case.draft,
        case.review_directory,
        roots=case.roots,
        run_id=case.run_id,
        expected_target_crs="EPSG:32647",
        existing_evidence=case.existing_evidence,
        now=datetime(2026, 7, 16, 0, 3, tzinfo=UTC),
    )


def _review(
    case: HandoffCase,
    layer: DraftLayerName,
    proposal_id: str,
    decision: Phase03ReviewDecision,
    *,
    geometry=None,  # type: ignore[no-untyped-def]
    reviewer: str = "geologist@example.test",
    note: str = "Synthetic review decision.",
    reviewed_at: str = "2026-07-16T00:04:00+00:00",
) -> None:
    gpkg = case.review_directory / "phase03-ai-review.gpkg"
    layer_name = f"review_{layer.value}"
    gdf = gpd.read_file(gpkg, layer=layer_name)
    selected = gdf["proposal_id"] == proposal_id
    assert selected.sum() == 1
    index = gdf.index[selected][0]
    gdf.loc[index, "review_decision"] = decision.value
    gdf.loc[index, "review_state"] = (
        Phase03ReviewState.PENDING.value
        if decision is Phase03ReviewDecision.PENDING
        else Phase03ReviewState.HUMAN_REVIEWED.value
    )
    gdf.loc[index, "reviewer"] = reviewer
    gdf.loc[index, "reviewed_at"] = reviewed_at
    gdf.loc[index, "review_note"] = note
    if geometry is not None:
        gdf.loc[index, "geometry"] = geometry
    gdf.to_file(gpkg, layer=layer_name, driver="GPKG", mode="w")


def test_imports_valid_point_line_and_polygon_into_portable_review_package(
    handoff_case: HandoffCase,
) -> None:
    source_before = handoff_case.source.read_bytes()
    draft_before = handoff_case.draft.read_bytes()
    existing_before = handoff_case.existing_evidence.read_bytes()
    manifest = _import(handoff_case)
    assert manifest.response_origin.value == "saved_response"
    assert manifest.provider == "openai"
    assert manifest.model == "synthetic-model"
    assert manifest.target_crs == "EPSG:32647"
    assert {item.draft_layer for item in manifest.proposals} >= {
        DraftLayerName.MINERAL_OCCURRENCES,
        DraftLayerName.FAULTS_STRUCTURES,
        DraftLayerName.GEOLOGY_UNITS,
    }
    review = handoff_case.review_directory / "phase03-ai-review.gpkg"
    for layer in (
        DraftLayerName.MINERAL_OCCURRENCES,
        DraftLayerName.FAULTS_STRUCTURES,
        DraftLayerName.GEOLOGY_UNITS,
    ):
        with fiona.open(review, layer=f"original_{layer.value}") as original:
            assert len(original) == 1
            properties = dict(next(iter(original))["properties"])
            assert properties["proposal_state"] == "AI_DRAFT"
            assert properties["review_state"] == Phase03ReviewState.PENDING.value
            assert properties["evidence_state"] == Phase03EvidenceState.NOT_ACCEPTED.value
            assert properties["validation"] == "valid"
            assert properties["repair_status"] == "not-repaired"
            assert properties["request_fp"] == manifest.request_fingerprint
            assert properties["response_sha"] == manifest.validated_response_sha256
    assert handoff_case.source.read_bytes() == source_before
    assert handoff_case.draft.read_bytes() == draft_before
    assert handoff_case.existing_evidence.read_bytes() == existing_before
    assert _import(handoff_case) == manifest  # deterministic, non-destructive rerun


def test_review_qgis_project_has_relative_grouped_filtered_layers(
    handoff_case: HandoffCase,
) -> None:
    _import(handoff_case)
    qgz = handoff_case.review_directory / "phase03-ai-review.qgz"
    with zipfile.ZipFile(qgz) as archive:
        root = ET.fromstring(
            archive.read(next(name for name in archive.namelist() if name.endswith(".qgs")))
        )
    groups = [item.get("name") for item in root.iter("layer-tree-group") if item.get("name")]
    assert groups == [
        "01_Source",
        "02_Existing_Evidence",
        "03_AI_DRAFT",
        "04_Validation_Findings",
        "05_Human_Accepted",
        "06_Human_Rejected",
    ]
    datasources = [item.findtext("datasource") or "" for item in root.iter("maplayer")]
    assert all(not Path(value.split("|", maxsplit=1)[0]).is_absolute() for value in datasources)
    subsets = {item.findtext("subsetString") for item in root.iter("maplayer")}
    assert "\"review_decision\" = 'pending'" in subsets
    assert "\"review_decision\" = 'rejected'" in subsets
    assert "\"review_decision\" IN ('accepted','accepted_with_edits')" in subsets
    readonly_by_name = {
        item.findtext("layername"): item.findtext("readOnly") for item in root.iter("maplayer")
    }
    assert readonly_by_name["Original AI_DRAFT geology_units"] == "1"
    assert readonly_by_name["Validation Findings"] == "1"
    assert readonly_by_name["Pending Review geology_units"] == "0"
    project_xml = ET.tostring(root, encoding="unicode")
    assert str(handoff_case.roots.require_work_root()) not in project_xml
    assert str(handoff_case.source) not in project_xml


def test_rejects_invalid_provenance_and_draft_corruption(handoff_case: HandoffCase) -> None:
    handoff_case.draft.write_bytes(handoff_case.draft.read_bytes() + b"corrupted")
    with pytest.raises(Phase03HandoffError, match="ledger event"):
        _import(handoff_case)


def test_copied_or_renamed_draft_cannot_impersonate_the_ledger_output(
    handoff_case: HandoffCase,
) -> None:
    copied = handoff_case.draft.with_name("copied_AI_DRAFT.gpkg")
    shutil.copy2(handoff_case.draft, copied)
    with pytest.raises(Phase03HandoffError, match="authoritative processed job"):
        import_ai_draft_review_package(
            copied,
            handoff_case.review_directory,
            roots=handoff_case.roots,
            run_id=handoff_case.run_id,
            expected_target_crs="EPSG:32647",
        )


def test_rejects_unexpected_crs(tmp_path: Path) -> None:
    case = _build_case(tmp_path, target_crs="EPSG:4326")
    with pytest.raises(Phase03HandoffError, match="EPSG:32647"):
        import_ai_draft_review_package(
            case.draft,
            case.review_directory,
            roots=case.roots,
            run_id=case.run_id,
            expected_target_crs="EPSG:32647",
        )


def test_rejects_layer_geometry_that_vertical_unknown_contract_allowed(tmp_path: Path) -> None:
    def dyke_polygon(payload):  # type: ignore[no-untyped-def]
        polygon = payload["proposals"][2]
        polygon["layer"] = "dykes_veins"
        polygon["feature_type"] = "dyke-polygon"

    case = _build_case(tmp_path, mutate_payload=dyke_polygon)
    with pytest.raises(Phase03HandoffError, match="unsupported geometry type"):
        _import(case)


def test_preserves_deterministic_geometry_repair_record(tmp_path: Path) -> None:
    def bowtie(payload):  # type: ignore[no-untyped-def]
        payload["proposals"][2]["geometry"]["coordinates"] = [
            [[2.0, 2.0], [6.0, 6.0], [6.0, 2.0], [2.0, 6.0], [2.0, 2.0]]
        ]

    case = _build_case(tmp_path, mutate_payload=bowtie, repair=True)
    _import(case)
    with fiona.open(
        case.review_directory / "phase03-ai-review.gpkg",
        layer="original_geology_units",
    ) as collection:
        properties = dict(next(iter(collection))["properties"])
    assert properties["validation"] == "repaired"
    assert properties["repair_status"] == "repaired"
    repair = json.loads(properties["repair_json"])
    assert repair["algorithm"] == "shapely.make_valid"
    assert repair["original_geometry_sha256"] != repair["repaired_geometry_sha256"]


def test_promotion_requires_reviewer_metadata(handoff_case: HandoffCase) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
        reviewer="",
    )
    with pytest.raises(Phase03HandoffError, match="require reviewer"):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg",
            roots=handoff_case.roots,
        )


def test_non_pending_decision_requires_explicit_human_reviewed_state(
    handoff_case: HandoffCase,
) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    gpkg = handoff_case.review_directory / "phase03-ai-review.gpkg"
    layer = "review_mineral_occurrences"
    gdf = gpd.read_file(gpkg, layer=layer)
    gdf.loc[gdf["proposal_id"] == "synthetic-point-1", "review_state"] = "PENDING"
    gdf.to_file(gpkg, layer=layer, driver="GPKG", mode="w")

    with pytest.raises(Phase03HandoffError, match="review state is inconsistent"):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg",
            roots=handoff_case.roots,
        )


@pytest.mark.parametrize(
    ("reviewer", "note", "message"),
    [
        (" geologist@example.test ", "Synthetic review decision.", "surrounding whitespace"),
        ("geologist@example.test", "x" * 4097, "contract limit"),
    ],
)
def test_reviewer_metadata_is_normalized_and_bounded(
    handoff_case: HandoffCase,
    reviewer: str,
    note: str,
    message: str,
) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
        reviewer=reviewer,
        note=note,
    )
    with pytest.raises(Phase03HandoffError, match=message):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg",
            roots=handoff_case.roots,
        )


def test_unknown_review_decision_fails_closed(handoff_case: HandoffCase) -> None:
    _import(handoff_case)
    gpkg = handoff_case.review_directory / "phase03-ai-review.gpkg"
    layer = "review_mineral_occurrences"
    gdf = gpd.read_file(gpkg, layer=layer)
    selected = gdf["proposal_id"] == "synthetic-point-1"
    gdf.loc[selected, "review_decision"] = "approved"
    gdf.loc[selected, "review_state"] = Phase03ReviewState.HUMAN_REVIEWED.value
    gdf.to_file(gpkg, layer=layer, driver="GPKG", mode="w")
    with pytest.raises(Phase03HandoffError, match="decision is unsupported"):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg",
            roots=handoff_case.roots,
        )


def test_duplicate_review_proposal_identity_fails_closed(handoff_case: HandoffCase) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    gpkg = handoff_case.review_directory / "phase03-ai-review.gpkg"
    layer = "review_mineral_occurrences"
    gdf = gpd.read_file(gpkg, layer=layer)
    gdf.loc[len(gdf)] = gdf.iloc[0]
    gdf.set_crs("EPSG:32647", allow_override=True, inplace=True)
    gdf.to_file(gpkg, layer=layer, driver="GPKG", mode="w")
    with pytest.raises(Phase03HandoffError, match="identities are inconsistent"):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg",
            roots=handoff_case.roots,
        )


def test_modified_original_proposal_or_manifest_fails_authoritative_reconciliation(
    handoff_case: HandoffCase,
) -> None:
    manifest = _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    gpkg = handoff_case.review_directory / "phase03-ai-review.gpkg"
    layer = "original_mineral_occurrences"
    original = gpd.read_file(gpkg, layer=layer)
    original.loc[0, "pixel_json"] = '{"coordinates":[7,7],"type":"Point"}'
    original.to_file(gpkg, layer=layer, driver="GPKG", mode="w")
    output = handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg"
    with pytest.raises(Phase03HandoffError, match="modified|authoritative provenance"):
        promote_reviewed_evidence(handoff_case.review_directory, output, roots=handoff_case.roots)
    assert not output.exists()

    # Restore by recreating the package, then prove the manifest seal also fails closed.
    shutil.rmtree(handoff_case.review_directory)
    assert _import(handoff_case).package_id == manifest.package_id
    manifest_path = handoff_case.review_directory / "review-manifest.json"
    tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
    tampered["created_at"] = "2020-01-01T00:00:00Z"
    manifest_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(Phase03HandoffError, match="manifest is invalid"):
        promote_reviewed_evidence(handoff_case.review_directory, output, roots=handoff_case.roots)


def test_empty_or_unsupported_review_geometry_fails_closed(handoff_case: HandoffCase) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED_WITH_EDITS,
        geometry=GeometryCollection(),
    )
    with pytest.raises(Phase03HandoffError, match="geometry"):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg",
            roots=handoff_case.roots,
        )


@pytest.mark.parametrize(
    ("decision", "edit_geometry", "message"),
    [
        (Phase03ReviewDecision.ACCEPTED, True, "accepted_with_edits"),
        (Phase03ReviewDecision.ACCEPTED_WITH_EDITS, False, "requires an exact geometry change"),
    ],
)
def test_review_decision_must_match_exact_geometry_change(
    handoff_case: HandoffCase,
    decision: Phase03ReviewDecision,
    edit_geometry: bool,
    message: str,
) -> None:
    _import(handoff_case)
    review = handoff_case.review_directory / "phase03-ai-review.gpkg"
    with fiona.open(review, layer="original_geology_units") as collection:
        original = shape(next(iter(collection))["geometry"])
    geometry = translate(original, xoff=1.0) if edit_geometry else None
    _review(
        handoff_case,
        DraftLayerName.GEOLOGY_UNITS,
        "synthetic-polygon-1",
        decision,
        geometry=geometry,
    )
    with pytest.raises(Phase03HandoffError, match=message):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.run_directory(handoff_case.run_id) / "promoted.gpkg",
            roots=handoff_case.roots,
        )


def test_complete_review_promotion_is_stable_idempotent_and_append_only(
    handoff_case: HandoffCase,
) -> None:
    _import(handoff_case)
    source_before = handoff_case.source.read_bytes()
    draft_before = handoff_case.draft.read_bytes()
    review_gpkg = handoff_case.review_directory / "phase03-ai-review.gpkg"
    with fiona.open(review_gpkg, layer="original_geology_units") as collection:
        original_polygon = shape(next(iter(collection))["geometry"])
    edited_polygon = translate(original_polygon, xoff=1.0, yoff=-1.0)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    _review(
        handoff_case,
        DraftLayerName.FAULTS_STRUCTURES,
        "synthetic-line-1",
        Phase03ReviewDecision.REJECTED,
    )
    _review(
        handoff_case,
        DraftLayerName.GEOLOGY_UNITS,
        "synthetic-polygon-1",
        Phase03ReviewDecision.ACCEPTED_WITH_EDITS,
        geometry=edited_polygon,
    )
    output = handoff_case.roots.run_directory(handoff_case.run_id) / "promotions" / "accepted.gpkg"
    result = promote_reviewed_evidence(
        handoff_case.review_directory,
        output,
        roots=handoff_case.roots,
        now=datetime(2026, 7, 16, 0, 5, tzinfo=UTC),
    )
    assert result.created is True
    assert len(result.promoted_feature_ids) == 2
    assert all(value.startswith("BUD-") for value in result.promoted_feature_ids)
    with fiona.open(output, layer="mineral_occurrences_point") as collection:
        point = next(iter(collection))
        point_properties = dict(point["properties"])
        assert point_properties["proposal_state"] == "AI_DRAFT"
        assert point_properties["review_state"] == Phase03ReviewState.HUMAN_REVIEWED.value
        assert point_properties["evidence_state"] == Phase03EvidenceState.ACCEPTED_EVIDENCE.value
        assert point_properties["response_origin"] == "saved_response"
    with fiona.open(output, layer="faults_structures_line") as collection:
        assert len(collection) == 0  # rejected records never promote
    with fiona.open(output, layer="geology_units_50k_polygon") as collection:
        polygon = next(iter(collection))
        polygon_properties = dict(polygon["properties"])
        assert shape(polygon["geometry"]).equals_exact(edited_polygon, 0)
        assert polygon_properties["review_decision"] == "accepted_with_edits"
        assert polygon_properties["original_geometry_wkb"]
        assert polygon_properties["draft_output_wkb"] == original_polygon.wkb.hex()
        assert polygon_properties["reviewed_geometry_provenance"].startswith("human-edited")
    with fiona.open(review_gpkg, layer="original_geology_units") as collection:
        assert shape(next(iter(collection))["geometry"]).equals_exact(original_polygon, 0)
    with fiona.open(review_gpkg, layer="review_faults_structures") as collection:
        rejected = dict(next(iter(collection))["properties"])
        assert rejected["review_state"] == Phase03ReviewState.HUMAN_REVIEWED.value
        assert rejected["evidence_state"] == Phase03EvidenceState.NOT_ACCEPTED.value
    assert handoff_case.source.read_bytes() == source_before
    assert handoff_case.draft.read_bytes() == draft_before
    output_before = output.read_bytes()
    audit_before = result.audit_ledger.read_bytes()
    repeated = promote_reviewed_evidence(
        handoff_case.review_directory,
        output,
        roots=handoff_case.roots,
        now=datetime(2027, 1, 1, tzinfo=UTC),
    )
    assert repeated.created is False
    assert repeated.promoted_feature_ids == result.promoted_feature_ids
    assert output.read_bytes() == output_before
    assert result.audit_ledger.read_bytes() == audit_before
    assert len(result.audit_ledger.read_text(encoding="utf-8").splitlines()) == 1
    audit = json.loads(audit_before)
    assert audit["promotion_contract_version"] == "1.0.0"
    assert audit["review_manifest_sha256"]
    assert audit["review_geopackage_sha256"]
    assert {item["reviewer"] for item in audit["promoted_features"]} == {"geologist@example.test"}


def test_point_line_and_polygon_attributes_round_trip_to_accepted_evidence(
    handoff_case: HandoffCase,
) -> None:
    _import(handoff_case)
    decisions = (
        (DraftLayerName.MINERAL_OCCURRENCES, "synthetic-point-1"),
        (DraftLayerName.FAULTS_STRUCTURES, "synthetic-line-1"),
        (DraftLayerName.GEOLOGY_UNITS, "synthetic-polygon-1"),
    )
    for layer, proposal_id in decisions:
        _review(handoff_case, layer, proposal_id, Phase03ReviewDecision.ACCEPTED)
    output = handoff_case.roots.run_directory(handoff_case.run_id) / "attributes.gpkg"
    promote_reviewed_evidence(handoff_case.review_directory, output, roots=handoff_case.roots)

    expected = {
        "mineral_occurrences_point": ("mineral-occurrence", "MO", "synthetic point"),
        "faults_structures_line": ("fault", "F", "synthetic line"),
        "geology_units_50k_polygon": ("geology-unit", "GU", "synthetic polygon"),
    }
    for layer, (feature_type, legend_code, observation) in expected.items():
        with fiona.open(output, layer=layer) as collection:
            properties = dict(next(iter(collection))["properties"])
        assert properties["feature_type"] == feature_type
        assert properties["legend_code"] == legend_code
        assert json.loads(properties["attributes_json"])["observation"] == observation
        assert json.loads(properties["source_references_json"])
        assert json.loads(properties["source_tile_ids_json"])
        assert json.loads(properties["confidence_components_json"])
        assert json.loads(properties["evidence_json"])
        assert properties["request_fingerprint"]
        assert properties["schema_version"]
        assert properties["validation_status"] == "Human reviewed AI proposal"
        assert properties["draft_geometry_validation_status"] == "valid"
        assert properties["repair_status"] == "not-repaired"
        assert properties["risk_level"] == "MEDIUM"


def test_changed_review_cannot_duplicate_or_rewrite_existing_promotion(
    handoff_case: HandoffCase,
) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    output = handoff_case.roots.run_directory(handoff_case.run_id) / "accepted.gpkg"
    first = promote_reviewed_evidence(
        handoff_case.review_directory,
        output,
        roots=handoff_case.roots,
    )
    output_sha = sha256_file(output)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
        note="Changed after immutable promotion.",
    )
    with pytest.raises(Phase03HandoffError, match="differs"):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            output,
            roots=handoff_case.roots,
        )
    assert sha256_file(output) == output_sha
    assert len(first.audit_ledger.read_text(encoding="utf-8").splitlines()) == 1


def test_corrupted_existing_promotion_is_rejected(handoff_case: HandoffCase) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    output = handoff_case.roots.run_directory(handoff_case.run_id) / "accepted.gpkg"
    result = promote_reviewed_evidence(
        handoff_case.review_directory, output, roots=handoff_case.roots
    )
    audit_before = result.audit_ledger.read_bytes()
    output.write_bytes(output.read_bytes() + b"corrupted")
    with pytest.raises(Phase03HandoffError, match="differs"):
        promote_reviewed_evidence(handoff_case.review_directory, output, roots=handoff_case.roots)
    assert result.audit_ledger.read_bytes() == audit_before


@pytest.mark.parametrize("failed_target", ["output", "audit"])
def test_promotion_commit_failure_leaves_no_partial_success(
    handoff_case: HandoffCase,
    monkeypatch: pytest.MonkeyPatch,
    failed_target: str,
) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    output = handoff_case.roots.run_directory(handoff_case.run_id) / "atomic.gpkg"
    audit = output.with_suffix(".promotion-ledger.jsonl")
    original_replace = Path.replace

    def fail_selected(source: Path, target: Path):  # type: ignore[no-untyped-def]
        expected = output if failed_target == "output" else audit
        if Path(target) == expected:
            raise OSError(f"synthetic {failed_target} commit failure")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_selected)
    with pytest.raises(OSError, match="synthetic"):
        promote_reviewed_evidence(handoff_case.review_directory, output, roots=handoff_case.roots)
    assert not output.exists()
    assert not audit.exists()
    assert not output.with_suffix(".promotion.lock").exists()


def test_existing_promotion_lock_fails_safely(handoff_case: HandoffCase) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    output = handoff_case.roots.run_directory(handoff_case.run_id) / "locked.gpkg"
    lock = output.with_suffix(".promotion.lock")
    lock.write_text("another invocation", encoding="utf-8")
    with pytest.raises(Phase03HandoffError, match="another promotion"):
        promote_reviewed_evidence(handoff_case.review_directory, output, roots=handoff_case.roots)
    assert not output.exists()
    assert not output.with_suffix(".promotion-ledger.jsonl").exists()


def test_accepted_feature_ids_do_not_depend_on_review_layer_row_order(tmp_path: Path) -> None:
    def second_point(payload):  # type: ignore[no-untyped-def]
        duplicate = copy.deepcopy(payload["proposals"][0])
        duplicate["feature_id"] = "synthetic-point-2"
        duplicate["geometry"]["coordinates"] = [2.0, 1.0]
        payload["proposals"].append(duplicate)

    cases = (
        _build_case(tmp_path / "ordered", mutate_payload=second_point),
        _build_case(tmp_path / "reversed", mutate_payload=second_point),
    )
    mappings: list[dict[str, str]] = []
    for index, case in enumerate(cases):
        _import(case)
        for proposal_id in ("synthetic-point-1", "synthetic-point-2"):
            _review(
                case,
                DraftLayerName.MINERAL_OCCURRENCES,
                proposal_id,
                Phase03ReviewDecision.ACCEPTED,
            )
        if index:
            gpkg = case.review_directory / "phase03-ai-review.gpkg"
            layer = "review_mineral_occurrences"
            reversed_rows = gpd.read_file(gpkg, layer=layer).iloc[::-1].reset_index(drop=True)
            reversed_rows.to_file(gpkg, layer=layer, driver="GPKG", mode="w")
        output = case.roots.run_directory(case.run_id) / "stable-ids.gpkg"
        promote_reviewed_evidence(case.review_directory, output, roots=case.roots)
        with fiona.open(output, layer="mineral_occurrences_point") as collection:
            mappings.append(
                {
                    str(item["properties"]["proposal_id"]): str(item["properties"]["feature_id"])
                    for item in collection
                }
            )
    assert mappings[0] == mappings[1]


def test_distinct_proposal_provenance_mints_distinct_ids_for_identical_geometry(
    tmp_path: Path,
) -> None:
    def duplicate_point(payload):  # type: ignore[no-untyped-def]
        duplicate = copy.deepcopy(payload["proposals"][0])
        duplicate["feature_id"] = "synthetic-point-2"
        payload["proposals"].append(duplicate)

    case = _build_case(tmp_path, mutate_payload=duplicate_point)
    _import(case)
    for proposal_id in ("synthetic-point-1", "synthetic-point-2"):
        _review(
            case,
            DraftLayerName.MINERAL_OCCURRENCES,
            proposal_id,
            Phase03ReviewDecision.ACCEPTED,
        )
    output = case.roots.run_directory(case.run_id) / "distinct-provenance.gpkg"
    result = promote_reviewed_evidence(case.review_directory, output, roots=case.roots)
    assert len(result.promoted_feature_ids) == 2
    assert len(set(result.promoted_feature_ids)) == 2


def test_moved_review_package_remains_portable_and_keeps_feature_identity(
    handoff_case: HandoffCase,
) -> None:
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    moved = handoff_case.roots.run_directory(handoff_case.run_id) / "moved-review"
    shutil.copytree(handoff_case.review_directory, moved)
    first_output = handoff_case.roots.run_directory(handoff_case.run_id) / "first.gpkg"
    moved_output = handoff_case.roots.run_directory(handoff_case.run_id) / "moved.gpkg"
    first = promote_reviewed_evidence(
        handoff_case.review_directory, first_output, roots=handoff_case.roots
    )
    second = promote_reviewed_evidence(moved, moved_output, roots=handoff_case.roots)
    assert first.promoted_feature_ids == second.promoted_feature_ids

    with zipfile.ZipFile(moved / "phase03-ai-review.qgz") as archive:
        project = archive.read(next(name for name in archive.namelist() if name.endswith(".qgs")))
    assert str(handoff_case.review_directory).encode() not in project
    assert str(handoff_case.roots.require_work_root()).encode() not in project
    for relative, _digest in json.loads(
        (moved / "review-manifest.json").read_text(encoding="utf-8")
    )["source_preview_files"]:
        assert (moved / relative).is_file()


def test_review_and_promotion_outputs_cannot_escape_run_root(handoff_case: HandoffCase) -> None:
    with pytest.raises(ValueError, match="escapes"):
        import_ai_draft_review_package(
            handoff_case.draft,
            handoff_case.roots.require_work_root() / "outside-review",
            roots=handoff_case.roots,
            run_id=handoff_case.run_id,
            expected_target_crs="EPSG:32647",
        )
    _import(handoff_case)
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
    )
    with pytest.raises(ValueError, match="escapes"):
        promote_reviewed_evidence(
            handoff_case.review_directory,
            handoff_case.roots.require_work_root() / "outside.gpkg",
            roots=handoff_case.roots,
        )


def test_phase03_handoff_cli_runs_without_provider_key(
    handoff_case: HandoffCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = handoff_case.roots
    environment = {
        "BUDUUNKHAD_RAW_ROOT": roots.raw_root,
        "BUDUUNKHAD_WORKFLOW_DOCS_ROOT": roots.workflow_docs_root,
        "BUDUUNKHAD_SNAPSHOT_ROOT": roots.snapshot_root,
        "BUDUUNKHAD_WORK_ROOT": roots.work_root,
        "BUDUUNKHAD_EVAL_ROOT": roots.eval_root,
        "BUDUUNKHAD_PUBLISH_ROOT": roots.publish_root,
    }
    for name, value in environment.items():
        assert value is not None
        monkeypatch.setenv(name, str(value))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    runner = CliRunner()
    imported = runner.invoke(
        app,
        [
            "ai",
            "phase03",
            "import-ai-draft",
            "--run-id",
            handoff_case.run_id,
            "--draft",
            str(handoff_case.draft),
            "--review-package",
            str(handoff_case.review_directory),
        ],
    )
    assert imported.exit_code == 0, imported.stdout
    assert "Original AI_DRAFT" in imported.stdout
    _review(
        handoff_case,
        DraftLayerName.MINERAL_OCCURRENCES,
        "synthetic-point-1",
        Phase03ReviewDecision.ACCEPTED,
        reviewed_at=datetime.now(UTC).isoformat(),
    )
    output = roots.run_directory(handoff_case.run_id) / "cli-accepted.gpkg"
    promoted = runner.invoke(
        app,
        [
            "ai",
            "phase03",
            "promote-reviewed",
            "--review-package",
            str(handoff_case.review_directory),
            "--output",
            str(output),
        ],
    )
    assert promoted.exit_code == 0, promoted.stdout
    assert "Promoted features: 1" in promoted.stdout
    assert output.is_file()
