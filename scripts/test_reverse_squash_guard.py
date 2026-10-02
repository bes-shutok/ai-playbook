#!/usr/bin/env python3
"""Selftest for scripts/reverse_squash_guard.py.

Every fixture is a scratch repository built inside a TemporaryDirectory with
its own git init, per-repo identity, and commits; every git invocation (guard
and fixture) is isolated from host state (GIT_CONFIG_GLOBAL / GIT_CONFIG_SYSTEM
pointed at /dev/null and the ambient git variable family unset).
"""

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = REPO_ROOT / "scripts" / "reverse_squash_guard.py"

_spec = importlib.util.spec_from_file_location("reverse_squash_guard", GUARD_PATH)
rsg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rsg)

AMBIENT_GIT_VARS = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS", "GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE",
)

SHA40 = re.compile(r"^[0-9a-f]{40}$")


def guard_env():
    env = dict(os.environ)
    for var in AMBIENT_GIT_VARS:
        env.pop(var, None)
    for key in list(env):
        if re.match(r"^GIT_CONFIG_(KEY|VALUE)_\d+$", key):
            env.pop(key, None)
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    return env


def git(root, *args):
    proc = subprocess.run(["git", "-C", str(root)] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=guard_env())
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args[0], proc.stderr.decode()))
    return proc.stdout.decode()


def run_guard(*args, stdin=None, cwd=None):
    return subprocess.run(
        [sys.executable, str(GUARD_PATH)] + list(args),
        input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=guard_env(), cwd=cwd)


def run_commit_tree(repo, tree, *parents):
    """Create a commit with an explicit tree and parents (commit-tree), the
    landed-squash builder shared by the check-commit and check-landed suites.

    A landed squash is built as tree = the staged branch's tree, parent = the
    pre-tip; a `git merge --squash` fixture would retain the peer path in the
    index and cannot produce the clobber shape."""
    args = ["commit-tree", tree]
    for parent in parents:
        args += ["-p", parent]
    env = guard_env()
    env.update({"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.test",
                "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.test"})
    proc = subprocess.run(["git", "-C", str(repo.root)] + args,
                          input=b"orphan\n", stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=env)
    if proc.returncode != 0:
        raise AssertionError("git commit-tree failed: %s" % proc.stderr.decode())
    return proc.stdout.decode().strip()


class ScratchRepo:
    def __init__(self, tmp):
        self.root = Path(tmp) / "scratch"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "test@example.test")
        git(self.root, "config", "user.name", "Test")
        self._write("base.txt", "base\n")

    def _write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def write(self, rel, text):
        self._write(rel, text)

    def commit_all(self, message):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", message)
        return git(self.root, "rev-parse", "HEAD").strip()

    def stage_all(self):
        git(self.root, "add", "-A")


class ReverseSquashGuardTest(unittest.TestCase):
    def _landed_squash_fixture(self, tmp):
        """Base commit, then a landed squash extending two code files and
        adding one completed plan plus two routed backlog archive files."""
        repo = ScratchRepo(tmp)
        repo.write("a.py", "a1\n")
        repo.write("c.py", "c1\n")
        repo.commit_all("base")
        repo.write("a.py", "a1\na2\na3\n")
        repo.write("c.py", "c1\nc2\nc3\n")
        repo.write("docs/history/plans/completed/p.md", "plan body\n")
        repo.write("docs/history/backlog/completed/b1.md", "b1\n")
        repo.write("docs/history/backlog/completed/b2.md", "b2\n")
        squash = repo.commit_all("landed squash")
        return repo, squash

    def test_staged_inverse_of_landed_squash_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, squash = self._landed_squash_fixture(tmp)
            git(repo.root, "mv", "docs/history/plans/completed/p.md", "docs/history/plans/p.md")
            git(repo.root, "rm", "-q", "docs/history/backlog/completed/b1.md",
                "docs/history/backlog/completed/b2.md")
            repo.write("a.py", "a1\n")
            repo.write("c.py", "c1\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            out = proc.stdout.decode()
            self.assertIn("docs/history/plans/completed/p.md", out)
            self.assertIn("docs/history/backlog/completed/b1.md", out)
            self.assertIn("docs/history/backlog/completed/b2.md", out)
            self.assertIn(squash, out)
            self.assertIn("refuse:", out)

    def test_staged_pure_code_inverse_with_padding_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("f1.py", "one\n")
            repo.write("f2.py", "two\n")
            repo.commit_all("base")
            repo.write("f1.py", "one\ne1\ne2\n")
            repo.write("f2.py", "two\ne3\ne4\n")
            squash = repo.commit_all("landed squash")
            repo.write("f1.py", "one\n")
            repo.write("f2.py", "two\n")
            repo.write("pad.txt", "padding edit\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            out = proc.stdout.decode()
            self.assertIn(squash, out)
            self.assertIn("refuse:", out)

    def test_normal_edit_staged_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("a.py", "a1\n")
            repo.commit_all("base")
            repo.write("a.py", "a1\na2\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            self.assertIn("ok: no reverse-squash signature", proc.stdout.decode())

    def test_empty_index_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            self.assertIn("ok: no reverse-squash signature", proc.stdout.decode())

    def test_rename_within_archive_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/completed/x.md", "x\n")
            repo.commit_all("base")
            git(repo.root, "mv", "docs/history/plans/completed/x.md",
                "docs/history/plans/completed/y.md")
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout.decode() + proc.stderr.decode())

    def test_rename_only_archive_egress_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/completed/x.md", "x\n")
            repo.commit_all("base")
            git(repo.root, "mv", "docs/history/plans/completed/x.md", "docs/history/plans/x.md")
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("docs/history/plans/completed/x.md", proc.stdout.decode())

    def test_staged_in_place_removal_in_archive_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/completed/p.md", "l1\nl2\nl3\nl4\n")
            repo.commit_all("base")
            repo.write("docs/history/plans/completed/p.md", "l1\nl4\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout.decode() + proc.stderr.decode())

    def test_staged_rename_back_of_landed_rename_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("a.py", "a1\n")
            repo.commit_all("base")
            git(repo.root, "mv", "a.py", "b.py")
            repo.write("b.py", "a1\nnew1\nnew2\n")
            repo.commit_all("rename with edit")
            git(repo.root, "mv", "b.py", "a.py")
            repo.write("a.py", "a1\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("refuse:", proc.stdout.decode())

    def test_check_diff_mode_recovers_extended_header_egress(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/completed/x.md", "x\n")
            repo.commit_all("base")
            git(repo.root, "mv", "docs/history/plans/completed/x.md", "docs/history/plans/x.md")
            git(repo.root, "add", "-A")
            diff = git(repo.root, "diff", "-M", "--cached")
            proc = run_guard("check-diff", "--against", "HEAD",
                             "--repo", str(repo.root), stdin=diff.encode())
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("docs/history/plans/completed/x.md", proc.stdout.decode())

    def test_quoted_extended_header_paths_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            archived = "docs/history/plans/completed/pl\xc3\xa4ne.md"
            repo._write(archived, "x\n")
            repo.commit_all("base")
            git(repo.root, "mv", archived, "docs/history/plans/pl\xc3\xa4ne.md")
            git(repo.root, "add", "-A")
            diff = git(repo.root, "diff", "-M", "--cached")
            self.assertIn('"', diff)  # header paths arrive C-quoted
            proc = run_guard("check-diff", "--against", "HEAD",
                             "--repo", str(repo.root), stdin=diff.encode())
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("pl\xc3\xa4ne.md", proc.stdout.decode())

    def test_check_staged_quoted_deleted_archive_path_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            archived = "docs/history/plans/completed/archiv \xc3\xa4.md"
            repo._write(archived, "x\n")
            repo.commit_all("base")
            git(repo.root, "rm", "-q", archived)
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("archiv \xc3\xa4.md", proc.stdout.decode())

    def test_binary_staged_file_uses_dash_placeholder_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            (repo.root / "blob.bin").write_bytes(bytes(range(256)))
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout.decode() + proc.stderr.decode())

    def test_check_diff_mode_clean_diff_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("a.py", "a1\n")
            repo.commit_all("base")
            repo.write("a.py", "a1\na2\n")
            diff = git(repo.root, "diff", "-M")
            proc = run_guard("check-diff", "--against", "HEAD",
                             "--repo", str(repo.root), stdin=diff.encode())
            self.assertEqual(proc.returncode, 0, proc.stdout.decode() + proc.stderr.decode())
            self.assertIn("ok: no reverse-squash signature", proc.stdout.decode())

    def test_partial_inverse_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("f1.py", "one\n")
            repo.write("f2.py", "two\n")
            repo.commit_all("base")
            repo.write("f1.py", "one\ne1\ne2\n")
            repo.write("f2.py", "two\ne3\ne4\n")
            repo.commit_all("landed squash")
            repo.write("f1.py", "one\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout.decode() + proc.stderr.decode())

    def test_check_diff_mode_refuses_diff_against_advanced_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("f.py", "one\n")
            base = repo.commit_all("base")
            git(repo.root, "branch", "stale", base)
            repo.write("f.py", "one\ne1\ne2\ne3\n")
            repo.write("g.py", "g1\ng2\n")
            target = repo.commit_all("landed squash")
            git(repo.root, "checkout", "-q", "stale")
            diff = git(repo.root, "diff", "-M", target)
            proc = run_guard("check-diff", "--against", target,
                             "--repo", str(repo.root), stdin=diff.encode())
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn(target, proc.stdout.decode())

    def test_unreachable_against_rev_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            proc = run_guard("check-diff", "--against", "no-such-revision",
                             "--repo", str(repo.root), stdin=b"garbage")
            self.assertEqual(proc.returncode, 2, proc.stdout.decode())
            self.assertIn("tool failure", proc.stderr.decode())

    def test_non_git_diff_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            proc = run_guard("check-diff", "--against", "HEAD",
                             "--repo", str(repo.root), stdin=b"this is not a diff\n")
            self.assertEqual(proc.returncode, 2, proc.stdout.decode())

    def test_plumbing_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            nonrepo = Path(tmp) / "not-a-repo"
            nonrepo.mkdir()
            proc = run_guard("check-diff", "--against", "HEAD",
                             "--repo", str(nonrepo), stdin=b"")
            self.assertEqual(proc.returncode, 2, proc.stdout.decode())

    def test_check_staged_plumbing_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            nonrepo = Path(tmp) / "not-a-repo"
            nonrepo.mkdir()
            proc = run_guard("check-staged", "--repo", str(nonrepo))
            self.assertEqual(proc.returncode, 2, proc.stdout.decode())

    def test_backlog_archive_egress_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/backlog/completed/b.md", "b\n")
            repo.commit_all("base")
            git(repo.root, "rm", "-q", "docs/history/backlog/completed/b.md")
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("docs/history/backlog/completed/b.md", proc.stdout.decode())

    def test_ack_suppresses_mirror_but_not_egress(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("f1.py", "one\n")
            repo.write("f2.py", "two\n")
            repo.commit_all("base")
            repo.write("f1.py", "one\ne1\ne2\n")
            repo.write("f2.py", "two\ne3\ne4\n")
            squash = repo.commit_all("landed squash")
            repo.write("f1.py", "one\n")
            repo.write("f2.py", "two\n")
            repo.stage_all()
            first = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(first.returncode, 1)
            acked = run_guard("check-staged", "--repo", str(repo.root), "--ack", squash)
            self.assertEqual(acked.returncode, 0, acked.stdout.decode())
            self.assertIn("ok: mirror %s acknowledged" % squash, acked.stdout.decode())
            # The same ack does not suppress an archive egress.
            with tempfile.TemporaryDirectory() as tmp2:
                repo2, _ = self._egress_with_squash(tmp2)
                refused = run_guard("check-staged", "--repo", str(repo2.root),
                                    "--ack", squash)
                self.assertEqual(refused.returncode, 1, refused.stdout.decode())

    def _egress_with_squash(self, tmp):
        repo = ScratchRepo(tmp)
        repo.write("f1.py", "one\n")
        repo.write("f2.py", "two\n")
        repo.commit_all("base")
        repo.write("f1.py", "one\ne1\ne2\n")
        repo.write("f2.py", "two\ne3\ne4\n")
        repo.write("docs/history/plans/completed/p.md", "plan\n")
        squash = repo.commit_all("landed squash")
        git(repo.root, "mv", "docs/history/plans/completed/p.md", "docs/history/plans/p.md")
        repo.write("f1.py", "one\n")
        repo.write("f2.py", "two\n")
        repo.stage_all()
        return repo, squash



class ReverseSquashGuardCheckCommitTest(unittest.TestCase):
    """check-commit: the parentless near-full-repo snapshot shape (P66 Task 2).

    ScratchRepo writes base.txt without committing it, so every fixture first
    seeds an initial commit; the committed tracked set then includes base.txt.
    """

    def _seed(self, repo):
        repo.commit_all("seed init commit")

    def _run_commit_tree(self, repo, tree, *parents):
        return run_commit_tree(repo, tree, *parents)

    def _mktree(self, repo, input_bytes):
        proc = subprocess.run(["git", "-C", str(repo.root), "mktree"],
                              input=input_bytes, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=guard_env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.decode().strip()

    def test_orphan_full_tree_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            self._seed(repo)
            for i in range(20):
                repo.write("f%02d.txt" % i, "x\n")
            repo.commit_all("twenty files")
            tracked = len(git(repo.root, "ls-files").strip().splitlines())
            tree = git(repo.root, "rev-parse", "HEAD^{tree}").strip()
            orphan = self._run_commit_tree(repo, tree)
            proc = run_guard("check-commit", "--rev", orphan, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("refuse: parentless near-full-repo squash commit detected",
                          proc.stdout.decode())
            self.assertIn("/%d paths >= 0.5)" % tracked, proc.stdout.decode())

    def test_parented_commit_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            self._seed(repo)
            repo.write("more.txt", "x\n")
            repo.commit_all("child of the seed commit")
            child = git(repo.root, "rev-parse", "HEAD").strip()
            proc = run_guard("check-commit", "--rev", child, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("ok: parented commit", proc.stdout.decode())

    def test_orphan_subtree_below_ratio_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            self._seed(repo)
            for i in range(18):
                repo.write("f%02d.txt" % i, "x\n")
            for i in range(2):
                repo.write("subdir/s%02d.txt" % i, "x\n")
            repo.commit_all("18 root plus 2 subdir")
            tracked = len(git(repo.root, "ls-files").strip().splitlines())
            tree = git(repo.root, "rev-parse", "HEAD:subdir").strip()
            orphan = self._run_commit_tree(repo, tree)
            proc = run_guard("check-commit", "--rev", orphan, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("ok: parentless commit below snapshot ratio (2/%d)" % tracked,
                          proc.stdout.decode())

    def test_missing_rev_is_tool_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            self._seed(repo)
            proc = run_guard("check-commit", "--rev", "deadbeef" * 5,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 2)

    def test_orphan_on_empty_repo_denominator_zero_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            # No seed: base.txt stays untracked, so ls-files is empty.
            self.assertEqual(git(repo.root, "ls-files").strip(), "")
            blob = subprocess.run(
                ["git", "-C", str(repo.root), "hash-object", "-w", "--stdin"],
                input=b"one\n", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=guard_env())
            self.assertEqual(blob.returncode, 0, blob.stderr)
            blob_sha = blob.stdout.decode().strip()
            one_tree = self._mktree(
                repo, ("100644 blob %s\tone.txt\n" % blob_sha).encode())
            orphan = self._run_commit_tree(repo, one_tree)
            proc = run_guard("check-commit", "--rev", orphan, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("(1/0 paths >= 0.5)", proc.stdout.decode())

    def test_orphan_empty_tree_zero_numerator_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            self._seed(repo)
            empty_tree = self._mktree(repo, b"")
            orphan = self._run_commit_tree(repo, empty_tree)
            proc = run_guard("check-commit", "--rev", orphan, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            tracked = len(git(repo.root, "ls-files").strip().splitlines())
            self.assertIn("ok: parentless commit below snapshot ratio (0/%d)" % tracked,
                          proc.stdout.decode())

    def test_orphan_at_exact_ratio_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            self._seed(repo)
            for i in range(10):
                repo.write("f%02d.txt" % i, "x\n")
            for i in range(11):
                repo.write("sub/s%02d.txt" % i, "x\n")
            repo.commit_all("eleven sub of twenty-two tracked")
            tree = git(repo.root, "rev-parse", "HEAD:sub").strip()
            orphan = self._run_commit_tree(repo, tree)
            proc = run_guard("check-commit", "--rev", orphan, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("(11/22 paths >= 0.5)", proc.stdout.decode())

    def _landing_fixture(self, tmp):
        """Default branch with a post-branch advance (t1.txt, t2.txt), plus a
        side branch cut before that advance and carrying its own work: the
        witnessed stale-base landing shape (2026-10-02 commit 3fd4be09)."""
        repo = ScratchRepo(tmp)
        repo.write("a.py", "a1\n")
        repo.commit_all("base")
        target = git(repo.root, "rev-parse", "--abbrev-ref", "HEAD").strip()
        git(repo.root, "checkout", "-qb", "side")
        repo.write("a.py", "a1\nside\n")
        repo.commit_all("side work")
        git(repo.root, "checkout", "-q", target)
        repo.write("t1.txt", "t1\n")
        repo.write("t2.txt", "t2\n")
        tip = repo.commit_all("target advance")
        git(repo.root, "checkout", "-q", "side")
        return repo, target, tip

    def test_check_landing_fresh_branch_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, target, tip = self._landing_fixture(tmp)
            git(repo.root, "rebase", "-q", target)
            proc = run_guard("check-landing", "--source-branch", "side",
                             "--target-ref", target, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout.decode())
            self.assertIn("ok:", proc.stdout.decode())
            self.assertIn("landing base fresh", proc.stdout.decode())

    def test_check_landing_stale_base_refused_with_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, target, tip = self._landing_fixture(tmp)
            proc = run_guard("check-landing", "--source-branch", "side",
                             "--target-ref", tip, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            out = proc.stdout.decode()
            self.assertIn("stale base", out)
            self.assertIn(tip, out)
            self.assertIn("t1.txt", out)
            self.assertIn("t2.txt", out)
            self.assertIn("refuse:", out)

    def test_check_landing_source_already_integrated_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, target, tip = self._landing_fixture(tmp)
            base = git(repo.root, "rev-parse", "%s^" % tip).strip()
            git(repo.root, "branch", "-f", "integrated", base)
            proc = run_guard("check-landing", "--source-branch", "integrated",
                             "--target-ref", tip, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("already an ancestor", proc.stdout.decode())

    def test_check_landing_unrelated_histories_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, target, tip = self._landing_fixture(tmp)
            git(repo.root, "checkout", "-q", "--orphan", "lonely")
            git(repo.root, "rm", "-rqf", ".")
            repo.write("lonely.txt", "lonely\n")
            repo.commit_all("lonely root")
            proc = run_guard("check-landing", "--source-branch", "lonely",
                             "--target-ref", tip, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout.decode())
            self.assertIn("stale base", proc.stdout.decode())

    def test_check_landing_unresolvable_branch_tool_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, target, tip = self._landing_fixture(tmp)
            proc = run_guard("check-landing", "--source-branch", "nope",
                             "--target-ref", tip, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 2, proc.stdout.decode())
            self.assertIn("tool failure", proc.stderr.decode())



class ReverseSquashGuardCheckLandedTest(unittest.TestCase):
    """check-landed: the post-landing foreign-deletion sweep (revert-set
    clobber plan Task 1).

    Every landed squash commit is built with the harness's run_commit_tree
    helper (tree = the staged branch's tree, parent = the pre-tip) and every
    guard invocation passes --repo <scratch root>.
    """

    def _run_commit_tree(self, repo, tree, *parents):
        return run_commit_tree(repo, tree, *parents)

    def _fresh_owned_fixture(self, tmp):
        """Landing base fresh at the squash parent: the squash's parent is
        the merge base and its diff deletes own.txt, content the branch's
        own history carried before the base (an owned fold-and-delete)."""
        repo = ScratchRepo(tmp)
        repo.write("own.txt", "own\n")
        repo.commit_all("trunk seeds own")
        base = git(repo.root, "rev-parse", "HEAD").strip()
        git(repo.root, "checkout", "-qb", "feature")
        repo.write("feature.txt", "feature\n")
        repo.commit_all("feature work")
        git(repo.root, "rm", "-q", "own.txt")
        repo.commit_all("feature folds own away")
        tree = git(repo.root, "rev-parse", "HEAD^{tree}").strip()
        landed = self._run_commit_tree(repo, tree, base)
        return repo, landed, base

    def _clobber_fixture(self, tmp, peer_rel, peer_body):
        """The witnessed stale-base clobber shape (2026-10-02 commit
        3fd4be09): source branch cut before a peer landing; the landed
        squash's parent is the peer tip (pre-tip) and its tree is the source
        branch's tree, which lacks the peer-added path."""
        repo = ScratchRepo(tmp)
        repo.write("a.py", "a1\n")
        repo.commit_all("base")
        trunk = git(repo.root, "rev-parse", "--abbrev-ref", "HEAD").strip()
        git(repo.root, "checkout", "-qb", "feature")
        repo.write("feature.txt", "feature\n")
        repo.commit_all("feature work")
        git(repo.root, "checkout", "-q", trunk)
        repo.write(peer_rel, peer_body)
        pre_tip = repo.commit_all("peer landing")
        feature_tree = git(repo.root, "rev-parse", "feature^{tree}").strip()
        landed = self._run_commit_tree(repo, feature_tree, pre_tip)
        return repo, landed, pre_tip

    def test_check_landed_fresh_base_owned_deletion_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, landed, base = self._fresh_owned_fixture(tmp)
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", base,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("ok: no foreign deletion in the landed commit",
                          proc.stdout.decode())

    def test_check_landed_stale_base_foreign_deletion_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, landed, pre_tip = self._clobber_fixture(tmp, "peer.txt", "peer\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("landed foreign deletion: peer.txt", out)
            self.assertIn(pre_tip, out)  # the commit that last touched the content
            self.assertIn("after merge base", out)
            self.assertIn("refuse: landed commit deletes foreign content", out)

    def test_check_landed_owned_fold_delete_ack_suppresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/backlog/2026-10-02-peer-origin.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "origin body\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-deleted", peer)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("acknowledged", proc.stdout.decode())
            self.assertIn(peer, proc.stdout.decode())

    def test_check_landed_ack_file_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/backlog/2026-10-02-peer-origin.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "origin body\n")
            ack_file = repo.root / "acks.txt"
            ack_file.write_text(peer + "\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-file", str(ack_file))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("acknowledged", proc.stdout.decode())

    def test_check_landed_ack_deferred_subtree_suppresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/plans/deferred/x.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "deferred body\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-deleted", peer)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("acknowledged", proc.stdout.decode())

    def test_check_landed_ack_sibling_tree_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/plans/deferred/x.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "deferred body\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-deleted", "docs/history/plans2/x.md")
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("tool failure", proc.stderr.decode())
            self.assertIn("docs/history/plans2/x.md",
                          proc.stdout.decode() + proc.stderr.decode())

    def test_check_landed_ack_outside_archive_trees_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/plans/deferred/x.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "deferred body\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-deleted", "docs/reviews/x.md")
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("tool failure", proc.stderr.decode())
            self.assertIn("docs/reviews/x.md",
                          proc.stdout.decode() + proc.stderr.decode())

    def test_check_landed_unused_ack_entry_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, landed, base = self._fresh_owned_fixture(tmp)
            unused = "docs/history/backlog/2026-10-02-not-deleted.md"
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", base,
                             "--repo", str(repo.root),
                             "--ack-deleted", unused)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("ok: no foreign deletion in the landed commit", out)
            self.assertIn("warning", out)
            self.assertIn(unused, out)

    def test_check_landed_duplicate_ack_entries_no_spurious_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/backlog/2026-10-02-peer-origin.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "origin body\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-deleted", peer, "--ack-deleted", peer)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("acknowledged", out)
            self.assertNotIn("warning", out)

    def test_check_landed_prefix_ack_suppresses_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/plans/deferred/x.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "deferred body\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-deleted", "docs/history/plans/")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("landed foreign deletion: %s" % peer, out)
            self.assertIn("warning", out)  # the prefix entry suppresses nothing

    def test_check_landed_unresolvable_rev_tool_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, landed, pre_tip = self._clobber_fixture(tmp, "peer.txt", "peer\n")
            proc = run_guard("check-landed", "--rev", "deadbeef" * 5,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("tool failure", proc.stderr.decode())

    def test_check_landed_unrelated_histories_tool_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, landed, pre_tip = self._clobber_fixture(tmp, "peer.txt", "peer\n")
            git(repo.root, "checkout", "-q", "--orphan", "lonely")
            git(repo.root, "rm", "-rqf", ".")
            repo.write("lonely.txt", "lonely\n")
            repo.commit_all("lonely root")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "lonely", "--pre-tip", pre_tip,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("tool failure", proc.stderr.decode())

    def test_check_landed_missing_ack_file_tool_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, landed, pre_tip = self._clobber_fixture(tmp, "peer.txt", "peer\n")
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-file", str(repo.root / "no-such-acks.txt"))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("tool failure", proc.stderr.decode())

    def test_check_landed_ack_file_blank_lines_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            peer = "docs/history/backlog/2026-10-02-peer-origin.md"
            repo, landed, pre_tip = self._clobber_fixture(tmp, peer, "origin body\n")
            ack_file = repo.root / "acks.txt"
            ack_file.write_text("\n%s\n\n" % peer)
            proc = run_guard("check-landed", "--rev", landed,
                             "--source-branch", "feature", "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             "--ack-file", str(ack_file))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("acknowledged", proc.stdout.decode())

    def test_check_landed_cli_accepts_wired_mode_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, landed, pre_tip = self._clobber_fixture(tmp, "peer.txt", "peer\n")
            proc = run_guard("check-landed",
                             "--rev", landed,
                             "--source-branch", "feature",
                             "--pre-tip", pre_tip,
                             "--repo", str(repo.root),
                             cwd=str(repo.root))
            self.assertNotIn("invalid choice", proc.stderr.decode())
            self.assertIn(proc.returncode, (0, 1),
                          proc.stdout + proc.stderr)

    def test_check_landing_stale_base_names_pre_base_deletion(self):
        """Preservation pin: the broad stale arm still names a path whose
        content was added at or before the merge base in its would-delete
        evidence (the addition probe is not narrowed by the refactor)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("a.py", "a1\n")
            repo.commit_all("root")
            trunk = git(repo.root, "rev-parse", "--abbrev-ref", "HEAD").strip()
            repo.write("pre.txt", "pre\n")
            repo.commit_all("trunk adds pre")
            repo.write("t1.txt", "t1\n")
            repo.commit_all("target advance")
            git(repo.root, "checkout", "-qb", "feature")
            git(repo.root, "rm", "-q", "pre.txt")
            repo.commit_all("feature drops pre")
            git(repo.root, "checkout", "-q", trunk)
            repo.write("t2.txt", "t2\n")
            repo.commit_all("target advance two")
            proc = run_guard("check-landing", "--source-branch", "feature",
                             "--target-ref", trunk, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("stale base", out)
            self.assertIn("pre.txt", out)
            self.assertIn("refuse: landing base stale", out)

    def test_check_landing_rename_away_named_under_stale_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("a.py", "a1\n")
            repo.commit_all("base")
            trunk = git(repo.root, "rev-parse", "--abbrev-ref", "HEAD").strip()
            repo.write("t1.txt", "t1\n")
            repo.commit_all("target adds t1")
            git(repo.root, "checkout", "-qb", "feature")
            git(repo.root, "mv", "t1.txt", "t1-moved.txt")
            repo.commit_all("feature renames t1 away")
            git(repo.root, "checkout", "-q", trunk)
            repo.write("t2.txt", "t2\n")
            repo.commit_all("target advance")
            proc = run_guard("check-landing", "--source-branch", "feature",
                             "--target-ref", trunk, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("stale base", out)
            self.assertIn("t1.txt", out)
            self.assertIn("refuse: landing base stale", out)


class ReverseSquashGuardReviewsHomeTest(unittest.TestCase):
    """reviews-home egress refusal class (revert-set clobber plan Task 3).

    Every guard invocation passes --repo <scratch root>. The deny set is
    REVIEWS_HOME_PREFIXES (docs/reviews/, docs/history/reviews/); the class
    is addition-side and never suppressible: A, M, R, and C records all
    count via the post-side path.
    """

    def test_check_staged_reviews_home_addition_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("a.py", "a1\n")
            base = repo.commit_all("base")
            repo.write("docs/reviews/x.md", "review body\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("reviews-home egress: docs/reviews/x.md", out)
            # Never suppressible: an --ack naming a sha suppresses mirror
            # findings only, and the reviews-home finding persists.
            acked = run_guard("check-staged", "--repo", str(repo.root),
                              "--ack", base)
            self.assertEqual(acked.returncode, 1, acked.stdout + acked.stderr)
            self.assertIn("reviews-home egress: docs/reviews/x.md",
                          acked.stdout.decode())

    def test_check_staged_reviews_home_rename_into_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/a.md", "a\n")
            repo.commit_all("base")
            (repo.root / "docs" / "reviews").mkdir()
            git(repo.root, "mv", "docs/a.md", "docs/reviews/y.md")
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("reviews-home egress: docs/reviews/y.md",
                          proc.stdout.decode())

    def test_check_diff_reviews_home_addition_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            repo.write("docs/reviews/x.md", "review body\n")
            git(repo.root, "add", "-A")
            diff = git(repo.root, "diff", "--cached")
            proc = run_guard("check-diff", "--against", "HEAD",
                             "--repo", str(repo.root), stdin=diff.encode())
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("reviews-home egress: docs/reviews/x.md",
                          proc.stdout.decode())

    def test_check_landing_reviews_home_addition_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("a.py", "a1\n")
            repo.commit_all("base")
            trunk = git(repo.root, "rev-parse", "--abbrev-ref", "HEAD").strip()
            git(repo.root, "checkout", "-qb", "feature")
            repo.write("docs/history/reviews/r.md", "review\n")
            repo.commit_all("feature adds a review record")
            # Fresh-base landing (trunk is an ancestor of feature): the
            # egress refusal must fire with its dedicated refuse line,
            # distinct from the stale-base refusal.
            proc = run_guard("check-landing", "--source-branch", "feature",
                             "--target-ref", trunk, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("reviews-home egress: docs/history/reviews/r.md", out)
            self.assertIn("refuse: reviews-home egress in the landing", out)
            self.assertNotIn("refuse: landing base stale", out)
            self.assertNotIn("landing base fresh", out)

    def test_check_landing_reviews_home_rename_into_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/a.md", "a\n")
            repo.commit_all("base")
            trunk = git(repo.root, "rev-parse", "--abbrev-ref", "HEAD").strip()
            git(repo.root, "checkout", "-qb", "feature")
            (repo.root / "docs" / "reviews").mkdir()
            git(repo.root, "mv", "docs/a.md", "docs/reviews/y.md")
            repo.commit_all("feature renames a record into the reviews home")
            # Proves the landing scan is not limited to A/M records: an R
            # record whose post-side path falls under the deny set refuses.
            proc = run_guard("check-landing", "--source-branch", "feature",
                             "--target-ref", trunk, "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("reviews-home egress: docs/reviews/y.md", out)
            self.assertIn("refuse: reviews-home egress in the landing", out)

    def test_check_staged_reviews_home_modification_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/reviews/x.md", "v1\n")
            repo.commit_all("base")
            repo.write("docs/reviews/x.md", "v1\nv2\n")
            repo.stage_all()
            # Proves M records are not skipped: a modified tracked record
            # under the home is the same witnessed harm.
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("reviews-home egress: docs/reviews/x.md",
                          proc.stdout.decode())

    def test_check_staged_reviews_home_deletion_clean(self):
        # No deletion arm: a staged deletion (the repair action that
        # untracks a force-added record) is never a reviews-home finding.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/reviews/x.md", "v1\n")
            repo.commit_all("base")
            git(repo.root, "rm", "-q", "docs/reviews/x.md")
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertNotIn("reviews-home egress", out)
            self.assertIn("ok: no reverse-squash signature", out)

    def test_check_diff_reviews_home_deletion_clean(self):
        # The check-diff arm shares the no-deletion-arm contract: a piped
        # deletion diff under the home is clean.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/reviews/x.md", "v1\n")
            repo.commit_all("base")
            git(repo.root, "rm", "-q", "docs/reviews/x.md")
            diff = git(repo.root, "diff", "-M", "--cached")
            proc = run_guard("check-diff", "--against", "HEAD",
                             "--repo", str(repo.root), stdin=diff.encode())
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertNotIn("reviews-home egress", out)
            self.assertIn("ok: no reverse-squash signature", out)

    def test_check_staged_non_reviews_paths_clean(self):
        # Control, expected green at RED: neither docs/tmp/ nor
        # docs/history/plans/ is under the deny set.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.commit_all("base")
            repo.write("docs/tmp/notes.md", "notes\n")
            repo.write("docs/history/plans/p.md", "plan\n")
            repo.stage_all()
            proc = run_guard("check-staged", "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("ok: no reverse-squash signature", proc.stdout.decode())


class ReverseSquashGuardCheckArchiveTest(unittest.TestCase):
    """check-archive: the plans-egress archive-ceremony family (plan
    2026-10-03-archive-ceremony-gate-universal Task 1).

    An egress is a rename or deletion moving a plan file from a plans root
    (docs/history/plans/, docs/history/backlog/, excluding their
    completed/, deferred/, and rejected/ subdirectories) into an archive
    state directory (completed/ or deferred/ of either root) or deleting
    it from a plans root. It passes only with execution evidence: zero
    unchecked `- [ ]` boxes in the egress bytes AND a digest-bound
    exec-review record under a reviews home at check time. A rejected/
    destination is the sanctioned non-execution exit.
    """

    UNCHECKED_PLAN = "# plan x\n- [ ] first thing\n- [ ] second thing\n"
    CHECKED_PLAN = "# plan, fully executed\n- [x] first thing\n- [x] second thing\n"

    def _ensure_dir(self, repo, rel):
        """Pre-create a destination directory (git mv requires it to exist;
        an empty directory stays untracked)."""
        (repo.root / rel).mkdir(parents=True, exist_ok=True)

    def _archived_repo(self, tmp, plan_body):
        """Base commit carrying docs/history/plans/2026-10-03-x.md, then the
        archive commit renaming it into docs/history/plans/completed/.
        Returns (repo, archive_sha, plan_bytes)."""
        repo = ScratchRepo(tmp)
        repo.write("docs/history/plans/2026-10-03-x.md", plan_body)
        repo.commit_all("base")
        self._ensure_dir(repo, "docs/history/plans/completed")
        git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
            "docs/history/plans/completed/2026-10-03-x.md")
        sha = repo.commit_all("plans: archive the plan")
        return repo, sha, plan_body.encode()

    def _write_record(self, repo, home, filename, body):
        """An untracked exec-review record under a reviews home (the homes
        are per-checkout state; the guard reads them at check time)."""
        record = repo.root / home / filename
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(body)
        return record

    def test_check_archive_refuses_unchecked_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha, _blob = self._archived_repo(tmp, self.UNCHECKED_PLAN)
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("docs/history/plans/2026-10-03-x.md", out)
            self.assertIn("2 unchecked", out)
            self.assertIn("sanctioned exits", out)
            self.assertIn("refuse:", out)

    def test_check_archive_refuses_missing_or_forged_record(self):
        digest = hashlib.sha256(self.CHECKED_PLAN.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha, _blob = self._archived_repo(tmp, self.CHECKED_PLAN)
            # No record at all: the missing evidence leg is named.
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("missing evidence leg", proc.stdout.decode())
            # A filename match without the plan bytes' sha256 refuses: the
            # name-only leg is forgeable and must not pass.
            record = self._write_record(
                repo, "docs/reviews", "2026-10-03-plan-review-x-exec-r1.md",
                "exec review r1 for plan x; no digest quoted here\n")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("missing evidence leg", proc.stdout.decode())
            # A mismatching digest refuses identically.
            record.write_text("exec review r1\nsha256 %s\n" % ("f" * 64))
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            # A record carrying the matching digest passes the leg (both
            # legs hold: exit 0).
            record.write_text("exec review r1\nplan bytes sha256: %s\n" % digest)
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_check_archive_passes_with_evidence(self):
        digest = hashlib.sha256(self.CHECKED_PLAN.encode()).hexdigest()
        record_body = "exec review r1\nplan bytes sha256: %s\n" % digest
        # A digest-matching record in docs/reviews/ passes.
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha, _blob = self._archived_repo(tmp, self.CHECKED_PLAN)
            self._write_record(repo, "docs/reviews",
                               "2026-10-03-plan-review-x-exec-r1.md", record_body)
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # A record in docs/history/reviews/ passes identically.
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha, _blob = self._archived_repo(tmp, self.CHECKED_PLAN)
            self._write_record(repo, "docs/history/reviews",
                               "2026-10-03-plan-review-x-exec-r2.md", record_body)
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # A record for a DIFFERENT slug refuses (hyphen-bounded
        # containment: plan slug x does not match bar-x's record).
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha, _blob = self._archived_repo(tmp, self.CHECKED_PLAN)
            self._write_record(repo, "docs/reviews",
                               "2026-10-03-plan-review-bar-x-exec-r1.md",
                               record_body)
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("missing evidence leg", proc.stdout.decode())

    def test_check_archive_rejected_path_deletions_and_deferred(self):
        # A rename into rejected/ passes without evidence (the sanctioned
        # non-execution exit).
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/rejected")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/rejected/2026-10-03-x.md")
            sha = repo.commit_all("reject the plan")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # A bare deletion of an unchecked plan from a plans root refuses
        # like the rename.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            git(repo.root, "rm", "-q", "docs/history/plans/2026-10-03-x.md")
            sha = repo.commit_all("delete the plan")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("docs/history/plans/2026-10-03-x.md", out)
            self.assertIn("refuse:", out)
        # A deletion of an evidenced plan passes (the evidence legs read
        # the parent-side bytes).
        digest = hashlib.sha256(self.CHECKED_PLAN.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.CHECKED_PLAN)
            repo.commit_all("base")
            git(repo.root, "rm", "-q", "docs/history/plans/2026-10-03-x.md")
            sha = repo.commit_all("delete the evidenced plan")
            self._write_record(repo, "docs/reviews",
                               "2026-10-03-plan-review-x-exec-r1.md",
                               "exec review r1\nplan bytes sha256: %s\n" % digest)
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # A rename into deferred/ of an unevidenced plan refuses (deferred
        # is an archive state, r1 finding 7).
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/deferred")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/deferred/2026-10-03-x.md")
            sha = repo.commit_all("defer the plan")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("refuse:", proc.stdout.decode())
        # A rename between two paths in the same plans root exits 0
        # (root-internal moves are not egress).
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/2026-10-03-x-renamed.md")
            sha = repo.commit_all("rename inside the plans root")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_check_archive_staged_arm_and_ack(self):
        # --staged refuses identically to the committed shape.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/completed")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/completed/2026-10-03-x.md")
            proc = run_guard("check-archive", "--staged",
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("docs/history/plans/2026-10-03-x.md", out)
            self.assertIn("refuse:", out)
        # An ack suppresses exactly its own path's refusal; another
        # offending path in the same change still refuses.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-a.md", self.UNCHECKED_PLAN)
            repo.write("docs/history/plans/2026-10-03-b.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/completed")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-a.md",
                "docs/history/plans/completed/2026-10-03-a.md")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-b.md",
                "docs/history/plans/completed/2026-10-03-b.md")
            proc = run_guard("check-archive", "--staged",
                             "--repo", str(repo.root),
                             "--ack-egress", "docs/history/plans/2026-10-03-a.md")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("acknowledged", out)
            # A staged-arm ack is warning-level only: it cannot be
            # trailer-verified pre-commit.
            self.assertIn("cannot be trailer-verified", out)
            self.assertIn("2026-10-03-b.md", out)
            self.assertNotIn("plan-egress: docs/history/plans/2026-10-03-a.md", out)
            self.assertIn("refuse:", out)
        # An ack whose path is not a detected egress is an unused-ack
        # refusal.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("f.py", "f1\n")
            repo.commit_all("base")
            repo.write("f.py", "f1\nf2\n")
            repo.stage_all()
            proc = run_guard("check-archive", "--staged",
                             "--repo", str(repo.root),
                             "--ack-egress", "docs/history/plans/2026-10-03-none.md")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("warning", out)
            self.assertIn("unused", out)
            self.assertIn("refuse:", out)
        # More than one ack in one invocation is a refusal.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/completed")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/completed/2026-10-03-x.md")
            proc = run_guard("check-archive", "--staged",
                             "--repo", str(repo.root),
                             "--ack-egress", "docs/history/plans/2026-10-03-x.md",
                             "--ack-egress", "docs/history/plans/2026-10-03-x.md")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("one --ack-egress", proc.stdout.decode())

    def test_check_archive_backlog_root(self):
        # An unchecked backlog-root egress refuses via the unchecked-boxes
        # leg (the exec-review record leg is scoped to plans-root files).
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/backlog/2026-10-02-b.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/backlog/completed")
            git(repo.root, "mv", "docs/history/backlog/2026-10-02-b.md",
                "docs/history/backlog/completed/2026-10-02-b.md")
            sha = repo.commit_all("archive the backlog plan")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("docs/history/backlog/2026-10-02-b.md", out)
            self.assertIn("unchecked", out)
            self.assertIn("refuse:", out)
            self.assertNotIn("exec-review record", out)

    def test_check_archive_backlog_root_checked_passes_without_record(self):
        # A checked backlog-root egress passes with NO exec-review record:
        # the record leg does not apply to backlog roots (the sanctioned
        # ticket is the sweep's own gate receipt context).
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/backlog/2026-10-02-b.md", self.CHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/backlog/completed")
            git(repo.root, "mv", "docs/history/backlog/2026-10-02-b.md",
                "docs/history/backlog/completed/2026-10-02-b.md")
            sha = repo.commit_all("archive the checked backlog plan")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("ok: no unevidenced plan egress",
                          proc.stdout.decode())

    def test_check_archive_backlog_root_deferred_refuses(self):
        # The fourth refuse cell: backlog-root to backlog/deferred/ refuses
        # via the unchecked-boxes leg (deferred is an archive state of the
        # backlog root too).
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/backlog/2026-10-02-b.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/backlog/deferred")
            git(repo.root, "mv", "docs/history/backlog/2026-10-02-b.md",
                "docs/history/backlog/deferred/2026-10-02-b.md")
            sha = repo.commit_all("defer the backlog plan")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("docs/history/backlog/2026-10-02-b.md", out)
            self.assertIn("unchecked", out)
            self.assertIn("refuse:", out)

    def test_check_archive_ack_trailer_verification(self):
        # --rev: an ack verified by the matching Archive-egress-ack:
        # trailer in the commit message passes.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/completed")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/completed/2026-10-03-x.md")
            sha = repo.commit_all(
                "plans: archive the plan\n\n"
                "Archive-egress-ack: docs/history/plans/2026-10-03-x.md\n")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root),
                             "--ack-egress", "docs/history/plans/2026-10-03-x.md")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("acknowledged", proc.stdout.decode())
        # --rev: an ack whose commit message lacks the trailer refuses.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/completed")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/completed/2026-10-03-x.md")
            sha = repo.commit_all("plans: archive the plan")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root),
                             "--ack-egress", "docs/history/plans/2026-10-03-x.md")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("not verified by a matching Archive-egress-ack:", out)
            self.assertIn("refuse:", out)
        # --rev: a trailer naming a DIFFERENT path does not verify the ack.
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/history/plans/completed")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/history/plans/completed/2026-10-03-x.md")
            sha = repo.commit_all(
                "plans: archive the plan\n\n"
                "Archive-egress-ack: docs/history/plans/2026-10-03-other.md\n")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root),
                             "--ack-egress", "docs/history/plans/2026-10-03-x.md")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("not verified by a matching Archive-egress-ack:",
                          proc.stdout.decode())

    def test_check_archive_sideways_rename(self):
        # A plans-root rename whose destination leaves the plans root
        # entirely (docs/tmp/) is egress and refuses without evidence (the
        # sideways egress arm).
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.UNCHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/tmp")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/tmp/2026-10-03-x.md")
            sha = repo.commit_all("move the plan aside")
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            out = proc.stdout.decode()
            self.assertIn("plan-egress: docs/history/plans/2026-10-03-x.md"
                          " -> docs/tmp/2026-10-03-x.md", out)
            self.assertIn("refuse:", out)
            self.assertIn("sanctioned exits", out)
        # The evidenced sideways rename passes (both legs hold).
        digest = hashlib.sha256(self.CHECKED_PLAN.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            repo = ScratchRepo(tmp)
            repo.write("docs/history/plans/2026-10-03-x.md", self.CHECKED_PLAN)
            repo.commit_all("base")
            self._ensure_dir(repo, "docs/tmp")
            git(repo.root, "mv", "docs/history/plans/2026-10-03-x.md",
                "docs/tmp/2026-10-03-x.md")
            sha = repo.commit_all("move the evidenced plan aside")
            self._write_record(repo, "docs/reviews",
                               "2026-10-03-plan-review-x-exec-r1.md",
                               "exec review r1\nplan bytes sha256: %s\n" % digest)
            proc = run_guard("check-archive", "--rev", sha,
                             "--repo", str(repo.root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class SingleCommitSweepTest(unittest.TestCase):
    """check-single-commit: the landing-residue sweep (single-commit-per-
    lane-event plan Task 4)."""

    def _repo_with_history(self):
        """base -> authoring landing -> flip -> prune -> next landing -> tail.
        Returns (repo, dict of shas)."""
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        counter = [0]

        def step(message):
            counter[0] += 1
            repo.write("step%d.txt" % counter[0], "step %d\n" % counter[0])
            return repo.commit_all(message)

        base = step("base")
        landing = step("plans: land probe-plan (the landing)")
        flip = step("done: mark probe-plan origin covered by the landed probe-plan plan")
        prune = step("plans: prune probe-plan entry (landed)")
        next_landing = step("done: execute probe-plan (execution lane event)")
        tail = step("wip: unrelated work")
        return repo, {"base": base, "landing": landing, "flip": flip,
                      "prune": prune, "next_landing": next_landing,
                      "tail": tail}

    def test_authoring_anchor_flags_flip_and_prune(self):
        repo, shas = self._repo_with_history()
        proc = run_guard("check-single-commit", "--rev", shas["landing"],
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout.decode())
        out = proc.stdout.decode()
        self.assertIn("[flip]", out)
        self.assertIn("[prune]", out)
        self.assertIn(shas["flip"][:12], out)
        self.assertIn(shas["prune"][:12], out)
        self.assertIn("findings=2", out)
        self.assertIn("window_scanned=", out)
        self.assertIn("window=[", out)

    def test_window_closes_at_next_landing_claim(self):
        repo, shas = self._repo_with_history()
        proc = run_guard("check-single-commit", "--rev", shas["landing"],
                         "--repo", str(repo.root))
        out = proc.stdout.decode()
        self.assertNotIn("finding " + shas["next_landing"][:12], out)
        self.assertNotIn("finding " + shas["tail"][:12], out)
        self.assertIn("closed-early", out)

    def test_clean_window_exits_zero(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        repo.commit_all("base")
        repo.write("l.txt", "l\n")
        landing = repo.commit_all("plans: land clean-plan (r1 ready)")
        repo.write("rider.txt", "rider\n")
        repo.commit_all("docs: unrelated rider on the branch")
        proc = run_guard("check-single-commit", "--rev", landing,
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 0, proc.stdout.decode())
        self.assertIn("ok: no unacknowledged follow-up residue",
                      proc.stdout.decode())

    def test_done_execute_subject_never_flags(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        repo.commit_all("base")
        repo.write("l.txt", "l\n")
        landing = repo.commit_all("plans: land some-plan")
        repo.write("x.txt", "x\n")
        repo.commit_all("done: execute some-plan")
        proc = run_guard("check-single-commit", "--rev", landing,
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 0, proc.stdout.decode())

    def test_execution_anchor_flags_slug_linked_closeouts_only(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        repo.commit_all("base")
        repo.write("l.txt", "l\n")
        landing = repo.commit_all("done: execute exec-plan-thing")
        repo.write("a.txt", "a\n")
        hit = repo.commit_all("done: archive exec-plan-thing to completed")
        repo.write("b.txt", "b\n")
        miss = repo.commit_all("done: archive other-plan-thing to completed")
        repo.write("c.txt", "c\n")
        fold = repo.commit_all("done: fold exec-plan-thing origin")
        proc = run_guard("check-single-commit", "--rev", landing,
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout.decode())
        out = proc.stdout.decode()
        self.assertIn("[archive]", out)
        self.assertIn("[fold]", out)
        self.assertIn(hit[:12], out)
        self.assertIn(fold[:12], out)
        self.assertNotIn(miss[:12], out)

    def test_authoring_anchor_ignores_closeout_classes(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        repo.commit_all("base")
        repo.write("l.txt", "l\n")
        landing = repo.commit_all("plans: land auth-plan")
        repo.write("a.txt", "a\n")
        repo.commit_all("done: archive auth-plan")
        proc = run_guard("check-single-commit", "--rev", landing,
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 0, proc.stdout.decode())

    def test_prev_landing_of_resolves_nearest_claim_below_tip(self):
        repo, shas = self._repo_with_history()
        # tip is itself a landing claim (done: execute); the window below it
        # carries the flip and prune follow-ups, so exit 1 is the verdict.
        proc = run_guard("check-single-commit",
                         "--prev-landing-of", shas["next_landing"],
                         "--until", shas["next_landing"],
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout.decode())
        out = proc.stdout.decode()
        # strictly below: the tip itself is never the resolved anchor
        self.assertIn("window=[" + shas["landing"][:12], out)
        self.assertIn("closed-early", out)

    def test_prev_landing_of_excludes_tip_itself(self):
        repo, shas = self._repo_with_history()
        # next_landing is a landing claim; the resolved anchor must be the
        # authoring landing strictly below it, never the tip itself.
        proc = run_guard("check-single-commit",
                         "--prev-landing-of", shas["next_landing"],
                         "--until", shas["tail"],
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout.decode())
        out = proc.stdout.decode()
        self.assertIn(shas["flip"][:12], out)
        self.assertIn(shas["prune"][:12], out)
        self.assertNotIn("finding " + shas["next_landing"][:12], out)

    def test_ack_file_flips_finding_to_acknowledged(self):
        repo, shas = self._repo_with_history()
        ack = Path(tempfile.mkdtemp()) / "acks.txt"
        ack.write_text(shas["flip"] + "\n\n")
        proc = run_guard("check-single-commit", "--rev", shas["landing"],
                         "--ack-file", str(ack), "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout.decode())
        out = proc.stdout.decode()
        self.assertIn("acknowledged " + shas["flip"][:12], out)
        self.assertIn("findings=1", out)
        self.assertIn("acknowledged=1", out)
        # a fully-acked window exits 0
        ack2 = Path(tempfile.mkdtemp()) / "acks.txt"
        ack2.write_text(shas["flip"] + "\n" + shas["prune"] + "\n")
        proc = run_guard("check-single-commit", "--rev", shas["landing"],
                         "--ack-file", str(ack2), "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 0, proc.stdout.decode())
        self.assertIn("acknowledged=2", proc.stdout.decode())

    def test_max_window_caps_scan(self):
        repo, shas = self._repo_with_history()
        proc = run_guard("check-single-commit", "--rev", shas["landing"],
                         "--max-window", "1", "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout.decode())
        self.assertIn("window_scanned=1", proc.stdout.decode())

    def test_non_landing_anchor_is_tool_failure(self):
        repo, shas = self._repo_with_history()
        proc = run_guard("check-single-commit", "--rev", shas["base"],
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 2, proc.stdout.decode())
        self.assertIn("not a landing-claiming commit", proc.stdout.decode())

    def test_missing_rev_and_prev_is_tool_failure(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        proc = run_guard("check-single-commit", "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 2, proc.stdout.decode())

    def test_unresolvable_prev_tip_is_tool_failure(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        repo.commit_all("base")
        proc = run_guard("check-single-commit", "--prev-landing-of", "deadbeef",
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 2, proc.stdout.decode())

    def test_no_prev_landing_claim_is_tool_failure(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        repo.commit_all("base")
        repo.write("t.txt", "t\n")
        tip = repo.commit_all("wip: no landings at all")
        proc = run_guard("check-single-commit", "--prev-landing-of", tip,
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 2, proc.stdout.decode())

    def test_batch_mode_flags_witnessed_anchor(self):
        repo, shas = self._repo_with_history()
        proc = run_guard("check-single-commit", "--scan-window", "5",
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 1, proc.stdout.decode())
        out = proc.stdout.decode()
        self.assertIn(shas["flip"][:12], out)
        self.assertIn(shas["prune"][:12], out)
        self.assertIn("anchor " + shas["landing"][:12], out)

    def test_batch_mode_clean_exits_zero(self):
        tmp = tempfile.mkdtemp()
        repo = ScratchRepo(tmp)
        repo.commit_all("base")
        repo.write("t.txt", "t\n")
        repo.commit_all("plans: land tidy-plan")
        proc = run_guard("check-single-commit", "--scan-window", "5",
                         "--repo", str(repo.root))
        self.assertEqual(proc.returncode, 0, proc.stdout.decode())

    def test_linkage_metadata_present_on_findings(self):
        repo, shas = self._repo_with_history()
        proc = run_guard("check-single-commit", "--rev", shas["landing"],
                         "--repo", str(repo.root))
        out = proc.stdout.decode()
        self.assertIn("linkage:", out)
        self.assertIn("slug:probe-plan", out)

    def test_usage_documents_exit_vocabulary_and_ack_grammar_split(self):
        proc = run_guard("check-single-commit", "--help")
        out = proc.stdout.decode()
        self.assertIn("0 clean or every finding acknowledged", out)
        self.assertIn("one commit", out)
        self.assertIn("NOT check-landed", out)


if __name__ == "__main__":
    unittest.main()
