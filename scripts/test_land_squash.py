#!/usr/bin/env python3
"""Selftest for land_squash.sh: scratch-repo fixtures driving the lock-bound
squash-landing helper via subprocess for every refusal, restore, and outcome
class. Covered classes: the probe modes with their no-mutation assertion, the
probe's tracked-ignored warning on force-tracked branch-delta paths (and its
clean-branch silence), the lock-authenticity classes (unset, empty,
nonexistent, meta-less, empty-token,
mismatched, sibling-repo), the wrong-HEAD and tip-moved refusals, the green
path with tree equality and base-pin forwarding, the unresolvable-branch tool
error, the dirty-intersection and staged pre-refusals, the record-only
intersection pre-refusal, the merge-failure path-exclusive restore with its
dirty-at-snapshot carve-out, the dirty-writer concurrent-writer block arm,
the interleaved-tip post-landing arm and the diverge-origin informational
note, the parentage pre-swap refusal propagation, the stale-base
tree-equality refusal, and the stale-record base-pin refusal, plus the
compose-time landing-claim grammar notice (the free-form warning line with
the landing outcome unchanged, the grammar-message silence, the
guard-import-failure note in land mode, and the no-helper-copy audit over
the guard constant). The
land-worktree mode (the worktree-complete landing class) is covered by its
own cases: the green path with the primary checkout byte-unchanged witness,
the dirty-source-worktree tree-inequality refusal, the lock-mismatch refusal
before composition, the wired check-landing stale-base refusal, the wired
check-archive plans-egress refusal and its sanctioned-archive and
operator-ack pass shapes, the wrong-source-tip refusals, the parentage
pre-swap refusal, the base-mover compare-and-swap refusal, the diverge-origin
informational note, the backward-peer indeterminate arm, and the
omission-scope and usage-text audit. The wired prompt-log prune audit
carries its own cases: a code-only range invokes no audit, a receipted
removal passes with the PRUNE-OK line retained and exactly one audit call,
the receipt names the pinned <merge-base>..<source-tip> range, a
receipt-less removal refuses before any ref move with the single direct
repair, a changed-then-reverted log and a log rename each run one audit
call, a bare-deleting receipt-line revert refuses before any ref move with
the named remedy, both logs touched run one invocation, a deleted touched log anchors
on the surviving sibling, and the checker's tool error and an unclassified
exit (the test-only prune-audit-unclassified seam) preserve diagnostics and
refs."""

import atexit
import hashlib
import importlib.util
import os
import shutil
import subprocess
import time
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
HELPER = SCRIPTS / "land_squash.sh"
DONE_LOCK = SCRIPTS / "done-lock.sh"

PROMPT_LOG_PLAN_REL = "docs/history/backlog/PLAN-PROMPTS.md"
PROMPT_LOG_EXEC_REL = "docs/history/backlog/EXEC-PROMPTS.md"

# The fixture logs' shape mirrors the checker suite's: an entry-template
# fence in the header (so the placeholder heading never parses as an
# entry), then one ## <slug> section per entry.
PROMPT_LOG_FENCE = (
    "Entry template (one section per entry):\n\n"
    "```\n"
    "## <short-slug>\n"
    "```\n"
)


def prompt_log_text(entries):
    return "Tracked rolling log fixture.\n\n" + PROMPT_LOG_FENCE + "\n".join(entries)


def prompt_log_ledger_text(entries, receipts):
    header = "".join("%s\n" % receipt for receipt in receipts)
    return (
        "Tracked rolling log fixture.\n\n"
        + header
        + "\n"
        + PROMPT_LOG_FENCE
        + "\n".join(entries)
    )


def prompt_log_entry(slug):
    return "## %s\n\nAdded: fixture provenance\n\nPrompt: fixture payload\n" % slug


def load_guard_module():
    """The guard script imported as a module: the fixture layer reads the
    recognized landing-claim prefixes from the same single source the
    helper's compose-time notice reads, so no fixture restates the
    grammar."""
    spec = importlib.util.spec_from_file_location(
        "reverse_squash_guard_test", str(SCRIPTS / "reverse_squash_guard.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD_MODULE = load_guard_module()


_EMPTY_CONFIG_HOME = None


def empty_config_home():
    """One empty directory per suite run, created lazily so every base_env()
    call pins the same path (git only reads its XDG home, never writes one).
    Registered for atexit removal so the suite stops leaking temp dirs."""
    global _EMPTY_CONFIG_HOME
    if _EMPTY_CONFIG_HOME is None:
        _EMPTY_CONFIG_HOME = tempfile.mkdtemp(prefix="land-squash-empty-home-")
        atexit.register(shutil.rmtree, _EMPTY_CONFIG_HOME, True)
    return _EMPTY_CONFIG_HOME


_SUITE_LOCK_ROOT = None


def suite_lock_root():
    """One merge-lock parent directory per suite run: the root the helper's
    internal swap-critical-section acquire keys through (MERGE_LOCK_ROOT)
    and the root the held-lock fixtures acquire against, so contention
    between a fixture hold and a helper acquire lands on the same keyed
    lock. Lock state keys per repo inside the root, so distinct scratch
    repos never share a lock."""
    global _SUITE_LOCK_ROOT
    if _SUITE_LOCK_ROOT is None:
        _SUITE_LOCK_ROOT = tempfile.mkdtemp(prefix="land-squash-lock-root-")
        atexit.register(shutil.rmtree, _SUITE_LOCK_ROOT, True)
    return _SUITE_LOCK_ROOT


def base_env():
    """A clean environment: no inherited GIT_* or lock/seam variables.
    HOME and XDG_CONFIG_HOME are pinned to an empty directory (mirroring the
    done-sweep suite's sweep_env hermeticity): git consults
    $XDG_CONFIG_HOME/git/ignore and $HOME/.config/git/ignore regardless of
    GIT_CONFIG_GLOBAL, so an ambient global ignore would flip the suite's
    exact-count warning assertions into false failures."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    empty_home = empty_config_home()
    env["HOME"] = empty_home
    env["XDG_CONFIG_HOME"] = empty_home
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    for key in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN",
                "DONE_LOCK_DIR", "DONE_LOCK_TOKEN",
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


def force_track_ignored(root, *rel_paths):
    """The done-sweep suite's force-add precedent: seed paths under an
    ignored directory and track them with `git add -f`, committed on the
    current branch; returns the new tip."""
    for rel in rel_paths:
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("force-tracked %s\n" % Path(rel).name)
    git(root, "add", "-f", "--", *rel_paths)
    git(root, "commit", "-q", "-m", "force-track ignored paths")
    return rev(root, "HEAD")


def acquire_merge_lock(repo, lock_root=None):
    """Acquire a live merge lock on repo via done-lock.sh; returns (dir, token).
    The lock root defaults to the suite root so a held lock and the helper's
    internal swap-critical-section acquire key identically."""
    env = base_env()
    env["MERGE_LOCK_ROOT"] = str(lock_root or suite_lock_root())
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


def acquire_done_lock(repo, lock_root=None):
    """Acquire a live primary done lock on repo via done-lock.sh; returns
    (dir, token). The lock root defaults to a git-internal directory so the
    fixture never adds porcelain-visible paths to the scratch repo."""
    env = base_env()
    env["DONE_LOCK_ROOT"] = str(lock_root or (Path(repo) / ".git" / "done-locks"))
    env["DONE_LOCK_HOLDER_PID"] = str(os.getpid())
    proc = subprocess.run(
        ["bash", str(DONE_LOCK), "acquire", "--label", "fixture"],
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
    # The session fence is done-lock's status witness, not fixture state:
    # remove it so the scratch repo carries only fixture-created paths.
    session = Path(repo) / ".ai-playbook" / "done-lock.session"
    try:
        session.unlink()
        session.parent.rmdir()
    except OSError:
        pass
    return values["DONE_LOCK_DIR"], values["DONE_LOCK_TOKEN"]


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
    """HEAD sha, index stage entries, porcelain, and the ignored set: the
    no-mutation witness (the ignored snapshot makes a write into an ignored
    directory visible to the no-mutation assertions, which the untracked
    porcelain arm alone never reports)."""
    return (
        rev(root, "HEAD"),
        git(root, "ls-files", "-s").stdout,
        git(root, "status", "--porcelain=v1").stdout,
        git(root, "ls-files", "--others", "--ignored", "--exclude-standard").stdout,
    )


def outcome_lines(proc):
    return [line for line in proc.stdout.splitlines()
            if line.startswith("OUTCOME:")]


def run_helper(args, cwd, lock=None, fault=None, fault_path=None,
               lock_dir_override=None, lock_token_override=None,
               with_lock_env=True, staged_wait=None, done_lock=None,
               lock_root=None, poll_secs=None, swap_wait=None):
    """Run the helper in the scratch repo; the lock env is injected only when
    with_lock_env is true (probe runs without it, per its contract).
    MERGE_LOCK_ROOT is always pinned to a suite-level scratch root so the
    land-worktree mode's internal swap-critical-section acquire never keys
    against the operator's real lock home; lock_root overrides it (a held
    lock and the helper must share the root for contention tests)."""
    env = base_env()
    if with_lock_env and lock is not None:
        env["MERGE_LOCK_DIR"] = lock_dir_override if lock_dir_override is not None else lock[0]
        env["MERGE_LOCK_TOKEN"] = lock_token_override if lock_token_override is not None else lock[1]
    env["MERGE_LOCK_ROOT"] = str(lock_root) if lock_root is not None else suite_lock_root()
    if poll_secs is not None:
        env["MERGE_LOCK_POLL_SECS"] = str(poll_secs)
    if swap_wait is not None:
        env["LAND_SQUASH_SWAP_LOCK_WAIT_SECS"] = str(swap_wait)
    if done_lock is not None:
        env["DONE_LOCK_DIR"] = done_lock[0]
        env["DONE_LOCK_TOKEN"] = done_lock[1]
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


def launch_helper(args, cwd, lock=None, fault=None, lock_root=None,
                  poll_secs=None, swap_wait=None):
    """Start the helper as a background process (the concurrency witness):
    returns (Popen, output file). stdout and stderr interleave into the
    file; poll it for markers while the process runs, then wait() and read."""
    env = base_env()
    if lock is not None:
        env["MERGE_LOCK_DIR"] = lock[0]
        env["MERGE_LOCK_TOKEN"] = lock[1]
    env["MERGE_LOCK_ROOT"] = str(lock_root) if lock_root is not None else suite_lock_root()
    if poll_secs is not None:
        env["MERGE_LOCK_POLL_SECS"] = str(poll_secs)
    if swap_wait is not None:
        env["LAND_SQUASH_SWAP_LOCK_WAIT_SECS"] = str(swap_wait)
    if fault is not None:
        env["LAND_SQUASH_TEST_FAULT"] = fault
    out = tempfile.TemporaryFile(mode="w+")
    proc = subprocess.Popen(
        ["bash", str(HELPER)] + args, stdout=out, stderr=subprocess.STDOUT,
        cwd=str(cwd), env=env)
    return proc, out


def land(root, branch, expected_tip, message, expected_base=None,
         done_lock="auto", **kwargs):
    """Run the land mode. done_lock="auto" acquires a primary done lock on
    root (the Primary land ownership fixture default); None omits the done
    environment (the missing-done matrix row); a (dir, token) tuple injects
    that environment verbatim."""
    if done_lock == "auto" and kwargs.get("lock") is not None:
        done_lock = acquire_done_lock(root)
    elif done_lock == "auto":
        done_lock = None
    args = ["land", "--branch", branch, "--expected-tip", expected_tip,
            "--message", message]
    if expected_base is not None:
        args += ["--expected-base", expected_base]
    return run_helper(args, cwd=root, done_lock=done_lock, **kwargs)


def land_worktree(root, branch, expected_tip, message, expected_base=None,
                  ack_egress=None, **kwargs):
    """Run the land-worktree mode from the primary checkout (cwd=root); the
    source worktree is addressed through the worktree list by --branch. The
    mode acquires its own swap-critical-section merge lock internally, so
    tests pass no caller-held lock env unless one is deliberately injected
    (the env-ignored witness)."""
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


class _LandSquashFixtureMixin:
    """Shared isolated fixture setup and constructors for landing tests."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def locked_repo(self, name="repo", extra_files=None):
        repo = make_repo(self.tmp / name, extra_files=extra_files)
        lock = acquire_merge_lock(repo)
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

    def staged_setup(self, name):
        repo, lock = self.locked_repo(name)
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        (repo / "f01.txt").write_text("f01 staged locally\n")
        git(repo, "add", "f01.txt")
        return repo, lock, tip

    def worktree_repo(self, name="wt-repo"):
        """Create a primary repo and linked feature worktree."""
        repo = make_repo(self.tmp / name)
        commit_file(repo, "main-base.txt", "main base\n", "main base work")
        wt = self.tmp / (name + "-source-wt")
        git(repo, "worktree", "add", "-q", "-b", "feature", str(wt))
        return repo, wt

    def worktree_repo_with_logs(self, name, plan_entries, exec_entries,
                                plan_text=None, exec_text=None):
        """Create a worktree fixture with both tracked prompt logs."""
        extra = {
            PROMPT_LOG_PLAN_REL: (
                plan_text if plan_text is not None
                else prompt_log_text([prompt_log_entry(s) for s in plan_entries])
            ),
            PROMPT_LOG_EXEC_REL: (
                exec_text if exec_text is not None
                else prompt_log_text([prompt_log_entry(s) for s in exec_entries])
            ),
        }
        repo = make_repo(self.tmp / name, extra_files=extra)
        commit_file(repo, "main-base.txt", "main base\n", "main base work")
        wt = self.tmp / (name + "-source-wt")
        git(repo, "worktree", "add", "-q", "-b", "feature", str(wt))
        return repo, wt

    def commit_log_change(self, wt, message):
        """Commit the source worktree's pending prompt-log edit."""
        git(wt, "add", "-A", "--", "docs/history/backlog")
        git(wt, "commit", "-q", "-m", message)

    def archive_fixture(self, name, plan_rel, plan_body):
        """Create a source worktree that archives a plans-root file."""
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
        return repo, wt, rev(wt, "HEAD"), completed_rel

    def assert_merge_lock_free(self, repo):
        env = base_env()
        env["MERGE_LOCK_ROOT"] = str(suite_lock_root())
        status = subprocess.run(
            ["bash", str(DONE_LOCK), "merge-status"], cwd=str(repo), env=env,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("free", status.stdout)


class LandSquashHelperTest(_LandSquashFixtureMixin, unittest.TestCase):

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

    # ---- probe tracked-ignored warning ---------------------------------

    def test_probe_warns_on_force_tracked_ignored_paths(self):
        # a source branch whose delta force-tracks three paths under an
        # ignored directory (one of them non-ASCII): the probe names each
        # path on its own warning line and still exits with the pass
        # verdict; the warning is report-only (no exit-code or verdict
        # change, no mutation). A base-inherited tracked-ignored path
        # (force-tracked and committed on main BEFORE the branch forked,
        # untouched by the branch) never warns: the predicate is the branch
        # delta, not a source-tree-wide scan.
        repo = make_repo(self.tmp / "tracked-ignored", extra_files={
            ".gitignore": "docs/tmp/\n.ai-playbook/\n"})
        force_track_ignored(repo, ".ai-playbook/inherited/base-inherited.md")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        force_track_ignored(repo, ".ai-playbook/review-certs/seal-a.md",
                            ".ai-playbook/review-certs/seal-b.md",
                            ".ai-playbook/review-certs/seal-é.md")
        git(repo, "checkout", "-q", "main")
        before = fingerprint(repo)

        proc = probe(repo, "feature")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        for path in (".ai-playbook/review-certs/seal-a.md",
                     ".ai-playbook/review-certs/seal-b.md",
                     ".ai-playbook/review-certs/seal-é.md"):
            self.assertEqual(
                proc.stdout.count(
                    "warning: tracked-ignored path on the branch delta: %s"
                    % path),
                1, proc.stdout)
        # the non-ASCII path warns as raw path bytes, never git's C-quoted
        # octal form (the quotePath pin sits on check-ignore's stdout)
        self.assertNotIn("\\303\\251", proc.stdout)
        # the base-inherited path never warns (tracked on main, absent
        # from the branch delta)
        self.assertEqual(
            proc.stdout.count(
                "warning: tracked-ignored path on the branch delta: "
                ".ai-playbook/inherited/base-inherited.md"),
            0, proc.stdout)
        # exactly the three matched delta paths warn; the non-ignored delta
        # path (feat.txt) and the base-inherited path never do
        self.assertEqual(proc.stdout.count("warning:"), 3, proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    def test_probe_warns_once_on_addition_and_silent_on_riding_untrack(self):
        # a branch that force-tracks a new ignored path AND untracks a
        # base-side tracked-ignored path in the same delta: the probe warns
        # exactly once on the addition and stays silent on the removal
        # (--diff-filter pins the deletion silence; a landing that untracks
        # inherited paths never warns about its own cleanup)
        repo = make_repo(self.tmp / "warn-untrack", extra_files={
            ".gitignore": "docs/tmp/\n.ai-playbook/\n"})
        force_track_ignored(repo, ".ai-playbook/base/base-side.md")
        git(repo, "checkout", "-q", "-b", "feature")
        force_track_ignored(repo, ".ai-playbook/review-certs/seal-a.md")
        git(repo, "rm", "--cached", "-q", "--", ".ai-playbook/base/base-side.md")
        git(repo, "commit", "-q", "-m", "untrack base-side tracked-ignored path")
        git(repo, "checkout", "-q", "main")
        before = fingerprint(repo)

        proc = probe(repo, "feature")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(
            proc.stdout.count(
                "warning: tracked-ignored path on the branch delta: "
                ".ai-playbook/review-certs/seal-a.md"),
            1, proc.stdout)
        # the riding removal never warns
        self.assertNotIn(".ai-playbook/base/base-side.md", proc.stdout)
        # the addition is the only warning line
        self.assertEqual(proc.stdout.count("warning:"), 1, proc.stdout)
        self.assertEqual(fingerprint(repo), before)

    def test_probe_clean_branch_prints_no_tracked_ignored_warning(self):
        # a clean (non-ignored-delta) branch over the same seeded ignore
        # rule: no warning line, the existing pass verdict unchanged
        repo = make_repo(self.tmp / "clean-no-warning", extra_files={
            ".gitignore": "docs/tmp/\n.ai-playbook/\n"})
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        before = fingerprint(repo)

        proc = probe(repo, "feature")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertNotIn("warning: tracked-ignored", proc.stdout)
        self.assertNotIn("warning: tracked-ignored", proc.stderr)
        self.assertEqual(fingerprint(repo), before)

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

    # ---- the compose-time landing-claim grammar notice -----------------------

    def test_land_free_form_message_warns_once_and_lands_unchanged(self):
        # a landing message whose first line matches no recognized prefix:
        # exactly one warning line naming the grammar read from the guard
        # constant through the module import, and the landing outcome
        # unchanged (pass, the landing commit composed with the warned
        # subject on the pre-landing tip with the branch tree)
        repo, lock = self.locked_repo("grammar-warn")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "landed.txt", "landed\n", "feature work")
        git(repo, "checkout", "-q", "main")
        branch_tree = rev(repo, "feature^{tree}")

        proc = land(repo, "feature", tip, "skills: separate the vendored twins",
                    lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(
            proc.stdout.count(
                "warning: landing message subject matches no recognized"
                " landing-claim grammar prefix"),
            1, proc.stdout)
        # the warning names every recognized prefix, read from the guard
        # constant (no helper-local restatement of the grammar)
        for prefix, _kind in GUARD_MODULE.LANDING_CLAIM_PREFIXES:
            self.assertIn(repr(prefix), proc.stdout)
        # the landing itself is unchanged by the notice
        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, tip)
        self.assertEqual(rev(repo, "%s^" % landing), tip)
        self.assertEqual(rev(repo, "%s^{tree}" % landing), branch_tree)
        self.assertEqual(
            git(repo, "log", "-1", "--format=%s", landing).stdout.strip(),
            "skills: separate the vendored twins")

    def test_land_grammar_message_no_warning(self):
        # a landing message whose first line carries a recognized prefix:
        # no warning line and behavior identical to today. Post-remap
        # expectation (plan docs/history/plans/2026-11-04-execution-lane-
        # authored-plans-misread-as-landed.md Task 2): the authoring-verb
        # subject is `plans: file` and its diff is plans-only, so neither
        # the unrecognized-prefix warning nor the mismatch warning fires.
        repo, lock = self.locked_repo("grammar-conformant")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "docs/history/plans/2026-10-23-widget-plan.md",
                    "# Plan: widget\n", "feature work")
        git(repo, "checkout", "-q", "main")

        proc = land(repo, "feature", tip,
                    "plans: file 2026-10-23-widget-plan (authored plan; "
                    "execution pending)",
                    lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertNotIn("warning:", proc.stdout)
        self.assertNotIn("grammar notice", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^" % landing), tip)

    def test_land_grammar_mismatch_warning_authoring_verb_operative_diff(self):
        # the verb/diff mismatch arm (warning-only): an authoring-family
        # subject whose landing diff carries operative-scope bytes prints
        # one mismatch warning; the landing outcome is unchanged
        repo, lock = self.locked_repo("grammar-mismatch-authoring")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "docs/history/plans/2026-10-23-widget-plan.md",
                    "# Plan: widget\n", "plan bytes")
        commit_file(repo, "scripts/operative.py", "x = 1\n", "operative bytes")
        git(repo, "checkout", "-q", "main")
        branch_tree = rev(repo, "feature^{tree}")

        proc = land(repo, "feature", tip,
                    "plans: file 2026-10-23-widget-plan (authored plan)",
                    lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(
            proc.stdout.count("warning: landing-claim verb/diff mismatch"),
            1, proc.stdout)
        self.assertIn("scripts/operative.py", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^{tree}" % landing), branch_tree)

    def test_land_grammar_mismatch_warning_retired_verb_operative_diff(self):
        # a retired-verb subject whose operative diff contradicts its
        # family's expectation prints the same mismatch warning
        repo, lock = self.locked_repo("grammar-mismatch-retired")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "scripts/operative.py", "x = 1\n", "operative bytes")
        git(repo, "checkout", "-q", "main")

        proc = land(repo, "feature", tip,
                    "plans: land retired-plan (combined landing)",
                    lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(
            proc.stdout.count("warning: landing-claim verb/diff mismatch"),
            1, proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^" % landing), tip)

    def test_land_grammar_no_mismatch_for_execution_verbs(self):
        # the execution verbs' operative diffs are their expectation: no
        # mismatch warning
        repo, lock = self.locked_repo("grammar-execution-conformant")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "scripts/operative.py", "x = 1\n", "operative bytes")
        git(repo, "checkout", "-q", "main")

        proc = land(repo, "feature", tip,
                    "execute-plan: land exec-plan-thing (the landing)",
                    lock=lock)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertNotIn("warning: landing-claim verb/diff mismatch",
                         proc.stdout)

    def test_land_guard_import_failure_note(self):
        # a missing guard copy at the notice point (land mode): one note
        # line and an unchanged landing; the land-worktree mode refuses a
        # missing guard copy at the wired check-landing gate before the
        # notice point, so this class is land-mode-only by construction
        scratch = self.tmp / "guardless-scripts"
        scratch.mkdir()
        shutil.copy(str(HELPER), str(scratch / "land_squash.sh"))
        for name in ("landing_parentage_gate.py", "reconcile_post_landing.py"):
            shutil.copy(str(SCRIPTS / name), str(scratch / name))
        # reverse_squash_guard.py is deliberately absent from the scratch
        # scripts home the copied helper resolves: the notice's guard import
        # fails there while the landing path stays guard-free (land mode
        # touches the guard at the notice point only)
        repo, lock = self.locked_repo("grammar-import-failure")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "landed.txt", "landed\n", "feature work")
        git(repo, "checkout", "-q", "main")

        env = base_env()
        env["MERGE_LOCK_DIR"] = lock[0]
        env["MERGE_LOCK_TOKEN"] = lock[1]
        done = acquire_done_lock(repo)
        env["DONE_LOCK_DIR"] = done[0]
        env["DONE_LOCK_TOKEN"] = done[1]
        proc = subprocess.run(
            ["bash", str(scratch / "land_squash.sh"), "land",
             "--branch", "feature", "--expected-tip", tip,
             "--message", "skills: separate the vendored twins"],
            capture_output=True, text=True, check=False, cwd=str(repo),
            env=env)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(
            proc.stdout.count(
                "note: the landing-claim grammar notice could not import"
                " the guard module"),
            1, proc.stdout)
        self.assertNotIn("warning: landing message subject", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^" % landing), tip)

    def test_land_notice_reads_guard_constant_not_a_helper_copy(self):
        # the helper text carries no literal copy of the recognized prefix
        # set: the grammar lives once, in the guard constant
        script = HELPER.read_text()
        for prefix, _kind in GUARD_MODULE.LANDING_CLAIM_PREFIXES:
            self.assertNotIn(prefix, script)

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

    def test_land_worktree_green_path(self):
        # the worktree-complete landing: a verified merge lock, the source
        # worktree on the branch at the expected tip, a clean tree; the base
        # branch moves by one two-value compare-and-swap to a single-parent
        # commit whose tree equals the source branch tip's tree
        repo, wt = self.worktree_repo("wt-green")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
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
        # the swap-critical-section lock was acquired and released inside
        # the invocation (no caller-held lock env existed)
        self.assert_merge_lock_free(repo)

    def test_land_worktree_dirty_source_worktree_refused(self):
        # a source worktree whose working-tree bytes differ from the branch
        # tip: tree inequality refused before the ref move, both refs
        # untouched, the divergent condition named
        repo, wt = self.worktree_repo("wt-dirty")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "f01.txt", "f01 branch\n", "branch edit")
        source_tip = rev(wt, "HEAD")
        (wt / "f01.txt").write_text("f01 dirty worktree bytes\n")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("tree inequality", proc.stdout)
        self.assertIn("f01.txt", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_stale_caller_lock_env_is_ignored(self):
        # the narrowed span: the mode acquires its own swap-critical-section
        # merge lock internally, so stale caller exports (a released lock
        # directory and a forged token) play no role in the landing; the
        # exclusivity the old env gate verified is provided by construction
        # (the helper holds a lock it just acquired)
        repo, wt = self.worktree_repo("wt-env-ignored")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             lock_dir_override="/nonexistent/stale-lock-dir",
                             lock_token_override="forged-token")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))
        self.assertEqual(rev(repo, "%s^" % landing), base_tip)
        self.assertEqual(rev(repo, "HEAD"), landing)
        self.assertEqual(git(repo, "status", "--porcelain=v1").stdout, "")
        self.assert_merge_lock_free(repo)

    def test_land_worktree_swap_lock_contention_refused(self):
        # a merge lock already held when the helper reaches its swap
        # critical section: every pre-lock gate (check-landing, the wired
        # prune audit position, composition, tree equality, check-archive)
        # has already run, the bounded wait exhausts, and the refusal names
        # the holder with the primary checkout untouched; after the holder
        # releases, the same invocation lands
        repo, wt = self.worktree_repo("wt-swap-contention")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        held = acquire_merge_lock(repo)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             swap_wait=1, poll_secs=1)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        # the pre-lock gates ran before the bounded wait: the composition
        # evidence precedes the lock refusal
        self.assertIn("check-landing:", proc.stdout)
        self.assertIn("check-archive:", proc.stdout)
        self.assertIn("swap", proc.stdout)
        self.assertIn(held[0], proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

        # the holder releases; the retry acquires and lands
        env = base_env()
        env["MERGE_LOCK_DIR"] = held[0]
        env["MERGE_LOCK_TOKEN"] = held[1]
        env["MERGE_LOCK_ROOT"] = suite_lock_root()
        release = subprocess.run(
            ["bash", str(DONE_LOCK), "merge-release"], capture_output=True,
            text=True, check=False, cwd=str(repo), env=env)
        self.assertEqual(release.returncode, 0, release.stdout + release.stderr)
        retry = land_worktree(repo, "feature", source_tip, "land it",
                              expected_base=base_tip)
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assertEqual(outcome_lines(retry), ["OUTCOME: pass"])
        self.assertEqual(rev(repo, "%s^{tree}" % rev(repo, "refs/heads/main")),
                         rev(repo, "feature^{tree}"))
        self.assert_merge_lock_free(repo)

    def test_land_worktree_stale_base_check_landing_refused(self):
        # a source branch tip that does not contain the recorded base: the
        # wired check-landing refusal names the stale merge base and the
        # would-delete paths, and the landing is deferred
        repo, wt = self.worktree_repo("wt-stale")
        fork_point = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        main_tip = commit_file(repo, "main-file.txt", "main\n", "main advance")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it")
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
        repo, wt, source_tip, completed_rel = self.archive_fixture(
            "wt-egress", plan_rel, "# Plan: widget\n\nWork complete.\n")
        base_tip = rev(repo, "refs/heads/main")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it")
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
        repo, wt, source_tip, completed_rel = self.archive_fixture(
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
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])

        landing = rev(repo, "refs/heads/main")
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))
        self.assertEqual(rev(repo, "%s^" % landing), base_tip)
        self.assertEqual(rev(repo, "HEAD"), landing)
        # the record exists only in the run worktree's reviews home
        self.assertFalse((repo / ".ai-playbook" / "reviews").exists())

    # ---- wired prompt-log prune audit (land-worktree) -----------------

    def test_land_worktree_code_only_range_skips_prune_audit(self):
        # a branch that touches no prompt log: the landing follows the
        # existing path and the receipt carries no audit section at all
        repo, wt = self.worktree_repo("wt-no-log")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertNotIn("prune-audit:", proc.stdout)
        self.assertNotIn("prune-audit summary:", proc.stdout)
        self.assertNotEqual(rev(repo, "refs/heads/main"), base_tip)

    def test_land_worktree_receipted_removal_passes_with_prune_ok(self):
        # a receipted log removal: exactly one audit call, its passing
        # summary in the receipt, the PRUNE-OK line retained, the landing
        # completes
        repo, wt = self.worktree_repo_with_logs("wt-receipt", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text(
                [], ["PLAN-PROMPTS-PRUNE: wt-entry -> landing"]))
        self.commit_log_change(wt, "prune wt-entry with its receipt")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertIn("prune-audit:", proc.stdout)
        self.assertIn("PRUNE-OK: wt-entry", proc.stdout)
        self.assertEqual(proc.stdout.count("prune-audit summary:"), 1)
        self.assertNotEqual(rev(repo, "refs/heads/main"), base_tip)

    def test_land_worktree_audit_pins_verified_source_tip(self):
        # the receipt names the audited range as <merge-base>..<source-tip>,
        # the pinned upper endpoint the helper passes, never a HEAD form
        repo, wt = self.worktree_repo_with_logs("wt-pinned", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text(
                [], ["PLAN-PROMPTS-PRUNE: wt-entry -> landing"]))
        self.commit_log_change(wt, "prune wt-entry with its receipt")
        source_tip = rev(wt, "HEAD")
        merge_base = git(repo, "merge-base", "refs/heads/main",
                         "feature").stdout.strip()

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("in %s..%s" % (merge_base, source_tip), proc.stdout)

    def test_land_worktree_receiptless_removal_refused_before_ref_move(self):
        # a receipt-less removal: the audit's finding is preserved, the
        # refusal names the single direct repair, and no ref moves
        repo, wt = self.worktree_repo_with_logs("wt-refused", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_text(prompt_log_text([]))
        self.commit_log_change(wt, "prune wt-entry without any receipt")
        source_tip = rev(wt, "HEAD")
        short = git(wt, "rev-parse", "--short", "HEAD").stdout.strip()
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("prune-audit:", proc.stdout)
        self.assertIn(
            "REMOVED-WITHOUT-WITNESS: wt-entry (commit %s" % short,
            proc.stdout)
        self.assertIn("lesson 234", proc.stdout)
        self.assertIn("remedy: put the removed entry's receipt in its removal commit",
                      proc.stdout)
        self.assertNotIn("PRUNE-OK", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_changed_then_reverted_log_runs_audit_once(self):
        # a log edit later reverted: commit history still shows the touch,
        # the audit runs exactly once, and the receipted removal keeps the
        # landing green
        repo, wt = self.worktree_repo_with_logs("wt-revert", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text(
                [], ["PLAN-PROMPTS-PRUNE: wt-entry -> landing"]))
        self.commit_log_change(wt, "prune wt-entry with its receipt")
        # the revert restores the entry beside its receipt line: the
        # receipt line is durable audit evidence, and a revert that
        # bare-deletes it is the checker's flagged receipt-loss class
        # (RECEIPT-LINE-REMOVED-WITHOUT-WITNESS), refused with the named
        # remedy; this green shape keeps the receipt line instead
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text(
                [prompt_log_entry("wt-entry")],
                ["PLAN-PROMPTS-PRUNE: wt-entry -> landing"]))
        self.commit_log_change(wt, "restore wt-entry beside its receipt")
        # a code file keeps the branch tip's tree distinct from the base
        # tip's (a pure revert would be the empty-diff landing refusal)
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(proc.stdout.count("prune-audit summary:"), 1)
        self.assertIn("PRUNE-OK: wt-entry", proc.stdout)
        self.assertNotEqual(rev(repo, "refs/heads/main"), base_tip)

    def test_land_worktree_receipt_line_revert_refused_before_ref_move(self):
        # the changed-then-reverted family's negative arm: the revert
        # bare-deletes the receipt line instead of restoring the entry
        # beside it, the audit's receipt-loss class fires (the removal
        # commit carries no witness), the refusal names the single direct
        # repair, and no ref moves
        repo, wt = self.worktree_repo_with_logs(
            "wt-receipt-revert", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text(
                [], ["PLAN-PROMPTS-PRUNE: wt-entry -> landing"]))
        self.commit_log_change(wt, "prune wt-entry with its receipt")
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text([prompt_log_entry("wt-entry")], []))
        self.commit_log_change(wt, "delete the receipt line")
        short = git(wt, "rev-parse", "--short", "HEAD").stdout.strip()
        # a code file keeps the branch tip's tree distinct from the base
        # tip's (the landing must reach the prune audit, not the
        # empty-diff refusal)
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("prune-audit:", proc.stdout)
        self.assertIn("PRUNE-OK: wt-entry", proc.stdout)
        self.assertIn(
            "RECEIPT-LINE-REMOVED-WITHOUT-WITNESS: wt-entry (commit %s" % short,
            proc.stdout)
        self.assertIn(
            "remedy: put the removed entry's receipt in its removal commit",
            proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_log_rename_runs_audit_once(self):
        # a rename is a touch with rename detection disabled: the audit
        # runs over the renamed log's whole-file removal, witnessed by the
        # ad-hoc receipt class in the rename commit's message
        repo, wt = self.worktree_repo_with_logs("wt-rename", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        renamed_rel = "docs/history/backlog/PLAN-PROMPTS-renamed.md"
        git(wt, "mv", PROMPT_LOG_PLAN_REL, renamed_rel)
        git(wt, "commit", "-q",
            "-m", "rename the plan prompt log",
            "-m", "EXEC-PROMPTS-PRUNE: wt-entry -> %s" % base_tip)
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(proc.stdout.count("prune-audit summary:"), 1)
        self.assertIn("PRUNE-OK: wt-entry", proc.stdout)

    def test_land_worktree_both_logs_touched_one_audit_call(self):
        # both logs touched by one range: a single invocation audits both,
        # both PRUNE-OK lines land in the receipt
        repo, wt = self.worktree_repo_with_logs(
            "wt-both", ["plan-entry"], ["exec-entry"])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text(
                [], ["PLAN-PROMPTS-PRUNE: plan-entry -> landing"]))
        (wt / PROMPT_LOG_EXEC_REL).write_text(
            prompt_log_ledger_text(
                [], ["EXEC-PROMPTS-PRUNE: exec-entry -> landing"]))
        self.commit_log_change(wt, "prune one entry from each log")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(proc.stdout.count("prune-audit summary:"), 1)
        self.assertIn("PRUNE-OK: plan-entry", proc.stdout)
        self.assertIn("PRUNE-OK: exec-entry", proc.stdout)

    def test_land_worktree_deleted_log_anchors_surviving_sibling(self):
        # the touched log was deleted in the range: the audit anchors on
        # the surviving sibling (anchoring on the deleted path would be the
        # checker's missing-log tool error and the landing would fail)
        repo, wt = self.worktree_repo_with_logs("wt-sibling", [], ["exec-entry"])
        base_tip = rev(repo, "refs/heads/main")
        git(wt, "rm", "-q", "--", PROMPT_LOG_PLAN_REL)
        (wt / PROMPT_LOG_EXEC_REL).write_text(
            prompt_log_ledger_text(
                [], ["EXEC-PROMPTS-PRUNE: exec-entry -> landing"]))
        self.commit_log_change(wt, "delete the plan log, prune the exec entry")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(proc.stdout.count("prune-audit summary:"), 1)
        self.assertIn(
            "anchor: %s" % os.path.realpath(str(wt / PROMPT_LOG_EXEC_REL)),
            proc.stdout)
        self.assertIn("PRUNE-OK: exec-entry", proc.stdout)

    def test_land_worktree_audit_tool_error_preserves_output_and_refs(self):
        # a non-UTF-8 log blob inside the range is the checker's modeled
        # tool error: the diagnostics are preserved in the receipt, the
        # outcome is the named tool error, and no ref moves
        repo, wt = self.worktree_repo_with_logs("wt-tool-error", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_bytes(
            prompt_log_text([prompt_log_entry("wt-entry")]).encode("utf-8")
            + b"\n<!-- caf\xe9 -->\n")
        self.commit_log_change(wt, "touch the log with a non-UTF-8 byte")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("prompt-log prune audit failed (exit 3)", proc.stdout)
        self.assertIn("  OUTCOME: tool_error", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_audit_unclassified_exit_is_tool_error(self):
        # an unclassified audit exit routes through the same named
        # tool-error arm with refs unchanged (the test-only seam
        # reclassifies a passing audit exit to 42)
        repo, wt = self.worktree_repo_with_logs("wt-unclassified", ["wt-entry"], [])
        base_tip = rev(repo, "refs/heads/main")
        (wt / PROMPT_LOG_PLAN_REL).write_text(
            prompt_log_ledger_text(
                [], ["PLAN-PROMPTS-PRUNE: wt-entry -> landing"]))
        self.commit_log_change(wt, "prune wt-entry with its receipt")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             fault="prune-audit-unclassified")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("prune-audit-unclassified", proc.stdout)
        self.assertIn("prompt-log prune audit failed (exit 42)", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_help_names_prompt_log_audit(self):
        # the usage text names the audit, its scoped trigger, and the
        # direct recoveries
        proc = subprocess.run(["bash", str(HELPER), "--help"],
                              capture_output=True, text=True,
                              env=base_env(), check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for token in ("prompt-log prune audit", "prune-audit", "lesson 234",
                      "self-heal", "PLAN-PROMPTS.md", "EXEC-PROMPTS.md"):
            self.assertIn(token, proc.stdout)

    def test_land_worktree_ack_egress_passthrough(self):
        # the flag without the matching Archive-egress-ack trailer in the
        # commit message: the trailer-mismatch refusal, both refs untouched
        plan_rel = "docs/history/plans/2026-01-01-ackme.md"
        repo, wt, source_tip, completed_rel = self.archive_fixture(
            "wt-ack", plan_rel, "# Plan: ackme\n\nWork complete.\n")
        base_tip = rev(repo, "refs/heads/main")
        before = primary_state(repo)
        proc = land_worktree(repo, "feature", source_tip, "land it",
                             ack_egress=plan_rel)
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
                             ack_egress=plan_rel)
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
        repo, wt = self.worktree_repo("wt-tip-ref")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        first_tip = rev(wt, "HEAD")
        commit_file(wt, "more.txt", "more\n", "branch moved on")
        current_tip = rev(wt, "HEAD")
        before = primary_state(repo)
        proc = land_worktree(repo, "feature", first_tip, "land it")
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
        repo, wt = self.worktree_repo("wt-tip-head")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        branch_tip = rev(wt, "HEAD")
        git(wt, "checkout", "-q", "--detach", "HEAD~1")
        detached_head = rev(wt, "HEAD")
        self.assertNotEqual(detached_head, branch_tip)
        before = primary_state(repo)
        proc = land_worktree(repo, "feature", branch_tip, "land it")
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
        repo, wt = self.worktree_repo("wt-preswap")
        base_tip = rev(repo, "refs/heads/main")
        git(wt, "commit", "-q", "--allow-empty", "-m", "empty branch commit")
        source_tip = rev(wt, "HEAD")
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("tree-identical", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(primary_state(repo), before)

    def test_land_worktree_base_moved_before_cas_refused(self):
        # the fault seam's value: the base ref moved between the check-landing
        # pass and the compare-and-swap; the compare-and-swap refuses on the
        # old-value mismatch naming the verified base tip AND the value the
        # ref actually reads (the verified-base-tip evidence the retry's
        # rebase duty re-derives from), both refs stand as the peer left them
        repo, wt = self.worktree_repo("wt-base-mover")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        peer_tip = rev(repo, "%s~1" % base_tip)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             fault="base-mover")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("base-mover", proc.stdout)
        self.assertIn("compare-and-swap ref move refused", proc.stdout)
        self.assertIn(base_tip, proc.stdout)
        # the strengthened evidence: the observed current tip is named, so
        # the retry re-derives onto the moved tip without a second probe,
        # and the remedy line names the rebase duty (rebase onto the moved
        # tip, refresh the base pin, re-run the pre-lock gates, retry)
        self.assertIn("now reads", proc.stdout)
        self.assertIn(peer_tip, proc.stdout)
        self.assertIn("remedy: rebase", proc.stdout)
        self.assertIn("pre-lock gate sequence", proc.stdout)
        self.assertEqual(rev(repo, "refs/heads/main"), peer_tip)
        self.assertEqual(rev(repo, "feature"), source_tip)
        self.assertEqual(rev(repo, "HEAD"), peer_tip)
        self.assertEqual(primary_state(repo), before)
        # the refusal path releases the swap-critical-section lock
        self.assert_merge_lock_free(repo)

    def test_land_worktree_swap_critical_section_serializes_disjoint_landings(self):
        # the safety witness: two ref-only landings on disjoint path sets
        # interleave their pre-lock composition and serialize their
        # compare-and-swap moves through the exclusive swap-critical-section
        # lock, with exactly one retry cycle on the loser. The loser's
        # pre-lock phase completes while the winner's swap critical section
        # holds the lock; the loser then acquires the lock, its CAS refuses
        # on the stale old-value (the disjoint-case serialization point),
        # and its single retry after the mechanical rebase lands it.
        repo = make_repo(self.tmp / "wt-serialize")
        commit_file(repo, "main-base.txt", "main base\n", "main base work")
        base_tip = rev(repo, "refs/heads/main")
        wt_a = self.tmp / "wt-serialize-a"
        wt_b = self.tmp / "wt-serialize-b"
        git(repo, "worktree", "add", "-q", "-b", "feature-a", str(wt_a))
        git(repo, "worktree", "add", "-q", "-b", "feature-b", str(wt_b))
        commit_file(wt_a, "a-file.txt", "a work\n", "a work")
        commit_file(wt_b, "b-file.txt", "b work\n", "b work")
        source_tip_b = rev(wt_b, "HEAD")
        before = primary_state(repo)

        # the winner's swap critical section holds the lock (modeled by the
        # harness hold); the loser composes pre-lock and blocks on the
        # bounded wait
        held = acquire_merge_lock(repo)
        loser_args = ["land-worktree", "--branch", "feature-b",
                      "--expected-tip", source_tip_b,
                      "--message", "land b", "--expected-base", base_tip]
        proc, out = launch_helper(loser_args, cwd=repo, poll_secs=1,
                                  swap_wait=120)
        try:
            deadline = time.time() + 60
            composed_pre_lock = False
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                out.seek(0)
                if "check-archive:" in out.read():
                    composed_pre_lock = True
                    break
                time.sleep(0.1)
            self.assertTrue(composed_pre_lock,
                            "the loser never reached the post-composition "
                            "check-archive gate pre-lock")
            # the loser is composed and parked at the swap lock: the base
            # ref still reads the pre-landing tip
            self.assertEqual(rev(repo, "refs/heads/main"), base_tip)
            # the winner's compare-and-swap inside its held critical section
            a_tree = rev(repo, "feature-a^{tree}")
            winner_landing = commit_tree(repo, a_tree, base_tip)
            git(repo, "update-ref", "refs/heads/main", winner_landing,
                base_tip)
            env = base_env()
            env["MERGE_LOCK_DIR"] = held[0]
            env["MERGE_LOCK_TOKEN"] = held[1]
            env["MERGE_LOCK_ROOT"] = suite_lock_root()
            release = subprocess.run(
                ["bash", str(DONE_LOCK), "merge-release"],
                capture_output=True, text=True, check=False, cwd=str(repo),
                env=env)
            self.assertEqual(release.returncode, 0,
                             release.stdout + release.stderr)
        finally:
            proc.wait(timeout=180)
            out.seek(0)
            loser_text = out.read()
            out.close()

        # the loser's single CAS refusal: the stale old-value check is the
        # disjoint-case serialization point, naming the verified base tip
        # and the winner's landed tip
        self.assertEqual(proc.returncode, 1, loser_text)
        self.assertIn("OUTCOME: fail", loser_text)
        self.assertIn("compare-and-swap ref move refused", loser_text)
        self.assertIn(base_tip, loser_text)
        self.assertIn(winner_landing, loser_text)
        self.assertIn("now reads", loser_text)
        self.assertEqual(rev(repo, "refs/heads/main"), winner_landing)
        self.assertEqual(rev(repo, "feature-b"), source_tip_b)
        self.assertEqual(primary_state(repo), before)
        self.assert_merge_lock_free(repo)

        # the exactly-one retry cycle: mechanical rebase onto the moved
        # tip (the Task 3 rebase duty, modeled mechanically), pre-lock
        # gates re-run, and the landing completes under a fresh swap lock
        git(wt_b, "rebase", "-q", "refs/heads/main")
        retry_tip = rev(wt_b, "HEAD")
        retry = land_worktree(repo, "feature-b", retry_tip, "land b",
                              expected_base=winner_landing)
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assertEqual(outcome_lines(retry), ["OUTCOME: pass"])
        # the retry re-ran the pre-lock gate sequence: the wired
        # base-freshness gate's marker precedes the fresh swap-lock acquire
        # on the retry output
        self.assertIn("check-landing:", retry.stdout)
        self.assertIn("swap lock: acquiring the merge lock", retry.stdout)
        self.assertLess(retry.stdout.index("check-landing:"),
                        retry.stdout.index("swap lock: acquiring the merge lock"))
        landing = rev(repo, "refs/heads/main")
        parents = git(repo, "rev-list", "--parents", "-n", "1",
                      landing).stdout.split()
        self.assertEqual(parents, [landing, winner_landing])
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature-b^{tree}"))
        self.assert_merge_lock_free(repo)

    def test_land_worktree_diverge_origin_keeps_landing(self):
        # the diverge-origin post-landing state is informational: the landing
        # kept on the pass path, the gate's note stating the descent fact (the
        # divergence predates the landing), the base ref left at the landing
        # commit
        repo, wt = self.worktree_repo("wt-diverge")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        forged = commit_tree(repo, rev(repo, "%s^{tree}" % base_tip), base_tip)
        git(repo, "update-ref", "refs/remotes/land-squash-fault/diverged", forged)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             fault="diverge-origin")
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
        repo, wt = self.worktree_repo("wt-backward-peer")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")
        peer_tip = rev(repo, "%s~1" % base_tip)
        before = primary_state(repo)

        proc = land_worktree(repo, "feature", source_tip, "land it",
                             fault="backward-peer")
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
        # the narrowed span: the swap-critical-section acquire (the helper's
        # own bounded-wait merge lock) sits after the check-archive wiring
        # and before the parentage pre-swap invocation, so the rebase, the
        # base-freshness gate, the prune audit, the composition, the tree
        # equality, and the plans-egress gate all run pre-lock in the source
        # worktree while the lock spans the parentage verification, the
        # compare-and-swap, the post-landing gate, and the reconcile tail
        self.assertLess(section.index("check-archive"),
                        section.index("merge-wait-acquire"))
        self.assertLess(section.index("merge-wait-acquire"),
                        section.index("GATE_ARGS=(pre-swap"))
        for token in ("merge-wait-acquire", "done-lock.sh",
                      "LAND_SQUASH_SWAP_LOCK_WAIT_SECS", "merge-release"):
            self.assertIn(token, section)
        # the swap-acquire rc mapping: rc 2 (ambiguous holder) is the
        # indeterminate arm, rc 3 (done-lock.sh's usage, environment, or
        # unsupported-lock-data tool error) is a tool error of its own
        # (never the retryable held-after-wait fail), and the residual rc
        # (held past the bounded wait) is that fail
        self.assertLess(section.index('SWAP_ACQ_RC" -eq 2'),
                        section.index('SWAP_ACQ_RC" -eq 3'))
        self.assertLess(section.index('SWAP_ACQ_RC" -eq 3'),
                        section.index(
                            "swap-critical-section lock acquire failed as a "
                            "done-lock.sh tool error"))
        self.assertLess(
            section.index("swap-critical-section lock acquire failed as a "
                          "done-lock.sh tool error"),
            section.index("swap-critical-section merge lock is held after "
                          "the bounded wait"))
        self.assertIn("emit_outcome tool_error", section)
        # the primary land mode keeps whole-landing exclusivity: its
        # caller-held lock verification precedes the snapshot machinery and
        # it never acquires internally
        land_section = script.split(end_marker, 1)[1]
        self.assertNotIn("merge-wait-acquire", land_section)
        self.assertLess(land_section.index("MERGE_LOCK_DIR"),
                        land_section.index("status --porcelain"))
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
                      "check-archive", "--ack-egress", "done-lock.sh exit 3"):
            self.assertIn(token, proc.stdout)


class ReconcileTailGateTest(_LandSquashFixtureMixin, unittest.TestCase):
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
        repo, wt = self.worktree_repo("wt-tail-restore")
        base_tip = rev(repo, "refs/heads/main")
        second = self.tmp / "wt-tail-second"
        git(repo, "worktree", "add", "-q", "--detach", str(second), base_tip)
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
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
        repo, wt = self.worktree_repo("wt-tail-block")
        base_tip = rev(repo, "refs/heads/main")
        second = self.tmp / "wt-tail-second"
        git(repo, "worktree", "add", "-q", "--detach", str(second), base_tip)
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")
        (second / "landed.txt").write_text("genuine local edit\n")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip)
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
        repo, wt = self.worktree_repo("wt-tail-fault")
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip,
                             fault="reconcile-tool-failure")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn("reconcile-gate", proc.stdout)
        self.assertIn("remedy: re-run", proc.stdout)
        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, base_tip)
        receipt = self.receipt_text(repo, landing)
        self.assertIn("exit code: 2", receipt)


class LandLockOwnershipTest(_LandSquashFixtureMixin, unittest.TestCase):
    """The landing lock-mode matrix and the primary land / rolling-log write
    lock orders (plan 2026-10-25-primary-log-branch-drift-at-commit.md
    Task 2): Primary `land` verifies both lock owners before its snapshot;
    ref-only `land-worktree` holds the merge lock only."""

    def test_land_missing_done_lock_refused_before_snapshot(self):
        # Matrix row 1: a valid matching merge lock with no done lock
        # refuses specifically for the missing done lock, before the
        # snapshot; the helper creates no lock state of its own.
        repo, lock = self.locked_repo("no-done")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        before = fingerprint(repo)
        done_root = repo / ".git" / "done-locks"

        proc = land(repo, "feature", tip, "land it", lock=lock,
                    done_lock=None)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("DONE_LOCK_DIR", proc.stdout)
        self.assertIn("Primary land", proc.stdout)
        self.assertEqual(fingerprint(repo), before)
        # the helper acquired nothing: no done lock state exists after the
        # refusal (the post-call status probe)
        self.assertFalse(done_root.exists())

    def test_land_worktree_runs_merge_only_while_done_held(self):
        # Matrix row 2: ref-only land-worktree with a valid merge lock and
        # the done lock held advances only the selected ref and never
        # touches the done lock.
        repo, wt = self.worktree_repo("wt-done-held")
        done = acquire_done_lock(repo)
        base_tip = rev(repo, "refs/heads/main")
        commit_file(wt, "landed.txt", "landed by feature\n", "feature work")
        source_tip = rev(wt, "HEAD")

        proc = land_worktree(repo, "feature", source_tip, "land feature",
                             expected_base=base_tip,
                             done_lock=done)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(rev(repo, "refs/heads/main"),
                         rev(repo, "refs/heads/main"))
        landing = rev(repo, "refs/heads/main")
        self.assertNotEqual(landing, base_tip)
        self.assertEqual(rev(repo, "%s^{tree}" % landing),
                         rev(repo, "feature^{tree}"))
        # the held done lock is untouched: its record still carries the
        # fixture's token and the hold is still live
        meta = Path(done[0]) / "meta.env"
        self.assertIn("lock_token=%s" % done[1], meta.read_text())
        env = base_env()
        env["DONE_LOCK_DIR"] = done[0]
        env["DONE_LOCK_TOKEN"] = done[1]
        env["DONE_LOCK_ROOT"] = str(repo / ".git" / "done-locks")
        status = subprocess.run(
            ["bash", str(DONE_LOCK), "status"], capture_output=True,
            text=True, check=False, cwd=str(repo), env=env)
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn(done[0], status.stdout)

    def test_log_writer_holding_done_blocks_land_snapshot(self):
        # Lock order 1: a primary log writer holds the done lock after
        # staging its owned delta; primary `land` cannot snapshot or
        # restore over it. The helper refuses on the staged-delta
        # pre-refusal before its snapshot, the staged delta survives, and
        # the held done lock is untouched.
        repo, lock = self.locked_repo("writer-first")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")
        log_rel = "docs/history/backlog/PLAN-PROMPTS.md"
        log_path = repo / log_rel
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("writer entry\n")
        git(repo, "add", log_rel)
        done = acquire_done_lock(repo)
        before = fingerprint(repo)

        proc = land(repo, "feature", tip, "land it", lock=lock,
                    done_lock=done)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn(log_rel, proc.stdout)
        self.assertIn("staged", proc.stdout)
        self.assertEqual(fingerprint(repo), before)
        meta = Path(done[0]) / "meta.env"
        self.assertIn("lock_token=%s" % done[1], meta.read_text())

    def test_land_holding_done_blocks_log_writer(self):
        # Lock order 2: primary `land` holds both locks through its
        # landing; a log writer cannot acquire the done lock until
        # checkout stability, and the log bytes stay unchanged.
        repo, lock = self.locked_repo("land-first")
        done = acquire_done_lock(repo)
        log_rel = "docs/history/backlog/PLAN-PROMPTS.md"
        log_path = repo / log_rel
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_before = "entry\n"
        log_path.write_text(log_before)
        git(repo, "add", log_rel)
        git(repo, "commit", "-q", "-m", "log entry")
        tip = rev(repo, "refs/heads/main")
        git(repo, "checkout", "-q", "-b", "feature")
        commit_file(repo, "feat.txt", "feat\n", "feature work")
        git(repo, "checkout", "-q", "main")

        # the writer's done-lock acquire refuses while land's hold stands
        env = base_env()
        env["DONE_LOCK_ROOT"] = str(repo / ".git" / "done-locks")
        env["DONE_LOCK_HOLDER_PID"] = str(os.getpid())
        writer_acquire = subprocess.run(
            ["bash", str(DONE_LOCK), "acquire", "--label", "log-writer"],
            capture_output=True, text=True, check=False, cwd=str(repo),
            env=env)
        self.assertNotEqual(writer_acquire.returncode, 0,
                            writer_acquire.stdout + writer_acquire.stderr)
        self.assertEqual(log_path.read_text(), log_before)

        # with both locks held, land's landing completes and the log write
        # is still pending (the writer retries after the release)
        proc = land(repo, "feature", tip, "land it", lock=lock,
                    done_lock=done)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(outcome_lines(proc), ["OUTCOME: pass"])
        self.assertEqual(rev(repo, "%s^{tree}" % rev(repo, "refs/heads/main")),
                         rev(repo, "feature^{tree}"))


if __name__ == "__main__":
    unittest.main()
