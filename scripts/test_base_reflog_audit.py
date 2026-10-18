#!/usr/bin/env python3
"""Selftest for scripts/base_reflog_audit.py: scratch-repo fixtures for the
reflog-window and landed-receipt row, clean, indeterminate, and tool-error
paths, plus the outcome contract's final `OUTCOME:` line on every
non-metadata exit (0 pass, 1 fail, 2 indeterminate, 3 tool error).

Every fixture is a scratch repository built inside a TemporaryDirectory with
its own git init and per-repo identity; every git invocation (audit and
fixture) is isolated from host state (the ambient GIT_* variable family
dropped, GIT_CONFIG_GLOBAL / GIT_CONFIG_SYSTEM pinned at /dev/null), so
scratch reflogs and fixture commits cannot inherit host config.

r1-review fold (docs/reviews/2026-10-04-code-review-main-rewind-bypass-fences-r1.md,
finding 2): test_reflog_window_missing_nul_separator_is_tool_error forges
one reflog message to carry a carriage return; git renders the byte
verbatim and does not rewrite the reflog file on read, so the
value-plus-message parse meets a continuation line with no NUL separator
and refuses the run as a tool error (exit 3, final `OUTCOME: tool_error`
line), while the restored file audits clean.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "base_reflog_audit.py"


def audit_env():
    """Hermetic git environment (guard_env style, after
    scripts/test_reverse_squash_guard.py): the ambient GIT_* family dropped
    and the two config variables pinned at /dev/null."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    return env


def run_audit(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + list(args),
        capture_output=True, text=True, check=False, env=audit_env(),
    )


def git(root, *args):
    proc = subprocess.run(
        ["git", "-C", str(root)] + list(args),
        capture_output=True, text=True, check=False, env=audit_env(),
    )
    assert proc.returncode == 0, (args, proc.stderr)
    return proc.stdout.strip()


def commit_tree(root, message, tree, *parents):
    """Create a commit with an explicit tree and parents (commit-tree), the
    builder for the empty-diff landing receipt (tree reused from the
    parent) and for side-branch tips that never touch the base reflog."""
    args = ["commit-tree", tree]
    for parent in parents:
        args += ["-p", parent]
    args += ["-m", message]
    proc = subprocess.run(
        ["git", "-C", str(root)] + args,
        capture_output=True, text=True, check=False, env=audit_env(),
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def make_repo(path, first_message="init"):
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "fixture")
    (path / "base.txt").write_text("base\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", first_message)
    return path


def commit_all(root, message, payload=None):
    """Commit a forward step; a distinct payload file keeps the commit
    content-bearing (an empty step would exit 1 with nothing to commit)."""
    if payload is None:
        counter = commit_all.counter[0]
        commit_all.counter[0] = counter + 1
        rel = "step%02d.txt" % counter
        body = "payload %d\n" % counter
    else:
        rel, body = payload
    (root / rel).write_text(body)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


commit_all.counter = [1]


def head_tree(root):
    return git(root, "rev-parse", "HEAD^{tree}")


def outcome_lines(proc):
    """The run's `OUTCOME:` lines from an audit invocation's stdout."""
    return [line for line in proc.stdout.splitlines()
            if line.startswith("OUTCOME:")]


def backward_rows(proc):
    return [line for line in proc.stdout.splitlines()
            if line.startswith("backward-move:")]


def raw_ref_rows(proc):
    return [line for line in proc.stdout.splitlines()
            if line.startswith("raw-ref-write:")]


def receipt_rows(proc):
    return [line for line in proc.stdout.splitlines()
            if line.startswith("empty-receipt:")]


class BaseReflogAuditTest(unittest.TestCase):
    def test_reflog_window_reports_backward_step(self):
        # Witness shape: two forward commits, then a non-fast-forward reset
        # of the base branch to the older commit; the anchor is the window's
        # oldest entry, so the whole walked window is audited.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            first = commit_all(root, "forward one")
            second = commit_all(root, "forward two")
            git(root, "reset", "-q", "--hard", first)
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", base)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(
                backward_rows(proc),
                ["backward-move: %s -> %s" % (second, first)])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
            self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: fail"))
            self.assertLess(proc.stdout.index("backward-move:"),
                            proc.stdout.index("OUTCOME:"))

    def test_reflog_window_audits_move_that_created_anchor(self):
        # Landing-tail shape (anchor at v1): forward to second, reset the
        # base branch to first, commit third; the window stops after the
        # pair whose newer value equals the anchor, and that pair is the
        # paying row (the move that created the anchor is itself audited).
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            first = commit_all(root, "forward one")
            second = commit_all(root, "forward two")
            git(root, "reset", "-q", "--hard", first)
            commit_all(root, "third forward")
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", first)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(
                backward_rows(proc),
                ["backward-move: %s -> %s" % (second, first)])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])

    def test_reflog_window_clean_and_stops_at_anchor(self):
        # Forward-only window with the anchor at the oldest entry: pass.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            commit_all(root, "forward one")
            commit_all(root, "forward two")
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", base)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(backward_rows(proc), [])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
            self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: pass"))

        # A backward step OLDER than the anchor sits outside the window:
        # the walk stops at the anchor and never reaches it.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            first = commit_all(root, "forward one")
            second = commit_all(root, "forward two")
            git(root, "reset", "-q", "--hard", first)
            third = commit_all(root, "third forward")
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", third)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(backward_rows(proc), [])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
            # Control on the same scratch: with the anchor at the oldest
            # entry the backward step IS inside the window and pays.
            base = git(root, "rev-parse", "main~2")
            controlled = run_audit("reflog-window", "--repo", str(root),
                                   "--base-branch", "main",
                                   "--since-sha", base)
            self.assertEqual(controlled.returncode, 1,
                             controlled.stdout + controlled.stderr)
            self.assertEqual(
                backward_rows(controlled),
                ["backward-move: %s -> %s" % (second, first)])

    def test_reflog_window_indeterminate_when_anchor_unreached(self):
        # A forward window longer than a small --max-entries, with a
        # --since-sha that resolves but never appears in the walked window
        # (a side-branch tip in the same scratch repo).
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            for i in range(10):
                (root / ("f%02d.txt" % i)).write_text("content %d\n" % i)
                git(root, "add", "-A")
                git(root, "commit", "-q", "-m", "forward %d" % i)
            side = commit_tree(root, "side tip", head_tree(root), base)
            git(root, "update-ref", "refs/heads/side", side)
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", side,
                             "--max-entries", "5")
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(backward_rows(proc), [])
            self.assertIn(side, proc.stdout)
            self.assertIn(
                "not reached within the walked reflog window (read 5 entries",
                proc.stdout)
            self.assertEqual(outcome_lines(proc), ["OUTCOME: indeterminate"])
            self.assertTrue(
                proc.stdout.rstrip().endswith("OUTCOME: indeterminate"))

    def test_reflog_window_reports_raw_ref_write(self):
        # Witness shape (the 2026-10-04 main rewind): a bare `git
        # update-ref refs/heads/main <sibling-tip>` with no -m leaves an
        # empty-description reflog entry whose new tip is not a descendant
        # of the previous entry; the pair is one raw-ref-write row, not a
        # message-bearing backward move.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            first = commit_all(root, "forward one")
            sibling = commit_tree(root, "side tip", head_tree(root), base)
            git(root, "update-ref", "refs/heads/main", sibling)
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", base)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(
                raw_ref_rows(proc),
                ["raw-ref-write: %s (empty reflog description; new tip is "
                 "not a descendant of previous entry %s)" % (sibling, first)])
            self.assertEqual(backward_rows(proc), [])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
            self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: fail"))
            self.assertLess(proc.stdout.index("raw-ref-write:"),
                            proc.stdout.index("OUTCOME:"))

    def test_reflog_window_empty_description_fast_forward_prints_no_row(self):
        # Declared non-row arm: a bare update-ref whose new tip IS a
        # descendant of the previous entry (the adjacent fast-forward raw
        # write) prints no row, and the clean window keeps the unchanged ok
        # line and exit 0.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            first = commit_all(root, "forward one")
            descendant = commit_tree(root, "side tip", head_tree(root), first)
            git(root, "update-ref", "refs/heads/main", descendant)
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", base)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(raw_ref_rows(proc), [])
            self.assertEqual(backward_rows(proc), [])
            self.assertEqual(
                proc.stdout.splitlines(),
                ["ok: no backward move in the audited reflog window "
                 "(2 pairs audited, anchor %s)" % base,
                 "OUTCOME: pass"])

    def test_reflog_window_raw_write_and_backward_move_in_one_run(self):
        # Both row classes in one walk, walk order preserved: a bare
        # update-ref onto a sibling tip (raw-ref-write) and a message-bearing
        # reset backward (the backward-move bytes unchanged).
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            first = commit_all(root, "forward one")
            second = commit_all(root, "forward two")
            sibling = commit_tree(root, "side tip", head_tree(root), base)
            git(root, "reset", "-q", "--hard", first)
            git(root, "update-ref", "refs/heads/main", sibling)
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", base)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(
                raw_ref_rows(proc),
                ["raw-ref-write: %s (empty reflog description; new tip is "
                 "not a descendant of previous entry %s)" % (sibling, first)])
            self.assertEqual(
                backward_rows(proc),
                ["backward-move: %s -> %s" % (second, first)])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
            self.assertLess(proc.stdout.index("raw-ref-write:"),
                            proc.stdout.index("backward-move:"))

    def test_reflog_window_non_ascii_reflog_message_classifies(self):
        # A message-bearing entry whose reflog message is non-ASCII UTF-8
        # classifies as its modeled row instead of regressing into a tool
        # error (per-field decode: the sha field ASCII-guarded, the message
        # field decoded UTF-8 with replacement).
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            first = commit_all(root, "forward one")
            second = commit_all(root, "forward two")
            git(root, "update-ref", "-m", "rücksetzen: ünïcode nachrícht",
                "refs/heads/main", first)
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", base)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertNotIn("tool error", proc.stdout + proc.stderr)
            self.assertEqual(
                backward_rows(proc),
                ["backward-move: %s -> %s" % (second, first)])
            self.assertEqual(raw_ref_rows(proc), [])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])

    def test_reflog_window_missing_nul_separator_is_tool_error(self):
        # A reflog message forged to carry a carriage return splits the real
        # render (git does not rewrite the reflog file on read) into a
        # NUL-less continuation line; the value-plus-message parse refuses
        # it as a tool error naming the line, and the restored file audits
        # clean, so the craft is the only cause.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            commit_all(root, "forward one")
            log = root / ".git" / "logs" / "refs" / "heads" / "main"
            original = log.read_bytes()
            log.write_bytes(original.replace(
                b"commit: forward one",
                b"commit: forward one\rcruel continuation"))
            proc = run_audit("reflog-window", "--repo", str(root),
                             "--base-branch", "main", "--since-sha", base)
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            self.assertIn("unexpected git reflog output line (missing NUL "
                          "separator)", proc.stderr)
            self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
            self.assertTrue(
                proc.stdout.rstrip().endswith("OUTCOME: tool_error"))
            self.assertEqual(backward_rows(proc), [])
            self.assertEqual(raw_ref_rows(proc), [])
            log.write_bytes(original)
            restored = run_audit("reflog-window", "--repo", str(root),
                                 "--base-branch", "main",
                                 "--since-sha", base)
            self.assertEqual(restored.returncode, 0,
                             restored.stdout + restored.stderr)
            self.assertEqual(outcome_lines(restored), ["OUTCOME: pass"])

    def test_landed_receipt_reports_empty_tip(self):
        # A landing-phrased commit whose tree is identical to its parent's
        # (commit-tree reusing the parent tree): one empty-receipt row
        # naming the repair path.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            base = git(root, "rev-parse", "HEAD")
            empty = commit_tree(root, "plans: land fixture",
                                head_tree(root), base)
            git(root, "update-ref", "refs/heads/main", empty)
            proc = run_audit("landed-receipt", "--repo", str(root),
                             "--base-branch", "main")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(
                receipt_rows(proc),
                ["empty-receipt: %s plans: land fixture (repair: a corrective"
                 " commit naming the content-bearing sha, never an amend)"
                 % empty])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
            self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: fail"))

    def test_landed_receipt_clean_and_non_landing_subjects(self):
        # A content-bearing landing-phrased commit is clean, and an
        # empty-diff commit with a non-landing subject produces no row (the
        # phrasing family is what the receipt audit checks).
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            (root / "landed.txt").write_text("landed content\n")
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "plans: land fixture")
            landed = git(root, "rev-parse", "HEAD")
            empty_wip = commit_tree(root, "wip: scratch notes",
                                    head_tree(root), landed)
            git(root, "update-ref", "refs/heads/main", empty_wip)
            proc = run_audit("landed-receipt", "--repo", str(root),
                             "--base-branch", "main")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(receipt_rows(proc), [])
            self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
            self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: pass"))

    def test_landed_receipt_root_commit_indeterminate(self):
        # A landing-phrased root commit inside the window: it has no parent,
        # so its receipt cannot be checked; the root is named and the run is
        # indeterminate.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo",
                             first_message="plans: land fixture")
            tip = git(root, "rev-parse", "HEAD")
            proc = run_audit("landed-receipt", "--repo", str(root),
                             "--base-branch", "main")
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(receipt_rows(proc), [])
            self.assertIn(tip, proc.stdout)
            self.assertIn("root commit", proc.stdout)
            self.assertEqual(outcome_lines(proc), ["OUTCOME: indeterminate"])
            self.assertTrue(
                proc.stdout.rstrip().endswith("OUTCOME: indeterminate"))

    def test_outcome_line_on_tool_error(self):
        # An unresolvable base branch against BOTH subcommands: each run is
        # a tool error with the final `OUTCOME: tool_error` line.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp) / "repo")
            head = git(root, "rev-parse", "HEAD")
            for args in (
                ["reflog-window", "--repo", str(root),
                 "--base-branch", "no-such-branch", "--since-sha", head],
                ["landed-receipt", "--repo", str(root),
                 "--base-branch", "no-such-branch"],
            ):
                proc = run_audit(*args)
                self.assertEqual(proc.returncode, 3,
                                 proc.stdout + proc.stderr)
                self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
                self.assertTrue(
                    proc.stdout.rstrip().endswith("OUTCOME: tool_error"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
