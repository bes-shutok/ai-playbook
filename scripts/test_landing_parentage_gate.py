#!/usr/bin/env python3
"""Selftest for landing_parentage_gate.py: scratch-repo fixtures for every
refused shape and the green paths, plus the outcome contract's four-outcome
fixtures (0 pass, 1 fail, 2 indeterminate, 3 tool error; final `OUTCOME:`
line per non-metadata run)."""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "landing_parentage_gate.py"


def run(args, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, check=False, cwd=cwd, env=env,
    )


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
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
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    env.update({"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@example.invalid",
                "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@example.invalid"})
    proc = subprocess.run(["git", "-C", str(root)] + args,
                          input="orphan\n", capture_output=True, text=True,
                          check=False, env=env)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def content_child(root):
    """Commit real content on the current branch (HEAD at the parent);
    returns the new commit sha, which carries a non-empty first-parent
    diff against its parent (the builder the empty-diff leg's pass-path
    tests share)."""
    (root / "landed.txt").write_text("landed content\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "landed content")
    return git(root, "rev-parse", "HEAD")


def outcome_lines(proc):
    """The run's `OUTCOME:` lines from a gate invocation's stdout."""
    return [line for line in proc.stdout.splitlines()
            if line.startswith("OUTCOME:")]


class LandingParentageGateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        self.pre_tip = git(self.root, "rev-parse", "refs/heads/main")
        self.tree = git(self.root, "rev-parse", "HEAD^{tree}")

    def test_pre_swap_child_of_pre_tip_passes(self):
        # The child carries real content: a tree-identical child of the
        # pre-tip is the empty-diff landing tip the gate's third pre-swap
        # check refuses, so this pass path must build a content child.
        new = content_child(self.root)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: landing commit parentage verified", proc.stdout)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])

    def test_pre_swap_refuses_tree_identical_commit(self):
        new = commit_tree(self.root, self.tree, self.pre_tip)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(
            "refuse: landing commit %s is tree-identical to its parent %s"
            % (new, self.pre_tip), proc.stdout)
        self.assertIn("(empty-diff landing tip)", proc.stdout)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertLess(proc.stdout.index("refuse:"),
                        proc.stdout.index("OUTCOME:"))

    def test_pre_swap_accepts_content_child(self):
        new = content_child(self.root)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: landing commit parentage verified", proc.stdout)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])

    def test_pre_swap_parentage_precedence(self):
        git(self.root, "checkout", "-q", "-b", "side")
        (self.root / "side.txt").write_text("side\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "side")
        side = git(self.root, "rev-parse", "refs/heads/side")
        # A tree-identical child of SIDE, not of the pre-tip: the parentage
        # checks run first and refuse; the empty-diff leg never speaks.
        new = commit_tree(self.root, self.tree, side)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("does not equal pre-landing tip", proc.stdout)
        self.assertNotIn("tree-identical to its parent", proc.stdout)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])

    def test_pre_swap_diff_plumbing_tool_failure(self):
        # A diff exit outside the 0/1 answer vocabulary over two resolved
        # commits is indeterminate (exit 2), never a modeled refusal. The
        # plumbing seam is stubbed in-process: real git cannot be made to
        # fail internally while rev-parse still resolves the same revs.
        # The child carries real content, so the diff cannot short-circuit
        # on equal tree shas and the diff arm is the one exercised.
        new = content_child(self.root)
        sys.path.insert(0, str(SCRIPT.parent))
        import landing_parentage_gate as gate

        def fake_git(repo, *args):
            if args[0] == "rev-parse":
                return subprocess.CompletedProcess(
                    [], 0, args[2].replace("^{commit}", "") + "\n", "")
            if args[0] == "rev-list":
                return subprocess.CompletedProcess(
                    [], 0, new + " " + self.pre_tip + "\n", "")
            return subprocess.CompletedProcess(
                [], 128, "", "fatal: diff plumbing exploded\n")

        original = gate._git
        gate._git = fake_git
        self.addCleanup(setattr, gate, "_git", original)

        # rev-parse resolves both commits, rev-list answers the parentage
        # pair, and the diff arm fails internally: indeterminate over the
        # two named commits, with no refusal line. The diagnostic rides
        # stderr (the gate's evidence channel for indeterminate); the
        # final `OUTCOME:` line rides stdout.
        buffer = io.StringIO()
        err_buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), \
                contextlib.redirect_stderr(err_buffer):
            code = gate.main(["pre-swap", "--repo", str(self.root),
                              "--pre-tip", self.pre_tip,
                              "--new-commit", new])
        self.assertEqual(code, 2)
        out = buffer.getvalue()
        combined = out + err_buffer.getvalue()
        self.assertEqual(
            [l for l in out.splitlines() if l.startswith("OUTCOME:")],
            ["OUTCOME: indeterminate"])
        self.assertTrue(out.rstrip().endswith("OUTCOME: indeterminate"))
        self.assertNotIn("refuse:", out)
        self.assertIn(new, combined)
        self.assertIn(self.pre_tip, combined)
        self.assertIn("could not be determined", combined)

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

    def test_pre_swap_unresolvable_pre_tip_is_tool_error(self):
        new = commit_tree(self.root, self.tree, self.pre_tip)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", "deadbeef" * 5, "--new-commit", new])
        self.assertEqual(proc.returncode, 3)

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

    def test_post_landing_unresolvable_pre_tip_is_tool_error(self):
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", "deadbeef" * 5, "--default-ref", "main"])
        self.assertEqual(proc.returncode, 3)

    def test_post_landing_unresolvable_default_ref_is_tool_error(self):
        proc = run(["post-landing", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--default-ref", "nosuchbranch"])
        self.assertEqual(proc.returncode, 3)

    def test_post_landing_not_a_repo_is_tool_error(self):
        not_a_repo = Path(self._tmp.name) / "notarepo"
        not_a_repo.mkdir()
        proc = run(["post-landing", "--repo", str(not_a_repo),
                    "--pre-tip", self.pre_tip, "--default-ref", "main"])
        self.assertEqual(proc.returncode, 3)

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


class LandingParentageGatePreSwapLegsTest(unittest.TestCase):
    """Task 1 fixtures (plan 2026-10-03-squash-landing-failure-path-guard):
    pre-swap's optional --source-branch (swap-time containment) and
    --expected-base (the base pin) legs. Both legs are additive opt-ins, so
    the no-args shapes keep their recorded outcomes, a stale source branch
    refusal names the fork-point merge base and delta paths, and an
    unresolvable ref is a tool error, never a modeled refusal."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        self.base = git(self.root, "rev-parse", "refs/heads/main")
        self.tree = git(self.root, "rev-parse", "HEAD^{tree}")

    def _side_branch_at(self, fork_sha):
        """Create branch `side` at FORK_SHA carrying one content commit;
        returns the side tip sha (main stays checked out)."""
        git(self.root, "checkout", "-q", "-b", "side", fork_sha)
        (self.root / "side.txt").write_text("side\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "side")
        side = git(self.root, "rev-parse", "refs/heads/side")
        git(self.root, "checkout", "-q", "main")
        return side

    def test_pre_swap_source_branch_containment_green(self):
        # side forks at the live pre-landing tip and carries content: the
        # branch tip contains the pre-tip, so the containment leg passes
        # and the run reports the containment line.
        new = content_child(self.root)
        self._side_branch_at(self.base)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.base, "--new-commit", new,
                    "--source-branch", "side"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: source branch containment verified", proc.stdout)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])

    def test_pre_swap_source_branch_stale_refusal(self):
        # side forked from the older base while main gained a commit the
        # branch lacks: the containment leg refuses (exit 1) naming the
        # fork-point merge base and the fork-point delta paths (the paths
        # main gained since the fork that the branch lacks).
        mainline = content_child(self.root)
        self._side_branch_at(self.base)
        (self.root / "landed2.txt").write_text("landed two\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "landed two")
        new = git(self.root, "rev-parse", "HEAD")
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", mainline, "--new-commit", new,
                    "--source-branch", "side"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("refuse:", proc.stdout)
        self.assertIn(self.base, proc.stdout)
        self.assertIn("landed.txt", proc.stdout)
        # The same fixture shows the leg green once main is reset to the
        # fork point: pre-tip main then equals the fork point, which side
        # contains, so the refusal no longer fires.
        git(self.root, "update-ref", "refs/heads/main", self.base)
        mainline_tree = git(self.root, "rev-parse", "%s^{tree}" % mainline)
        reset_child = commit_tree(self.root, mainline_tree, self.base)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", "main", "--new-commit", reset_child,
                    "--source-branch", "side"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("refuse:", proc.stdout)
        self.assertIn("ok: source branch containment verified", proc.stdout)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])

    def test_pre_swap_expected_base_pin(self):
        # side forks at the live pre-landing tip, so the computed merge
        # base of the pre-tip and the side tip is the fork commit itself:
        # a pin equal to it passes, and a value differing from it (the
        # silent-rebase-under-a-stale-record class) refuses naming both
        # shas and the words base pin.
        self._side_branch_at(self.base)
        new = content_child(self.root)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.base, "--new-commit", new,
                    "--source-branch", "side",
                    "--expected-base", self.base])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok: base pin verified", proc.stdout)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.base, "--new-commit", new,
                    "--source-branch", "side",
                    "--expected-base", new])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("refuse:", proc.stdout)
        self.assertIn("base pin", proc.stdout)
        self.assertIn(self.base, proc.stdout)
        self.assertIn(new, proc.stdout)

    def test_pre_swap_new_args_optional(self):
        # Additive opt-in sweep: both flags exist and are optional, and
        # every pre-existing pre-swap shape, run without --source-branch
        # and --expected-base, keeps its recorded outcome and gains no
        # new-leg evidence lines.
        help_proc = run(["pre-swap", "--help"])
        self.assertEqual(help_proc.returncode, 0, help_proc.stdout)
        self.assertIn("--source-branch", help_proc.stdout)
        self.assertIn("--expected-base", help_proc.stdout)
        new = content_child(self.root)
        tree_identical = commit_tree(self.root, self.tree, self.base)
        parentless = commit_tree(self.root, self.tree)
        git(self.root, "checkout", "-q", "-b", "side2", self.base)
        (self.root / "side2.txt").write_text("side2\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "side2")
        side2 = git(self.root, "rev-parse", "refs/heads/side2")
        git(self.root, "checkout", "-q", "main")
        wrong_parent = commit_tree(self.root, self.tree, self.base, side2)
        scenarios = [
            (["--pre-tip", self.base, "--new-commit", new], 0, "pass"),
            (["--pre-tip", self.base, "--new-commit", tree_identical],
             1, "fail"),
            (["--pre-tip", self.base, "--new-commit", wrong_parent],
             1, "fail"),
            (["--pre-tip", self.base, "--new-commit", parentless],
             1, "fail"),
            (["--pre-tip", self.base, "--new-commit", "deadbeef" * 5],
             1, "fail"),
            (["--pre-tip", "deadbeef" * 5, "--new-commit", new],
             3, "tool_error"),
        ]
        for extra, code, outcome in scenarios:
            proc = run(["pre-swap", "--repo", str(self.root)] + extra)
            self.assertEqual(
                proc.returncode, code,
                (extra, proc.stdout + proc.stderr))
            self.assertEqual(
                outcome_lines(proc), ["OUTCOME: %s" % outcome], extra)
            self.assertNotIn("containment", proc.stdout)
            self.assertNotIn("base pin", proc.stdout)
        # The usage-error shape keeps its tool-error exit and gains no leg.
        proc = run(["pre-swap", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])

    def test_pre_swap_expected_base_requires_source_branch(self):
        # --expected-base without its companion --source-branch is a usage
        # tool error naming the missing companion, never a modeled refusal.
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.base, "--new-commit", self.base,
                    "--expected-base", self.base])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("requires its companion --source-branch", proc.stderr)

    def test_pre_swap_unresolvable_source_branch(self):
        # An unresolvable --source-branch is an unheld operating-context
        # assumption: a tool error naming the ref, never a modeled refusal.
        new = content_child(self.root)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.base, "--new-commit", new,
                    "--source-branch", "nosuchbranch"])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("source branch unresolvable: nosuchbranch",
                      proc.stderr)


class LandingParentageGateOutcomeTest(unittest.TestCase):
    """Outcome-contract fixtures (plan 2026-10-03-outcome-contract-migration-
    batch-1 Task 1): every non-metadata run ends with exactly one final
    `OUTCOME:` line; a plumbing failure over resolved revs is indeterminate
    (exit 2); an unresolvable rev, a usage error, or an unheld environment
    assumption is tool error (exit 3, the argparse override); `--help` stays
    metadata-exempt with no `OUTCOME:` line."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_repo(Path(self._tmp.name) / "repo")
        self.pre_tip = git(self.root, "rev-parse", "refs/heads/main")
        self.tree = git(self.root, "rev-parse", "HEAD^{tree}")

    def test_pass_emits_single_final_outcome_pass(self):
        # A content child, not a tree-identical one: the empty-diff leg
        # refuses tree-identical children, so the pass fixture must carry
        # real content (same builder as the pass-path tests above).
        new = content_child(self.root)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: pass"))

    def test_fail_emits_outcome_fail_with_evidence(self):
        new = commit_tree(self.root, self.tree)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", self.pre_tip, "--new-commit", new])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("refuse: landing commit is parentless", proc.stdout)
        self.assertLess(proc.stdout.index("refuse:"),
                        proc.stdout.index("OUTCOME:"))

    def test_unresolvable_rev_is_tool_error(self):
        # Legacy guard-family behavior: this shape exits 2 (tool failure).
        # Contract expectation: an input that never resolved is tool error
        # (exit 3) with a final `OUTCOME: tool_error` line.
        new = commit_tree(self.root, self.tree, self.pre_tip)
        proc = run(["pre-swap", "--repo", str(self.root),
                    "--pre-tip", "deadbeef" * 5, "--new-commit", new])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])

    def test_usage_error_is_tool_error_and_help_is_exempt(self):
        # Legacy: argparse exits 2 on usage errors. Contract: exit 3 with a
        # final `OUTCOME: tool_error` line; --help stays exempt.
        proc = run(["pre-swap", "--repo", str(self.root)])
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("usage:", proc.stderr)
        help_proc = run(["--help"])
        self.assertEqual(help_proc.returncode, 0, help_proc.stdout)
        self.assertEqual(outcome_lines(help_proc), [])

    def test_plumbing_failure_over_resolved_revs_is_indeterminate(self):
        # The answer-vocabulary criterion: both revs resolve, then the
        # plumbing answers outside its 0/1 answer vocabulary (here exit 128
        # for rev-list --parents and merge-base --is-ancestor): indeterminate
        # (exit 2), never a tool failure, with an observed/could-not-determine
        # evidence line. The plumbing seam is stubbed in-process: real git
        # cannot be made to fail internally while rev-parse still resolves
        # the same revs.
        sys.path.insert(0, str(SCRIPT.parent))
        import landing_parentage_gate as gate

        resolved = subprocess.CompletedProcess(
            [], 0, self.pre_tip + "\n", "")
        broken = subprocess.CompletedProcess(
            [], 128, "", "fatal: plumbing exploded\n")

        def fake_git(repo, *args):
            if args[0] == "rev-parse":
                return resolved
            return broken

        original = gate._git
        gate._git = fake_git
        self.addCleanup(setattr, gate, "_git", original)

        # pre-swap: both revs resolve; rev-list fails internally. The
        # observed/could-not-determine evidence rides stderr (the gate's
        # diagnostic stream, as before); the final `OUTCOME:` line stdout.
        buffer = io.StringIO()
        err_buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), \
                contextlib.redirect_stderr(err_buffer):
            code = gate.main(["pre-swap", "--repo", str(self.root),
                              "--pre-tip", self.pre_tip,
                              "--new-commit", self.pre_tip])
        self.assertEqual(code, 2)
        out = buffer.getvalue()
        combined = out + err_buffer.getvalue()
        self.assertEqual(
            [l for l in out.splitlines() if l.startswith("OUTCOME:")],
            ["OUTCOME: indeterminate"])
        self.assertIn("could not be determined", combined)
        self.assertTrue(out.rstrip().endswith("OUTCOME: indeterminate"))

        # post-landing: both revs resolve; merge-base fails internally.
        buffer = io.StringIO()
        err_buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), \
                contextlib.redirect_stderr(err_buffer):
            code = gate.main(["post-landing", "--repo", str(self.root),
                              "--pre-tip", self.pre_tip,
                              "--default-ref", "main"])
        self.assertEqual(code, 2)
        out = buffer.getvalue()
        combined = out + err_buffer.getvalue()
        self.assertEqual(
            [l for l in out.splitlines() if l.startswith("OUTCOME:")],
            ["OUTCOME: indeterminate"])
        self.assertIn("could not be determined", combined)


if __name__ == "__main__":
    unittest.main(verbosity=1)
