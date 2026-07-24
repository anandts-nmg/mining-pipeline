"""Decision-gate evaluation and go/no-go logging.

Invariant #6 (second half): each phase ends at a decision gate. A failing QA/QC
check blocks advance. The runtime runner supplies ``override=False`` and handles only exact,
policy-permitted operational-exception records; the Boolean remains for direct legacy callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from buduunkhad.core.qaqc import Decision, QAQCReport


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
    #: GO reached with QA/QC items still PENDING human completion (orchestrate phases): the
    #: automated scaffold/ingest is done but the phase is not yet methodologically complete.
    provisional: bool = False

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
            "provisional": self.provisional,
        }


def evaluate_gate(
    qaqc: QAQCReport,
    *,
    condition: str = "",
    override: bool = False,
    pending_blocks: bool = False,
    pending_override_allowed: bool = True,
) -> GateDecision:
    """Derive a :class:`GateDecision` from a QA/QC report.

    - any failed item                 -> BLOCKED (or GO if ``override``)
    - items present, none failed       -> GO (``provisional`` if any item is PENDING), unless
                                          ``pending_blocks`` requires completed human evidence
    - no items recorded                -> BLOCKED (nothing was checked)

    ``pending_override_allowed`` applies only to pending-item blocks. Runtime code never maps the
    retired generic CLI flag to this Boolean; scientific handoff remains non-overridable.
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

    pending = [i.item for i in qaqc.items if i.decision is Decision.PENDING]
    if pending:
        base = condition or "All automated QA/QC checks passed"
        reason = f"{base}; {len(pending)} item(s) PENDING human completion."
        if pending_blocks:
            if override and pending_override_allowed:
                return GateDecision(
                    qaqc.phase_id,
                    GateStatus.GO,
                    f"OVERRIDDEN - {reason}",
                    overridden=True,
                )
            return GateDecision(qaqc.phase_id, GateStatus.BLOCKED, reason)
        return GateDecision(qaqc.phase_id, GateStatus.GO, reason, provisional=True)

    reason = condition or "All QA/QC checks passed."
    return GateDecision(qaqc.phase_id, GateStatus.GO, reason)
