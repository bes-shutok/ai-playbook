#!/usr/bin/env python3
"""Selftest for revert_set_classifier.py: scratch-repo fixtures for every
contract arm (staged/unstaged vintage transplants, staged/unstaged deletions
of HEAD-added paths, foreign edits and deletions, mixed partial sets, clean
checkouts, untracked paths, --path restriction, non-ASCII paths, unresolvable
head)."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "revert_set_classifier.py"


def run(args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, check=False, env=env,
    )


def run_with_shim(args, shim_dir):
    """run() with a directory prepended to PATH (a git plumbing-failure
    shim: the classifier's git calls resolve through it)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["PATH"] = str(shim_dir) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, check=False, env=env,
    )


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run(
        ["git", "-C", str(root)] + list(args),
        capture_output=True, text=True, check=False, env=env,
    )
    assert proc.returncode == 0, (args, proc.stderr)
    return proc.stdout.strip()


def make_repo(path):
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "fixture")
    return path


def commit_file(root, rel, content, message):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    git(root, "add", rel)
    git(root, "commit", "-q", "-m", message)


class RevertSetClassifierTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        commit_file(self.root, "a.txt", "v1\n", "v1")
        self.v1 = git(self.root, "rev-parse", "HEAD")
        commit_file(self.root, "a.txt", "v2\n", "v2")
        commit_file(self.root, "b.txt", "b\n", "add b")

    def test_staged_vintage_transplant_is_pure_reversal(self):
        git(self.root, "checkout", "-q", self.v1, "--", "a.txt")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(
            "reversal: a.txt dirty state equals ancestor %s vintage" % self.v1,
            proc.stdout)
        self.assertIn("revert-set: pure", proc.stdout)

    def test_unstaged_vintage_transplant_is_pure_reversal(self):
        (self.root / "a.txt").write_text("v1\n")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("reversal: a.txt", proc.stdout)
        self.assertIn("revert-set: pure", proc.stdout)

    def test_staged_deletion_of_head_added_path_is_pure_reversal(self):
        git(self.root, "rm", "-q", "b.txt")
        add_b = git(self.root, "log", "--diff-filter=A", "--format=%H",
                    "--", "b.txt")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(
            "reversal: b.txt deletion reverts the addition at %s" % add_b,
            proc.stdout)
        self.assertIn("revert-set: pure", proc.stdout)

    def test_unstaged_deletion_of_head_added_path_is_pure_reversal(self):
        (self.root / "b.txt").unlink()
        add_b = git(self.root, "log", "--diff-filter=A", "--format=%H",
                    "--", "b.txt")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("deletion reverts the addition at %s" % add_b,
                      proc.stdout)
        self.assertIn("revert-set: pure", proc.stdout)

    def test_fresh_foreign_edit_is_foreign_exit_0(self):
        (self.root / "a.txt").write_text("fresh work\n")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("foreign: a.txt dirty state matches no ancestor vintage",
                      proc.stdout)
        self.assertIn("revert-set: partial", proc.stdout)

    def test_mixed_vintage_plus_foreign_is_partial_exit_1(self):
        (self.root / "a.txt").write_text("v1\n")
        (self.root / "b.txt").write_text("fresh work\n")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("reversal: a.txt", proc.stdout)
        self.assertIn("foreign: b.txt", proc.stdout)
        self.assertIn("revert-set: partial", proc.stdout)
        self.assertNotIn("revert-set: pure", proc.stdout)

    def test_clean_checkout_is_none_exit_0(self):
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("revert-set: none", proc.stdout)

    def test_untracked_only_is_foreign_exit_0(self):
        (self.root / "new.txt").write_text("untracked\n")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("foreign: new.txt untracked (never reversal damage)",
                      proc.stdout)
        self.assertIn("revert-set: partial", proc.stdout)

    def test_path_restriction_scopes_rows_and_summary(self):
        git(self.root, "checkout", "-q", self.v1, "--", "a.txt")
        proc = run(["classify", "--repo", str(self.root), "--path", "a.txt",
                    "--path", "b.txt"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("reversal: a.txt", proc.stdout)
        self.assertIn("clean: b.txt", proc.stdout)
        self.assertIn("revert-set: pure", proc.stdout)

    def test_non_ascii_path_row_names_unquoted_path(self):
        name = "файл-Ω.txt"
        commit_file(self.root, name, "body\n", "add unicode path")
        (self.root / name).write_text("v1-body\n")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("foreign: %s" % name, proc.stdout)
        self.assertNotIn('"', proc.stdout)

    def test_foreign_deletion_via_path_on_absent_everywhere(self):
        proc = run(["classify", "--repo", str(self.root), "--path",
                    "never/existed.txt"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("foreign: never/existed.txt deletion matches no "
                      "reachable addition", proc.stdout)
        self.assertIn("revert-set: none", proc.stdout)

    def test_staged_rename_classifies_once_no_phantom_paths(self):
        # git mv produces R<new> + <old> NUL records; the old path is
        # consumed as data and no phantom path may be fabricated.
        git(self.root, "mv", "b.txt", "b-renamed.txt")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertNotIn("clean: xt", proc.stdout)
        self.assertIn("reversal: b.txt deletion reverts the addition at",
                      proc.stdout)
        self.assertIn("foreign: b-renamed.txt dirty state matches no ancestor vintage",
                      proc.stdout)
        self.assertIn("revert-set: partial", proc.stdout)

    def test_staged_rename_into_subdir_no_phantom_exit_2(self):
        # The reviewer's live repro: a rename whose old path is nested;
        # a phantom "/keep.txt" would make ls-tree fail and exit 2.
        (self.root / "sub").mkdir()
        git(self.root, "mv", "b.txt", "sub/keep.txt")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertNotIn("foreign: /keep.txt", proc.stdout)
        self.assertNotIn("tool failure", proc.stderr)
        self.assertIn("foreign: sub/keep.txt dirty state matches no ancestor vintage",
                      proc.stdout)

    def test_staged_foreign_edit_on_non_ascii_path_is_foreign(self):
        # ls-files C-quoting must never misread a staged non-ASCII path's
        # state as a staged deletion (which would fabricate pure reversal).
        name = "\u0444\u0430\u0439\u043b.txt"
        commit_file(self.root, name, "body\n", "add cyrillic file")
        git(self.root, "checkout", "-q", self.v1, "--", "a.txt")
        (self.root / name).write_text("foreign edit\n")
        git(self.root, "add", name)
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("reversal: a.txt", proc.stdout)
        self.assertIn("foreign: %s dirty state matches no ancestor vintage"
                      % name, proc.stdout)
        self.assertIn("revert-set: partial", proc.stdout)
        self.assertNotIn("revert-set: pure", proc.stdout)

    # ------------------------------------------------------------------
    # Outcome-contract arms (scripts/OUTCOME_CONTRACT.md): the four-outcome
    # vocabulary under the answer-vocabulary criterion, exactly one final
    # `OUTCOME:` line per non-metadata run, the retired tool-failure prefix.
    # ------------------------------------------------------------------
    def assert_single_final_outcome(self, proc, label):
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        self.assertTrue(lines, "no stdout lines: %r" % proc.stderr)
        self.assertEqual(
            lines[-1], "OUTCOME: %s" % label,
            "final stdout line must be the OUTCOME line, stdout: %s"
            % proc.stdout)
        self.assertEqual(
            sum(1 for line in lines if line.startswith("OUTCOME:")), 1,
            "exactly one OUTCOME line expected, stdout: %s" % proc.stdout)

    def test_clean_checkout_outcome_pass(self):
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("revert-set: none", proc.stdout)
        self.assert_single_final_outcome(proc, "pass")

    def test_pure_reversal_outcome_fail_with_summary(self):
        (self.root / "a.txt").write_text("v1\n")
        proc = run(["classify", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("reversal: a.txt", proc.stdout)
        self.assertIn("revert-set: pure", proc.stdout)
        self.assert_single_final_outcome(proc, "fail")

    def test_bad_repo_is_tool_error(self):
        proc = run(["classify", "--repo",
                    str(Path(self._tmp.name) / "no-such-repo")])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("head unresolvable", proc.stderr)
        self.assertNotIn("revert-set-classifier tool failure:", proc.stderr)
        self.assert_single_final_outcome(proc, "tool_error")

    def test_unresolvable_head_ref_is_tool_error(self):
        proc = run(["classify", "--repo", str(self.root), "--head",
                    "nosuchref"])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("head unresolvable: nosuchref", proc.stderr)
        self.assertNotIn("revert-set-classifier tool failure:", proc.stderr)
        self.assert_single_final_outcome(proc, "tool_error")

    def test_usage_violation_is_tool_error(self):
        proc = run([])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("OUTCOME: tool_error", proc.stderr)

    def test_plumbing_failure_over_resolved_inputs_is_indeterminate(self):
        # Repo and HEAD resolve through the shimmed git; the addition lookup
        # (git log --diff-filter=A) answers outside its 0/1 vocabulary
        # mid-walk: the answer-vocabulary criterion classifies that as
        # indeterminate (exit 2), never as a reversal finding and never as
        # the retired tool-failure shape.
        git(self.root, "rm", "-q", "b.txt")
        real_git = shutil.which("git")
        shim = Path(self._tmp.name) / "git-shim"
        shim.mkdir()
        script = shim / "git"
        script.write_text(
            "#!/bin/sh\n"
            'for a in "$@"; do\n'
            '  if [ "$a" = "--diff-filter=A" ]; then exit 1; fi\n'
            "done\n"
            'exec "%s" "$@"\n' % real_git,
            encoding="utf-8",
        )
        script.chmod(0o755)
        proc = run_with_shim(["classify", "--repo", str(self.root)], shim)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("addition lookup failed for b.txt", proc.stderr)
        self.assertNotIn("tool failure", proc.stderr)
        self.assert_single_final_outcome(proc, "indeterminate")


if __name__ == "__main__":
    unittest.main()
