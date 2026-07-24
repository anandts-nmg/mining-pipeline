"""Publish curated deliverables to a publish root (e.g. a Google-Drive folder).

Per ADR 0001, generated outputs are build artifacts. This copies only the small,
high-value **deliverables** — GIS layers, registers, logs, reports — into a
*versioned* subfolder under ``publish_root`` (typically a Drive-for-Desktop folder
so teammates can see them once shared). The bulky **raw working copies** (rasters
and scans copied from the read-only archive) are deliberately excluded so we never
re-upload duplicates of data that already lives in the Drive.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import cast

from pydantic import ValidationError

from buduunkhad import __version__
from buduunkhad.core.execution_policy import (
    ExecutionAuthorization,
    ExecutionMode,
    ExecutionPolicyBinding,
    legacy_execution_mode,
    validate_execution_policy_binding,
)
from buduunkhad.core.publication_manifest import (
    AGGREGATION_NOTICE,
    PUBLICATION_MANIFEST_FORMAT_VERSION,
    QGZ_FLAT_DATASOURCE_REWRITE,
    CompatibilityRunManifest,
    PublicationManifest,
    PublicationProjectReference,
    PublishedOutput,
    PublishedPhase,
    SourceBindingMode,
    phase_package_tag,
    publication_id_for,
    publication_status_for,
)
from buduunkhad.core.run_artifacts import (
    DELIVERABLE_SUFFIXES,
    WORKING_COPY_DIRS,
    ArtifactSealError,
    RunOutputArtifact,
    has_symlink_component,
    is_publishable_relative,
    is_working_copy,
    require_regular_file_under,
    sha256_file,
)
from buduunkhad.core.run_storage import (
    RUN_LAYOUT_VERSION,
    SUPPORTED_RUN_MANIFEST_FORMAT_VERSIONS,
    RunLayout,
    RunStorageError,
    validate_run_id,
    verify_sealed_artifacts,
)


class PublishError(RuntimeError):
    """Raised when a publish would silently overwrite (label reuse) or clobber (name collision)."""


@dataclass(frozen=True)
class PublishResult:
    dest: Path
    files: list[Path] = field(default_factory=list)
    skipped_working_copies: int = 0


@dataclass(frozen=True)
class _RunPhaseRecord:
    manifest_path: Path
    manifest_sha256: str
    run_id: str
    started_at: str
    finished_at: str
    phase_id: str
    execution_status: str
    outputs: tuple[Path, ...]
    output_artifacts: tuple[RunOutputArtifact, ...] | None
    gate_state: str
    gate_provisional: bool
    human_review_or_qaqc_pending: bool
    pending_human_review_or_qaqc_count: int | None
    execution_mode: ExecutionMode
    authorization_ids: tuple[str, ...]

    @property
    def binding_mode(self) -> SourceBindingMode:
        return "SHA256_BOUND" if self.output_artifacts is not None else "LEGACY_PATH_ONLY"


@dataclass(frozen=True)
class _ObservedArtifact:
    path: Path
    relative: str
    sha256: str
    size_bytes: int


def _require_safe_component(value: str, field_name: str) -> str:
    if (
        not value
        or value in {".", ".."}
        or any(separator in value for separator in ("/", "\\", ":"))
    ):
        raise PublishError(f"{field_name} must be one path-safe component")
    return value


def _is_working_copy(rel: Path) -> bool:
    return is_working_copy(rel)


def _require_link_free_path(path: Path, description: str) -> Path:
    absolute = Path(path).absolute()
    if has_symlink_component(absolute):
        raise PublishError(f"{description} must not use a symlink: {path}")
    return absolute.resolve()


def _require_root(path: Path, description: str, *, create: bool = False) -> Path:
    absolute = Path(path).absolute()
    if has_symlink_component(absolute):
        raise PublishError(f"{description} must not use a symlink: {path}")
    if create:
        absolute.mkdir(parents=True, exist_ok=True)
    resolved = _require_link_free_path(absolute, description)
    if not resolved.is_dir():
        raise PublishError(f"{description} is not a directory: {path}")
    return resolved


def _require_package_file(package_root: Path, relative: str, description: str) -> Path:
    try:
        return require_regular_file_under(
            package_root, package_root / Path(relative), description=description
        )
    except ArtifactSealError as exc:
        raise PublishError(str(exc)) from exc


def _reject_overlapping_roots(*roots: tuple[str, Path]) -> None:
    for index, (left_name, left) in enumerate(roots):
        for right_name, right in roots[index + 1 :]:
            if left == right or left in right.parents or right in left.parents:
                raise PublishError(
                    f"{left_name} and {right_name} must not overlap: {left} ; {right}"
                )


def _phase_tag(rel: Path) -> str:
    """Shallow phase grouping for the published package (keeps paths short, reader-friendly).

    Phase folders are named ``<NN>_<...>``; group everything by the two-digit prefix into
    ``PhaseNN`` (so ``03_Phase_3_Geological_...`` publishes under ``Phase03/``, not its long name).
    """
    return phase_package_tag(rel)


def collect_deliverables(output_root: Path) -> list[Path]:
    """Deliverable files under ``output_root`` (excludes raw working copies)."""
    output_root = _require_root(Path(output_root), "output root")
    out: list[Path] = []
    for p in sorted(output_root.rglob("*")):
        if p.is_symlink():
            raise PublishError(f"output tree contains a symlink: {p}")
        if not p.is_file():
            continue
        rel = p.relative_to(output_root)
        if is_publishable_relative(rel):
            try:
                out.append(
                    require_regular_file_under(output_root, p, description="publication output")
                )
            except ArtifactSealError as exc:
                raise PublishError(str(exc)) from exc
    return out


def latest_run_manifest(runs_root: Path) -> Path | None:
    """Return the chronologically latest manifest by its recorded completion time."""

    runs_root = Path(runs_root)
    if not runs_root.exists():
        return None
    manifests = list(runs_root.glob("*/run_manifest.json"))
    if not manifests:
        return None
    timed = [(_run_manifest_completion(manifest), manifest) for manifest in manifests]
    latest_time = max(value for value, _manifest in timed)
    latest = [manifest for value, manifest in timed if value == latest_time]
    if len(latest) != 1:
        raise PublishError("latest run manifest is ambiguous by recorded completion time")
    return latest[0]


def latest_gate_per_phase(runs_root: Path) -> dict[str, dict[str, object]]:
    """Most-recent **real** (non-dry) gate per phase across all run manifests.

    The published package spans phases run at different times, so a single latest manifest
    (which may be a dry run or cover only some phases) can't describe every PhaseNN folder.
    Compare recorded completion timestamps; caller-supplied run IDs are not chronological.
    """
    runs_root = Path(runs_root)
    out: dict[str, dict[str, object]] = {}
    if not runs_root.exists():
        return out
    phase_times: dict[str, datetime] = {}
    for man in runs_root.glob("*/run_manifest.json"):
        completed_at = _run_manifest_completion(man)
        data = _load_json_object(man)
        if data.get("dry_run"):
            continue
        phases = data.get("phases")
        if not isinstance(phases, list):
            raise PublishError(f"run manifest lacks a phases list: {man}")
        for p in phases:
            if not isinstance(p, dict):
                raise PublishError(f"run manifest contains a malformed phase record: {man}")
            phase_id = p.get("phase_id")
            if not isinstance(phase_id, str):
                raise PublishError(f"run manifest contains a malformed phase record: {man}")
            gate = p.get("gate")
            gate_status = gate.get("status") if isinstance(gate, dict) else None
            gate_provisional = gate.get("provisional", False) if isinstance(gate, dict) else False
            if isinstance(gate_status, str) and gate_status:
                if phase_times.get(phase_id) == completed_at:
                    raise PublishError(
                        f"latest gate is ambiguous for Phase {phase_id} at {completed_at.isoformat()}"
                    )
                if phase_id not in phase_times or completed_at > phase_times[phase_id]:
                    phase_times[phase_id] = completed_at
                    out[phase_id] = {
                        "status": gate_status,
                        "provisional": gate_provisional,
                        "run_id": data.get("run_id", ""),
                    }
    return out


def _run_manifest_completion(path: Path) -> datetime:
    if path.is_symlink() or has_symlink_component(path):
        raise PublishError(f"source run manifest must not use a symlink: {path}")
    data = _load_json_object(path)
    run_id = data.get("run_id")
    if run_id != path.parent.name:
        raise PublishError(f"source run ID does not match its directory: {path}")
    value = data.get("finished_at")
    if not isinstance(value, str) or not value:
        raise PublishError(f"run manifest lacks finished_at: {path}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PublishError(f"run manifest has invalid finished_at: {path}") from exc
    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        return parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PublishError(f"run manifest contains duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise PublishError(f"run manifest is unreadable or invalid: {path}") from exc
    if not isinstance(value, dict):
        raise PublishError(f"run manifest root must be an object: {path}")
    return value


def _resolve_recorded_output(value: str, output_root: Path) -> Path:
    recorded = Path(value)
    candidates: tuple[Path, ...]
    if recorded.is_absolute():
        candidates = (recorded.absolute(),)
    else:
        candidates = (
            (output_root / recorded).absolute(),
            (output_root.parent / recorded).absolute(),
            (Path.cwd() / recorded).absolute(),
        )
    selected = candidates[0]
    for candidate in candidates:
        if candidate.exists():
            selected = candidate
            break
    for candidate in candidates:
        try:
            candidate.resolve().relative_to(output_root.resolve())
        except ValueError:
            continue
        if not selected.exists():
            selected = candidate
        break
    if has_symlink_component(selected):
        raise PublishError(f"recorded phase output must not use a symlink: {value}")
    resolved = selected.resolve()
    try:
        resolved.relative_to(output_root.resolve())
    except ValueError as exc:
        raise PublishError(f"recorded phase output escapes output_root: {value}") from exc
    return resolved


def _deliverable_relative(path: Path, output_root: Path) -> Path | None:
    try:
        relative = path.resolve().relative_to(output_root.resolve())
    except ValueError:
        return None
    if not is_publishable_relative(relative):
        return None
    return relative


def _manifest_timestamp(data: dict[str, object], field_name: str, path: Path) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value:
        raise PublishError(f"run manifest lacks {field_name}: {path}")
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise PublishError(f"run manifest has invalid {field_name}: {path}") from exc
    return value


def _load_run_phase_records(
    runs_root: Path, output_root: Path, *, selected_run_id: str | None = None
) -> dict[str, list[_RunPhaseRecord]]:
    records: dict[str, list[_RunPhaseRecord]] = {}
    if not runs_root.exists():
        raise PublishError(f"runs root does not exist: {runs_root}")
    manifests = (
        [runs_root / validate_run_id(selected_run_id) / "run_manifest.json"]
        if selected_run_id is not None
        else list(runs_root.glob("*/run_manifest.json"))
    )
    manifests = [path for path in manifests if path.exists()]
    if not manifests:
        raise PublishError(f"no source run manifests found under: {runs_root}")
    seen_runs: set[str] = set()
    for manifest_path in manifests:
        if manifest_path.is_symlink() or has_symlink_component(manifest_path):
            raise PublishError(f"source run manifest must not use a symlink: {manifest_path}")
        try:
            manifest_path.resolve().relative_to(runs_root.resolve())
        except ValueError as exc:
            raise PublishError(f"source run manifest escapes runs_root: {manifest_path}") from exc
        data = _load_json_object(manifest_path)
        run_id = data.get("run_id")
        phases = data.get("phases")
        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or not isinstance(phases, list)
            or type(data.get("dry_run")) is not bool
        ):
            raise PublishError(f"run manifest lacks a valid run_id or phases list: {manifest_path}")
        _require_safe_component(run_id, "source run ID")
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id) is None:
            raise PublishError(f"source run ID has unsupported characters: {run_id}")
        if run_id != manifest_path.parent.name:
            raise PublishError(
                f"source run ID does not match its directory: {run_id} != "
                f"{manifest_path.parent.name}"
            )
        if run_id in seen_runs:
            raise PublishError(f"duplicate source run identity: {run_id}")
        seen_runs.add(run_id)
        started_at = _manifest_timestamp(data, "started_at", manifest_path)
        finished_at = _manifest_timestamp(data, "finished_at", manifest_path)
        try:
            if datetime.fromisoformat(finished_at) < datetime.fromisoformat(started_at):
                raise PublishError(f"run manifest finishes before it starts: {manifest_path}")
        except TypeError as exc:
            raise PublishError(
                f"run manifest timestamps use incompatible timezone forms: {manifest_path}"
            ) from exc
        if data.get("dry_run") is True:
            continue
        run_isolated = data.get("run_layout_version") == RUN_LAYOUT_VERSION
        seen_phases: set[str] = set()
        for phase in phases:
            if not isinstance(phase, dict):
                raise PublishError(
                    f"run manifest contains a malformed phase record: {manifest_path}"
                )
            phase_id = phase.get("phase_id")
            execution_status = phase.get("status")
            output_values = phase.get("outputs")
            gate = phase.get("gate")
            if (
                not isinstance(phase_id, str)
                or re.fullmatch(r"(0[0-9]|1[01]|99)", phase_id) is None
                or not isinstance(execution_status, str)
                or not isinstance(output_values, list)
                or not all(isinstance(item, str) for item in output_values)
                or not isinstance(gate, dict)
                or not isinstance(gate.get("status"), str)
                or not gate.get("status")
                or type(gate.get("provisional")) is not bool
                or type(phase.get("qaqc_pending")) is not bool
            ):
                raise PublishError(
                    f"run manifest phase lacks outputs or gate provenance: {manifest_path}"
                )
            if phase_id in seen_phases:
                raise PublishError(f"run manifest repeats Phase {phase_id}: {manifest_path}")
            seen_phases.add(phase_id)
            recorded_outputs = cast(list[str], output_values)
            gate_status = gate.get("status")
            assert isinstance(gate_status, str)
            pending_count = phase.get("pending_human_review_or_qaqc_count")
            if pending_count is not None and (type(pending_count) is not int or pending_count < 0):
                raise PublishError(f"run manifest has an invalid pending count: {manifest_path}")
            execution_mode, authorization_ids = _source_phase_execution_provenance(
                data,
                cast(dict[str, object], phase),
                phase_id,
            )
            has_artifact_inventory = "output_artifacts" in phase
            artifact_values = phase.get("output_artifacts")
            output_artifacts: tuple[RunOutputArtifact, ...] | None
            if not has_artifact_inventory:
                output_artifacts = None
                resolved_outputs = tuple(
                    _resolve_recorded_output(item, output_root) for item in recorded_outputs
                )
            elif not isinstance(artifact_values, list):
                raise PublishError(f"run manifest output_artifacts is invalid: {manifest_path}")
            else:
                try:
                    output_artifacts = tuple(
                        RunOutputArtifact.model_validate(item) for item in artifact_values
                    )
                except ValidationError as exc:
                    raise PublishError(
                        f"run manifest output_artifacts is invalid: {manifest_path}"
                    ) from exc
                artifact_paths = tuple(item.path for item in output_artifacts)
                if len(set(artifact_paths)) != len(artifact_paths):
                    raise PublishError(f"run manifest repeats an artifact path: {manifest_path}")
                recorded_paths = _recorded_publishable_paths(
                    recorded_outputs,
                    set(artifact_paths),
                    phase_id,
                )
                if set(artifact_paths) != recorded_paths:
                    raise PublishError(
                        f"run manifest artifact inventory is incomplete or inconsistent: "
                        f"{manifest_path}"
                    )
                resolved_outputs_list: list[Path] = []
                for artifact_path in artifact_paths:
                    artifact_root = manifest_path.parent if run_isolated else output_root
                    candidate = (artifact_root / Path(artifact_path)).absolute()
                    if has_symlink_component(candidate):
                        raise PublishError(
                            f"recorded phase artifact must not use a symlink: {artifact_path}"
                        )
                    resolved = candidate.resolve()
                    try:
                        resolved.relative_to(artifact_root.resolve())
                    except ValueError as exc:
                        raise PublishError(
                            f"recorded phase artifact escapes its declared root: {artifact_path}"
                        ) from exc
                    resolved_outputs_list.append(resolved)
                resolved_outputs = tuple(resolved_outputs_list)
                if execution_status != "ok" and output_artifacts:
                    raise PublishError(
                        f"incomplete phase claims sealed output artifacts: {manifest_path}"
                    )
            record = _RunPhaseRecord(
                manifest_path=manifest_path,
                manifest_sha256=_sha256(manifest_path),
                run_id=run_id,
                started_at=started_at,
                finished_at=finished_at,
                phase_id=phase_id,
                execution_status=execution_status,
                outputs=resolved_outputs,
                output_artifacts=output_artifacts,
                gate_state=gate_status,
                gate_provisional=gate.get("provisional") is True,
                human_review_or_qaqc_pending=phase.get("qaqc_pending") is True,
                pending_human_review_or_qaqc_count=pending_count,
                execution_mode=execution_mode,
                authorization_ids=authorization_ids,
            )
            records.setdefault(phase_id, []).append(record)
    return records


def _phase_id_from_relative(relative: Path) -> str:
    tag = _phase_tag(relative)
    if not tag.startswith("Phase") or len(tag) != 7 or not tag[5:].isdigit():
        raise PublishError(f"deliverable is not inside a registered phase directory: {relative}")
    return tag[5:]


def _is_runner_qaqc_relative(path: str, phase_id: str) -> bool:
    relative = PurePosixPath(path)
    return relative.name.endswith(f"_Phase{phase_id}_QAQC_Log.xlsx")


def _record_matches_observed(
    candidate: _RunPhaseRecord,
    observed: Mapping[str, _ObservedArtifact],
    output_root: Path,
) -> bool:
    if candidate.output_artifacts is not None:
        expected = {
            artifact.path: (artifact.sha256, artifact.size_bytes)
            for artifact in candidate.output_artifacts
        }
        current = {
            path: (artifact.sha256, artifact.size_bytes) for path, artifact in observed.items()
        }
        return expected == current
    expected_paths = {
        relative.as_posix()
        for path in candidate.outputs
        if (relative := _deliverable_relative(path, output_root)) is not None
    }
    observed_paths = set(observed)
    return expected_paths <= observed_paths and all(
        path in expected_paths or _is_runner_qaqc_relative(path, candidate.phase_id)
        for path in observed_paths
    )


def _recorded_publishable_paths(
    output_values: Sequence[object], expected_paths: set[str], phase_id: str
) -> set[str]:
    matched: list[str] = []
    for value in output_values:
        if not isinstance(value, str):
            raise PublishError(f"source outputs are invalid for Phase {phase_id}")
        normalized = value.replace("\\", "/")
        path = PurePosixPath(normalized)
        if path.suffix.lower() not in DELIVERABLE_SUFFIXES or any(
            part in WORKING_COPY_DIRS for part in path.parts
        ):
            continue
        matches = [
            expected
            for expected in expected_paths
            if normalized == expected or normalized.endswith(f"/{expected}")
        ]
        if len(matches) != 1:
            raise PublishError(
                f"source output path is unrecorded or ambiguous for Phase {phase_id}: {value}"
            )
        matched.append(matches[0])
    if len(matched) != len(set(matched)):
        raise PublishError(f"source output paths are duplicated for Phase {phase_id}")
    return set(matched)


def _select_publication_records(
    output_root: Path,
    sources: tuple[Path, ...],
    records: dict[str, list[_RunPhaseRecord]],
    source_runs: Mapping[str, str] | None = None,
) -> dict[str, _RunPhaseRecord]:
    actual: dict[str, dict[str, _ObservedArtifact]] = {}
    for source in sources:
        relative = source.resolve().relative_to(output_root.resolve())
        portable = relative.as_posix()
        actual.setdefault(_phase_id_from_relative(relative), {})[portable] = _ObservedArtifact(
            path=source.resolve(),
            relative=portable,
            sha256=_sha256(source),
            size_bytes=source.stat().st_size,
        )

    phase_ids = set(actual)
    for phase_id, candidates in records.items():
        if any(
            candidate.output_artifacts
            or any(
                _deliverable_relative(path, output_root) is not None for path in candidate.outputs
            )
            for candidate in candidates
        ):
            phase_ids.add(phase_id)
    selectors = dict(source_runs or {})
    unknown_selectors = sorted(set(selectors) - phase_ids)
    if unknown_selectors:
        raise PublishError(f"source-run selector has no deliverable Phase: {unknown_selectors}")

    selected: dict[str, _RunPhaseRecord] = {}
    for phase_id in sorted(phase_ids):
        phase_candidates = [
            candidate
            for candidate in records.get(phase_id, [])
            if candidate.execution_status == "ok"
        ]
        if not phase_candidates:
            raise PublishError(f"no complete source run manifest published Phase {phase_id}")
        observed = actual.get(phase_id, {})
        if not observed:
            raise PublishError(f"Phase {phase_id} source run has missing output(s)")
        requested_run = selectors.get(phase_id)
        if requested_run is not None:
            phase_candidates = [
                candidate for candidate in phase_candidates if candidate.run_id == requested_run
            ]
            if not phase_candidates:
                raise PublishError(
                    f"selected source run {requested_run} has no complete Phase {phase_id}"
                )

        if requested_run is not None:
            matches_requested = [
                candidate
                for candidate in phase_candidates
                if _record_matches_observed(candidate, observed, output_root)
            ]
            if len(matches_requested) != 1:
                raise PublishError(
                    f"selected source run {requested_run} does not exactly match Phase "
                    f"{phase_id} outputs"
                )
            selected[phase_id] = matches_requested[0]
            continue

        strong_candidates = [
            candidate for candidate in phase_candidates if candidate.output_artifacts is not None
        ]
        matching = [
            candidate
            for candidate in strong_candidates
            if _record_matches_observed(candidate, observed, output_root)
        ]
        if not strong_candidates:
            matching = [
                candidate
                for candidate in phase_candidates
                if _record_matches_observed(candidate, observed, output_root)
            ]
        if not matching:
            mode = "SHA256-bound" if strong_candidates else "legacy path-only"
            raise PublishError(
                f"no {mode} source run exactly matches current Phase {phase_id} outputs"
            )
        if len(matching) != 1:
            run_ids = sorted(candidate.run_id for candidate in matching)
            raise PublishError(
                f"Phase {phase_id} matches multiple source runs {run_ids}; select one with "
                f"--source-run {phase_id}=RUN_ID"
            )
        selected[phase_id] = matching[0]
    if not selected:
        raise PublishError("publication contains no phase deliverables")
    return selected


def _select_exact_run_records(
    runs_root: Path,
    run_id: str,
    records: dict[str, list[_RunPhaseRecord]],
) -> tuple[dict[str, _RunPhaseRecord], dict[Path, Path]]:
    """Select every complete strongly sealed phase from one run-isolated manifest."""

    manifest_path = runs_root / run_id / "run_manifest.json"
    data = _load_json_object(manifest_path)
    if (
        data.get("manifest_format_version") not in SUPPORTED_RUN_MANIFEST_FORMAT_VERSIONS
        or data.get("run_layout_version") != RUN_LAYOUT_VERSION
    ):
        raise PublishError("exact-run publication requires a run-isolated source manifest")
    if not isinstance(data.get("finished_at"), str) or not data.get("finished_at"):
        raise PublishError("source run is incomplete and cannot be published")
    if data.get("error"):
        raise PublishError("source run ended with an error and cannot be published")
    raw_phases = data.get("phases")
    if not isinstance(raw_phases, list):
        raise PublishError("source run phase records are invalid")
    sealed_files: list[RunOutputArtifact] = []
    try:
        for raw_phase in raw_phases:
            if isinstance(raw_phase, dict) and raw_phase.get("status") == "ok":
                values = raw_phase.get("sealed_files")
                if not isinstance(values, list):
                    raise PublishError("run-isolated phase lacks a complete file seal")
                sealed_files.extend(RunOutputArtifact.model_validate(value) for value in values)
        verify_sealed_artifacts(RunLayout(runs_root, run_id), sealed_files)
    except (RunStorageError, ValidationError) as exc:
        raise PublishError(f"source run file seal is invalid: {exc}") from exc
    selected: dict[str, _RunPhaseRecord] = {}
    targets: dict[Path, Path] = {}
    for phase_id, candidates in sorted(records.items()):
        matching = [candidate for candidate in candidates if candidate.run_id == run_id]
        if len(matching) != 1:
            raise PublishError(f"exact run has ambiguous Phase {phase_id} provenance")
        record = matching[0]
        if record.execution_status != "ok":
            continue
        if record.output_artifacts is None:
            raise PublishError("run-isolated publication cannot use legacy path-only binding")
        if not record.output_artifacts:
            continue
        selected[phase_id] = record
        for artifact, source in zip(record.output_artifacts, record.outputs, strict=True):
            if phase_package_tag(PurePosixPath(artifact.path)) != f"Phase{phase_id}":
                raise PublishError(
                    f"run artifact path does not belong to Phase {phase_id}: {artifact.path}"
                )
            target_relative = Path(f"Phase{phase_id}") / source.name
            if target_relative in targets.values():
                previous = next(
                    path for path, target in targets.items() if target == target_relative
                )
                raise PublishError(
                    f"Publish name collision: {previous} and {source} both map to {target_relative}"
                )
            targets[source] = target_relative
    if not selected:
        raise PublishError("exact source run contains no complete sealed phase deliverables")
    return selected, targets


def _portable_project_reference(config_path: Path) -> str:
    resolved = config_path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return f"external-config::{resolved.name}"


def _git_commit_sha(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip().lower()
    if len(value) not in {40, 64} or any(
        character not in "0123456789abcdef" for character in value
    ):
        return None
    return value


def _assemble_publication(
    output_root: Path,
    publish_root: Path,
    label: str,
    *,
    runs_root: Path | None = None,
    overwrite: bool = False,
    project_config_path: Path | None = None,
    superseded_publication_id: str | None = None,
    published_at: datetime | None = None,
    source_runs: Mapping[str, str] | None = None,
    run_id: str | None = None,
) -> PublishResult:
    """Copy provenance-bound deliverables into a local publication staging package.

    Raises :class:`PublishError` if the label dir already exists and is non-empty (unless
    ``overwrite=True``) or if two source files would flatten to the same published path — both
    would otherwise silently overwrite, so we fail loudly per the repo's philosophy.
    """
    _require_safe_component(label, "publish label")
    if (
        superseded_publication_id is not None
        and re.fullmatch(r"pub-[0-9a-f]{32}", superseded_publication_id) is None
    ):
        raise PublishError("superseded publication ID is invalid")
    if published_at is not None and (
        published_at.tzinfo is None or published_at.utcoffset() is None
    ):
        raise PublishError("publication timestamp must be timezone-aware")
    publication_time = (published_at or datetime.now(UTC)).astimezone(UTC)
    output_root = _require_root(Path(output_root), "output root")
    if runs_root is None:
        raise PublishError("runs_root is required to bind published phases to source runs")
    runs_root = _require_root(Path(runs_root), "runs root")
    if run_id is not None and source_runs:
        raise PublishError("exact --run-id publication cannot use per-phase source selectors")
    if run_id is not None:
        try:
            run_id = validate_run_id(run_id)
        except RuntimeError as exc:
            raise PublishError(str(exc)) from exc
    publish_root_candidate = _require_link_free_path(Path(publish_root), "publication root")
    _reject_overlapping_roots(
        ("output root", output_root),
        ("runs root", runs_root),
        ("publication root", publish_root_candidate),
    )
    publish_root = _require_root(publish_root_candidate, "publication root", create=True)
    config_path = _require_link_free_path(
        Path(project_config_path or "config/project.yaml"), "project configuration"
    )
    if not config_path.is_file():
        raise PublishError(f"authoritative project configuration is unavailable: {config_path}")
    project = PublicationProjectReference(
        configuration_reference=_portable_project_reference(config_path),
        configuration_sha256=_sha256(config_path),
    )

    dest = publish_root / f"Buduunkhad_Deliverables_{label}"
    if dest.is_symlink() or has_symlink_component(dest):
        raise PublishError(f"publication destination must not use a symlink: {dest}")
    if dest.exists() and any(dest.iterdir()) and not overwrite:
        raise PublishError(
            f"Publish destination already exists and is not empty: {dest}. "
            "Choose a new --label or remove that folder first."
        )

    source_root = output_root
    if run_id is not None:
        source_data = _load_json_object(runs_root / run_id / "run_manifest.json")
        if source_data.get("error"):
            raise PublishError("source run ended with an error and cannot be published")
        records = _load_run_phase_records(runs_root, output_root, selected_run_id=run_id)
        selected, targets = _select_exact_run_records(runs_root, run_id, records)
        source_root = (runs_root / run_id).resolve()
    else:
        v2_manifests = [
            path
            for path in runs_root.glob("*/run_manifest.json")
            if _load_json_object(path).get("run_layout_version") == RUN_LAYOUT_VERSION
        ]
        if v2_manifests:
            raise PublishError(
                "run-isolated outputs require one exact --run-id; the mutable current view "
                "cannot be used as publication provenance"
            )
        # Legacy compatibility: map current-view sources to flattened PhaseNN/<filename> targets.
        targets = {}
        for src in collect_deliverables(output_root):
            target_relative = Path(_phase_tag(src.relative_to(output_root))) / src.name
            if target_relative in targets.values():
                previous = next(
                    source for source, target in targets.items() if target == target_relative
                )
                raise PublishError(
                    f"Publish name collision: {previous} and {src} both map to {target_relative}"
                )
            targets[src.resolve()] = target_relative
        records = _load_run_phase_records(runs_root, output_root)
        selected = _select_publication_records(
            output_root, tuple(targets), records, source_runs=source_runs
        )

    if dest.exists() and overwrite:
        if any(entry.is_symlink() for entry in dest.rglob("*")):
            raise PublishError("existing publication destination contains a symlink")
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    skipped = sum(
        1
        for p in source_root.rglob("*")
        if p.is_file() and _is_working_copy(p.relative_to(source_root))
    )

    copied: list[Path] = []
    phase_records: list[PublishedPhase] = []
    copied_source_manifests: dict[Path, Path] = {}
    for phase_id, record in sorted(selected.items()):
        source_manifest_relative = (
            Path("source_run_manifests") / record.run_id / "run_manifest.json"
        )
        source_manifest_target = dest / source_manifest_relative
        if record.manifest_path not in copied_source_manifests:
            source_manifest_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(record.manifest_path, source_manifest_target)
            copied_source_manifests[record.manifest_path] = source_manifest_target
            copied.append(source_manifest_target)
        sealed_by_path = {artifact.path: artifact for artifact in (record.output_artifacts or ())}
        phase_outputs_list: list[PublishedOutput] = []
        phase_sources = sorted(
            (
                source
                for source in targets
                if _phase_id_from_relative(source.relative_to(source_root)) == phase_id
            ),
            key=lambda source: targets[source].as_posix(),
        )
        for source in phase_sources:
            source_relative = source.relative_to(source_root).as_posix()
            before_sha256 = _sha256(source)
            before_size = source.stat().st_size
            sealed = sealed_by_path.get(source_relative)
            if sealed is not None and (
                sealed.sha256 != before_sha256 or sealed.size_bytes != before_size
            ):
                raise PublishError(
                    f"source output changed after run {record.run_id}: {source_relative}"
                )
            target_relative = targets[source]
            target = dest / target_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            transformation_id = None
            if source.suffix.lower() == ".qgz":
                _publish_qgz_flat(source, target)
                transformation_id = QGZ_FLAT_DATASOURCE_REWRITE
            else:
                shutil.copy2(source, target)
            after_sha256 = _sha256(source)
            after_size = source.stat().st_size
            if (before_sha256, before_size) != (after_sha256, after_size):
                raise PublishError(f"source output changed while publishing: {source_relative}")
            published_sha256 = _sha256(target)
            published_size = target.stat().st_size
            if transformation_id is None and (
                published_sha256 != before_sha256 or published_size != before_size
            ):
                raise PublishError(f"published copy differs from source: {source_relative}")
            copied.append(target)
            phase_outputs_list.append(
                PublishedOutput(
                    path=target_relative.as_posix(),
                    sha256=published_sha256,
                    size_bytes=published_size,
                    source_path=source_relative,
                    source_sha256=sealed.sha256 if sealed is not None else None,
                    source_size_bytes=sealed.size_bytes if sealed is not None else None,
                    transformation_id=transformation_id,
                )
            )
        phase_outputs = tuple(phase_outputs_list)
        phase_records.append(
            PublishedPhase(
                phase_id=phase_id,
                source_run_id=record.run_id,
                source_started_at=record.started_at,
                source_finished_at=record.finished_at,
                source_run_manifest_path=source_manifest_relative.as_posix(),
                source_run_manifest_sha256=record.manifest_sha256,
                execution_status="ok",
                gate_state=record.gate_state,
                gate_provisional=record.gate_provisional,
                human_review_or_qaqc_pending=record.human_review_or_qaqc_pending,
                pending_human_review_or_qaqc_count=record.pending_human_review_or_qaqc_count,
                execution_mode=record.execution_mode,
                authorization_ids=record.authorization_ids,
                source_binding_mode=record.binding_mode,
                outputs=phase_outputs,
            )
        )

    phases = tuple(phase_records)
    compatibility_record = selected[min(selected)]
    compatibility_path = dest / "run_manifest.json"
    shutil.copy2(compatibility_record.manifest_path, compatibility_path)
    copied.append(compatibility_path)
    compatibility_run_manifest = CompatibilityRunManifest(
        run_id=compatibility_record.run_id,
        path="run_manifest.json",
        sha256=compatibility_record.manifest_sha256,
    )
    package_status = publication_status_for(phases)
    git_commit_sha = _git_commit_sha(Path.cwd())
    publication_id = publication_id_for(
        project=project,
        package_version=__version__,
        git_commit_sha=git_commit_sha,
        phases=phases,
        package_status=package_status,
        compatibility_run_manifest=compatibility_run_manifest,
        superseded_publication_id=superseded_publication_id,
    )
    publication_manifest = PublicationManifest(
        manifest_format_version=PUBLICATION_MANIFEST_FORMAT_VERSION,
        project=project,
        package_version=__version__,
        git_commit_sha=git_commit_sha,
        published_at=publication_time,
        publication_id=publication_id,
        included_phase_ids=tuple(phase.phase_id for phase in phases),
        phases=phases,
        package_status=package_status,
        compatibility_run_manifest=compatibility_run_manifest,
        aggregation_notice=AGGREGATION_NOTICE,
        superseded_publication_id=superseded_publication_id,
    )
    publication_manifest_path = dest / "publication_manifest.json"
    publication_manifest_path.write_text(
        publication_manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    copied.append(publication_manifest_path)
    index_path = dest / "INDEX.md"
    index_path.write_bytes(render_publication_index(publication_manifest))
    copied.append(index_path)
    verify_publication_package(dest)
    return PublishResult(dest=dest, files=copied, skipped_working_copies=skipped)


def publish(
    output_root: Path,
    publish_root: Path,
    label: str,
    *,
    runs_root: Path | None = None,
    overwrite: bool = False,
    project_config_path: Path | None = None,
    superseded_publication_id: str | None = None,
    published_at: datetime | None = None,
    source_runs: Mapping[str, str] | None = None,
    run_id: str | None = None,
) -> PublishResult:
    """Atomically assemble and install one verified publication package.

    Repeating an exact-run publication with the same label and identity returns the already
    verified package. A changed identity still fails unless explicit overwrite is requested.
    """

    _require_safe_component(label, "publish label")
    root = _require_root(Path(publish_root), "publication root", create=True)
    checked_output_root = _require_root(Path(output_root), "output root")
    if runs_root is None:
        raise PublishError("runs_root is required to bind published phases to source runs")
    checked_runs_root = _require_root(Path(runs_root), "runs root")
    _reject_overlapping_roots(
        ("output root", checked_output_root),
        ("runs root", checked_runs_root),
        ("publication root", root),
    )
    final = root / f"Buduunkhad_Deliverables_{label}"
    if final.is_symlink() or has_symlink_component(final):
        raise PublishError(f"publication destination must not use a symlink: {final}")
    if final.exists() and any(final.iterdir()) and not overwrite:
        if run_id is not None and runs_root is not None:
            existing = verify_publication_package(final)
            source_manifest = Path(runs_root) / run_id / "run_manifest.json"
            config_path = Path(project_config_path or "config/project.yaml")
            current_source_sha256 = _sha256(source_manifest) if source_manifest.is_file() else ""
            current_config_sha256 = _sha256(config_path) if config_path.is_file() else ""
            if (
                existing.phases
                and all(phase.source_run_id == run_id for phase in existing.phases)
                and all(
                    phase.source_run_manifest_sha256 == current_source_sha256
                    for phase in existing.phases
                )
                and existing.project.configuration_sha256 == current_config_sha256
                and existing.package_version == __version__
                and existing.git_commit_sha == _git_commit_sha(Path.cwd())
                and existing.superseded_publication_id == superseded_publication_id
            ):
                files = sorted(path for path in final.rglob("*") if path.is_file())
                return PublishResult(dest=final, files=files)
        raise PublishError(
            f"Publish destination already exists and is not empty: {final}. "
            "Choose a new --label or remove that folder first."
        )

    transaction_root = root / f".p-{uuid.uuid4().hex[:8]}"
    backup = root / f".b-{uuid.uuid4().hex[:8]}"
    transaction_root.mkdir()
    staged_result: PublishResult | None = None
    installed = False
    moved_existing = False
    try:
        staged_result = _assemble_publication(
            output_root,
            transaction_root,
            label,
            runs_root=runs_root,
            overwrite=False,
            project_config_path=project_config_path,
            superseded_publication_id=superseded_publication_id,
            published_at=published_at,
            source_runs=source_runs,
            run_id=run_id,
        )
        verify_publication_package(staged_result.dest)
        if final.exists():
            if any(entry.is_symlink() for entry in final.rglob("*")):
                raise PublishError("existing publication destination contains a symlink")
            os.replace(final, backup)
            moved_existing = True
        try:
            os.replace(staged_result.dest, final)
            installed = True
        except Exception:
            if moved_existing and backup.exists() and not final.exists():
                os.replace(backup, final)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        remapped = [final / path.relative_to(staged_result.dest) for path in staged_result.files]
        verify_publication_package(final)
        return PublishResult(
            dest=final,
            files=remapped,
            skipped_working_copies=staged_result.skipped_working_copies,
        )
    finally:
        if transaction_root.exists():
            shutil.rmtree(transaction_root)
        if backup.exists() and installed:
            shutil.rmtree(backup)


def load_publication_manifest(package_root: Path) -> PublicationManifest:
    root = _require_root(Path(package_root), "publication package")
    path = _require_package_file(root, "publication_manifest.json", "publication manifest")
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
        return PublicationManifest.model_validate(data)
    except (OSError, UnicodeError, ValueError, ValidationError) as exc:
        raise PublishError(f"publication manifest is unreadable or invalid: {path}") from exc


def _package_file_claims(manifest: PublicationManifest) -> tuple[str, ...]:
    """Validate physical package-file claim multiplicity before creating an allowlist."""

    claims: dict[str, str] = {}

    def claim(path: str, owner: str) -> None:
        previous = claims.get(path)
        if previous is not None:
            raise PublishError(
                f"publication package path has conflicting claims: {path} ({previous}; {owner})"
            )
        claims[path] = owner

    claim("publication_manifest.json", "publication manifest")
    claim("INDEX.md", "publication index")
    claim(manifest.compatibility_run_manifest.path, "compatibility run manifest")

    source_manifest_identities: dict[str, tuple[str, str]] = {}
    for phase in manifest.phases:
        source_identity = (phase.source_run_id, phase.source_run_manifest_sha256)
        previous_identity = source_manifest_identities.get(phase.source_run_manifest_path)
        if previous_identity is None:
            source_manifest_identities[phase.source_run_manifest_path] = source_identity
            claim(phase.source_run_manifest_path, f"source run {phase.source_run_id}")
        elif previous_identity != source_identity:
            raise PublishError(
                "copied source run manifest path has conflicting identities: "
                f"{phase.source_run_manifest_path}"
            )
        for output in phase.outputs:
            claim(output.path, f"Phase {phase.phase_id} output")
    return tuple(claims)


def _source_phase_execution_provenance(
    source_data: dict[str, object],
    source_phase: dict[str, object],
    phase_id: str,
) -> tuple[ExecutionMode, tuple[str, ...]]:
    """Resolve and validate execution-purpose provenance from a copied run manifest."""

    if source_data.get("manifest_format_version") != "2.2.0":
        forbidden = {"execution_policy", "authorizations", "used_authorization_ids"}
        if forbidden & set(source_data) or {
            "execution_mode",
            "authorization_ids",
        } & set(source_phase):
            raise PublishError("legacy source run cannot claim execution-policy authorization")
        return legacy_execution_mode(phase_id), ()
    try:
        policy = ExecutionPolicyBinding.model_validate(source_data.get("execution_policy"))
        raw_authorizations = source_data.get("authorizations")
        if not isinstance(raw_authorizations, list):
            raise ValueError("authorization inventory is not a list")
        parsed = tuple(ExecutionAuthorization.model_validate(value) for value in raw_authorizations)
        mode = ExecutionMode(source_phase.get("execution_mode"))
    except (TypeError, ValidationError, ValueError) as exc:
        raise PublishError("source run execution-policy provenance is invalid") from exc
    policy_modes = {item.phase_id: item.execution_mode for item in policy.phase_modes}
    selected = source_data.get("selected_phases")
    if not isinstance(selected, list) or tuple(policy_modes) != tuple(selected):
        raise PublishError("source run execution-policy phase selection is inconsistent")
    try:
        validate_execution_policy_binding(
            policy,
            cast(list[str], selected),
            dry_run=False,
        )
    except RuntimeError as exc:
        raise PublishError("source run execution-policy binding is unauthorized") from exc
    if policy_modes.get(phase_id) is not mode:
        raise PublishError(f"source run execution mode mismatch for Phase {phase_id}")
    authorization_map = {item.authorization_id: item for item in parsed}
    raw_used = source_data.get("used_authorization_ids")
    raw_phase_ids = source_phase.get("authorization_ids")
    if (
        len(authorization_map) != len(parsed)
        or not isinstance(raw_used, list)
        or not all(isinstance(item, str) for item in raw_used)
        or len(set(raw_used)) != len(raw_used)
        or set(raw_used) != set(authorization_map)
        or not isinstance(raw_phase_ids, list)
        or not all(isinstance(item, str) for item in raw_phase_ids)
    ):
        raise PublishError("source run authorization inventory is inconsistent")
    authorization_ids = tuple(cast(list[str], raw_phase_ids))
    if (
        tuple(sorted(set(authorization_ids))) != authorization_ids
        or not set(authorization_ids) <= set(raw_used)
        or any(
            phase_id not in authorization_map[identity].scope_phase_ids
            for identity in authorization_ids
        )
    ):
        raise PublishError(f"source run authorization mismatch for Phase {phase_id}")
    return mode, authorization_ids


def verify_publication_package(package_root: Path) -> PublicationManifest:
    """Verify source provenance, published bytes, deterministic metadata, and package contents."""

    package_root = _require_root(Path(package_root), "publication package")
    manifest = load_publication_manifest(package_root)
    allowed_files = set(_package_file_claims(manifest))
    for phase in manifest.phases:
        source_manifest = _require_package_file(
            package_root, phase.source_run_manifest_path, "copied source run manifest"
        )
        if _sha256(source_manifest) != phase.source_run_manifest_sha256:
            raise PublishError(
                f"source run manifest is missing or changed: {phase.source_run_manifest_path}"
            )
        source_data = _load_json_object(source_manifest)
        if source_data.get("run_id") != phase.source_run_id:
            raise PublishError(f"source run identity mismatch for Phase {phase.phase_id}")
        if source_data.get("dry_run") is not False:
            raise PublishError(f"source run is not a completed real run for Phase {phase.phase_id}")
        if (
            source_data.get("started_at") != phase.source_started_at
            or source_data.get("finished_at") != phase.source_finished_at
        ):
            raise PublishError(f"source run timestamps mismatch for Phase {phase.phase_id}")
        source_phases = source_data.get("phases")
        if not isinstance(source_phases, list):
            raise PublishError(f"source run has no phase records for Phase {phase.phase_id}")
        matching = [
            item
            for item in source_phases
            if isinstance(item, dict) and item.get("phase_id") == phase.phase_id
        ]
        if len(matching) != 1:
            raise PublishError(f"source run phase identity is ambiguous for Phase {phase.phase_id}")
        source_phase = cast(dict[str, object], matching[0])
        source_execution_mode, source_authorization_ids = _source_phase_execution_provenance(
            source_data, source_phase, phase.phase_id
        )
        if (
            source_execution_mode is not phase.execution_mode
            or source_authorization_ids != phase.authorization_ids
        ):
            raise PublishError(
                f"source run execution-policy provenance mismatch for Phase {phase.phase_id}"
            )
        source_gate = source_phase.get("gate")
        if (
            source_phase.get("status") != phase.execution_status
            or not isinstance(source_gate, dict)
            or type(source_gate.get("provisional")) is not bool
            or type(source_phase.get("qaqc_pending")) is not bool
            or source_gate.get("status") != phase.gate_state
            or (source_gate.get("provisional") is True) != phase.gate_provisional
            or (source_phase.get("qaqc_pending") is True) != phase.human_review_or_qaqc_pending
            or source_phase.get("pending_human_review_or_qaqc_count")
            != phase.pending_human_review_or_qaqc_count
        ):
            raise PublishError(f"source run gate provenance mismatch for Phase {phase.phase_id}")
        has_artifact_inventory = "output_artifacts" in source_phase
        artifact_values = source_phase.get("output_artifacts")
        source_output_map = {output.source_path: output for output in phase.outputs}
        output_values = source_phase.get("outputs")
        if not isinstance(output_values, list):
            raise PublishError(f"source outputs are invalid for Phase {phase.phase_id}")
        recorded_paths = _recorded_publishable_paths(
            output_values,
            set(source_output_map),
            phase.phase_id,
        )
        if not has_artifact_inventory:
            source_binding_mode = "LEGACY_PATH_ONLY"
            if not recorded_paths <= set(source_output_map) or any(
                path not in recorded_paths and not _is_runner_qaqc_relative(path, phase.phase_id)
                for path in source_output_map
            ):
                raise PublishError(f"legacy source paths mismatch for Phase {phase.phase_id}")
        else:
            source_binding_mode = "SHA256_BOUND"
            if not isinstance(artifact_values, list):
                raise PublishError(
                    f"source artifact inventory is invalid for Phase {phase.phase_id}"
                )
            try:
                source_artifacts = tuple(
                    RunOutputArtifact.model_validate(value) for value in artifact_values
                )
            except ValidationError as exc:
                raise PublishError(
                    f"source artifact inventory is invalid for Phase {phase.phase_id}"
                ) from exc
            artifact_map = {artifact.path: artifact for artifact in source_artifacts}
            if (
                len(artifact_map) != len(source_artifacts)
                or set(artifact_map) != set(source_output_map)
                or recorded_paths != set(artifact_map)
            ):
                raise PublishError(f"source artifact paths mismatch for Phase {phase.phase_id}")
            for path, artifact in artifact_map.items():
                published = source_output_map[path]
                if (
                    published.source_sha256 != artifact.sha256
                    or published.source_size_bytes != artifact.size_bytes
                ):
                    raise PublishError(
                        f"source artifact identity mismatch for Phase {phase.phase_id}: {path}"
                    )
        if source_binding_mode != phase.source_binding_mode:
            raise PublishError(f"source binding mode mismatch for Phase {phase.phase_id}")
        for output in phase.outputs:
            output_file = _require_package_file(package_root, output.path, "published output")
            if (
                _sha256(output_file) != output.sha256
                or output_file.stat().st_size != output.size_bytes
            ):
                raise PublishError(f"published output is missing or changed: {output.path}")

    compatibility = manifest.compatibility_run_manifest
    compatibility_path = _require_package_file(
        package_root, compatibility.path, "compatibility run manifest"
    )
    if _sha256(compatibility_path) != compatibility.sha256:
        raise PublishError("compatibility root run manifest is missing or changed")
    compatibility_data = _load_json_object(compatibility_path)
    if compatibility_data.get("run_id") != compatibility.run_id:
        raise PublishError("compatibility root run identity mismatch")
    matching_source_paths = [
        phase.source_run_manifest_path
        for phase in manifest.phases
        if phase.source_run_id == compatibility.run_id
        and phase.source_run_manifest_sha256 == compatibility.sha256
    ]
    if not matching_source_paths or not any(
        _require_package_file(package_root, path, "copied source run manifest").read_bytes()
        == compatibility_path.read_bytes()
        for path in matching_source_paths
    ):
        raise PublishError("compatibility root manifest is not one selected source run")

    index = _require_package_file(package_root, "INDEX.md", "publication index")
    if index.read_bytes() != render_publication_index(manifest):
        raise PublishError("publication INDEX.md is missing or changed")

    for entry in package_root.rglob("*"):
        if entry.is_symlink():
            raise PublishError(f"publication package contains a symlink: {entry}")
        if entry.is_file():
            relative = entry.relative_to(package_root).as_posix()
            if relative not in allowed_files:
                raise PublishError(f"publication package contains an unexpected file: {relative}")
        elif not entry.is_dir():
            raise PublishError(f"publication package contains an unsupported entry: {entry}")
    return manifest


def _publish_qgz_flat(src: Path, target: Path) -> None:
    """Copy a QGIS project, rewriting layer datasources for the flat publish layout.

    Phase outputs reference their GPKGs relative to the .qgz inside the phase's
    subfolder tree (e.g. ``../05_KMZ_KML_to_GPKG/x.gpkg|layername=y``); publishing
    flattens every deliverable of a phase into one ``PhaseNN/`` folder, so each
    datasource is rewritten to ``./<basename>`` — the published project then opens
    with its layers resolving beside it.
    """
    import zipfile
    from xml.etree import ElementTree as ET

    def flatten(source: str) -> str:
        path_part, sep, layer_part = source.partition("|")
        return f"./{Path(path_part).name}{sep}{layer_part}"

    with zipfile.ZipFile(src) as zf:
        qgs_name = next(n for n in zf.namelist() if n.endswith(".qgs"))
        root = ET.fromstring(zf.read(qgs_name))
    for node in root.iter("layer-tree-layer"):
        if node.get("source"):
            node.set("source", flatten(node.get("source", "")))
    for ds in root.iter("datasource"):
        if ds.text:
            ds.text = flatten(ds.text)
    ET.indent(root)
    payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    info = zipfile.ZipInfo(qgs_name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr(info, payload)


def render_publication_index(manifest: PublicationManifest) -> bytes:
    """Render the human-readable index solely from the validated machine contract."""

    lines = [
        f"# Deliverable publication package {manifest.publication_id}",
        "",
        "Published deliverables (GIS layers, COG rasters, registers, logs, reports). Raw working",
        "copies are excluded — those are duplicates of the read-only Drive archive.",
        "",
        f"**Package status:** {manifest.package_status}",
        "",
        "Machine-readable package provenance and output hashes are recorded in",
        "`publication_manifest.json`.",
        "",
        f"The root `run_manifest.json` is a compatibility copy of selected source run "
        f"`{manifest.compatibility_run_manifest.run_id}`. It is not package-wide provenance,",
        "especially when this package aggregates multiple source runs.",
        "",
        manifest.aggregation_notice,
        "",
    ]
    legacy_phases = [
        phase.phase_id
        for phase in manifest.phases
        if phase.source_binding_mode == "LEGACY_PATH_ONLY"
    ]
    if legacy_phases:
        lines.extend(
            [
                "**Integrity limitation:** This package includes legacy path-only source binding",
                f"for Phase(s) {', '.join(legacy_phases)}. Those source-run manifests did not seal",
                "artifact bytes, so the package cannot be APPROVED and no source-run byte identity",
                "is claimed for those phases.",
                "",
            ]
        )
    parts = []
    for phase in manifest.phases:
        tag = (
            f"{phase.phase_id}={phase.gate_state} from run {phase.source_run_id} "
            f"[{phase.source_binding_mode}]"
        )
        if manifest.manifest_format_version != "1.1.0":
            tag += f" [mode={phase.execution_mode.value}]"
        if phase.gate_provisional:
            tag += " (provisional)"
        if phase.human_review_or_qaqc_pending:
            tag += " (human review / QA/QC pending)"
        parts.append(tag)
    lines.append(f"**Source phase gates:** {', '.join(parts)}")
    if manifest.manifest_format_version != "1.1.0":
        lines.extend(
            [
                "",
                "Only `authoritative` source phases can support APPROVED package status;",
                "scaffold, support-evidence, and legacy-comparator outputs remain provisional.",
            ]
        )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- `publication_manifest.json` (machine-readable package contract)")
    lines.append("- `run_manifest.json` (recorded compatibility source manifest)")
    for source_path in sorted({phase.source_run_manifest_path for phase in manifest.phases}):
        lines.append(f"- `{source_path}` (selected source-run manifest)")
    for phase in manifest.phases:
        for output in phase.outputs:
            transform = (
                f", transformation `{output.transformation_id}`"
                if output.transformation_id is not None
                else ""
            )
            lines.append(
                f"- `{output.path}` (SHA-256 `{output.sha256}`, {output.size_bytes} bytes{transform})"
            )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


# --------------------------------------------------------------------------- #
# raw-archive backup (a frozen, checksum-verified copy of the complete raw set)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RawBackupResult:
    dest: Path
    files: int
    verified: int
    missing: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str:
    return sha256_file(path)


def backup_raw_archive(
    raw_root: Path,
    checksum_register: Path,
    publish_root: Path,
    label: str,
    *,
    integrity_files: Sequence[Path] = (),
    overwrite: bool = False,
) -> RawBackupResult:
    """Copy the *complete* raw archive to a frozen, checksum-verified backup under ``publish_root``.

    Creates ``publish_root/Raw_Archive_Backup_<label>/`` with the full raw tree under
    ``0_Raw_Data/``, the Phase-00 checksum register + any ``integrity_files`` at the root, and a
    README. Every row of the checksum register is re-hashed against the copied file; a missing or
    mismatched file raises :class:`PublishError` (the README is still written for diagnosis).

    Raw is read-only — this only *reads* ``raw_root``. Unlike :func:`publish` (which excludes raw
    working copies), this deliberately backs up the raw data so teammates have an immutable,
    verifiable copy separate from the working source. Intended one-time / on-change, not per run.
    """
    raw_root = Path(raw_root)
    publish_root = Path(publish_root)
    checksum_register = Path(checksum_register)
    if not raw_root.exists():
        raise PublishError(f"raw_root does not exist: {raw_root}")
    if not checksum_register.exists():
        raise PublishError(f"checksum register not found: {checksum_register} (run Phase 00 first)")
    dest = publish_root / f"Raw_Archive_Backup_{label}"
    if dest.exists() and any(dest.iterdir()) and not overwrite:
        raise PublishError(
            f"{dest} already exists and is non-empty; pass overwrite=True or use a new label"
        )
    data_dir = dest / "0_Raw_Data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # copy the complete raw tree (skip Windows desktop.ini folder-config junk Drive re-creates)
    files = 0
    for f in sorted(raw_root.rglob("*")):
        if not f.is_file() or f.name.lower() == "desktop.ini":
            continue
        target = data_dir / f.relative_to(raw_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        files += 1

    # copy the integrity evidence (register + inventory/log/readme) to the backup root
    shutil.copy2(checksum_register, dest / checksum_register.name)
    for extra in integrity_files:
        extra = Path(extra)
        if extra.exists():
            shutil.copy2(extra, dest / extra.name)

    # verify every register row against the copied file
    verified = 0
    missing: list[str] = []
    mismatched: list[str] = []
    with open(checksum_register, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rel = row["relative_path"].replace("/", os.sep)
            p = data_dir / rel
            if not p.exists():
                missing.append(row["relative_path"])
            elif _sha256(p) == row["sha256"]:
                verified += 1
            else:
                mismatched.append(row["relative_path"])

    _write_raw_backup_readme(dest, label, files, verified, checksum_register.name)
    if missing or mismatched:
        raise PublishError(
            f"raw backup verification failed: {len(missing)} missing, "
            f"{len(mismatched)} mismatched vs the checksum register (dest={dest})"
        )
    return RawBackupResult(
        dest=dest, files=files, verified=verified, missing=missing, mismatched=mismatched
    )


def _write_raw_backup_readme(
    dest: Path, label: str, files: int, verified: int, register_name: str
) -> Path:
    lines = [
        f"# Raw Archive Backup — {label}",
        "",
        "**Frozen, checksum-verified backup of the complete raw exploration data archive.**",
        "Do not edit anything in this folder — it exists so the working source can be protected",
        "and, if it is ever altered, restored/verified against this snapshot.",
        "",
        "## Contents",
        f"- `0_Raw_Data/` — complete raw archive ({files} files, full folder structure).",
        f"- `{register_name}` — SHA-256 integrity baseline (the source of truth for verification).",
        "- Phase-00 inventory / integrity log / source readme (where provided).",
        "",
        "## Verification",
        f"All {verified} checksum-register rows were re-hashed against the copied files and "
        "matched byte-for-byte at backup time. To re-verify a file, compare its SHA-256 against "
        f"the `sha256` column in `{register_name}` (`Get-FileHash -Algorithm SHA256` / `sha256sum`).",
        "",
        "## Notes",
        "- One-time, versioned backup — raw data does not change, so it is not re-uploaded per run.",
        "  If the raw archive is ever legitimately updated, create a new label rather than overwriting.",
        "- Raw inputs are read-only source evidence; remote-sensing / pXRF / drone data are *support*",
        "  evidence, never ore proof.",
    ]
    readme = dest / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
    return readme
