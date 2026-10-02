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
the interleaved-tip and divergence-note post-landing arms, the parentage
pre-swap refusal propagation, the stale-base tree-equality refusal, and the
stale-record base-pin refusal."""

import os
import subprocess
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
               with_lock_env=True):
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

    # ---- the origin-leg-only divergence note arm ------------------------------

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
        self.assertIn("divergence", proc.stdout)
        self.assertIn("operator reconciliation", proc.stdout)

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


if __name__ == "__main__":
    unittest.main()
