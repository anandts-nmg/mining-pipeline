"""Run-isolated staging, sealing, locking, and compatibility promotion."""

from __future__ import annotations

import hashlib
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
from typing import Annotated, Final, Self, cast

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

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

RUN_MANIFEST_FORMAT_VERSION: Final[str] = "2.1.0"
SUPPORTED_RUN_MANIFEST_FORMAT_VERSIONS: Final[frozenset[str]] = frozenset({"2.0.0", "2.1.0"})
RUN_LAYOUT_VERSION: Final[str] = "run-isolated-v1"
CURRENT_VIEW_FILENAME: Final[str] = ".buduunkhad-current-view.json"
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PHASE_SEQUENCE = tuple(f"{value:02d}" for value in range(12)) + ("99",)
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class RunStorageError(RuntimeError):
    """Raised when run-local storage cannot be used without ambiguity or mutation."""


class ExecutionLockError(RunStorageError):
    """Raised when another process owns the project execution lock."""


class SourcePhaseBinding(BaseModel):
    """Stable identity of one sealed predecessor phase consumed by another run."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    phase_id: str
    source_run_id: str
    source_manifest_sha256: Sha256
    source_phase_sha256: Sha256

    @field_validator("phase_id")
    @classmethod
    def _valid_phase_id(cls, value: str) -> str:
        _validate_phase_id(value)
        return value

    @field_validator("source_run_id")
    @classmethod
    def _valid_source_run_id(cls, value: str) -> str:
        return validate_run_id(value)

    @classmethod
    def model_construct(
        cls,
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> Self:
        del _fields_set, values
        raise TypeError("model_construct is unsupported; use validated construction")


@dataclass(frozen=True)
class ResolvedSourcePhase:
    """One strictly validated source phase and its immutable run-local directory."""

    binding: SourcePhaseBinding
    phase_dir: Path
    output_artifacts: tuple[RunOutputArtifact, ...]
    sealed_files: tuple[RunOutputArtifact, ...]
    gate_status: str
    gate_provisional: bool


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


def resolve_source_phase(
    runs_root: Path,
    phase_id: str,
    source_run_id: str,
    *,
    require_advance: bool,
    require_qaqc_passed: bool = True,
) -> ResolvedSourcePhase:
    """Resolve one exact completed source phase from a strict run-manifest contract.

    This is the shared authority boundary for predecessor-run inputs and evidence records. It
    validates the top-level run identity and chronology, every phase identity and inventory, and
    the exact selected phase seal before returning a path. ``require_advance`` additionally
    rejects a phase whose recorded gate did not permit downstream execution.
    """

    _validate_phase_id(phase_id)
    run_id = validate_run_id(source_run_id)
    layout = RunLayout(Path(runs_root).absolute(), run_id)
    try:
        manifest_path = require_regular_file_under(
            layout.run_dir,
            layout.manifest_path,
            description="source run manifest",
        )
        data = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (ArtifactSealError, OSError, UnicodeError, ValueError) as exc:
        raise RunStorageError("source run manifest is invalid") from exc
    if not isinstance(data, dict):
        raise RunStorageError("source run manifest root must be an object")
    if data.get("manifest_format_version") not in SUPPORTED_RUN_MANIFEST_FORMAT_VERSIONS:
        raise RunStorageError("source run manifest format is unsupported")
    if data.get("run_layout_version") != RUN_LAYOUT_VERSION:
        raise RunStorageError("source run layout is unsupported")
    if data.get("run_id") != run_id or layout.run_dir.name != run_id:
        raise RunStorageError("source run manifest identity does not match its directory")
    started = _aware_datetime(data.get("started_at"), "source run started_at")
    finished = _aware_datetime(data.get("finished_at"), "source run finished_at")
    if finished < started:
        raise RunStorageError("source run timestamps are out of order")
    if data.get("dry_run") is not False:
        raise RunStorageError("dry runs cannot provide sealed predecessor evidence")
    if data.get("error") != "":
        raise RunStorageError("failed or incomplete runs cannot provide predecessor evidence")

    selected = data.get("selected_phases")
    raw_phases = data.get("phases")
    if (
        not isinstance(selected, list)
        or not selected
        or not all(isinstance(item, str) for item in selected)
        or len(selected) != len(set(selected))
        or not isinstance(raw_phases, list)
        or not raw_phases
    ):
        raise RunStorageError("source run phase selection is malformed")
    for selected_id in selected:
        _validate_phase_id(selected_id)
    if [*selected] != sorted(selected, key=_PHASE_SEQUENCE.index):
        raise RunStorageError("source run phase selection is not in workflow order")

    phase_records: dict[str, dict[str, object]] = {}
    for raw_phase in raw_phases:
        if not isinstance(raw_phase, dict):
            raise RunStorageError("source run phase record is malformed")
        raw_phase_id = raw_phase.get("phase_id")
        if not isinstance(raw_phase_id, str):
            raise RunStorageError("source run phase identity is malformed")
        _validate_phase_id(raw_phase_id)
        if raw_phase_id in phase_records or raw_phase_id not in selected:
            raise RunStorageError("source run phase identities are duplicated or unselected")
        phase_records[raw_phase_id] = cast(dict[str, object], raw_phase)
    if list(phase_records) != selected[: len(phase_records)]:
        raise RunStorageError("source run phases are not an ordered prefix of its selection")
    if phase_id not in phase_records:
        raise RunStorageError(f"source run does not contain completed Phase {phase_id}")

    phase = phase_records[phase_id]
    if phase.get("status") != "ok" or phase.get("error") != "":
        raise RunStorageError(f"source Phase {phase_id} did not complete successfully")
    if require_qaqc_passed and phase.get("qaqc_passed") is not True:
        raise RunStorageError(f"source Phase {phase_id} did not pass deterministic QA/QC")
    if not isinstance(phase.get("qaqc_pending"), bool):
        raise RunStorageError("source phase QA/QC pending state is malformed")
    pending_count = phase.get("pending_human_review_or_qaqc_count")
    if not isinstance(pending_count, int) or isinstance(pending_count, bool) or pending_count < 0:
        raise RunStorageError("source phase pending count is malformed")
    if phase.get("qaqc_pending") is not (pending_count > 0):
        raise RunStorageError("source phase pending count is inconsistent")

    gate = phase.get("gate")
    if not isinstance(gate, dict):
        raise RunStorageError("source phase gate record is malformed")
    gate_data = cast(dict[str, object], gate)
    gate_status = gate_data.get("status")
    if gate_status not in {"go", "no-go", "blocked"}:
        raise RunStorageError("source phase gate status is malformed")
    if not isinstance(gate_data.get("overridden"), bool) or not isinstance(
        gate_data.get("provisional"), bool
    ):
        raise RunStorageError("source phase gate flags are malformed")
    if require_advance and gate_status != "go":
        raise RunStorageError(f"source Phase {phase_id} gate did not permit advancement")

    outputs_raw = phase.get("output_artifacts")
    sealed_raw = phase.get("sealed_files")
    outputs_list = phase.get("outputs")
    if (
        not isinstance(outputs_raw, list)
        or not isinstance(sealed_raw, list)
        or not isinstance(outputs_list, list)
        or not all(isinstance(item, str) for item in outputs_list)
    ):
        raise RunStorageError("source phase artifact inventory is malformed")
    try:
        outputs = tuple(RunOutputArtifact.model_validate(item) for item in outputs_raw)
        sealed = tuple(RunOutputArtifact.model_validate(item) for item in sealed_raw)
    except ValueError as exc:
        raise RunStorageError("source phase artifact inventory is malformed") from exc
    output_map = {item.path: item for item in outputs}
    sealed_map = {item.path: item for item in sealed}
    expected_prefix = ("phases", phase_id)
    if (
        len(output_map) != len(outputs)
        or len(sealed_map) != len(sealed)
        or len(outputs_list) != len(set(outputs_list))
        or set(outputs_list) != set(output_map)
        or any(sealed_map.get(path) != artifact for path, artifact in output_map.items())
        or any(tuple(Path(item.path).parts[:2]) != expected_prefix for item in sealed)
    ):
        raise RunStorageError("source phase artifact inventory is inconsistent")
    verify_sealed_artifacts(layout, sealed)

    source_phase_sha256 = _sha256_json_value(phase)
    binding = SourcePhaseBinding(
        phase_id=phase_id,
        source_run_id=run_id,
        source_manifest_sha256=sha256_file(manifest_path),
        source_phase_sha256=source_phase_sha256,
    )
    return ResolvedSourcePhase(
        binding=binding,
        phase_dir=layout.sealed_phase(phase_id).resolve(),
        output_artifacts=outputs,
        sealed_files=sealed,
        gate_status=cast(str, gate_status),
        gate_provisional=cast(bool, gate_data["provisional"]),
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
    phases = cast(dict[str, object], data["phases"])
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
    payload = json.dumps(
        [artifact.model_dump(mode="json") for artifact in artifacts],
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_json_value(value: object) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _aware_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise RunStorageError(f"{field} is missing")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RunStorageError(f"{field} is malformed") from exc
    if parsed.utcoffset() is None:
        raise RunStorageError(f"{field} must be timezone-aware")
    return parsed


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _validate_phase_id(value: str) -> None:
    if re.fullmatch(r"(0[0-9]|1[01]|99)", value) is None:
        raise RunStorageError(f"invalid phase ID: {value}")
