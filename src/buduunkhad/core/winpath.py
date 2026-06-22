"""Windows path-length helpers.

Some real input filenames are long (the longest is ~117 chars); combined with a
deep output root and the phase folder names, generated paths can approach the
Windows 260-char ``MAX_PATH`` limit, where GDAL/IO start failing cryptically.
These helpers let the pipeline detect the risk and fail (or warn) clearly.

Remedies, in order of convenience:
  1. Enable long paths once (admin):
       Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem' \\
         -Name LongPathsEnabled -Value 1 -Type DWord
  2. Keep ``paths.output_root`` shallow (e.g. ``C:\\bk\\outputs``).
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

#: Classic Windows path limit (260 includes the terminating NUL, so 259 usable).
WINDOWS_MAX_PATH = 260


def is_windows() -> bool:
    return sys.platform.startswith("win")


def long_paths_enabled() -> bool | None:
    """Whether Windows long-path support is enabled.

    Returns ``True``/``False`` on Windows (from the registry), or ``None`` when it
    cannot be determined. On non-Windows platforms there is no such limit, so this
    returns ``True``.
    """
    if not is_windows():
        return True
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem"
        )
        try:
            value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
        finally:
            winreg.CloseKey(key)
        return bool(value)
    except OSError:
        return None


def overlength_paths(
    paths: Iterable[Path | str], limit: int = WINDOWS_MAX_PATH
) -> list[tuple[str, int]]:
    """Return ``(path, length)`` for absolute paths that meet/exceed ``limit``.

    Length is measured on the resolved absolute path string, sorted longest first.
    """
    hits: list[tuple[str, int]] = []
    for p in paths:
        s = str(Path(p).resolve())
        if len(s) >= limit:
            hits.append((s, len(s)))
    hits.sort(key=lambda t: t[1], reverse=True)
    return hits


def extended_length_path(p: Path | str) -> str:
    """Return the ``\\\\?\\``-prefixed extended-length form of an absolute Windows path.

    This bypasses ``MAX_PATH`` per-call without any system change. No-op on
    non-Windows or for already-prefixed paths.
    """
    if not is_windows():
        return str(p)
    resolved = Path(p).resolve()
    s = str(resolved)
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):  # UNC path -> \\?\UNC\server\share
        return "\\\\?\\UNC\\" + s[2:]
    return "\\\\?\\" + s
