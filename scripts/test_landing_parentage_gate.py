#!/usr/bin/env python3
"""Selftest for landing_parentage_gate.py: scratch-repo fixtures for every
refused shape and the green paths (exit 0 pass, 1 refuse, 2 tool failure)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "landing_parentage_gate.py"


def run(args, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, check=False, cwd=cwd, env=env,
    )


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run(
        ["git", "-C", str(root)] + list(args),
        capture_output=True, text=True, check=False, env=env,
    )
    assert proc.returncode == 0, (args, proc.stderr)
    return proc.stdout.strip()


def make_repo(path, files=20):
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "fixture")
    for i in range(files):
        (path / ("f%02d.txt" % i)).write_text("content %d\n" % i)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "init")
    return path


def commit_tree(root, tree, *parents):
    args = ["commit-tree", tree]
    for parent in parents:
        args += ["-p", parent]
    env = dict(os.environ)
    env.update({"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@example.invalid",
                "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@example.invalid"})
    proc = subprocess.run(["git", "-C", str(root)] + args,
                          input="orphan\n", capture_output=True, text=True,
                          check=False, env=env)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


class LandingParentageGateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        self.pre_tip = git(self.root, "rev-parse", "refs/heads/main")
        self.tree = git(self.root, "rev-parse", "HEAD^{tree}")

    def test_pre_swap_child_of_pre_tip_passes(self):
        new = commit_tree(self.root, self.tree, self.pre_tip)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: landing commit parentage verified", proc.stdout)

    def test_pre_swap_parentless_refuses(self):
        new = commit_tree(self.root, self.tree)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("refuse: landing commit is parentless", proc.stdout)

    def test_pre_swap_wrong_parent_refuses(self):
        git(self.root, "checkout", "-q", "-b", "side")
        (self.root / "side.txt").write_text("side\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "side")
        side = git(self.root, "rev-parse", "refs/heads/side")
        new = commit_tree(self.root, self.tree, side)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not equal pre-landing tip", proc.stdout)

    def test_pre_swap_merge_commit_refuses(self):
        git(self.root, "checkout", "-q", "-b", "side")
        (self.root / "side.txt").write_text("side\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "side")
        side = git(self.root, "rev-parse", "refs/heads/side")
        new = commit_tree(self.root, self.tree, self.pre_tip, side)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("refuse: landing commit has 2 parents", proc.stdout)

    def test_pre_swap_unresolvable_new_commit_refuses(self):
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", "deadbeef" * 5])
        self.assertEqual(proc.returncode, 1)

    def test_pre_swap_unresolvable_pre_tip_is_tool_failure(self):
        new = commit_tree(self.root, self.tree, self.pre_tip)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", "deadbeef" * 5, "--new-commit", new])
        self.assertEqual(proc.returncode, 2)

    def test_post_landing_descendant_passes(self):
        new = commit_tree(self.root, self.tree, self.pre_tip)
        git(self.root, "update-ref", "refs/heads/main", new)
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "main"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: default branch ancestry verified", proc.stdout)

    def test_post_landing_severed_refuses(self):
        orphan = commit_tree(self.root, self.tree)
        git(self.root, "update-ref", "refs/heads/main", orphan)
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "main"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            "refuse: default branch no longer descends from pre-landing tip",
            proc.stdout)

    def test_post_landing_origin_ref_passes_and_refuses(self):
        git(self.root, "update-ref", "refs/remotes/origin/main", self.pre_tip)
        # Refuse case: origin at the pre-orphan base, main severed.
        orphan = commit_tree(self.root, self.tree)
        git(self.root, "update-ref", "refs/heads/main", orphan)
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "main",
                    "--origin-ref", "origin/main"])
        self.assertEqual(proc.returncode, 1)
        self.assertIn("refuse: default branch no longer descends from origin/main",
                      proc.stdout)
        # Green path: a fresh pre-tip child on main with origin repointed at
        # an ancestor of main passes both legs (exercises the origin-leg ok).
        child = commit_tree(self.root, self.tree, self.pre_tip)
        git(self.root, "update-ref", "refs/heads/main", child)
        git(self.root, "update-ref", "refs/remotes/origin/main", self.pre_tip)
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "main",
                    "--origin-ref", "origin/main"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: default branch ancestry verified", proc.stdout)

    def test_post_landing_absent_origin_ref_skips(self):
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "main",
                    "--origin-ref", "origin/main"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("note: origin ref origin/main absent; ancestry leg skipped",
                      proc.stdout)

    def test_post_landing_unresolvable_pre_tip_is_tool_failure(self):
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", "deadbeef" * 5, "--default-ref", "main"])
        self.assertEqual(proc.returncode, 2)

    def test_post_landing_unresolvable_default_ref_is_tool_failure(self):
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "nosuchbranch"])
        self.assertEqual(proc.returncode, 2)

    def test_post_landing_plumbing_failure_is_tool_failure(self):
        not_a_repo = Path(self._tmp.name) / "notarepo"
        not_a_repo.mkdir()
        proc = run(["post-landing", "--repo", str(not_a_repo),
                    "--pre-tip", self.pre_tip, "--default-ref", "main"])
        self.assertEqual(proc.returncode, 2)

    def test_post_landing_both_legs_drop_prints_both_refuse_lines(self):
        git(self.root, "update-ref", "refs/remotes/origin/main", self.pre_tip)
        orphan = commit_tree(self.root, self.tree)
        git(self.root, "update-ref", "refs/heads/main", orphan)
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "main",
                    "--origin-ref", "origin/main"])
        self.assertEqual(proc.returncode, 1)
        pre_line = proc.stdout.index(
            "refuse: default branch no longer descends from pre-landing tip")
        origin_line = proc.stdout.index(
            "refuse: default branch no longer descends from origin/main")
        self.assertLess(pre_line, origin_line)


if __name__ == "__main__":
    unittest.main(verbosity=1)
