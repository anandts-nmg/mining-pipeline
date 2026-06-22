"""Phase 04 — Preliminary Prospect Delineation & Ranking (BUILD, pending).

100-point evidence-overlay scoring matrix -> A/B/C/D prospect ranking.
"""

from __future__ import annotations

from buduunkhad.phases.base import StubPhase


class Phase04ProspectRanking(StubPhase):
    id = "04"
    name = "Preliminary Prospect Delineation and Ranking"
    mode = "build"
    input_numbers = [*range(1, 9), *range(47, 79)]
    software = "QGIS, Excel scoring matrix"
    output_summary = "Prospect polygons, 100-point ranking table, Go/No-Go desktop matrix"
    gate_condition = "Prospects scored and ranked A/B/C/D; desktop Go/No-Go recorded."


PHASE = Phase04ProspectRanking
