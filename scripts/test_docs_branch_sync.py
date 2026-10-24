#!/usr/bin/env python3
"""Focused fixtures for the canonical docs-branch sync runner."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
import sys
import types
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


REPO_TOP = Path(__file__).resolve().parents[1]
SCRIPT = REPO_TOP / "scripts" / "docs_branch_sync.sh"
# The repo-local done-lock copy the fixtures pin as DONE_LOCK_SCRIPT, so the
# runner's internal merge-lock span always resolves this hereditary copy and
# never a deployed runtime-home twin.
DONE_LOCK_SCRIPT = REPO_TOP / "scripts" / "done-lock.sh"
NOW = "2026-04-30T12:00:00Z"


def lock_env_pins(root: Path) -> dict[str, str]:
    """Hermetic lock env: the merge-lock root and poll interval live inside
    the fixture tmp tree and the done-lock script is the repo-local copy, so
    no fixture reads or writes the host lock home."""
    return {
        "DONE_LOCK_SCRIPT": str(DONE_LOCK_SCRIPT),
        "MERGE_LOCK_ROOT": str(root / "merge-locks"),
        "MERGE_LOCK_POLL_SECS": "1",
    }


def parse_merge_exports(output: str) -> dict[str, str]:
    """Parse the acquire subcommands' `export NAME=value` stdout lines."""
    exports: dict[str, str] = {}
    for line in output.splitlines():
        for name in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
            prefix = f"export {name}="
            if line.startswith(prefix):
                exports[name] = line[len(prefix):]
    return exports


def merge_lock_status(root: Path, repo: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run merge-status against the fixture's pinned lock root."""
    env = {**fixture_git_environment(root), **lock_env_pins(root)}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(DONE_LOCK_SCRIPT), "merge-status"],
        cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def acquire_foreign_merge_lock(root: Path, repo: Path, label: str, holder_pid: int) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    """Acquire a foreign merge-lock hold in the fixture repo; returns the
    acquire process and its parsed exports."""
    env = {
        **fixture_git_environment(root),
        **lock_env_pins(root),
        "MERGE_LOCK_HOLDER_PID": str(holder_pid),
    }
    acquired = subprocess.run(
        ["bash", str(DONE_LOCK_SCRIPT), "merge-acquire", "--label", label],
        cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return acquired, parse_merge_exports(acquired.stdout)


def release_merge_lock(root: Path, repo: Path, exports: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {**fixture_git_environment(root), **lock_env_pins(root), **exports}
    return subprocess.run(
        ["bash", str(DONE_LOCK_SCRIPT), "merge-release"],
        cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def fixture_git_environment(root: Path) -> dict[str, str]:
    """Return an allowlisted Git environment, independent of host selectors."""
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(root / "home"),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "Sync Fixture",
        "GIT_AUTHOR_EMAIL": "sync@example.invalid",
        "GIT_COMMITTER_NAME": "Sync Fixture",
        "GIT_COMMITTER_EMAIL": "sync@example.invalid",
        "GIT_AUTHOR_DATE": NOW,
        "GIT_COMMITTER_DATE": NOW,
        "GIT_OPTIONAL_LOCKS": "0",
        "TZ": "Pacific/Kiritimati",
        **lock_env_pins(root),
    }


@contextmanager
def direct_main_environment(repo: "SyncRepo", trace_name: str, now: str = NOW):
    original = dict(os.environ)
    trace = repo.root / trace_name
    os.environ.clear()
    os.environ.update({
        "PATH": original.get("PATH", "/usr/bin:/bin"),
        "HOME": str(repo.root / "home"),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "Sync Fixture",
        "GIT_AUTHOR_EMAIL": "sync@example.invalid",
        "GIT_COMMITTER_NAME": "Sync Fixture",
        "GIT_COMMITTER_EMAIL": "sync@example.invalid",
        "GIT_AUTHOR_DATE": NOW,
        "GIT_COMMITTER_DATE": NOW,
        "GIT_OPTIONAL_LOCKS": "0",
        "TZ": "UTC",
        "DOCS_SYNC_NOW": now,
        "DOCS_SYNC_TRACE_FILE": str(trace),
        **lock_env_pins(repo.root),
    })
    try:
        yield trace
    finally:
        os.environ.clear()
        os.environ.update(original)

def load_runner_namespace():
    source = SCRIPT.read_text(encoding="utf-8")
    marker = "python3 - \"$@\" <<'PY'\n"
    start = source.index(marker) + len(marker)
    end = source.index("\ntry:\n    sys.exit(main())", start)
    module = types.ModuleType("docs_branch_sync_test_module")
    module.__file__ = str(SCRIPT)
    sys.modules[module.__name__] = module
    exec(compile(source[start:end], str(SCRIPT), "exec"), module.__dict__)
    return module.__dict__


def epoch(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def _concurrent_sync_worker(root_text: str, role: str, restore_entered, release_restore, events) -> None:
    root = Path(root_text)
    repo = SyncRepo.__new__(SyncRepo)
    repo.root = root
    namespace = load_runner_namespace()
    original_restore = namespace["restore_files"]
    if role == "restore-first":
        def pause_restore(*args, **kwargs):
            restore_entered.set()
            if not release_restore.wait(10):
                raise AssertionError("test did not release first restore")
            result = original_restore(*args, **kwargs)
            events.put("first-restore-complete")
            return result
        namespace["restore_files"] = pause_restore
    original_cwd = Path.cwd()
    try:
        os.chdir(root)
        now = NOW if role == "restore-first" else "2027-02-01T12:00:00Z"
        with direct_main_environment(repo, f"{role}.trace", now=now):
            namespace["main"]([])
        events.put(f"{role}-complete")
    finally:
        os.chdir(original_cwd)


class SyncRepo:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True)
        self.git_env = fixture_git_environment(root)
        (root / "home").mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Sync Fixture")
        self.git("config", "user.email", "sync@example.invalid")
        (root / ".ai-playbook").mkdir()
        (root / ".gitignore").write_text("docs/\n", encoding="utf-8")
        (root / ".ai-playbook" / "facts.md").write_text(self.facts(), encoding="utf-8")
        (root / "tracked.txt").write_text("main branch\n", encoding="utf-8")
        self.git("add", ".gitignore", ".ai-playbook/facts.md", "tracked.txt")
        self.git("commit", "-qm", "main seed")

    def facts(self, *, reviews: str | None = ".ai-playbook/reviews", metrics: str | None = ".ai-playbook/metrics", policy: str | None = None) -> str:
        rows = []
        if reviews is not None:
            rows.append(f"reviews_dir = {json.dumps(reviews)}")
        if metrics is not None:
            rows.append(f"metrics_dir = {json.dumps(metrics)}")
        if policy is not None:
            rows.append(f"worktree_policy = {json.dumps(policy)}")
        return "```toml\n" + "\n".join(rows) + "\n```\n"

    def write_facts(self, *, reviews: str | None = ".ai-playbook/reviews", metrics: str | None = ".ai-playbook/metrics", policy: str | None = None) -> None:
        (self.root / ".ai-playbook" / "facts.md").write_text(self.facts(reviews=reviews, metrics=metrics, policy=policy), encoding="utf-8")

    def git(self, *args: str, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            env=env or self.git_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def add_docs_commit(self, path: str, data: bytes, committer_date: str, *, author_date: str | None = None, first: bool = False, mode: str = "100644") -> str:
        index = self.root / f".test-index-{len(list(self.root.glob('.test-index-*')))}"
        env = {**self.git_env, "GIT_INDEX_FILE": str(index)}
        try:
            if first:
                self.git("read-tree", "--empty", env=env)
            else:
                self.git("read-tree", "refs/heads/docs", env=env)
            hashed = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"], cwd=self.root, env=env,
                input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            ).stdout.decode().strip()
            self.git("update-index", "--add", "--cacheinfo", f"{mode},{hashed},{path}", env=env)
            tree = self.git("write-tree", env=env).stdout.strip()
            date_env = {
                **env,
                "GIT_AUTHOR_DATE": author_date or committer_date,
                "GIT_COMMITTER_DATE": committer_date,
            }
            args = ["commit-tree", tree]
            if not first:
                args.extend(["-p", "refs/heads/docs"])
            args.extend(["-m", f"archive {path}"])
            commit = self.git(*args, env=date_env).stdout.strip()
            old = "0" * len(commit) if first else self.git("rev-parse", "refs/heads/docs").stdout.strip()
            self.git("update-ref", "refs/heads/docs", commit, old)
            return commit
        finally:
            index.unlink(missing_ok=True)

    def seed_docs(self, entries: list[tuple[str, bytes, str, str | None]]) -> str:
        old = None
        for path, data, committer_date, author_date in entries:
            old = self.add_docs_commit(path, data, committer_date, author_date=author_date, first=old is None)
        if old is None:
            raise AssertionError("seed_docs needs at least one path")
        return old

    def local_file(self, relative: str, data: bytes, mtime: str = NOW) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        timestamp = epoch(mtime)
        os.utime(path, (timestamp, timestamp))
        return path

    def run(self, *, extra_env: dict[str, str] | None = None, policy: str | None = None) -> subprocess.CompletedProcess[str]:
        if policy is not None:
            self.write_facts(policy=policy)
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.root / "home"),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_AUTHOR_NAME": "Sync Fixture",
            "GIT_AUTHOR_EMAIL": "sync@example.invalid",
            "GIT_COMMITTER_NAME": "Sync Fixture",
            "GIT_COMMITTER_EMAIL": "sync@example.invalid",
            "GIT_AUTHOR_DATE": NOW,
            "GIT_COMMITTER_DATE": NOW,
            "GIT_OPTIONAL_LOCKS": "0",
            "TZ": "Pacific/Kiritimati",
            "DOCS_SYNC_NOW": NOW,
            **lock_env_pins(self.root),
        }
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(SCRIPT)], cwd=self.root, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def docs_paths(self) -> list[str]:
        result = self.git("ls-tree", "-r", "--name-only", "refs/heads/docs", check=False)
        return result.stdout.splitlines() if result.returncode == 0 else []

    def blob(self, path: str) -> bytes:
        return subprocess.run(
            ["git", "cat-file", "blob", f"refs/heads/docs:{path}"], cwd=self.root,
            env=self.git_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout

    def write_raw_tree(self, entries: list[tuple[str, str, str]]) -> str:
        body = b"".join(
            mode.encode("ascii") + b" " + os.fsencode(name) + b"\0" + bytes.fromhex(oid)
            for mode, name, oid in entries
        )
        return subprocess.run(
            ["git", "hash-object", "-w", "--literally", "-t", "tree", "--stdin"], cwd=self.root,
            env=self.git_env, input=body, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True,
        ).stdout.decode("ascii").strip()

    def write_blob(self, data: bytes) -> str:
        return subprocess.run(
            ["git", "hash-object", "-w", "--stdin"], cwd=self.root,
            env=self.git_env, input=data, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True,
        ).stdout.decode("ascii").strip()

    def install_docs_tree(self, tree: str) -> str:
        commit = self.git("commit-tree", tree, "-m", "crafted docs tree").stdout.strip()
        zero = "0" * len(commit)
        self.git("update-ref", "refs/heads/docs", commit, zero)
        return commit


class DocsBranchSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="docs-sync-test-")
        self.repo = SyncRepo(Path(self.temp.name) / "repo")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_ok(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_symbolic_docs_ref_is_refused_without_changing_main(self) -> None:
        main_tip = self.repo.git("rev-parse", "refs/heads/main").stdout.strip()
        main_tree = self.repo.git("rev-parse", "refs/heads/main^{tree}").stdout.strip()
        self.repo.git("symbolic-ref", "refs/heads/docs", "refs/heads/main")

        result = self.repo.run()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("symbolic docs refs are refused", result.stderr)
        self.assertEqual(self.repo.git("symbolic-ref", "refs/heads/docs").stdout.strip(), "refs/heads/main")
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main").stdout.strip(), main_tip)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main^{tree}").stdout.strip(), main_tree)

    def test_docs_snapshot_oid_survives_symref_installed_after_enumeration(self) -> None:
        docs_tip = self.repo.seed_docs([
            (".ai-playbook/reviews/docs-only.md", b"docs snapshot\n", NOW, None),
        ])
        self.repo.git("switch", "-c", "target")
        self.repo.local_file(".ai-playbook/reviews/docs-only.md", b"target copy\n")
        self.repo.local_file(".ai-playbook/reviews/target-only.md", b"target branch\n")
        self.repo.git("add", "-f", ".ai-playbook/reviews/docs-only.md", ".ai-playbook/reviews/target-only.md")
        self.repo.git("commit", "-qm", "target branch archive")
        target_tip = self.repo.git("rev-parse", "refs/heads/target").stdout.strip()
        self.repo.git("switch", "main")
        main_tip = self.repo.git("rev-parse", "refs/heads/main").stdout.strip()
        main_tree = self.repo.git("rev-parse", "refs/heads/main^{tree}").stdout.strip()
        namespace = load_runner_namespace()
        original_git = namespace["git"]
        snapshot_reads: list[str] = []

        def interpose_symbolic_ref(args, **kwargs):
            result = original_git(args, **kwargs)
            if args[:2] == ["for-each-ref", "--format=%(refname)%00%(symref)%00%(objectname)"]:
                self.repo.git("update-ref", "-d", "refs/heads/docs")
                self.repo.git("symbolic-ref", "refs/heads/docs", "refs/heads/target")
            if args and args[0] == "ls-tree" and len(args) > 1:
                snapshot_reads.append(args[-1])
            return result

        namespace["git"] = interpose_symbolic_ref
        original_cwd = Path.cwd()
        try:
            os.chdir(self.repo.root)
            with direct_main_environment(self.repo, "symref-interposition-trace.log"):
                with self.assertRaisesRegex(namespace["SyncError"], "symbolic docs refs are refused"):
                    namespace["main"]([])
        finally:
            os.chdir(original_cwd)
            namespace["git"] = original_git

        self.assertIn(docs_tip, snapshot_reads)
        self.assertNotIn(target_tip, snapshot_reads)
        self.assertFalse((self.repo.root / ".ai-playbook/reviews/target-only.md").exists())
        self.assertEqual(self.repo.git("symbolic-ref", "refs/heads/docs").stdout.strip(), "refs/heads/target")
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main").stdout.strip(), main_tip)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main^{tree}").stdout.strip(), main_tree)

    def test_runner_ignores_host_selectors_and_stays_in_invoked_repository(self) -> None:
        other = SyncRepo(Path(self.temp.name) / "other")
        self.repo.local_file(".ai-playbook/reviews/from-a.md", b"A archive\n")
        other.local_file(".ai-playbook/reviews/from-b.md", b"B archive\n")
        other_before = other.git("rev-parse", "refs/heads/main").stdout.strip()
        other_tree = other.git("rev-parse", "refs/heads/main^{tree}").stdout.strip()
        other_index = (other.root / ".git" / "index").read_bytes()
        hostile = {
            **fixture_git_environment(self.repo.root),
            "DOCS_SYNC_NOW": NOW,
            "GIT_DIR": str(other.root / ".git"),
            "GIT_WORK_TREE": str(other.root),
            "GIT_COMMON_DIR": str(other.root / ".git"),
            "GIT_INDEX_FILE": str(other.root / ".git" / "index"),
            "GIT_OBJECT_DIRECTORY": str(other.root / ".git" / "objects"),
            "GIT_CEILING_DIRECTORIES": str(other.root.parent),
        }
        result = subprocess.run(
            ["bash", str(SCRIPT)], cwd=self.repo.root, env=hostile,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(".ai-playbook/reviews/from-a.md", self.repo.docs_paths())
        self.assertEqual(other.git("rev-parse", "refs/heads/main").stdout.strip(), other_before)
        self.assertEqual(other.git("rev-parse", "refs/heads/main^{tree}").stdout.strip(), other_tree)
        self.assertEqual((other.root / ".git" / "index").read_bytes(), other_index)
        self.assertEqual(other.git("show-ref", "--verify", "--quiet", "refs/heads/docs", check=False).returncode, 1)

    def test_witness_append_uses_direct_docs_ref(self) -> None:
        docs_tip = self.repo.seed_docs([
            (".ai-playbook/reviews/witness.md", b"archive\n", NOW, None),
        ])
        main_tip = self.repo.git("rev-parse", "refs/heads/main").stdout.strip()
        result = subprocess.run(
            ["bash", str(SCRIPT), "--append-witness", "lesson-scope-audit: fixture drift"],
            cwd=self.repo.root, env={**fixture_git_environment(self.repo.root), "DOCS_SYNC_NOW": NOW},
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        new_tip = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        self.assertNotEqual(new_tip, docs_tip)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main").stdout.strip(), main_tip)
        self.assertIn("lesson-scope-audit: fixture drift", self.repo.git("show", "-s", "--format=%B", new_tip).stdout)

    def test_witness_append_refuses_symbolic_docs_without_changing_main(self) -> None:
        main_tip = self.repo.git("rev-parse", "refs/heads/main").stdout.strip()
        main_tree = self.repo.git("rev-parse", "refs/heads/main^{tree}").stdout.strip()
        self.repo.git("symbolic-ref", "refs/heads/docs", "refs/heads/main")
        result = subprocess.run(
            ["bash", str(SCRIPT), "--append-witness", "lesson-scope-audit: fixture drift"],
            cwd=self.repo.root, env={**fixture_git_environment(self.repo.root), "DOCS_SYNC_NOW": NOW},
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("symbolic docs refs are refused", result.stderr)
        self.assertEqual(self.repo.git("symbolic-ref", "refs/heads/docs").stdout.strip(), "refs/heads/main")
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main").stdout.strip(), main_tip)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main^{tree}").stdout.strip(), main_tree)

    def test_foreign_held_merge_lock_refuses_sync_and_leaves_docs_ref_identical(self) -> None:
        self.repo.seed_docs([
            (".ai-playbook/reviews/kept.md", b"old branch copy\n", NOW, None),
        ])
        self.repo.local_file(".ai-playbook/reviews/kept.md", b"new local bytes\n")
        tip = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        acquired, exports = acquire_foreign_merge_lock(self.repo.root, self.repo.root, "blocker", holder.pid)
        self.assertEqual(acquired.returncode, 0, acquired.stderr)
        try:
            result = self.repo.run(extra_env={"DOCS_SYNC_MERGE_MAX_WAIT": "2"})
        finally:
            released = release_merge_lock(self.repo.root, self.repo.root, exports)
        self.assertEqual(released.returncode, 0, released.stderr)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("timed out after 2s", result.stderr)
        self.assertIn("label: blocker", result.stderr)
        self.assertIn("docs ref stays unchanged", result.stderr)
        self.assertNotIn("landed", result.stdout)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)

    def test_foreign_held_merge_lock_refuses_witness_append_and_leaves_docs_ref_identical(self) -> None:
        docs_tip = self.repo.seed_docs([
            (".ai-playbook/reviews/witness.md", b"archive\n", NOW, None),
        ])
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        acquired, exports = acquire_foreign_merge_lock(self.repo.root, self.repo.root, "blocker", holder.pid)
        self.assertEqual(acquired.returncode, 0, acquired.stderr)
        env = {
            **fixture_git_environment(self.repo.root),
            "DOCS_SYNC_NOW": NOW,
            "DOCS_SYNC_MERGE_MAX_WAIT": "2",
        }
        try:
            result = subprocess.run(
                ["bash", str(SCRIPT), "--append-witness", "lesson-scope-audit: fixture drift"],
                cwd=self.repo.root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        finally:
            released = release_merge_lock(self.repo.root, self.repo.root, exports)
        self.assertEqual(released.returncode, 0, released.stderr)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("timed out after 2s", result.stderr)
        self.assertIn("label: blocker", result.stderr)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), docs_tip)

    def test_sync_failure_after_merge_acquire_releases_and_traces_the_acquire(self) -> None:
        old_tip = self.repo.seed_docs([
            (".ai-playbook/reviews/kept.md", b"old\n", "2026-04-20T00:00:00Z", None),
        ])
        self.repo.local_file(".ai-playbook/reviews/kept.md", b"updated\n")
        namespace = load_runner_namespace()
        sync_error = namespace["SyncError"]
        original_snapshot = namespace["docs_ref_snapshot"]

        def fail_after_acquire(repo: Path):
            raise sync_error("injected mid-sync failure")

        namespace["docs_ref_snapshot"] = fail_after_acquire
        original_cwd = Path.cwd()
        try:
            os.chdir(self.repo.root)
            with direct_main_environment(self.repo, "merge-release-sync-trace.log") as trace:
                with self.assertRaisesRegex(sync_error, "injected mid-sync failure"):
                    namespace["main"]([])
        finally:
            os.chdir(original_cwd)
            namespace["docs_ref_snapshot"] = original_snapshot
        self.assertIn("merge-acquire", trace.read_text(encoding="utf-8").splitlines())
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), old_tip)
        status = merge_lock_status(self.repo.root, self.repo.root)
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("free", status.stdout)
        self.assertEqual(list((self.repo.root / "merge-locks").iterdir()), [])

    def test_witness_failure_after_merge_acquire_releases_and_traces_the_acquire(self) -> None:
        main_tip = self.repo.git("rev-parse", "refs/heads/main").stdout.strip()
        namespace = load_runner_namespace()
        sync_error = namespace["SyncError"]
        original_cwd = Path.cwd()
        try:
            os.chdir(self.repo.root)
            with direct_main_environment(self.repo, "merge-release-witness-trace.log") as trace:
                with self.assertRaisesRegex(sync_error, "no docs branch"):
                    namespace["main"](["--append-witness", "lesson-scope-audit: fixture drift"])
        finally:
            os.chdir(original_cwd)
        self.assertIn("merge-acquire", trace.read_text(encoding="utf-8").splitlines())
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main").stdout.strip(), main_tip)
        status = merge_lock_status(self.repo.root, self.repo.root)
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("free", status.stdout)
        self.assertEqual(list((self.repo.root / "merge-locks").iterdir()), [])

    def test_witness_append_cas_loss_keeps_competing_tip_and_preserves_recovery_ref(self) -> None:
        witness_line = "lesson-scope-audit: fixture drift: caller-owned witness text"
        old_docs_tip = self.repo.seed_docs([
            (".ai-playbook/reviews/witness.md", b"archive\n", NOW, None),
        ])
        main_tip = self.repo.git("rev-parse", "refs/heads/main").stdout.strip()
        namespace = load_runner_namespace()
        sync_error = namespace["SyncError"]
        original_update = namespace["update_docs_ref"]

        def racing_update(repo: Path, new_tip: str, expected: str) -> None:
            docs_tree = self.repo.git("rev-parse", "refs/heads/docs^{tree}").stdout.strip()
            competing = self.repo.git(
                "commit-tree", docs_tree, "-p", expected, "-m", "competing docs tip",
            ).stdout.strip()
            self.repo.git("update-ref", "refs/heads/docs", competing)
            racing_update.competing = competing
            original_update(repo, new_tip, expected)

        racing_update.competing = None
        namespace["update_docs_ref"] = racing_update
        original_cwd = Path.cwd()
        try:
            os.chdir(self.repo.root)
            with direct_main_environment(self.repo, "witness-cas-loss-trace.log"):
                with self.assertRaisesRegex(sync_error, "docs tip changed; witness preserved at "):
                    namespace["main"](["--append-witness", witness_line])
        finally:
            os.chdir(original_cwd)
            namespace["update_docs_ref"] = original_update
        self.assertIsNotNone(racing_update.competing)
        self.assertEqual(
            self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(),
            racing_update.competing,
        )
        recoveries = self.repo.git(
            "for-each-ref", "--format=%(refname)%00%(objectname)", "refs/docs-witness-recovery/",
        ).stdout.strip().splitlines()
        self.assertEqual(len(recoveries), 1)
        refname, object_name = recoveries[0].split("\0")
        self.assertTrue(refname.startswith("refs/docs-witness-recovery/"))
        self.assertIn(witness_line, self.repo.git("show", "-s", "--format=%B", object_name).stdout)
        self.assertEqual(self.repo.git("rev-parse", f"{object_name}^").stdout.strip(), old_docs_tip)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/main").stdout.strip(), main_tip)
        status = merge_lock_status(self.repo.root, self.repo.root)
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("free", status.stdout)
        self.assertEqual(list((self.repo.root / "merge-locks").iterdir()), [])

    def test_sync_lock_serializes_prune_before_restore(self) -> None:
        self.repo.seed_docs([
            (".ai-playbook/reviews/expiring.md", b"old branch copy\n", NOW, None),
        ])
        import multiprocessing
        context = multiprocessing.get_context("fork")
        restore_entered = context.Event()
        release_restore = context.Event()
        events = context.Queue()
        first = context.Process(target=_concurrent_sync_worker, args=(str(self.repo.root), "restore-first", restore_entered, release_restore, events))
        second = context.Process(target=_concurrent_sync_worker, args=(str(self.repo.root), "prune-second", restore_entered, release_restore, events))
        first.start()
        self.assertTrue(restore_entered.wait(10), "first sync did not reach restore")
        second.start()
        second.join(0.2)
        self.assertTrue(second.is_alive(), "second sync should wait for the first sync lock")
        release_restore.set()
        first.join(10)
        second.join(10)
        self.assertEqual(first.exitcode, 0)
        self.assertEqual(second.exitcode, 0)
        observed = [events.get(timeout=2) for _ in range(3)]
        self.assertLess(observed.index("first-restore-complete"), observed.index("prune-second-complete"))
        self.assertNotIn(".ai-playbook/reviews/expiring.md", self.repo.docs_paths())

    def test_fixture_git_calls_ignore_host_repository_selectors(self) -> None:
        selectors = {
            "GIT_DIR": str(REPO_TOP / ".git"),
            "GIT_WORK_TREE": str(REPO_TOP),
            "GIT_INDEX_FILE": str(REPO_TOP / ".git" / "index"),
            "GIT_COMMON_DIR": str(REPO_TOP / ".git"),
            "GIT_OBJECT_DIRECTORY": str(REPO_TOP / ".git" / "objects"),
            "GIT_CEILING_DIRECTORIES": str(REPO_TOP.parent),
        }
        outer_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(Path.home()),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
        }

        def outer_git(*args: str) -> str:
            return subprocess.run(
                ["git", "-C", str(REPO_TOP), *args], env=outer_env,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            ).stdout.strip()

        outer_tip = outer_git("rev-parse", "HEAD")
        outer_tree = outer_git("rev-parse", "HEAD^{tree}")
        with patch.dict(os.environ, selectors):
            fixture = SyncRepo(Path(self.temp.name) / "hostile-repo")
            self.assertTrue(set(selectors).isdisjoint(fixture.git_env))
            fixture.seed_docs([(".ai-playbook/reviews/fixture.md", b"isolated\n", NOW, None)])
            fixture.local_file(".ai-playbook/reviews/local.md", b"local\n")
            result = fixture.run()
            self.assert_ok(result)
            self.assertIn(".ai-playbook/reviews/fixture.md", fixture.docs_paths())
            self.assertEqual(outer_git("rev-parse", "HEAD"), outer_tip)
            self.assertEqual(outer_git("rev-parse", "HEAD^{tree}"), outer_tree)

    def test_symlink_containment_rejects_windows_absolute_and_backslash_escape_targets(self) -> None:
        under = load_runner_namespace()["symlink_target_is_under"]
        for target in ("C:/private/file", "C:\\private\\file", "\\\\server\\share\\file", "..\\..\\outside"):
            with self.subTest(target=target):
                self.assertFalse(under(".ai-playbook/reviews/link", target, ".ai-playbook/reviews"))
        self.assertTrue(under(".ai-playbook/reviews/link", "nested\\file.md", ".ai-playbook/reviews"))

    def test_only_review_and_metrics_archives_remain_and_removed_absent_paths_are_reported(self) -> None:
        old = self.repo.seed_docs([
            (".ai-playbook/reviews/kept.md", b"branch review\n", "2026-04-20T00:00:00Z", None),
            (".ai-playbook/metrics/run.json", b"{}\n", "2026-04-20T00:00:00Z", None),
            ("docs/tmp/absent.md", b"scratch\n", "2026-04-20T00:00:00Z", None),
            ("docs/history/plans/absent.md", b"plan\n", "2026-04-20T00:00:00Z", None),
        ])
        tmp = self.repo.local_file("docs/tmp/local.md", b"local scratch\n")
        before = tmp.read_bytes()
        trace = self.repo.root / "sync-trace.log"
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assert_ok(result)
        self.assertCountEqual(self.repo.docs_paths(), [
            ".ai-playbook/reviews/kept.md", ".ai-playbook/metrics/run.json",
        ])
        self.assertIn("docs-branch: pruned docs/tmp/absent.md", result.stdout + result.stderr)
        self.assertIn("docs-branch: pruned docs/history/plans/absent.md", result.stdout + result.stderr)
        self.assertFalse((self.repo.root / "docs/tmp/absent.md").exists())
        self.assertEqual(tmp.read_bytes(), before)
        self.assertTrue(self.repo.git("merge-base", "--is-ancestor", old, "refs/heads/docs", check=False).returncode == 0)
        self.assertCountEqual(trace.read_text(encoding="utf-8").splitlines(), [
            "merge-acquire", "candidate-walk", "snapshot", "prune", "ref-update-cas",
        ])

    def test_malformed_branch_components_refuse_before_restore_and_keep_ref_unchanged(self) -> None:
        payload = self.repo.write_blob(b"escaped branch payload\n")
        outside = self.repo.write_raw_tree([("100644", "escaped.md", payload)])
        traversal = self.repo.write_raw_tree([("040000", "outside", outside)])
        for name in ("..", "..", ".."):
            traversal = self.repo.write_raw_tree([("040000", name, traversal)])
        reviews = traversal
        history = self.repo.write_raw_tree([("040000", "reviews", reviews)])
        docs = self.repo.write_raw_tree([("040000", "history", history)])
        tip = self.repo.install_docs_tree(self.repo.write_raw_tree([("040000", "docs", docs)]))
        escaped = self.repo.root / "outside" / "escaped.md"
        trace = self.repo.root / "malformed-tree-trace.log"

        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("invalid docs-branch tree path", result.stderr)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        self.assertFalse(escaped.exists())
        trace_body = trace.read_text(encoding="utf-8")
        for forbidden in ("prune", "ref-update-cas", "ref-verify-absent"):
            self.assertNotIn(forbidden, trace_body)

    def test_absent_empty_tree_cas_refuses_competing_docs_ref(self) -> None:
        self.assertNotEqual(
            self.repo.git("show-ref", "--verify", "--quiet", "refs/heads/docs", check=False).returncode,
            0,
        )
        namespace = load_runner_namespace()
        original_index_tree = namespace["index_tree"]
        original_cwd = Path.cwd()
        race_tip: list[str] = []

        def create_competing_ref(repo, paths, index_path):
            tree = original_index_tree(repo, paths, index_path)
            race_tip.append(self.repo.seed_docs([
                (".ai-playbook/reviews/peer.md", b"peer archive\n", NOW, None),
            ]))
            return tree

        namespace["index_tree"] = create_competing_ref
        with direct_main_environment(self.repo, "empty-race-trace.log") as trace:
            try:
                os.chdir(self.repo.root)
                with self.assertRaisesRegex(namespace["SyncError"], "expected absent"):
                    namespace["main"]([])
            finally:
                os.chdir(original_cwd)
                namespace["index_tree"] = original_index_tree

        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), race_tip[0])
        self.assertEqual(self.repo.blob(".ai-playbook/reviews/peer.md"), b"peer archive\n")
        trace_body = trace.read_text(encoding="utf-8")
        self.assertIn("ref-verify-absent", trace_body)
        self.assertNotIn("ref-update-cas", trace_body)

    def test_any_execute_bit_is_preserved_as_executable_archive_mode(self) -> None:
        path = self.repo.local_file(".ai-playbook/reviews/group-executable.md", b"executable\n")
        path.chmod(path.stat().st_mode | 0o010)
        result = self.repo.run()
        self.assert_ok(result)
        entry = self.repo.git("ls-tree", "refs/heads/docs", ".ai-playbook/reviews/group-executable.md").stdout
        self.assertTrue(entry.startswith("100755 blob "), entry)

    def test_branch_blobs_batch_matches_single_object_reads(self) -> None:
        self.repo.seed_docs([
            (".ai-playbook/reviews/one.md", b"shared\n", NOW, None),
            (".ai-playbook/reviews/two.md", b"shared\n", NOW, None),
            (".ai-playbook/metrics/run.json", b"{}\n", NOW, None),
        ])
        namespace = load_runner_namespace()
        branch = namespace["read_branch_tree"](self.repo.root, self.repo.git("rev-parse", "refs/heads/docs").stdout.strip())
        expected = {
            entry.oid: subprocess.run(
                ["git", "cat-file", "blob", entry.oid], cwd=self.repo.root, env=self.repo.git_env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            ).stdout
            for entry in branch.values()
        }
        original_git = namespace["git"]
        batches: list[list[str]] = []

        def counted_git(args, **kwargs):
            if args[:2] == ["cat-file", "--batch"]:
                batches.append(args)
            return original_git(args, **kwargs)

        namespace["git"] = counted_git
        actual = namespace["branch_blobs"](self.repo.root, list(branch.values()))
        self.assertEqual(actual, expected)
        self.assertEqual(len(batches), 1)

    def test_pruned_submodule_path_is_reported(self) -> None:
        path = ".ai-playbook/reviews/vendor"
        self.repo.add_docs_commit(path, b"submodule-object\n", NOW, first=True, mode="160000")
        result = self.repo.run()
        self.assert_ok(result)
        self.assertIn(f"docs-branch: pruned {path}", result.stdout)
        self.assertNotIn(path, self.repo.docs_paths())
        self.assertFalse((self.repo.root / path).exists())

    def test_custom_roots_are_normalized_and_fixed_reviews_always_apply(self) -> None:
        self.repo.write_facts(reviews=r"docs\team\reviews///", metrics="docs/team/metrics/")
        self.repo.local_file("docs/reviews/fixed.md", b"fixed\n")
        self.repo.local_file("docs/team/reviews/custom.md", b"custom review\n")
        self.repo.local_file("docs/team/metrics/custom.json", b"custom metric\n")
        result = self.repo.run()
        self.assert_ok(result)
        self.assertCountEqual(self.repo.docs_paths(), [
            "docs/reviews/fixed.md", "docs/team/reviews/custom.md", "docs/team/metrics/custom.json",
        ])

    def test_absent_root_keys_use_history_defaults(self) -> None:
        self.repo.write_facts(reviews=None, metrics=None)
        self.repo.local_file(".ai-playbook/reviews/default.md", b"r\n")
        self.repo.local_file(".ai-playbook/metrics/default.json", b"m\n")
        self.assert_ok(self.repo.run())
        self.assertCountEqual(self.repo.docs_paths(), [
            ".ai-playbook/reviews/default.md", ".ai-playbook/metrics/default.json",
        ])

    def test_review_certs_seal_survives_docs_branch_rebuild(self) -> None:
        # The review-certs retention root (plan
        # 2026-10-11-review-certs-seal-home-untracked Task 3): a seal file in
        # the root is copied to the docs branch and comes back from the
        # configured roots when the branch is rebuilt (the witnessed
        # rebuild-drop class, commit fc3864e28).
        seal = self.repo.local_file(".ai-playbook/review-certs/round-seal.md", b"seal entry\n")
        self.assert_ok(self.repo.run())
        self.assertIn(".ai-playbook/review-certs/round-seal.md", self.repo.docs_paths())
        self.assertEqual(self.repo.blob(".ai-playbook/review-certs/round-seal.md"), b"seal entry\n")
        self.assertEqual(seal.read_bytes(), b"seal entry\n")
        self.repo.git("update-ref", "-d", "refs/heads/docs")
        self.assert_ok(self.repo.run())
        self.assertIn(".ai-playbook/review-certs/round-seal.md", self.repo.docs_paths())
        self.assertEqual(self.repo.blob(".ai-playbook/review-certs/round-seal.md"), b"seal entry\n")

    def test_same_role_overlaps_are_merged_once(self) -> None:
        self.repo.write_facts(reviews="docs/reviews", metrics=".ai-playbook/metrics")
        nested = self.repo.root / "docs" / "reviews" / "nested" / "reviews"
        nested.mkdir(parents=True)
        (self.repo.root / "docs" / "reviews" / "one.md").write_text("one\n", encoding="utf-8")
        (nested / "two.md").write_text("two\n", encoding="utf-8")
        result = self.repo.run()
        self.assert_ok(result)
        self.assertCountEqual(self.repo.docs_paths(), [
            "docs/reviews/one.md", "docs/reviews/nested/reviews/two.md",
        ])

    def test_invalid_facts_or_roots_refuse_before_walk_snapshot_or_prune(self) -> None:
        invalid_facts = [
            self.repo.facts(reviews="", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="/tmp/reviews", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="docs/../reviews", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="docs/./reviews", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="docs/team/archive", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="docs/team/metrics", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="docs", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="docs/team", metrics=".ai-playbook/metrics"),
            self.repo.facts(reviews="docs/team/reviews", metrics="docs/team/reviews/metrics"),
        ]
        self.repo.seed_docs([("docs/tmp/old.md", b"old\n", "2026-04-20T00:00:00Z", None)])
        initial_tip = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        for index, facts in enumerate(invalid_facts):
            with self.subTest(facts=facts):
                facts_path = self.repo.root / ".ai-playbook" / "facts.md"
                facts_path.write_text(facts, encoding="utf-8")
                trace = self.repo.root / f"trace-{index}.log"
                result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), initial_tip)
                trace_body = trace.read_text(encoding="utf-8") if trace.exists() else ""
                for forbidden in ("candidate-walk", "snapshot", "prune"):
                    self.assertNotIn(forbidden, trace_body)

    def test_missing_and_malformed_facts_refuse_without_ref_change(self) -> None:
        self.repo.seed_docs([(".ai-playbook/reviews/keep.md", b"keep\n", "2026-04-20T00:00:00Z", None)])
        tip = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        facts = self.repo.root / ".ai-playbook" / "facts.md"
        trace = self.repo.root / "facts-trace.log"
        facts.unlink()
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        # The merge-lock acquire is traced before the facts parse (the runner
        # holds the lock across the whole sync body); no mutation stage runs.
        self.assertEqual(trace.read_text(encoding="utf-8").splitlines(), ["merge-acquire"])
        facts.write_text("```toml\nreviews_dir = [\n```\n", encoding="utf-8")
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        self.assertEqual(trace.read_text(encoding="utf-8").splitlines(), ["merge-acquire", "merge-acquire"])
        facts.unlink()
        facts.mkdir()
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        self.assertEqual(trace.read_text(encoding="utf-8").splitlines(), ["merge-acquire", "merge-acquire", "merge-acquire"])

    def test_fixed_reviews_symlink_to_configured_root_is_archived_once_at_target(self) -> None:
        configured = self.repo.root / "docs" / "team" / "archive" / "reviews"
        configured.mkdir(parents=True)
        (configured / "review.md").write_text("review\n", encoding="utf-8")
        alias = self.repo.root / "docs" / "reviews"
        alias.parent.mkdir(parents=True, exist_ok=True)
        try:
            alias.symlink_to("team/archive/reviews", target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        self.repo.write_facts(reviews="docs/team/archive/reviews", metrics=".ai-playbook/metrics")
        result = self.repo.run()
        self.assert_ok(result)
        paths = self.repo.docs_paths()
        self.assertEqual(paths, ["docs/team/archive/reviews/review.md"])

    def test_fixed_reviews_symlink_to_outside_docs_or_wrong_role_refuses(self) -> None:
        for target in ("../outside/reviews", "team/metrics"):
            with self.subTest(target=target):
                if self.repo.git("show-ref", "--verify", "--quiet", "refs/heads/docs", check=False).returncode == 0:
                    self.repo.git("update-ref", "-d", "refs/heads/docs")
                alias = self.repo.root / "docs" / "reviews"
                if alias.is_symlink() or alias.exists():
                    alias.unlink()
                alias.parent.mkdir(parents=True, exist_ok=True)
                resolved = (alias.parent / target).resolve()
                resolved.mkdir(parents=True, exist_ok=True)
                alias.symlink_to(target, target_is_directory=True)
                self.repo.write_facts(reviews="docs/team/reviews", metrics=".ai-playbook/metrics")
                tip = self.repo.seed_docs([(".ai-playbook/reviews/branch.md", b"branch\n", "2026-04-20T00:00:00Z", None)])
                result = self.repo.run()
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                if target.startswith("../"):
                    self.assertIn("resolves outside docs/", result.stdout + result.stderr)
                else:
                    self.assertIn("wrong archive role", result.stdout + result.stderr)
                self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)

    def test_escaping_symlink_inside_allowed_root_refuses_without_copy(self) -> None:
        outside = self.repo.root / "outside" / "secret.md"
        outside.parent.mkdir(parents=True)
        outside.write_text("outside secret\n", encoding="utf-8")
        reviews = self.repo.root / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True)
        try:
            (reviews / "escape.md").symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        tip = self.repo.seed_docs([(".ai-playbook/metrics/old.json", b"{}\n", "2026-04-20T00:00:00Z", None)])
        trace = self.repo.root / "escape-trace.log"
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive symlink escapes its allowed root", result.stdout + result.stderr)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        self.assertNotIn(b"outside secret", self.repo.blob(".ai-playbook/metrics/old.json"))
        trace_body = trace.read_text(encoding="utf-8")
        self.assertIn("candidate-walk", trace_body)
        for forbidden in ("snapshot", "prune", "ref-update-cas", "ref-update-no-cas"):
            self.assertNotIn(forbidden, trace_body)

    def test_chained_local_symlink_escape_refuses_before_snapshot(self) -> None:
        reviews = self.repo.root / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True)
        try:
            (reviews / "link").symlink_to("nested", target_is_directory=True)
            (reviews / "nested").symlink_to("../../../outside", target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        self.repo.seed_docs([(".ai-playbook/metrics/keep.json", b"{}\n", "2026-04-20T00:00:00Z", None)])
        tip = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        trace = self.repo.root / "chain-trace.log"
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive symlink escapes its allowed root", result.stdout + result.stderr)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        trace_body = trace.read_text(encoding="utf-8")
        self.assertNotIn("snapshot", trace_body)
        self.assertNotIn("prune", trace_body)

    def test_intermediate_symlink_then_parent_traversal_refuses_without_ref_change(self) -> None:
        reviews = self.repo.root / ".ai-playbook" / "reviews"
        reviews.mkdir(parents=True)
        try:
            (self.repo.root / "docs" / "escape").symlink_to("../outside", target_is_directory=True)
            (reviews / "traversal.md").symlink_to("../../escape/../history/reviews/branch.md")
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        tip = self.repo.seed_docs([(".ai-playbook/metrics/keep.json", b"{}\n", "2026-04-20T00:00:00Z", None)])
        trace = self.repo.root / "intermediate-link-trace.log"
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("archive symlink escapes its allowed root", result.stdout + result.stderr)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        trace_body = trace.read_text(encoding="utf-8")
        self.assertIn("candidate-walk", trace_body)
        for forbidden in ("snapshot", "prune", "ref-update-cas", "ref-update-no-cas"):
            self.assertNotIn(forbidden, trace_body)

    def test_chained_branch_symlink_escape_refuses_before_ref_update(self) -> None:
        self.repo.add_docs_commit(".ai-playbook/reviews/link", b"nested", "2026-04-20T00:00:00Z", first=True, mode="120000")
        self.repo.add_docs_commit(".ai-playbook/reviews/nested", b"../../../outside", "2026-04-20T00:00:00Z", mode="120000")
        tip = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        trace = self.repo.root / "branch-chain-trace.log"
        result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("docs-branch archive symlink escapes its allowed root", result.stdout + result.stderr)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), tip)
        trace_body = trace.read_text(encoding="utf-8")
        self.assertNotIn("prune", trace_body)
        self.assertNotIn("ref-update-cas", trace_body)
        self.assertNotIn("ref-update-no-cas", trace_body)

    def test_sync_refuses_candidate_swapped_to_escaping_symlink_without_ref_change(self) -> None:
        outside = self.repo.root.parent / "outside-race.txt"
        outside.write_bytes(b"must not be read\n")
        candidate = self.repo.local_file(".ai-playbook/reviews/race.md", b"safe\n")
        old_tip = self.repo.seed_docs([
            (".ai-playbook/metrics/keep.json", b"{}\n", "2026-04-20T00:00:00Z", None),
        ])
        trace = self.repo.root / "swap-trace.log"
        namespace = load_runner_namespace()
        sync_error = namespace["SyncError"]
        original_reader = namespace["read_regular_candidate"]
        original_os = namespace["os"]
        original_cwd = Path.cwd()
        read_calls: list[int] = []

        class OSProxy:
            def __getattr__(self, name):
                return getattr(original_os, name)

            def read(self, descriptor, size):
                read_calls.append(descriptor)
                return original_os.read(descriptor, size)

        def swap_then_read(repo, root, path, expected):
            path.unlink()
            path.symlink_to(outside)
            return original_reader(repo, root, path, expected)

        namespace["read_regular_candidate"] = swap_then_read
        namespace["os"] = OSProxy()
        with direct_main_environment(self.repo, "candidate-race-trace.log") as trace:
            try:
                os.chdir(self.repo.root)
                with self.assertRaisesRegex(sync_error, "cannot read archive file"):
                    namespace["main"]([])
            finally:
                os.chdir(original_cwd)
        self.assertEqual(trace.parent, self.repo.root)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), old_tip)
        self.assertEqual(outside.read_bytes(), b"must not be read\n")
        self.assertTrue(candidate.is_symlink())
        self.assertEqual(read_calls, [])
        self.assertNotIn("snapshot", trace.read_text(encoding="utf-8") if trace.exists() else "")

    def test_sync_refuses_allowed_root_swapped_to_symlink_before_snapshot(self) -> None:
        namespace = load_runner_namespace()
        sync_error = namespace["SyncError"]
        original_open = namespace["open_repo_directory"]
        original_os = namespace["os"]
        original_cwd = Path.cwd()

        for swapped_relative in (".ai-playbook/reviews", ".ai-playbook"):
            with self.subTest(swapped=swapped_relative):
                repo = SyncRepo(Path(self.temp.name) / swapped_relative.replace("/", "-"))
                self.repo = repo
                outside = repo.root.parent / f"outside-root-{repo.root.name}"
                outside.mkdir()
                (outside / "secret.md").write_bytes(b"must not be read\n")
                (repo.root / ".ai-playbook/reviews").mkdir(parents=True)
                old_tip = repo.seed_docs([
                    (".ai-playbook/metrics/keep.json", b"{}\n", "2026-04-20T00:00:00Z", None),
                ])
                read_calls: list[int] = []

                class OSProxy:
                    def __getattr__(self, name):
                        return getattr(original_os, name)

                    def read(self, descriptor, size):
                        read_calls.append(descriptor)
                        return original_os.read(descriptor, size)

                swapped = False
                swapped_parts = Path(swapped_relative).parts

                def swap_root_before_open(repo_root, parts, *, create):
                    nonlocal swapped
                    if tuple(parts[:len(swapped_parts)]) == swapped_parts and not swapped:
                        target = repo.root.joinpath(*swapped_parts)
                        moved = target.with_name(target.name + "-original")
                        target.rename(moved)
                        target.symlink_to(outside, target_is_directory=True)
                        swapped = True
                    return original_open(repo_root, parts, create=create)

                namespace["open_repo_directory"] = swap_root_before_open
                namespace["os"] = OSProxy()
                with direct_main_environment(repo, "root-race-trace.log") as trace:
                    try:
                        os.chdir(repo.root)
                        with self.assertRaisesRegex(sync_error, "cannot safely traverse archive root"):
                            namespace["main"]([])
                    finally:
                        os.chdir(original_cwd)
                self.assertTrue(swapped)
                self.assertEqual(repo.git("rev-parse", "refs/heads/docs").stdout.strip(), old_tip)
                self.assertEqual((outside / "secret.md").read_bytes(), b"must not be read\n")
                self.assertEqual(read_calls, [])
                trace = repo.root / "sync-trace.log"
                self.assertNotIn("snapshot", trace.read_text(encoding="utf-8") if trace.exists() else "")

    def test_failure_building_replacement_tree_leaves_docs_tip_unchanged(self) -> None:
        old_tip = self.repo.seed_docs([
            (".ai-playbook/reviews/kept.md", b"old\n", "2026-04-20T00:00:00Z", None),
        ])
        self.repo.local_file(".ai-playbook/reviews/kept.md", b"updated\n")
        trace = self.repo.root / "tree-failure-trace.log"
        namespace = load_runner_namespace()
        sync_error = namespace["SyncError"]
        original_index_tree = namespace["index_tree"]
        original_cwd = Path.cwd()

        def fail_tree(*args, **kwargs):
            raise sync_error("injected replacement-tree failure")

        namespace["index_tree"] = fail_tree
        with direct_main_environment(self.repo, "tree-failure-trace.log") as trace:
            try:
                os.chdir(self.repo.root)
                with self.assertRaisesRegex(sync_error, "injected replacement-tree failure"):
                    namespace["main"]([])
            finally:
                os.chdir(original_cwd)
                namespace["index_tree"] = original_index_tree
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), old_tip)
        trace_body = trace.read_text(encoding="utf-8")
        self.assertIn("snapshot", trace_body)
        self.assertIn("prune", trace_body)
        self.assertNotIn("ref-update-cas", trace_body)

    def test_cutoff_is_strict_utc_month_end_and_uses_committer_date(self) -> None:
        before = "2026-02-28T11:59:59Z"
        at = "2026-02-28T12:00:00Z"
        after = "2026-02-28T12:00:01Z"
        self.repo.seed_docs([
            (".ai-playbook/reviews/before.md", b"before\n", before, "2026-05-01T00:00:00Z"),
            (".ai-playbook/reviews/at.md", b"at\n", at, "2026-01-01T00:00:00Z"),
            (".ai-playbook/reviews/after.md", b"after\n", after, "2026-01-01T00:00:00Z"),
            (".ai-playbook/metrics/unrelated-tip.json", b"{}\n", "2026-04-29T00:00:00Z", None),
        ])
        result = self.repo.run()
        self.assert_ok(result)
        self.assertCountEqual(self.repo.docs_paths(), [
            ".ai-playbook/reviews/at.md", ".ai-playbook/reviews/after.md", ".ai-playbook/metrics/unrelated-tip.json",
        ])
        self.assertFalse((self.repo.root / ".ai-playbook/reviews/before.md").exists())
        self.assertTrue((self.repo.root / ".ai-playbook/reviews/at.md").exists())
        self.assertTrue((self.repo.root / ".ai-playbook/reviews/after.md").exists())

    def test_expired_copy_only_renews_for_recent_changed_bytes_and_new_paths(self) -> None:
        old = self.repo.seed_docs([
            (".ai-playbook/reviews/identical.md", b"same\n", "2026-02-01T00:00:00Z", None),
            (".ai-playbook/reviews/changed.md", b"old\n", "2026-02-01T00:00:00Z", None),
        ])
        identical = self.repo.local_file(".ai-playbook/reviews/identical.md", b"same\n")
        self.repo.local_file(".ai-playbook/reviews/changed.md", b"new\n")
        self.repo.local_file(".ai-playbook/reviews/new.md", b"new archive\n")
        before = {p: (self.repo.root / p).read_bytes() for p in (
            ".ai-playbook/reviews/identical.md", ".ai-playbook/reviews/changed.md", ".ai-playbook/reviews/new.md",
        )}
        result = self.repo.run()
        self.assert_ok(result)
        self.assertCountEqual(self.repo.docs_paths(), [
            ".ai-playbook/reviews/changed.md", ".ai-playbook/reviews/new.md",
        ])
        self.assertEqual(self.repo.blob(".ai-playbook/reviews/changed.md"), b"new\n")
        self.assertEqual(self.repo.blob(".ai-playbook/reviews/new.md"), b"new archive\n")
        self.assertEqual({p: (self.repo.root / p).read_bytes() for p in before}, before)
        self.assertNotEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), old)
        self.assertEqual(identical.stat().st_mtime, epoch(NOW))

    def test_recent_changed_bytes_renew_even_when_mtime_predates_latest_path_change(self) -> None:
        path = ".ai-playbook/reviews/changed.md"
        self.repo.seed_docs([
            (path, b"historical\n", "2026-04-20T00:00:00Z", None),
            (".ai-playbook/metrics/later-tip.json", b"{}\n", "2026-04-29T00:00:00Z", None),
        ])
        local = self.repo.local_file(path, b"recent changed\n", "2026-04-10T00:00:00Z")
        result = self.repo.run()
        self.assert_ok(result)
        self.assertEqual(self.repo.blob(path), b"recent changed\n")
        self.assertEqual(local.read_bytes(), b"recent changed\n")
        self.assertEqual(local.stat().st_mtime, epoch("2026-04-10T00:00:00Z"))

    def test_recent_branch_only_is_restored_but_expired_branch_only_is_pruned(self) -> None:
        old = self.repo.seed_docs([
            (".ai-playbook/reviews/recent.md", b"recent review\n", "2026-04-20T00:00:00Z", None),
            (".ai-playbook/reviews/expired.md", b"expired review\n", "2026-02-01T00:00:00Z", None),
            ("docs/tmp/scratch.md", b"scratch\n", "2026-04-20T00:00:00Z", None),
        ])
        scratch = self.repo.local_file("docs/tmp/local.md", b"local tmp bytes\n")
        result = self.repo.run()
        self.assert_ok(result)
        self.assertEqual((self.repo.root / ".ai-playbook/reviews/recent.md").read_bytes(), b"recent review\n")
        self.assertFalse((self.repo.root / ".ai-playbook/reviews/expired.md").exists())
        self.assertEqual(scratch.read_bytes(), b"local tmp bytes\n")
        self.assertCountEqual(self.repo.docs_paths(), [".ai-playbook/reviews/recent.md"])
        self.assertEqual(self.repo.git("merge-base", "--is-ancestor", old, "refs/heads/docs", check=False).returncode, 0)

    def test_recent_changed_local_bytes_win_even_when_branch_path_change_is_later(self) -> None:
        relative = ".ai-playbook/reviews/recent.md"
        self.repo.seed_docs([(relative, b"newer branch bytes\n", "2026-04-20T00:00:00Z", None)])
        local = self.repo.local_file(relative, b"older checkout bytes\n", "2026-04-10T00:00:00Z")
        result = self.repo.run()
        self.assert_ok(result)
        self.assertEqual(local.read_bytes(), b"older checkout bytes\n")
        self.assertEqual(self.repo.blob(relative), b"older checkout bytes\n")

    def test_staged_local_deletion_is_not_restored(self) -> None:
        relative = ".ai-playbook/reviews/intentional-delete.md"
        path = self.repo.local_file(relative, b"main copy\n")
        self.repo.git("add", "-f", relative)
        self.repo.git("commit", "-qm", "track local archive source")
        old = self.repo.seed_docs([(relative, b"docs branch copy\n", "2026-04-20T00:00:00Z", None)])
        self.repo.git("rm", "-q", "--", relative)
        index_before = (self.repo.root / ".git" / "index").read_bytes()
        result = self.repo.run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(path.exists())
        self.assertIn(relative, self.repo.docs_paths())
        self.assertEqual((self.repo.root / ".git" / "index").read_bytes(), index_before)
        self.assertEqual(self.repo.git("merge-base", "--is-ancestor", old, "refs/heads/docs", check=False).returncode, 0)

    def test_worktree_policy_does_not_change_backend_or_create_worktrees(self) -> None:
        for policy in (None, "worktrees", "primary", "legacy-value"):
            with self.subTest(policy=policy):
                branch_only = self.repo.root / ".ai-playbook/reviews/branch-only.md"
                if os.path.lexists(branch_only):
                    branch_only.unlink()
                if self.repo.git("show-ref", "--verify", "--quiet", "refs/heads/docs", check=False).returncode == 0:
                    self.repo.git("update-ref", "-d", "refs/heads/docs")
                old = self.repo.seed_docs([
                    (".ai-playbook/reviews/branch-only.md", b"review\n", "2026-04-20T00:00:00Z", None),
                    ("docs/tmp/pruned.md", b"scratch\n", "2026-04-20T00:00:00Z", None),
                ])
                local = self.repo.local_file(".ai-playbook/metrics/local.json", b"{}\n")
                head_before = self.repo.git("rev-parse", "HEAD").stdout.strip()
                index = self.repo.root / ".git" / "index"
                index_before = index.read_bytes()
                worktrees_before = self.repo.git("worktree", "list", "--porcelain").stdout
                trace = self.repo.root / f"{policy or 'worktree'}-cas-trace.log"
                result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)}, policy=policy)
                self.assert_ok(result)
                self.assertNotIn("sync mode", result.stdout + result.stderr)
                self.assertEqual(self.repo.git("worktree", "list", "--porcelain").stdout, worktrees_before)
                self.assertIn("ref-update-cas", trace.read_text(encoding="utf-8"))
                self.assertIn(".ai-playbook/reviews/branch-only.md", self.repo.docs_paths())
                self.assertEqual(self.repo.git("merge-base", "--is-ancestor", old, "refs/heads/docs", check=False).returncode, 0)
                self.assertEqual(self.repo.git("rev-parse", "HEAD").stdout.strip(), head_before)
                self.assertEqual(index.read_bytes(), index_before)
                self.assertEqual(local.read_bytes(), b"{}\n")

    def test_changed_tree_cas_refuses_competing_tip_at_publication(self) -> None:
        path = ".ai-playbook/reviews/current.md"
        baseline = self.repo.seed_docs([(path, b"old\n", NOW, None)])
        namespace = load_runner_namespace()
        old_tree = self.repo.git("rev-parse", f"{baseline}^{{tree}}").stdout.strip()
        index = self.repo.root / ".test-index-replacement"
        env = {**self.repo.git_env, "GIT_INDEX_FILE": str(index)}
        try:
            self.repo.git("read-tree", baseline, env=env)
            blob = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"], cwd=self.repo.root, env=env,
                input=b"replacement\n", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            ).stdout.decode().strip()
            self.repo.git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
            tree = self.repo.git("write-tree", env=env).stdout.strip()
        finally:
            index.unlink(missing_ok=True)
        self.assertNotEqual(tree, old_tree)
        original_update = namespace["update_docs_ref"]

        def compete_then_update(repo, new_tip, expected):
            self.repo.add_docs_commit(".ai-playbook/metrics/competitor.json", b"peer\n", NOW)
            return original_update(repo, new_tip, expected)

        namespace["update_docs_ref"] = compete_then_update
        with self.assertRaisesRegex(namespace["SyncError"], "CAS refusal updating refs/heads/docs"):
            namespace["apply_tree"](self.repo.root, tree, baseline)
        current = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        self.assertNotEqual(current, baseline)
        self.assertEqual(self.repo.git("merge-base", "--is-ancestor", baseline, current, check=False).returncode, 0)
        self.assertEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), current)

    def test_noop_update_uses_cas_and_refuses_a_competing_tip(self) -> None:
        self.repo.seed_docs([(".ai-playbook/reviews/current.md", b"current review\n", NOW, None)])
        self.repo.local_file(".ai-playbook/reviews/current.md", b"current review\n", NOW)
        namespace = load_runner_namespace()
        sync_error = namespace["SyncError"]
        original_git = namespace["git"]
        baseline = self.repo.git("rev-parse", "refs/heads/docs").stdout.strip()
        tree = original_git(["rev-parse", f"{baseline}^{{tree}}"], cwd=self.repo.root).stdout.decode().strip()

        for trial in range(1):
            with self.subTest(trial=trial):
                self.repo.git("update-ref", "refs/heads/docs", baseline)
                moved = False

                def move_after_tree_read(args, *, cwd, env=None, check=True, input_data=None):
                    nonlocal moved
                    result = original_git(args, cwd=cwd, env=env, check=check, input_data=input_data)
                    if not moved and args[:1] == ["rev-parse"] and args[1].endswith("^{tree}"):
                        moved = True
                        self.repo.add_docs_commit(".ai-playbook/metrics/competing.json", b"peer\n", NOW)
                    return result

                namespace["git"] = move_after_tree_read
                with self.assertRaisesRegex(sync_error, "CAS refusal updating refs/heads/docs"):
                    namespace["apply_tree"](self.repo.root, tree, baseline)
                self.assertNotEqual(self.repo.git("rev-parse", "refs/heads/docs").stdout.strip(), baseline)
        namespace["git"] = original_git

    def test_no_follow_read_rejects_file_replaced_after_validation(self) -> None:
        outside = self.repo.root.parent / "outside.txt"
        outside.write_bytes(b"private\n")
        candidate = self.repo.local_file(".ai-playbook/reviews/race.md", b"safe\n")
        expected = candidate.lstat()
        candidate.unlink()
        candidate.symlink_to(outside)
        namespace = load_runner_namespace()
        root = namespace["ArchiveRoot"]("reviews", ".ai-playbook/reviews", self.repo.root / ".ai-playbook/reviews")
        with self.assertRaisesRegex(OSError, "Not a directory|Too many levels|changed after validation"):
            namespace["read_regular_candidate"](self.repo.root, root, candidate, expected)

    def test_restore_refuses_a_symlinked_parent_without_writing_outside(self) -> None:
        outside = self.repo.root.parent / "outside-restore"
        outside.mkdir()
        nested = self.repo.root / ".ai-playbook/reviews/nested"
        nested.mkdir(parents=True)
        nested.rmdir()
        nested.symlink_to(outside, target_is_directory=True)
        namespace = load_runner_namespace()
        path = ".ai-playbook/reviews/nested/branch-only.md"
        roots = [namespace["ArchiveRoot"]("reviews", ".ai-playbook/reviews", self.repo.root / ".ai-playbook/reviews")]
        with self.assertRaisesRegex(namespace["SyncError"], "cannot restore recent docs-branch archive"):
            namespace["restore_files"](self.repo.root, roots, [path], {path: ("100644", b"must stay inside\n")})
        self.assertFalse((outside / "branch-only.md").exists())

    def test_restore_refuses_parent_swapped_to_symlink_without_writing_outside(self) -> None:
        outside = self.repo.root.parent / "outside-restore-race"
        outside.mkdir()
        nested = self.repo.root / ".ai-playbook/reviews/nested"
        nested.mkdir(parents=True)
        namespace = load_runner_namespace()
        original_open_directory = namespace["open_repo_directory"]
        path = ".ai-playbook/reviews/nested/branch-only.md"

        def swap_parent_then_open(repo, parts, *, create):
            if parts == (".ai-playbook", "reviews", "nested"):
                nested.rmdir()
                nested.symlink_to(outside, target_is_directory=True)
            return original_open_directory(repo, parts, create=create)

        namespace["open_repo_directory"] = swap_parent_then_open
        roots = [namespace["ArchiveRoot"]("reviews", ".ai-playbook/reviews", self.repo.root / ".ai-playbook/reviews")]
        with self.assertRaisesRegex(namespace["SyncError"], "cannot restore recent docs-branch archive"):
            namespace["restore_files"](self.repo.root, roots, [path], {path: ("100644", b"must stay inside\n")})
        self.assertFalse((outside / "branch-only.md").exists())

    def test_worktree_policy_is_ignored_and_sync_does_not_report_mode(self) -> None:
        self.repo.local_file(".ai-playbook/reviews/new.md", b"review\n")
        for policy in (None, "worktrees", "primary", "legacy-value"):
            with self.subTest(policy=policy):
                if policy is not None:
                    self.repo.write_facts(policy=policy)
                trace = self.repo.root / f"policy-{policy or 'absent'}.log"
                worktrees_before = self.repo.git("worktree", "list", "--porcelain").stdout
                result = self.repo.run(extra_env={"DOCS_SYNC_TRACE_FILE": str(trace)})
                self.assert_ok(result)
                self.assertNotIn("sync mode", result.stdout + result.stderr)
                self.assertNotIn("temporary detached worktree", result.stdout + result.stderr)
                self.assertEqual(self.repo.git("worktree", "list", "--porcelain").stdout, worktrees_before)
                self.assertIn("landed", result.stdout)
                self.assertIn("ref-update-cas", trace.read_text(encoding="utf-8"))
                self.repo.git("update-ref", "-d", "refs/heads/docs")

    def test_skill_contract_excludes_tmp_and_keeps_done_deferral_availability_gate(self) -> None:
        docs_skill = (REPO_TOP / "agents/skills/docs-branch/SKILL.md").read_text(encoding="utf-8")
        # Re-aimed 2026-10-11 (the done target-state flip): the done skill is
        # one collapsed SKILL.md; the sync-facing contract rows and the
        # docs-tmp-sweep Integration Point live there, and the
        # merge-wait-acquire absence holds across the whole done corpus.
        done_skill = (REPO_TOP / "agents/skills/done/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("It excludes `docs/tmp/`", docs_skill)
        self.assertIn("does not remove, sweep, or rewrite local `docs/tmp/` files", docs_skill)
        self.assertIn("separate `docs-tmp-sweep` gate", docs_skill)
        self.assertIn("`docs-tmp-sweep` remains the separate local cleanup gate", done_skill)
        self.assertIn("Explicit sync deferral (availability-checked)", done_skill)
        self.assertIn("owned-review claims verified present under the primary reviews home", done_skill)
        self.assertIn("the deferral never overrides a missing deliverable", done_skill)
        # The runner-owned span contract: the done skill names the runner-held
        # merge-lock spans and carries no skill-side merge-acquire block.
        self.assertIn("Runner-owned merge-lock spans", done_skill)
        self.assertNotIn("merge-wait-acquire", done_skill)


if __name__ == "__main__":
    unittest.main()
