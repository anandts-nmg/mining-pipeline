from __future__ import annotations

import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_HEAD_OBJECT = "7ccf81d1c9c0ecc4e33d4990aafcc0ee45bed64d"
EXCLUDED_LATER_PLAN = "docs/PROSPECTIVITY_MAPPING_LLM_API_PLAN.md"


def test_legacy_claude_file_remains_byte_identical_to_pr1_baseline() -> None:
    result = subprocess.run(
        ["git", "hash-object", "CLAUDE.md"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == CLAUDE_HEAD_OBJECT


def test_later_prospectivity_plan_is_not_tracked_in_pr1() -> None:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", EXCLUDED_LATER_PLAN],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
