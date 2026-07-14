from __future__ import annotations

import _socket
import os
import socket

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("BUDUUNKHAD_NETWORK_SEQUENCE_PROBE") != "1",
    reason="run only by the network guard isolation test",
)


def test_attempted_guard_mutation_is_confined_to_one_test() -> None:
    socket.getaddrinfo = lambda *_args, **_kwargs: []  # type: ignore[assignment]
    _socket.socket = lambda *_args, **_kwargs: object()  # type: ignore[attr-defined]
    _socket.SocketType = lambda *_args, **_kwargs: object()  # type: ignore[attr-defined]
    assert socket.getaddrinfo("example.invalid", 443) == []
    assert _socket.socket() is not None
    assert _socket.SocketType() is not None  # type: ignore[attr-defined]


def test_guard_is_active_after_previous_test() -> None:
    with pytest.raises(RuntimeError, match="network access is disabled"):
        socket.getaddrinfo("example.invalid", 443)
    with pytest.raises(RuntimeError, match="network access is disabled"):
        _socket.socket()
    with pytest.raises(RuntimeError, match="network access is disabled"):
        _socket.SocketType()  # type: ignore[attr-defined]
