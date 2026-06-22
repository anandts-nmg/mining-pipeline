"""Phase 07 — Rock Chip / Channel / Verification Sampling (ORCHESTRATE).

Sample register + lab submission + assay import templates.
"""

from __future__ import annotations

from buduunkhad.phases.base import StubPhase


class Phase07RockChipSampling(StubPhase):
    id = "07"
    name = "Rock Chip, Channel and Verification Sampling"
    mode = "orchestrate"
    input_numbers = [55, 60, 63, 64, 66, 67, 68]
    software = "QField/QGIS, GPS/GNSS, lab submission templates"
    output_summary = "Rock chip/channel register, lab submission, assay import template"
    gate_condition = "Sample register + lab submission complete; assay import template ready."


PHASE = Phase07RockChipSampling
