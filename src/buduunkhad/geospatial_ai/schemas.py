"""Schema-bound outputs for the first AI-to-QGIS vision slice."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from buduunkhad.ai.contracts import (
    ConfidenceComponent,
    CritiqueVerdict,
    FrozenModel,
    NamedJSONValue,
    PixelGeometry,
    ReviewStatus,
    RiskLevel,
    SourceReference,
    _freeze_named_values,
)


class DraftLayerName(StrEnum):
    GEOLOGY_UNITS = "geology_units"
    FAULTS_STRUCTURES = "faults_structures"
    INTRUSIVE_CONTACTS = "intrusive_contacts"
    DYKES_VEINS = "dykes_veins"
    MINERAL_OCCURRENCES = "mineral_occurrences"
    ALTERATION_ZONES = "alteration_zones"
    PROSPECT_PROPOSALS = "prospect_proposals"


class LegendItem(FrozenModel):
    legend_code: str
    label: str
    description: str | None = None
    color: str | None = None
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    confidence_components: tuple[ConfidenceComponent, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = Field(min_length=1)


class LegendExtraction(FrozenModel):
    items: tuple[LegendItem, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = ()


class InterpretedMapFeature(FrozenModel):
    observation_id: str
    feature_type: str
    geometry: PixelGeometry
    geometry_tile_id: str
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    confidence_components: tuple[ConfidenceComponent, ...] = Field(min_length=1)
    evidence_observations: tuple[str, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = Field(min_length=1)
    risk_level: RiskLevel


class MapFeatureInterpretation(FrozenModel):
    features: tuple[InterpretedMapFeature, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = ()


class VerticalFeatureProposal(FrozenModel):
    """One provider proposal expressed only in source-tile pixel coordinates."""

    feature_id: str
    layer: DraftLayerName
    feature_type: str
    legend_code: str | None = None
    geometry: PixelGeometry
    geometry_tile_id: str
    attributes: tuple[NamedJSONValue, ...] = ()
    confidence: float = Field(ge=0, le=1)
    confidence_components: tuple[ConfidenceComponent, ...] = Field(min_length=1)
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    evidence_observations: tuple[str, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = Field(min_length=1)
    risk_level: RiskLevel
    review_status: Literal[ReviewStatus.AI_DRAFT] = ReviewStatus.AI_DRAFT

    @field_validator("attributes", mode="before")
    @classmethod
    def _canonical_attributes(cls, value: object) -> tuple[NamedJSONValue, ...]:
        return _freeze_named_values(value)


class GeologicalFeatureProposalBatch(FrozenModel):
    proposals: tuple[VerticalFeatureProposal, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _unique_feature_ids(self) -> GeologicalFeatureProposalBatch:
        identities = tuple(item.feature_id for item in self.proposals)
        if len(set(identities)) != len(identities):
            raise ValueError("geological proposals contain duplicate feature IDs")
        return self


class FeatureCritiqueItem(FrozenModel):
    feature_id: str
    verdict: CritiqueVerdict
    findings: tuple[str, ...] = Field(min_length=1)
    confidence_components: tuple[ConfidenceComponent, ...] = ()
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = ()


class FeatureCritiqueBatch(FrozenModel):
    critiques: tuple[FeatureCritiqueItem, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _unique_feature_ids(self) -> FeatureCritiqueBatch:
        identities = tuple(item.feature_id for item in self.critiques)
        if len(set(identities)) != len(identities):
            raise ValueError("feature critiques contain duplicate feature IDs")
        return self
