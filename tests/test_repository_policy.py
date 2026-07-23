"""Tests for the reusable tracked-artifact and secret policy."""

from __future__ import annotations

import codecs
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

import pytest

from buduunkhad.repository_policy import (
    APPROVED_METHODOLOGY_DOCUMENTS,
    APPROVED_SYNTHETIC_FIXTURES,
    artifact_violations,
    repository_policy_violations,
    secret_findings,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_reusable_policy_accepts_current_tracked_repository() -> None:
    violations = repository_policy_violations(REPOSITORY_ROOT)
    assert not violations, "repository policy violations:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "path",
    [
        "raw/map.gpkg",
        "raw/image.tif",
        "raw/image.hdf",
        "raw/boundary.kmz",
        "raw/boundary.kml",
        "raw/raster.img",
        "raw/raster.aux.xml",
        "raw/raster.ovr",
        "raw/raster.tfw",
        "raw/raster.jgw",
        "raw/raster.rpc",
        "raw/raster.eph",
        "raw/ortho.avif",
        "raw/vector.prj",
        "raw/vector.shp.xml",
        "docs/project.docx",
        "docs/project.xlsx",
        "runtime/project.qgz",
        "runtime/project.qgs",
        "runtime/project.qml",
        "runtime/cloud.las",
        "runtime/cloud.laz",
        "runtime/cloud.copc.laz",
        "runtime/cloud.e57",
        "runtime/jobs.sqlite",
        "runtime/jobs.duckdb",
        "response-store.jsonl",
        "job-database.json",
        "credentials.json",
        "certificate.crt",
        "private.key",
        "private.ppk",
    ],
)
def test_complete_forbidden_artifact_set_is_centralized(path: str) -> None:
    candidate = PurePosixPath(path)
    assert artifact_violations(REPOSITORY_ROOT, (candidate,)) == (path,)


@pytest.mark.parametrize(
    "path",
    [
        "data/raw.bin",
        "outputs/result.txt",
        "control/state.json",
        "runs/run.json",
        "evidence-authority/evidence_manifest.json",
        "ai_jobs/job.json",
        "ai_responses/response.json",
        "private_evaluations/case.json",
        "qgis_runtime/state.txt",
        "rendered_tiles/tile.txt",
        ".codex-local/audit.md",
    ],
)
def test_control_runtime_and_private_roots_are_forbidden(path: str) -> None:
    assert artifact_violations(REPOSITORY_ROOT, (PurePosixPath(path),)) == (path,)


def test_fixture_exceptions_are_exact_not_directory_wide() -> None:
    assert not APPROVED_SYNTHETIC_FIXTURES
    path = PurePosixPath("tests/fixtures/synthetic/arbitrary.gpkg")
    assert artifact_violations(REPOSITORY_ROOT, (path,)) == (str(path),)


def test_reviewed_methodology_documents_are_exact_path_and_hash_exceptions() -> None:
    assert len(APPROVED_METHODOLOGY_DOCUMENTS) == 17
    assert artifact_violations(REPOSITORY_ROOT, APPROVED_METHODOLOGY_DOCUMENTS) == ()


def test_reviewed_methodology_documents_are_secret_free() -> None:
    for path in APPROVED_METHODOLOGY_DOCUMENTS:
        candidate = REPOSITORY_ROOT / Path(path.as_posix())
        assert secret_findings(candidate) == (), str(path)


def test_changed_methodology_document_loses_its_exception(tmp_path: Path) -> None:
    path = next(iter(APPROVED_METHODOLOGY_DOCUMENTS))
    candidate = tmp_path / Path(path.as_posix())
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"not the reviewed methodology bytes")
    assert artifact_violations(tmp_path, (path,)) == (str(path),)


def test_unlisted_methodology_docx_remains_forbidden(tmp_path: Path) -> None:
    path = PurePosixPath("docs/methodology/phase_02/unreviewed.docx")
    candidate = tmp_path / Path(path.as_posix())
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"unreviewed")
    assert artifact_violations(tmp_path, (path,)) == (str(path),)


def test_methodology_exception_rejects_a_symlink_substitution(tmp_path: Path) -> None:
    path, expected = next(iter(APPROVED_METHODOLOGY_DOCUMENTS.items()))
    source = REPOSITORY_ROOT / Path(path.as_posix())
    assert source.is_file()
    outside = tmp_path / "outside.docx"
    outside.write_bytes(source.read_bytes())
    candidate = tmp_path / "repository" / Path(path.as_posix())
    candidate.parent.mkdir(parents=True)
    try:
        candidate.symlink_to(outside)
    except OSError:
        pytest.skip("this platform cannot create the required file symlink")
    assert expected == APPROVED_METHODOLOGY_DOCUMENTS[path]
    assert artifact_violations(tmp_path / "repository", (path,)) == (str(path),)


@pytest.mark.parametrize(
    "name",
    [
        "OPENAI_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "CLIENT_SECRET",
        "ACCESS_TOKEN",
        "AUTH_TOKEN",
        "PASSWORD",
        "vendor.CLIENT_SECRET",
    ],
)
def test_representative_namespaced_secret_assignments_are_detected(
    tmp_path: Path, name: str
) -> None:
    path = tmp_path / "unknown.extension"
    path.write_text(name + "=" + "sensitive_value_123456", encoding="utf-8")
    assert "suspicious secret assignment" in secret_findings(path)


def test_environment_key_lookup_is_not_mistaken_for_a_stored_secret(tmp_path: Path) -> None:
    path = tmp_path / "provider.py"
    path.write_text(
        'api_key = os.environ.get("OPENAI_API_KEY")\n',
        encoding="utf-8",
    )
    assert "suspicious secret assignment" not in secret_findings(path)


@pytest.mark.parametrize(
    "token",
    [
        "sk-" + "A" * 30,
        "ghp_" + "A" * 35,
        "glpat-" + "A" * 24,
        "hf_" + "A" * 24,
        "xoxb-" + "A" * 24,
        "AIza" + "A" * 35,
        "AKIA" + "A" * 16,
    ],
)
def test_common_provider_token_formats_are_detected(tmp_path: Path, token: str) -> None:
    path = tmp_path / "token.txt"
    path.write_text("value: " + token, encoding="utf-8")
    assert secret_findings(path)


@pytest.mark.parametrize(
    "header",
    [
        "PRIVATE KEY",
        "RSA PRIVATE KEY",
        "EC PRIVATE KEY",
        "DSA PRIVATE KEY",
        "OPENSSH PRIVATE KEY",
        "ENCRYPTED PRIVATE KEY",
        "PGP PRIVATE KEY BLOCK",
        "PuTTY-User-Key-File-3: ssh-rsa",
    ],
)
def test_private_key_forms_are_detected(tmp_path: Path, header: str) -> None:
    path = tmp_path / "key.unknown"
    text = header if header.startswith("PuTTY") else "-----BEGIN " + header + "-----"
    path.write_text(text + "\nsynthetic", encoding="utf-8")
    assert any("private key" in finding.casefold() for finding in secret_findings(path))


@pytest.mark.parametrize(
    ("encoding", "bom"),
    [
        ("utf-8", b""),
        ("utf-16-le", codecs.BOM_UTF16_LE),
        ("utf-16-be", codecs.BOM_UTF16_BE),
    ],
)
def test_utf8_and_bom_marked_utf16_are_scanned(tmp_path: Path, encoding: str, bom: bytes) -> None:
    path = tmp_path / "encoded.noextension"
    text = "CLIENT" + "_SECRET=" + "sensitive_value_123456"
    path.write_bytes(bom + text.encode(encoding))
    assert "suspicious secret assignment" in secret_findings(path)


def test_text_like_file_with_invalid_utf8_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "malformed.noextension"
    path.write_bytes(b"ordinary text followed by invalid UTF-8: \xff")
    assert secret_findings(path) == ("unscannable text encoding",)


def test_docx_text_members_are_secret_scanned(tmp_path: Path) -> None:
    path = tmp_path / "methodology.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<w:document>CLIENT_SE" + "CRET=sensitive_value_123456</w:document>",
        )
    assert "suspicious secret assignment" in secret_findings(path)


def test_invalid_docx_fails_closed_for_secret_scanning(tmp_path: Path) -> None:
    path = tmp_path / "methodology.docx"
    path.write_bytes(b"not a valid package")
    assert secret_findings(path) == ("unscannable text encoding",)


@pytest.mark.parametrize("name", ["AGENTS.md", ".env.example", "notes.md", "file.weird"])
def test_every_text_filename_is_scanned(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_text("API" + "_KEY=" + "sensitive_value_123456", encoding="utf-8")
    assert "suspicious secret assignment" in secret_findings(path)


def test_large_text_and_chunk_boundary_secrets_are_streamed(tmp_path: Path) -> None:
    path = tmp_path / "large.noextension"
    prefix = "x" * (64 * 1024 - 3) + "\n"
    path.write_text(
        prefix + "OPENAI" + "_API_KEY=" + "sensitive_value_123456",
        encoding="utf-8",
    )
    assert "suspicious secret assignment" in secret_findings(path)


@pytest.mark.parametrize(
    "text",
    [
        '{"CLIENT_SE' + 'CRET": "value with spaces and !@#$%^&* punctuation"}',
        "'PASS" + "WORD': 'value with spaces and !@#$%^&* punctuation'",
        "export ACCESS_TO" + 'KEN="value with spaces and !@#$%^&* punctuation"',
        "$env:OPENAI_API" + "_KEY = 'value with spaces and !@#$%^&* punctuation'",
    ],
)
def test_quoted_json_yaml_shell_and_powershell_assignments_are_detected(
    tmp_path: Path,
    text: str,
) -> None:
    path = tmp_path / "assignment.unknown"
    path.write_text(text, encoding="utf-8")
    assert "suspicious secret assignment" in secret_findings(path)


def test_genuine_multi_megabyte_unknown_text_is_streamed(tmp_path: Path) -> None:
    path = tmp_path / "large.unknown"
    path.write_text(
        "x" * (1024 * 1024 + 127) + "\nCLIENT_SE" + "CRET=sensitive_value_123456",
        encoding="utf-8",
    )
    assert path.stat().st_size > 1024 * 1024
    assert "suspicious secret assignment" in secret_findings(path)


@pytest.mark.parametrize(
    ("encoding", "bom"),
    [("utf-16-le", codecs.BOM_UTF16_LE), ("utf-16-be", codecs.BOM_UTF16_BE)],
)
def test_utf16_secret_crossing_raw_stream_boundary_is_detected(
    tmp_path: Path,
    encoding: str,
    bom: bytes,
) -> None:
    path = tmp_path / "boundary.unknown"
    prefix = "x" * 32762 + "\n"
    payload_text = "OPENAI_API" + "_KEY=sensitive_value_123456"
    payload = bom + (prefix + payload_text).encode(encoding)
    path.write_bytes(payload)
    boundary = 64 * 1024
    secret_start = len(bom) + len(prefix.encode(encoding))
    assert secret_start < boundary < secret_start + len(payload_text.encode(encoding))
    assert "suspicious secret assignment" in secret_findings(path)


@pytest.mark.parametrize(
    "forced_path",
    [
        "raw/forced.geojson",
        "runtime/forced.txt",
        "logs/forced.txt",
        "build/forced.txt",
        "dist/forced.txt",
        "cache/forced.txt",
        "photos/forced.jpg",
        "imagery/forced.avif",
        "gis/forced.prj",
        "qgis/forced.qgs",
        "response-store.jsonl",
        "job-store.duckdb",
    ],
)
def test_force_added_artifacts_are_found_end_to_end_in_temporary_git_repository(
    tmp_path: Path,
    forced_path: str,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    (repository / ".gitignore").write_text("*\n", encoding="utf-8")
    candidate = repository / forced_path
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("synthetic policy probe", encoding="utf-8")
    subprocess.run(
        ["git", "add", "-f", ".gitignore", forced_path],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    violations = repository_policy_violations(repository)
    assert forced_path in violations


def test_binary_file_is_not_misdecoded_as_text(tmp_path: Path) -> None:
    path = tmp_path / "binary.bin"
    path.write_bytes(b"\0API" + b"_KEY=" + b"sensitive_value_123456")
    assert secret_findings(path) == ()
