#!/usr/bin/env python3
"""Selftest for prestage_freshness_gate.py: scratch-repo fixtures for every
refused shape and the green paths (exit 0 pass, 1 refuse, 2 tool failure)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "prestage_freshness_gate.py"


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


def make_repo(path):
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "fixture")
    return path


def commit_file(root, rel, content, message):
    (root / rel).write_text(content)
    git(root, "add", rel)
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "refs/heads/main")


class PrestageFreshnessGateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        self.v1_sha = commit_file(self.root, "file.txt", "v1\n", "v1")

    def test_fresh_path_passes(self):
        # Committed file with identical disk bytes: both blobs exist and match.
        proc = run(["check", "--repo", str(self.root), "--", "file.txt"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: file.txt", proc.stdout)
        self.assertIn("ok: all candidate paths fresh against HEAD", proc.stdout)

    def test_stale_ancestor_match_refuses_naming_ancestor(self):
        # Advance HEAD past v1 with a second commit, then rewrite the disk
        # bytes back to v1's content: the disk blob equals the v1 blob.
        v2_sha = commit_file(self.root, "file.txt", "v2\n", "v2")
        (self.root / "file.txt").write_text("v1\n")
        proc = run(["check", "--repo", str(self.root), "--", "file.txt"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        expected = ("refuse: file.txt disk bytes equal ancestor %s, not HEAD %s"
                    % (self.v1_sha, v2_sha))
        self.assertIn(expected, proc.stdout)

    def test_session_owned_fresh_write_passes(self):
        # A new untracked file listed in the fresh list passes; the list
        # parser tolerates comment lines and blank lines.
        (self.root / "new.txt").write_text("fresh work\n")
        fresh_list = self.root / "fresh-writes.txt"
        fresh_list.write_text("# session-owned fresh writes\n\nnew.txt\n")
        proc = run(["check", "--repo", str(self.root),
                    "--fresh-list", str(fresh_list), "--", "new.txt"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: new.txt", proc.stdout)
        self.assertIn("ok: all candidate paths fresh against HEAD", proc.stdout)

    def test_unlisted_untracked_refuses(self):
        # A new untracked file absent from the fresh list is refused.
        (self.root / "other.txt").write_text("unlisted work\n")
        fresh_list = self.root / "fresh-writes.txt"
        fresh_list.write_text("# session-owned fresh writes\nnew.txt\n")
        proc = run(["check", "--repo", str(self.root),
                    "--fresh-list", str(fresh_list), "--", "other.txt"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(
            "refuse: other.txt disk bytes match neither HEAD nor the session-owned fresh list",
            proc.stdout)

    def test_modified_bytes_match_no_ancestor_refuses(self):
        # Disk bytes differing from HEAD and from every ancestor blob.
        commit_file(self.root, "file.txt", "v2\n", "v2")
        (self.root / "file.txt").write_text("totally different\n")
        proc = run(["check", "--repo", str(self.root), "--", "file.txt"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(
            "refuse: file.txt disk bytes match neither HEAD nor the session-owned fresh list",
            proc.stdout)

    def test_unresolvable_head_is_tool_failure(self):
        bogus = "deadbeef" * 5
        proc = run(["check", "--repo", str(self.root), "--head", bogus,
                    "--", "file.txt"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn(
            "prestage-freshness-gate tool failure: head unresolvable: %s" % bogus,
            proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
