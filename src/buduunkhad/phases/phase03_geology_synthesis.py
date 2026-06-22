"""Phase 03 / 03A — Geological, Metallogenic & CMCS Synthesis + Deposit Model (ORCHESTRATE).

Manual digitizing/interpretation. The pipeline scaffolds evidence layers, evidence
registers and the preliminary deposit-model template; interpretation is done in QGIS.
"""

from __future__ import annotations

from buduunkhad.phases.base import StubPhase


class Phase03GeologySynthesis(StubPhase):
    id = "03"
    name = "Geological, Metallogenic and CMCS Synthesis (incl. 03A Deposit Model)"
    mode = "orchestrate"
    input_numbers = [*range(1, 8), *range(53, 73)]
    software = "QGIS, QGIS Georeferencer, Excel/Word evidence registers"
    output_summary = (
        "Geological evidence layers, metallogenic context, occurrence database, "
        "Preliminary Deposit Model.docx"
    )
    gate_condition = "Evidence layers digitized + registered; deposit model drafted; QA/QC passed."


PHASE = Phase03GeologySynthesis
