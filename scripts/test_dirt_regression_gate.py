#!/usr/bin/env python3
"""Tests for the dirt regression gate (dirt_regression_gate.py).

Fixtures are scratch git repositories under tempfile.mkdtemp with explicit
teardown; git identity is configured locally in each fixture and nothing
touches the network.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "dirt_regression_gate.py"

BASE_TEXT = "alpha\nbeta\ngamma\ndelta\nepsilon\n"
HEAD_TEXT = "alpha\nbeta-head-v2\ngamma\ndelta-head\nepsilon\nzeta-head\n"


class DirtRegressionGateTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="dirt-regression-gate-test-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.tmp = tmp
        self.repo = self._init_repo()

    def _git_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = str(self.tmp / "gitconfig")
        return env

    def _git(self, *args: str, cwd: Path | None = None) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd if cwd is not None else self.repo),
            capture_output=True,
            text=True,
            env=self._git_env(),
        )
        self.assertEqual(
            proc.returncode, 0, f"git {args} failed: {proc.stderr}"
        )
        return proc.stdout

    def _init_repo(self) -> Path:
        repo = self.tmp / "repo"
        repo.mkdir()
        self._git("init", "-q", "-b", "main", cwd=repo)
        self._git("config", "user.email", "test@example.com", cwd=repo)
        self._git("config", "user.name", "Test Fixture", cwd=repo)
        return repo

    def _commit(self, rel: str, text: str, message: str) -> None:
        target = self.repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)

    def _set_dirt(self, rel: str, text: str) -> None:
        (self.repo / rel).write_text(text, encoding="utf-8")

    def _run_gate(self, *args: str) -> tuple[int, str, str]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            cwd=str(self.repo),
            env=self._git_env(),
        )
        return proc.returncode, proc.stdout, proc.stderr

    def _seed_head_gained_lines(self) -> str:
        """Commit base, then a HEAD commit whose lines are HEAD-gained; return base sha."""
        self._commit("app.txt", BASE_TEXT, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", HEAD_TEXT, "head gains lines")
        return base_sha

    def test_reverting_hunk_is_regression(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt restores the exact base-era file: a byte-identical whole-file
        # revert of content HEAD gained since the merge base.
        self._set_dirt("app.txt", BASE_TEXT)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn("dirt REGRESSION", stdout)

    def test_forward_dirt_passes(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt only adds a brand-new line; nothing HEAD-gained is removed.
        self._set_dirt("app.txt", HEAD_TEXT + "forward-note\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("PASS", stdout)

    def test_prebase_line_modification_passes(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt modifies "gamma", a line already present at the merge base.
        # The removed line is not HEAD-gained, so this passes even though the
        # hunk removes a line (discriminates against an all-removed-lines
        # reading of the rule).
        dirt = HEAD_TEXT.replace("gamma\n", "gamma-tweaked\n")
        self.assertNotEqual(dirt, HEAD_TEXT)
        self._set_dirt("app.txt", dirt)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("PASS", stdout)

    def test_headgained_line_modification_passes(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt modifies a line HEAD gained, replacing it with new text not
        # present at the base: a forward-looking rewrite, not a regression
        # (discriminates the hunk-level rule from a literal
        # any-removed-HEAD-gained-line reading).
        dirt = HEAD_TEXT.replace(
            "beta-head-v2\n", "beta-head-v3-forward\n"
        )
        self.assertNotEqual(dirt, HEAD_TEXT)
        self._set_dirt("app.txt", dirt)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("PASS", stdout)

    def test_revert_to_base_text_is_regression(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt reverts only the "delta" region to its base-era text while
        # keeping the HEAD-gained "zeta-head": not a whole-file revert, still
        # a regression (the witnessed partial-revert shape).
        dirt = HEAD_TEXT.replace("delta-head\n", "delta\n")
        self.assertNotEqual(dirt, HEAD_TEXT)
        self._set_dirt("app.txt", dirt)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn("dirt REGRESSION", stdout)

    def test_out_of_repo_path_fails_closed(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        outside = self.tmp / "outside.txt"
        outside.write_text("x\n", encoding="utf-8")
        proc_rc, proc_stdout, proc_stderr = self._run_gate(
            "--base", self._git("rev-parse", "HEAD").strip(), str(outside)
        )
        proc = subprocess.CompletedProcess([], proc_rc, proc_stdout, proc_stderr)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not inside repository", proc.stderr)

    def test_missing_path_fails_closed(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        ghost = self.repo / "ghost.txt"
        proc_rc, proc_stdout, proc_stderr = self._run_gate(
            "--base", self._git("rev-parse", "HEAD").strip(), str(ghost)
        )
        proc = subprocess.CompletedProcess([], proc_rc, proc_stdout, proc_stderr)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("does not exist", proc.stderr)

    def test_regressive_whole_file_deletion_is_regression(self) -> None:
        base_sha = self._seed_head_gained_lines()
        (self.repo / "app.txt").unlink()
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1)
        self.assertIn("app.txt", stdout)

    def test_neutral_whole_file_deletion_passes(self) -> None:
        self._commit("app.txt", BASE_TEXT, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", BASE_TEXT + "tail\n", "head changes a line")
        self._commit("app.txt", BASE_TEXT, "head restores base content")
        (self.repo / "app.txt").unlink()
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0)

    def test_untracked_missing_path_fails_closed(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        ghost = self.repo / "ghost.txt"
        code, stdout, stderr = self._run_gate(
            "--base", self._git("rev-parse", "HEAD").strip(), str(ghost)
        )
        self.assertEqual(code, 2)

    def test_unreadable_stamp_treated_as_absent(self) -> None:
        base_sha = self._seed_head_gained_lines()
        (self.repo / ".source-commit").write_bytes(b"\xff\xfe\x00binary")
        code, stdout, stderr = self._run_gate(
            "--base", base_sha, "--stamp", "app.txt"
        )
        self.assertEqual(code, 0)
        self.assertIn("treated as unstamped", stderr)

    def test_stamp_cited_when_present(self):
        base_sha = self._seed_head_gained_lines()
        self._set_dirt("app.txt", BASE_TEXT)
        stamped_sha = self._git("rev-parse", "HEAD").strip()
        stamp = self.repo / ".source-commit"
        stamp.write_text(stamped_sha + "\n", encoding="utf-8")
        code, stdout, stderr = self._run_gate(
            "--base", base_sha, "--stamp", "app.txt"
        )
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn(stamped_sha, stdout)


if __name__ == "__main__":
    unittest.main()
