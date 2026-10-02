#!/usr/bin/env python3
"""Selftest for prestage_freshness_gate.py: scratch-repo fixtures for every
refused shape and the green paths, plus the outcome contract's four-outcome
fixtures (0 pass, 1 fail, 2 indeterminate, 3 tool error; final `OUTCOME:`
line per non-metadata run)."""

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

    def test_unresolvable_head_is_tool_error(self):
        bogus = "deadbeef" * 5
        proc = run(["check", "--repo", str(self.root), "--head", bogus,
                    "--", "file.txt"])
        self.assertEqual(proc.returncode, 3)
        self.assertIn(
            "prestage-freshness-gate tool error: head unresolvable: %s" % bogus,
            proc.stderr)


class PrestageFreshnessGateOutcomeTest(unittest.TestCase):
    """Outcome-contract fixtures (plan 2026-10-03-outcome-contract-migration-
    batch-1 Task 1): every non-metadata run ends with exactly one final
    `OUTCOME:` line; the NEW explicit type check (HEAD tree mode type versus
    disk lstat type) is indeterminate (exit 2) ahead of the byte comparison;
    an unresolvable head, an unreadable fresh list, or a usage error is tool
    error (exit 3); `--help` stays metadata-exempt."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        self.v1_sha = commit_file(self.root, "file.txt", "v1\n", "v1")

    @staticmethod
    def _outcome_lines(proc):
        return [line for line in proc.stdout.splitlines()
                if line.startswith("OUTCOME:")]

    def test_pass_emits_single_final_outcome_pass(self):
        proc = run(["check", "--repo", str(self.root), "--", "file.txt"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: pass"])
        self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: pass"))

    def test_refuse_emits_outcome_fail_with_evidence(self):
        commit_file(self.root, "file.txt", "v2\n", "v2")
        (self.root / "file.txt").write_text("v1\n")
        proc = run(["check", "--repo", str(self.root), "--", "file.txt"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("refuse: file.txt", proc.stdout)
        self.assertLess(proc.stdout.index("refuse:"),
                        proc.stdout.index("OUTCOME:"))

    def test_unresolvable_head_is_tool_error(self):
        # Legacy: exit 2 (tool failure). Contract: exit 3.
        bogus = "deadbeef" * 5
        proc = run(["check", "--repo", str(self.root), "--head", bogus,
                    "--", "file.txt"])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: tool_error"])

    def test_unreadable_fresh_list_is_tool_error(self):
        # Legacy: exit 2 (tool failure). Contract: an unreadable input is
        # tool error (exit 3).
        proc = run(["check", "--repo", str(self.root),
                    "--fresh-list", str(self.root / "no-such-list.txt"),
                    "--", "file.txt"])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: tool_error"])

    def test_dangling_symlink_typechange_is_indeterminate(self):
        # Legacy behavior for the same input: a stale refuse at exit 1 (the
        # dangling symlink's target does not exist, so the byte comparison
        # never passes). Contract: the NEW explicit type check ahead of the
        # byte comparison reports indeterminate (exit 2) naming the path.
        commit_file(self.root, "file.txt", "v2\n", "v2")
        (self.root / "file.txt").unlink()
        os.symlink("no-such-target.txt", self.root / "file.txt")
        proc = run(["check", "--repo", str(self.root), "--", "file.txt"])
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: indeterminate"])
        # The indeterminate evidence names the path and the type disagreement
        # (the gate's diagnostic stream carries it; the OUTCOME line stdout).
        self.assertIn("file.txt", proc.stdout + proc.stderr)
        self.assertIn("type", proc.stdout + proc.stderr)

    def test_symlink_with_matching_target_bytes_is_indeterminate(self):
        # Legacy behavior for the same input: a bogus byte-equality pass at
        # exit 0 (hash-object follows the symlink, and the target's bytes
        # equal the HEAD blob). Contract: the type check fires first and
        # reports indeterminate (exit 2) naming the path.
        commit_file(self.root, "file.txt", "v2\n", "v2")
        (self.root / "target.txt").write_text("v2\n")
        (self.root / "file.txt").unlink()
        os.symlink("target.txt", self.root / "file.txt")
        proc = run(["check", "--repo", str(self.root), "--", "file.txt"])
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn("file.txt", proc.stdout + proc.stderr)

    def test_multi_path_typechange_and_stale_name_both_evidence_both_orders(self):
        # Dominance rule (outcome contract): a multi-path run observing
        # both a regressed path and a typechange path reports indeterminate
        # (exit 2) AND still names every regressed path in its evidence
        # lines, regardless of argument order. Regression for the early-
        # return shape that dropped the stale path's refuse evidence
        # whenever the typechange path was examined first.
        commit_file(self.root, "file.txt", "v2\n", "v2")
        head_sha = commit_file(self.root, "linked.txt", "linked v1\n",
                               "linked v1")
        (self.root / "file.txt").write_text("v1\n")  # stale ancestor match
        (self.root / "linked.txt").unlink()
        os.symlink("no-such-target.txt", self.root / "linked.txt")
        for order in (["linked.txt", "file.txt"], ["file.txt", "linked.txt"]):
            proc = run(["check", "--repo", str(self.root), "--"] + order)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(self._outcome_lines(proc),
                             ["OUTCOME: indeterminate"])
            # The typechange path is named with the type disagreement...
            self.assertIn("type change for linked.txt",
                          proc.stdout + proc.stderr)
            # ...and the regressed path's refuse evidence is never
            # dropped, whichever order the paths were given in.
            self.assertIn(
                "refuse: file.txt disk bytes equal ancestor %s, not HEAD %s"
                % (self.v1_sha, head_sha),
                proc.stdout)
            self.assertLess(proc.stdout.index("refuse: file.txt"),
                            proc.stdout.index("OUTCOME:"))

    def test_multi_path_plumbing_failure_still_names_remaining_refuse(self):
        # The `except PlumbingFailure` arm collects the same way: a
        # plumbing failure over one path must not drop the remaining
        # paths' refuse evidence (no early return out of the loop). The
        # fixture uses a real plumbing failure over resolved inputs: a
        # candidate path outside the repository makes `git log` fail
        # (exit 128) after `hash-object` answered for its disk bytes.
        commit_file(self.root, "b.txt", "b1\n", "b1")
        (self.root / "b.txt").write_text("junk b\n")  # regressed, no ancestor
        escape = self.root.parent / "escape.txt"
        escape.write_text("outside the repository\n")
        rel_escape = os.path.join("..", "escape.txt")
        for order in ([rel_escape, "b.txt"], ["b.txt", rel_escape]):
            proc = run(["check", "--repo", str(self.root), "--"] + order)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(self._outcome_lines(proc),
                             ["OUTCOME: indeterminate"])
            self.assertIn("git log failed for %s" % rel_escape,
                          proc.stdout + proc.stderr)
            self.assertIn("could not be determined",
                          proc.stdout + proc.stderr)
            self.assertIn(
                "refuse: b.txt disk bytes match neither HEAD nor the "
                "session-owned fresh list", proc.stdout)
            self.assertLess(proc.stdout.index("refuse: b.txt"),
                            proc.stdout.index("OUTCOME:"))

    def test_usage_error_is_tool_error_and_help_is_exempt(self):
        # Legacy: argparse exits 2 on usage errors. Contract: exit 3 with a
        # final `OUTCOME: tool_error` line; --help stays exempt.
        proc = run(["check", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("usage:", proc.stderr)
        help_proc = run(["--help"])
        self.assertEqual(help_proc.returncode, 0, help_proc.stdout)
        self.assertEqual(self._outcome_lines(help_proc), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
