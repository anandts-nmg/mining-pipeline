"""AI_DRAFT GeoPackage creation for validated vertical-slice responses."""

from __future__ import annotations

import json
from pathlib import Path

import fiona
from pyproj import CRS
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

from buduunkhad.ai.contracts import RasterTileLocator, ReviewStatus
from buduunkhad.ai.fingerprint import sha256_file, sha256_value
from buduunkhad.geospatial_ai.geometry_validation import (
    GeometryValidationResult,
    validate_geometry,
)
from buduunkhad.geospatial_ai.ledger import AIJobLedger, LedgerStatus
from buduunkhad.geospatial_ai.manifests import RequestPackageManifest, ValidatedResponseRecord
from buduunkhad.geospatial_ai.path_safety import StorageRoots
from buduunkhad.geospatial_ai.pixel_world import (
    PixelWorldError,
    transform_pixel_geometry,
    transformed_source_extent,
)
from buduunkhad.geospatial_ai.requests import (
    load_request_package,
    validate_package_ledger,
    verify_package_source,
)
from buduunkhad.geospatial_ai.responses import (
    load_validated_response,
    validate_output_source_references,
)
from buduunkhad.geospatial_ai.schemas import (
    DraftLayerName,
    GeologicalFeatureProposalBatch,
    VerticalFeatureProposal,
)

LAYER_GEOMETRIES: dict[DraftLayerName, str] = {
    DraftLayerName.GEOLOGY_UNITS: "Polygon",
    DraftLayerName.FAULTS_STRUCTURES: "LineString",
    DraftLayerName.INTRUSIVE_CONTACTS: "LineString",
    DraftLayerName.DYKES_VEINS: "Unknown",
    DraftLayerName.MINERAL_OCCURRENCES: "Point",
    DraftLayerName.ALTERATION_ZONES: "Polygon",
    DraftLayerName.PROSPECT_PROPOSALS: "Polygon",
}


class DraftOutputError(ValueError):
    """A validated response cannot safely become a draft GIS artifact."""


def process_validated_response(
    package_directory: Path,
    validated_response_path: Path,
    *,
    roots: StorageRoots,
    expected_target_crs: str,
    repair: bool = False,
    license_boundary: BaseGeometry | None = None,
) -> Path:
    package_directory = roots.assert_run_artifact(package_directory)
    package = load_request_package(package_directory)
    verify_package_source(package, roots=roots)
    run_directory = roots.run_directory(package.request.run_id)
    expected_response = roots.assert_writable(
        run_directory / "validated-responses" / f"{package.request.job_id}.json",
        run_id=package.request.run_id,
    ).resolve(strict=True)
    if validated_response_path.resolve(strict=True) != expected_response:
        raise DraftOutputError("validated response is outside its authoritative run location")
    ledger = AIJobLedger(
        run_directory / "ai_jobs.sqlite", roots=roots, run_id=package.request.run_id
    )
    ledger_view = validate_package_ledger(package, ledger, package_directory)
    if ledger_view.status is not LedgerStatus.INGESTED:
        raise DraftOutputError("job must have an ingested response before processing")
    ingestion_event = ledger_view.events[-1]
    if ingestion_event.response_file != expected_response.relative_to(
        run_directory
    ).as_posix() or ingestion_event.response_sha256 != sha256_file(expected_response):
        raise DraftOutputError("validated response differs from the append-only job ledger")
    response = load_validated_response(validated_response_path)
    _validate_response_binding(package, response)
    if package.source.target_crs != expected_target_crs:
        raise DraftOutputError("request package target CRS differs from project configuration")
    try:
        output = GeologicalFeatureProposalBatch.model_validate(response.payload.to_python())
    except ValueError as exc:
        raise DraftOutputError("response is not a geological feature proposal batch") from exc
    validate_output_source_references(output, package.request.source_references)
    gpkg = roots.assert_writable(
        run_directory / "gis" / f"{package.request.job_id}_AI_DRAFT.gpkg",
        run_id=package.request.run_id,
    )
    gpkg.parent.mkdir(parents=True, exist_ok=True)
    if gpkg.exists():
        raise DraftOutputError("draft GeoPackage already exists")
    tiles = {tile.tile_id: tile for tile in package.tile_manifest.tiles}
    extent = transformed_source_extent(package.source)
    features: dict[
        DraftLayerName,
        list[
            tuple[
                VerticalFeatureProposal,
                BaseGeometry,
                BaseGeometry,
                GeometryValidationResult,
            ]
        ],
    ] = {layer: [] for layer in DraftLayerName}
    for proposal in output.proposals:
        try:
            tile = tiles[proposal.geometry_tile_id]
        except KeyError as exc:
            raise DraftOutputError("proposal geometry references an unknown tile") from exc
        _require_proposal_tile_reference(proposal, tile.tile_id)
        try:
            original_transformed = transform_pixel_geometry(
                proposal.geometry,
                tile=tile,
                source=package.source,
            )
        except PixelWorldError as exc:
            raise DraftOutputError(
                f"feature {proposal.feature_id} has invalid pixel geometry"
            ) from exc
        transformed, validation = validate_geometry(
            original_transformed,
            expected_geometry=LAYER_GEOMETRIES[proposal.layer],
            extent=extent,
            license_boundary=license_boundary,
            repair=repair,
        )
        if not validation.valid:
            raise DraftOutputError(f"feature {proposal.feature_id} failed geometry validation")
        features[proposal.layer].append((proposal, original_transformed, transformed, validation))
    _write_geopackage(gpkg, package=package, response=response, features=features)
    ledger.transition(
        package.request.job_id,
        LedgerStatus.PROCESSED,
        response_file=gpkg.relative_to(run_directory).as_posix(),
        response_sha256=sha256_file(gpkg),
    )
    return gpkg


def _write_geopackage(
    path: Path,
    *,
    package: RequestPackageManifest,
    response: ValidatedResponseRecord,
    features: dict[
        DraftLayerName,
        list[
            tuple[
                VerticalFeatureProposal,
                BaseGeometry,
                BaseGeometry,
                GeometryValidationResult,
            ]
        ],
    ],
) -> None:
    crs_wkt = CRS.from_user_input(package.source.target_crs).to_wkt()
    schema = {
        "geometry": "Unknown",
        "properties": {
            "feature_id": "str",
            "feature_ver": "int",
            "feature_type": "str",
            "legend_code": "str",
            "parent_ids": "str",
            "run_id": "str",
            "phase_id": "str",
            "job_id": "str",
            "source_id": "str",
            "source_sha": "str",
            "source_refs": "str",
            "tile_ids": "str",
            "prompt_id": "str",
            "prompt_ver": "str",
            "prompt_sha": "str",
            "schema_id": "str",
            "schema_ver": "str",
            "schema_sha": "str",
            "provider": "str",
            "model": "str",
            "response_id": "str",
            "pixel_json": "str",
            "original_wkb": "str",
            "output_wkb": "str",
            "attributes": "str",
            "confidence": "float",
            "conf_json": "str",
            "evidence": "str",
            "limitations": "str",
            "risk_level": "str",
            "geom_status": "str",
            "repair_status": "str",
            "repair_json": "str",
            "content_sha": "str",
            "review_status": "str",
        },
    }
    for layer in DraftLayerName:
        with fiona.open(
            path,
            mode="w",
            driver="GPKG",
            layer=layer.value,
            schema=schema,
            crs_wkt=crs_wkt,
        ) as collection:
            for proposal, original_geometry, geometry, validation in features[layer]:
                collection.write(
                    {
                        "geometry": mapping(geometry),
                        "properties": _properties(
                            proposal,
                            original_geometry,
                            geometry,
                            validation,
                            package=package,
                            response=response,
                        ),
                    }
                )
    finding_schema = {
        "geometry": "Point",
        "properties": {
            "feature_id": "str",
            "code": "str",
            "severity": "str",
            "message": "str",
        },
    }
    with fiona.open(
        path,
        mode="w",
        driver="GPKG",
        layer="validation_findings",
        schema=finding_schema,
        crs_wkt=crs_wkt,
    ) as collection:
        for layer_features in features.values():
            for proposal, _original_geometry, geometry, validation in layer_features:
                for finding in validation.findings:
                    collection.write(
                        {
                            "geometry": mapping(geometry.representative_point()),
                            "properties": {
                                "feature_id": proposal.feature_id,
                                "code": finding.code,
                                "severity": finding.severity,
                                "message": finding.message,
                            },
                        }
                    )


def _properties(
    proposal: VerticalFeatureProposal,
    original_geometry: BaseGeometry,
    geometry: BaseGeometry,
    validation: GeometryValidationResult,
    *,
    package: RequestPackageManifest,
    response: ValidatedResponseRecord,
) -> dict[str, object]:
    tile_ids = sorted(
        locator.tile_id
        for source in proposal.source_references
        for locator in source.locators
        if isinstance(locator, RasterTileLocator)
    )
    repair_json = validation.repair.model_dump_json() if validation.repair else ""
    content_sha = sha256_value(
        {
            "proposal": proposal,
            "original_geometry_wkb": original_geometry.wkb.hex(),
            "geometry_wkb": geometry.wkb.hex(),
            "validation": validation,
        }
    )
    return {
        "feature_id": proposal.feature_id,
        "feature_ver": 1,
        "feature_type": proposal.feature_type,
        "legend_code": proposal.legend_code or "",
        "parent_ids": "[]",
        "run_id": package.request.run_id,
        "phase_id": package.request.phase_id,
        "job_id": package.request.job_id,
        "source_id": package.source.asset_id,
        "source_sha": package.source.sha256,
        "source_refs": json.dumps(
            [item.model_dump(mode="json") for item in proposal.source_references],
            sort_keys=True,
            separators=(",", ":"),
        ),
        "tile_ids": json.dumps(tile_ids, separators=(",", ":")),
        "prompt_id": package.prompt.prompt_id,
        "prompt_ver": package.prompt.version,
        "prompt_sha": package.prompt.sha256,
        "schema_id": package.schema_identity.schema_id,
        "schema_ver": package.schema_identity.version,
        "schema_sha": package.schema_identity.sha256,
        "provider": response.provider,
        "model": response.model,
        "response_id": response.response_id,
        "pixel_json": proposal.geometry.model_dump_json(),
        "original_wkb": original_geometry.wkb.hex(),
        "output_wkb": geometry.wkb.hex(),
        "attributes": json.dumps(
            {item.name: item.value.to_python() for item in proposal.attributes},
            separators=(",", ":"),
        ),
        "confidence": proposal.confidence,
        "conf_json": json.dumps(
            [item.model_dump(mode="json") for item in proposal.confidence_components],
            sort_keys=True,
            separators=(",", ":"),
        ),
        "evidence": json.dumps(proposal.evidence_observations, separators=(",", ":")),
        "limitations": json.dumps(proposal.limitations, separators=(",", ":")),
        "risk_level": proposal.risk_level.value,
        "geom_status": validation.status,
        "repair_status": "repaired" if validation.repair else "not-repaired",
        "repair_json": repair_json,
        "content_sha": content_sha,
        "review_status": ReviewStatus.AI_DRAFT.value,
    }


def _require_proposal_tile_reference(proposal: VerticalFeatureProposal, tile_id: str) -> None:
    referenced = {
        locator.tile_id
        for source in proposal.source_references
        for locator in source.locators
        if isinstance(locator, RasterTileLocator)
    }
    if tile_id not in referenced:
        raise DraftOutputError("proposal geometry tile is absent from its source references")


def _validate_response_binding(
    package: RequestPackageManifest, response: ValidatedResponseRecord
) -> None:
    if (
        response.request_fingerprint != package.request_fingerprint
        or response.request_id != package.request.request_id
        or response.job_id != package.request.job_id
        or response.run_id != package.request.run_id
        or response.phase_id != package.request.phase_id
        or response.task_type != package.request.task_type
        or response.prompt != package.prompt
        or response.schema_identity != package.schema_identity
        or response.provider != package.request.provider.provider
        or response.model != package.request.provider.model
    ):
        raise DraftOutputError("validated response is unrelated to its request package")
