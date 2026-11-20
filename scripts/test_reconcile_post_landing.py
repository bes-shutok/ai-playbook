#!/usr/bin/env python3
"""Hermetic fixture suite for scripts/reconcile_post_landing.py.

Every fixture builds its own throwaway repository under ``tempfile.mkdtemp``
with ``GIT_CONFIG_GLOBAL`` and ``GIT_CONFIG_SYSTEM`` nulled, pinned
``user.email``/``user.name`` and ``commit.gpgsign false``, and tears the whole
tree down on every path (tearDown runs on success and failure alike). The
landings are ref-level: the landing commit is built through a temporary index
with plumbing so no working tree is ever written by the landing itself, which
is exactly the shape the post-landing reconciliation implementation owns.

Two cases are driven in-process against the module
(``test_pre_restore_tip_move_blocks`` and ``test_midwindow_change_reclassifies``);
the rest invoke the script as a subprocess and assert on its rows and exit code.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import reconcile_post_landing  # noqa: E402

RECONCILE_SCRIPT = os.path.join(SCRIPTS_DIR, "reconcile_post_landing.py")

HERMETIC_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL="/dev/null",
    GIT_CONFIG_SYSTEM="/dev/null",
    GIT_CONFIG_NOSYSTEM="1",
)


class FixtureRepo:
    """A throwaway repository plus the helpers the fixtures need."""

    def __init__(self, prefix="p102-recon-"):
        self.base = os.path.realpath(tempfile.mkdtemp(prefix=prefix))
        self.root = os.path.join(self.base, "repo")
        os.makedirs(self.root)
        self._worktrees = []
        self._worktree_count = 0
        self.git("init", "-q", "-b", "main", self.root)
        self.git("config", "user.email", "fixture@example.com")
        self.git("config", "user.name", "fixture")
        self.git("config", "commit.gpgsign", "false")

    # -- plumbing ----------------------------------------------------------

    def git(self, *args, **kwargs):
        cwd = kwargs.pop("cwd", None) or self.root
        index_file = kwargs.pop("index_file", None)
        stdin = kwargs.pop("stdin", None)
        check = kwargs.pop("check", True)
        env = dict(HERMETIC_ENV)
        if index_file:
            env["GIT_INDEX_FILE"] = index_file
        proc = subprocess.run(
            ["git", "-C", cwd] + list(args),
            capture_output=True,
            text=True,
            input=stdin,
            env=env,
        )
        if check and proc.returncode != 0:
            raise AssertionError(
                "git %s failed rc=%d: %s" % (args, proc.returncode, proc.stderr)
            )
        return proc

    def write(self, rel, content):
        full = os.path.join(self.root, rel)
        parent = os.path.dirname(full)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(full, "w") as handle:
            handle.write(content)
        return full

    def read(self, rel):
        with open(os.path.join(self.root, rel)) as handle:
            return handle.read()

    def exists(self, rel):
        return os.path.lexists(os.path.join(self.root, rel))

    def commit_all(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.head()

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def rev(self, rev):
        return self.git("rev-parse", rev).stdout.strip()

    def commit_time(self, sha):
        return int(self.git("show", "-s", "--format=%ct", sha).stdout.strip())

    def backdate(self, rel, epoch):
        os.utime(os.path.join(self.root, rel), (epoch, epoch))

    def freshen(self, rel, epoch):
        os.utime(os.path.join(self.root, rel), (epoch, epoch))

    def status(self, cwd=None):
        return self.git("status", "--porcelain", cwd=cwd).stdout

    def blob_at(self, tip, rel):
        proc = self.git("rev-parse", "--verify", "--quiet", "%s:%s" % (tip, rel), check=False)
        if proc.returncode == 0:
            return proc.stdout.strip()
        return None

    def index_blob(self, rel, cwd=None):
        out = self.git("ls-files", "--stage", "--", rel, cwd=cwd).stdout
        for line in out.splitlines():
            meta, _, path = line.partition("\t")
            if path == rel:
                return meta.split()[1]
        return None

    def worktree_blob(self, rel, cwd=None):
        full = os.path.join(cwd or self.root, rel)
        if not os.path.isfile(full):
            return None
        return self.git("hash-object", "--", rel, cwd=cwd).stdout.strip()

    # -- ref-level landing through a temporary index -----------------------

    def ref_landing(self, changes):
        """Move refs/heads/main to a new commit without writing any working tree."""
        pre = self.head()
        index_file = os.path.join(self.base, "landing-temp-index")
        self.git("read-tree", pre, index_file=index_file)
        for rel, content in changes.items():
            if content is None:
                self.git("update-index", "--force-remove", rel, index_file=index_file)
            else:
                blob = self.git("hash-object", "-w", "--stdin", stdin=content).stdout.strip()
                self.git(
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    "100644,%s,%s" % (blob, rel),
                    index_file=index_file,
                )
        tree = self.git("write-tree", index_file=index_file).stdout.strip()
        post = self.git("commit-tree", tree, "-p", pre, "-m", "landing").stdout.strip()
        self.git("update-ref", "refs/heads/main", post)
        os.remove(index_file)
        return pre, post

    def newer_landing_on(self, post_tip):
        """An empty newer landing commit on top of post_tip, moved onto main."""
        newer = self.git(
            "commit-tree", post_tip + "^{tree}", "-p", post_tip, "-m", "newer landing"
        ).stdout.strip()
        self.git("update-ref", "refs/heads/main", newer)
        return newer

    def add_detached_worktree(self, name, commit):
        path = os.path.join(self.base, name)
        self.git("worktree", "add", "-q", "--detach", path, commit)
        self._worktrees.append(path)
        return path

    def add_branch_worktree(self, name, branch):
        path = os.path.join(self.base, name)
        self.git("worktree", "add", "-q", "-b", branch, path)
        self._worktrees.append(path)
        return path

    def git_dir(self, cwd):
        return self.git("rev-parse", "--absolute-git-dir", cwd=cwd).stdout.strip()

    def close(self):
        for path in self._worktrees:
            self.git("worktree", "remove", "--force", "--force", path, check=False)
        self.git("worktree", "prune", check=False)
        shutil.rmtree(self.base, ignore_errors=True)


class ReconcilePostLandingTest(unittest.TestCase):
    """The reconciliation fixture suite: given/expects per case."""

    def setUp(self):
        self.repo = FixtureRepo()
        self.fresh_epoch = 2000000000

    def tearDown(self):
        self.repo.close()

    # -- drivers -----------------------------------------------------------

    def run_script(self, pre_tip, post_tip, base="main", repo=None):
        proc = subprocess.run(
            [
                sys.executable,
                RECONCILE_SCRIPT,
                "--repo",
                repo or self.repo.root,
                "--base",
                base,
                "--pre-tip",
                pre_tip,
                "--post-tip",
                post_tip,
            ],
            capture_output=True,
            text=True,
            env=HERMETIC_ENV,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def invocation(self, pre_tip, post_tip, base="main"):
        return reconcile_post_landing.Invocation(
            base=base, pre_tip=pre_tip, post_tip=post_tip, repo=self.repo.root
        )

    def run_script_landing_tail(self, pre_tip, post_tip, base="main", repo=None):
        """The landing flow's own reconcile-gate invocation shape: the same
        landing arguments plus --landing-tail."""
        proc = subprocess.run(
            [
                sys.executable,
                RECONCILE_SCRIPT,
                "--repo",
                repo or self.repo.root,
                "--base",
                base,
                "--pre-tip",
                pre_tip,
                "--post-tip",
                post_tip,
                "--landing-tail",
            ],
            capture_output=True,
            text=True,
            env=HERMETIC_ENV,
        )
        return proc.returncode, proc.stdout, proc.stderr

    # -- 1 -----------------------------------------------------------------

    def test_stale_primary_restored_and_recorded(self):
        """Given a ref-level landing changing two paths, the primary carrying one
        stale path (mtime backdated before the pre-landing tip's commit time) and
        one path already at post-tip bytes in both byte states, expects exit 0,
        the stale path restored, a restored row and a synced row."""
        r = self.repo
        r.write("skill.md", "landed v1\n")
        r.write("other.md", "other v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "landed v2\n", "other.md": "other v2\n"})
        pre_time = r.commit_time(pre)
        r.write("skill.md", "landed v1\n")
        r.backdate("skill.md", pre_time - 100000)
        r.write("other.md", "other v2\n")
        r.git("add", "other.md")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("restored %s skill.md" % r.root, out)
        self.assertIn("synced %s other.md" % r.root, out)
        self.assertEqual(r.read("skill.md"), "landed v2\n")
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(post, "skill.md"))
        self.assertEqual(r.worktree_blob("skill.md"), r.blob_at(post, "skill.md"))
        self.assertEqual(r.status(), "")

    # -- 2 -----------------------------------------------------------------

    def test_landing_added_path_materialized(self):
        """Given a ref-level landing adding one path and an untouched primary
        checkout, expects exit 0, the file present at post-tip content, and a
        restored row."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"added.md": "brand new\n"})
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("restored %s added.md" % r.root, out)
        self.assertTrue(r.exists("added.md"))
        self.assertEqual(r.read("added.md"), "brand new\n")
        self.assertEqual(r.index_blob("added.md"), r.blob_at(post, "added.md"))
        self.assertEqual(r.status(), "")

    # -- 3 -----------------------------------------------------------------

    def test_landing_deleted_path_removed(self):
        """Given a landing deleting one path still present with pre-landing bytes
        in the primary (mtime backdated to predate the pre-landing tip's commit
        time), expects exit 0 and the path removed with the removal verb: the
        index-present staged-residue shape prints `removed` (not `restored`)
        per the landing-deleted leg's re-class."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.write("gone.md", "bye\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None})
        pre_time = r.commit_time(pre)
        r.backdate("gone.md", pre_time - 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertNotIn("restored %s gone.md" % r.root, out)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    # -- 4 -----------------------------------------------------------------

    def test_wholesale_index_signature_targeted_restore(self):
        """Given the primary's index sitting at the pre-landing tree with stale
        worktree bytes (mtimes backdated before the pre-landing tip's commit
        time), expects the wholesale recognition line and per-path restores
        ending clean."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.write("second.md", "s1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n", "second.md": "s2\n"})
        pre_time = r.commit_time(pre)
        r.git("read-tree", pre)
        r.write("skill.md", "v1\n")
        r.write("second.md", "s1\n")
        r.backdate("skill.md", pre_time - 100000)
        r.backdate("second.md", pre_time - 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("wholesale %s" % r.root, out)
        self.assertIn("restored %s skill.md" % r.root, out)
        self.assertIn("restored %s second.md" % r.root, out)
        self.assertEqual(r.read("skill.md"), "v2\n")
        self.assertEqual(r.read("second.md"), "s2\n")
        self.assertEqual(r.status(), "")

    # -- 5 -----------------------------------------------------------------

    def test_genuine_modification_blocked_not_restored(self):
        """Given a landing-changed path carrying new content matching no
        pre-landing blob, expects exit 1 with a block row and the peer bytes
        preserved byte-for-byte."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.write("skill.md", "a genuine peer edit\n")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s skill.md" % r.root, out)
        self.assertEqual(r.read("skill.md"), "a genuine peer edit\n")
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(pre, "skill.md"))

    # -- 6 -----------------------------------------------------------------

    def test_detached_ancestor_fast_forwarded(self):
        """Given a detached checkout at the pre-landing tip, expects it
        fast-forwarded to the post-landing tip."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre = r.head()
        peer = r.add_detached_worktree("peer", pre)
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.backdate("skill.md", r.commit_time(pre) - 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertEqual(r.git("rev-parse", "HEAD", cwd=peer).stdout.strip(), post)
        self.assertEqual(r.status(cwd=peer), "")
        self.assertEqual(r.worktree_blob("skill.md", cwd=peer), r.blob_at(post, "skill.md"))

    # -- 7 -----------------------------------------------------------------

    def test_dirty_detached_ff_refusal_blocked(self):
        """Given a detached ancestor checkout with a local modification on a
        landing-changed path, expects a block row and the bytes preserved."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre = r.head()
        peer = r.add_detached_worktree("peer", pre)
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        with open(os.path.join(peer, "skill.md"), "w") as handle:
            handle.write("dirty local work\n")
        status_before = r.status(cwd=peer)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s" % peer, out)
        self.assertIn("ff-refused", out)
        with open(os.path.join(peer, "skill.md")) as handle:
            self.assertEqual(handle.read(), "dirty local work\n")
        self.assertEqual(r.status(cwd=peer), status_before)

    # -- 8 -----------------------------------------------------------------

    def test_mid_merge_checkout_blocked(self):
        """Given a live checkout with MERGE_HEAD present, expects a block row and
        zero writes to that checkout."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre = r.head()
        peer = r.add_detached_worktree("peer", pre)
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        with open(os.path.join(r.git_dir(peer), "MERGE_HEAD"), "w") as handle:
            handle.write(post + "\n")
        status_before = r.status(cwd=peer)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s - mid-merge" % peer, out)
        self.assertEqual(r.status(cwd=peer), status_before)
        self.assertEqual(r.worktree_blob("skill.md", cwd=peer), r.blob_at(pre, "skill.md"))

    # -- 9 -----------------------------------------------------------------

    def test_rebase_state_blocked(self):
        """Given a live checkout with rebase-merge present in its git dir, expects
        a block row and zero writes to that checkout."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre = r.head()
        peer = r.add_detached_worktree("peer", pre)
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        os.makedirs(os.path.join(r.git_dir(peer), "rebase-merge"))
        status_before = r.status(cwd=peer)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s - mid-rebase" % peer, out)
        self.assertEqual(r.status(cwd=peer), status_before)
        self.assertEqual(r.worktree_blob("skill.md", cwd=peer), r.blob_at(pre, "skill.md"))

    # -- 10 ----------------------------------------------------------------

    def test_older_ancestor_stale_restored(self):
        """Given a checkout whose landing-changed path carries, in both byte
        states, a blob from an ancestor older than the pre-landing tip, expects a
        restored row and exit 0."""
        r = self.repo
        r.write("skill.md", "v0\n")
        r.commit_all("v0")
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        pre_time = r.commit_time(pre)
        r.write("skill.md", "v0\n")
        r.git("add", "skill.md")
        r.backdate("skill.md", pre_time - 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("restored %s skill.md" % r.root, out)
        self.assertEqual(r.read("skill.md"), "v2\n")
        self.assertEqual(r.status(), "")

    # -- 11 ----------------------------------------------------------------

    def test_half_synced_index_stale_restored(self):
        """Given the worktree at post-tip bytes and the index at an ancestor blob
        on a landing-changed path, expects a restored row, the worktree bytes
        unchanged, and exit 0."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.write("skill.md", "v2\n")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("restored %s skill.md" % r.root, out)
        self.assertEqual(r.read("skill.md"), "v2\n")
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(post, "skill.md"))
        self.assertEqual(r.status(), "")

    # -- 12 (in-process) ---------------------------------------------------

    def test_pre_restore_tip_move_blocks(self):
        """Driven in-process: given classification started against --post-tip and
        refs/heads/<base> moved before the restore phase, expects the restore
        phase to map to the newer-landing block rows and exit 1 with zero
        writes."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        pre_time = r.commit_time(pre)
        r.write("skill.md", "v1\n")
        r.backdate("skill.md", pre_time - 100000)
        inv = self.invocation(pre, post)
        plan = reconcile_post_landing.build_plan(inv)
        r.newer_landing_on(post)
        result = reconcile_post_landing.apply_plan(plan, inv)
        self.assertEqual(result.exit_code, 1)
        joined = "\n".join(result.rows)
        self.assertIn("newer-landing", joined)
        self.assertIn("block %s" % r.root, joined)
        self.assertEqual(r.read("skill.md"), "v1\n")
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(pre, "skill.md"))

    # -- 13 ----------------------------------------------------------------

    def test_delete_readd_history_restored(self):
        """Given a landing-changed path whose history deletes and re-adds it and
        a checkout carrying the pre-deletion blob in both byte states, expects a
        restored row and exit 0."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.write("r.md", "r0\n")
        r.commit_all("v0")
        r.git("rm", "-q", "r.md")
        r.git("commit", "-qm", "delete r.md")
        r.write("r.md", "r1\n")
        r.git("add", "r.md")
        r.git("commit", "-qm", "readd r.md")
        pre, post = r.ref_landing({"r.md": "r2\n"})
        pre_time = r.commit_time(pre)
        r.write("r.md", "r0\n")
        r.git("add", "r.md")
        r.backdate("r.md", pre_time - 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("restored %s r.md" % r.root, out)
        self.assertEqual(r.read("r.md"), "r2\n")
        self.assertEqual(r.status(), "")

    # -- 14 ----------------------------------------------------------------

    def test_unrelated_checkout_untouched(self):
        """Given a second worktree on an unrelated branch carrying local dirt,
        expects no rows for it and a byte-identical status after the run."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre = r.head()
        peer = r.add_branch_worktree("feature", "feature")
        with open(os.path.join(peer, "skill.md"), "w") as handle:
            handle.write("feature work\n")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.backdate("skill.md", r.commit_time(pre) - 100000)
        status_before = r.status(cwd=peer)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertNotIn(peer, out)
        self.assertEqual(r.status(cwd=peer), status_before)
        with open(os.path.join(peer, "skill.md")) as handle:
            self.assertEqual(handle.read(), "feature work\n")

    # -- 15 ----------------------------------------------------------------

    def test_base_moved_guard_blocks_without_writes(self):
        """Given refs/heads/<base> no longer equal to --post-tip, expects block
        rows naming the newer landing and zero writes anywhere."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.write("skill.md", "v1\n")
        r.newer_landing_on(post)
        status_before = r.status()
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("newer-landing", out)
        self.assertIn("block %s" % r.root, out)
        self.assertEqual(r.status(), status_before)
        self.assertEqual(r.read("skill.md"), "v1\n")
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(pre, "skill.md"))

    # -- 16 ----------------------------------------------------------------

    def test_tool_failure_maps_to_exit_2(self):
        """Given a --pre-tip value git cannot resolve in a live fixture repo,
        expects exit 2 and zero writes."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.write("skill.md", "v1\n")
        status_before = r.status()
        proc = subprocess.run(
            [
                sys.executable,
                RECONCILE_SCRIPT,
                "--repo",
                r.root,
                "--base",
                "main",
                "--pre-tip",
                "no-such-landing-tip",
                "--post-tip",
                post,
            ],
            capture_output=True,
            text=True,
            env=HERMETIC_ENV,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(r.status(), status_before)
        self.assertEqual(r.read("skill.md"), "v1\n")

    def test_abbreviated_tip_args_resolve_not_false_blocked(self):
        """Given abbreviated --pre-tip and --post-tip spellings, the tip guards
        compare resolved identities, not argument spellings: expects a normal
        verified run (no newer-landing block) with the stale path restored."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        pre_time = r.commit_time(pre)
        r.write("skill.md", "v1\n")
        r.backdate("skill.md", pre_time - 100000)
        rc, out, _ = self.run_script(pre[:10], post[:10])
        self.assertEqual(rc, 0, out)
        self.assertNotIn("newer-landing", out)
        self.assertIn("restored %s skill.md" % r.root, out)
        self.assertEqual(r.read("skill.md"), "v2\n")

    # -- 17 ----------------------------------------------------------------

    def test_index_stale_worktree_peer_edit_blocked(self):
        """Given the index left at the pre-landing blob and the worktree carrying
        the peer's unstaged edit, expects a block row and both byte states
        preserved."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.write("skill.md", "unstaged peer edit\n")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s skill.md" % r.root, out)
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(pre, "skill.md"))
        self.assertEqual(r.read("skill.md"), "unstaged peer edit\n")

    # -- 18 ----------------------------------------------------------------

    def test_worktree_stale_index_peer_staged_blocked(self):
        """Given the worktree at the pre-landing blob and the index carrying the
        peer's staged edit, expects a block row and both byte states preserved."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        r.write("skill.md", "staged peer edit\n")
        r.git("add", "skill.md")
        r.write("skill.md", "v1\n")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s skill.md" % r.root, out)
        staged_blob = r.git("hash-object", "--stdin", stdin="staged peer edit\n").stdout.strip()
        self.assertEqual(r.index_blob("skill.md"), staged_blob)
        self.assertEqual(r.read("skill.md"), "v1\n")

    # -- 19 ----------------------------------------------------------------

    def test_primary_reverted_path_with_fresh_mtime_blocked(self):
        """Given the primary checkout holding an ancestor-blob match whose file
        mtime postdates the pre-landing tip's commit time, expects a block row
        instead of an auto-restore and the bytes preserved."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        pre_time = r.commit_time(pre)
        r.write("skill.md", "v1\n")
        r.freshen("skill.md", pre_time + 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s skill.md" % r.root, out)
        self.assertIn("fresh-mtime", out)
        self.assertEqual(r.read("skill.md"), "v1\n")
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(pre, "skill.md"))

    # -- 19b (witnessed 2026-11-12 shape: the two-file staged
    # reverse-of-landing residue) ------------------------------------------

    def test_primary_staged_reverse_stage_fresh_mtime_two_files_blocked_standalone(self):
        """Given a landing changing two files while the primary holds both
        files' pre-landing bytes staged and their mtimes freshened past the
        pre-landing commit time, the standalone invocation expects fresh-mtime
        block rows and exit 1 (the sanctioned partial state the witnessed
        landing completed under)."""
        r = self.repo
        r.write("a.md", "a1\n")
        r.write("b.md", "b1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"a.md": "a2\n", "b.md": "b2\n"})
        pre_time = r.commit_time(pre)
        r.write("a.md", "a1\n")
        r.git("add", "a.md")
        r.write("b.md", "b1\n")
        r.git("add", "b.md")
        r.freshen("a.md", pre_time + 100000)
        r.freshen("b.md", pre_time + 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s a.md fresh-mtime" % r.root, out)
        self.assertIn("block %s b.md fresh-mtime" % r.root, out)
        self.assertEqual(r.read("a.md"), "a1\n")
        self.assertEqual(r.read("b.md"), "b1\n")
        self.assertEqual(r.index_blob("a.md"), r.blob_at(pre, "a.md"))
        self.assertEqual(r.index_blob("b.md"), r.blob_at(pre, "b.md"))

    def test_primary_staged_reverse_stage_fresh_mtime_restored_landing_tail(self):
        """The same fixture under the landing-tail invocation: the pure stale
        witness (index and worktree both byte-identical to pre-landing
        ancestor blobs) is restored regardless of the fresh mtime, exit 0, the
        primary holding the landing bytes unstaged - never a silent stray
        stage."""
        r = self.repo
        r.write("a.md", "a1\n")
        r.write("b.md", "b1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"a.md": "a2\n", "b.md": "b2\n"})
        pre_time = r.commit_time(pre)
        r.write("a.md", "a1\n")
        r.git("add", "a.md")
        r.write("b.md", "b1\n")
        r.git("add", "b.md")
        r.freshen("a.md", pre_time + 100000)
        r.freshen("b.md", pre_time + 100000)
        rc, out, _ = self.run_script_landing_tail(pre, post)
        self.assertEqual(rc, 0)
        self.assertIn("restored %s a.md" % r.root, out)
        self.assertIn("restored %s b.md" % r.root, out)
        self.assertNotIn("fresh-mtime", out)
        self.assertEqual(r.read("a.md"), "a2\n")
        self.assertEqual(r.read("b.md"), "b2\n")
        self.assertEqual(r.index_blob("a.md"), r.blob_at(post, "a.md"))
        self.assertEqual(r.index_blob("b.md"), r.blob_at(post, "b.md"))

    # -- 20 (in-process) ---------------------------------------------------

    def test_midwindow_change_reclassifies(self):
        """Driven in-process against the module: given classification of a stale
        path followed by a mutation of the path's bytes before the re-read,
        expects the restore to abort to a block row."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        pre_time = r.commit_time(pre)
        r.write("skill.md", "v1\n")
        r.backdate("skill.md", pre_time - 100000)
        inv = self.invocation(pre, post)
        plan = reconcile_post_landing.build_plan(inv)
        r.write("skill.md", "midwindow peer edit\n")
        result = reconcile_post_landing.apply_plan(plan, inv)
        self.assertEqual(result.exit_code, 1)
        joined = "\n".join(result.rows)
        self.assertIn("block %s skill.md" % r.root, joined)
        self.assertEqual(r.read("skill.md"), "midwindow peer edit\n")
        self.assertEqual(r.index_blob("skill.md"), r.blob_at(pre, "skill.md"))

    # -- 21 ----------------------------------------------------------------

    def test_landing_deleted_path_with_staged_peer_blocked(self):
        """Given a landing-deleted path whose worktree bytes equal the
        pre-landing blob while the index carries a staged non-ancestor blob,
        expects a block row naming the staged state, the file and the staged
        entry both preserved, and exit 1."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.write("gone.md", "bye\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None})
        r.write("gone.md", "staged deletion override\n")
        r.git("add", "gone.md")
        r.write("gone.md", "bye\n")
        r.backdate("gone.md", r.commit_time(pre) - 100000)
        status_before = r.status()
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s gone.md" % r.root, out)
        self.assertIn("staged-peer-edit", out)
        self.assertTrue(r.exists("gone.md"))
        self.assertEqual(r.read("gone.md"), "bye\n")
        staged_blob = r.git(
            "hash-object", "--stdin", stdin="staged deletion override\n"
        ).stdout.strip()
        self.assertEqual(r.index_blob("gone.md"), staged_blob)
        self.assertEqual(r.status(), status_before)

    # -- 22 ---------------------------------------------------------------

    def test_stale_row_names_containment_delta(self):
        """[class: REPOSITORY_TEST] Given the stale-checkout fixture (a checkout
        stale against a landed commit), the stale restore row carries the
        containment note naming the checkout branch's merge base with the
        landed post-tip and the landed parent; a fully-synced checkout (clean
        reconcile) carries no note, and neither does the fast-forwarded row of
        a detached checkout at the pre-landing tip (the ff moves its bytes to
        the landed tip, so its row is synced: the note is a stale-witness
        restore-only field, never noise on clean reconciles)."""
        # The stale-checkout fixture: the primary stale against the landed
        # commit on one path, synced on the other.
        r = self.repo
        r.write("skill.md", "landed v1\n")
        r.write("other.md", "other v1\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"skill.md": "landed v2\n", "other.md": "other v2\n"})
        pre_time = r.commit_time(pre)
        r.write("skill.md", "landed v1\n")
        r.backdate("skill.md", pre_time - 100000)
        r.write("other.md", "other v2\n")
        r.git("add", "other.md")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        stale_row = [
            line for line in out.splitlines()
            if line.startswith("restored %s skill.md" % r.root)
        ][0]
        self.assertIn("containment-delta", stale_row)
        self.assertIn("checkout merge base %s" % post, stale_row)
        self.assertIn("versus landed parent %s" % pre, stale_row)
        synced_row = [
            line for line in out.splitlines()
            if line.startswith("synced %s other.md" % r.root)
        ][0]
        self.assertNotIn("containment-delta", synced_row)

        # Fully-synced checkout: every row synced, no containment note.
        synced = FixtureRepo()
        self.addCleanup(synced.close)
        synced.write("skill.md", "v1\n")
        synced.commit_all("v1")
        pre_synced, post_synced = synced.ref_landing({"skill.md": "v2\n"})
        synced.write("skill.md", "v2\n")
        synced.git("add", "skill.md")
        rc, out, _ = self.run_script(pre_synced, post_synced, repo=synced.root)
        self.assertEqual(rc, 0, out)
        self.assertNotIn("containment-delta", out)

        # A detached checkout at the pre-landing tip fast-forwards: its bytes
        # reach the landed tip, so its row is synced and carries no note.
        detached = FixtureRepo()
        self.addCleanup(detached.close)
        detached.write("skill.md", "v1\n")
        detached.commit_all("v1")
        pre_detached = detached.head()
        peer = detached.add_detached_worktree("peer", pre_detached)
        pre_detached, post_detached = detached.ref_landing({"skill.md": "v2\n"})
        detached.backdate(
            "skill.md", detached.commit_time(pre_detached) - 100000
        )
        rc, out, _ = self.run_script(pre_detached, post_detached, repo=detached.root)
        self.assertEqual(rc, 0, out)
        peer_row = [
            line for line in out.splitlines()
            if line.startswith("synced %s skill.md" % peer)
        ][0]
        self.assertNotIn("containment-delta", peer_row)

    # -- deleted_reclass ---------------------------------------------------

    def deleted_fixture(self):
        """Fold-and-delete landing: one deleted path (gone.md, v1 bytes), one
        surviving path. Returns (r, pre, post)."""
        r = self.repo
        r.write("gone.md", "bye\n")
        r.write("keep.md", "k\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None})
        return r, pre, post

    def test_deleted_reclass_witnessed_shape_landing_tail(self):
        """deleted_reclass canary: the witnessed stale-restore shape (fold-and-
        delete landing, primary HEAD at post tip, index and worktree holding
        pre bytes, fresh mtime) under --landing-tail expects exit 0, a
        `removed` row, no resurrected paths, the file absent, and clean
        status."""
        r, pre, post = self.deleted_fixture()
        pre_time = r.commit_time(pre)
        r.freshen("gone.md", pre_time + 100000)
        rc, out, _ = self.run_script_landing_tail(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertNotIn("fresh-mtime", out)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_deleted_reclass_index_absent_orphan_standalone(self):
        """deleted_reclass: a landing-deleted path whose index entry is absent
        and whose worktree bytes equal the pre-landing blob (fresh mtime) is
        removed with os.remove and a `removed` row, the fresh mtime no longer
        blocking (standalone mode)."""
        r, pre, post = self.deleted_fixture()
        # The index-absent shape: drop the index entry (the ref-level landing
        # leaves the primary index holding the pre-landing blob), keep the
        # worktree file with its fresh mtime.
        r.git("update-index", "--force-remove", "gone.md")
        pre_time = r.commit_time(pre)
        r.freshen("gone.md", pre_time + 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_deleted_reclass_index_absent_orphan_landing_tail(self):
        """deleted_reclass: the index-absent orphan shape under --landing-tail
        expects the same removal with a `removed` row, exit 0."""
        r, pre, post = self.deleted_fixture()
        r.git("update-index", "--force-remove", "gone.md")
        rc, out, _ = self.run_script_landing_tail(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_deleted_reclass_staged_residue_worktree_absent_standalone(self):
        """deleted_reclass staged-residue removal: the index carries the
        pre-landing blob (staged-looking only because HEAD moved under the
        checkout) with the worktree bytes absent; expects the single-path
        restore removal with a `removed` row (not `restored`), exit 0
        (standalone)."""
        r, pre, post = self.deleted_fixture()
        r.git("add", "gone.md")
        os.remove(os.path.join(r.root, "gone.md"))
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertNotIn("restored %s gone.md" % r.root, out)
        self.assertEqual(r.index_blob("gone.md"), None)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_deleted_reclass_staged_residue_worktree_ancestor_landing_tail(self):
        """deleted_reclass staged-residue removal under --landing-tail: the
        index carries the pre-landing blob with fresh worktree bytes matching
        the pre-landing blob; expects the restore removal with a `removed`
        row, exit 0, no fresh-mtime block."""
        r, pre, post = self.deleted_fixture()
        pre_time = r.commit_time(pre)
        r.git("add", "gone.md")
        r.freshen("gone.md", pre_time + 100000)
        rc, out, _ = self.run_script_landing_tail(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertNotIn("fresh-mtime", out)
        self.assertEqual(r.index_blob("gone.md"), None)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_landing_tail_lift_is_stale_only_fresh_mtime_removed_deleted_reclass(
        self,
    ):
        """deleted_reclass (renamed from
        test_landing_tail_lift_is_stale_only_fresh_mtime_deleted_still_blocked):
        the landing-tail lift stays stale-only for the surviving-path
        witnesses, but the landing-deleted leg is now the removal class: the
        same fixture (staged ancestor index blob, fresh mtime) is removed,
        never fresh-mtime blocked, because a landing-deleted path's pure
        ancestor bytes carry no peer edit content and the landing must not
        strand its own restage residue."""
        r, pre, post = self.deleted_fixture()
        pre_time = r.commit_time(pre)
        r.git("add", "gone.md")
        r.freshen("gone.md", pre_time + 100000)
        rc, out, _ = self.run_script_landing_tail(pre, post)
        self.assertEqual(rc, 0)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertNotIn("fresh-mtime", out)
        self.assertFalse(r.exists("gone.md"))

    def test_deleted_reclass_older_ancestor_orphan_standalone(self):
        """deleted_reclass older-ancestor deletion (index-absent orphan
        variant, standalone): a landing-deleted path whose worktree bytes
        match an ancestor blob older than the pre-landing tip (not equal to
        it) expects the same removal class."""
        r = self.repo
        r.write("gone.md", "v0\n")
        r.write("keep.md", "k\n")
        r.commit_all("v0")
        r.write("gone.md", "bye\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None})
        older_blob = r.blob_at(r.rev(pre + "~"), "gone.md")
        self.assertNotEqual(older_blob, r.blob_at(pre, "gone.md"))
        r.write("gone.md", "v0\n")
        r.git("update-index", "--force-remove", "gone.md")
        pre_time = r.commit_time(pre)
        r.freshen("gone.md", pre_time + 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_deleted_reclass_older_ancestor_staged_residue_landing_tail(self):
        """deleted_reclass older-ancestor deletion (staged-residue variant,
        landing-tail): the index carries an ancestor blob older than the
        pre-landing tip with the worktree bytes absent; expects the restore
        removal with a `removed` row."""
        r = self.repo
        r.write("gone.md", "v0\n")
        r.write("keep.md", "k\n")
        r.commit_all("v0")
        r.write("gone.md", "bye\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None})
        older_blob = r.blob_at(r.rev(pre + "~"), "gone.md")
        self.assertNotEqual(older_blob, r.blob_at(pre, "gone.md"))
        r.write("gone.md", "v0\n")
        r.git("add", "gone.md")
        os.remove(os.path.join(r.root, "gone.md"))
        rc, out, _ = self.run_script_landing_tail(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertEqual(r.index_blob("gone.md"), None)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_deleted_reclass_staged_peer_edit_blocked_both_modes(self):
        """deleted_reclass block-unchanged: a landing-deleted path whose index
        carries a staged non-ancestor blob (a peer's edit) still blocks as
        staged-peer-edit in both modes, byte-unchanged."""
        for driver in (self.run_script, self.run_script_landing_tail):
            r, pre, post = self.deleted_fixture()
            r.write("gone.md", "staged deletion override\n")
            r.git("add", "gone.md")
            r.write("gone.md", "bye\n")
            rc, out, _ = driver(pre, post)
            self.assertEqual(rc, 1)
            self.assertIn("block %s gone.md" % r.root, out)
            self.assertIn("staged-peer-edit", out)
            self.assertTrue(r.exists("gone.md"))
            staged_blob = r.git(
                "hash-object", "--stdin", stdin="staged deletion override\n"
            ).stdout.strip()
            self.assertEqual(r.index_blob("gone.md"), staged_blob)

    def test_deleted_reclass_genuine_modification_blocked_both_modes(self):
        """deleted_reclass block-unchanged: a landing-deleted path whose
        worktree bytes match no ancestor blob still blocks as
        genuine-modification in both modes, byte-unchanged."""
        for driver in (self.run_script, self.run_script_landing_tail):
            r, pre, post = self.deleted_fixture()
            r.write("gone.md", "peer rewrite\n")
            rc, out, _ = driver(pre, post)
            self.assertEqual(rc, 1)
            self.assertIn("block %s gone.md genuine-modification" % r.root, out)
            self.assertEqual(r.read("gone.md"), "peer rewrite\n")

    def test_deleted_reclass_staged_index_ancestor_worktree_peer_blocked(self):
        """deleted_reclass block-unchanged: a landing-deleted path whose index
        carries an ancestor blob while the worktree bytes match no ancestor is
        a genuine modification, never a removal (the staged-residue removal
        requires absent or ancestor worktree bytes)."""
        r, pre, post = self.deleted_fixture()
        r.git("add", "gone.md")
        r.write("gone.md", "peer rewrite over staged ancestor\n")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s gone.md genuine-modification" % r.root, out)
        self.assertEqual(r.read("gone.md"), "peer rewrite over staged ancestor\n")

    def test_deleted_reclass_clean_checkout_synced_noop(self):
        """deleted_reclass synced no-op: a landing-deleted path absent from
        both index and worktree (the clean-checkout shape) expects the
        `synced` row and exit 0."""
        r, pre, post = self.deleted_fixture()
        r.git("update-index", "--force-remove", "gone.md")
        os.remove(os.path.join(r.root, "gone.md"))
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("synced %s gone.md" % r.root, out)
        self.assertEqual(r.status(), "")


if __name__ == "__main__":
    unittest.main()


class ReconciliationResidualsTest(ReconcilePostLandingTest):
    """Plan 2026-09-30-reconciliation-coupling-residuals fixtures: inherits
    the fixture repo, driver, and teardown of the main suite."""

    def tearDown(self):
        # Restore a non-writable fixture root (the unreadable-removal test)
        # before the inherited teardown removes the tree.
        saved = getattr(self, "_nonwritable_root_mode", None)
        if saved is not None:
            os.chmod(self.repo.root, saved)
            self._nonwritable_root_mode = None
        super().tearDown()

    def test_landing_deleted_untracked_orphan_removed(self):
        """[class: REPOSITORY_TEST] The machinery-elimination end state: a
        landing deletes the path, ``git rm --cached`` leaves the worktree copy
        untracked with the pre-landing bytes, and the mtime is backdated
        before the pre-tip commit time. The index-absent deleted orphan is
        removed directly (git restore cannot remove an index-absent path):
        expects exit 0, the file removed, and clean status."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.write("gone.md", "bye\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None, "added.md": "brand new\n"})
        pre_time = r.commit_time(pre)
        r.backdate("skill.md", pre_time - 100000)
        r.backdate("gone.md", pre_time - 100000)
        # The witnessed shape: gone.md leaves the index (untracked in the
        # checkout) while the worktree keeps the pre bytes, so the deleted
        # path is index-absent and the orphan is removed directly.
        r.git("rm", "--cached", "-q", "gone.md")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("removed %s gone.md" % r.root, out)
        self.assertIn("restored %s added.md" % r.root, out)
        self.assertFalse(r.exists("gone.md"))
        self.assertEqual(r.status(), "")

    def test_unreadable_removal_degrades_to_block_row(self):
        """[class: REPOSITORY_TEST] Same untracked-orphan fixture but the
        file's parent directory made non-writable (chmod 555, restored in
        tearDown; skipped as root) so the direct removal fails: expects exit
        1, the gone.md ``restore-refused`` block row, and the file still
        present. The landing-added sibling may carry its own degraded row
        (its worktree write hits the same non-writable directory); it is not
        asserted."""
        r = self.repo
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("running as root: directory write bits are not enforced")
        r.write("skill.md", "v1\n")
        r.write("gone.md", "bye\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None, "added.md": "brand new\n"})
        pre_time = r.commit_time(pre)
        r.backdate("skill.md", pre_time - 100000)
        r.backdate("gone.md", pre_time - 100000)
        r.git("rm", "--cached", "-q", "gone.md")
        self._nonwritable_root_mode = os.stat(r.root).st_mode & 0o777
        os.chmod(r.root, 0o555)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1, out)
        self.assertIn("block %s gone.md restore-refused" % r.root, out)
        self.assertTrue(r.exists("gone.md"))

    def test_mixed_reset_wholesale_residue_worktree_only_restore(self):
        """[class: REPOSITORY_TEST] The wholesale-residue signature (index at
        the post-tip blob, worktree at the ancestor blob) takes the
        worktree-only restore: the index stays at the post-tip blob."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        ancestor = r.head()
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        pre_time = r.commit_time(pre)
        r.backdate("skill.md", pre_time - 100000)
        wt = r.add_detached_worktree("mixed", ancestor)
        # Index at the post-tip blob, worktree at the ancestor blob.
        r.git("-C", wt, "reset", "--soft", post)
        r.git("-C", wt, "restore", "--source=" + ancestor, "--worktree", "--", "skill.md")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            r.index_blob("skill.md", cwd=wt), r.blob_at(post, "skill.md")
        )
        self.assertEqual(
            r.worktree_blob("skill.md", cwd=wt), r.blob_at(post, "skill.md")
        )

    def test_cherry_pick_state_witnessed_midflight(self):
        """[class: REPOSITORY_TEST] CHERRY_PICK_HEAD in the checkout's git dir
        witnesses as a midflight state and blocks the checkout."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        pre = r.head()
        peer = r.add_detached_worktree("cherry", pre)
        pre, post = r.ref_landing({"skill.md": "v2\n"})
        with open(os.path.join(r.git_dir(peer), "CHERRY_PICK_HEAD"), "w") as handle:
            handle.write(post + "\n")
        status_before = r.status(cwd=peer)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1)
        self.assertIn("block %s - mid-cherry-pick" % peer, out)
        self.assertEqual(r.status(cwd=peer), status_before)

    def test_rev_parse_verify_runs_hermetic_env(self):
        """[class: REPOSITORY_TEST] Construction witness (rev-parse output is
        not config-sensitive): rev_parse_verify builds its subprocess with
        the same hermetic environment mapping git() constructs."""
        import reconcile_post_landing as mod

        captured = {}

        class FakeProc:
            returncode = 0
            stdout = "0123456789abcdef" * 5 + "\n"
            stderr = ""

        original_run = mod.subprocess.run

        def spy(*args, **kwargs):
            captured["env"] = kwargs.get("env")
            captured["argv"] = args[0]
            return FakeProc()

        mod.subprocess.run = spy
        try:
            sha = mod.rev_parse_verify(self.repo.root, "refs/heads/main")
        finally:
            mod.subprocess.run = original_run
        self.assertEqual(sha, "0123456789abcdef" * 5)
        self.assertEqual(
            captured["env"].get("GIT_CONFIG_GLOBAL"), "/dev/null"
        )
        self.assertEqual(
            captured["env"].get("GIT_CONFIG_SYSTEM"), "/dev/null"
        )
        self.assertEqual(captured["env"].get("GIT_CONFIG_NOSYSTEM"), "1")
        self.assertIn("rev-parse", captured["argv"])


class CheckPrimarySweepTest(ReconcilePostLandingTest):
    """The read-only primary freshness sweep (--check-primary): warning-only
    stale-witness rows, no writes, exit 0/1/2."""

    def run_sweep(self, repo=None, extra=()):
        proc = subprocess.run(
            [sys.executable, RECONCILE_SCRIPT, "--check-primary", "--repo",
             repo or self.repo.root] + list(extra),
            capture_output=True,
            text=True,
            env=HERMETIC_ENV,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_silent_working_tree_variant_reported_stale(self):
        """Given a tracked path whose worktree bytes equal a pre-landing
        ancestor blob with nothing staged while HEAD advanced past it,
        expects exit 1, a stale worktree-arm row naming the path and the
        ancestor commit, and the file bytes unchanged."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        v1 = r.head()
        r.write("skill.md", "v2\n")
        r.commit_all("v2")
        r.write("skill.md", "v1\n")
        rc, out, _ = self.run_sweep()
        self.assertEqual(rc, 1)
        self.assertIn("stale skill.md %s worktree" % v1, out)
        self.assertEqual(r.read("skill.md"), "v1\n")

    def test_untracked_and_genuine_edits_exit_zero(self):
        """Given an untracked file and a genuine (non-ancestor) worktree edit,
        expects exit 0 with no stale row."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        r.write("notes.txt", "untracked\n")
        r.write("skill.md", "genuinely edited beyond every ancestor\n")
        rc, out, _ = self.run_sweep()
        self.assertEqual(rc, 0)
        self.assertNotIn("stale ", out)

    def test_mid_rebase_primary_notes_and_skips(self):
        """Given a primary mid-rebase, expects the note row and no stale
        classification."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        r.write("skill.md", "v1-ancestor-revert\n")
        os.makedirs(os.path.join(r.git_dir(r.root), "rebase-merge"))
        rc, out, _ = self.run_sweep()
        self.assertEqual(rc, 0)
        self.assertIn("note %s midflight" % r.root, out)
        self.assertNotIn("stale ", out)

    def test_fresh_mtime_witness_reported(self):
        """Given stale worktree bytes whose mtime postdates the matching
        commit's committer time, expects the fresh-mtime witness on the row,
        warning-only."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        v1 = r.head()
        r.write("skill.md", "v2\n")
        r.commit_all("v2")
        r.write("skill.md", "v1\n")
        r.freshen("skill.md", self.fresh_epoch)
        rc, out, _ = self.run_sweep()
        self.assertEqual(rc, 1)
        self.assertIn("stale skill.md %s worktree fresh-mtime" % v1, out)

    def test_staged_ancestor_variant_reports_index_arm(self):
        """Given index bytes at the parent blob while the worktree carries the
        post bytes, expects the stale row naming the index arm."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        v1 = r.head()
        r.write("skill.md", "v2\n")
        r.commit_all("v2")
        r.write("skill.md", "v1\n")
        r.git("add", "skill.md")
        r.write("skill.md", "v2\n")
        rc, out, _ = self.run_sweep()
        self.assertEqual(rc, 1)
        self.assertIn("stale skill.md %s index" % v1, out)
        self.assertNotIn(" worktree", out.replace("worktree arm", ""))

    def test_both_arms_variant_reports_worktree_row(self):
        """Given index and worktree bytes each matching ancestor blobs,
        expects the worktree arm per the pinned precedence."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        v1 = r.head()
        r.write("skill.md", "v2\n")
        r.commit_all("v2")
        r.write("skill.md", "v1\n")
        r.git("add", "skill.md")
        rc, out, _ = self.run_sweep()
        self.assertEqual(rc, 1)
        self.assertIn("stale skill.md %s worktree" % v1, out)

    def test_check_primary_mutually_exclusive_with_landing_args(self):
        """Given --check-primary combined with a landing argument, expects a
        usage error exiting 2."""
        rc, out, err = self.run_sweep(extra=["--base", "main"])
        self.assertEqual(rc, 2)
        self.assertNotIn("stale ", out)

    def test_landing_tail_check_primary_mutually_exclusive(self):
        """Given --check-primary combined with --landing-tail, expects a usage
        error exiting 2."""
        rc, out, err = self.run_sweep(extra=["--landing-tail"])
        self.assertEqual(rc, 2)
        self.assertNotIn("restored ", out)

    def test_clean_primary_exits_zero(self):
        """Given a clean primary at HEAD, expects exit 0 and no rows."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.commit_all("v1")
        rc, out, _ = self.run_sweep()
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
