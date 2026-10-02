#!/usr/bin/env python3
"""Selftest for scripts/read_freshness_probe.py.

Every fixture is a scratch repository built inside a TemporaryDirectory with
its own git init, per-repo identity, and commits; every git invocation (probe
and fixture) is isolated from host state (GIT_CONFIG_GLOBAL / GIT_CONFIG_SYSTEM
pointed at /dev/null and the ambient git variable family unset).

Pinned classes (docs/history/plans/2026-10-02-evidence-integrity-fences.md,
Task 1): test_present_match, test_absent_mismatch, test_stale_mismatch (both
sub-cases: bytes equal the tip blob matches, bytes differing mismatch naming
the git probe), and test_unresolvable_path.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROBE_PATH = REPO_ROOT / "scripts" / "read_freshness_probe.py"

AMBIENT_GIT_VARS = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS", "GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE",
)


def probe_env():
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
                          env=probe_env())
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args[0], proc.stderr.decode()))
    return proc.stdout


class ScratchRepo:
    def __init__(self, tmp):
        self.root = Path(tmp) / "scratch"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "test@example.test")
        git(self.root, "config", "user.name", "Test")

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit_all(self, message):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", message)
        return git(self.root, "rev-parse", "HEAD").decode().strip()

    def head_time(self):
        return int(git(self.root, "show", "-s", "--format=%ct", "HEAD").decode().strip())


def run_probe(repo_root, claim, rel_path, cwd=None):
    return subprocess.run(
        [sys.executable, str(PROBE_PATH), "--repo", str(repo_root),
         "--path", rel_path, "--claim", claim],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=probe_env(), cwd=cwd)


class ReadFreshnessProbeTest(unittest.TestCase):

    def test_present_match(self):
        """A tracked file present in the worktree and at HEAD: match, exit 0."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/notes/plan.md", "plan body\n")
            repo.commit_all("add plan")
            proc = run_probe(repo.root, "present", "docs/notes/plan.md", cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            self.assertEqual(proc.stdout.decode().strip(), "match")

    def test_absent_mismatch(self):
        """A file present on disk but deleted at HEAD, claim absent: the
        filesystem probe contradicts the claim, mismatch names it, exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("tracked.txt", "tracked\n")
            repo.commit_all("base")
            repo.write("untracked.txt", "on disk only\n")
            proc = run_probe(repo.root, "absent", "untracked.txt", cwd=tmp)
            self.assertEqual(proc.returncode, 1, proc.stderr.decode())
            self.assertEqual(proc.stdout.decode().strip(), "mismatch: filesystem probe")

    def test_stale_mismatch(self):
        """Claim stale, both sub-cases.

        Sub-case 1: the worktree mtime predates the tip commit's timestamp
        while the bytes equal the tip blob, so the verdict is match. Sub-case
        2: the bytes differ from the tip blob while the mtime still predates
        the tip, so the verdict flips to mismatch naming the git probe (the
        byte comparison is the deciding command)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("log.md", "v1\n")
            repo.commit_all("v1")
            past = repo.head_time() - 100
            os.utime(repo.root / "log.md", (past, past))
            proc = run_probe(repo.root, "stale", "log.md", cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            self.assertEqual(proc.stdout.decode().strip(), "match")
            repo.write("log.md", "v2\n")
            os.utime(repo.root / "log.md", (past, past))
            proc = run_probe(repo.root, "stale", "log.md", cwd=tmp)
            self.assertEqual(proc.returncode, 1, proc.stderr.decode())
            self.assertEqual(proc.stdout.decode().strip(), "mismatch: git probe")

    def test_unresolvable_path(self):
        """A path unknown to both the filesystem and the tip commit:
        unresolvable, exit 2 (both the present and the absent claim)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("tracked.txt", "tracked\n")
            repo.commit_all("base")
            proc = run_probe(repo.root, "present", "ghost.txt", cwd=tmp)
            self.assertEqual(proc.returncode, 2, proc.stderr.decode())
            self.assertEqual(proc.stdout.decode().strip(), "unresolvable: ghost.txt")
            proc = run_probe(repo.root, "absent", "ghost.txt", cwd=tmp)
            self.assertEqual(proc.returncode, 2, proc.stderr.decode())
            self.assertEqual(proc.stdout.decode().strip(), "unresolvable: ghost.txt")


if __name__ == "__main__":
    unittest.main()
