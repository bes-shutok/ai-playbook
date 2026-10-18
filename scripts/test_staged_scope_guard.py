#!/usr/bin/env python3
"""Suite for scripts/staged_scope_guard.py over fixture repositories.

Every test builds a throwaway git repo, stages the fixture shape, and runs
the guard as a subprocess against it, so the suite exercises the real
NUL-delimited parse and exit behavior, not a mock.
"""

import os
import subprocess
import sys
import tempfile
import unittest

GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "staged_scope_guard.py")


def run(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


class FixtureRepo:
    def __init__(self):
        self.path = tempfile.mkdtemp(prefix="staged-scope-guard-fixture-")
        run(["git", "init", "-q"], self.path)
        run(["git", "config", "user.email", "fixture@example.com"], self.path)
        run(["git", "config", "user.name", "fixture"], self.path)
        for name in ("keep.txt", "backlog-new.md", "unrelated.txt", "preexisting.txt", "space path.txt"):
            self.write(name, f"original {name}\n")
        run(["git", "add", "-A"], self.path)
        run(["git", "commit", "-q", "-m", "baseline"], self.path)

    def write(self, name, content):
        with open(os.path.join(self.path, name), "w") as fh:
            fh.write(content)

    def git(self, *args):
        return run(["git"] + list(args), self.path)

    def guard(self, *includes):
        return run([sys.executable, GUARD, "--repo", self.path]
                   + [f"--include={i}" for i in includes], self.path)


class StagedScopeGuardTests(unittest.TestCase):
    def setUp(self):
        self.repo = FixtureRepo()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo.path])

    def test_unrelated_staged_deletion_refuses(self):
        # The witnessed shape: the index carries a deletion of an unrelated
        # tracked file; the declared set is only the new backlog path.
        self.repo.git("rm", "-q", "--cached", "unrelated.txt")
        result = self.repo.guard("docs/history/backlog/backlog-new.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("D unrelated.txt", result.stdout)
        self.assertIn("OUTCOME: fail", result.stdout)

    def test_unrelated_staged_modification_refuses(self):
        self.repo.write("unrelated.txt", "modified\n")
        self.repo.git("add", "unrelated.txt")
        result = self.repo.guard("docs/history/backlog/backlog-new.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("M unrelated.txt", result.stdout)
        self.assertIn("OUTCOME: fail", result.stdout)

    def test_rename_consumes_both_sides(self):
        # Both rename sides outside the declared set: refusal names both,
        # origin before destination.
        self.repo.git("mv", "unrelated.txt", "renamed.txt")
        result = self.repo.guard("docs/history/backlog/backlog-new.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        origin_at = result.stdout.index("R100 unrelated.txt")
        destination_at = result.stdout.index("renamed.txt", origin_at)
        self.assertLess(origin_at, destination_at)
        # Origin inside, destination outside: the symmetric any-side
        # membership rule passes the entry...
        self.repo.git("reset", "-q", "--hard")
        self.repo.git("mv", "keep.txt", "renamed.txt")
        result = self.repo.guard("keep.txt")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OUTCOME: pass", result.stdout)
        # ...while the same rename against an unrelated declared set refuses
        # naming the destination (origin first).
        result = self.repo.guard("docs/history/backlog/backlog-new.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        origin_at = result.stdout.index("R100 keep.txt")
        destination_at = result.stdout.index("renamed.txt", origin_at)
        self.assertLess(origin_at, destination_at)

    def test_paths_with_spaces_round_trip(self):
        self.repo.write("space path.txt", "modified\n")
        self.repo.git("add", "space path.txt")
        result = self.repo.guard("space path.txt")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.repo.git("reset", "-q", "--hard")
        self.repo.write("space path.txt", "modified again\n")
        self.repo.git("add", "space path.txt")
        result = self.repo.guard("backlog-new.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("M space path.txt", result.stdout)

    def test_exact_set_passes_and_empty_set_passes(self):
        self.repo.write("backlog-new.md", "new row\n")
        self.repo.git("add", "backlog-new.md")
        result = self.repo.guard("backlog-new.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("compared 1 staged entries", result.stdout)
        self.assertIn("OUTCOME: pass", result.stdout)
        # Empty staged set passes vacuously.
        self.repo.git("reset", "-q")
        result = self.repo.guard("backlog-new.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # Missing --include is a usage violation.
        result = run([sys.executable, GUARD, "--repo", self.repo.path], self.repo.path)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("OUTCOME: tool_error", result.stdout)

    def test_guard_mutates_nothing(self):
        self.repo.git("rm", "-q", "--cached", "unrelated.txt")
        before_status = self.repo.git("status", "--porcelain").stdout
        before_files = self.repo.git("ls-files", "-s").stdout
        result = self.repo.guard("backlog-new.md")
        self.assertEqual(result.returncode, 1)
        after_status = self.repo.git("status", "--porcelain").stdout
        after_files = self.repo.git("ls-files", "-s").stdout
        self.assertEqual(before_status, after_status)
        self.assertEqual(before_files, after_files)


if __name__ == "__main__":
    unittest.main()
