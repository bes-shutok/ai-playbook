#!/usr/bin/env python3
"""Selftest for land_squash.sh: scratch-repo fixtures driving the lock-bound
squash-landing helper via subprocess for every refusal, restore, and outcome
class. Covered classes: the probe modes with their no-mutation assertion, the
lock-authenticity classes (unset, empty, nonexistent, meta-less, empty-token,
mismatched, sibling-repo), the wrong-HEAD and tip-moved refusals, the green
path with tree equality and base-pin forwarding, the unresolvable-branch tool
error, the dirty-intersection and staged pre-refusals, the record-only
intersection pre-refusal, the merge-failure path-exclusive restore with its
dirty-at-snapshot carve-out, the dirty-writer concurrent-writer block arm,
the interleaved-tip post-landing arm and the diverge-origin informational
note, the parentage pre-swap refusal propagation, the stale-base
tree-equality refusal, and the stale-record base-pin refusal. The
land-worktree mode (the worktree-complete landing class) is covered by its
own cases: the green path with the primary checkout byte-unchanged witness,
the dirty-source-worktree tree-inequality refusal, the lock-mismatch refusal
before composition, the wired check-landing stale-base refusal, the wired
check-archive plans-egress refusal and its sanctioned-archive and
operator-ack pass shapes, the wrong-source-tip refusals, the parentage
pre-swap refusal, the base-mover compare-and-swap refusal, the diverge-origin
informational note, the backward-peer indeterminate arm, and the
omission-scope and usage-text audit."""

import hashlib
import os
import subprocess
import time
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
HELPER = SCRIPTS / "land_squash.sh"
DONE_LOCK = SCRIPTS / "done-lock.sh"


def base_env():
    """A clean environment: no inherited GIT_* or lock/seam variables."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    for key in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN",
                "LAND_SQUASH_TEST_FAULT", "LAND_SQUASH_TEST_FAULT_PATH"):
        env.pop(key, None)
    return env


def git(root, *args, check=True):
    proc = subprocess.run(
        ["git", "-C", str(root)] + list(args),
        capture_output=True, text=True, check=False, env=base_env(),
    )
    if check:
        assert proc.returncode == 0, (args, proc.stdout, proc.stderr)
    return proc


def rev(root, spec):
    return git(root, "rev-parse", spec).stdout.strip()


def commit_file(root, rel_path, content, message):
    path = Path(root) / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    git(root, "add", "--", rel_path)
    git(root, "commit", "-q", "-m", message)
    return rev(root, "HEAD")


def commit_tree(root, tree, *parents):
    args = ["commit-tree", tree]
    for parent in parents:
        args += ["-p", parent]
    env = base_env()
    env.update({"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@example.invalid",
                "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@example.invalid"})
    proc = subprocess.run(["git", "-C", str(root)] + args,
                          input="fixture commit\n", capture_output=True,
                          text=True, check=False, env=env)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def make_repo(path, extra_files=None):
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "fixture")
    (path / "f01.txt").write_text("f01 base\n")
    (path / "f02.txt").write_text("f02 base\n")
    (path / "notes.txt").write_text("notes base\n")
    # the receipt home is gitignored in the real repository (docs/tmp/); the
    # scratch repos carry the same ignore so the landing-tail reconcile
    # receipt never pollutes the porcelain assertions
    (path / ".gitignore").write_text("docs/tmp/\n")
    for name, content in (extra_files or {}).items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "base")
    return path


def acquire_merge_lock(repo, lock_root):
    """Acquire a live merge lock on repo via done-lock.sh; returns (dir, token)."""
    env = base_env()
    env["MERGE_LOCK_ROOT"] = str(lock_root)
    env["MERGE_LOCK_HOLDER_PID"] = str(os.getpid())
    proc = subprocess.run(
        ["bash", str(DONE_LOCK), "merge-acquire", "--label", "fixture"],
        capture_output=True, text=True, check=False, cwd=str(repo), env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    values = {}
    for line in proc.stdout.splitlines():
        if line.startswith("export "):
            key, _, value = line[len("export "):].partition("=")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            values[key] = value
    # The session fence is done-lock's status witness, not part of the fixture
    # state under test: remove it so the scratch repo's porcelain, snapshots,
    # and diffstats carry only the paths the fixture itself created.
    session = Path(repo) / ".ai-playbook" / "merge-lock.session"
    try:
        session.unlink()
        session.parent.rmdir()
    except OSError:
        pass
    return values["MERGE_LOCK_DIR"], values["MERGE_LOCK_TOKEN"]


def set_meta_field(lock_dir, key, value):
    meta = Path(lock_dir) / "meta.env"
    lines = []
    for line in meta.read_text().splitlines():
        if line.startswith(key + "="):
            lines.append("%s=%s" % (key, value))
        else:
            lines.append(line)
    meta.write_text("\n".join(lines) + "\n")


def fingerprint(root):
    """HEAD sha, index stage entries, and porcelain: the no-mutation witness."""
    return (
        rev(root, "HEAD"),
        git(root, "ls-files", "-s").stdout,
        git(root, "status", "--porcelain=v1").stdout,
    )


def outcome_lines(proc):
    return [line for line in proc.stdout.splitlines()
            if line.startswith("OUTCOME:")]


def run_helper(args, cwd, lock=None, fault=None, fault_path=None,
               lock_dir_override=None, lock_token_override=None,
               with_lock_env=True, staged_wait=None):
    """Run the helper in the scratch repo; the lock env is injected only when
    with_lock_env is true (probe runs without it, per its contract)."""
    env = base_env()
    if with_lock_env and lock is not None:
        env["MERGE_LOCK_DIR"] = lock_dir_override if lock_dir_override is not None else lock[0]
        env["MERGE_LOCK_TOKEN"] = lock_token_override if lock_token_override is not None else lock[1]
    if fault is not None:
        env["LAND_SQUASH_TEST_FAULT"] = fault
    if fault_path is not None:
        env["LAND_SQUASH_TEST_FAULT_PATH"] = fault_path
    if staged_wait is not None:
        env["LAND_SQUASH_STAGED_WAIT_SECS"] = staged_wait
    if not HELPER.exists():
        return subprocess.CompletedProcess(
            [str(HELPER)] + args, 127, "", "land_squash.sh absent\n")
    return subprocess.run(
        ["bash", str(HELPER)] + args,
        capture_output=True, text=True, check=False, cwd=str(cwd), env=env,
    )


def probe(root, branch):
    return run_helper(["probe", "--branch", branch], cwd=root, with_lock_env=False)


def land(root, branch, expected_tip, message, expected_base=None, **kwargs):
    args = ["land", "--branch", branch, "--expected-tip", expected_tip,
            "--message", message]
    if expected_base is not None:
        args += ["--expected-base", expected_base]
    return run_helper(args, cwd=root, **kwargs)


def land_worktree(root, branch, expected_tip, message, expected_base=None,
                  ack_egress=None, **kwargs):
    """Run the land-worktree mode from the primary checkout (cwd=root); the
    source worktree is addressed through the worktree list by --branch."""
    args = ["land-worktree", "--branch", branch, "--expected-tip", expected_tip,
            "--message", message]
    if expected_base is not None:
        args += ["--expected-base", expected_base]
    if ack_egress is not None:
        args += ["--ack-egress", ack_egress]
    return run_helper(args, cwd=root, **kwargs)


def primary_state(root):
    """The primary checkout's byte-bearing state per Evaluation Criterion 1:
    index stage entries, the worktree-vs-index diff, and the untracked set
    (`git ls-files --others --exclude-standard`), taken by this harness around
    the invocation. HEAD is asserted separately because the compare-and-swap
    moves it on the pass path; a changed primary_state is a primary-write
    violation."""
    return (
        git(root, "ls-files", "-s").stdout,
        git(root, "diff", "--name-only").stdout,
        git(root, "ls-files", "--others", "--exclude-standard").stdout,
    )


class LandSquashHelperTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.locks = self.tmp / "locks"
        self.locks.mkdir()

    def locked_repo(self, name="repo", extra_files=None):
        repo = make_repo(self.tmp / name, extra_files=extra_files)
        lock = acquire_merge_lock(repo, self.locks)
        return repo, lock

    def conflict_setup(self, repo):
        """Branch and main both edit shared.txt; the branch also adds a new
        file; returns the new expected tip (main's advanced tip)."""
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "shared.txt", "base branch\n", "branch edit")
        commit_file(repo, "added.txt", "added by branch\n", "branch add")
        git(repo, "checkout", "-q", "main")
        tip = commit_file(repo, "shared.txt", "base main\n", "main edit")
        return tip

    # ---- probe modes -------------------------------------------------

    def test_probe_modes(self):
        # clean fast-forwardable branch: pass with containment and a
        # conflict-free trial, and no mutation of HEAD, index, or worktree.
        repo = make_repo(self.tmp / "clean")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        before = fingerprint(repo)
        proc = probe(repo, "feature")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("containment verified", proc.stdout)
        self.assertIn("no conflicts", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

        # stale base: the branch forked while main gained a commit it lacks.
        stale = make_repo(self.tmp / "stale")
        git(stale, "checkout", "-q", "-b", "feature")
        commit_file(stale, "stale.txt", "stale\n", "stale branch work")
        git(stale, "checkout", "-q", "main")
        main_tip = commit_file(stale, "main-file.txt", "main\n", "main advance")
        fork_point = rev(stale, "main~1")
        before = fingerprint(stale)
        proc = probe(stale, "feature")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("fork-point merge base: %s" % fork_point, proc.stdout)
        self.assertIn("main-file.txt", proc.stdout)
        self.assertEqual(fingerprint(stale), before)

        # conflicting branch: both sides edit one file.
        conf = make_repo(self.tmp / "conflict")
        self.conflict_setup(conf)
        before = fingerprint(conf)
        proc = probe(conf, "feature")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("shared.txt", proc.stdout)
        self.assertIn("conflict", proc.stdout)
        self.assertEqual(fingerprint(conf), before)

    # ---- lock authenticity -------------------------------------------

    def test_land_requires_live_token_lock(self):
        def no_mutation_tool_error(repo, lock=None, **kwargs):
            before = fingerprint(repo)
            proc = land(repo, "feature", rev(repo, "refs/heads/main"),
                        "land it", lock=lock, **kwargs)
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
            self.assertEqual(fingerprint(repo), before)
            return proc

        # unset MERGE_LOCK_DIR
        repo, lock = self.locked_repo("unset")
        proc = no_mutation_tool_error(repo, lock=lock, lock_dir_override="")
        self.assertIn("MERGE_LOCK_DIR", proc.stdout)

        # empty MERGE_LOCK_TOKEN
        repo, lock = self.locked_repo("empty-token-env")
        proc = no_mutation_tool_error(repo, lock=lock, lock_token_override="")
        self.assertIn("MERGE_LOCK_TOKEN", proc.stdout)

        # nonexistent lock directory
        repo, lock = self.locked_repo("nonexistent")
        missing = self.tmp / "no-such-lock"
        proc = no_mutation_tool_error(repo, lock=lock, lock_dir_override=str(missing))
        self.assertIn(str(missing), proc.stdout)

        # live directory whose meta.env is missing
        repo, lock = self.locked_repo("meta-less")
        os.remove(Path(lock[0]) / "meta.env")
        proc = no_mutation_tool_error(repo, lock=lock)
        self.assertIn("meta.env", proc.stdout)

        # live record carrying an empty lock_token
        repo, lock = self.locked_repo("empty-token-record")
        set_meta_field(lock[0], "lock_token", "")
        proc = no_mutation_tool_error(repo, lock=lock)
        self.assertIn("lock_token", proc.stdout)

        # live record whose lock_token differs from the env token
        repo, lock = self.locked_repo("mismatched")
        proc = no_mutation_tool_error(repo, lock=lock,
                                      lock_token_override="forged-token")
        self.assertIn("lock_token", proc.stdout)

        # live token-matching record whose repo_root names a different repo
        repo_a = make_repo(self.tmp / "repo-a")
        repo_b, lock_b = self.locked_repo("repo-b")
        before = fingerprint(repo_a)
        proc = land(repo_a, "feature", rev(repo_a, "refs/heads/main"),
                    "land it", lock=lock_b)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("repo_root", proc.stdout)
        self.assertEqual(fingerprint(repo_a), before)

    # ---- wrong HEAD and moved tips ------------------------------------

    def test_land_wrong_head_refused(self):
        # detached primary checkout: tool error naming HEAD and the tip
        repo, lock = self.locked_repo("detached")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "--detach")
        before = fingerprint(repo)
        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("detached", proc.stdout)
        self.assertIn(tip, proc.stdout)
        self.assertEqual(fingerprint(repo), before)

        # attached HEAD but the ref tip moved past --expected-tip: the
        # tip-moved class fires (the wrong-branch-at-same-tip coincidence is
        # the accepted residual the plan's Assumptions record).
        repo, lock = self.locked_repo("ref-moved")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        old_tip = rev(repo, "refs/heads/main")
        commit_file(repo, "advanced.txt", "advanced\n", "main advanced")
        before = fingerprint(repo)
        proc = land(repo, "feature", old_tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("tip moved", proc.stdout)
        self.assertIn(old_tip, proc.stdout)
        self.assertIn(rev(repo, "refs/heads/main"), proc.stdout)
        self.assertIn("re-derive", proc.stdout)
        self.assertIn("retry", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    # ---- the green path ------------------------------------------------

    def test_land_green_path(self):
        repo, lock = self.locked_repo("green")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        landing_content = "landed by feature\n"
        commit_file(repo, "landed.txt", landing_content, "feature work")
        git(repo, "checkout", "-q", "main")
        branch_tree = rev(repo, "feature^{tree}")

        proc = land(repo, "feature", tip, "land feature", expected_base=tip,
                    lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("base pin verified", proc.stdout)

        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, tip)
        self.assertEqual(rev(repo, "%s^" % landing), tip)
        self.assertEqual(rev(repo, "%s^{tree}" % landing), branch_tree)
        self.assertIn("new tip: %s" % landing, proc.stdout)
        self.assertIn("landed.txt", proc.stdout)
        self.assertIn("| 1 +", proc.stdout)
        # the landing-tail reconcile gate ran and recorded its receipt
        self.assertIn("reconcile-receipt:", proc.stdout)
        landing_receipt = repo / "docs" / "tmp" / "landing-receipts" / (
            "%s.txt" % rev(repo, "refs/heads/main"))
        self.assertIn("exit code: 0", landing_receipt.read_text())
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")

    # ---- unresolvable source branch -------------------------------------

    def test_land_unresolvable_source_branch(self):
        repo, lock = self.locked_repo("unresolvable")
        tip = rev(repo, "refs/heads/main")
        before = fingerprint(repo)
        proc = land(repo, "no-such-branch", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("no-such-branch", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    # ---- tip moved before the call ---------------------------------------

    def test_land_tip_moved_refusal(self):
        repo, lock = self.locked_repo("tip-moved")
        expected = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        new_tip = commit_file(repo, "main-more.txt", "more\n", "main moved on")
        before = fingerprint(repo)
        proc = land(repo, "feature", expected, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn(expected, proc.stdout)
        self.assertIn(new_tip, proc.stdout)
        self.assertIn("re-derive", proc.stdout)
        self.assertIn("retry", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    # ---- merge failure: path-exclusive restore ----------------------------

    def test_land_merge_failure_restores_path_exclusively(self):
        repo, lock = self.locked_repo("merge-failure")
        tip = self.conflict_setup(repo)
        # a pre-existing dirty tracked path OUTSIDE the branch's diff
        (repo / "notes.txt").write_text("notes dirty\n")
        before_porcelain = git(repo, "status", "--porcelain=v1").stdout
        self.assertEqual(before_porcelain, " M notes.txt\n")

        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn("merge failure", proc.stdout)

        # the failure-time staged set is fully restored
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout,
                         before_porcelain)
        self.assertIn("base main\n", (repo / "shared.txt").read_text())

        # the merge-created file is removed and named
        self.assertFalse((repo / "added.txt").exists())
        self.assertNotIn("added.txt", git(repo, "ls-files").stdout)
        self.assertIn("added.txt", proc.stdout)

        # the dirty-at-snapshot carve-out: the pre-existing dirty path keeps
        # its bytes and is named as not restored
        self.assertEqual((repo / "notes.txt").read_text(), "notes dirty\n")
        self.assertIn("notes.txt", proc.stdout)
        self.assertIn("dirty at snapshot", proc.stdout)

    def test_merge_failure_space_paths(self):
        """Sibling of test_land_merge_failure_restores_path_exclusively with a
        tracked non-ASCII path and a space-bearing tracked path staged for
        deletion by the failed merge, plus a merge-created space-named file:
        both tracked shapes restore per path and are named exactly once, and
        the merge-created file is removed and named."""
        repo, lock = self.locked_repo("merge-failure-space")
        # tracked at HEAD on main: non-ASCII + space-bearing names
        commit_file(repo, "rapport final na\u00efve.txt", "nonascii\n", "add nonascii")
        commit_file(repo, "my notes.txt", "space\n", "add space")
        # branch deletes both, edits shared.txt, adds a merge-created file
        git(repo, "checkout", "-q", "-b", "feature")
        git(repo, "rm", "-q", "--", "rapport final na\u00efve.txt", "my notes.txt")
        git(repo, "commit", "-q", "-m", "branch deletes space-bearing paths")
        commit_file(repo, "shared.txt", "base branch\n", "branch edit")
        commit_file(repo, "my added.txt", "added by branch\n", "branch add space")
        git(repo, "checkout", "-q", "main")
        tip = commit_file(repo, "shared.txt", "base main\n", "main edit")

        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn("merge failure", proc.stdout)

        # the staged set is fully restored: HEAD bytes back for both
        # space-bearing deletions, the merge-created file removed
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")
        self.assertEqual((repo / "my notes.txt").read_text(), "space\n")
        self.assertEqual(
            (repo / "rapport final na\u00efve.txt").read_text(), "nonascii\n"
        )
        self.assertFalse((repo / "my added.txt").exists())
        self.assertNotIn("my added.txt", git(repo, "ls-files").stdout)

        # named per path: each raw name appears exactly once in the report,
        # never under the skipped-writer heading
        self.assertIn("restored to HEAD:", proc.stdout)
        self.assertEqual(proc.stdout.count("my notes.txt"), 1)
        self.assertEqual(proc.stdout.count("rapport final na\u00efve.txt"), 1)
        self.assertIn("my added.txt", proc.stdout)
        skip_idx = proc.stdout.find("skipped (changed after the snapshot")
        if skip_idx != -1:
            skip_block = proc.stdout[skip_idx:proc.stdout.find("\n\n", skip_idx)]
            self.assertNotIn("my notes.txt", skip_block)
            self.assertNotIn("rapport final na\u00efve.txt", skip_block)

    def test_dirty_intersection_nonascii_prefused(self):
        """GREEN-today pin: the dirty-intersection pre-refusal fires for a
        non-ASCII-named tracked path under today's paired quoted forms and
        must still fire after the -z switches."""
        repo, lock = self.locked_repo("dirty-intersection-nonascii")
        commit_file(repo, "rapport na\u00efve.txt", "base\n", "add nonascii")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "rapport na\u00efve.txt", "branch\n", "branch edit")
        git(repo, "checkout", "-q", "main")
        tip = commit_file(repo, "other.txt", "main\n", "main edit")
        # local modification of the non-ASCII path in the primary checkout
        (repo / "rapport na\u00efve.txt").write_text("dirty local\n")
        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("refuse: dirty intersection", proc.stdout)
        # GREEN-today: the refusal fires for the non-ASCII name under either
        # spelling (today's C-quoted line form or the post-fix raw -z form)
        self.assertTrue(
            "rapport na\u00efve.txt" in proc.stdout
            or "rapport na\\303\\257ve.txt" in proc.stdout,
            proc.stdout,
        )

    # ---- the record-only intersection pre-refusal -------------------------

    def test_land_record_only_intersection_prefused(self):
        record_only = "projects/.ai-playbook/development_lessons.md"
        repo, lock = self.locked_repo(
            "record-only", extra_files={record_only: "lessons base\n"})
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, record_only, "lessons branch\n", "branch edit")
        git(repo, "checkout", "-q", "main")
        (repo / record_only).write_text("lessons local edit\n")
        before = fingerprint(repo)

        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn(record_only, proc.stdout)
        self.assertIn("dirty intersection", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    # ---- the dirty-intersection pre-refusal -------------------------------

    def test_land_dirty_intersection_prefused(self):
        repo, lock = self.locked_repo("dirty-intersection")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "f01.txt", "f01 branch\n", "branch edit")
        git(repo, "checkout", "-q", "main")
        (repo / "f01.txt").write_text("f01 local edit\n")
        before = fingerprint(repo)

        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("f01.txt", proc.stdout)
        self.assertIn("dirty intersection", proc.stdout)
        self.assertEqual((repo / "f01.txt").read_text(), "f01 local edit\n")
        self.assertEqual(fingerprint(repo), before)

    # ---- the staged-state pre-refusal --------------------------------------

    def test_land_staged_prefused(self):
        repo, lock = self.locked_repo("staged")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        (repo / "f01.txt").write_text("f01 staged locally\n")
        git(repo, "add", "f01.txt")
        before = fingerprint(repo)

        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("f01.txt", proc.stdout)
        self.assertIn("staged", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    # ---- the arm-1 staged-orphan bounded exit (plan
    # 2026-10-10-coordination-single-writer-ttl, Task 1) ----------------------

    def staged_setup(self, name):
        repo, lock = self.locked_repo(name)
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        (repo / "f01.txt").write_text("f01 staged locally\n")
        git(repo, "add", "f01.txt")
        return repo, lock, tip

    def test_land_staged_bounded_wait_attributed(self):
        repo, lock, tip = self.staged_setup("staged-wait-attributed")
        claims = repo / "docs" / "tmp" / "execution-claims"
        claims.mkdir(parents=True)
        # the claim cross-references the staged path by its plan basename
        (claims / "some-plan.md").write_text(
            "session: sess_fixture\n"
            "plan: docs/history/plans/2026-10-10-f01.txt.md\n"
            "created: 2026-10-10T00:00:00Z\nupdated: 2026-10-10T00:00:00Z\n"
        )
        before = fingerprint(repo)
        started = time.time()
        proc = land(repo, "feature", tip, "land it", lock=lock,
                    staged_wait="1")
        elapsed = time.time() - started
        self.assertGreaterEqual(elapsed, 1.0)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("arm-1 bounded exit, waited 1s", proc.stdout)
        self.assertIn("attributed to claim some-plan.md (session sess_fixture)", proc.stdout)
        self.assertIn("route per D-9", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    def test_land_staged_bounded_wait_unattributed_refusal_shape(self):
        repo, lock, tip = self.staged_setup("staged-wait-unattributed")
        before = fingerprint(repo)
        proc = land(repo, "feature", tip, "land it", lock=lock,
                    staged_wait="0")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        # the park-for-operator route keeps today's refusal shape
        self.assertIn("refuse: staged state exists in the primary index", proc.stdout)
        self.assertIn("f01.txt: unattributed", proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    # ---- the concurrent-writer block arm ------------------------------------

    def test_land_concurrent_writer_block_named(self):
        repo, lock = self.locked_repo("dirty-writer")
        tip = self.conflict_setup(repo)
        # notes.txt is tracked, clean at snapshot, and outside the branch diff
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")

        proc = land(repo, "feature", tip, "land it", lock=lock,
                    fault="dirty-writer", fault_path="notes.txt")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn("dirty-writer", proc.stdout)
        self.assertIn("LAND_SQUASH_TEST_FAULT", proc.stdout)

        # the writer path carries the writer's bytes, skipped and named
        self.assertIn("writer line appended after the snapshot\n",
                      (repo / "notes.txt").read_text())
        self.assertIn("notes.txt", proc.stdout)
        self.assertIn("skipped", proc.stdout)

        # every staged merge path is restored; no other path moved
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout,
                         " M notes.txt\n")
        self.assertFalse((repo / "added.txt").exists())
        self.assertIn("base main\n", (repo / "shared.txt").read_text())

    # ---- the post-landing interleaved-tip refusal ----------------------------

    def test_land_post_tip_interleaved_refusal(self):
        repo, lock = self.locked_repo("backward-peer")
        main_tip = commit_file(repo, "main-file.txt", "main\n", "main work")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "landed.txt", "landed\n", "feature work")
        git(repo, "checkout", "-q", "main")
        fault_commit = rev(repo, "%s~1" % main_tip)
        self.assertNotEqual(fault_commit, main_tip)

        proc = land(repo, "feature", main_tip, "land it", lock=lock,
                    fault="backward-peer")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn("backward-peer", proc.stdout)
        self.assertIn("no longer descends from pre-landing tip", proc.stdout)
        self.assertIn("interleaved tip", proc.stdout)
        self.assertIn(fault_commit, proc.stdout)

        # the base ref sits at the fault commit (the peer's commit; the clean
        # inverse-CAS-landed arm is unreachable through the pre-tip leg)
        self.assertEqual(rev(repo, "refs/heads/main"), fault_commit)
        # the staged merge is restored path-exclusively; no other path moved
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")

    # ---- the diverge-origin informational note on the pass path --------------

    def test_land_origin_leg_divergence_note(self):
        repo, lock = self.locked_repo("diverge-origin")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "landed.txt", "landed\n", "feature work")
        git(repo, "checkout", "-q", "main")
        # a forged origin ref at a commit that is not an ancestor of the
        # landing commit (a sibling child of the pre-landing tip)
        forged = commit_tree(repo, rev(repo, "%s^{tree}" % tip), tip)
        git(repo, "update-ref", "refs/remotes/land-squash-fault/diverged", forged)

        proc = land(repo, "feature", tip, "land it", lock=lock,
                    fault="diverge-origin")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("diverge-origin", proc.stdout)
        # the origin-only divergence is the gate's informational note (it
        # names the origin ref and states the descent fact), not a refusal
        # and not an operator duty
        self.assertIn(
            "note: default branch does not descend from"
            " refs/remotes/land-squash-fault/diverged; the divergence predates"
            " the landing", proc.stdout)
        self.assertNotIn("operator reconciliation", proc.stdout)

        # the landing is kept: the base ref equals the new landing commit
        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, tip)
        self.assertEqual(rev(repo, "%s^" % landing), tip)
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))
        # the real remote-tracking ref is untouched (absent in the fixture)
        real = git(repo, "rev-parse", "--verify", "--quiet",
                   "refs/remotes/origin/main", check=False)
        self.assertNotEqual(real.returncode, 0)
        # the checkout is clean
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")

    # ---- the parentage pre-swap refusal propagation ---------------------------

    def test_land_preswap_refusal_restores(self):
        repo, lock = self.locked_repo("preswap-refusal")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        git(repo, "commit", "-q", "--allow-empty", "-m", "empty branch commit")
        git(repo, "checkout", "-q", "main")

        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("tree-identical", proc.stdout)
        # path-exclusive restore left nothing behind
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")

    # ---- the stale-base tree-equality refusal ---------------------------------

    def test_land_stale_base_tree_refused(self):
        repo, lock = self.locked_repo("stale-tree")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feature-file.txt", "feature\n", "feature work")
        git(repo, "checkout", "-q", "main")
        tip = commit_file(repo, "main-file.txt", "main\n", "main moved on")

        proc = land(repo, "feature", tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("main-file.txt", proc.stdout)
        self.assertIn("re-derive", proc.stdout)
        self.assertIn("rebase", proc.stdout)
        # the composed index was restored after the refusal
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")

    # ---- the stale-record base-pin refusal -------------------------------------

    def test_land_expected_base_stale_record_refused(self):
        repo, lock = self.locked_repo("stale-record")
        base = rev(repo, "refs/heads/main")
        tip = commit_file(repo, "main-file.txt", "main\n", "main work")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "landed.txt", "landed\n", "feature work")
        git(repo, "checkout", "-q", "main")

        # the recorded pin names the base commit, but the branch forked at the
        # main tip: a silent rebase under a stale record
        proc = land(repo, "feature", tip, "land it", expected_base=base, lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("base pin", proc.stdout)
        self.assertIn(base, proc.stdout)
        self.assertIn(tip, proc.stdout)
        # path-exclusive restore left nothing behind
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assertEqual(git(repo, "diff", "--cached", "--name-only", "HEAD").stdout, "")

    # ==== land-worktree mode: the worktree-complete landing ================

    def worktree_repo(self, name="wt-repo"):
        """A primary repo whose main carries one advance past the init commit
        (so the verified base tip's parent exists for the fault seams), a
        linked source worktree checked out on branch `feature`, and a live
        merge lock keyed to the primary checkout."""
        repo = make_repo(self.tmp / name)
        commit_file(repo, "main-base.txt", "main base\n", "main base work")
        wt = self.tmp / (name + "-source-wt")
        git(repo, "worktree", "add", "-q", "-b", "feature", str(wt))
        lock = acquire_merge_lock(repo, self.locks)
        return repo, wt, lock

    def archive_fixture(self, name, plan_rel, plan_body):
        """A primary repo plus a source worktree whose branch renames a
        plans-root file into docs/history/plans/completed/ (the archive
        ceremony's egress shape). Returns (repo, wt, lock, source_tip,
        completed_rel)."""
        repo = make_repo(self.tmp / name)
        commit_file(repo, "main-base.txt", "main base\n", "main base work")
        commit_file(repo, plan_rel, plan_body, "add plan")
        wt = self.tmp / (name + "-source-wt")
        git(repo, "worktree", "add", "-q", "-b", "feature", str(wt))
        completed_rel = "docs/history/plans/completed/" + plan_rel.rsplit("/", 1)[-1]
        completed_path = wt / completed_rel
        completed_path.parent.mkdir(parents=True, exist_ok=True)
        git(wt, "mv", plan_rel, completed_rel)
        git(wt, "commit", "-q", "-m", "archive the plan")
        lock = acquire_merge_lock(repo, self.locks)
        return repo, wt, lock, rev(wt, "HEAD"), completed_rel

    def test_land_worktree_green_path(self):
        # the worktree-complete landing: a verified merge lock, the source
        # worktree on the branch at the expected tip, a clean tree; the base
        # branch moves by one two-value compare-and-swap to a single-parent
        # commit whose tree equals the source branch tip's tree
        repo, wt, lock = self.worktree_repo("wt-green")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip, lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])

        landing = rev(repo, "refs/heads/main")
        parents = git(repo, "rev-list", "--parents", "-n", "1",
                      landing).stdout.split()
        self.assertEqual(parents, [landing, base_tip])
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))
        self.assertIn("new tip: %s" % landing, proc.stdout)
        self.assertIn("landed.txt", proc.stdout)

        # safety witness: the primary checkout carries exactly the landing's
        # bytes after the tail reconcile restored it (the worktree-complete
        # landing's stale-primary residue class is reconciled at the tail):
        # HEAD moved to exactly the landing commit, and index entries plus
        # the worktree match the landing tree with nothing left over.
        self.assertEqual(rev(repo, "HEAD"), landing)
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assertEqual((repo / "landed.txt").read_text(),
                         "landed by feature\n")
        self.assertIn("reconcile-receipt:", proc.stdout)
        receipt = repo / "docs" / "tmp" / "landing-receipts" / (
            "%s.txt" % landing)
        self.assertIn("exit code: 0", receipt.read_text())
        self.assertEqual(git(wt, "status", "--porcelain=v1").stdout, "")

    def test_land_worktree_dirty_source_worktree_refused(self):
        # a source worktree whose working-tree bytes differ from the branch
        # tip: tree inequality refused before the ref move, both refs
        # untouched, the divergent condition named
        repo, wt, lock = self.worktree_repo("wt-dirty")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "f01.txt", "f01 branch\n", "branch edit")
        source_tip = rev(wt, "HEAD")
        (wt / "f01.txt").write_text("f01 dirty worktree bytes\n")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("tree inequality", proc.stdout)
        self.assertIn("f01.txt", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_lock_mismatch_refused_before_composition(self):
        # a lock record whose token does not match the invoking environment:
        # the start is refused before any composition
        repo, wt, lock = self.worktree_repo("wt-lock")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             lock=lock, lock_token_override="forged-token")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("lock_token", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_stale_base_check_landing_refused(self):
        # a source branch tip that does not contain the recorded base: the
        # wired check-landing refusal names the stale merge base and the
        # would-delete paths, and the landing is deferred
        repo, wt, lock = self.worktree_repo("wt-stale")
        fork_point = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        main_tip = commit_file(repo, "main-file.txt", "main\n", "main advance")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("stale base", proc.stdout)
        self.assertIn(fork_point, proc.stdout)
        self.assertIn("would delete from target: main-file.txt", proc.stdout)
        self.assertIn(main_tip, proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), main_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_plans_egress_refused_before_ref_move(self):
        # a landing whose changed paths egress the plans root without
        # evidence: check-archive refuses before the ref move with the
        # egress findings named
        plan_rel = "docs/history/plans/2026-01-01-widget.md"
        repo, wt, lock, source_tip, completed_rel = self.archive_fixture(
            "wt-egress", plan_rel, "# Plan: widget\n\nWork complete.\n")
        base_tip = rev(repo, "refs/heads/main")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("check-archive", proc.stdout)
        self.assertIn("plan-egress: %s -> %s" % (plan_rel, completed_rel),
                      proc.stdout)
        self.assertIn("missing evidence leg", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_sanctioned_plan_archive_passes(self):
        # a sanctioned plan-archive landing: checkboxes verified, the
        # exec-review record carrying the egress bytes' sha256 present only
        # in the run worktree's reviews home; check-archive passes and the
        # landing completes
        plan_rel = "docs/history/plans/2026-01-01-widget.md"
        repo, wt, lock, source_tip, completed_rel = self.archive_fixture(
            "wt-sanctioned", plan_rel, "# Plan: widget\n\nWork complete.\n")
        base_tip = rev(repo, "refs/heads/main")
        digest = hashlib.sha256((wt / completed_rel).read_bytes()).hexdigest()
        slug = plan_rel.rsplit("/", 1)[-1][:-3].split("-", 3)[3]
        record = wt / ".ai-playbook" / "reviews" / (
            "2026-01-01-widget-plan-review-%s-exec-r1.md" % slug)
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(
            "# execution review: widget\n\negress bytes sha256: %s\n" % digest)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip,
                             "land the sanctioned archive",
                             expected_base=base_tip, lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])

        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))
        self.assertEqual(rev(repo, "%s^" % landing), base_tip)
        self.assertEqual(rev(repo, "HEAD"), landing)
        # the record exists only in the run worktree's reviews home
        self.assertFalse((repo / ".ai-playbook" / "reviews").exists())

    def test_land_worktree_ack_egress_passthrough(self):
        # the flag without the matching Archive-egress-ack trailer in the
        # commit message: the trailer-mismatch refusal, both refs untouched
        plan_rel = "docs/history/plans/2026-01-01-ackme.md"
        repo, wt, lock, source_tip, completed_rel = self.archive_fixture(
            "wt-ack", plan_rel, "# Plan: ackme\n\nWork complete.\n")
        base_tip = rev(repo, "refs/heads/main")
        before = primary_state(repo)
        proc = land_worktree(repo, "feature", source_tip, "land it",
                             ack_egress=plan_rel, lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("is not verified by a matching", proc.stdout)
        self.assertIn(plan_rel, proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

        # the flag with the matching trailer riding --message: the
        # operator-ack pass
        message = ("land the acked archive\n\n"
                   "Archive-egress-ack: %s\n" % plan_rel)
        proc = land_worktree(repo, "feature", source_tip, message,
                             ack_egress=plan_rel, lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("ok: acknowledged plan egress (operator ack): %s" % plan_rel,
                      proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))

    def test_land_worktree_wrong_source_tip_refused(self):
        # shape 1: the source worktree's checked-out HEAD (an attached
        # checkout, so the source branch tip) is past the expected tip; the
        # tip refusal fires before any composition
        repo, wt, lock = self.worktree_repo("wt-tip-ref")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        first_tip = rev(wt, "HEAD")
        commit_file(wt, "more.txt", "more\n", "branch moved on")
        current_tip = rev(wt, "HEAD")
        before = primary_state(repo)
        proc = land_worktree(repo, "feature", first_tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("checked-out HEAD", proc.stdout)
        self.assertIn(first_tip, proc.stdout)
        self.assertIn(current_tip, proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(primary_state(repo), before)

        # shape 2: the worktree detached from the branch carries no branch
        # mapping in the worktree list, so the source worktree cannot be
        # resolved; the class mirrors land's detached primary HEAD tool error
        repo, wt, lock = self.worktree_repo("wt-tip-head")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        branch_tip = rev(wt, "HEAD")
        git(wt, "checkout", "-q", "--detach", "HEAD~1")
        detached_head = rev(wt, "HEAD")
        self.assertNotEqual(detached_head, branch_tip)
        before = primary_state(repo)
        proc = land_worktree(repo, "feature", branch_tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("no worktree checked out on the source branch: feature",
                      proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), branch_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_preswap_refusal(self):
        # the parentage pre-swap refusal propagates its outcome-contract line
        # with both refs untouched (the empty-diff branch: tree equality
        # holds, the pre-swap tree-identical leg refuses)
        repo, wt, lock = self.worktree_repo("wt-preswap")
        base_tip = rev(repo, "refs/heads/main")
        git(wt, "commit", "-q", "--allow-empty", "-m", "empty branch commit")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it", lock=lock)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("tree-identical", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_base_moved_before_cas_refused(self):
        # the fault seam's value: the base ref moved between the check-landing
        # pass and the compare-and-swap; the compare-and-swap refuses on the
        # old-value mismatch, both refs stand as the peer left them
        repo, wt, lock = self.worktree_repo("wt-base-mover")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        peer_tip = rev(repo, "%s~1" % base_tip)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             lock=lock, fault="base-mover")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("base-mover", proc.stdout)
        self.assertIn("compare-and-swap ref move refused", proc.stdout)
        self.assertIn(base_tip, proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), peer_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(rev(repo, "HEAD"), peer_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_diverge_origin_keeps_landing(self):
        # the diverge-origin post-landing state is informational: the landing
        # kept on the pass path, the gate's note stating the descent fact (the
        # divergence predates the landing), the base ref left at the landing
        # commit
        repo, wt, lock = self.worktree_repo("wt-diverge")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        forged = commit_tree(repo, rev(repo, "%s^{tree}" % base_tip), base_tip)
        git(repo, "update-ref", "refs/remotes/land-squash-fault/diverged", forged)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             lock=lock, fault="diverge-origin")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("diverge-origin", proc.stdout)
        self.assertIn(
            "note: default branch does not descend from"
            " refs/remotes/land-squash-fault/diverged; the divergence predates"
            " the landing", proc.stdout)
        self.assertNotIn("operator reconciliation", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, base_tip)
        self.assertEqual(rev(repo, "%s^" % landing), base_tip)
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))
        self.assertEqual(rev(repo, "HEAD"), landing)
        # the tail reconcile restored the primary to the landing bytes
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assertEqual((repo / "landed.txt").read_text(), "landed\n")
        self.assertIn("reconcile-receipt:", proc.stdout)

    def test_land_worktree_backward_peer_indeterminate(self):
        # the backward-peer interleaved tip after the compare-and-swap: the
        # refused inverse compare-and-swap keeps the peer's tip and names the
        # attempted rollback target; no restore-report lines; the primary
        # checkout's index and working tree unchanged
        repo, wt, lock = self.worktree_repo("wt-backward-peer")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        peer_tip = rev(repo, "%s~1" % base_tip)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             lock=lock, fault="backward-peer")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn("backward-peer", proc.stdout)
        self.assertIn("no longer descends from pre-landing tip", proc.stdout)
        self.assertIn("interleaved tip", proc.stdout)
        self.assertIn(peer_tip, proc.stdout)
        # the attempted rollback target is the verified base tip, never the
        # source-worktree tip value carried by --expected-tip
        self.assertIn("attempted rollback target: %s" % base_tip, proc.stdout)
        self.assertNotIn("attempted rollback target: %s" % source_tip,
                         proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), peer_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertNotIn("restored to HEAD:", proc.stdout)
        self.assertNotIn("removed (created after the snapshot):", proc.stdout)
        self.assertNotIn("skipped (changed after the snapshot", proc.stdout)
        self.assertEqual(primary_state(repo), before)
        self.assertEqual(rev(repo, "HEAD"), peer_tip)

    def test_land_worktree_omission_scope_and_usage(self):
        # the omission scope: the mode's section holds no porcelain, restore,
        # snapshot, or merge-squash machinery, and its composition front-end
        # and both guard wirings are present
        script = HELPER.read_text()
        start_marker = "# ---- land-worktree mode:"
        end_marker = "# ---- land mode:"
        self.assertIn(start_marker, script)
        self.assertIn(end_marker, script)
        section = script.split(start_marker, 1)[1].split(end_marker, 1)[0]
        for token in ("git status", "status --porcelain", "run_restore",
                      "restore_or_stop", "print_restore_report",
                      "git restore", "load_snapshot", "merge --squash"):
            self.assertNotIn(token, section,
                             "land-worktree must not invoke %r" % token)
        for token in ("GIT_INDEX_FILE", "read-tree", "update-index",
                      "write-tree", "commit-tree", "check-landing",
                      "check-archive", "REVERSE_GUARD",
                      "--ack-egress", "worktree list"):
            self.assertIn(token, section)
        # the wired guard resolves adjacent to the helper, the $SCRIPT_DIR
        # precedent the parentage gate sets
        self.assertIn('REVERSE_GUARD="$SCRIPT_DIR/reverse_squash_guard.py"',
                      script)

        # the usage text names the mode, the per-mode seam reword, and the
        # passthrough
        proc = subprocess.run(["bash", str(HELPER), "--help"],
                              capture_output=True, text=True,
                              env=base_env(), check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for token in ("land-worktree", "base-mover", "check-landing",
                      "check-archive", "--ack-egress"):
            self.assertIn(token, proc.stdout)


class ReconcileTailGateTest(LandSquashHelperTest):
    """The landing-tail reconcile receipt gate: both helper modes run the
    post-landing reconciliation under the lock, write the receipt, and route
    the completion verdict on it."""

    def receipt_text(self, repo, landing):
        return (repo / "docs" / "tmp" / "landing-receipts" / (
            "%s.txt" % landing)).read_text()

    def test_land_worktail_restores_second_live_checkout(self):
        # a second live checkout of the base branch (detached at the base
        # tip) carrying pre-landing bytes: the tail reconcile restores it,
        # the receipt records exit 0, OUTCOME pass
        repo, wt, lock = self.worktree_repo("wt-tail-restore")
        base_tip = rev(repo, "refs/heads/main")
        second = self.tmp / "wt-tail-second"
        git(repo, "worktree", "add", "-q", "--detach", str(second), base_tip)
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip, lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("reconcile-receipt:", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        receipt = self.receipt_text(repo, landing)
        self.assertIn("exit code: 0", receipt)
        # the receipt names the second checkout's bring-current row
        self.assertIn("synced %s " % os.path.realpath(str(second)), receipt)
        # the second checkout was brought current (fast-forwarded to the
        # landing commit)
        self.assertEqual(rev(second, "HEAD"), landing)
        self.assertEqual((second / "landed.txt").read_text(),
                         "landed by feature\n")

    def test_land_tail_block_rows_recorded_landing_completes(self):
        # the second live checkout carries a genuine local edit on a landing
        # path: reconcile exit 1, every block row printed, the receipt
        # recording the rows, OUTCOME pass, the landed ref intact
        repo, wt, lock = self.worktree_repo("wt-tail-block")
        base_tip = rev(repo, "refs/heads/main")
        second = self.tmp / "wt-tail-second"
        git(repo, "worktree", "add", "-q", "--detach", str(second), base_tip)
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")
        (second / "landed.txt").write_text("genuine local edit\n")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip, lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("block", proc.stdout)
        self.assertIn("sanctioned partial state", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "refs/heads/main"), landing)
        receipt = self.receipt_text(repo, landing)
        self.assertIn("exit code: 1", receipt)
        # the second checkout's refusal is the recorded block row (its dirty
        # landing path refuses the fast-forward; the restore never touches it)
        self.assertIn("ff-refused", receipt)
        self.assertIn("block ", receipt)
        self.assertEqual((second / "landed.txt").read_text(),
                         "genuine local edit\n")

    def test_fault_seam_reconcile_tool_failure_land_mode(self):
        # land mode: the reconcile-tool-failure seam forces the reconcile-gate
        # refusal; the landed ref stays moved, the receipt records the
        # failure, the remedy names the re-run command
        repo, lock = self.locked_repo("tail-fault-land")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "landed.txt", "landed\n", "feature work")
        git(repo, "checkout", "-q", "main")

        proc = land(repo, "feature", tip, "land feature", lock=lock,
                    fault="reconcile-tool-failure")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("reconcile-gate", proc.stdout)
        self.assertIn("reconcile-tool-failure", proc.stdout)
        self.assertIn("remedy: re-run", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, tip)
        self.assertEqual(landing,
                         git(repo, "rev-parse", "refs/heads/main").stdout.strip())
        receipt = self.receipt_text(repo, landing)
        self.assertIn("exit code: 2", receipt)

    def test_fault_seam_reconcile_tool_failure_land_worktree_mode(self):
        # land-worktree mode: the same seam, the same refusal shape, the
        # landed ref kept
        repo, wt, lock = self.worktree_repo("wt-tail-fault")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip, lock=lock,
                             fault="reconcile-tool-failure")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("reconcile-gate", proc.stdout)
        self.assertIn("remedy: re-run", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, base_tip)
        receipt = self.receipt_text(repo, landing)
        self.assertIn("exit code: 2", receipt)


if __name__ == "__main__":
    unittest.main()
