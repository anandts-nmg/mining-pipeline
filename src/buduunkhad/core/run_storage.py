"""Run-isolated staging, sealing, locking, and compatibility promotion."""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from collections.abc import Iterable
from contextlib import AbstractContextManager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from buduunkhad.core import paths
from buduunkhad.core.run_artifacts import (
    ArtifactSealError,
    RunOutputArtifact,
    has_symlink_component,
    is_publishable_relative,
    require_regular_file_under,
    seal_output_artifacts,
    sha256_file,
)

RUN_MANIFEST_FORMAT_VERSION: Final[str] = "2.0.0"
RUN_LAYOUT_VERSION: Final[str] = "run-isolated-v1"
CURRENT_VIEW_FILENAME: Final[str] = ".buduunkhad-current-view.json"
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class RunStorageError(RuntimeError):
    """Raised when run-local storage cannot be used without ambiguity or mutation."""


class ExecutionLockError(RunStorageError):
    """Raised when another process owns the project execution lock."""


def generate_run_id(*, now: datetime | None = None, entropy: str | None = None) -> str:
    """Return a UUIDv7 run identity without requiring Python 3.14.

    The UUID carries a 48-bit Unix-millisecond timestamp and 74 random bits. This preserves time
    sorting and same-second uniqueness while keeping Windows execution paths materially shorter.
    """

    instant = (now or datetime.now(UTC)).astimezone(UTC)
    suffix = entropy or uuid.uuid4().hex
    if re.fullmatch(r"[0-9a-f]{32}", suffix) is None:
        raise ValueError("run ID entropy must be 32 lowercase hexadecimal characters")
    random_bits = int(suffix, 16)
    timestamp_ms = int(instant.timestamp() * 1000) & ((1 << 48) - 1)
    value = timestamp_ms << 80
    value |= 0x7 << 76
    value |= (random_bits & 0xFFF) << 64
    value |= 0b10 << 62
    value |= (random_bits >> 12) & ((1 << 62) - 1)
    return str(uuid.UUID(int=value))


def validate_run_id(value: str) -> str:
    stem = value.split(".", 1)[0].upper() if value else ""
    reserved = stem in {"CON", "PRN", "AUX", "NUL"} or (
        re.fullmatch(r"(?:COM|LPT)[1-9]", stem) is not None
    )
    if (
        not value
        or len(value) > 96
        or value in {".", ".."}
        or value.endswith(".")
        or reserved
        or _RUN_ID_RE.fullmatch(value) is None
    ):
        raise RunStorageError("run ID must be one safe portable path component")
    return value


def validate_execution_roots(raw_root: Path, output_root: Path, runs_root: Path) -> None:
    """Reject symlinked or overlapping raw, compatibility, and execution roots."""

    roots = {
        "raw root": Path(raw_root).absolute(),
        "compatibility output root": Path(output_root).absolute(),
        "runs root": Path(runs_root).absolute(),
    }
    for name, root in roots.items():
        if has_symlink_component(root):
            raise RunStorageError(f"{name} must not use a symlink: {root}")
        roots[name] = root.resolve(strict=False)
    items = list(roots.items())
    for index, (left_name, left) in enumerate(items):
        for right_name, right in items[index + 1 :]:
            if left == right or left in right.parents or right in left.parents:
                raise RunStorageError(
                    f"{left_name} and {right_name} must not overlap: {left} ; {right}"
                )


@dataclass(frozen=True)
class RunLayout:
    """Canonical filesystem layout for one execution."""

    runs_root: Path
    run_id: str

    def __post_init__(self) -> None:
        validate_run_id(self.run_id)

    @property
    def run_dir(self) -> Path:
        return self.runs_root / self.run_id

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / "run_manifest.json"

    @property
    def logs_dir(self) -> Path:
        return self.run_dir / "logs"

    @property
    def log_path(self) -> Path:
        return self.logs_dir / "run.log"

    @property
    def staging_root(self) -> Path:
        return self.run_dir / "staging"

    @property
    def phases_root(self) -> Path:
        return self.run_dir / "phases"

    def staging_phase(self, phase_id: str) -> Path:
        _validate_phase_id(phase_id)
        return self.staging_root / phase_id

    def sealed_phase(self, phase_id: str) -> Path:
        _validate_phase_id(phase_id)
        return self.phases_root / phase_id

    def initialize(self, *, resume: bool = False) -> None:
        root = self.run_dir.absolute()
        if has_symlink_component(root):
            raise RunStorageError(f"run directory must not use a symlink: {root}")
        if root.exists() and not resume:
            raise RunStorageError(f"run directory already exists: {root}")
        if resume and not root.is_dir():
            raise RunStorageError(f"run directory does not exist for resume: {root}")
        for child in (self.logs_dir, self.staging_root, self.phases_root):
            if child.exists() and (child.is_symlink() or has_symlink_component(child)):
                raise RunStorageError(f"run layout must not use a symlink: {child}")
        self.logs_dir.mkdir(parents=True, exist_ok=resume)
        self.staging_root.mkdir(parents=True, exist_ok=resume)
        self.phases_root.mkdir(parents=True, exist_ok=resume)


class ProjectExecutionLock(AbstractContextManager["ProjectExecutionLock"]):
    """Exclusive, fail-closed project execution lock based on atomic file creation."""

    def __init__(self, runs_root: Path, run_id: str) -> None:
        self.runs_root = Path(runs_root).absolute()
        self.run_id = validate_run_id(run_id)
        self.path = self.runs_root / ".pipeline.lock"
        self._owned = False

    def __enter__(self) -> ProjectExecutionLock:
        if has_symlink_component(self.runs_root):
            raise ExecutionLockError(f"runs root must not use a symlink: {self.runs_root}")
        self.runs_root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "run_id": self.run_id,
                "pid": os.getpid(),
                "acquired_at": datetime.now(UTC).isoformat(),
            },
            sort_keys=True,
        ).encode("utf-8")
        try:
            descriptor = os.open(
                self.path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError as exc:
            owner = "unknown"
            with suppress(OSError):
                owner = self.path.read_text(encoding="utf-8")
            raise ExecutionLockError(
                f"another pipeline run owns the project execution lock: {owner}"
            ) from exc
        try:
            os.write(descriptor, payload)
        finally:
            os.close(descriptor)
        self._owned = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        if self._owned:
            with suppress(FileNotFoundError):
                self.path.unlink()
            self._owned = False


def prepare_staging_phase(layout: RunLayout, phase_id: str) -> Path:
    """Create one empty staging directory; existing content is never reused."""

    stage = layout.staging_phase(phase_id)
    sealed = layout.sealed_phase(phase_id)
    if stage.exists():
        raise RunStorageError(
            f"partial phase staging already exists and will not be reused: {stage}"
        )
    if sealed.exists():
        raise RunStorageError(f"sealed phase already exists: {sealed}")
    stage.mkdir(parents=True)
    return stage


def seal_and_finalize_phase(
    layout: RunLayout,
    phase_id: str,
    outputs: Iterable[Path],
) -> tuple[
    tuple[Path, ...],
    tuple[RunOutputArtifact, ...],
    tuple[RunOutputArtifact, ...],
]:
    """Seal completed declared outputs, then atomically move staging into ``phases/NN``."""

    stage = layout.staging_phase(phase_id)
    sealed = layout.sealed_phase(phase_id)
    if not stage.is_dir() or stage.is_symlink() or has_symlink_component(stage):
        raise RunStorageError(f"phase staging directory is missing or unsafe: {stage}")
    if sealed.exists() or sealed.is_symlink():
        raise RunStorageError(f"sealed phase destination already exists: {sealed}")
    declared = tuple(Path(value) for value in outputs)
    declared_publishable: set[str] = set()
    for output in declared:
        try:
            candidate = require_regular_file_under(stage, output, description="phase output")
        except ArtifactSealError as exc:
            raise RunStorageError(str(exc)) from exc
        relative = candidate.relative_to(stage.resolve())
        if is_publishable_relative(relative):
            declared_publishable.add(relative.as_posix())
    discovered_publishable: set[str] = set()
    for candidate in stage.rglob("*"):
        if candidate.is_symlink():
            raise RunStorageError(f"phase staging contains a symlink: {candidate}")
        if candidate.is_file():
            relative = candidate.relative_to(stage)
            if is_publishable_relative(relative):
                discovered_publishable.add(relative.as_posix())
    if declared_publishable != discovered_publishable:
        missing = sorted(discovered_publishable - declared_publishable)
        extra = sorted(declared_publishable - discovered_publishable)
        raise RunStorageError(
            "phase publishable output inventory is incomplete "
            f"(unrecorded={missing}, missing={extra})"
        )
    try:
        stage_artifacts = seal_output_artifacts(stage, declared)
    except ArtifactSealError as exc:
        raise RunStorageError(str(exc)) from exc
    relative_outputs: list[Path] = []
    for output in declared:
        try:
            candidate = require_regular_file_under(stage, output, description="phase output")
            relative_outputs.append(candidate.relative_to(stage.resolve()))
        except ArtifactSealError as exc:
            raise RunStorageError(str(exc)) from exc
    sealed.parent.mkdir(parents=True, exist_ok=True)
    sealed_files = tuple(
        RunOutputArtifact(
            path=(Path("phases") / phase_id / candidate.relative_to(stage)).as_posix(),
            sha256=sha256_file(candidate),
            size_bytes=candidate.stat().st_size,
        )
        for candidate in sorted(value for value in stage.rglob("*") if value.is_file())
    )
    os.replace(stage, sealed)
    finalized_outputs = tuple(sealed / relative for relative in relative_outputs)
    artifacts = tuple(
        RunOutputArtifact(
            path=(Path("phases") / phase_id / Path(artifact.path)).as_posix(),
            sha256=artifact.sha256,
            size_bytes=artifact.size_bytes,
        )
        for artifact in stage_artifacts
    )
    verify_sealed_artifacts(layout, sealed_files)
    return finalized_outputs, artifacts, sealed_files


def verify_sealed_artifacts(layout: RunLayout, artifacts: Iterable[RunOutputArtifact]) -> None:
    """Fail if any run-sealed artifact is missing, unsafe, or byte-mutated."""

    seen: set[str] = set()
    phases: dict[str, set[str]] = {}
    for artifact in artifacts:
        if artifact.path in seen:
            raise RunStorageError(f"sealed artifact path is duplicated: {artifact.path}")
        seen.add(artifact.path)
        parts = Path(artifact.path).parts
        if len(parts) < 3 or parts[0] != "phases":
            raise RunStorageError(f"sealed artifact path is not run-local: {artifact.path}")
        _validate_phase_id(parts[1])
        phases.setdefault(parts[1], set()).add(artifact.path)
        try:
            path = require_regular_file_under(
                layout.run_dir,
                layout.run_dir / Path(artifact.path),
                description="sealed run artifact",
            )
        except ArtifactSealError as exc:
            raise RunStorageError(str(exc)) from exc
        if path.stat().st_size != artifact.size_bytes or sha256_file(path) != artifact.sha256:
            raise RunStorageError(f"sealed run artifact changed: {artifact.path}")
    for phase_id, expected in phases.items():
        root = layout.sealed_phase(phase_id)
        observed: set[str] = set()
        for path in root.rglob("*"):
            if path.is_symlink():
                raise RunStorageError(f"sealed phase contains a symlink: {path}")
            if path.is_file():
                observed.add(path.relative_to(layout.run_dir).as_posix())
        if observed != expected:
            raise RunStorageError(
                f"sealed Phase {phase_id} file inventory changed "
                f"(added={sorted(observed - expected)}, missing={sorted(expected - observed)})"
            )


def promote_phase_to_current(
    layout: RunLayout,
    phase_id: str,
    output_root: Path,
    artifacts: Iterable[RunOutputArtifact],
) -> Path:
    """Atomically replace one long-named compatibility phase view from a sealed run."""

    artifact_tuple = tuple(artifacts)
    verify_sealed_artifacts(layout, artifact_tuple)
    source = layout.sealed_phase(phase_id)
    if not source.is_dir() or source.is_symlink() or has_symlink_component(source):
        raise RunStorageError(f"sealed phase directory is missing or unsafe: {source}")
    root = Path(output_root).absolute()
    if has_symlink_component(root):
        raise RunStorageError(f"compatibility output root must not use a symlink: {root}")
    root.mkdir(parents=True, exist_ok=True)
    destination = paths.phase_dir(root, phase_id)
    temporary = root / f".promote-{phase_id}-{uuid.uuid4().hex}"
    backup = root / f".previous-{phase_id}-{uuid.uuid4().hex}"
    try:
        shutil.copytree(source, temporary, copy_function=shutil.copy2)
        for artifact in artifact_tuple:
            prefix = Path("phases") / phase_id
            relative = Path(artifact.path).relative_to(prefix)
            copied = require_regular_file_under(
                temporary, temporary / relative, description="promoted compatibility artifact"
            )
            if (
                copied.stat().st_size != artifact.size_bytes
                or sha256_file(copied) != artifact.sha256
            ):
                raise RunStorageError(f"compatibility promotion changed bytes: {artifact.path}")
        if destination.exists():
            os.replace(destination, backup)
        try:
            os.replace(temporary, destination)
        except Exception:
            if backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise
        try:
            _record_current_view(root, phase_id, layout.run_id, artifact_tuple)
        except Exception:
            if destination.exists():
                shutil.rmtree(destination)
            if backup.exists():
                os.replace(backup, destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return destination
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        if backup.exists() and destination.exists():
            shutil.rmtree(backup)


def _record_current_view(
    output_root: Path,
    phase_id: str,
    run_id: str,
    artifacts: tuple[RunOutputArtifact, ...],
) -> None:
    path = output_root / CURRENT_VIEW_FILENAME
    data: dict[str, object] = {"format_version": "1.0.0", "phases": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            raise RunStorageError(f"compatibility current-view record is invalid: {path}") from exc
        if not isinstance(loaded, dict) or not isinstance(loaded.get("phases"), dict):
            raise RunStorageError(f"compatibility current-view record is invalid: {path}")
        data = loaded
    phases = data["phases"]
    assert isinstance(phases, dict)
    phases[phase_id] = {
        "run_id": run_id,
        "artifact_inventory_sha256": _artifact_inventory_sha256(artifacts),
    }
    temporary = output_root / f"{CURRENT_VIEW_FILENAME}.{uuid.uuid4().hex}.tmp"
    try:
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _artifact_inventory_sha256(artifacts: tuple[RunOutputArtifact, ...]) -> str:
    import hashlib

    payload = json.dumps(
        [artifact.model_dump(mode="json") for artifact in artifacts],
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_phase_id(value: str) -> None:
    if re.fullmatch(r"(0[0-9]|1[01]|99)", value) is None:
        raise RunStorageError(f"invalid phase ID: {value}")
