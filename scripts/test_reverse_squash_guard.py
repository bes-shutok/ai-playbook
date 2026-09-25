#!/usr/bin/env python3
"""Selftest for scripts/reverse_squash_guard.py.

Every fixture is a scratch repository built inside a TemporaryDirectory with
its own git init, per-repo identity, and commits; every git invocation (guard
and fixture) is isolated from host state (GIT_CONFIG_GLOBAL / GIT_CONFIG_SYSTEM
pointed at /dev/null and the ambient git variable family unset).
"""

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


def run_guard(*args, stdin=None):
    return subprocess.run(
        [sys.executable, str(GUARD_PATH)] + list(args),
        input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=guard_env())


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


if __name__ == "__main__":
    unittest.main()
