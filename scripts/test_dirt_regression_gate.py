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
    HERMETIC_FIXTURES = {
        "test_removal_only_cleanup_hunk_passes",
        "test_removalonly_hunk_without_surviving_baseera_content_still_regression",
        "test_removalonly_regression_keys_on_worktree_baseera_absence",
        "test_pure_append_whole_reversion_still_regression",
        "test_set_equal_list_unequal_worktree_passes",
        "test_worktree_read_error_is_tool_error",
        "test_no_candidate_hunk_does_not_read_worktree",
        "test_worktree_decode_error_is_tool_error",
    }

    def setUp(self) -> None:
        if self._testMethodName in self.HERMETIC_FIXTURES:
            self._clear_ambient_git_environment()
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

    def _seed_baseabsent_head_file(self) -> str:
        """Commit a seed, then a file the merge base lacks; return base sha."""
        self._commit("seed.txt", "seed\n", "seed")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit(
            "new.txt", "one\ntwo\nthree\nfour\nfive\n", "head adds new file"
        )
        return base_sha

    def _clear_ambient_git_environment(self) -> None:
        names = (
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_COMMON_DIR",
            "GIT_CONFIG_COUNT",
            "GIT_CONFIG_KEY_0",
            "GIT_CONFIG_KEY_1",
            "GIT_CONFIG_PARAMETERS",
            "GIT_EXTERNAL_DIFF",
        )
        prior_values = {name: os.environ.get(name) for name in names}
        self.addCleanup(self._restore_ambient_git_environment, prior_values)
        for name in names:
            os.environ.pop(name, None)

    @staticmethod
    def _restore_ambient_git_environment(
        prior_values: dict[str, str | None],
    ) -> None:
        for name, value in prior_values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _run_main_with_worktree_read_error(self, read_error: Exception):
        import contextlib
        import io
        from unittest.mock import patch

        import scripts.dirt_regression_gate as gate

        base_sha = self._seed_head_gained_lines()
        self._set_dirt(
            "app.txt",
            "alpha\nbeta-head-v2\ngamma\ndelta-head\nepsilon\n",
        )
        target = self.repo / "app.txt"
        read_text = Path.read_text
        original_cwd = Path.cwd()
        self.addCleanup(os.chdir, original_cwd)
        os.chdir(self.repo)

        def fail_worktree_read(path, *args, **kwargs):
            if path.resolve() == target.resolve():
                raise read_error
            return read_text(path, *args, **kwargs)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.dict(os.environ, self._git_env()),
            patch.object(Path, "read_text", fail_worktree_read),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = gate.main(["--base", base_sha, "app.txt"])

        return code, stdout.getvalue(), stderr.getvalue()

    def test_removal_only_cleanup_hunk_passes(self):
        base_text = "alpha\nbeta\ngamma\n"
        head_text = base_text + "gained-one\ngained-two\ngained-three\n"
        self._commit("app.txt", base_text, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", head_text, "head gains lines")

        # Remove part of the branch-added block while base-era lines survive.
        self._set_dirt("app.txt", base_text + "gained-one\ngained-three\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("PASS", stdout)

    def test_removalonly_hunk_without_surviving_baseera_content_still_regression(self):
        base_text = "base-one\nbase-two\n"
        head_text = "gained-one\ngained-two\ngained-three\n"
        self._commit("app.txt", base_text, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", head_text, "head rewrites file")

        self._set_dirt("app.txt", "gained-one\ngained-three\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION", stdout)

    def test_removalonly_regression_keys_on_worktree_baseera_absence(self):
        base_text = "base-one\nbase-two\n"
        head_text = base_text + "gained-one\ngained-two\n"
        self._commit("app.txt", base_text, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", head_text, "head adds lines")

        # The worktree retains one gained line and removes both base-era lines.
        self._set_dirt("app.txt", "gained-one\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION", stdout)

    def test_pure_append_whole_reversion_still_regression(self):
        base_text = "base-one\nbase-two\n"
        head_text = base_text + "gained-one\ngained-two\n"
        self._commit("app.txt", base_text, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", head_text, "head appends lines")

        # Removing exactly the appended block restores the base file.
        self._set_dirt("app.txt", base_text)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION", stdout)

    def test_set_equal_list_unequal_worktree_passes(self):
        base_text = "p\nq\nr\ns\n"
        head_text = base_text + "g\n"
        self._commit("app.txt", base_text, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", head_text, "head appends a line")

        # Reorder base lines while deleting the gained append. The worktree's
        # set and multiset equal base, but its ordered line list does not.
        self._set_dirt("app.txt", "q\np\nr\ns\n")
        diff = self._git("diff", "HEAD", "--unified=0", "--", "app.txt")
        hunks: list[list[str]] = []
        for line in diff.splitlines():
            if line.startswith("@@"):
                hunks.append([])
            elif hunks and line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                hunks[-1].append(line)
        # The equality witness must be isolated from a mixed-restoration hunk.
        self.assertFalse(
            any(
                any(line.startswith("+") for line in hunk)
                and any(line.startswith("-") for line in hunk)
                for hunk in hunks
            ),
            diff,
        )
        self.assertTrue(
            any(
                "-g" in hunk and not any(line.startswith("+") for line in hunk)
                for hunk in hunks
            ),
            diff,
        )
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("PASS", stdout)

    def test_reverting_hunk_is_regression(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt restores the exact base-era file: a byte-identical whole-file
        # revert of content HEAD gained since the merge base.
        self._set_dirt("app.txt", BASE_TEXT)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn("dirt REGRESSION", stdout)
        self.assertIn("OUTCOME: fail", stdout)

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

    def test_removing_headgained_import_does_not_look_like_reversion(self):
        base_text = "class Example {}\n"
        head_text = "import java.util.List;\n" + base_text
        self._commit("Example.java", base_text, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("Example.java", head_text, "head adds import")

        # An unused-import cleanup removes a line HEAD gained, but does not
        # restore any base-era behavior.
        self._set_dirt("Example.java", base_text)
        code, stdout, stderr = self._run_gate(
            "--base", base_sha, "Example.java"
        )
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("PASS", stdout)

    def test_moving_headgained_line_between_hunks_does_not_look_like_reversion(self):
        base_text = "alpha\nbeta\ngamma\ndelta\nepsilon\nzeta\neta\ntheta\n"
        moved_line = "branch-added-line\n"
        self._commit("app.txt", base_text, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", moved_line + base_text, "head adds line")

        # Relocate the HEAD-gained line far enough that git emits separate
        # deletion and insertion hunks, while retaining the exact content.
        self._set_dirt("app.txt", base_text + moved_line)
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
        self.assertEqual(proc.returncode, 3)
        self.assertIn("not inside repository", proc.stderr)

    def test_missing_path_fails_closed(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        ghost = self.repo / "ghost.txt"
        proc_rc, proc_stdout, proc_stderr = self._run_gate(
            "--base", self._git("rev-parse", "HEAD").strip(), str(ghost)
        )
        proc = subprocess.CompletedProcess([], proc_rc, proc_stdout, proc_stderr)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("does not exist", proc.stderr)

    def test_regressive_whole_file_deletion_is_regression(self) -> None:
        base_sha = self._seed_head_gained_lines()
        (self.repo / "app.txt").unlink()
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1)
        self.assertIn("app.txt", stdout)

    def test_staged_regressive_whole_file_deletion_is_regression(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # Staged whole-file deletion (git rm: index removal, not a bare
        # unlink) of a file whose content HEAD gained: the staged shape
        # restores base-era text over lines HEAD gained, so the gate must
        # classify it as a regression, not a git-environment error.
        self._git("rm", "-q", "app.txt")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn("dirt REGRESSION", stdout)

    def test_neutral_whole_file_deletion_passes(self) -> None:
        self._commit("app.txt", BASE_TEXT, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", BASE_TEXT + "tail\n", "head changes a line")
        self._commit("app.txt", BASE_TEXT, "head restores base content")
        (self.repo / "app.txt").unlink()
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0)

    def test_staged_neutral_whole_file_deletion_passes(self) -> None:
        self._commit("app.txt", BASE_TEXT, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", BASE_TEXT + "tail\n", "head changes a line")
        self._commit("app.txt", BASE_TEXT, "head restores base content")
        # Mirror of test_neutral_whole_file_deletion_passes with the
        # deletion staged via git rm: the file's HEAD content already
        # equals base, so the staged deletion removes no HEAD-gained
        # lines and the gate passes.
        self._git("rm", "-q", "app.txt")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")

    def test_baseabsent_file_removalonly_hunk_passes(self) -> None:
        base_sha = self._seed_baseabsent_head_file()
        # The merge base lacks new.txt (the branch introduced it), so no
        # base-era text exists for a hunk to restore: deleting one
        # HEAD-gained line is an intentional forward refactor, not a
        # regression (the witnessed false-positive shape; today's vacuous
        # removal-only reading of the added-line condition flags it).
        self._set_dirt("new.txt", "one\ntwo\nthree\nfive\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "new.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: pass", stdout)

    def test_baseabsent_file_replacement_hunk_passes(self) -> None:
        base_sha = self._seed_baseabsent_head_file()
        # Same base-absent fixture with a HEAD-gained line replaced by new
        # text absent from every version: the non-vacuous added set already
        # passes today; pinned so the newly-introduced rule cannot regress it.
        self._set_dirt("new.txt", "one\ntwo-replaced\nthree\nfour\nfive\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "new.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: pass", stdout)

    def test_baseabsent_file_whole_deletion_is_regression(self) -> None:
        base_sha = self._seed_baseabsent_head_file()
        # Unstaged whole-file deletion of a base-absent file: every deleted
        # line is HEAD-gained by definition, so this is the maximal
        # regression shape (uncommitted loss of committed branch work),
        # distinct from the partial-edit removal-only hunk above, which
        # stays clean as intentional forward refactoring.
        (self.repo / "new.txt").unlink()
        code, stdout, stderr = self._run_gate("--base", base_sha, "new.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION", stdout)
        self.assertIn("new.txt", stdout)

    def test_baseabsent_file_staged_whole_deletion_is_regression(self) -> None:
        base_sha = self._seed_baseabsent_head_file()
        # Staged whole-file deletion (git rm: index removal) of a
        # base-absent file exercises the staged-deletion arm: the removal
        # classifies through the same HEAD-gained-lines rule as the
        # unstaged deletion, never as a pass.
        self._git("rm", "-q", "new.txt")
        code, stdout, stderr = self._run_gate("--base", base_sha, "new.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION", stdout)
        self.assertIn("new.txt", stdout)

    def test_emptybase_file_removalonly_hunk_still_regression(self) -> None:
        # The file EXISTS at the base with empty content: existence, not
        # base-set emptiness, decides newly-introduced classification, so a
        # removal-only hunk of HEAD-gained lines is still a regression here.
        self._commit("app.txt", "", "base with empty file")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("app.txt", HEAD_TEXT, "head gains lines")
        self._set_dirt("app.txt", "alpha\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn("dirt REGRESSION", stdout)

    def test_baseabsent_binary_dirt_stays_indeterminate(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        base_sha = self._git("rev-parse", "HEAD").strip()
        binary = self.repo / "new.bin"
        binary.write_bytes(b"\x00\x01\x02binary\n")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "head adds binary file")
        # Binary dirt on a base-absent file: the hunk-less indeterminate
        # shape check precedes the newly-introduced clean classification, so
        # an unmodelable diff shape still reports indeterminate, never a pass.
        binary.write_bytes(b"\x00\x01\x03changed\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "new.bin")
        self.assertEqual(code, 2, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt INDETERMINATE", stdout)
        self.assertIn("OUTCOME: indeterminate", stdout)

    def test_mixed_baseabsent_refactor_and_basepresent_revert_reports_regression(self) -> None:
        self._commit("app.txt", BASE_TEXT, "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self._commit("new.txt", "one\ntwo\nthree\nfour\nfive\n", "head adds new file")
        self._commit("app.txt", HEAD_TEXT, "head gains app lines")
        # One invocation over a base-absent forward refactor and a
        # base-present genuine revert: the revert still fails and only the
        # base-present path is named; the base-absent refactor is not.
        self._set_dirt("new.txt", "one\ntwo\nthree\nfive\n")
        self._set_dirt("app.txt", BASE_TEXT)
        code, stdout, stderr = self._run_gate(
            "--base", base_sha, "new.txt", "app.txt"
        )
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION: app.txt", stdout)
        self.assertNotIn("dirt REGRESSION: new.txt", stdout)
        self.assertIn("OUTCOME: fail", stdout)

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


    def test_binary_dirt_is_indeterminate(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # Dirt replaces the text file with binary bytes: the diff carries the
        # Binary files line and no hunks, the witnessed unmodeled shape.
        (self.repo / "app.txt").write_bytes(b"\x00\x01\x02binary\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 2, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt INDETERMINATE", stdout)
        self.assertIn("could not", stdout)
        self.assertIn("OUTCOME: indeterminate", stdout)

    def test_binary_dirt_with_mode_flip_is_indeterminate(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # Binary dirt riding a mode flip: the diff carries old/new mode lines
        # AND the Binary files line; the payload is still unclassifiable.
        target = self.repo / "app.txt"
        target.write_bytes(b"\x00\x01\x02binary\n")
        import os as _os
        _os.chmod(target, 0o755)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 2, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: indeterminate", stdout)

    def test_mode_change_dirt_stays_clean(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # A pure mode flip with no content change is a modeled hunk-less
        # shape and stays clean (the preserved known case).
        import os as _os
        _os.chmod(self.repo / "app.txt", 0o755)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: pass", stdout)

    def test_no_candidate_hunk_does_not_read_worktree(self) -> None:
        import contextlib
        import io
        from unittest.mock import patch

        import scripts.dirt_regression_gate as gate

        base_sha = self._seed_head_gained_lines()
        import os as _os
        _os.chmod(self.repo / "app.txt", 0o755)
        target = self.repo / "app.txt"
        read_text = Path.read_text
        original_cwd = Path.cwd()
        self.addCleanup(os.chdir, original_cwd)
        os.chdir(self.repo)

        def fail_worktree_read(path, *args, **kwargs):
            if path.resolve() == target.resolve():
                raise OSError("unexpected worktree read without candidate hunk")
            return read_text(path, *args, **kwargs)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.dict(os.environ, self._git_env()),
            patch.object(Path, "read_text", fail_worktree_read),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = gate.main(["--base", base_sha, "app.txt"])

        self.assertEqual(code, 0, stderr.getvalue())
        self.assertIn("OUTCOME: pass", stdout.getvalue())

    def test_mixed_regression_and_indeterminate_reports_indeterminate(self) -> None:
        base_sha = self._seed_head_gained_lines()
        self._commit("bin.dat", "text\n", "tracked binary candidate")
        # Mixed batch: one true regression plus one binary-restored TRACKED
        # path (an untracked path is invisible to git diff HEAD and is not a
        # gate input). Uncertainty dominates the verdict (exit 2) and both
        # evidence lines are still printed for the caller.
        self._set_dirt("app.txt", BASE_TEXT)
        (self.repo / "bin.dat").write_bytes(b"\x00\x01binary\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt", "bin.dat")
        self.assertEqual(code, 2, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION: app.txt", stdout)
        self.assertIn("dirt INDETERMINATE: bin.dat", stdout)
        self.assertIn("OUTCOME: indeterminate", stdout)

    def test_nonutf8_blob_is_tool_error(self) -> None:
        # A tracked blob git cannot decode as text is unsupported data: the
        # gate reports tool error, never a domain verdict (contract Terms).
        self._commit("seed.txt", "seed\n", "seed")
        blob = self.repo / "bin.dat"
        blob.write_bytes(b"\xff\xfe\x00binary\xff\n")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "binary blob")
        blob.write_bytes(b"\xff\xfe\x00binary\xff\nmore\n")
        code, stdout, stderr = self._run_gate("--base", "HEAD", "bin.dat")
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("unsupported data", stderr)
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_nonutf8_worktree_dirt_is_tool_error(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # NUL-free non-UTF-8 dirt: git diffs it as text, the gate cannot
        # decode the diff output, and the contract routes it to tool error.
        (self.repo / "app.txt").write_bytes(
            HEAD_TEXT.encode("utf-8") + b"caf\xe9-latin1\n"
        )
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("unsupported data", stderr)
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_worktree_read_error_is_tool_error(self) -> None:
        code, stdout, stderr = self._run_main_with_worktree_read_error(
            OSError("injected worktree read failure")
        )

        self.assertEqual(code, 3, stderr)
        self.assertIn("could not read worktree file", stderr)
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_worktree_decode_error_is_tool_error(self) -> None:
        code, stdout, stderr = self._run_main_with_worktree_read_error(
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        )

        self.assertEqual(code, 3, stderr)
        self.assertIn("could not read worktree file", stderr)
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_worktree_reader_uses_strict_utf8(self) -> None:
        import scripts.dirt_regression_gate as gate

        invalid_utf8 = self.tmp / "invalid-utf8.txt"
        invalid_utf8.write_bytes(b"valid prefix\n\xff\n")

        with self.assertRaisesRegex(RuntimeError, "could not read worktree file") as raised:
            gate._worktree_lines(invalid_utf8)

        self.assertIsInstance(raised.exception.__cause__, UnicodeDecodeError)

    def test_usage_error_is_tool_error(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        code, stdout, stderr = self._run_gate("--no-such-flag", "seed.txt")
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_missing_head_is_tool_error(self) -> None:
        empty = self.tmp / "empty-repo"
        empty.mkdir()
        self._git("init", "-q", "-b", "main", cwd=empty)
        (empty / "x.txt").write_text("x\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--base", "main", "x.txt"],
            capture_output=True,
            text=True,
            cwd=str(empty),
            env=self._git_env(),
        )
        self.assertEqual(proc.returncode, 3, f"stderr: {proc.stderr}")
        self.assertIn("OUTCOME: tool_error", proc.stdout)

    def test_unresolvable_base_is_tool_error(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        code, stdout, stderr = self._run_gate(
            "--base", "0" * 40, "seed.txt"
        )
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_outcome_final_line_pass(self) -> None:
        base_sha = self._seed_head_gained_lines()
        self._set_dirt("app.txt", HEAD_TEXT + "forward-note\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: pass", stdout)


if __name__ == "__main__":
    unittest.main()
