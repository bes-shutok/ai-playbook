#!/usr/bin/env python3
"""Selftest for the squash-landing tree-equality gate mechanics: scratch-repo
fixtures proving `git diff --quiet <branch> <squash-commit>` refuses the
witnessed divergence (the squash commit's tree carrying a path the squashed
branch tip dropped) while never false-positiving on legitimate branch-side
content changes."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PLAN = "docs/history/plans/2026-10-02-example.md"
ARCHIVE = "docs/history/plans/completed/2026-10-02-example.md"


def git(root, *args, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run(
        ["git", "-C", str(root)] + list(args),
        capture_output=True, text=True, check=False, env=env,
    )
    if check:
        assert proc.returncode == 0, (args, proc.stderr)
    return proc


def make_repo(path):
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "fixture")
    return path


def commit(root, message):
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD").stdout.strip()


def tree_diff(root, branch, squash):
    quiet = git(root, "diff", "--quiet", branch, squash, check=False)
    names = git(root, "diff", "--name-only", branch, squash).stdout.split()
    return quiet.returncode, names


class SquashTreeEqualityTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        (self.root / PLAN).parent.mkdir(parents=True)
        (self.root / PLAN).write_text("plan body v1\n")
        git(self.root, "add", PLAN)
        self.base = commit(self.root, "base: add plan")

    def _branch_rename(self, content=None):
        git(self.root, "checkout", "-q", "-b", "exec/plan")
        target = self.root / ARCHIVE
        target.parent.mkdir(parents=True)
        body = "plan body v1\n" if content is None else content
        target.write_text(body)
        git(self.root, "add", ARCHIVE)
        git(self.root, "rm", "-q", PLAN)
        commit(self.root, "exec: archive plan")
        git(self.root, "checkout", "-q", "main")

    def _squash(self):
        git(self.root, "merge", "--squash", "exec/plan")
        return commit(self.root, "land: squash the branch")

    def test_clean_squash_tree_equals_branch_tip(self):
        self._branch_rename()
        squash = self._squash()
        rc, names = tree_diff(self.root, "exec/plan", squash)
        self.assertEqual(rc, 0)
        self.assertEqual(names, [])

    def test_witnessed_divergence_stale_source_readded_refuses(self):
        self._branch_rename()
        git(self.root, "merge", "--squash", "exec/plan")
        # The deletion half of the rename is dropped: the stale pre-execution
        # root copy is re-added into the landing commit before it is created.
        (self.root / PLAN).write_text("plan body v1\n")
        git(self.root, "add", PLAN)
        squash = commit(self.root, "land: squash with stale root copy")
        rc, names = tree_diff(self.root, "exec/plan", squash)
        self.assertEqual(rc, 1)
        self.assertIn(PLAN, names)

    def test_byte_divergence_on_same_path_set_refuses(self):
        self._branch_rename()
        git(self.root, "merge", "--squash", "exec/plan")
        (self.root / ARCHIVE).write_text("mutated bytes\n")
        git(self.root, "add", ARCHIVE)
        squash = commit(self.root, "land: squash with diverged bytes")
        rc, names = tree_diff(self.root, "exec/plan", squash)
        self.assertEqual(rc, 1)
        self.assertEqual(names, [ARCHIVE])

    def test_rename_with_content_change_clean_squash_passes(self):
        self._branch_rename(content="plan body v2 with edits\n")
        squash = self._squash()
        rc, names = tree_diff(self.root, "exec/plan", squash)
        self.assertEqual(rc, 0)
        self.assertEqual(names, [])
        # Negative control: a landing that drops the branch's edit refuses.
        self_root = self.root
        git(self_root, "reset", "-q", "--hard", self.base)
        git(self_root, "merge", "--squash", "exec/plan")
        (self_root / ARCHIVE).write_text("plan body v1\n")
        git(self_root, "add", ARCHIVE)
        squash = commit(self_root, "land: squash dropping the branch edit")
        rc, names = tree_diff(self_root, "exec/plan", squash)
        self.assertEqual(rc, 1)
        self.assertEqual(names, [ARCHIVE])


if __name__ == "__main__":
    unittest.main()
