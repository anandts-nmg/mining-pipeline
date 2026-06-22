"""Phase 11 — Follow-up Trench / Geophysics / Scout Drill Planning (ORCHESTRATE).

Planning templates + collar table.
"""

from __future__ import annotations

from buduunkhad.phases.base import StubPhase


class Phase11Followup(StubPhase):
    id = "11"
    name = "Follow-up Trench / Geophysics / Scout Drill Planning"
    mode = "orchestrate"
    input_numbers = [*range(9, 23), *range(53, 69), *range(73, 79)]
    software = "QGIS, trench/geophysics/drilling planning templates"
    output_summary = (
        "Follow-up work plan, trench/geophysics lines, scout drilling proposal, collar table"
    )
    gate_condition = "Follow-up plan + collar table prepared; Go/No-Go recorded."


PHASE = Phase11Followup
