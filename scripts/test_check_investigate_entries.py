"""Pins for the entry-validator floor (entry-validator floor follow-ups plan)."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check_investigate_entries.py"


@pytest.fixture
def log_fixture(tmp_path):
    log = tmp_path / "PLAN-PROMPTS.md"
    log.write_text(
        "## entry-one\n\n"
        "Rejected alternatives:\n"
        "- Skip the check: rejected (agents/skills/investigate/SKILL.md)\n",
        encoding="utf-8",
    )
    return log


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=cwd,
        capture_output=True, text=True)


def test_entry_validator_floor_refuses_subdirectory_invocation(tmp_path):
    """A subdirectory invocation refuses with the named message (exit 2)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    proc = _run(sub)
    assert proc.returncode == 2
    assert "invoked outside the repository root" in proc.stderr
    assert "run from the repository root" in proc.stderr


def test_entry_validator_floor_repo_root_invocation_unchanged(tmp_path, log_fixture):
    """Repo-root invocation with an explicit --log fixture behaves as today."""
    proc = _run(REPO, "--log", str(log_fixture))
    assert proc.returncode == 0, proc.stderr
    assert "0 violation(s)" in proc.stdout
