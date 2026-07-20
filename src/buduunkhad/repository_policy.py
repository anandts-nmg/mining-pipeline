"""Reusable tracked-artifact and secret policy for repository and CI checks."""

from __future__ import annotations

import codecs
import hashlib
import re
import subprocess
import zipfile
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

# Synthetic fixture exceptions must identify one file and its exact bytes.
APPROVED_SYNTHETIC_FIXTURES: Mapping[PurePosixPath, str] = MappingProxyType({})

# Reviewed methodology sources are the only approved production-document artifacts. Each
# exception binds one repository path to the exact source bytes reviewed on 2026-07-20.
APPROVED_METHODOLOGY_DOCUMENTS: Mapping[PurePosixPath, str] = MappingProxyType(
    {
        PurePosixPath(
            "docs/methodology/master/"
            "XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v9_25km_"
            "Clickable_TOC_PageNumbers.docx"
        ): "86ab7c8926aeccf032835c1b1ba9a00518740cdfaea2a1ad01313e4bfcb3b65e",
        PurePosixPath(
            "docs/methodology/master/"
            "XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v6_"
            "Phasewise_File_Processing_Output_Matrix.docx"
        ): "2b27b9035b24e2239caa8ce0b345969bf23f7d1d0beb69c3f6f4f2a0fe7cd996",
        PurePosixPath(
            "docs/methodology/phase_01/XV-023222_Buduunkhad_Phase1_Methodology.docx"
        ): "99bb2d59fc649701c9aa5656e40fc7c2a220ab6ccfe2a343c0a1831d40123349",
        PurePosixPath(
            "docs/methodology/phase_02/Phase_2_Remote_Sensing_Preprocessing_Guide_MN.docx"
        ): "77d194c1914b463486bda553e0303d865b0742e5847a81d4e9da85abea4590f2",
        PurePosixPath(
            "docs/methodology/phase_02/operator_guides/"
            "XV023222_Buduunkhad_Sentinel2_QGIS402_Detailed_Guide_v01.docx"
        ): "98ecf4defac3058f474d78ffa5ca2acda25e561688714bd045f27ebe66ff2fe2",
        PurePosixPath(
            "docs/methodology/phase_02/operator_guides/"
            "QGIS_4_0_2_Google_HighResolution_Basemap_Detailed_Guide.docx"
        ): "1c6380686574e2bc92558bcf6dc787d07454ec092de0ee47268a30ce633ebaaf",
        PurePosixPath(
            "docs/methodology/phase_02/operator_guides/"
            "XV023222_Buduunkhad_QGIS402_DEM_ALOS_PALSAR_ASTERGDEM_Detailed_Guide.docx"
        ): "84f809fef429bb0279bbd67f036fbaa0e03a70427a827f8139284f4190b5f081",
        PurePosixPath(
            "docs/methodology/phase_03/"
            "Phase_3_Geological_Metallogenic_and_CMCS_Synthesis_Guide_MN.docx"
        ): "deceebe736db6dcd70500204a5e30391b6992d7973633afb8abdc4016aff8b49",
        PurePosixPath(
            "docs/methodology/phase_04/"
            "Phase_4_Preliminary_Prospect_Delineation_and_Ranking_Guide_MN.docx"
        ): "b73044d954e625c7c3c65a6042e378bfdb479f58d13be6c4120912c092f4b003",
        PurePosixPath(
            "docs/methodology/phase_05/Phase_5_Drone_LiDAR_Photogrammetry_Detailed_Guide_MN.docx"
        ): "f1add3a2c229224454ff1624f70602f2592ad2240b23f45be3d5744c07700ade",
        PurePosixPath(
            "docs/methodology/phase_06/"
            "Phase_6_Recon_Mapping_and_pXRF_Field_Screening_Detailed_Guide_MN.docx"
        ): "71433eee7c1cdf972e0b7ab48bdc8ab0539068fd3e8d73502d55473d0fe7e40f",
        PurePosixPath(
            "docs/methodology/phase_07/"
            "Phase_7_Rock_Chip_Channel_Verification_Sampling_Guide_MN.docx"
        ): "95e040dbe1a4c1bb5d99ddced1d555e6aef632c844070b59b40143864eb071e1",
        PurePosixPath(
            "docs/methodology/phase_08/"
            "Phase_8_Orientation_Soil_StreamSediment_HeavyMineral_Check_Detailed_Guide_MN.docx"
        ): "d01817cfc34c3b4c117828551f9854d0d5978092337d9186364340f44023410a",
        PurePosixPath(
            "docs/methodology/phase_09/"
            "Phase_9_Systematic_Soil_Grid_Laboratory_QAQC_Detailed_Guide_MN.docx"
        ): "2c58418831d81be2b4e6b665707074668f8080bd15cbe39a3bbf0ba8c0012737",
        PurePosixPath(
            "docs/methodology/phase_10/"
            "Phase_10_Integrated_Interpretation_Final_Target_Ranking_Guide_MN.docx"
        ): "cab3d4b2f0e28b833894469df28311a6c32ebacb924ec4d2ae27f5f5ee59af4a",
        PurePosixPath(
            "docs/methodology/phase_11/"
            "Phase_11_Follow_Up_Trench_Geophysics_Scout_Drill_Planning_Guide_MN.docx"
        ): "ee3d9dd4a1cb28541926fb1a8319c30cd884d20f8774762a0303506df74eda69",
        PurePosixPath(
            "docs/methodology/phase_99/99_Final_Deliverables_Detailed_Guide_MN.docx"
        ): "dc20825afaff3cd5cc4c8f0d22913af4177a9abe3e2ff7f11289b2417e812fe7",
    }
)

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
            r"(?!placeholder\b|example\b|dummy\b|redacted\b|change[_-]?me\b|"
            r"re\.compile\b|os\.environ\.get\b|os\.getenv\b)"
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
        if is_exact_approved_artifact(repository_root, path):
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
    return _is_safe_exact_file(repository_root, path, expected)


def is_exact_approved_artifact(repository_root: Path, path: PurePosixPath) -> bool:
    expected = APPROVED_METHODOLOGY_DOCUMENTS.get(path)
    if expected is not None:
        return _is_safe_exact_file(repository_root, path, expected)
    return is_exact_approved_fixture(repository_root, path)


def _is_safe_exact_file(repository_root: Path, path: PurePosixPath, expected: str) -> bool:
    try:
        root = repository_root.resolve(strict=True)
        candidate = repository_root / Path(path.as_posix())
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError):
        return False
    return (
        candidate.is_file() and not candidate.is_symlink() and _sha256_file(candidate) == expected
    )


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
    if path.suffix.casefold() == ".docx":
        yield from _docx_text_chunks(path)
        return
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


def _docx_text_chunks(path: Path) -> Iterator[str]:
    """Yield text-bearing XML from a DOCX without extracting archive members."""

    try:
        with zipfile.ZipFile(path) as archive:
            members = tuple(
                sorted(
                    (
                        member
                        for member in archive.infolist()
                        if not member.is_dir()
                        and member.filename.casefold().endswith((".xml", ".rels", ".txt"))
                    ),
                    key=lambda member: member.filename.casefold(),
                )
            )
            if not members:
                raise UnicodeError("DOCX contains no text-bearing package members")
            if sum(member.file_size for member in members) > 128 * 1024 * 1024:
                raise UnicodeError("DOCX expanded text exceeds the repository scan limit")
            for member in members:
                if member.flag_bits & 0x1:
                    raise UnicodeError("encrypted DOCX members cannot be secret-scanned")
                try:
                    decoded = archive.read(member).decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise UnicodeError(
                        f"DOCX member is not valid UTF-8 XML: {member.filename}"
                    ) from exc
                yield decoded
                # Text nodes normally begin immediately after a closing angle bracket;
                # insert a scan boundary so assignment patterns see the first text token.
                yield decoded.replace(">", ">\n")
    except (OSError, zipfile.BadZipFile) as exc:
        raise UnicodeError("DOCX package is unreadable or invalid") from exc


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
