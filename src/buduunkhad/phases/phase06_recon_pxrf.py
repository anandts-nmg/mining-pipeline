"""Phase 06 — Recon Mapping & Portable XRF Field Screening (ORCHESTRATE).

Field forms + pXRF register ingest/QA.
"""

from __future__ import annotations

from buduunkhad.phases.base import StubPhase


class Phase06ReconPXRF(StubPhase):
    id = "06"
    name = "Recon Mapping and Portable XRF Field Screening"
    mode = "orchestrate"
    input_numbers = [51, 52, 60, 63, 64]
    software = "QField/QGIS, Olympus Vanta M, Bruker Titan S1"
    output_summary = "Recon traverse, field observations, pXRF register and QA/QC report"
    gate_condition = "Field observations + pXRF register ingested and QA/QC passed."


PHASE = Phase06ReconPXRF
