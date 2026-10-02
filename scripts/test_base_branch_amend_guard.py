#!/usr/bin/env python3
"""Selftest for scripts/base_branch_amend_guard.py.

Every fixture is a scratch repository built inside a TemporaryDirectory with
its own git init (fixed branch name `main`), per-repo identity, and commits;
every git invocation (guard and fixture) is isolated from host state
(GIT_CONFIG_GLOBAL / GIT_CONFIG_SYSTEM pointed at /dev/null and the ambient
git variable family unset).

Pinned classes (docs/history/plans/2026-10-02-evidence-integrity-fences.md,
Task 3): test_check_head_refuses_base_amend,
test_check_head_allows_branch_amend, test_reflog_scan_reports_foreign_amend,
test_reflog_scan_allows_landing_authored_amend, and test_reflog_scan_clean.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = REPO_ROOT / "scripts" / "base_branch_amend_guard.py"

AMBIENT_GIT_VARS = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS", "GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE",
)


def guard_env():
    env = dict(os.environ)
    for var in AMBIENT_GIT_VARS:
        env.pop(var, None)
    for key in list(env):
        if re.match(r"^GIT_CONFIG_(KEY|VALUE)_\d+$", key):
            env.pop(key, None)
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    return env


def git(root, *args):
    proc = subprocess.run(["git", "-C", str(root)] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=guard_env())
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args[0], proc.stderr.decode()))
    return proc.stdout


def run_guard(*argv, cwd=None):
    return subprocess.run(
        [sys.executable, str(GUARD_PATH)] + list(argv),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=guard_env(), cwd=cwd)


class ScratchRepo:
    def __init__(self, tmp):
        self.root = Path(tmp) / "scratch"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.email", "test@example.test")
        git(self.root, "config", "user.name", "Test")
        # Seed one tracked file so the first commit_all has content; an
        # empty-tree commit is refused by git ("nothing to commit").
        (self.root / "seed.txt").write_text("seed\n")

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit_all(self, message):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", message)
        return git(self.root, "rev-parse", "HEAD").decode().strip()

    def amend_head(self, message):
        git(self.root, "commit", "--amend", "-qm", message)
        return git(self.root, "rev-parse", "HEAD").decode().strip()

    def amend_rows(self, stdout):
        return [line for line in stdout.decode().splitlines()
                if line.startswith("amend-entry ")]


class BaseBranchAmendGuardTest(unittest.TestCase):

    def test_check_head_refuses_base_amend(self):
        """HEAD is the base branch and the last reflog entry is
        `commit (amend)`: the guard refuses with exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            repo.amend_head("base with one extra line")
            proc = run_guard("check-head", "--base-branch", "main",
                             cwd=repo.root)
            self.assertEqual(proc.returncode, 1, proc.stderr.decode())
            self.assertIn("commit (amend)", proc.stdout.decode())

    def test_check_head_allows_branch_amend(self):
        """HEAD is a session's own feature branch with an amend reflog
        entry: the guard does not refuse, exit 0."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            git(repo.root, "checkout", "-qb", "feature")
            repo.write("feature.txt", "feature work\n")
            repo.commit_all("feature work")
            repo.amend_head("feature work amended")
            proc = run_guard("check-head", "--base-branch", "main",
                             cwd=repo.root)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            self.assertNotIn("amend-entry", proc.stdout.decode())

    def test_reflog_scan_reports_foreign_amend(self):
        """An amend entry on the base branch reflog after the since sha with
        no matching --allow-sha: exit 1 and one report row naming the entry."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            pre_tip = repo.commit_all("landed base tip")
            foreign = repo.amend_head("landed base tip, amended by a peer")
            proc = run_guard("reflog-scan", "--repo", str(repo.root),
                             "--base-branch", "main", "--since", pre_tip)
            self.assertEqual(proc.returncode, 1, proc.stderr.decode())
            rows = repo.amend_rows(proc.stdout)
            self.assertEqual(len(rows), 1, proc.stdout.decode())
            self.assertIn(foreign, rows[0])
            self.assertIn("commit (amend)", rows[0])

    def test_reflog_scan_allows_landing_authored_amend(self):
        """The same amend entry with its new commit passed via --allow-sha:
        the landing-authored amend is not reported, exit 0."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            pre_tip = repo.commit_all("landed base tip")
            foreign = repo.amend_head("landed base tip, amended by a peer")
            proc = run_guard("reflog-scan", "--repo", str(repo.root),
                             "--base-branch", "main", "--since", pre_tip,
                             "--allow-sha", foreign)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            self.assertEqual(repo.amend_rows(proc.stdout), [])

    def test_reflog_scan_clean(self):
        """Only ordinary commits after the since sha: exit 0 and no rows."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            pre_tip = repo.commit_all("landed base tip")
            repo.write("second.txt", "second\n")
            repo.commit_all("additive second")
            repo.write("third.txt", "third\n")
            repo.commit_all("additive third")
            proc = run_guard("reflog-scan", "--repo", str(repo.root),
                             "--base-branch", "main", "--since", pre_tip)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            self.assertEqual(repo.amend_rows(proc.stdout), [])


if __name__ == "__main__":
    unittest.main()
