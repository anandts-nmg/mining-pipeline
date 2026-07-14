"""Reusable tracked-artifact and secret policy for repository and CI checks."""

from __future__ import annotations

import codecs
import hashlib
import re
import subprocess
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path, PurePosixPath
from types import MappingProxyType

FORBIDDEN_DIRECTORIES = frozenset(
    {
        ".codex-local",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "ai_jobs",
        "ai_responses",
        "artifacts",
        "build",
        "cache",
        "caches",
        "control",
        "data",
        "dist",
        "job_stores",
        "log",
        "logs",
        "outputs",
        "private_evaluations",
        "qgis_profiles",
        "qgis_runtime",
        "rendered_tiles",
        "response_stores",
        "raw",
        "runs",
        "runtime",
    }
)

FORBIDDEN_SUFFIXES = frozenset(
    {
        ".accdb",
        ".aux.xml",
        ".asc",
        ".avif",
        ".bmp",
        ".bpw",
        ".cer",
        ".cpg",
        ".crt",
        ".db",
        ".dbf",
        ".der",
        ".doc",
        ".docm",
        ".docx",
        ".dng",
        ".duckdb",
        ".ecw",
        ".e57",
        ".eph",
        ".exr",
        ".feather",
        ".fgb",
        ".gfw",
        ".gif",
        ".gpkg",
        ".geojson",
        ".gml",
        ".grd",
        ".h5",
        ".hdr",
        ".hdf",
        ".hdf5",
        ".heic",
        ".img",
        ".j2k",
        ".jgw",
        ".jfif",
        ".jks",
        ".jpe",
        ".jp2",
        ".jpeg",
        ".jpg",
        ".kdbx",
        ".keystore",
        ".key",
        ".kml",
        ".kmz",
        ".las",
        ".laz",
        ".mdb",
        ".mif",
        ".mid",
        ".nc",
        ".nitf",
        ".ntf",
        ".ods",
        ".odt",
        ".ovr",
        ".p12",
        ".p8",
        ".parquet",
        ".pcd",
        ".pem",
        ".pfx",
        ".pgp",
        ".pgw",
        ".pkcs8",
        ".ply",
        ".png",
        ".ppk",
        ".ppt",
        ".pptm",
        ".pptx",
        ".prj",
        ".psd",
        ".pts",
        ".ptx",
        ".qgs",
        ".qgz",
        ".qlr",
        ".qml",
        ".rpc",
        ".raw",
        ".rrd",
        ".sbn",
        ".sbx",
        ".shp",
        ".shp.xml",
        ".shx",
        ".sid",
        ".sqlite",
        ".sqlite3",
        ".tfw",
        ".tif",
        ".tiff",
        ".tab",
        ".vrt",
        ".wld",
        ".webp",
        ".xls",
        ".xlsm",
        ".xlsx",
        ".xyz",
    }
)

# Exceptions must identify one file and its exact bytes. PR 1 currently needs none.
APPROVED_SYNTHETIC_FIXTURES: Mapping[PurePosixPath, str] = MappingProxyType({})

SECRET_PATTERNS: Mapping[str, re.Pattern[str]] = MappingProxyType(
    {
        "OpenAI-style API key": re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b"),
        "GitHub token": re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"
        ),
        "Anthropic token": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
        "GitLab token": re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
        "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
        "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
        "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
        "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "private key": re.compile(
            r"-----BEGIN\s+(?:(?:RSA|EC|DSA|OPENSSH|ENCRYPTED)\s+)?PRIVATE KEY-----"
        ),
        "PGP private key": re.compile(r"-----BEGIN PGP " r"PRIVATE KEY BLOCK-----"),
        "PuTTY private key": re.compile(r"(?m)^PuTTY-User-Key-File-[0-9]+:"),
        "suspicious secret assignment": re.compile(
            r"(?im)(?:^|[\s;,{])"
            r"(?:export\s+|\$env\s*:\s*)?"
            r"[\"']?(?:[A-Za-z0-9_.-]+[.:])?"
            r"(?:OPENAI_API_KEY|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|CLIENT_SECRET|"
            r"API[_-]?KEY|ACCESS[_-]?TOKEN|AUTH[_-]?TOKEN|BEARER[_-]?TOKEN|"
            r"REFRESH[_-]?TOKEN|TOKEN|PASSWORD|PASSWD|SECRET(?:[_-]?KEY)?)"
            r"[\"']?\s*[:=]\s*"
            r"(?:"
            r"\"(?!placeholder\"|example\"|dummy\"|redacted\"|change[_-]?me\")"
            r"[^\"\r\n]{8,}\"|"
            r"'(?!placeholder'|example'|dummy'|redacted'|change[_-]?me')"
            r"[^'\r\n]{8,}'|"
            r"(?!placeholder\b|example\b|dummy\b|redacted\b|change[_-]?me\b|re\.compile\b)"
            r"[^\s,;#}{]{8,}"
            r")"
        ),
    }
)

_SCAN_CHUNK_BYTES = 64 * 1024
_PATTERN_OVERLAP = 16 * 1024


def tracked_files(repository_root: Path) -> tuple[PurePosixPath, ...]:
    """Return every Git-tracked path without extension or size filtering."""
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    try:
        return tuple(
            PurePosixPath(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item
        )
    except UnicodeError as exc:
        raise ValueError("tracked path is not valid UTF-8") from exc


def artifact_violations(
    repository_root: Path,
    paths: Iterable[PurePosixPath],
) -> tuple[str, ...]:
    violations: list[str] = []
    for path in paths:
        if is_exact_approved_fixture(repository_root, path):
            continue
        parts = {part.casefold() for part in path.parts}
        name = path.name.casefold()
        if parts & FORBIDDEN_DIRECTORIES:
            violations.append(str(path))
            continue
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            violations.append(str(path))
            continue
        if (
            any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)
            or name.endswith(".copc.laz")
            or name.startswith("credentials")
            or name.startswith("service-account")
            or name.startswith("private-evaluation")
            or name.startswith("secrets.")
            or name.startswith("ai-response")
            or name.startswith("provider-response")
            or name.startswith("response-store")
            or name.startswith("job-store")
            or name.startswith("job-database")
            or name
            in {
                ".netrc",
                ".npmrc",
                ".pypirc",
                "id_dsa",
                "id_ecdsa",
                "id_ed25519",
                "id_rsa",
            }
        ):
            violations.append(str(path))
    return tuple(violations)


def is_exact_approved_fixture(repository_root: Path, path: PurePosixPath) -> bool:
    expected = APPROVED_SYNTHETIC_FIXTURES.get(path)
    if expected is None:
        return False
    candidate = repository_root / Path(path.as_posix())
    return candidate.is_file() and _sha256_file(candidate) == expected


def secret_findings(path: Path) -> tuple[str, ...]:
    """Stream one non-binary text file, including BOM-marked UTF-16 text."""
    findings: set[str] = set()
    overlap = ""
    try:
        for chunk in text_chunks(path):
            combined = overlap + chunk
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(combined):
                    findings.add(label)
            overlap = combined[-_PATTERN_OVERLAP:]
    except UnicodeError:
        findings.add("unscannable text encoding")
    return tuple(sorted(findings))


def text_chunks(path: Path) -> Iterator[str]:
    """Yield decoded text chunks, or no chunks for a detected binary file."""
    with path.open("rb") as stream:
        first = stream.read(_SCAN_CHUNK_BYTES)
        encoding = _detect_encoding(first)
        if encoding is None:
            return
        decoder = codecs.getincrementaldecoder(encoding)(errors="strict")
        if first:
            yield decoder.decode(first)
        for raw in iter(lambda: stream.read(_SCAN_CHUNK_BYTES), b""):
            yield decoder.decode(raw)
        tail = decoder.decode(b"", final=True)
        if tail:
            yield tail


def repository_policy_violations(repository_root: Path) -> tuple[str, ...]:
    paths = tracked_files(repository_root)
    violations = list(artifact_violations(repository_root, paths))
    for relative in paths:
        candidate = repository_root / Path(relative.as_posix())
        if not candidate.is_file():
            continue
        for finding in secret_findings(candidate):
            violations.append(f"{relative}: {finding}")
    return tuple(violations)


def _detect_encoding(sample: bytes) -> str | None:
    if sample.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if sample.startswith(codecs.BOM_UTF16_LE):
        return "utf-16"
    if sample.startswith(codecs.BOM_UTF16_BE):
        return "utf-16"
    if not sample:
        return "utf-8"
    if b"\0" in sample:
        return None
    controls = sum(byte < 9 or (13 < byte < 32) for byte in sample)
    if controls / len(sample) > 0.20:
        return None
    return "utf-8"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
