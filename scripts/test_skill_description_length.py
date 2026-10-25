"""Contract tests for the skill description length checker.

Outcome classes (plan
docs/history/plans/2026-10-24-description-length-gate-catch-promotion.md
Task 1): exit 1 is reserved for measured over-cap descriptions only; exit 2
reports an operational exception (an unreadable file, or an unexpected scan
failure) as a stderr diagnostic and is never a measured result; exit 0
passes."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts" / "check_skill_description_length.py"


def load_checker_module():
    spec = importlib.util.spec_from_file_location(
        "check_skill_description_length_under_test", CHECKER
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


# --------------------------------------------------------------------------- #
# Outcome-class separation (plan 2026-10-24-description-length-gate-catch-
# promotion Task 1): exit 2 is the operational-exception class and never
# masquerades as the measured over-cap exit 1.
# --------------------------------------------------------------------------- #
def test_unreadable_file_is_operational_exception_exit_two(tmp_path):
    import os

    if os.geteuid() == 0:
        import pytest

        pytest.skip("chmod-based unreadability never holds for root")
    directory = tmp_path / "agents" / "skills" / "locked"
    directory.mkdir(parents=True)
    locked = directory / "SKILL.md"
    locked.write_text("---\nname: locked\ndescription: short\n---\n", encoding="utf-8")
    locked.chmod(0o000)
    try:
        result = run_checker(str(tmp_path / "agents" / "skills"))
    finally:
        locked.chmod(0o644)
    assert result.returncode == 2, (result.returncode, result.stderr)
    out = result.stderr + result.stdout
    assert "operational exception" in out
    assert "locked" in out
    # An operational exception is never reported as a measured result.
    assert "folded description" not in out


def test_error_dominates_measured_failures_exit_stays_two(tmp_path):
    import os

    if os.geteuid() == 0:
        import pytest

        pytest.skip("chmod-based unreadability never holds for root")
    over_dir = tmp_path / "agents" / "skills" / "over"
    over_dir.mkdir(parents=True)
    (over_dir / "SKILL.md").write_text(
        "---\nname: over\ndescription: " + "x" * 1025 + "\n---\n", encoding="utf-8"
    )
    locked_dir = tmp_path / "agents" / "skills" / "locked"
    locked_dir.mkdir(parents=True)
    locked = locked_dir / "SKILL.md"
    locked.write_text("---\nname: locked\ndescription: short\n---\n", encoding="utf-8")
    locked.chmod(0o000)
    try:
        result = run_checker(str(tmp_path / "agents" / "skills"))
    finally:
        locked.chmod(0o644)
    # The run measured a real over-cap description AND hit an operational
    # exception; exit 1 is reserved for measured-only results, so the
    # exception class wins with exit 2 and both diagnostics print.
    assert result.returncode == 2, (result.returncode, result.stderr)
    out = result.stderr + result.stdout
    assert "1025" in out
    assert "operational exception" in out


def test_unexpected_scan_exception_captured_as_exit_two(
    tmp_path, monkeypatch, capsys
):
    """A scan crash (any non-OSError escaping check_tree) is captured by
    main and answered as exit 2 with a diagnostic, never as a traceback exit
    that would masquerade as the measured over-cap class exit 1."""
    module = load_checker_module()

    def boom(roots, tracked_only=False):  # noqa: ARG001 - signature mirror
        raise RuntimeError("scan exploded")

    monkeypatch.setattr(module, "check_tree", boom)
    code = module.main([str(tmp_path)])
    assert code == 2
    err = capsys.readouterr().err
    assert "operational exception" in err
    assert "RuntimeError" in err


def test_exit_one_is_exclusively_measured_over_cap(tmp_path):
    """The measured class keeps exit 1 end to end through main(): the same
    over-cap tree the sweep classifies as the one catch-eligible result."""
    module = load_checker_module()
    over_dir = tmp_path / "agents" / "skills" / "over"
    over_dir.mkdir(parents=True)
    (over_dir / "SKILL.md").write_text(
        "---\nname: over\ndescription: " + "x" * 1025 + "\n---\n", encoding="utf-8"
    )
    assert module.main([str(tmp_path)]) == 1
