from __future__ import annotations

import _socket
import http.client
import os
import socket
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest


@pytest.mark.parametrize(
    ("function", "args"),
    [
        (socket.getaddrinfo, ("example.invalid", 443)),
        (socket.gethostbyname, ("example.invalid",)),
        (socket.gethostbyname_ex, ("example.invalid",)),
        (socket.gethostbyaddr, ("192.0.2.1",)),
        (socket.getnameinfo, (("192.0.2.1", 443), 0)),
        (socket.getfqdn, ("example.invalid",)),
    ],
)
def test_all_dns_and_name_resolution_entry_points_are_denied(function, args) -> None:
    with pytest.raises(RuntimeError, match="network access is disabled"):
        function(*args)


def test_socket_construction_and_connection_helpers_are_denied() -> None:
    checks: tuple[tuple[Callable[..., object], tuple[object, ...]], ...] = (
        (socket.socket, ()),
        (socket.SocketType, ()),
        (socket.create_connection, (("192.0.2.1", 443),)),
        (socket.create_server, (("127.0.0.1", 0),)),
        (socket.socketpair, ()),
    )
    for function, args in checks:
        invoke = cast(Callable[..., object], function)
        with pytest.raises(RuntimeError, match="network access is disabled"):
            invoke(*args)


def test_native_socket_construction_pair_and_resolvers_are_denied() -> None:
    checks: list[tuple[Callable[..., object], tuple[object, ...]]] = [(_socket.socket, ())]
    socket_type_name = "Socket" + "Type"
    if hasattr(_socket, socket_type_name):
        checks.append((cast(Callable[..., object], getattr(_socket, socket_type_name)), ()))
    socketpair_name = "socket" + "pair"
    if hasattr(_socket, socketpair_name):
        checks.append((cast(Callable[..., object], getattr(_socket, socketpair_name)), ()))
    for name, args in (
        ("getaddrinfo", ("example.invalid", 443)),
        ("gethostbyname", ("example.invalid",)),
        ("gethostbyname_ex", ("example.invalid",)),
        ("gethostbyaddr", ("192.0.2.1",)),
        ("getnameinfo", (("192.0.2.1", 443), 0)),
    ):
        if hasattr(_socket, name):
            checks.append((cast(Callable[..., object], getattr(_socket, name)), args))
    for function, args in checks:
        with pytest.raises(RuntimeError, match="network access is disabled"):
            function(*args)


def test_common_http_entry_points_are_denied() -> None:
    with pytest.raises(RuntimeError, match="network access is disabled"):
        urllib.request.urlopen("https://example.invalid", timeout=0.01)
    with pytest.raises(RuntimeError, match="network access is disabled"):
        http.client.HTTPConnection("example.invalid").request("GET", "/")
    with pytest.raises(RuntimeError, match="network access is disabled"):
        http.client.HTTPSConnection("example.invalid").connect()


def test_sequential_pytest_sessions_cannot_leave_guard_disabled(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[1]
    probe = repository / "tests" / "network_guard_sequence_probe.py"
    env = os.environ.copy()
    env["BUDUUNKHAD_NETWORK_SEQUENCE_PROBE"] = "1"
    env["PYTHONPATH"] = str(repository / "src")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(probe)],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_embedded_pytest_main_does_not_leak_network_monkeypatch(monkeypatch) -> None:
    repository = Path(__file__).resolve().parents[1]
    probe = repository / "tests" / "network_guard_sequence_probe.py"
    monkeypatch.setenv("BUDUUNKHAD_NETWORK_SEQUENCE_PROBE", "1")
    exit_code = pytest.main(
        [
            "-q",
            str(probe),
            "-k",
            "test_guard_is_active_after_previous_test",
        ]
    )
    assert exit_code == pytest.ExitCode.OK
    with pytest.raises(RuntimeError, match="network access is disabled"):
        socket.getaddrinfo("example.invalid", 443)
    with pytest.raises(RuntimeError, match="network access is disabled"):
        _socket.socket()


@pytest.mark.skipif(
    os.environ.get("BUDUUNKHAD_PROCESS_NETWORK_ISOLATED") != "1",
    reason="exercised only inside the Linux CI network namespace",
)
def test_linux_process_isolation_blocks_subprocess_dns_and_connection() -> None:
    script = """
import socket

blocked = 0
try:
    socket.getaddrinfo('example.com', 443)
except OSError:
    blocked += 1
try:
    socket.create_connection(('1.1.1.1', 53), timeout=0.2)
except OSError:
    blocked += 1
raise SystemExit(0 if blocked == 2 else 1)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
