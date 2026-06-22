"""Decision-gate evaluation and go/no-go logging.

Invariant #6 (second half): each phase ends at a decision gate. A failing QA/QC
check blocks advance; the runner will not proceed past a blocked gate unless an
explicit ``--override`` is given, which is recorded on the decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from buduunkhad.core.qaqc import QAQCReport


class GateStatus(StrEnum):
    GO = "go"
    NO_GO = "no-go"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class GateDecision:
    """Outcome of a phase's decision gate."""

    phase_id: str
    status: GateStatus
    reason: str
    overridden: bool = False

    @property
    def can_advance(self) -> bool:
        """May the runner advance to the next phase?"""
        return self.status is GateStatus.GO or self.overridden

    def as_row(self) -> dict[str, object]:
        return {
            "phase_id": self.phase_id,
            "status": self.status.value,
            "reason": self.reason,
            "overridden": self.overridden,
        }


def evaluate_gate(
    qaqc: QAQCReport,
    *,
    condition: str = "",
    override: bool = False,
) -> GateDecision:
    """Derive a :class:`GateDecision` from a QA/QC report.

    - any failed item                 -> BLOCKED (or GO if ``override``)
    - items present, none failed       -> GO
    - no items recorded                -> BLOCKED (nothing was checked)
    """
    if qaqc.has_failures:
        failed = [i.item for i in qaqc.items if i.decision.value == "Fail"]
        reason = f"QA/QC failures: {', '.join(failed)}"
        if override:
            return GateDecision(
                qaqc.phase_id, GateStatus.GO, f"OVERRIDDEN - {reason}", overridden=True
            )
        return GateDecision(qaqc.phase_id, GateStatus.BLOCKED, reason)

    if not qaqc.items:
        reason = "No QA/QC items recorded; nothing verified."
        if override:
            return GateDecision(
                qaqc.phase_id, GateStatus.GO, f"OVERRIDDEN - {reason}", overridden=True
            )
        return GateDecision(qaqc.phase_id, GateStatus.BLOCKED, reason)

    reason = condition or "All QA/QC checks passed."
    return GateDecision(qaqc.phase_id, GateStatus.GO, reason)
