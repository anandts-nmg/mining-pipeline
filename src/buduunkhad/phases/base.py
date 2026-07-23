"""The uniform Phase interface and the per-run context passed to every phase."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from buduunkhad.config import InputRecord, ProjectConfig
from buduunkhad.core import naming, paths
from buduunkhad.core.gates import GateDecision, evaluate_gate
from buduunkhad.core.qaqc import QAQCReport

Mode = Literal["build", "orchestrate"]


@dataclass
class RunContext:
    """Everything a phase needs at run time. Built once per pipeline run."""

    config: ProjectConfig
    register: list[InputRecord]
    run_id: str
    dry_run: bool = False
    override: bool = False
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("buduunkhad"))
    run_isolated: bool = False
    active_phase_id: str | None = None

    # ---- derived paths ---------------------------------------------------- #

    @property
    def raw_root(self) -> Path:
        return self.config.raw_root

    @property
    def output_root(self) -> Path:
        return self.config.output_root

    @property
    def run_dir(self) -> Path:
        return self.config.runs_root / self.run_id

    def phase_dir(self, phase_id: str) -> Path:
        if self.run_isolated:
            if phase_id == self.active_phase_id:
                return self.run_dir / "staging" / phase_id
            sealed = self.run_dir / "phases" / phase_id
            if sealed.is_dir():
                return sealed
            # A run may deliberately start at a later phase. Its prior-phase inputs come from
            # the explicitly promoted compatibility view, while every new write remains local.
            return paths.phase_dir(self.output_root, phase_id)
        return paths.phase_dir(self.output_root, phase_id)

    def stable_output_path(self, path: Path) -> Path:
        """Translate an active staging path to its immutable finalized run location."""

        candidate = Path(path)
        if not self.run_isolated or self.active_phase_id is None:
            return candidate
        stage = self.run_dir / "staging" / self.active_phase_id
        try:
            relative = candidate.resolve().relative_to(stage.resolve())
        except ValueError:
            return candidate
        return self.run_dir / "phases" / self.active_phase_id / relative

    # ---- register helpers ------------------------------------------------- #

    def records_for_phase(self, phase_id: str) -> list[InputRecord]:
        return [r for r in self.register if r.primary_phase == phase_id]

    def record_by_no(self, no: int) -> InputRecord:
        for r in self.register:
            if r.no == no:
                return r
        raise KeyError(f"No input #{no} in register")

    def records_by_numbers(self, numbers: list[int]) -> list[InputRecord]:
        wanted = set(numbers)
        return [r for r in self.register if r.no in wanted]

    # ---- naming helpers --------------------------------------------------- #

    def data_name(
        self,
        description: str,
        *,
        crs_or_param: str | None = None,
        version: int = 1,
        ext: str,
        draft: bool = False,
    ) -> str:
        return naming.data_name(
            self.config.data_prefix,
            description,
            crs_or_param=crs_or_param,
            version=version,
            ext=ext,
            draft=draft,
        )

    def register_name(
        self, description: str, *, ext: str, version: int | None = None, draft: bool = False
    ) -> str:
        return naming.register_name(
            self.config.register_prefix, description, ext=ext, version=version, draft=draft
        )


@dataclass
class PhaseResult:
    """What a phase's ``run`` returns."""

    phase_id: str
    status: str = "ok"  # ok | dry-run | stub
    outputs: list[Path] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def add_output(self, path: Path) -> None:
        self.outputs.append(Path(path))

    def log(self, message: str) -> None:
        self.messages.append(message)


class Phase(ABC):
    """Base class for every workflow phase.

    Subclasses set the class attributes and implement :meth:`run` and
    :meth:`qaqc`. ``prepare`` (folder creation) and ``gate`` have sensible
    defaults but may be overridden.
    """

    id: str = ""
    name: str = ""
    mode: Mode = "build"
    input_numbers: list[int] = []
    #: Methodology decision-gate / next-phase condition text.
    gate_condition: str = ""
    #: Override the standard subfolder set if the methodology specifies a custom tree.
    custom_subfolders: list[str] | None = None

    # ---- lifecycle -------------------------------------------------------- #

    @property
    def subfolders(self) -> list[str]:
        return (
            self.custom_subfolders
            if self.custom_subfolders is not None
            else paths.subfolders_for(self.id)
        )

    def prepare(self, ctx: RunContext) -> None:
        """Create the phase's folder tree. Safe to call repeatedly."""
        phase_root = ctx.phase_dir(self.id)
        phase_root.mkdir(parents=True, exist_ok=True)
        for subfolder in self.subfolders:
            (phase_root / subfolder).mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def run(self, ctx: RunContext) -> PhaseResult:
        """Do the phase's work (or emit templates/empties in dry-run)."""
        raise NotImplementedError

    @abstractmethod
    def qaqc(self, ctx: RunContext) -> QAQCReport:
        """Run/record acceptance checks and return the QA/QC report."""
        raise NotImplementedError

    def gate(self, qaqc: QAQCReport, ctx: RunContext) -> GateDecision:
        """Evaluate the decision gate from the QA/QC report."""
        return evaluate_gate(qaqc, condition=self.gate_condition, override=ctx.override)

    # ---- helpers for subclasses ------------------------------------------ #

    def records(self, ctx: RunContext) -> list[InputRecord]:
        """Inputs assigned to this phase (by ``input_numbers``, else primary_phase)."""
        if self.input_numbers:
            return ctx.records_by_numbers(self.input_numbers)
        return ctx.records_for_phase(self.id)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Phase {self.id} {self.name!r} mode={self.mode}>"


class StubPhase(Phase):
    """A not-yet-built phase.

    Participates in ``--dry-run`` (creates its folders and a method/status note)
    but raises a clear ``NotImplementedError`` on a real run. Subclasses set the
    class attributes; they need not implement :meth:`run` / :meth:`qaqc`.
    """

    #: Main software/equipment referenced by the methodology for this phase.
    software: str = ""
    #: One-line summary of the phase's main output package.
    output_summary: str = ""

    def run(self, ctx: RunContext) -> PhaseResult:
        if not ctx.dry_run:
            raise NotImplementedError(f"Phase {self.id} — build pending ({self.mode})")
        result = PhaseResult(self.id, status="dry-run")
        note = self._write_method_note(ctx)
        result.add_output(note)
        result.log(f"stub ({self.mode}): folders + method note created (dry-run)")
        return result

    def qaqc(self, ctx: RunContext) -> QAQCReport:
        from buduunkhad.core.qaqc import Decision, new_report

        report = new_report(self.id, self.name)
        report.add(
            "Phase scaffolding created",
            "Folders and method/status note present (dry-run).",
            decision=Decision.PASS if ctx.dry_run else Decision.PENDING,
            note=f"Phase {self.id} is a {self.mode} stub — implementation pending.",
        )
        return report

    def _write_method_note(self, ctx: RunContext) -> Path:
        admin = self.subfolders[0] if self.subfolders else "00_Admin_and_Method"
        target = ctx.phase_dir(self.id) / admin
        target.mkdir(parents=True, exist_ok=True)
        path = (
            target
            / f"{ctx.config.project.project_code}_{ctx.config.project.name}_Phase{self.id}_Method_and_Status.md"
        )
        nums = ", ".join(map(str, self.input_numbers)) if self.input_numbers else "(derived/none)"
        path.write_text(
            "\n".join(
                [
                    f"# Phase {self.id} — {self.name}",
                    "",
                    f"- **Mode:** {self.mode}",
                    "- **Status:** build pending (stub)",
                    f"- **Raw input numbers:** {nums}",
                    f"- **Main software / equipment:** {self.software or 'TBD'}",
                    f"- **Main output package:** {self.output_summary or 'TBD'}",
                    f"- **Decision gate / next-phase condition:** {self.gate_condition or 'TBD'}",
                    "",
                    "This phase is registered but not yet implemented. Running it outside "
                    "`--dry-run` raises `NotImplementedError`.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path
