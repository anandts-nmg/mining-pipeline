"""Isolated adapter boundary for optional QGIS Processing execution."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class QgisProcessError(RuntimeError):
    """A requested QGIS Processing operation could not be executed safely."""


SUPPORTED_ALGORITHMS = frozenset(
    {
        "native:checkvalidity",
        "native:fixgeometries",
        "native:reprojectlayer",
        "native:clip",
        "native:createspatialindex",
        "native:package",
    }
)


class QgisProcessAdapter(Protocol):
    def run(self, algorithm: str, parameters: Mapping[str, str]) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class SubprocessQgisProcessAdapter:
    """Optional local adapter; ordinary imports and tests never require QGIS."""

    executable: Path = Path("qgis_process")
    timeout_seconds: float = 600.0

    def run(self, algorithm: str, parameters: Mapping[str, str]) -> Mapping[str, object]:
        if algorithm not in SUPPORTED_ALGORITHMS:
            raise QgisProcessError(f"unsupported QGIS Processing algorithm: {algorithm}")
        command: list[str] = [str(self.executable), "run", algorithm, "--json"]
        command.extend(_arguments(parameters))
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise QgisProcessError("qgis_process is unavailable or timed out") from exc
        if completed.returncode != 0:
            raise QgisProcessError(f"qgis_process failed with exit status {completed.returncode}")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise QgisProcessError("qgis_process returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise QgisProcessError("qgis_process returned an unsupported result")
        return payload


def _arguments(parameters: Mapping[str, str]) -> Sequence[str]:
    arguments: list[str] = []
    for name in sorted(parameters):
        if not name or name.startswith("-"):
            raise QgisProcessError("invalid QGIS Processing parameter name")
        arguments.append(f"--{name}={parameters[name]}")
    return arguments
