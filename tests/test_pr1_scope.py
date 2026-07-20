from __future__ import annotations

import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_agents_is_the_only_tracked_markdown_file() -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    markdown_suffixes = (".md", ".markdown", ".mdown", ".mdwn")
    tracked_markdown = [
        path
        for path in result.stdout.splitlines()
        if path.lower().endswith(markdown_suffixes) and (REPOSITORY_ROOT / path).is_file()
    ]
    assert tracked_markdown == ["AGENTS.md"], (
        "AGENTS.md must remain the only tracked Markdown file; durable methodology and audit "
        f"facts belong in versioned machine-readable contracts. Found: {tracked_markdown}"
    )
