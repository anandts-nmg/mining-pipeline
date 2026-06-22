"""Phase 08 — Orientation Soil / Stream Sediment / Heavy Mineral Check (ORCHESTRATE).

Orientation survey design + ingest.
"""

from __future__ import annotations

from buduunkhad.phases.base import StubPhase


class Phase08OrientationGeochem(StubPhase):
    id = "08"
    name = "Orientation Soil / Stream Sediment and Heavy Mineral Check"
    mode = "orchestrate"
    input_numbers = [*range(47, 53), 55, 60, 63, 64]
    software = "QGIS, DEM drainage tools, pXRF, lab workflow"
    output_summary = "Orientation soil plan, stream/heavy-mineral follow-up plan"
    gate_condition = "Orientation survey designed; results ingested and QA/QC passed."


PHASE = Phase08OrientationGeochem
