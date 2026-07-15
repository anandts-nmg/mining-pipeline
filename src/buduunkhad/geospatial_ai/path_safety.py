"""Central protected-root and writable-target policy for AI workflows."""

from __future__ import annotations

import os
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

WORKFLOW_DOCS_ROOT_ENV = "BUDUUNKHAD_WORKFLOW_DOCS_ROOT"
SNAPSHOT_ROOT_ENV = "BUDUUNKHAD_SNAPSHOT_ROOT"
WORK_ROOT_ENV = "BUDUUNKHAD_WORK_ROOT"
EVAL_ROOT_ENV = "BUDUUNKHAD_EVAL_ROOT"
PUBLISH_ROOT_ENV = "BUDUUNKHAD_PUBLISH_ROOT"

_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class PathSafetyError(ValueError):
    """A source or output path violates the configured storage policy."""


class StorageRoots(BaseModel):
    """Resolved storage roots with immutable/read-only and writable roles."""

    model_config = ConfigDict(frozen=True)

    raw_root: Path
    workflow_docs_root: Path | None = None
    snapshot_root: Path | None = None
    work_root: Path | None = None
    eval_root: Path | None = None
    publish_root: Path | None = None

    @field_validator(
        "raw_root", "workflow_docs_root", "snapshot_root", "work_root", "eval_root", "publish_root"
    )
    @classmethod
    def _absolute_resolved_root(cls, value: Path | None) -> Path | None:
        if value is None:
            return None
        return value.expanduser().resolve(strict=False)

    @model_validator(mode="after")
    def _non_overlapping_roles(self) -> StorageRoots:
        protected = self.protected_roots
        writable = tuple(root for root in (self.work_root, self.publish_root) if root is not None)
        for protected_root in protected:
            for writable_root in writable:
                if _contains(protected_root, writable_root) or _contains(
                    writable_root, protected_root
                ):
                    raise PathSafetyError(
                        f"protected and writable roots overlap: {protected_root} / {writable_root}"
                    )
        return self

    @classmethod
    def from_environment(cls, *, raw_root: Path) -> StorageRoots:
        return cls(
            raw_root=raw_root,
            workflow_docs_root=_environment_path(WORKFLOW_DOCS_ROOT_ENV),
            snapshot_root=_environment_path(SNAPSHOT_ROOT_ENV),
            work_root=_environment_path(WORK_ROOT_ENV),
            eval_root=_environment_path(EVAL_ROOT_ENV),
            publish_root=_environment_path(PUBLISH_ROOT_ENV),
        )

    @property
    def protected_roots(self) -> tuple[Path, ...]:
        return tuple(
            root
            for root in (
                self.raw_root,
                self.workflow_docs_root,
                self.snapshot_root,
                self.eval_root,
            )
            if root is not None
        )

    def require_snapshot_root(self) -> Path:
        if self.snapshot_root is None:
            raise PathSafetyError(f"{SNAPSHOT_ROOT_ENV} is required for this operation")
        return self.snapshot_root

    def require_work_root(self) -> Path:
        if self.work_root is None:
            raise PathSafetyError(f"{WORK_ROOT_ENV} is required for this operation")
        return self.work_root

    def require_eval_root(self) -> Path:
        if self.eval_root is None:
            raise PathSafetyError(f"{EVAL_ROOT_ENV} is required for evaluation")
        return self.eval_root

    def require_publish_root(self) -> Path:
        if self.publish_root is None:
            raise PathSafetyError(f"{PUBLISH_ROOT_ENV} is required for publication output")
        return self.publish_root

    def run_directory(self, run_id: str, *, create: bool = False) -> Path:
        if not _RUN_ID.fullmatch(run_id):
            raise PathSafetyError("run_id contains path traversal or unsupported characters")
        run_dir = self.require_work_root() / "runs" / run_id
        safe = self.assert_writable(run_dir, run_id=run_id)
        if create:
            safe.mkdir(parents=True, exist_ok=True)
            safe = self.assert_writable(safe, run_id=run_id)
        return safe

    def assert_run_artifact(self, path: Path, *, run_id: str | None = None) -> Path:
        """Resolve an existing run artifact without following an escape from the work root."""

        candidate = path.expanduser().resolve(strict=True)
        runs_root = (self.require_work_root() / "runs").resolve(strict=False)
        if not _contains(runs_root, candidate):
            raise PathSafetyError("run artifact is outside the configured work root")
        relative = candidate.relative_to(runs_root)
        if not relative.parts or not _RUN_ID.fullmatch(relative.parts[0]):
            raise PathSafetyError("run artifact has no valid run directory identity")
        if run_id is not None and relative.parts[0] != run_id:
            raise PathSafetyError("run artifact belongs to a different run")
        return candidate

    def assert_snapshot_source(self, path: Path) -> Path:
        source = path.expanduser().resolve(strict=True)
        snapshot = self.require_snapshot_root()
        if not _contains(snapshot, source):
            raise PathSafetyError("AI source must be inside the immutable snapshot root")
        if not source.is_file():
            raise PathSafetyError("AI source must be a regular file")
        return source

    def assert_evaluation_source(self, path: Path) -> Path:
        source = path.expanduser().resolve(strict=True)
        if not _contains(self.require_eval_root(), source) or not source.is_file():
            raise PathSafetyError("evaluation source must be a file under the evaluation root")
        return source

    def assert_writable(
        self,
        path: Path,
        *,
        run_id: str | None = None,
        publication: bool = False,
    ) -> Path:
        candidate = path.expanduser().resolve(strict=False)
        for protected in self.protected_roots:
            if _contains(protected, candidate):
                raise PathSafetyError(f"writes are forbidden under protected root: {protected}")
        if publication:
            allowed = self.require_publish_root()
        else:
            if run_id is None or not _RUN_ID.fullmatch(run_id):
                raise PathSafetyError("run-specific writes require a valid run_id")
            allowed = self.require_work_root() / "runs" / run_id
        allowed = allowed.resolve(strict=False)
        if not _contains(allowed, candidate):
            raise PathSafetyError(f"output escapes its allowed writable root: {candidate}")
        return candidate


def _environment_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def _contains(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True
