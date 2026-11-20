#!/usr/bin/env python3
"""Focused fixtures for the published-stack review-fix round helper.

Every fixture builds a scratch git repository (plus a local bare remote)
under a literal `mktemp -d` call and tears it down explicitly through
unittest addCleanup. The suite covers the helper's five subcommands:

- affected: affected-set derivation (lowest edited branch plus chain
  descendants in chain order; inputs outside the model are tool errors).
- restack: the Method C shape wrapped, not re-derived: backup refs for every
  rewritten tip before any rewrite, per-descendant checkout plus
  `git rebase --onto <predecessor-new-tip> <predecessor-old-tip>`, per-link
  parentage verification, the wrong-range safety-witness refusal, the
  missing old-tip refusal, and the conflict abort-and-restore arm.
- push-leases: one lease push per branch with the remote tip read through
  the overridable ls-remote seam; protected-name refusal before any remote
  call; stale-tip refusal reported per branch.
- verify-heads: one ls-remote comparison per branch for the expected head
  and the expected base branch, reporting equality or the observed mismatch.
- retest-set: the caller-provided command set scoped to the affected
  branches; the helper never encodes project commands.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_TOP = Path(__file__).resolve().parents[1]
HELPER = REPO_TOP / "scripts" / "stack_review_round.sh"

if not HELPER.is_file():
    # The RED witness: the suite must fail before the helper exists.
    raise ModuleNotFoundError(
        "stack_review_round helper missing before first run: "
        "scripts/stack_review_round.sh"
    )

NOW = "2026-11-20T09:00:00Z"
PROG_PREFIX = "stack-review-round: "
LS_REMOTE_LOG_ENV = "STACK_TEST_LS_REMOTE_LOG"
LS_REMOTE_SHA_ENV = "STACK_TEST_LS_REMOTE_SHA_FILE"


def mktemp_dir(label: str) -> Path:
    """Scratch root from a literal mktemp -d call, per the plan's fixture
    requirement."""
    template = str(Path(tempfile.gettempdir()) / f"stack-review-round-{label}.XXXXXX")
    out = subprocess.run(
        ["mktemp", "-d", template],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return Path(out.stdout.strip())


def fixture_git_environment(root: Path) -> dict[str, str]:
    """Hermetic git environment, independent of host selectors."""
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(root / "home"),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "Stack Fixture",
        "GIT_AUTHOR_EMAIL": "stack-fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Stack Fixture",
        "GIT_COMMITTER_EMAIL": "stack-fixture@example.invalid",
        "GIT_AUTHOR_DATE": NOW,
        "GIT_COMMITTER_DATE": NOW,
        "TZ": "UTC",
    }


class StackFixture:
    """A scratch repository with a published three-branch stack and a local
    bare remote."""

    def __init__(self, test: unittest.TestCase, label: str, shared_conflict: bool = False):
        self.test = test
        self.root = mktemp_dir(label)
        test.addCleanup(shutil.rmtree, self.root, True)
        self.env = fixture_git_environment(self.root)
        (self.root / "home").mkdir()
        self.repo = self.root / "repo"
        self.remote = self.root / "remote.git"
        self.shared_conflict = shared_conflict
        self._git("init", "--bare", "-q", str(self.remote), cwd=self.root)
        self._git("init", "-q", "-b", "main", str(self.repo), cwd=self.root)
        self._write_and_commit({"base.txt": "base\n", "shared.txt": "shared v1\n"}, "base")
        self.base_tip = self.rev("main")
        self._git("checkout", "-qb", "feat-a", "main")
        self._write_and_commit({"a.txt": "a1\n"}, "a1")
        self.old_a = self.rev("feat-a")
        self._git("checkout", "-qb", "feat-b", "feat-a")
        b_files = {"b.txt": "b1\n"}
        if shared_conflict:
            b_files["shared.txt"] = "shared feat-b\n"
        self._write_and_commit(b_files, "b1")
        self.old_b = self.rev("feat-b")
        self._git("checkout", "-qb", "feat-c", "feat-b")
        self._write_and_commit({"c.txt": "c1\n"}, "c1")
        self.old_c = self.rev("feat-c")
        self._git("checkout", "-q", "feat-a")
        self._git("remote", "add", "origin", str(self.remote))
        self._git("push", "-q", "origin", "main", "feat-a", "feat-b", "feat-c")

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd or self.repo), env=self.env,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"fixture git failed: git {' '.join(args)}\n"
                f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def _write_and_commit(self, files: dict[str, str], message: str) -> None:
        for name, content in files.items():
            (self.repo / name).write_text(content)
        self._git("add", "-A")
        self._git("commit", "-qm", message)

    def rev(self, ref: str) -> str:
        return self._git("rev-parse", "--verify", ref).stdout.strip()

    def amend_head(self, files: dict[str, str], message: str) -> str:
        """A real amend: the new tip replaces the old tip, parent unchanged."""
        for name, content in files.items():
            (self.repo / name).write_text(content)
        self._git("add", "-A")
        self._git("commit", "-q", "--amend", "-m", message)
        return self.rev("HEAD")

    def amend_feat_a(self) -> tuple[str, str]:
        """Amend the bottom branch the way a review-fix round would; returns
        (old tip, new tip)."""
        if self.shared_conflict:
            new_a = self.amend_head({"shared.txt": "shared amended\n"}, "a1 amended")
        else:
            new_a = self.amend_head({"a.txt": "a1 amended\n"}, "a1 amended")
        return self.old_a, new_a

    def side_commit_on_main(self, message: str) -> str:
        """A commit on main that no stack branch descends from."""
        self._git("checkout", "-q", "main")
        self._write_and_commit({"side.txt": "side\n"}, message)
        side = self.rev("main")
        self._git("checkout", "-q", "feat-a")
        return side

    def run_helper(self, *args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        env = dict(self.env)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(HELPER), *args], cwd=str(self.repo), env=env,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def remote_tip(self, branch: str) -> str:
        out = self._git("ls-remote", "origin", f"refs/heads/{branch}")
        return out.stdout.split()[0]

    def write_ls_remote_stub(self) -> str:
        """Stub interposed through STACK_REVIEW_LS_REMOTE: logs each requested
        refspec and prints the sha file's contents, so the suite stages a
        stale tip between read and push deterministically."""
        stub = self.root / "ls-remote-stub.sh"
        stub.write_text(
            "#!/bin/sh\n"
            f'printf \'%s\\n\' "$2" >> "${LS_REMOTE_LOG_ENV}"\n'
            f'cat "${LS_REMOTE_SHA_ENV}"\n'
        )
        stub.chmod(0o755)
        (self.root / "ls-remote-sha.txt").write_text("")
        (self.root / "ls-remote-log.txt").write_text("")
        return str(stub)

    def stub_env(self, sha: str) -> dict[str, str]:
        (self.root / "ls-remote-sha.txt").write_text(f"{sha}\trefs/heads/stubbed\n")
        return {
            LS_REMOTE_LOG_ENV: str(self.root / "ls-remote-log.txt"),
            LS_REMOTE_SHA_ENV: str(self.root / "ls-remote-sha.txt"),
        }

    def stub_log(self) -> str:
        return (self.root / "ls-remote-log.txt").read_text()


OUTCOME_LINE_RE = re.compile(r"^OUTCOME: (pass|fail|indeterminate|tool_error)$")


def outcome_lines(text: str) -> list[str]:
    """Strict final-line matches: OUTCOME: <pass|fail|indeterminate|tool_error>."""
    return [line for line in text.splitlines() if OUTCOME_LINE_RE.match(line)]


def assert_single_final_outcome(test: unittest.TestCase, proc: subprocess.CompletedProcess) -> str:
    """Exactly one OUTCOME line, and it is the final stdout line."""
    lines = proc.stdout.splitlines()
    matched = outcome_lines(proc.stdout)
    test.assertEqual(len(matched), 1, f"stdout was: {proc.stdout}")
    test.assertEqual(lines[-1], matched[0], f"stdout was: {proc.stdout}")
    return matched[0]


def assert_exit_matches_outcome(test: unittest.TestCase, proc: subprocess.CompletedProcess, outcome: str) -> None:
    expected = {"pass": 0, "fail": 1, "indeterminate": 2, "tool_error": 3}[outcome]
    test.assertEqual(proc.returncode, expected, f"stdout was: {proc.stdout}\nstderr: {proc.stderr}")


class AffectedSetTests(unittest.TestCase):
    def test_lowest_edited_branch_plus_chain_descendants_in_order(self):
        fx = StackFixture(self, "affected-basic")
        proc = fx.run_helper(
            "affected", "--stack-base", "main",
            "--chain", "feat-a,feat-b,feat-c", "--edited", "feat-b",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: pass")
        affected = [
            line.split("affected branch: ", 1)[1]
            for line in proc.stdout.splitlines()
            if PROG_PREFIX + "affected: affected branch: " in line
        ]
        self.assertEqual(affected, ["feat-b", "feat-c"])
        self.assertIn("lowest edited branch: feat-b", proc.stdout)
        self.assertIn("stack base: main", proc.stdout)

    def test_multiple_edited_branches_resolve_to_the_lowest(self):
        fx = StackFixture(self, "affected-multi")
        proc = fx.run_helper(
            "affected", "--stack-base", "main",
            "--chain", "feat-a,feat-b,feat-c", "--edited", "feat-c,feat-a",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: pass")
        self.assertIn("affected branch: feat-a", proc.stdout)
        self.assertIn("affected branch: feat-b", proc.stdout)
        self.assertIn("affected branch: feat-c", proc.stdout)
        self.assertIn("lowest edited branch: feat-a", proc.stdout)

    def test_edited_branch_outside_the_chain_is_tool_error(self):
        fx = StackFixture(self, "affected-ghost")
        proc = fx.run_helper(
            "affected", "--stack-base", "main",
            "--chain", "feat-a,feat-b,feat-c", "--edited", "ghost-branch",
        )
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "tool_error")
        self.assertIn("ghost-branch", proc.stdout + proc.stderr)

    def test_unresolvable_stack_base_is_tool_error(self):
        fx = StackFixture(self, "affected-base")
        proc = fx.run_helper(
            "affected", "--stack-base", "no-such-base",
            "--chain", "feat-a,feat-b,feat-c", "--edited", "feat-b",
        )
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "tool_error")
        self.assertIn("no-such-base", proc.stdout + proc.stderr)


class RestackTests(unittest.TestCase):
    def fixture_with_amended_bottom(self, label: str) -> StackFixture:
        fx = StackFixture(self, label)
        fx.old_a_recorded, fx.new_a = fx.amend_feat_a()
        return fx

    def test_replays_chain_in_order_with_parentage_verified(self):
        fx = self.fixture_with_amended_bottom("restack-success")
        proc = fx.run_helper(
            "restack", "--old-tip", fx.old_a_recorded, "--new-tip", fx.new_a,
            "--chain", "feat-b,feat-c",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: pass")
        # Per-link rebase --onto with the predecessor's new tip: feat-b sits
        # directly on the amended bottom branch and carries only its own
        # commit (no whole-stack replay).
        self.assertEqual(fx.rev("feat-b~1"), fx.new_a)
        self.assertEqual(
            fx._git("rev-list", "--count", f"{fx.new_a}..feat-b").stdout.strip(), "1"
        )
        # Link two replays only feat-c's own commit onto the new feat-b.
        self.assertEqual(fx.rev("feat-c~1"), fx.rev("feat-b"))
        self.assertEqual(
            fx._git("rev-list", "--count", "feat-b..feat-c").stdout.strip(), "1"
        )
        # The replayed content survives: each branch keeps its own file plus
        # the amended bottom content below it.
        self.assertEqual(
            fx._git("show", "feat-b:b.txt").stdout.strip(), "b1"
        )
        self.assertEqual(
            fx._git("show", "feat-c:c.txt").stdout.strip(), "c1"
        )
        self.assertEqual(
            fx._git("show", "feat-b:a.txt").stdout.strip(), "a1 amended"
        )
        # Backup refs exist for every rewritten tip.
        self.assertEqual(fx.rev("refs/stack-review-backup/feat-b"), fx.old_b)
        self.assertEqual(fx.rev("refs/stack-review-backup/feat-c"), fx.old_c)
        # The helper walked the chain: HEAD ends on the last descendant.
        self.assertEqual(fx.rev("HEAD"), fx.rev("feat-c"))

    def test_missing_old_tip_refuses_before_any_rebase(self):
        fx = self.fixture_with_amended_bottom("restack-no-old-tip")
        proc = fx.run_helper("restack", "--new-tip", fx.new_a, "--chain", "feat-b,feat-c")
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "tool_error")
        combined = proc.stdout + proc.stderr
        self.assertIn("old tip", combined)
        # Nothing was rewritten.
        self.assertEqual(fx.rev("feat-b"), fx.old_b)
        self.assertEqual(fx.rev("feat-c"), fx.old_c)

    def test_unresolvable_old_tip_refuses_before_any_rebase(self):
        fx = self.fixture_with_amended_bottom("restack-bad-old-tip")
        bogus = "deadbeef" * 5
        proc = fx.run_helper(
            "restack", "--old-tip", bogus, "--new-tip", fx.new_a,
            "--chain", "feat-b,feat-c",
        )
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "tool_error")
        self.assertIn("old tip", proc.stdout + proc.stderr)
        self.assertIn(bogus, proc.stdout + proc.stderr)
        self.assertEqual(fx.rev("feat-b"), fx.old_b)

    def test_wrong_range_old_tip_refuses_safety_witness_before_replay(self):
        fx = self.fixture_with_amended_bottom("restack-wrong-range")
        side = fx.side_commit_on_main("side commit")
        proc = fx.run_helper(
            "restack", "--old-tip", side, "--new-tip", fx.new_a,
            "--chain", "feat-b,feat-c",
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        # The refusal names the offending old tip and the descendant it would
        # have replayed.
        self.assertIn("safety witness", combined)
        self.assertIn(side, combined)
        self.assertIn("feat-b", combined)
        # Nothing was replayed: both descendant tips are unchanged, and no
        # rebase is left in progress.
        self.assertEqual(fx.rev("feat-b"), fx.old_b)
        self.assertEqual(fx.rev("feat-c"), fx.old_c)
        self.assertFalse((fx.repo / ".git" / "rebase-merge").exists())
        # Backups were captured before any rewrite attempt, so the caller can
        # always re-derive.
        self.assertEqual(fx.rev("refs/stack-review-backup/feat-b"), fx.old_b)

    def test_conflict_aborts_rebase_and_restores_from_backups(self):
        fx = StackFixture(self, "restack-conflict", shared_conflict=True)
        fx.old_a_recorded, fx.new_a = fx.amend_feat_a()
        proc = fx.run_helper(
            "restack", "--old-tip", fx.old_a_recorded, "--new-tip", fx.new_a,
            "--chain", "feat-b,feat-c",
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("abort", combined.lower())
        # Both rewritten tips were restored from the backup refs.
        self.assertEqual(fx.rev("feat-b"), fx.old_b)
        self.assertEqual(fx.rev("feat-c"), fx.old_c)
        # No rebase left in progress and the worktree is clean.
        self.assertFalse((fx.repo / ".git" / "rebase-merge").exists())
        status = fx._git("status", "--porcelain").stdout.strip()
        self.assertEqual(status, "")
        # The backup refs still hold the pre-restack tips for re-derivation.
        self.assertEqual(fx.rev("refs/stack-review-backup/feat-b"), fx.old_b)
        self.assertEqual(fx.rev("refs/stack-review-backup/feat-c"), fx.old_c)


class PushLeasesTests(unittest.TestCase):
    def test_pushes_one_lease_push_per_branch_with_fresh_tips(self):
        fx = StackFixture(self, "push-fresh")
        fx.old_a_recorded, fx.new_a = fx.amend_feat_a()
        proc = fx.run_helper("push-leases", "--branch", "feat-a", "--branch", "feat-b")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: pass")
        # The remote moved to the amended tip; the lease read was the fresh
        # remote tip captured immediately before the push.
        self.assertEqual(fx.remote_tip("feat-a"), fx.new_a)
        self.assertEqual(fx.remote_tip("feat-b"), fx.old_b)
        self.assertIn(f"pushed with lease {fx.old_a}", proc.stdout)

    def test_protected_branch_refused_before_any_remote_call(self):
        fx = StackFixture(self, "push-protected")
        fx.old_a_recorded, fx.new_a = fx.amend_feat_a()
        stub = fx.write_ls_remote_stub()
        proc = fx.run_helper(
            "push-leases", "--branch", "main", "--branch", "feat-a",
            extra_env={"STACK_REVIEW_LS_REMOTE": stub, **fx.stub_env(fx.old_a)},
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: fail")
        self.assertIn("protected branch", proc.stdout)
        # The remote call log proves the protected branch never reached the
        # ls-remote seam: only feat-a was read.
        log = fx.stub_log()
        self.assertNotIn("refs/heads/main", log)
        self.assertIn("refs/heads/feat-a", log)
        # The protected remote ref is untouched; the unprotected branch pushed.
        self.assertEqual(fx.remote_tip("main"), fx.base_tip)
        self.assertEqual(fx.remote_tip("feat-a"), fx.new_a)

    def test_stale_remote_tip_refused_per_branch(self):
        fx = StackFixture(self, "push-stale")
        fx.old_a_recorded, fx.new_a = fx.amend_feat_a()
        stub = fx.write_ls_remote_stub()
        # The seam interposes a stale tip (the stack base, a valid sha that no
        # longer matches the remote feat-a tip) between read and push.
        proc = fx.run_helper(
            "push-leases", "--branch", "feat-a",
            extra_env={"STACK_REVIEW_LS_REMOTE": stub, **fx.stub_env(fx.base_tip)},
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: fail")
        self.assertIn("feat-a", proc.stdout)
        self.assertIn("refused", proc.stdout)
        # The push refusal left the remote untouched.
        self.assertEqual(fx.remote_tip("feat-a"), fx.old_a)


class VerifyHeadsTests(unittest.TestCase):
    def test_reports_match_per_branch_for_expected_base_and_head(self):
        fx = StackFixture(self, "verify-match")
        proc = fx.run_helper(
            "verify-heads",
            "--branch", "feat-a", "--base-ref", "main",
            "--expected-base", fx.base_tip, "--expected-head", fx.old_a,
            "--branch", "feat-b", "--base-ref", "feat-a",
            "--expected-base", fx.old_a, "--expected-head", fx.old_b,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: pass")
        self.assertIn("feat-a: head match", proc.stdout)
        self.assertIn("feat-a: base match", proc.stdout)
        self.assertIn("feat-b: head match", proc.stdout)
        self.assertIn("feat-b: base match", proc.stdout)

    def test_reports_observed_mismatch_for_wrong_head_and_wrong_base(self):
        fx = StackFixture(self, "verify-mismatch")
        proc = fx.run_helper(
            "verify-heads",
            "--branch", "feat-a", "--base-ref", "main",
            "--expected-base", fx.base_tip, "--expected-head", fx.base_tip,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: fail")
        self.assertIn("head mismatch", proc.stdout)
        self.assertIn(fx.base_tip, proc.stdout)
        self.assertIn(fx.old_a, proc.stdout)

        proc = fx.run_helper(
            "verify-heads",
            "--branch", "feat-a", "--base-ref", "main",
            "--expected-base", fx.old_b, "--expected-head", fx.old_a,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: fail")
        self.assertIn("base mismatch", proc.stdout)
        self.assertIn("main", proc.stdout)

    def test_read_failure_reports_indeterminate(self):
        fx = StackFixture(self, "verify-indeterminate")
        stub = fx.write_ls_remote_stub()
        # The stub's sha file is removed so the read fails (cat exits
        # nonzero); the seam env still points at the removed path.
        (fx.root / "ls-remote-sha.txt").unlink()
        proc = fx.run_helper(
            "verify-heads",
            "--branch", "feat-a", "--base-ref", "main",
            "--expected-base", fx.base_tip, "--expected-head", fx.old_a,
            extra_env={
                "STACK_REVIEW_LS_REMOTE": stub,
                LS_REMOTE_LOG_ENV: str(fx.root / "ls-remote-log.txt"),
                LS_REMOTE_SHA_ENV: str(fx.root / "ls-remote-sha.txt"),
            },
        )
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "indeterminate")
        self.assertIn("ls-remote read failed", proc.stdout + proc.stderr)


class RetestSetTests(unittest.TestCase):
    def test_prints_caller_command_set_scoped_to_affected_branches(self):
        fx = StackFixture(self, "retest-print")
        proc = fx.run_helper(
            "retest-set",
            "--branch", "feat-a", "--branch", "feat-b",
            "--command", "pytest -q tests_a", "--command", "mise run lint",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(assert_single_final_outcome(self, proc), "OUTCOME: pass")
        scoped = [
            line.split(PROG_PREFIX + "retest-set: ", 1)[1]
            for line in proc.stdout.splitlines()
            if line.startswith(PROG_PREFIX + "retest-set: feat-")
        ]
        self.assertEqual(scoped, [
            "feat-a: pytest -q tests_a",
            "feat-a: mise run lint",
            "feat-b: pytest -q tests_a",
            "feat-b: mise run lint",
        ])

    def test_missing_command_set_is_tool_error_without_invented_commands(self):
        fx = StackFixture(self, "retest-empty")
        proc = fx.run_helper("retest-set", "--branch", "feat-a")
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "tool_error")
        combined = proc.stdout + proc.stderr
        self.assertIn("project test policy", combined)
        # Nothing was invented: no command pair is printed for any branch.
        self.assertNotIn(PROG_PREFIX + "retest-set: feat-a: ", proc.stdout)

        proc = fx.run_helper("retest-set", "--command", "pytest -q tests_a")
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "tool_error")


class OutcomeContractTests(unittest.TestCase):
    def test_help_is_metadata_exit_without_outcome_line(self):
        fx = StackFixture(self, "contract-help")
        proc = fx.run_helper("--help")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # The usage text may mention the phrase; a metadata exit emits no
        # strict OUTCOME line.
        self.assertEqual(outcome_lines(proc.stdout), [])

    def test_unknown_subcommand_is_tool_error(self):
        fx = StackFixture(self, "contract-unknown")
        proc = fx.run_helper("no-such-subcommand")
        assert_single_final_outcome(self, proc)
        assert_exit_matches_outcome(self, proc, "tool_error")

    def test_outcome_line_matches_exit_code_for_pass_and_fail_runs(self):
        fx = StackFixture(self, "contract-mapping")
        passed = fx.run_helper(
            "affected", "--stack-base", "main",
            "--chain", "feat-a,feat-b,feat-c", "--edited", "feat-a",
        )
        self.assertEqual(passed.returncode, 0)
        self.assertEqual(assert_single_final_outcome(self, passed), "OUTCOME: pass")

        failed = fx.run_helper("push-leases", "--branch", "main")
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(assert_single_final_outcome(self, failed), "OUTCOME: fail")


if __name__ == "__main__":
    unittest.main()
