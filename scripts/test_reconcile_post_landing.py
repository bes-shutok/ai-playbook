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
        time), expects exit 0 and the path removed."""
        r = self.repo
        r.write("skill.md", "v1\n")
        r.write("gone.md", "bye\n")
        r.commit_all("v1")
        pre, post = r.ref_landing({"gone.md": None})
        pre_time = r.commit_time(pre)
        r.backdate("gone.md", pre_time - 100000)
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 0, out)
        self.assertIn("restored %s gone.md" % r.root, out)
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


if __name__ == "__main__":
    unittest.main()


class ReconciliationResidualsTest(ReconcilePostLandingTest):
    """Plan 2026-09-30-reconciliation-coupling-residuals fixtures: inherits
    the fixture repo, driver, and teardown of the main suite."""

    def test_single_path_restore_refusal_degrades_to_block_row(self):
        """[class: REPOSITORY_TEST] Untracked debris at a landing-ADDED path
        refuses the single-path restore (git restore refuses to overwrite an
        untracked file); the run degrades to a
        ``block <checkout> <path> restore-refused`` row (exit 1) and still
        restores the landing's other paths."""
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
        # path classifies as a restore and the restore itself refuses.
        r.git("rm", "--cached", "-q", "gone.md")
        rc, out, _ = self.run_script(pre, post)
        self.assertEqual(rc, 1, out)
        self.assertIn(
            "block %s gone.md restore-refused" % r.root, out
        )
        self.assertIn("restored %s added.md" % r.root, out)
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
