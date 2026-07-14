from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def _wait_for(path: Path, *, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.05)
    raise AssertionError(f"timed out waiting for {path.name}")


def test_two_concurrent_pytest_sessions_keep_owned_temporary_roots(
    project,
    tmp_path: Path,
) -> None:
    probe_id = os.environ.get("BUDUUNKHAD_CONCURRENT_PROBE_ID")
    coordination_value = os.environ.get("BUDUUNKHAD_CONCURRENT_PROBE_DIR")
    if probe_id is not None and coordination_value is not None:
        _config, _register, work = project
        coordination = Path(coordination_value)
        owner = work / f"owner-{probe_id}.txt"
        owner.write_text(probe_id, encoding="utf-8")
        (coordination / f"ready-{probe_id}").write_text(str(work), encoding="utf-8")
        _wait_for(coordination / "ready-a")
        _wait_for(coordination / "ready-b")
        assert owner.read_text(encoding="utf-8") == probe_id
        if probe_id == "b":
            return
        _wait_for(coordination / "b-terminated")
        assert owner.read_text(encoding="utf-8") == "a"
        owner.write_text("a-after-b-teardown", encoding="utf-8")
        assert owner.read_text(encoding="utf-8") == "a-after-b-teardown"
        (coordination / "a-survived").write_text(str(owner), encoding="utf-8")
        _wait_for(coordination / "release-a")
        return

    repository = Path(__file__).resolve().parents[1]
    test_file = Path(__file__).resolve()
    coordination = tmp_path / "coordination"
    coordination.mkdir()
    base_env = os.environ.copy()
    base_env["BUDUUNKHAD_CONCURRENT_PROBE_DIR"] = str(coordination)
    base_env["PYTHONPATH"] = str(repository / "src")

    def start(probe: str) -> subprocess.Popen[str]:
        env = base_env | {"BUDUUNKHAD_CONCURRENT_PROBE_ID": probe}
        return subprocess.Popen(
            [sys.executable, "-m", "pytest", "-q", str(test_file)],
            cwd=repository,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    first = start("a")
    _wait_for(coordination / "ready-a")
    second = start("b")
    _wait_for(coordination / "ready-b")
    second_stdout, second_stderr = second.communicate(timeout=30)
    assert second.returncode == 0, second_stdout + second_stderr
    (coordination / "b-terminated").write_text("reaped", encoding="utf-8")
    _wait_for(coordination / "a-survived")
    owner = Path((coordination / "a-survived").read_text(encoding="utf-8"))
    assert owner.read_text(encoding="utf-8") == "a-after-b-teardown"
    (coordination / "release-a").write_text("release", encoding="utf-8")
    first_stdout, first_stderr = first.communicate(timeout=30)
    assert first.returncode == 0, first_stdout + first_stderr
