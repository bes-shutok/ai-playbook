"""Contract tests for the skill description length checker."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts" / "check_skill_description_length.py"


def run_checker(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        capture_output=True,
        text=True,
    )


def skill(tmp_path: Path, name: str, description: str) -> Path:
    directory = tmp_path / "agents" / "skills" / name
    directory.mkdir(parents=True)
    path = directory / "SKILL.md"
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nbody\n",
        encoding="utf-8",
    )
    return path


def test_over_cap_fails(tmp_path):
    skill(tmp_path, "over", "x" * 1025)
    result = run_checker(str(tmp_path / "agents" / "skills"))
    assert result.returncode == 1
    assert "over" in result.stderr + result.stdout
    assert "1025" in result.stderr + result.stdout


def test_at_cap_passes(tmp_path):
    skill(tmp_path, "edge", "x" * 1024)
    result = run_checker(str(tmp_path / "agents" / "skills"))
    assert result.returncode == 0, result.stderr


def test_near_cap_warns(tmp_path):
    skill(tmp_path, "near", "x" * 951)
    result = run_checker(str(tmp_path / "agents" / "skills"))
    assert result.returncode == 0
    assert "near" in result.stderr + result.stdout


def test_folded_scalar_measured_folded(tmp_path):
    folded = ">"
    for _ in range(11):
        folded += "\n  " + "x" * 100
    directory = tmp_path / "agents" / "skills" / "folded"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        f"---\nname: folded\ndescription: {folded}\n---\n\nbody\n",
        encoding="utf-8",
    )
    # 11 indented lines of 100 joined single-spaced: 11*100 + 10 = 1110 > cap.
    result = run_checker(str(tmp_path / "agents" / "skills"))
    assert result.returncode == 1
    assert "1110" in result.stderr + result.stdout


def test_body_fence_not_swallowed(tmp_path):
    directory = tmp_path / "agents" / "skills" / "fenced"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        "---\n"
        "name: fenced\n"
        "description: short\n"
        "---\n"
        "\n"
        "```yaml\n"
        "  description: yyyyyyyy\n"
        "```\n",
        encoding="utf-8",
    )
    result = run_checker(str(tmp_path / "agents" / "skills"))
    assert result.returncode == 0, result.stderr
    assert "fenced" not in result.stderr


def test_missing_description_skipped(tmp_path):
    directory = tmp_path / "agents" / "skills" / "nodesc"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        "---\nname: nodesc\n---\n\nbody\n", encoding="utf-8"
    )
    result = run_checker(str(tmp_path / "agents" / "skills"))
    assert result.returncode == 0
    assert "nodesc" not in result.stderr + result.stdout
