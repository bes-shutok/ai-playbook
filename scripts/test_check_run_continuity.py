#!/usr/bin/env python3
"""Tests for the per-boundary run-continuity probe (check_run_continuity.py).

Every fixture builds hermetic scratch repositories (``git init``,
``git worktree add``) under a temp dir and drives the probe's ``check``
invocation as a subprocess, asserting the four-outcome contract from
``scripts/OUTCOME_CONTRACT.md`` (exit 0 pass / 1 fail / 2 indeterminate /
3 tool_error, final ``OUTCOME:`` line required).
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "check_run_continuity.py"

# Collection-time module-load pin: the probe module must exist for this test
# module to even collect, so a missing implementation fails at collection.
_spec = importlib.util.spec_from_file_location("check_run_continuity_under_test", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = MODULE
_spec.loader.exec_module(MODULE)

CHECK_NAMES = ("linked", "registered", "branch", "facts", "reviews", "baseline")
RECORDED_BRANCH = "run-branch"


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"git -C {repo} {' '.join(args)} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def _make_primary(root: Path, name: str = "primary") -> Path:
    """A plain primary checkout on branch main, with one base commit."""
    repo = root / name
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Continuity Fixture")
    _git(repo, "config", "user.email", "continuity.fixture@invalid")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture base")
    return repo


def _add_worktree(primary: Path, path: Path, branch: str) -> Path:
    _git(primary, "worktree", "add", "-q", "-b", branch, str(path))
    return path


def _provision_inputs(repo: Path, manifest_dir: Path) -> Path:
    """Transfer in the gitignored inputs: facts file, reviews dir, baseline."""
    (repo / ".ai-playbook").mkdir(parents=True, exist_ok=True)
    (repo / ".ai-playbook" / "facts.md").write_text(
        "```toml\n"
        'reviews_dir = ".ai-playbook/reviews/"\n'
        "```\n",
        encoding="utf-8",
    )
    (repo / ".ai-playbook" / "reviews").mkdir(parents=True, exist_ok=True)
    (repo / ".ai-playbook" / "reviews" / "r1.md").write_text(
        "review record\n", encoding="utf-8"
    )
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "closeout-baseline.json").write_text("{}\n", encoding="utf-8")
    return manifest_dir


def _run_check(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "check", *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _check_line(out: str, name: str) -> str | None:
    for line in out.splitlines():
        if line.startswith(name + ":"):
            return line
    return None


def _fail_lines(out: str) -> list[str]:
    # Anchored on check-name prefixes so the final `OUTCOME: fail` row is
    # never counted as a per-check fail line.
    return [
        line
        for line in out.splitlines()
        if any(line.startswith(name + ": fail") for name in CHECK_NAMES)
    ]


def _assert_all_names_reported(out: str) -> None:
    for name in CHECK_NAMES:
        line = _check_line(out, name)
        self_msg = f"no line for check {name!r} in output:\n{out}"
        assert line is not None, self_msg


def _green_fixture(root: Path) -> tuple[Path, Path, Path]:
    """Primary + linked worktree on the recorded branch, inputs transferred in."""
    primary = _make_primary(root)
    wt = _add_worktree(primary, root / "wt", RECORDED_BRANCH)
    manifest_dir = _provision_inputs(wt, root / "manifests")
    return primary, wt, manifest_dir


class CheckRunContinuityTest(unittest.TestCase):
    def test_green_linked_worktree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _primary, wt, manifest_dir = _green_fixture(root)
            code, out, err = _run_check(
                "--repo", str(wt),
                "--branch", RECORDED_BRANCH,
                "--manifest-dir", str(manifest_dir),
            )
            self.assertEqual(code, 0, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: pass"), out)
            _assert_all_names_reported(out)
            for name in CHECK_NAMES:
                line = _check_line(out, name)
                self.assertIsNotNone(line)
                self.assertTrue(
                    line.startswith(f"{name}: pass "),
                    f"expected pass line for {name}, got: {line}",
                )

    def test_branch_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _primary, wt, manifest_dir = _green_fixture(root)
            code, out, err = _run_check(
                "--repo", str(wt),
                "--branch", "some-other-branch",
                "--manifest-dir", str(manifest_dir),
            )
            self.assertEqual(code, 1, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: fail"), out)
            branch_line = _check_line(out, "branch")
            self.assertIsNotNone(branch_line)
            self.assertTrue(branch_line.startswith("branch: fail"), branch_line)
            # The fail line names the observed branch.
            self.assertIn(RECORDED_BRANCH, branch_line)

    def test_missing_inputs_fail_individually(self):
        arms = (
            ("facts", "missing_facts"),
            ("reviews", "missing_reviews"),
            ("baseline", "missing_baseline"),
        )
        for check_name, arm in arms:
            with self.subTest(arm=arm):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    _primary, wt, manifest_dir = _green_fixture(root)
                    reviews_arg = []
                    if arm == "missing_facts":
                        # The reviews path comes from --reviews so exactly the
                        # facts check fails (facts is the only lost input).
                        (wt / ".ai-playbook" / "facts.md").unlink()
                        reviews_arg = ["--reviews", str(wt / ".ai-playbook/reviews")]
                    elif arm == "missing_reviews":
                        shutil.rmtree(wt / ".ai-playbook" / "reviews")
                    else:
                        (manifest_dir / "closeout-baseline.json").unlink()
                    code, out, err = _run_check(
                        "--repo", str(wt),
                        "--branch", RECORDED_BRANCH,
                        "--manifest-dir", str(manifest_dir),
                        *reviews_arg,
                    )
                    self.assertEqual(code, 1, f"arm {arm}: stdout:\n{out}\nstderr:\n{err}")
                    self.assertTrue(out.rstrip().endswith("OUTCOME: fail"), out)
                    _assert_all_names_reported(out)
                    failing = _fail_lines(out)
                    self.assertEqual(len(failing), 1, f"arm {arm}: want one fail line, got:\n{out}")
                    self.assertTrue(
                        failing[0].startswith(f"{check_name}: fail"),
                        f"arm {arm}: want {check_name} to fail, got: {failing[0]}",
                    )

    def test_baseline_skip_sibling_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _primary, wt, manifest_dir = _green_fixture(root)
            (manifest_dir / "closeout-baseline.json").unlink()
            (manifest_dir / "closeout-baseline-skip.json").write_text("{}\n", encoding="utf-8")
            code, out, err = _run_check(
                "--repo", str(wt),
                "--branch", RECORDED_BRANCH,
                "--manifest-dir", str(manifest_dir),
            )
            self.assertEqual(code, 0, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: pass"), out)
            baseline_line = _check_line(out, "baseline")
            self.assertIsNotNone(baseline_line)
            self.assertTrue(baseline_line.startswith("baseline: pass"), baseline_line)

    def test_non_linked_repo_fails_linked_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = _make_primary(root)
            manifest_dir = _provision_inputs(primary, root / "manifests")
            code, out, err = _run_check(
                "--repo", str(primary),
                "--branch", "main",
                "--manifest-dir", str(manifest_dir),
            )
            self.assertEqual(code, 1, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: fail"), out)
            linked_line = _check_line(out, "linked")
            self.assertIsNotNone(linked_line)
            self.assertTrue(linked_line.startswith("linked: fail"), linked_line)
            # The fail evidence names the equal git-dir path.
            self.assertIn(str((primary / ".git").resolve()), linked_line)

    def test_standalone_checkout_fails_linked_and_registered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = _make_primary(root)
            clone = root / "clone"
            _git(root, "clone", "-q", str(primary), str(clone))
            manifest_dir = _provision_inputs(clone, root / "manifests")
            branch = _git(clone, "rev-parse", "--abbrev-ref", "HEAD").strip()
            code, out, err = _run_check(
                "--repo", str(clone),
                "--branch", branch,
                "--manifest-dir", str(manifest_dir),
            )
            self.assertEqual(code, 1, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: fail"), out)
            linked_line = _check_line(out, "linked")
            self.assertIsNotNone(linked_line)
            self.assertTrue(linked_line.startswith("linked: fail"), linked_line)
            registered_line = _check_line(out, "registered")
            self.assertIsNotNone(registered_line)
            self.assertTrue(registered_line.startswith("registered: fail"), registered_line)

    def test_broken_gitdir_is_indeterminate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = _make_primary(root)
            wt = _add_worktree(primary, root / "wt", RECORDED_BRANCH)
            manifest_dir = _provision_inputs(wt, root / "manifests")
            gitfile = wt / ".git"
            self.assertTrue(gitfile.is_file(), "fixture: the worktree gitfile must remain")
            gitdir_target = ""
            for line in gitfile.read_text(encoding="utf-8").splitlines():
                if line.startswith("gitdir:"):
                    gitdir_target = line[len("gitdir:"):].strip()
                    break
            self.assertTrue(gitdir_target, "fixture: gitfile carries a gitdir pointer")
            # Prune the registration entry while the gitfile remains.
            shutil.rmtree(gitdir_target)
            code, out, err = _run_check(
                "--repo", str(wt),
                "--branch", RECORDED_BRANCH,
                "--manifest-dir", str(manifest_dir),
            )
            self.assertEqual(code, 2, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: indeterminate"), out)
            # The evidence names the invalid gitfile's target.
            self.assertIn(gitdir_target, out)
            # Per-check fail lines are suppressed on the indeterminate path.
            self.assertEqual(_fail_lines(out), [], out)
            for name in CHECK_NAMES:
                line = _check_line(out, name)
                self.assertTrue(
                    line is None or ": fail" not in line,
                    f"unexpected check fail line for {name}: {line}",
                )

    def test_usage_errors_are_tool_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = _make_primary(root)
            # Arm 1: missing --branch.
            code, out, err = _run_check("--repo", str(primary))
            self.assertEqual(code, 3, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertIn("OUTCOME: tool_error", out + err)
            # Arm 2: nonexistent --repo path.
            missing = root / "nope"
            code2, out2, err2 = _run_check("--repo", str(missing), "--branch", "main")
            self.assertEqual(code2, 3, f"stdout:\n{out2}\nstderr:\n{err2}")
            self.assertIn("OUTCOME: tool_error", out2 + err2)
            self.assertIn("nope", out2 + err2)
            # Arm 3: an existing path that is not a checkout at all (no .git
            # entry): the plumbing failure is the tool-error class, never an
            # indeterminate over an "existing checkout".
            plain = root / "plain-dir"
            plain.mkdir()
            self.assertFalse((plain / ".git").exists())
            code3, out3, err3 = _run_check("--repo", str(plain), "--branch", "main")
            self.assertEqual(code3, 3, f"stdout:\n{out3}\nstderr:\n{err3}")
            self.assertIn("OUTCOME: tool_error", out3 + err3)
            self.assertIn("plain-dir", out3 + err3)
            self.assertNotIn("OUTCOME: indeterminate", out3 + err3)

    def test_primary_placement_skips_worktree_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _primary, wt, manifest_dir = _green_fixture(root)
            args = [
                "--repo", str(wt),
                "--branch", RECORDED_BRANCH,
                "--manifest-dir", str(manifest_dir),
                "--skip-worktree-checks",
            ]
            code, out, err = _run_check(*args)
            self.assertEqual(code, 0, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertTrue(out.rstrip().endswith("OUTCOME: pass"), out)
            for name in ("linked", "registered", "branch"):
                line = _check_line(out, name)
                self.assertIsNotNone(line)
                self.assertEqual(line, f"{name}: skipped")
            for name in ("facts", "reviews", "baseline"):
                line = _check_line(out, name)
                self.assertIsNotNone(line)
                self.assertTrue(line.startswith(f"{name}: pass "), line)
            # The input and baseline checks stay enforced under the flag.
            (manifest_dir / "closeout-baseline.json").unlink()
            code2, out2, err2 = _run_check(*args)
            self.assertEqual(code2, 1, f"stdout:\n{out2}\nstderr:\n{err2}")
            self.assertTrue(out2.rstrip().endswith("OUTCOME: fail"), out2)
            baseline_line = _check_line(out2, "baseline")
            self.assertIsNotNone(baseline_line)
            self.assertTrue(baseline_line.startswith("baseline: fail"), baseline_line)
            for name in ("linked", "registered", "branch"):
                self.assertEqual(_check_line(out2, name), f"{name}: skipped")


if __name__ == "__main__":
    unittest.main()
