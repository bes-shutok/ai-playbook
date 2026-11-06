#!/usr/bin/env python3
"""Tests for the worktree closeout migration tool (worktree_closeout_migrate.py)."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
from pathlib import Path

# Sibling-module import bootstrap (the repo-wide test idiom, e.g.
# test_code_delta_classifier.py): the plan's validation command runs this
# suite as `python3 -m unittest scripts.test_worktree_closeout_migrate`,
# a namespace-package import that does not put this directory on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import review_plan_identity

SCRIPT_PATH = Path(__file__).resolve().parent / "worktree_closeout_migrate.py"
DONE_LOCK_SCRIPT_PATH = SCRIPT_PATH.parent / "done-lock.sh"

# The lock env vars a fixture must control (the SweepTest inventory) so no
# fixture reads or writes the host lock home.
LOCK_ENV_VARS = (
    "DONE_LOCK_DIR",
    "DONE_LOCK_TOKEN",
    "DONE_LOCK_ROOT",
    "DONE_LOCK_SCRIPT",
    "MERGE_LOCK_ROOT",
    "MERGE_LOCK_DIR",
    "MERGE_LOCK_TOKEN",
    "MERGE_LOCK_HOLDER_PID",
)


# The deterministic locale/timezone a git fixture pins (plan
# 2026-10-19-gate-removal-closeout-accounting Task 2): commit dates and
# message rendering never depend on the host locale or clock zone.
FIXTURE_LOCALE_ENV = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"}


def _hermetic_git_env(root: Path, **extra: str) -> dict[str, str]:
    """Git-fixture hermeticity (plan 2026-10-19-gate-removal-closeout-
    accounting Task 2): every inherited GIT_* variable is cleared, HOME
    moves to a fixture-local directory (no host git config leaks in), and
    the locale/timezone are deterministic. Every fixture passes the result
    to its git subprocesses and to the CLI subprocesses it launches."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    home = Path(root) / "fixture-home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    # Guideline #28's gate: null both non-GIT_* config sources so the
    # XDG and system gitconfigs cannot leak into fixture git calls.
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    # core.attributesFile / core.excludesFile default into
    # $XDG_CONFIG_HOME/git/ too; the devnull pins cover only the two
    # config files, so the XDG root itself goes (git falls back to
    # $HOME/.config/git/, inside the fixture-local home).
    env.pop("XDG_CONFIG_HOME", None)
    env.update(FIXTURE_LOCALE_ENV)
    env.update(extra)
    return env


def _hermetic_lock_env(root: Path, **extra: str) -> dict[str, str]:
    """Fixture hermeticity (plan 2026-10-10-done-closeout-lock-span Task 1):
    pin the merge-lock root and poll interval into the fixture tmp tree and
    the done-lock script at the repo-local copy, so a fixture's lock activity
    never touches the host lock home. The git-side hygiene rides the same
    env: inherited GIT_* variables are cleared, HOME is fixture-local, and
    the locale/timezone are deterministic, because every CLI subprocess the
    tests launch inherits this env (and any git it spawns inherits from it)."""
    env = _hermetic_git_env(root)
    for var in LOCK_ENV_VARS:
        env.pop(var, None)
    env.update(
        {
            "DONE_LOCK_SCRIPT": str(DONE_LOCK_SCRIPT_PATH),
            "MERGE_LOCK_ROOT": str(Path(root) / "merge-locks"),
            "MERGE_LOCK_POLL_SECS": "1",
        }
    )
    env.update(extra)
    return env

# Collection-time module-load pin: the tool module must exist for this test
# module to even collect, so a missing implementation fails at collection.
_spec = importlib.util.spec_from_file_location("worktree_closeout_migrate_under_test", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = MODULE
_spec.loader.exec_module(MODULE)


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _run_cli(*args: str, cwd: Path) -> tuple[int, str, str]:
    if args and args[0] == "capture":
        # Capture resolves the dirs family from the facts block (single
        # source, fail-closed): provision the standard four keys when the
        # fixture repo has none, the same production ordering.
        facts_dir = Path(cwd) / ".ai-playbook"
        if not (facts_dir / "facts.md").is_file():
            facts_dir.mkdir(parents=True, exist_ok=True)
            (facts_dir / "facts.md").write_text(
                "```toml\n"
                'reviews_dir = ".ai-playbook/reviews/"\n'
                'tmp_dir = "docs/tmp/"\n'
                'metrics_dir = ".ai-playbook/metrics/"\n'
                'review_certs_dir = ".ai-playbook/review-certs/"\n'
                "```\n",
                encoding="utf-8",
            )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=_hermetic_lock_env(cwd),
    )
    return proc.returncode, proc.stdout, proc.stderr


def _capture_baseline(source: Path, out: Path) -> None:
    code, _stdout, stderr = _run_cli("capture", "--out", str(out), cwd=source)
    if code != 0:
        raise AssertionError(f"capture failed: {stderr}")


def _migrate(source: Path, target: Path, baseline: Path, manifest: Path, suffix: str = "1") -> int:
    return MODULE.main(
        [
            "migrate",
            "--baseline",
            str(baseline),
            "--source",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--suffix",
            suffix,
        ]
    )


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _receipts_token(items: list[dict]) -> str:
    """Producer-side mirror-receipt token (plan
    2026-10-24-closeout-migration-same-run-mirror-replace): compact JSON
    with every table pipe escaped as the six-character \\u007c sequence so
    one manifest row can carry the array unsplit; the consumer decodes it
    with a plain JSON parse."""
    text = json.dumps(items, separators=(",", ":"), ensure_ascii=True)
    return text.replace("|", "\\u007c")


def _file_receipt(path: str, digest: str) -> dict:
    return {"path": path, "status": "verified", "type": "file", "sha256": digest}


def _symlink_receipt(path: str, link_target: str) -> dict:
    return {"path": path, "status": "verified", "type": "symlink", "target": link_target}


def _status_receipt(path: str, status: str) -> dict:
    return {"path": path, "status": status}


def _write_session_manifest(
    path: Path,
    rows: list[str],
    *,
    run_worktree: str,
    run_session_id: str = "sess-mirror-fixture-1",
    plan_path: str = "docs/history/plans/2026-10-24-mirror-fixture.md",
) -> None:
    """The production session-manifest shape (identity block plus one
    task_boundary row per entry), pinned beside the baseline the way Step
    0.4 writes it."""
    lines = [
        "# Execute-plan session: mirror-fixture",
        "",
        "workflow_state: active",
        "updated: 2026-10-24T00:00:00Z",
        f"run_session_id: {run_session_id}",
        "session_id: sess-current-1",
        f"plan_path: {plan_path}",
        "session_start_commit: abc1234def",
        "canonical_root: /tmp/primary-checkout",
        f"run_worktree: {run_worktree}",
        "run_branch: mirror-fixture",
        "run_base: main c06633961",
        "",
        "| Step | Log path | Status |",
        "|------|----------|--------|",
        *rows,
    ]
    _write(path, ("\n".join(lines) + "\n").encode("utf-8"))


class WorktreeCloseoutTest(unittest.TestCase):
    def setUp(self) -> None:
        # In-process migrate runs resolve the lock script and merge-lock root
        # from this process's environment: pin them hermetically for the whole
        # class so no fixture reads or writes the host lock home.
        lock_root = Path(tempfile.mkdtemp(prefix="wcm-lock-root-"))
        self.addCleanup(shutil.rmtree, lock_root, ignore_errors=True)
        pins = _hermetic_lock_env(lock_root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_capture_records_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / ".ai-playbook/reviews/notes.md", b"review notes\n")
            _write(root / "docs/tmp/scratch.md", b"scratch pad\n")
            _write(root / ".ai-playbook/review-certs/round-seal.md", b"seal entry\n")
            baseline = root / "baseline.json"
            code, stdout, stderr = _run_cli("capture", "--out", str(baseline), cwd=root)
            self.assertEqual(code, 0, stderr)
            self.assertIn(
                f"(checkout: {root.resolve()})",
                stdout,
                "the capture output did not name the checkout it captured in",
            )
            data = json.loads(baseline.read_text(encoding="utf-8"))
            self.assertEqual(
                data["dirs"],
                [".ai-playbook/reviews", "docs/tmp", ".ai-playbook/metrics", ".ai-playbook/review-certs"],
            )
            files = data["files"]
            self.assertIn(".ai-playbook/reviews/notes.md", files)
            self.assertIn("docs/tmp/scratch.md", files)
            self.assertIn(".ai-playbook/review-certs/round-seal.md", files)
            self.assertEqual(
                files[".ai-playbook/reviews/notes.md"],
                hashlib.sha256(b"review notes\n").hexdigest(),
            )
            self.assertEqual(
                files["docs/tmp/scratch.md"],
                hashlib.sha256(b"scratch pad\n").hexdigest(),
            )
            # The capture time (entry closeout-migrate-zero-delta-silence):
            # every baseline carries an ISO-8601 UTC captured_at.
            self.assertIn("captured_at", data)
            captured = datetime.fromisoformat(data["captured_at"])
            self.assertIsNotNone(captured.utcoffset())
            self.assertEqual(captured.utcoffset(), timedelta(0))

    def test_capture_records_captured_at_before_the_source_walk(self):
        """[class: REPOSITORY_TEST] capture records captured_at before it
        walks the configured source paths: the recorded value is ISO-8601
        UTC and does not postdate the walk itself, observed through the
        walk seam (entry closeout-migrate-zero-delta-silence, Task 1
        capture-time ordering). The marking walk crosses a whole-second
        boundary, so a captured_at recorded after the walk (the
        second-truncation mutation) truncates to a strictly later second
        than the mark and fails, while the correct order can only render
        equal-or-earlier and always passes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / ".ai-playbook/reviews/notes.md", b"review notes\n")
            walk_marks: list[str] = []
            original_walk = MODULE._iter_configured_files

            def marking_walk(walk_root, walk_dirs):
                walk_marks.append(datetime.now(timezone.utc).isoformat(timespec="seconds"))
                # Sleep past the next whole-second boundary inside the walk:
                # without this, a capture that recorded captured_at after
                # the walk still truncated into the mark's own second
                # (same-second runs passed), so the assertion did not
                # discriminate the ordering at whole-second granularity.
                time.sleep(1.1)
                return original_walk(walk_root, walk_dirs)

            baseline = root / "baseline.json"
            previous_cwd = os.getcwd()
            os.chdir(root)
            try:
                MODULE._iter_configured_files = marking_walk
                try:
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        code = MODULE.main(
                            [
                                "capture",
                                "--out",
                                str(baseline),
                                "--dirs",
                                ".ai-playbook/reviews",
                            ]
                        )
                finally:
                    MODULE._iter_configured_files = original_walk
            finally:
                os.chdir(previous_cwd)
            self.assertEqual(code, 0, stderr.getvalue())
            data = json.loads(baseline.read_text(encoding="utf-8"))
            self.assertIn(".ai-playbook/reviews/notes.md", data["files"])
            captured = datetime.fromisoformat(data["captured_at"])
            self.assertIsNotNone(captured.utcoffset())
            self.assertEqual(captured.utcoffset(), timedelta(0))
            self.assertTrue(walk_marks)
            for mark in walk_marks:
                self.assertLessEqual(captured, datetime.fromisoformat(mark))

    def test_capture_facts_unresolvable_fails_loud(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        # Arm 1 (no facts file) runs the CLI directly: the _run_cli helper
        # provisions standard facts for capture, which would mask the
        # missing-facts arm this test exists to pin.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "capture", "--out",
             str(root / "baseline.json")],
            capture_output=True, text=True, cwd=str(root),
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("cannot resolve the capture dirs", proc.stderr)
        facts = root / ".ai-playbook" / "facts.md"
        facts.parent.mkdir(parents=True, exist_ok=True)
        facts.write_text(
            "```toml\n"
            'reviews_dir = ""\n'
            'tmp_dir = "docs/tmp/"\n'
            'metrics_dir = ".ai-playbook/metrics/"\n'
            'review_certs_dir = ".ai-playbook/review-certs/"\n'
            "```\n",
            encoding="utf-8",
        )
        code, _out, err = _run_cli(
            "capture", "--out", str(root / "baseline.json"), cwd=root
        )
        self.assertEqual(code, 2)
        self.assertIn("cannot resolve the capture dirs", err)

    def test_migrate_baseline_without_dirs_fails_loud(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        source = root / "source"
        target = root / "target"
        source.mkdir()
        target.mkdir()
        baseline = root / "baseline.json"
        baseline.write_text(json.dumps({"files": {}}), encoding="utf-8")
        code = MODULE.main(
            [
                "migrate",
                "--baseline", str(baseline),
                "--source", str(source),
                "--target", str(target),
                "--manifest", str(root / "manifest.json"),
            ]
        )
        self.assertEqual(code, 2)

    def test_capture_skips_dangling_symlink_with_named_warn(self):
        # The dangling symlink is unreadable (its open raises), so it flows
        # through the same named skip-and-warn as any OSError from the
        # per-file digest read: exit 0, a stderr warn naming the unreadable
        # path, and a "skipped" entry in the baseline JSON, while the
        # regular file beside it still hashes normally.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / ".ai-playbook/reviews/real.md", b"real review notes\n")
            os.symlink("missing-target.md", root / ".ai-playbook/reviews/dangling.md")
            baseline = root / "baseline.json"
            code, _stdout, stderr = _run_cli("capture", "--out", str(baseline), cwd=root)
            self.assertEqual(code, 0, stderr)
            self.assertIn("skipping unreadable path", stderr)
            self.assertIn(".ai-playbook/reviews/dangling.md", stderr)
            data = json.loads(baseline.read_text(encoding="utf-8"))
            self.assertIn(".ai-playbook/reviews/real.md", data["files"])
            self.assertEqual(
                data["files"][".ai-playbook/reviews/real.md"],
                hashlib.sha256(b"real review notes\n").hexdigest(),
            )
            skipped = {entry["path"]: entry for entry in data["skipped"]}
            self.assertIn(".ai-playbook/reviews/dangling.md", skipped)

    def test_migrate_copies_new_and_modified_with_checksum_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/keep.md", b"unchanged\n")
            _write(source / ".ai-playbook/reviews/edit.md", b"old edit\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/edit.md", b"new edit\n")
            _write(source / ".ai-playbook/reviews/fresh.md", b"fresh file\n")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            self.assertEqual((target / ".ai-playbook/reviews/edit.md").read_bytes(), b"new edit\n")
            self.assertEqual((target / ".ai-playbook/reviews/fresh.md").read_bytes(), b"fresh file\n")
            self.assertFalse((target / ".ai-playbook/reviews/keep.md").exists())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            migrated = {entry["source"] for entry in data["migrated"]}
            self.assertEqual(migrated, {".ai-playbook/reviews/edit.md", ".ai-playbook/reviews/fresh.md"})

    def test_migrate_skips_identical_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/same.md", b"v1\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/same.md", b"v2\n")
            _write(target / ".ai-playbook/reviews/same.md", b"v2\n")
            os.utime(target / ".ai-playbook/reviews/same.md", (1000, 1000))
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            stat = os.stat(target / ".ai-playbook/reviews/same.md")
            self.assertEqual(stat.st_mtime, 1000, "identical target was rewritten")
            self.assertFalse(
                any(path.name.startswith("same.wt-") for path in (target / ".ai-playbook/reviews").iterdir())
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            skipped = {entry["source"] for entry in data.get("skipped", [])}
            self.assertIn(".ai-playbook/reviews/same.md", skipped)

    def test_migrate_renames_on_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/collide.md", b"incoming content\n")
            _write(target / ".ai-playbook/reviews/collide.md", b"existing different\n")
            _write(target / ".ai-playbook/reviews/collide.wt-9.md", b"prior run copy\n")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest, suffix="9")
            self.assertEqual(code, 0)
            self.assertEqual(
                (target / ".ai-playbook/reviews/collide.md").read_bytes(),
                b"existing different\n",
            )
            self.assertEqual(
                (target / ".ai-playbook/reviews/collide.wt-9.md").read_bytes(),
                b"prior run copy\n",
                "pre-existing .wt- copy was overwritten",
            )
            self.assertEqual(
                (target / ".ai-playbook/reviews/collide.wt-9-2.md").read_bytes(),
                b"incoming content\n",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            renamed = {entry["source"] for entry in data.get("renamed", [])}
            self.assertIn(".ai-playbook/reviews/collide.md", renamed)
            renamed_entry = next(
                entry
                for entry in data["renamed"]
                if entry["source"] == ".ai-playbook/reviews/collide.md"
            )
            self.assertTrue(renamed_entry["destination"].endswith("collide.wt-9-2.md"))

    def test_migrate_collision_rename_prints_pair_loudness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/collide.md", b"incoming content\n")
            _write(target / ".ai-playbook/reviews/collide.md", b"existing different\n")
            _write(source / ".ai-playbook/reviews/same.md", b"shared bytes\n")
            _write(target / ".ai-playbook/reviews/same.md", b"shared bytes\n")
            manifest = root / "manifest.json"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = _migrate(source, target, baseline, manifest, suffix="9")
            self.assertEqual(code, 0)
            out = buf.getvalue()
            src_short = hashlib.sha256(b"incoming content\n").hexdigest()[:12]
            dst_short = hashlib.sha256(b"existing different\n").hexdigest()[:12]
            collision_lines = [
                line for line in out.splitlines() if line.startswith("COLLISION:")
            ]
            self.assertEqual(len(collision_lines), 1, out)
            line = collision_lines[0]
            self.assertIn(".ai-playbook/reviews/collide.md", line)
            self.assertIn("collide.wt-9.md", line)
            self.assertIn(src_short, line)
            self.assertIn(dst_short, line)
            self.assertLess(line.index("incoming"), line.index("existing"))
            self.assertLess(line.index(src_short), line.index(dst_short))
            renamed = json.loads(manifest.read_text(encoding="utf-8")).get("renamed", [])
            self.assertEqual(
                [entry["source"] for entry in renamed],
                [".ai-playbook/reviews/collide.md"],
            )

    def test_migrate_collision_dangling_destination_symlink_renames_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/dangle.md", b"incoming content\n")
            reviews = target / ".ai-playbook/reviews"
            reviews.mkdir(parents=True)
            (reviews / "dangle.md").symlink_to(root / "missing-target.md")
            manifest = root / "manifest.json"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = _migrate(source, target, baseline, manifest, suffix="9")
            self.assertEqual(code, 0)
            self.assertTrue((reviews / "dangle.wt-9.md").is_file())
            collision_lines = [
                line
                for line in buf.getvalue().splitlines()
                if line.startswith("COLLISION:")
            ]
            self.assertEqual(len(collision_lines), 1)
            self.assertIn("unreadable", collision_lines[0])

    def test_migrate_preserves_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/real.md", b"linked content\n")
            os.symlink("real.md", source / ".ai-playbook/reviews/link.md")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            dst_link = target / ".ai-playbook/reviews/link.md"
            self.assertTrue(dst_link.is_symlink(), "symlink was dereferenced into a regular file")
            self.assertEqual(os.readlink(dst_link), "real.md")
            self.assertTrue((target / ".ai-playbook/reviews/real.md").is_file())

    def test_migrate_skips_dangling_symlink_in_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/kept.md", b"kept v1\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/kept.md", b"kept v2\n")
            _write(source / ".ai-playbook/reviews/fresh.md", b"fresh file\n")
            os.symlink("missing-target.md", source / ".ai-playbook/reviews/dangling.md")
            manifest = root / "manifest.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            migrated = {entry["source"] for entry in data["migrated"]}
            self.assertEqual(
                migrated,
                {".ai-playbook/reviews/kept.md", ".ai-playbook/reviews/fresh.md"},
                "dangling symlink was migrated instead of skipped",
            )
            skipped = {entry["source"]: entry for entry in data["skipped"]}
            self.assertIn(".ai-playbook/reviews/dangling.md", skipped)
            self.assertIn(
                "dangling symlink",
                skipped[".ai-playbook/reviews/dangling.md"]["reason"],
            )
            err = stderr.getvalue()
            self.assertNotIn("Traceback", err)
            self.assertIn("WARN: skipping dangling symlink:", err)
            self.assertIn("dangling.md", err)
            self.assertFalse((target / ".ai-playbook/reviews/dangling.md").exists())
            self.assertFalse((target / ".ai-playbook/reviews/dangling.md").is_symlink())

    def test_unreadable_regular_file_capture_skips_and_migrate_fails(self):
        # Task 6 split the posture per command. Capture contains EVERY
        # OSError from the per-file digest read (a permission-denied regular
        # file exactly like a dangling symlink): named warn, "skipped"
        # entry, exit 0, baseline still written. Migrate keeps no such
        # containment on its copy path: the unreadable regular file aborts
        # the run loudly, is never misrecorded as a skip, and the manifest
        # is still made durable by the finally block (interrupted marker).
        # Seam patching (never chmod), in-process via MODULE.main, per r2 F5.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/readable.md", b"readable v1\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/readable.md", b"readable v2\n")
            _write(source / ".ai-playbook/reviews/unreadable.md", b"secret\n")
            manifest = root / "manifest.json"
            original_sha = MODULE._sha256

            def failing_sha(path):
                if Path(path).name == "unreadable.md":
                    raise PermissionError(f"simulated unreadable regular file: {path}")
                return original_sha(path)

            MODULE._sha256 = failing_sha
            try:
                # capture: every OSError from the digest read is contained
                # as a named skip-and-warn; the exit stays 0.
                previous_cwd = os.getcwd()
                os.chdir(source)
                try:
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        code = MODULE.main(
                            [
                                "capture",
                                "--out",
                                str(root / "baseline2.json"),
                                "--dirs",
                                ".ai-playbook/reviews",
                            ]
                        )
                finally:
                    os.chdir(previous_cwd)
                self.assertEqual(code, 0)
                err = stderr.getvalue()
                self.assertIn("skipping unreadable path", err)
                self.assertIn(".ai-playbook/reviews/unreadable.md", err)
                data = json.loads((root / "baseline2.json").read_text(encoding="utf-8"))
                self.assertEqual(
                    data["files"][".ai-playbook/reviews/readable.md"],
                    hashlib.sha256(b"readable v2\n").hexdigest(),
                )
                skipped = {entry["path"]: entry for entry in data["skipped"]}
                self.assertIn(".ai-playbook/reviews/unreadable.md", skipped)
                self.assertIn(
                    "PermissionError",
                    skipped[".ai-playbook/reviews/unreadable.md"]["reason"],
                )
                # migrate: same OSError is NOT contained on the copy path;
                # it propagates loudly and unchanged.
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(PermissionError):
                        _migrate(source, target, baseline, manifest)
            finally:
                MODULE._sha256 = original_sha
            # Unconditional (r1 F12): manifest durability writes the manifest
            # in a finally block even when the walk aborts, so the file must
            # exist here; the guard this replaces could hide a durability
            # regression by skipping the assertion.
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertIs(data["interrupted"], True)
            self.assertNotIn(
                "unreadable.md",
                json.dumps(data.get("skipped", [])),
                "unreadable regular file was misrecorded as a skip on the migrate path",
            )

    def test_manifest_written_on_midloop_crash(self):
        # Manifest durability on the crash-injection seam: _copy_file patched
        # to raise OSError for exactly one path (distinct from the
        # verify-error arm, which tampers _verify_copy instead). The raised
        # exception must propagate AND the manifest must already contain the
        # first file's migrated entry plus an "interrupted": true marker, so
        # no copied file is orphaned from the audit record.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/first.md", b"first v1\n")
            _write(source / ".ai-playbook/reviews/second.md", b"second v1\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/first.md", b"first v2\n")
            _write(source / ".ai-playbook/reviews/second.md", b"second v2\n")
            manifest = root / "manifest.json"
            original_copy = MODULE._copy_file

            def crashing_copy(src, dst):
                if Path(src).name == "second.md":
                    raise OSError(f"simulated copy crash: {src}")
                return original_copy(src, dst)

            MODULE._copy_file = crashing_copy
            try:
                with self.assertRaises(OSError):
                    _migrate(source, target, baseline, manifest)
            finally:
                MODULE._copy_file = original_copy
            data = json.loads(manifest.read_text(encoding="utf-8"))
            migrated = {entry["source"] for entry in data["migrated"]}
            self.assertEqual(migrated, {".ai-playbook/reviews/first.md"})
            first_entry = next(
                entry for entry in data["migrated"] if entry["source"] == ".ai-playbook/reviews/first.md"
            )
            self.assertTrue(first_entry["verified"])
            self.assertEqual((target / ".ai-playbook/reviews/first.md").read_bytes(), b"first v2\n")
            self.assertIs(data["interrupted"], True)
            # The incomplete entry keeps naming the error for the audit record.
            self.assertIn("simulated copy crash", data["incomplete"][0]["error"])

    def test_migrate_missing_baseline_fails_loud(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/only.md", b"content\n")
            missing = root / "does-not-exist.json"
            manifest = root / "manifest.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, missing, manifest)
            self.assertNotEqual(code, 0)
            self.assertIn(str(missing), stderr.getvalue())
            self.assertIn(
                "remedy: check the primary checkout's session dir",
                stderr.getvalue(),
                "the refusal did not carry the primary-checkout remedy clause",
            )
            self.assertIn(
                "a recapture here is a late baseline",
                stderr.getvalue(),
                "the refusal did not name the late-baseline deviation",
            )
            self.assertFalse((target / ".ai-playbook/reviews/only.md").exists())

    def test_setup_capture_production_shape_then_migrate_accepts(self):
        """The Phase 0 closeout-evidence establishment duty's production
        shape (plan-authoring-done-closeout): capture with --out inside the
        facts-resolved tmp run dir from the worktree root, then migrate
        accepts that baseline. Capture-then-migrate acceptance is already
        witnessed by test_migrate_copies_new_and_modified_with_checksum_verify;
        this fixture pins the production run-dir shape of the baseline path."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/certified.md", b"certified\n")
            run_dir = source / "docs/tmp/execute-plan/2026-10-10-plan-authoring-done-closeout"
            baseline = run_dir / "closeout-baseline.json"
            code, _stdout, stderr = _run_cli("capture", "--out", str(baseline), cwd=source)
            self.assertEqual(code, 0, f"production-shape capture failed: {stderr}")
            self.assertTrue(baseline.is_file(), "capture wrote no baseline in the run dir")
            _write(source / ".ai-playbook/reviews/fresh.md", b"fresh\n")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0, "migrate refused the production-shape setup baseline")
            self.assertTrue((target / ".ai-playbook/reviews/fresh.md").is_file())

    def test_skip_sibling_never_substitutes_for_baseline(self):
        """A written closeout-baseline-skip.json (the sanctioned Phase 0
        failure-arm sibling, plan-authoring-done-closeout) never substitutes
        for a baseline at the helper: the refusal stands (the helper reads
        the sibling as a dirs-less baseline and refuses with the
        baseline-lacks-dirs error; the implicit-empty-baseline message for a
        missing baseline file stays covered by
        test_migrate_missing_baseline_fails_loud, the both-absent refusal
        with nothing copied)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/only.md", b"content\n")
            skip = source / "docs/tmp/execute-plan/slug/closeout-baseline-skip.json"
            _write(skip, json.dumps({"skip": True, "reason": "capture failed"}).encode("utf-8"))
            manifest = root / "manifest.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, skip, manifest)
            self.assertNotEqual(
                code, 0, "migrate accepted the skip sibling as a baseline"
            )
            self.assertIn(
                "baseline lacks dirs",
                stderr.getvalue(),
                "the refusal did not name the dirs-less baseline error",
            )
            self.assertFalse((target / ".ai-playbook/reviews/only.md").exists())

    def test_migrate_markdown_manifest_fails_loud_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/keep.md", b"unchanged\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/fresh.md", b"fresh file\n")
            manifest = root / "manifest.json"
            manifest.write_text("# session manifest\n", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, manifest)
            self.assertNotEqual(code, 0)
            self.assertIn(str(manifest), stderr.getvalue())
            self.assertFalse(
                (target / ".ai-playbook/reviews/fresh.md").exists(),
                "migration copied files despite an invalid manifest",
            )
            self.assertEqual(
                manifest.read_text(encoding="utf-8"),
                "# session manifest\n",
                "invalid manifest was rewritten instead of refused",
            )

    def test_migrate_fails_without_moving_on_verify_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / ".ai-playbook/reviews/untouched.md", b"untouched\n")
            _write(source / ".ai-playbook/reviews/victim.md", b"original bytes\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/victim.md", b"modified bytes\n")
            manifest = root / "manifest.json"
            original_verify = MODULE._verify_copy

            def refused_verify(src, dst):
                return False

            MODULE._verify_copy = refused_verify
            try:
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = _migrate(source, target, baseline, manifest)
            finally:
                MODULE._verify_copy = original_verify
            self.assertNotEqual(code, 0)
            self.assertIn("verification failed", stderr.getvalue())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            failed = {entry["source"]: entry for entry in data["failed"]}
            self.assertIn(".ai-playbook/reviews/victim.md", failed)
            self.assertFalse(failed[".ai-playbook/reviews/victim.md"]["verified"])
            self.assertIn(
                "checksum mismatch after copy",
                failed[".ai-playbook/reviews/victim.md"]["error"],
            )
            self.assertEqual(
                data["migrated"],
                [],
                "a verify-refused file was recorded as migrated",
            )
            # Copy-never-move, asserted against real copy semantics: the copy
            # path is unpatched, so the refused copy still landed on the
            # target while every source file remains in place.
            self.assertEqual(
                (source / ".ai-playbook/reviews/victim.md").read_bytes(),
                b"modified bytes\n",
                "source file was moved instead of copied",
            )
            self.assertTrue((source / ".ai-playbook/reviews/untouched.md").is_file())
            self.assertEqual((target / ".ai-playbook/reviews/victim.md").read_bytes(), b"modified bytes\n")

    def test_migrate_noop_when_source_equals_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            _write(source / ".ai-playbook/reviews/solo.md", b"content\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/solo.md", b"changed content\n")
            manifest = root / "manifest.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, source, baseline, manifest)
            self.assertEqual(code, 0)
            self.assertIn("no-op", stderr.getvalue().lower())
            self.assertEqual((source / ".ai-playbook/reviews/solo.md").read_bytes(), b"changed content\n")
            self.assertFalse(
                any(path.name.startswith("solo.wt-") for path in (source / ".ai-playbook/reviews").iterdir())
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertTrue(data.get("noop"))

    def test_manifest_records_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/one.md", b"one\n")
            _write(source / "docs/tmp/two.md", b"two\n")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            migrated = {entry["source"]: entry for entry in data["migrated"]}
            self.assertEqual(set(migrated), {".ai-playbook/reviews/one.md", "docs/tmp/two.md"})
            for entry in migrated.values():
                self.assertTrue(entry["verified"])
                self.assertEqual(
                    hashlib.sha256(Path(entry["destination"]).read_bytes()).hexdigest(),
                    hashlib.sha256((source / entry["source"]).read_bytes()).hexdigest(),
                )

    def test_migrate_transfers_new_artifacts_across_all_four_capture_roots(self):
        """[class: REPOSITORY_TEST] The Phase 0 capture root set covers the
        reviews, tmp, metrics, and review-certs homes, and the baseline
        migration carries a post-baseline artifact from every one of the
        four roots, each manifest entry verified (plan
        2026-10-18-worktree-closeout-single-start-baseline Task 1)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            new_artifacts = {
                ".ai-playbook/reviews/2026-10-18-four-roots-review-r1.md": b"review\n",
                "docs/tmp/execute-plan/four-roots/task-1.log.md": b"log\n",
                ".ai-playbook/metrics/four-roots-telemetry.json": b"{}\n",
                ".ai-playbook/review-certs/four-roots-seal.md": b"seal\n",
            }
            for rel, data in new_artifacts.items():
                _write(source / rel, data)
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            migrated = {entry["source"]: entry for entry in data["migrated"]}
            self.assertEqual(set(migrated), set(new_artifacts))
            for rel, entry in migrated.items():
                self.assertTrue(entry["verified"])
                self.assertEqual(
                    (target / rel).read_bytes(),
                    new_artifacts[rel],
                )

    def test_zero_delta_report_predates_reading_names_both_timestamps(self):
        """[class: REPOSITORY_TEST] A zero-result migrate whose newest
        configured-dir file predates the baseline capture prints the
        zero-delta report naming both timestamps with the ambiguity wording
        (correctly empty delta vs a baseline that postdates the run edits),
        warning-only with the exit code unchanged (entry
        closeout-migrate-zero-delta-silence, arm 1)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            _write(source / ".ai-playbook/reviews/pre-existing-r1.md", b"old\n")
            # A fixture-set mtime (not the natural now) so the printed
            # newest time is exactly assertable (fix pass 2 UTC rendering).
            old = time.time() - 120
            os.utime(source / ".ai-playbook/reviews/pre-existing-r1.md", (old, old))
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            baseline_bytes = baseline.read_bytes()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            # No auto-recapture: the migrate run leaves the baseline file
            # byte-identical (fix pass 2 baseline-unchanged arm).
            self.assertEqual(baseline.read_bytes(), baseline_bytes)
            text = stderr.getvalue()
            self.assertIn("zero-delta report", text)
            self.assertIn("predates the baseline capture", text)
            self.assertIn("correctly empty delta", text)
            self.assertIn("baseline that postdates the run edits", text)
            # The reported capture time is the recorded captured_at, not the
            # baseline file's mtime.
            captured_at = json.loads(baseline.read_text(encoding="utf-8"))["captured_at"]
            self.assertIn(captured_at, text)
            # The printed newest time is the UTC rendering of the fixture's
            # mtime, not a local-naive one (fix pass 2): it names the exact
            # second the fixture set and never carries microseconds.
            expected_newest = datetime.fromtimestamp(
                old, timezone.utc
            ).isoformat(timespec="seconds")
            self.assertIn(expected_newest, text)
            self.assertIn(".ai-playbook/reviews/pre-existing-r1.md", text)

    def test_zero_delta_report_equal_second_boundary_takes_predates_arm(self):
        """[class: REPOSITORY_TEST] A zero-result migrate whose newest
        configured-dir file mtime shares its whole second with the baseline
        capture instant (the equal-second boundary) takes the predates/
        ambiguity arm, never the postdates warning: both sides compare at
        the whole-second granularity the report prints, so an equal second
        is not evidence of a post-capture touch (entry
        closeout-migrate-zero-delta-silence, Phase 3 boundary pin)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            rel = ".ai-playbook/reviews/boundary-r1.md"
            _write(source / rel, b"boundary\n")
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            captured_at = json.loads(baseline.read_text(encoding="utf-8"))["captured_at"]
            # Pin the newest mtime to exactly the captured_at instant,
            # truncated to the whole second both sides of the comparison
            # use, so the fixture is deterministic rather than racing the
            # capture clock.
            same_second = int(datetime.fromisoformat(captured_at).timestamp())
            os.utime(source / rel, (same_second, same_second))
            baseline_bytes = baseline.read_bytes()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            # No auto-recapture: the migrate run leaves the baseline file
            # byte-identical (fix pass 2 baseline-unchanged arm).
            self.assertEqual(baseline.read_bytes(), baseline_bytes)
            text = stderr.getvalue()
            self.assertIn("WARNING: zero-delta report:", text)
            self.assertIn("predates the baseline capture", text)
            self.assertNotIn("postdates the baseline capture", text)
            self.assertIn(captured_at, text)
            # The printed newest time is the exact shared second, UTC.
            expected_newest = datetime.fromtimestamp(
                same_second, timezone.utc
            ).isoformat(timespec="seconds")
            self.assertIn(expected_newest, text)
            self.assertIn(rel, text)

    def test_zero_delta_report_postdates_reading_flags_touched_without_change(self):
        """[class: REPOSITORY_TEST] A zero-result migrate whose newest
        configured-dir file mtime postdates the baseline capture (a
        content-identical touch) prints the explicit postdates warning and
        still exits 0 with nothing migrated (entry
        closeout-migrate-zero-delta-silence, arm 1, warning-only)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            rel = ".ai-playbook/reviews/touched-r1.md"
            _write(source / rel, b"same\n")
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            future = time.time() + 120
            os.utime(source / rel, (future, future))
            baseline_bytes = baseline.read_bytes()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            # No auto-recapture: the migrate run leaves the baseline file
            # byte-identical (fix pass 2 baseline-unchanged arm).
            self.assertEqual(baseline.read_bytes(), baseline_bytes)
            data = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(data["migrated"], [])
            text = stderr.getvalue()
            self.assertIn("zero-delta report", text)
            self.assertIn("postdates the baseline capture", text)
            captured_at = json.loads(baseline.read_text(encoding="utf-8"))["captured_at"]
            self.assertIn(captured_at, text)
            # The printed newest time is the UTC rendering of the fixture's
            # mtime, not a local-naive one (fix pass 2): it names the exact
            # second the fixture set and never carries microseconds.
            expected_newest = datetime.fromtimestamp(
                future, timezone.utc
            ).isoformat(timespec="seconds")
            self.assertIn(expected_newest, text)
            self.assertIn(rel, text)

    def test_zero_delta_report_legacy_baseline_reports_unknown_capture_time(self):
        """[class: REPOSITORY_TEST] A legacy baseline written before
        captured_at still migrates, exits 0, and the zero-delta report names
        its capture time as unknown without borrowing the baseline file's
        own (later) mtime: no postdates/predates comparison runs (entry
        closeout-migrate-zero-delta-silence, legacy unknown arm)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            rel = ".ai-playbook/reviews/legacy-r1.md"
            _write(source / rel, b"legacy\n")
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            data = json.loads(baseline.read_text(encoding="utf-8"))
            del data["captured_at"]
            baseline.write_text(
                json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            text = stderr.getvalue()
            self.assertIn("zero-delta report", text)
            self.assertIn("capture time unknown", text)
            # The newest source mtime is still named, and the baseline
            # file's later mtime is never borrowed as the capture time, so
            # neither comparison verdict appears.
            self.assertIn(rel, text)
            self.assertNotIn("predates the baseline capture", text)
            self.assertNotIn("postdates the baseline capture", text)

    def test_zero_delta_report_unreadable_source_mtime_reports_none(self):
        """[class: REPOSITORY_TEST] When no source artifact under the
        configured dirs yields a readable mtime (the only entry a dangling
        symlink), the zero-delta report states the none arm and the
        migration still exits 0 (entry closeout-migrate-zero-delta-silence,
        missing-mtime none arm)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            reviews = source / ".ai-playbook/reviews"
            reviews.mkdir(parents=True, exist_ok=True)
            os.symlink("missing-target.md", reviews / "dangling-r1.md")
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            text = stderr.getvalue()
            self.assertIn("zero-delta report", text)
            self.assertIn("no readable files found under the configured dirs", text)
            self.assertNotIn("predates", text)
            self.assertNotIn("postdates", text)

    def test_zero_delta_report_excludes_the_baseline_file_from_newest_mtime(self):
        """[class: REPOSITORY_TEST] When the baseline file sits under a
        configured source dir, the zero-delta report's newest-mtime walk
        excludes it (capture writes the baseline after walking the source
        paths, so a broken exclusion makes the baseline itself the newest
        artifact); the newest named file is the real source artifact (entry
        closeout-migrate-zero-delta-silence, baseline-file exclusion arm)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            rel = ".ai-playbook/reviews/earlier-r1.md"
            _write(source / rel, b"earlier\n")
            old = time.time() - 120
            os.utime(source / rel, (old, old))
            # The baseline lives under the facts-resolved docs/tmp dir of
            # the source tree.
            baseline = source / "docs/tmp/closeout-baseline.json"
            _capture_baseline(source, baseline)
            # A re-run shape: the target already holds a byte-identical twin
            # of the un-baselined baseline file, so the transfer skips it
            # and the delta stays at zero.
            _write(target / "docs/tmp/closeout-baseline.json", baseline.read_bytes())
            # Widen the margin: a broken exclusion would make the baseline
            # file the newest artifact by a full two minutes.
            future = time.time() + 120
            os.utime(baseline, (future, future))
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            text = stderr.getvalue()
            self.assertIn("zero-delta report", text)
            self.assertIn("predates the baseline capture", text)
            self.assertIn(rel, text)
            self.assertNotIn("closeout-baseline.json", text)
            self.assertNotIn("postdates the baseline capture", text)

    def test_zero_delta_report_unbaselined_target_identical_file_contributes_newest_mtime(self):
        """[class: REPOSITORY_TEST] A source file absent from the baseline
        whose target copy is byte-identical is skipped without a rename or
        rewrite, leaving the transfer delta at zero, and its mtime still
        anchors the zero-delta report as the newest source artifact (entry
        closeout-migrate-zero-delta-silence, un-baselined contributor
        arm)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            rel = ".ai-playbook/reviews/pre-existing-r1.md"
            _write(source / rel, b"old\n")
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            # The baseline never saw this artifact and the target already
            # carries a byte-identical copy: skipped without rename or
            # rewrite, the delta stays zero.
            extra_rel = ".ai-playbook/reviews/unbaselined-r2.md"
            _write(source / extra_rel, b"unbaselined\n")
            _write(target / extra_rel, b"unbaselined\n")
            old = time.time() - 120
            newer = time.time() - 60
            os.utime(source / rel, (old, old))
            os.utime(source / extra_rel, (newer, newer))
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            data = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(data["migrated"], [])
            skipped = {entry["source"]: entry for entry in data["skipped"]}
            self.assertIn(extra_rel, skipped)
            self.assertEqual(
                skipped[extra_rel]["reason"],
                "target byte-identical; skipped without rename or rewrite",
            )
            text = stderr.getvalue()
            self.assertIn("zero-delta report", text)
            self.assertIn("predates the baseline capture", text)
            self.assertIn(extra_rel, text)

    def test_migrate_rename_only_delta_prints_no_zero_delta_report(self):
        """[class: REPOSITORY_TEST] A migration whose only delta is one
        collision rename (nothing copied, the target holding different
        bytes) exits 0, keeps the manifest rename entry, and prints no
        zero-delta report line: the plan Terms define zero-delta as no
        copied, collision-renamed, OR receipt-proven replaced files, so a
        rename-only migration is not the ambiguous empty shape the
        adjudication line exists for (entry
        closeout-migrate-zero-delta-silence, fix pass 2 trigger scope)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "closeout-baseline.json"
            _capture_baseline(source, baseline)
            _write(source / ".ai-playbook/reviews/collide.md", b"incoming content\n")
            _write(target / ".ai-playbook/reviews/collide.md", b"existing different\n")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, root / "manifest.json")
            self.assertEqual(code, 0)
            data = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(data["migrated"], [])
            self.assertEqual(
                [entry["source"] for entry in data.get("renamed", [])],
                [".ai-playbook/reviews/collide.md"],
            )
            self.assertEqual(
                (target / ".ai-playbook/reviews/collide.wt-1.md").read_bytes(),
                b"incoming content\n",
            )
            self.assertNotIn("zero-delta report", stderr.getvalue())


class MigrateMergeLockTest(unittest.TestCase):
    """Fixtures for the migrate subcommand's runner-owned merge-lock span
    (plan 2026-10-10-done-closeout-lock-span Task 1): a bounded-wait acquire
    under its own label, a contended refusal that fails loud with the holder
    evidence and copies nothing, and an always-run release when the migration
    fails mid-run. The sweep suite's blocker fixture is the pattern."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-migrate-lock-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        env = os.environ.copy()
        env.update(self.GIT_IDENTITY)
        subprocess.run(["git", "-C", str(self.primary), "init", "-q"], capture_output=True, env=env, check=True)
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\nreview_certs_dir = \".ai-playbook/review-certs/\"\n```\n",
        )
        # The repo-local done-lock copy the migrate arm resolves beside the
        # env override (the SweepTest fixture convention).
        (self.primary / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(DONE_LOCK_SCRIPT_PATH, self.primary / "scripts" / "done-lock.sh")
        subprocess.run(["git", "-C", str(self.primary), "add", "-A"], capture_output=True, env=env, check=True)
        subprocess.run(["git", "-C", str(self.primary), "commit", "-q", "-m", "init: fixture repo"], capture_output=True, env=env, check=True)
        self.merge_lock_root = self.root / "merge-locks"
        # In-process runs (MODULE.main) resolve the lock env from this
        # process's environment: pin it hermetically for the whole class.
        pins = _hermetic_lock_env(self.root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _seed_transfer(self) -> tuple[Path, Path, Path]:
        """A baseline capture from a source dir plus one new file, so a
        successful migrate copies exactly one file into the primary."""
        source = self.root / "source"
        _write(source / ".ai-playbook/reviews/notes.md", b"review notes\n")
        baseline = self.root / "baseline.json"
        code, _stdout, stderr = _run_cli("capture", "--out", str(baseline), cwd=source)
        self.assertEqual(code, 0, stderr)
        _write(source / ".ai-playbook/reviews/fresh.md", b"fresh bytes\n")
        manifest = self.root / "closeout-migration.json"
        return source, baseline, manifest

    def _run_migrate_subprocess(self, source: Path, baseline: Path, manifest: Path, **extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH), "migrate",
                "--baseline", str(baseline),
                "--source", str(source),
                "--target", str(self.primary),
                "--manifest", str(manifest),
            ],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root, **extra),
        )

    def _acquire_foreign_hold(self, label: str, holder_pid: int) -> dict[str, str]:
        acquired = subprocess.run(
            ["bash", str(self.primary / "scripts" / "done-lock.sh"), "merge-acquire", "--label", label],
            capture_output=True, text=True, cwd=str(self.primary),
            env=_hermetic_lock_env(self.root, MERGE_LOCK_HOLDER_PID=str(holder_pid)),
        )
        self.assertEqual(acquired.returncode, 0, acquired.stderr)
        exports: dict[str, str] = {}
        for line in acquired.stdout.splitlines():
            for name in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
                prefix = f"export {name}="
                if line.startswith(prefix):
                    exports[name] = line[len(prefix):]
        self.assertIn("MERGE_LOCK_DIR", exports)
        self.assertIn("MERGE_LOCK_TOKEN", exports)
        return exports

    def _release_hold(self, exports: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(self.primary / "scripts" / "done-lock.sh"), "merge-release"],
            capture_output=True, text=True, cwd=str(self.primary),
            env=_hermetic_lock_env(self.root, **exports),
        )

    def test_migrate_foreign_held_merge_lock_refuses_and_copies_nothing(self):
        source, baseline, manifest = self._seed_transfer()
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        exports = self._acquire_foreign_hold("blocker", holder.pid)
        try:
            proc = self._run_migrate_subprocess(source, baseline, manifest, DOCS_SYNC_MERGE_MAX_WAIT="2")
        finally:
            released = self._release_hold(exports)
        self.assertEqual(released.returncode, 0, released.stderr)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("timed out after 2s", proc.stderr)
        self.assertIn("label: blocker", proc.stderr)
        self.assertFalse((self.primary / ".ai-playbook/reviews/fresh.md").exists(), "a copy ran while the merge lock was held")
        self.assertFalse(manifest.exists(), "a manifest was written while the merge lock was held")

    def test_migrate_merge_lock_released_when_migration_fails(self):
        source, baseline, manifest = self._seed_transfer()
        original_verify = MODULE._verify_copy
        captured = io.StringIO()

        def failing_verify(src: Path, dst: Path) -> bool:
            return False

        MODULE._verify_copy = failing_verify
        try:
            with contextlib.redirect_stderr(captured):
                code = MODULE.main(
                    [
                        "migrate",
                        "--baseline", str(baseline),
                        "--source", str(source),
                        "--target", str(self.primary),
                        "--manifest", str(manifest),
                    ]
                )
        finally:
            MODULE._verify_copy = original_verify
        self.assertEqual(code, 1)
        self.assertIn("merge-lock: held", captured.getvalue(), "no held-span line at release")
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the merge lock was not released")
        self.assertTrue(manifest.is_file())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertTrue(data.get("failed"))

    def test_migrate_receipt_replacement_runs_inside_merge_lock_span(self):
        """[class: REPOSITORY_TEST] The replacement decision, staging, final
        recheck, and install all sit inside the existing runner-owned merge
        lock: a foreign hold refuses the whole migration (nothing replaced),
        and the same invocation after release replaces through the span."""
        source = self.root / "mirror-source"
        rel = ".ai-playbook/reviews/runtime_state.json"
        prior_bytes = b'{"state": "boundary-1"}\n'
        incoming_bytes = b'{"state": "boundary-2"}\n'
        _write(source / rel, prior_bytes)
        session_dir = source / "docs/tmp/execute-plan/mirror-lock-fixture"
        _write_session_manifest(
            session_dir / "manifest.md",
            [f"task_boundary: task 1 commit abc1234; mirror_status=complete mirror_receipts={_receipts_token([_file_receipt(rel, _digest(prior_bytes))])}"],
            run_worktree=str(source),
        )
        baseline = session_dir / "closeout-baseline.json"
        _capture_baseline(source, baseline)
        _write(source / rel, incoming_bytes)
        _write(self.primary / rel, prior_bytes)
        migration_manifest = self.root / "closeout-migration.json"
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        exports = self._acquire_foreign_hold("blocker", holder.pid)
        try:
            proc = self._run_migrate_subprocess(source, baseline, migration_manifest, DOCS_SYNC_MERGE_MAX_WAIT="2")
        finally:
            released = self._release_hold(exports)
        self.assertEqual(released.returncode, 0, released.stderr)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(
            (self.primary / rel).read_bytes(),
            prior_bytes,
            "a replacement ran while the merge lock was held",
        )
        self.assertFalse(migration_manifest.exists(), "a manifest was written while the merge lock was held")
        code = MODULE.main(
            [
                "migrate",
                "--baseline", str(baseline),
                "--source", str(source),
                "--target", str(self.primary),
                "--manifest", str(migration_manifest),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual((self.primary / rel).read_bytes(), incoming_bytes)
        data = json.loads(migration_manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["replaced"]], [rel])



class _StripsHostGitEnv:
    """Process-env hermeticity for in-process migrate runs: save and
    strip inherited GIT_* variables, restore on cleanup. One home for the
    BaselineClobberGuardTest / MigrateMirrorReceiptTest twins, so a
    hermeticity fix to one class cannot silently miss the other."""

    def strip_host_git_env(self) -> None:
        self._saved_git_env = {
            key: os.environ.get(key)
            for key in list(os.environ)
            if key.startswith("GIT_") or key == "XDG_CONFIG_HOME"
        }
        for key in self._saved_git_env:
            os.environ.pop(key, None)
        # The non-GIT_* git-config surfaces (guideline #28's gate): pin
        # both config files off so in-process git subprocesses read no
        # host XDG or system config; restore pops the saved-None keys.
        self._saved_git_env.setdefault("GIT_CONFIG_GLOBAL", None)
        self._saved_git_env.setdefault("GIT_CONFIG_SYSTEM", None)
        os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
        os.environ["GIT_CONFIG_SYSTEM"] = os.devnull

    def restore_host_git_env(self) -> None:
        for key, value in self._saved_git_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class MigrateMirrorReceiptTest(_StripsHostGitEnv, unittest.TestCase):
    """Fixtures for receipt-proven same-run mirror replacement at closeout
    migration (plan 2026-10-24-closeout-migration-same-run-mirror-replace
    Task 1): the session manifest beside the baseline binds the stable run
    tuple, terminal mirror_status/mirror_receipts tokens on task_boundary
    rows authorize replacing a different-byte primary target only while its
    current state still matches the latest valid receipt for that exact
    path, and every invalid or mismatched shape keeps the existing foreign
    rename or verified no-op behavior."""

    CONTROL = ".ai-playbook/reviews/control.md"
    PROBE = ".ai-playbook/reviews/probe.md"

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-mirror-receipt-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        lock_root = self.root / "lock-root"
        # Strip BEFORE the lock-env pins are applied so the saved map
        # captures the true host state (the pins carry their own
        # GIT_CONFIG_GLOBAL/SYSTEM devnull values; the in-process
        # _migrate git subprocesses inherit this process env, so the
        # recorded blob and the expected blob hash under one conversion
        # configuration - shared twin home _StripsHostGitEnv).
        self.strip_host_git_env()
        self.addCleanup(self.restore_host_git_env)
        pins = _hermetic_lock_env(lock_root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _seed(self, rows: list[str]) -> tuple[Path, Path]:
        """The source worktree with a session manifest carrying `rows` and
        the baseline captured beside it (both before any post-baseline
        mutation, so mutated files become migration candidates)."""
        source = self.root / "source"
        source.mkdir(parents=True, exist_ok=True)
        session_dir = source / "docs/tmp/execute-plan/mirror-fixture"
        _write_session_manifest(session_dir / "manifest.md", rows, run_worktree=str(source))
        baseline = session_dir / "closeout-baseline.json"
        _capture_baseline(source, baseline)
        return source, baseline

    def _boundary_row(self, items: list[dict], status: str = "complete") -> str:
        return (
            "task_boundary: task 1 commit abc1234 verification: pass; "
            f"mirror_status={status} mirror_receipts={_receipts_token(items)}"
        )

    def _boundary_row_raw(self, status: str, token: str) -> str:
        return (
            "task_boundary: task 1 commit abc1234; "
            f"mirror_status={status} mirror_receipts={token}"
        )

    def _collision_case(
        self, rows: list[str], rel: str, prior_bytes: bytes, incoming_bytes: bytes
    ) -> tuple[Path, Path, Path]:
        """Seed the run with `rows`, then make `rel` a different-byte
        collision: incoming bytes in the source worktree, prior bytes at the
        primary. Returns (source, baseline, target)."""
        source, baseline = self._seed(rows)
        _write(source / rel, incoming_bytes)
        target = self.root / "target"
        _write(target / rel, prior_bytes)
        return source, baseline, target

    def _renamed_sibling(self, target: Path, rel: str) -> Path:
        return target / Path(rel).with_name(f"{Path(rel).stem}.wt-1{Path(rel).suffix}")

    def _migrate_expect_foreign(
        self,
        source: Path,
        baseline: Path,
        target: Path,
        rel: str,
        prior_bytes: bytes,
        incoming_bytes: bytes,
    ) -> dict:
        manifest = self.root / "closeout-migration.json"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0, buf.getvalue())
        self.assertEqual(
            (target / rel).read_bytes(),
            prior_bytes,
            "the current target was overwritten",
        )
        self.assertEqual(self._renamed_sibling(target, rel).read_bytes(), incoming_bytes)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])
        self.assertIn(rel, [entry["source"] for entry in data.get("renamed", [])])
        return data

    # Task 1 checklist item 1: the collision-shape fixtures.

    def test_migrate_replaces_receipt_proven_same_run_collision(self):
        """[class: REPOSITORY_TEST] The exact-path positive case: the
        primary mirror's current bytes match the latest valid receipt for
        that exact path, so the incoming file replaces the target instead of
        being renamed; every replaced-entry payload field and the summary
        count are asserted."""
        rel = ".ai-playbook/reviews/runtime_state.json"
        prior = b'{"state": "boundary-1"}\n'
        incoming = b'{"state": "boundary-2"}\n'
        row = self._boundary_row([_file_receipt(rel, _digest(prior))])
        source, baseline, target = self._collision_case([row], rel, prior, incoming)
        manifest = self.root / "closeout-migration.json"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / rel).read_bytes(), incoming)
        self.assertEqual(
            [path.name for path in (target / ".ai-playbook/reviews").iterdir()],
            ["runtime_state.json"],
            "a receipt-proven replacement produced a .wt- rename sibling",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data.get("renamed", [])], [])
        replaced = data["replaced"]
        self.assertEqual(len(replaced), 1)
        entry = replaced[0]
        self.assertEqual(entry["source"], rel)
        self.assertEqual(entry["destination"], (target.resolve() / rel).as_posix())
        self.assertTrue(entry["verified"])
        self.assertEqual(entry["run_session_id"], "sess-mirror-fixture-1")
        self.assertEqual(entry["prior_state"], {"type": "file", "sha256": _digest(prior)})
        self.assertEqual(entry["incoming_state"], {"type": "file", "sha256": _digest(incoming)})
        self.assertIn("replaced 1", buf.getvalue())
        self.assertNotIn("COLLISION:", buf.getvalue())

    def test_migrate_replaced_only_delta_prints_no_zero_delta_report(self):
        """[class: REPOSITORY_TEST] A migration whose only delta is one
        receipt-proven replacement (nothing copied, no collision rename)
        exits 0, keeps the manifest replaced entry intact, and prints no
        zero-delta report line: the plan Terms define zero-delta as no
        copied, collision-renamed, OR receipt-proven replaced files, so a
        replaced-only migration is not the ambiguous empty shape the
        adjudication line exists for (entry
        closeout-migrate-zero-delta-silence, Phase 3 trigger scope)."""
        rel = ".ai-playbook/reviews/runtime_state.json"
        prior = b'{"state": "boundary-1"}\n'
        incoming = b'{"state": "boundary-2"}\n'
        row = self._boundary_row([_file_receipt(rel, _digest(prior))])
        source, baseline, target = self._collision_case([row], rel, prior, incoming)
        # The un-baselined baseline file itself would otherwise be the one
        # copied file; a byte-identical twin at the target keeps it a
        # verified no-op skip so the transfer delta is the replacement only.
        _write(
            target / "docs/tmp/execute-plan/mirror-fixture/closeout-baseline.json",
            baseline.read_bytes(),
        )
        manifest = self.root / "closeout-migration.json"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / rel).read_bytes(), incoming)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["migrated"], [])
        self.assertEqual([entry["source"] for entry in data.get("renamed", [])], [])
        replaced = data["replaced"]
        self.assertEqual([entry["source"] for entry in replaced], [rel])
        self.assertTrue(replaced[0]["verified"])
        self.assertEqual(replaced[0]["prior_state"], {"type": "file", "sha256": _digest(prior)})
        self.assertEqual(replaced[0]["incoming_state"], {"type": "file", "sha256": _digest(incoming)})
        # The summary shape the Worktree-first companion clause quotes: the
        # transfer was fully non-empty in the replaced arm only.
        self.assertIn(
            "Migrated 0 file(s), renamed 0 on collision, replaced 1, skipped 1 identical",
            stdout.getvalue(),
        )
        self.assertNotIn("zero-delta report", stderr.getvalue())

    def test_migrate_identical_target_with_receipt_stays_verified_noop(self):
        """[class: REPOSITORY_TEST] A receipt-proven path whose target
        already equals the incoming bytes is a verified transfer recorded
        without a rewrite: the verified migrated row (plan
        2026-10-30-execute-plan-teardown-staging-record-mirror Task 2)
        carries the destination so the removal gate's presence check sees
        it, while the bytes stay identical, the mtime stands, and no
        rename or replaced record appears."""
        shared = b'{"state": "boundary-2"}\n'
        row = self._boundary_row([_file_receipt(self.CONTROL, _digest(shared))])
        source, baseline = self._seed([row])
        _write(source / self.CONTROL, shared)
        target = self.root / "target"
        _write(target / self.CONTROL, shared)
        os.utime(target / self.CONTROL, (1000, 1000))
        manifest = self.root / "closeout-migration.json"
        code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual(os.stat(target / self.CONTROL).st_mtime, 1000, "identical target was rewritten")
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).exists(), False)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])
        migrated = {entry["source"]: entry for entry in data.get("migrated", [])}
        self.assertIn(self.CONTROL, migrated)
        self.assertTrue(migrated[self.CONTROL]["verified"])
        self.assertEqual(
            migrated[self.CONTROL]["destination"],
            (target.resolve() / self.CONTROL).as_posix(),
        )
        self.assertNotIn(
            self.CONTROL, {entry["source"] for entry in data.get("skipped", [])}
        )

    def test_migrate_identical_target_with_receipt_records_delivered_blob(self):
        """[class: REPOSITORY_TEST] The receipt-proven identical-transfer
        arm (a byte-identical target covered by the exact path's valid
        same-run mirror receipt) records the delivered blob too: the
        verified migrated row carries the delivered_blob sha of the bytes
        standing at the target (plan
        2026-11-04-closeout-clobber-guard-review-residual-trio R10 pins
        this previously unasserted capture site)."""
        shared = b'{"state": "boundary-2"}\n'
        row = self._boundary_row([_file_receipt(self.CONTROL, _digest(shared))])
        source, baseline = self._seed([row])
        _write(source / self.CONTROL, shared)
        target = self.root / "target"
        _write(target / self.CONTROL, shared)
        manifest = self.root / "closeout-migration.json"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0, buf.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        migrated = {entry["source"]: entry for entry in data.get("migrated", [])}
        self.assertIn(self.CONTROL, migrated)
        self.assertTrue(migrated[self.CONTROL]["verified"])
        # The delivered blob derived independently of the recorder: hash a
        # scratch copy of the standing bytes (git hash-object succeeds
        # outside a repository, so a plain non-git target works).
        scratch = self.root / "standing-scratch.md"
        _write(scratch, shared)
        expected_blob = subprocess.run(
            ["git", "hash-object", "--", str(scratch)],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root), cwd=str(self.root),
        ).stdout.strip()
        scratch.unlink()
        self.assertEqual(
            migrated[self.CONTROL]["delivered_blob"], expected_blob,
            "the receipt-identical migrated row must carry the delivered "
            "blob sha of the bytes standing at the target",
        )

    def test_migrate_same_digest_other_path_stays_foreign(self):
        """[class: REPOSITORY_TEST] Cross-path same-digest rejection: a
        receipt proves one exact path only, so a collision on another path
        whose target digest equals the receipt's digest is still a foreign
        rename."""
        shared = b"shared mirror bytes\n"
        incoming = b"incoming b bytes\n"
        row = self._boundary_row([_file_receipt(self.CONTROL, _digest(shared))])
        source, baseline = self._seed([row])
        _write(source / self.PROBE, incoming)
        target = self.root / "target"
        _write(target / self.CONTROL, shared)
        _write(target / self.PROBE, shared)
        self._migrate_expect_foreign(source, baseline, target, self.PROBE, shared, incoming)
        self.assertEqual((target / self.CONTROL).read_bytes(), shared, "the receipt-proven bystander was touched")

    def test_migrate_foreign_run_worktree_authorizes_no_replacement(self):
        """[class: REPOSITORY_TEST] Identity mismatch (registered run
        worktree differs from the supplied source) authorizes no
        replacement: the collision keeps the foreign rename."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        source = self.root / "source"
        source.mkdir(parents=True)
        session_dir = source / "docs/tmp/execute-plan/mirror-fixture"
        _write_session_manifest(
            session_dir / "manifest.md",
            [self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))])],
            run_worktree=str(self.root / "elsewhere"),
        )
        baseline = session_dir / "closeout-baseline.json"
        _capture_baseline(source, baseline)
        _write(source / self.CONTROL, incoming)
        target = self.root / "target"
        _write(target / self.CONTROL, prior)
        self._migrate_expect_foreign(source, baseline, target, self.CONTROL, prior, incoming)

    def test_migrate_missing_identity_authorizes_no_replacement(self):
        """[class: REPOSITORY_TEST] A manifest whose stable tuple is
        incomplete (empty run_session_id) authorizes no replacement."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        source = self.root / "source"
        source.mkdir(parents=True)
        session_dir = source / "docs/tmp/execute-plan/mirror-fixture"
        _write_session_manifest(
            session_dir / "manifest.md",
            [self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))])],
            run_worktree=str(source),
            run_session_id="",
        )
        baseline = session_dir / "closeout-baseline.json"
        _capture_baseline(source, baseline)
        _write(source / self.CONTROL, incoming)
        target = self.root / "target"
        _write(target / self.CONTROL, prior)
        self._migrate_expect_foreign(source, baseline, target, self.CONTROL, prior, incoming)

    def test_migrate_unrecoverable_plan_path_authorizes_no_replacement(self):
        """[class: REPOSITORY_TEST] Identity negative control: a plan_path
        outside the repository root (absolute, or escaping through ..)
        fails the recoverable-path form check, so the manifest authorizes
        no replacement and the collision stays a foreign rename."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        for name, plan_path in (
            ("absolute", "/abs/closeout-plan.md"),
            ("dotdot-escape", "../outside/closeout-plan.md"),
        ):
            with self.subTest(plan_path=plan_path):
                case_root = self.root / f"identity-{name}"
                source = case_root / "source"
                source.mkdir(parents=True)
                session_dir = source / "docs/tmp/execute-plan/mirror-fixture"
                _write_session_manifest(
                    session_dir / "manifest.md",
                    [self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))])],
                    run_worktree=str(source),
                    plan_path=plan_path,
                )
                baseline = session_dir / "closeout-baseline.json"
                _capture_baseline(source, baseline)
                _write(source / self.CONTROL, incoming)
                target = case_root / "target"
                _write(target / self.CONTROL, prior)
                self._migrate_expect_foreign(
                    source, baseline, target, self.CONTROL, prior, incoming
                )

    def test_migrate_changed_target_stays_foreign(self):
        """[class: REPOSITORY_TEST] A target whose current state no longer
        matches the receipt (changed after the boundary recorded it) is
        foreign: preserved bytes, renamed incoming, COLLISION evidence."""
        prior = b"prior mirror bytes\n"
        changed = b"changed after the boundary bytes\n"
        incoming = b"incoming mirror bytes\n"
        row = self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))])
        source, baseline = self._seed([row])
        _write(source / self.CONTROL, incoming)
        target = self.root / "target"
        _write(target / self.CONTROL, changed)
        manifest = self.root / "closeout-migration.json"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / self.CONTROL).read_bytes(), changed)
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).read_bytes(), incoming)
        self.assertIn("COLLISION:", buf.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])

    # Symlink receipts.

    def test_migrate_replaces_receipt_proven_symlink_collision(self):
        """[class: REPOSITORY_TEST] A symlink mirror whose current link
        target matches its receipt is replaced by the incoming link."""
        rel = ".ai-playbook/reviews/link.md"
        row = self._boundary_row([_symlink_receipt(rel, "boundary-1.md")])
        source, baseline = self._seed([row])
        (source / rel).parent.mkdir(parents=True, exist_ok=True)
        # The link target must exist in the source so the link is not the
        # dangling shape the migration skips.
        _write(source / ".ai-playbook/reviews/boundary-2.md", b"boundary two content\n")
        os.symlink("boundary-2.md", source / rel)
        target = self.root / "target"
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        os.symlink("boundary-1.md", target / rel)
        manifest = self.root / "closeout-migration.json"
        code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertTrue((target / rel).is_symlink(), "symlink replacement dereferenced the link")
        self.assertEqual(os.readlink(target / rel), "boundary-2.md")
        self.assertEqual(self._renamed_sibling(target, rel).exists(), False)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(len(data["replaced"]), 1)
        entry = data["replaced"][0]
        self.assertEqual(entry["source"], rel)
        self.assertEqual(entry["prior_state"], {"type": "symlink", "target": "boundary-1.md"})
        self.assertEqual(entry["incoming_state"], {"type": "symlink", "target": "boundary-2.md"})

    def test_migrate_receipt_type_mismatch_stays_foreign(self):
        """[class: REPOSITORY_TEST] A receipt typed file never authorizes
        replacing a symlink at that path: the link's destination holds bytes
        matching the receipt digest, so only the type guard (symlink
        rejection) keeps the collision a foreign rename."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        row = self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))])
        source, baseline = self._seed([row])
        _write(source / self.CONTROL, incoming)
        target = self.root / "target"
        # The destination file lives beside the link so the relative link
        # resolves: its bytes match the receipt digest, leaving the type
        # guard as the only mismatch signal.
        _write(target / ".ai-playbook/reviews/elsewhere.md", prior)
        (target / self.CONTROL).parent.mkdir(parents=True, exist_ok=True)
        os.symlink("elsewhere.md", target / self.CONTROL)
        data = self._migrate_expect_foreign(
            source, baseline, target, self.CONTROL, prior, incoming
        )
        self.assertTrue((target / self.CONTROL).is_symlink(), "the type guard dereferenced the link")
        self.assertEqual(os.readlink(target / self.CONTROL), "elsewhere.md")
        self.assertEqual(data.get("replaced", []), [])

    # Task 1 checklist item 2: the parser cases (run-wide versus
    # path-only invalidation).

    def test_migrate_invalid_json_receipts_invalidate_run(self):
        """[class: REPOSITORY_TEST] An unparseable mirror_receipts payload
        invalidates run history: no replacement anywhere, no crash."""
        incoming = b"incoming mirror bytes\n"
        prior = b"prior mirror bytes\n"
        row = self._boundary_row_raw("complete", '[{"path":')
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        self._migrate_expect_foreign(source, baseline, target, self.CONTROL, prior, incoming)

    def test_migrate_unknown_row_status_invalidates_run(self):
        """[class: REPOSITORY_TEST] A mirror_status outside the known set
        invalidates run history even though the receipts array parses."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        row = self._boundary_row_raw("finished", _receipts_token([_file_receipt(self.CONTROL, _digest(prior))]))
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        self._migrate_expect_foreign(source, baseline, target, self.CONTROL, prior, incoming)

    def test_migrate_unparseable_row_tokens_invalidate_run(self):
        """[class: REPOSITORY_TEST] A task_boundary row carrying
        mirror_status without its terminal mirror_receipts token cannot be
        parsed and invalidates run history."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        rows = [
            self._boundary_row([_file_receipt(self.PROBE, _digest(prior))]),
            "task_boundary: task 2 commit abc1235; mirror_status=complete",
        ]
        source, baseline, target = self._collision_case(rows, self.CONTROL, prior, incoming)
        _write(target / self.PROBE, prior)
        _write(source / self.PROBE, incoming)
        self._migrate_expect_foreign(source, baseline, target, self.CONTROL, prior, incoming)
        data = json.loads((self.root / "closeout-migration.json").read_text(encoding="utf-8"))
        self.assertIn(self.PROBE, [entry["source"] for entry in data.get("renamed", [])],
                      "the newer unparseable row did not invalidate the older valid receipt")

    def test_migrate_older_valid_newer_malformed_invalidates_run(self):
        """[class: REPOSITORY_TEST] A valid older row never survives a newer
        malformed one: run history is invalidated run-wide, never falling
        back to the older valid receipt."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        rows = [
            self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))]),
            self._boundary_row_raw("partial", "[oops"),
        ]
        source, baseline, target = self._collision_case(rows, self.CONTROL, prior, incoming)
        self._migrate_expect_foreign(source, baseline, target, self.CONTROL, prior, incoming)

    def test_migrate_two_valid_rows_same_path_latest_row_wins(self):
        """[class: REPOSITORY_TEST] Two verified receipts for one path across
        rows resolve latest-row-wins: the primary target holds the row-1
        digest, which does not match the row-2 receipt, so the collision
        stays a foreign rename with COLLISION evidence, never a replacement."""
        row_one = b"row one mirror bytes\n"
        row_two = b"row two mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        rows = [
            self._boundary_row([_file_receipt(self.CONTROL, _digest(row_one))]),
            self._boundary_row([_file_receipt(self.CONTROL, _digest(row_two))]),
        ]
        source, baseline, target = self._collision_case(rows, self.CONTROL, row_one, incoming)
        manifest = self.root / "closeout-migration.json"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual(
            (target / self.CONTROL).read_bytes(),
            row_one,
            "the primary target was replaced against the latest row's receipt",
        )
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).read_bytes(), incoming)
        self.assertIn("COLLISION:", buf.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])
        self.assertIn(self.CONTROL, [entry["source"] for entry in data.get("renamed", [])])

    def test_migrate_complete_empty_receipts_row_changes_no_path(self):
        """[class: REPOSITORY_TEST] A terminal row carrying
        mirror_status=complete mirror_receipts=[] between valid receipt rows
        changes no path: the earlier valid receipt still authorizes
        replacement and the empty row invalidates nothing."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        rows = [
            self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))]),
            self._boundary_row([]),
            self._boundary_row([_file_receipt(self.PROBE, _digest(prior))]),
        ]
        source, baseline, target = self._collision_case(rows, self.CONTROL, prior, incoming)
        manifest = self.root / "closeout-migration.json"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual(
            (target / self.CONTROL).read_bytes(),
            incoming,
            "the empty complete row invalidated the earlier valid receipt",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["replaced"]], [self.CONTROL])
        self.assertEqual(data.get("renamed", []), [])

    def test_migrate_duplicate_path_invalidates_only_that_path(self):
        """[class: REPOSITORY_TEST] A path repeated inside one row's array
        is ambiguous and invalidates only that path; another receipt-proven
        path in the same row stays eligible."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        probe_prior = b"probe prior bytes\n"
        probe_incoming = b"probe incoming bytes\n"
        row = self._boundary_row(
            [
                _file_receipt(self.CONTROL, _digest(prior)),
                _file_receipt(self.CONTROL, _digest(prior)),
                _file_receipt(self.PROBE, _digest(probe_prior)),
            ]
        )
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        _write(source / self.PROBE, probe_incoming)
        _write(target / self.PROBE, probe_prior)
        manifest = self.root / "closeout-migration.json"
        code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / self.PROBE).read_bytes(), probe_incoming, "the unambiguous path was not replaced")
        self.assertEqual((target / self.CONTROL).read_bytes(), prior)
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).read_bytes(), incoming)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["replaced"]], [self.PROBE])
        self.assertIn(self.CONTROL, [entry["source"] for entry in data.get("renamed", [])])

    def test_migrate_unknown_item_status_invalidates_only_that_path(self):
        """[class: REPOSITORY_TEST] Task 1 checklist item 3: in one row with
        valid path A and malformed (unknown-status) recoverable path B, A
        stays eligible and is replaced while B is preserved and renamed."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        probe_prior = b"probe prior bytes\n"
        probe_incoming = b"probe incoming bytes\n"
        row = self._boundary_row(
            [
                _file_receipt(self.PROBE, _digest(probe_prior)),
                _status_receipt(self.CONTROL, "copied"),
            ]
        )
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        _write(source / self.PROBE, probe_incoming)
        _write(target / self.PROBE, probe_prior)
        manifest = self.root / "closeout-migration.json"
        code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / self.PROBE).read_bytes(), probe_incoming, "the valid path lost eligibility")
        self.assertEqual((target / self.CONTROL).read_bytes(), prior)
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).read_bytes(), incoming)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["replaced"]], [self.PROBE])
        self.assertIn(self.CONTROL, [entry["source"] for entry in data.get("renamed", [])])

    def test_migrate_unrecoverable_item_path_invalidates_run(self):
        """[class: REPOSITORY_TEST] An item whose path cannot be recovered
        (not a repository-relative string) invalidates run history: even a
        validly receipted path is foreign-renamed."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        probe_prior = b"probe prior bytes\n"
        probe_incoming = b"probe incoming bytes\n"
        bad_item = {"path": 42, "status": "verified", "type": "file", "sha256": _digest(prior)}
        row = self._boundary_row([bad_item, _file_receipt(self.PROBE, _digest(probe_prior))])
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        _write(source / self.PROBE, probe_incoming)
        _write(target / self.PROBE, probe_prior)
        data = self._migrate_expect_foreign(source, baseline, target, self.CONTROL, prior, incoming)
        self.assertIn(self.PROBE, [entry["source"] for entry in data.get("renamed", [])],
                      "run-wide invalidation fell back to a per-path authorization")

    def test_migrate_missing_digest_invalidates_only_that_path(self):
        """[class: REPOSITORY_TEST] A malformed verified file item (no
        sha256) with a recoverable path invalidates only that path."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        probe_prior = b"probe prior bytes\n"
        probe_incoming = b"probe incoming bytes\n"
        malformed = {"path": self.CONTROL, "status": "verified", "type": "file"}
        row = self._boundary_row([_file_receipt(self.PROBE, _digest(probe_prior)), malformed])
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        _write(source / self.PROBE, probe_incoming)
        _write(target / self.PROBE, probe_prior)
        manifest = self.root / "closeout-migration.json"
        code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / self.PROBE).read_bytes(), probe_incoming)
        self.assertEqual((target / self.CONTROL).read_bytes(), prior)
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).read_bytes(), incoming)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["replaced"]], [self.PROBE])

    # Task 1 checklist item 4: partial and skipped rows.

    def test_migrate_partial_row_failed_path_invalidates_only_itself(self):
        """[class: REPOSITORY_TEST] In a partial row the failed path
        invalidates only itself; an untouched path keeps its prior receipt
        and can use it after the digest recheck, and a newly verified path
        becomes eligible."""
        prior_a = b"a prior bytes\n"
        prior_b = b"b prior bytes\n"
        prior_c = b"c prior bytes\n"
        incoming_a = b"a incoming bytes\n"
        incoming_b = b"b incoming bytes\n"
        incoming_c = b"c incoming bytes\n"
        rel_a = ".ai-playbook/reviews/a.md"
        rel_b = ".ai-playbook/reviews/b.md"
        rel_c = ".ai-playbook/reviews/c.md"
        rows = [
            self._boundary_row([
                _file_receipt(rel_a, _digest(prior_a)),
                _file_receipt(rel_b, _digest(prior_b)),
            ]),
            self._boundary_row([
                _status_receipt(rel_a, "failed"),
                _file_receipt(rel_c, _digest(prior_c)),
            ], status="partial"),
        ]
        source, baseline = self._seed(rows)
        _write(source / rel_a, incoming_a)
        _write(source / rel_b, incoming_b)
        _write(source / rel_c, incoming_c)
        target = self.root / "target"
        _write(target / rel_a, prior_a)
        _write(target / rel_b, prior_b)
        _write(target / rel_c, prior_c)
        manifest = self.root / "closeout-migration.json"
        code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / rel_a).read_bytes(), prior_a, "the failed path was replaced")
        self.assertEqual(self._renamed_sibling(target, rel_a).read_bytes(), incoming_a)
        self.assertEqual((target / rel_b).read_bytes(), incoming_b, "the untouched path lost its prior receipt")
        self.assertEqual((target / rel_c).read_bytes(), incoming_c)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(entry["source"] for entry in data["replaced"]),
            sorted([rel_b, rel_c]),
        )
        self.assertIn(rel_a, [entry["source"] for entry in data.get("renamed", [])])

    def test_migrate_skipped_row_items_invalidate_only_their_paths(self):
        """[class: REPOSITORY_TEST] A skipped row (lock contention shape)
        invalidates exactly the paths it lists; other receipts stay valid."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        probe_prior = b"probe prior bytes\n"
        probe_incoming = b"probe incoming bytes\n"
        rows = [
            self._boundary_row([
                _file_receipt(self.CONTROL, _digest(prior)),
                _file_receipt(self.PROBE, _digest(probe_prior)),
            ]),
            self._boundary_row([_status_receipt(self.CONTROL, "skipped")], status="skipped"),
        ]
        source, baseline, target = self._collision_case(rows, self.CONTROL, prior, incoming)
        _write(source / self.PROBE, probe_incoming)
        _write(target / self.PROBE, probe_prior)
        manifest = self.root / "closeout-migration.json"
        code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / self.PROBE).read_bytes(), probe_incoming)
        self.assertEqual((target / self.CONTROL).read_bytes(), prior)
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).read_bytes(), incoming)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["replaced"]], [self.PROBE])

    # Task 1 checklist item 5: the interleaving fixture.

    def test_migrate_destination_change_between_staging_and_recheck_stays_foreign(self):
        """[class: REPOSITORY_TEST] A destination changed between staging
        and the final recheck is foreign: its changed bytes are preserved
        and the incoming file takes the existing rename path."""
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        interloper = b"interloper bytes written after staging\n"
        row = self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))])
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        original_copy = MODULE._copy_file

        def interleaving_copy(src, dst):
            result = original_copy(src, dst)
            if Path(src).name == "control.md":
                _write(target / self.CONTROL, interloper)
            return result

        MODULE._copy_file = interleaving_copy
        try:
            manifest = self.root / "closeout-migration.json"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = _migrate(source, target, baseline, manifest)
        finally:
            MODULE._copy_file = original_copy
        self.assertEqual(code, 0)
        self.assertEqual((target / self.CONTROL).read_bytes(), interloper, "the interloper write was lost")
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).read_bytes(), incoming)
        self.assertIn("COLLISION:", buf.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])

    # Task 1 checklist item 6: the failure injections.

    def _failure_case(self):
        prior = b"prior mirror bytes\n"
        incoming = b"incoming mirror bytes\n"
        row = self._boundary_row([_file_receipt(self.CONTROL, _digest(prior))])
        source, baseline, target = self._collision_case([row], self.CONTROL, prior, incoming)
        return source, baseline, target, prior, incoming

    def _assert_no_temp_siblings(self, target: Path) -> None:
        leaked = [
            path.name
            for path in target.rglob("*")
            if ".repl-" in path.name or ".tmp-" in path.name
        ]
        self.assertEqual(leaked, [], "temporary siblings survived the failure")

    def test_migrate_replacement_copy_failure_preserves_prior_and_fails(self):
        """[class: REPOSITORY_TEST] A failed staged copy preserves the prior
        target and the source, removes the temporary sibling, records the
        failure, and keeps the migration unsuccessful."""
        source, baseline, target, prior, incoming = self._failure_case()
        original_copy = MODULE._copy_file

        def failing_copy(src, dst):
            if ".repl-" in Path(dst).name:
                raise OSError("simulated staged copy failure")
            return original_copy(src, dst)

        MODULE._copy_file = failing_copy
        try:
            manifest = self.root / "closeout-migration.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, manifest)
        finally:
            MODULE._copy_file = original_copy
        self.assertEqual(code, 1)
        self.assertEqual((target / self.CONTROL).read_bytes(), prior)
        self.assertEqual((source / self.CONTROL).read_bytes(), incoming, "the source was moved")
        self._assert_no_temp_siblings(target)
        self.assertEqual(self._renamed_sibling(target, self.CONTROL).exists(), False)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])
        failed = {entry["source"]: entry for entry in data.get("failed", [])}
        self.assertIn(self.CONTROL, failed)
        self.assertIn("receipt replacement failed", failed[self.CONTROL]["error"])
        self.assertIn("verification failed", stderr.getvalue())

    def test_migrate_replacement_verification_failure_preserves_prior_and_fails(self):
        """[class: REPOSITORY_TEST] A staged copy that fails verification
        preserves the prior target and the source and removes the temp."""
        source, baseline, target, prior, incoming = self._failure_case()
        original_verify = MODULE._verify_copy

        def refused_verify(src, dst):
            if ".repl-" in Path(dst).name:
                return False
            return original_verify(src, dst)

        MODULE._verify_copy = refused_verify
        try:
            manifest = self.root / "closeout-migration.json"
            code = _migrate(source, target, baseline, manifest)
        finally:
            MODULE._verify_copy = original_verify
        self.assertEqual(code, 1)
        self.assertEqual((target / self.CONTROL).read_bytes(), prior)
        self.assertEqual((source / self.CONTROL).read_bytes(), incoming)
        self._assert_no_temp_siblings(target)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])
        failed = {entry["source"]: entry for entry in data.get("failed", [])}
        self.assertIn(self.CONTROL, failed)

    def test_migrate_replacement_install_failure_preserves_prior_and_fails(self):
        """[class: REPOSITORY_TEST] A failed atomic install preserves the
        prior target and the source, removes the staged and prior-temp
        siblings, records the failure, and keeps the migration
        unsuccessful."""
        source, baseline, target, prior, incoming = self._failure_case()
        original_install = MODULE._install_staged

        def failing_install(temp, dst):
            raise OSError("simulated install failure")

        MODULE._install_staged = failing_install
        try:
            manifest = self.root / "closeout-migration.json"
            code = _migrate(source, target, baseline, manifest)
        finally:
            MODULE._install_staged = original_install
        self.assertEqual(code, 1)
        self.assertEqual((target / self.CONTROL).read_bytes(), prior)
        self.assertEqual((source / self.CONTROL).read_bytes(), incoming)
        self._assert_no_temp_siblings(target)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced", []), [])
        failed = {entry["source"]: entry for entry in data.get("failed", [])}
        self.assertIn(self.CONTROL, failed)

    def test_migrate_manifest_persistence_failure_restores_prior_target(self):
        """[class: REPOSITORY_TEST] Task 1 checklist item 14: a migration
        manifest persistence failure after staged installation restores the
        prior target, leaves the prior manifest bytes intact, retains the
        source, and fails; a retry then records a durable replaced entry."""
        source, baseline, target, prior, incoming = self._failure_case()
        migration_manifest = self.root / "closeout-migration.json"
        _write(migration_manifest, b'{"prior": true}\n')
        original_append = MODULE._append_manifest

        def failing_persist(path, sections):
            raise OSError("simulated manifest persistence failure")

        MODULE._append_manifest = failing_persist
        try:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, migration_manifest)
        finally:
            MODULE._append_manifest = original_append
        self.assertEqual(code, 1)
        self.assertIn("persistence failed", stderr.getvalue())
        self.assertEqual((target / self.CONTROL).read_bytes(), prior, "the prior target was not restored")
        self.assertEqual((source / self.CONTROL).read_bytes(), incoming)
        self.assertEqual(migration_manifest.read_bytes(), b'{"prior": true}\n', "the prior manifest was not intact")
        self._assert_no_temp_siblings(target)
        # Retry: the restored prior target still matches the receipt, so the
        # replacement lands again and the replaced record becomes durable.
        code = _migrate(source, target, baseline, migration_manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / self.CONTROL).read_bytes(), incoming)
        data = json.loads(migration_manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["replaced"]], [self.CONTROL])
        self.assertTrue(data["prior"])

    # Task 1 checklist item 14: the escaping round trip.

    def test_migrate_roundtrips_pipe_quote_backslash_path(self):
        """[class: REPOSITORY_TEST] A receipt path containing a table pipe,
        a quote, and a backslash survives the token grammar: the serialized
        token carries the \\u007c escape and no literal pipe, and the
        replacement lands at the exact decoded path."""
        weird_rel = 'docs/tmp/pipe|quote"\\back.md'
        prior = b"prior weird bytes\n"
        incoming = b"incoming weird bytes\n"
        row = self._boundary_row([_file_receipt(weird_rel, _digest(prior))])
        token = row.split("mirror_receipts=", 1)[1]
        self.assertIn("\\u007c", token)
        self.assertNotIn("|", token)
        source, baseline, target = self._collision_case([row], weird_rel, prior, incoming)
        manifest = self.root / "closeout-migration.json"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = _migrate(source, target, baseline, manifest)
        self.assertEqual(code, 0)
        self.assertEqual((target / weird_rel).read_bytes(), incoming, "the decoded path was not replaced exactly")
        target_names = [path.name for path in (target / "docs/tmp").iterdir()]
        self.assertIn('pipe|quote"\\back.md', target_names)
        self.assertFalse(
            any(".wt-" in name for name in target_names),
            "the replacement produced a rename sibling",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["replaced"][0]["source"], weird_rel)
        self.assertEqual(data["replaced"][0]["destination"], (target.resolve() / weird_rel).as_posix())
        self.assertIn("replaced 1", buf.getvalue())


class BoundaryMirrorTest(unittest.TestCase):
    """Producer fixtures for the boundary-mirror operation (plan
    2026-10-24-closeout-migration-same-run-mirror-replace Task 2): one live
    operation holds the worktree-closeout-migrate merge lock from its
    try-once acquire through every staged mirror install and the atomic
    task_boundary manifest-row replacement, routes handled signals through
    the ordinary rollback and the token-fenced release, and on a refused
    acquire copies no primary files while recording one skipped item per
    planned path and no verified receipt."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    RUN_SESSION_ID = "sess-boundary-fixture-1"
    PLAN_PATH = "docs/history/plans/2026-10-24-boundary-fixture.md"
    SESSION_DIR_REL = "docs/tmp/execute-plan/boundary-fixture"

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-boundary-mirror-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        env = os.environ.copy()
        env.update(self.GIT_IDENTITY)
        subprocess.run(["git", "-C", str(self.primary), "init", "-q"], capture_output=True, env=env, check=True)
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\nreview_certs_dir = \".ai-playbook/review-certs/\"\n```\n",
        )
        (self.primary / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(DONE_LOCK_SCRIPT_PATH, self.primary / "scripts" / "done-lock.sh")
        subprocess.run(["git", "-C", str(self.primary), "add", "-A"], capture_output=True, env=env, check=True)
        subprocess.run(["git", "-C", str(self.primary), "commit", "-q", "-m", "init: fixture repo"], capture_output=True, env=env, check=True)
        self.merge_lock_root = self.root / "merge-locks"
        pins = _hermetic_lock_env(self.root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _seed_worktree(self, prior_rows: list[str] | None = None) -> tuple[Path, Path]:
        worktree = self.root / "run-worktree"
        manifest = worktree / self.SESSION_DIR_REL / "manifest.md"
        _write_session_manifest(
            manifest,
            list(prior_rows or []),
            run_worktree=str(worktree),
            run_session_id=self.RUN_SESSION_ID,
            plan_path=self.PLAN_PATH,
        )
        return worktree, manifest

    def _operation_argv(self, worktree: Path, manifest: Path, paths: list[str], note: str = "task 1 commit abc1234 verification: pass") -> list[str]:
        argv = [
            "boundary-mirror",
            "--worktree", str(worktree),
            "--target", str(self.primary),
            "--manifest", str(manifest),
            "--run-session-id", self.RUN_SESSION_ID,
            "--plan-path", self.PLAN_PATH,
            "--run-worktree", str(worktree),
            "--boundary-note", note,
        ]
        for rel in paths:
            argv += ["--mirror-path", rel]
        return argv

    def _run_operation_subprocess(self, worktree: Path, manifest: Path, paths: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *self._operation_argv(worktree, manifest, paths)],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root),
        )

    def _poplan_operation(self, worktree: Path, manifest: Path, paths: list[str]) -> subprocess.Popen:
        return subprocess.Popen(
            [sys.executable, str(SCRIPT_PATH), *self._operation_argv(worktree, manifest, paths)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(self.root), env=_hermetic_lock_env(self.root),
        )

    def _acquire_foreign_hold(self, label: str, holder_pid: int) -> dict[str, str]:
        acquired = subprocess.run(
            ["bash", str(self.primary / "scripts" / "done-lock.sh"), "merge-acquire", "--label", label],
            capture_output=True, text=True, cwd=str(self.primary),
            env=_hermetic_lock_env(self.root, MERGE_LOCK_HOLDER_PID=str(holder_pid)),
        )
        self.assertEqual(acquired.returncode, 0, acquired.stderr)
        exports: dict[str, str] = {}
        for line in acquired.stdout.splitlines():
            for name in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
                prefix = f"export {name}="
                if line.startswith(prefix):
                    exports[name] = line[len(prefix):]
        self.assertIn("MERGE_LOCK_DIR", exports)
        self.assertIn("MERGE_LOCK_TOKEN", exports)
        return exports

    def _release_hold(self, exports: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(self.primary / "scripts" / "done-lock.sh"), "merge-release"],
            capture_output=True, text=True, cwd=str(self.primary),
            env=_hermetic_lock_env(self.root, **exports),
        )

    def _boundary_rows(self, manifest_path: Path) -> list[str]:
        return [
            line.strip()
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("task_boundary:")
        ]

    def _temps_under(self, root: Path) -> list[str]:
        return sorted(path.name for path in root.rglob("*bndmirror*"))

    def test_boundary_mirror_installs_mirrors_and_records_verified_receipts(self):
        """[class: REPOSITORY_TEST] The happy path: every planned path
        installs at the primary, the primary manifest copy is the pre-row
        manifest (the receipt records the verified primary copy of
        manifest.md before this row), the appended row parses as complete
        with one verified item per path, and the lock releases."""
        worktree, manifest = self._seed_worktree()
        reviews_rel = ".ai-playbook/reviews/notes.md"
        sidecar_rel = ".ai-playbook/reviews/notes.md.stats.json"
        state_rel = self.SESSION_DIR_REL + "/runtime_state.json"
        manifest_rel = self.SESSION_DIR_REL + "/manifest.md"
        reviews_bytes = b"review notes one\n"
        sidecar_bytes = b'{"round": 1}\n'
        state_bytes = b'{"workflow_state": "active", "boundary": 1}\n'
        _write(worktree / reviews_rel, reviews_bytes)
        _write(worktree / sidecar_rel, sidecar_bytes)
        _write(worktree / state_rel, state_bytes)
        pre_row_manifest_bytes = manifest.read_bytes()
        _write(self.primary / state_rel, b'{"workflow_state": "active", "boundary": 0}\n')
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = MODULE.main(self._operation_argv(worktree, manifest, [reviews_rel, sidecar_rel, state_rel, manifest_rel]))
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual((self.primary / reviews_rel).read_bytes(), reviews_bytes)
        self.assertEqual((self.primary / sidecar_rel).read_bytes(), sidecar_bytes)
        self.assertEqual((self.primary / state_rel).read_bytes(), state_bytes)
        self.assertEqual(
            (self.primary / manifest_rel).read_bytes(),
            pre_row_manifest_bytes,
            "the primary manifest copy is not the verified pre-row manifest",
        )
        rows = self._boundary_rows(manifest)
        self.assertEqual(len(rows), 1)
        self.assertIn("task_boundary: task 1 commit abc1234 verification: pass; mirror_status=complete", rows[0])
        status, items = MODULE._parse_mirror_row(rows[0])
        self.assertEqual(status, "complete")
        by_path = {item["path"]: item for item in items}
        self.assertEqual(
            by_path[state_rel],
            {"path": state_rel, "status": "verified", "type": "file", "sha256": _digest(state_bytes)},
        )
        self.assertEqual(by_path[manifest_rel]["sha256"], _digest(pre_row_manifest_bytes))
        self.assertEqual(by_path[reviews_rel]["sha256"], _digest(reviews_bytes))
        self.assertEqual(by_path[sidecar_rel]["sha256"], _digest(sidecar_bytes))
        self.assertIn("merge-lock: held", err.getvalue(), "no held-span line at release")
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the merge lock was not released")
        self.assertEqual(self._temps_under(self.primary), [])
        self.assertEqual(self._temps_under(manifest.parent), [])

    def test_boundary_mirror_identity_mismatch_fails_before_any_copy(self):
        """[class: REPOSITORY_TEST] The passed stable run tuple must match
        the manifest identity block exactly; a mismatch fails loud (exit 2)
        before the lock, before any copy, and before any row."""
        worktree, manifest = self._seed_worktree()
        rel = ".ai-playbook/reviews/notes.md"
        _write(worktree / rel, b"review notes\n")
        argv = self._operation_argv(worktree, manifest, [rel])
        argv[argv.index("--run-session-id") + 1] = "sess-foreign-run"
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = MODULE.main(argv)
        self.assertEqual(code, 2)
        self.assertIn("stable tuple", err.getvalue())
        self.assertFalse((self.primary / rel).exists())
        self.assertEqual(self._boundary_rows(manifest), [])
        self.assertFalse(self.merge_lock_root.exists() and list(self.merge_lock_root.iterdir()), "the lock was taken")

    def test_boundary_mirror_lock_contention_records_skipped_row_and_copies_nothing(self):
        """[class: REPOSITORY_TEST] A try-once acquire refused by a live
        foreign hold (held well beyond the dead-holder grace by a live
        holder pid) copies no primary files, reports the existing copy
        error with the holder evidence, appends the local row with one
        status=skipped item per planned path and no verified receipts, and
        exits 0 so the boundary continues."""
        worktree, manifest = self._seed_worktree()
        rel_a = ".ai-playbook/reviews/notes.md"
        rel_b = self.SESSION_DIR_REL + "/runtime_state.json"
        _write(worktree / rel_a, b"review notes\n")
        _write(worktree / rel_b, b'{"boundary": 1}\n')
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        exports = self._acquire_foreign_hold("blocker", holder.pid)
        try:
            proc = self._run_operation_subprocess(worktree, manifest, [rel_a, rel_b])
        finally:
            released = self._release_hold(exports)
        self.assertEqual(released.returncode, 0, released.stderr)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("label: blocker", proc.stderr, "the refusal evidence was not reported")
        self.assertFalse((self.primary / rel_a).exists(), "a copy ran while the merge lock was held")
        self.assertFalse((self.primary / rel_b).exists(), "a copy ran while the merge lock was held")
        rows = self._boundary_rows(manifest)
        self.assertEqual(len(rows), 1)
        status, items = MODULE._parse_mirror_row(rows[0])
        self.assertEqual(status, "skipped")
        self.assertEqual(
            items,
            [
                {"path": rel_a, "status": "skipped"},
                {"path": rel_b, "status": "skipped"},
            ],
        )

    def test_boundary_mirror_partial_copy_failure_records_partial_row(self):
        """[class: REPOSITORY_TEST] A per-path copy error is contained the
        report-only way: the failed path records one failed item and keeps
        its prior target (r2 low-d: an existing prior target's bytes are
        retained unchanged), a capture-then-verification failure leaves no
        rollback-span residue (the appended entry is removed and the prior
        sibling unlinked), the earlier verified mirror stands, the row is
        partial, temps are removed, sources are retained, and the lock
        releases."""
        worktree, manifest = self._seed_worktree()
        ok_rel = ".ai-playbook/reviews/notes.md"
        bad_rel = ".ai-playbook/reviews/unreadable.md"
        bad2_rel = ".ai-playbook/reviews/unverifiable.md"
        ok_bytes = b"review notes\n"
        bad_bytes = b"unreadable bytes\n"
        bad2_prior = b"prior unverifiable target bytes\n"
        bad2_incoming = b"incoming unverifiable bytes\n"
        bad_prior = b"prior unreadable target bytes\n"
        _write(worktree / ok_rel, ok_bytes)
        _write(worktree / bad_rel, bad_bytes)
        _write(worktree / bad2_rel, bad2_incoming)
        _write(self.primary / bad_rel, bad_prior)
        _write(self.primary / bad2_rel, bad2_prior)
        os.chmod(worktree / bad_rel, 0o000)
        self.addCleanup(os.chmod, worktree / bad_rel, 0o644)
        original_verify = MODULE._verify_copy
        bad2_src = (worktree / bad2_rel).resolve()

        def unverifiable_verify(src, dst):
            if src == bad2_src:
                return False
            return original_verify(src, dst)

        MODULE._verify_copy = unverifiable_verify
        try:
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = MODULE.main(self._operation_argv(worktree, manifest, [ok_rel, bad_rel, bad2_rel]))
        finally:
            MODULE._verify_copy = original_verify
        self.assertEqual(code, 1)
        self.assertIn("copy error", err.getvalue())
        self.assertIn("unreadable.md", err.getvalue())
        self.assertIn("unverifiable.md", err.getvalue())
        self.assertEqual((self.primary / ok_rel).read_bytes(), ok_bytes, "the verified mirror did not stand")
        self.assertEqual((self.primary / bad_rel).read_bytes(), bad_prior, "the failing path's prior target was not retained")
        self.assertEqual((self.primary / bad2_rel).read_bytes(), bad2_prior, "the capture-then-failure path's prior target was not retained")
        rows = self._boundary_rows(manifest)
        self.assertEqual(len(rows), 1)
        status, items = MODULE._parse_mirror_row(rows[0])
        self.assertEqual(status, "partial")
        self.assertEqual(
            items,
            [
                {"path": ok_rel, "status": "verified", "type": "file", "sha256": _digest(ok_bytes)},
                {"path": bad_rel, "status": "failed"},
                {"path": bad2_rel, "status": "failed"},
            ],
        )
        self.assertEqual(list(self.merge_lock_root.iterdir()), [])
        self.assertEqual(self._temps_under(self.primary), [], "a prior or staged sibling leaked on a handled failure")
        self.assertEqual(os.stat(worktree / bad_rel).st_size, len(bad_bytes), "the worktree source was not retained")
        self.assertEqual((worktree / bad2_rel).read_bytes(), bad2_incoming, "the worktree source was not retained")

    def test_boundary_mirror_manifest_install_failure_restores_prior_targets(self):
        """[class: REPOSITORY_TEST] An atomic manifest-install failure after
        mirrors installed rolls the whole transaction back: prior primary
        targets restored, the fresh manifest mirror removed, the prior
        manifest bytes intact with no receipt row, temps removed, sources
        retained, and the lock released."""
        worktree, manifest = self._seed_worktree()
        state_rel = ".ai-playbook/reviews/runtime_state.json"
        manifest_rel = self.SESSION_DIR_REL + "/manifest.md"
        prior_primary = b'{"boundary": 0}\n'
        incoming = b'{"boundary": 1}\n'
        _write(worktree / state_rel, incoming)
        _write(self.primary / state_rel, prior_primary)
        manifest.parent.chmod(0o500)
        self.addCleanup(manifest.parent.chmod, 0o755)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = MODULE.main(self._operation_argv(worktree, manifest, [state_rel, manifest_rel]))
        self.assertEqual(code, 1)
        self.assertIn("boundary-mirror rolled back", err.getvalue())
        self.assertEqual((self.primary / state_rel).read_bytes(), prior_primary, "the prior primary target was not restored")
        self.assertFalse((self.primary / manifest_rel).exists(), "the fresh manifest mirror survived the rollback")
        self.assertEqual(self._boundary_rows(manifest), [], "the prior manifest bytes did not stand")
        self.assertEqual(list(self.merge_lock_root.iterdir()), [])
        self.assertEqual(self._temps_under(self.primary), [])
        self.assertEqual(self._temps_under(manifest.parent), [])
        self.assertEqual((worktree / state_rel).read_bytes(), incoming, "the worktree source was not retained")

    @staticmethod
    def _kill_process(proc: subprocess.Popen) -> None:
        """Post-failure cleanup for the FIFO signal fixtures: a pre-signal
        assertion must not leak a child parked on the FIFO source."""
        if proc.poll() is None:
            proc.kill()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass

    def _signal_delivery_case(self, sig: int) -> None:
        repl_rel = ".ai-playbook/reviews/runtime_state.json"
        prior_primary = b'{"boundary": 0}\n'
        # The task-0 prior row carries one non-empty verified receipt item
        # (this same path's prior boundary mirror), so the rollback
        # assertion proves receipt history still parses after the restore.
        worktree, manifest = self._seed_worktree(
            prior_rows=[
                "task_boundary: task 0 commit 0000000 verification: pass; mirror_status=complete "
                "mirror_receipts=" + _receipts_token([_file_receipt(repl_rel, _digest(prior_primary))])
            ]
        )
        fresh_rel = self.SESSION_DIR_REL + "/boundary-1.log.md"
        fifo_rel = ".ai-playbook/reviews/never-arrives.md"
        repl_bytes = b'{"boundary": 1}\n'
        fresh_bytes = b"boundary log one\n"
        _write(worktree / repl_rel, repl_bytes)
        _write(worktree / fresh_rel, fresh_bytes)
        _write(self.primary / repl_rel, prior_primary)
        os.mkfifo(worktree / fifo_rel)

        def _drop_fifo() -> None:
            try:
                (worktree / fifo_rel).unlink()
            except OSError:
                pass

        self.addCleanup(_drop_fifo)
        pre_manifest_bytes = manifest.read_bytes()
        pre_rows = self._boundary_rows(manifest)
        self.assertEqual(len(pre_rows), 1)
        paths = [repl_rel, fresh_rel, fifo_rel]
        # The FIFO source parks the operation inside the mirror loop, after
        # the first two installs and before the receipt replacement, so the
        # signal delivery point is deterministic.
        proc = self._poplan_operation(worktree, manifest, paths)
        self.addCleanup(self._kill_process, proc)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if (self.primary / fresh_rel).exists():
                    break
                if proc.poll() is not None:
                    self.fail(f"the operation exited before the second mirror installed: {proc.communicate()}")
                time.sleep(0.02)
            else:
                proc.kill()
                self.fail("the second mirror never installed")
            self.assertEqual(
                len(self._boundary_rows(manifest)),
                1,
                "the receipt row landed before the signal",
            )
            proc.send_signal(sig)
        finally:
            out, err = proc.communicate(timeout=30)
        text = (out + err).decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 1, text)
        self.assertIn("interrupted", err.decode("utf-8", "replace"))
        self.assertEqual((self.primary / repl_rel).read_bytes(), prior_primary, "rollback did not restore the prior primary bytes")
        self.assertFalse((self.primary / fresh_rel).exists(), "the fresh install survived the rollback")
        self.assertFalse((self.primary / fifo_rel).exists())
        self.assertEqual(manifest.read_bytes(), pre_manifest_bytes, "the prior manifest bytes did not stand")
        status, items = MODULE._parse_mirror_row(self._boundary_rows(manifest)[0])
        self.assertEqual(status, "complete", "the earlier receipts stopped being parseable")
        self.assertEqual(
            items,
            [_file_receipt(repl_rel, _digest(prior_primary))],
            "the seeded task-0 receipt did not survive the rollback parseable",
        )
        self.assertEqual((worktree / repl_rel).read_bytes(), repl_bytes, "the worktree source was not retained")
        self.assertEqual((worktree / fresh_rel).read_bytes(), fresh_bytes, "the worktree source was not retained")
        self.assertEqual(self._temps_under(self.primary), [])
        self.assertEqual(self._temps_under(manifest.parent), [])
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the lock did not release")
        # Retry after the blocked source is replaceable succeeds end to end.
        _drop_fifo()
        _write(worktree / fifo_rel, b"late bytes\n")
        err_buf = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err_buf):
            code = MODULE.main(self._operation_argv(worktree, manifest, paths))
        self.assertEqual(code, 0, err_buf.getvalue())
        self.assertEqual((self.primary / repl_rel).read_bytes(), repl_bytes)
        self.assertEqual((self.primary / fifo_rel).read_bytes(), b"late bytes\n")
        rows = self._boundary_rows(manifest)
        self.assertEqual(len(rows), 2)
        status, items = MODULE._parse_mirror_row(rows[-1])
        self.assertEqual(status, "complete")
        self.assertEqual(len(items), 3)
        self.assertEqual(list(self.merge_lock_root.iterdir()), [])

    def test_boundary_mirror_sigint_rolls_back_releases_and_retries(self):
        """[class: REPOSITORY_TEST] SIGINT delivered after the lock acquire
        and after one primary mirror installs but before the receipt
        replacement routes through the ordinary rollback and the token-
        fenced release, and the retry succeeds."""
        self._signal_delivery_case(signal.SIGINT)

    def test_boundary_mirror_sigterm_rolls_back_releases_and_retries(self):
        """[class: REPOSITORY_TEST] SIGTERM takes the same handled-signal
        route as SIGINT: rollback restores prior primary and manifest
        bytes, the lock releases, and the retry succeeds."""
        self._signal_delivery_case(signal.SIGTERM)

    def test_boundary_mirror_note_carrying_mirror_tokens_is_refused(self):
        """[class: REPOSITORY_TEST] r2 F1: a --boundary-note carrying the
        mirror_status= or mirror_receipts= substring is refused with exit 2
        before the lock and before any copy; the consumer keys the terminal
        tokens on first occurrence, so a note-carried token would forge or
        corrupt receipt history."""
        worktree, manifest = self._seed_worktree()
        rel = ".ai-playbook/reviews/notes.md"
        _write(worktree / rel, b"review notes\n")
        for token in ("mirror_status=", "mirror_receipts="):
            argv = self._operation_argv(worktree, manifest, [rel], note=f"task 1 {token}complete forged")
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = MODULE.main(argv)
            self.assertEqual(code, 2)
            self.assertIn(token, err.getvalue())
            self.assertFalse((self.primary / rel).exists(), "a copy ran for a refused note")
            self.assertEqual(self._boundary_rows(manifest), [], "a row landed for a refused note")
            self.assertEqual(self._temps_under(self.primary), [])
            self.assertFalse(
                self.merge_lock_root.exists() and list(self.merge_lock_root.iterdir()),
                "the lock was taken for a refused note",
            )

    def test_boundary_mirror_interrupt_between_capture_and_install_restores_captured_prior(self):
        """[class: REPOSITORY_TEST] r2 F2: the rollback-span entry rides
        `priors` from the capture onward, so a handled signal raising
        between the prior capture and the staged install unwinds with the
        entry addressable: the prior sibling is consumed by the restore and
        the staged sibling is removed, leaving no temp residue and the
        prior target bytes standing."""
        worktree, manifest = self._seed_worktree()
        repl_rel = ".ai-playbook/reviews/runtime_state.json"
        prior_primary = b'{"boundary": 0}\n'
        repl_bytes = b'{"boundary": 1}\n'
        _write(worktree / repl_rel, repl_bytes)
        _write(self.primary / repl_rel, prior_primary)
        pre_manifest_bytes = manifest.read_bytes()
        original_install = MODULE._install_staged

        def interrupted_install(temp, dst):
            raise MODULE._BoundaryMirrorInterrupt(signal.SIGINT)

        MODULE._install_staged = interrupted_install
        try:
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = MODULE.main(self._operation_argv(worktree, manifest, [repl_rel]))
        finally:
            MODULE._install_staged = original_install
        self.assertEqual(code, 1)
        self.assertIn("interrupted", err.getvalue())
        self.assertEqual((self.primary / repl_rel).read_bytes(), prior_primary, "the prior target did not stand")
        self.assertEqual(manifest.read_bytes(), pre_manifest_bytes, "a row landed for an interrupted run")
        self.assertEqual(self._temps_under(self.primary), [], "the captured prior or staged sibling leaked")
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the lock did not release")
        self.assertEqual((worktree / repl_rel).read_bytes(), repl_bytes, "the worktree source was not retained")

    def test_commit_window_signal_block_holds_pending_until_unblock(self):
        """[class: REPOSITORY_TEST] r2 F2: across the manifest
        os.replace-to-commit pair the handled signals are blocked, so a
        signal delivered in that window stays pending (no handler can
        unwind a durable row) and surfaces at the unblock as the captured
        boundary interrupt with the mask restored."""
        if not hasattr(signal, "pthread_sigmask"):
            self.skipTest("pthread_sigmask unavailable on this platform")
        self.assertTrue(MODULE._install_boundary_signal_handlers())
        self.addCleanup(MODULE._restore_boundary_signal_handlers)
        try:
            self.assertTrue(MODULE._block_commit_window_signals())
            os.kill(os.getpid(), signal.SIGINT)
            # Still running here: the delivered signal is pending, not handled.
            self.assertIn(signal.SIGINT, signal.pthread_sigmask(signal.SIG_BLOCK, []))
        finally:
            captured = MODULE._unblock_commit_window_signals()
        self.assertIsInstance(captured, MODULE._BoundaryMirrorInterrupt)
        self.assertEqual(captured.signum, signal.SIGINT)
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, [])
        self.assertNotIn(signal.SIGINT, mask)
        self.assertNotIn(signal.SIGTERM, mask)

    def test_boundary_mirror_roundtrips_pipe_quote_backslash_path(self):
        """[class: REPOSITORY_TEST] The producer side of the \\u007c grammar
        end to end: a planned path containing a table pipe, a quote, and a
        backslash installs at the exact decoded path and its receipt rides
        the row as the \\u007c escape with no literal pipe, parseable by
        the migration consumer."""
        worktree, manifest = self._seed_worktree()
        weird_rel = 'docs/tmp/weird/pipe|quote"\\back.md'
        weird_bytes = b"weird boundary bytes\n"
        _write(worktree / weird_rel, weird_bytes)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = MODULE.main(self._operation_argv(worktree, manifest, [weird_rel]))
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual((self.primary / weird_rel).read_bytes(), weird_bytes, "the decoded path did not install exactly")
        rows = self._boundary_rows(manifest)
        self.assertEqual(len(rows), 1)
        token = rows[0].split("mirror_receipts=", 1)[1]
        self.assertIn("\\u007c", token)
        self.assertNotIn("|", token)
        status, items = MODULE._parse_mirror_row(rows[0])
        self.assertEqual(status, "complete")
        self.assertEqual(
            items,
            [{"path": weird_rel, "status": "verified", "type": "file", "sha256": _digest(weird_bytes)}],
        )
        self.assertEqual(self._temps_under(self.primary), [])
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the lock did not release")


class VerifyRecordsTest(unittest.TestCase):
    """Fixtures for the verify-records subcommand (cited/claimed record
    resolution against the target's primary reviews home)."""

    def _repo(self, root: Path, with_facts: bool = True) -> Path:
        repo = root / "repo"
        repo.mkdir(parents=True)
        if with_facts:
            _write(
                repo / ".ai-playbook/facts.md",
                b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
            )
        return repo

    def _plan(self, repo: Path, body: str) -> Path:
        plan = repo / "docs/history/plans/2026-10-06-x.md"
        _write(plan, body.encode("utf-8"))
        return plan

    def _run_verify(self, *args: str, cwd: Path) -> tuple[int, str, str]:
        return _run_cli("verify-records", *args, cwd=cwd)

    def test_worktree_bound_failure_names_missing_primary_path(self):
        # record exists only under the SOURCE tree's reviews home (the
        # worktree-bound shape): the check against the target must exit 1
        # naming the missing primary-home path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-x-r2.md\n",
            )
            _write(repo / ".ai-playbook/reviews/2026-10-06-plan-review-x-r2.md", b"r2\n")
            other = self._repo(root / "elsewhere")  # target without the record
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(other), cwd=repo
            )
            self.assertEqual(code, 1)
            self.assertIn("missing under", err)
            self.assertIn(str(other.resolve() / ".ai-playbook/reviews/2026-10-06-plan-review-x-r2.md"), err)
            self.assertIn("2026-10-06-plan-review-x-r2.md", err)
            data = json.loads(out)
            self.assertIn(
                str(other.resolve() / ".ai-playbook/reviews/2026-10-06-plan-review-x-r2.md"),
                data["missing"],
            )

    def test_both_homes_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-y-r1.md\n",
            )
            _write(repo / ".ai-playbook/reviews/2026-10-06-plan-review-y-r1.md", b"r1\n")
            target = self._repo(root / "primary")
            _write(target / ".ai-playbook/reviews/2026-10-06-plan-review-y-r1.md", b"r1\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["missing"], [])
            self.assertEqual(len(data["checked"]), 1)

    def test_series_r1_only_passes_with_r1_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-z-r*.md (the highest rN is the authoritative record)\n",
            )
            target = self._repo(root / "primary")
            _write(target / ".ai-playbook/reviews/2026-10-06-plan-review-z-r1.md", b"r1\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["series_witness"], {
                ".ai-playbook/reviews/2026-10-06-plan-review-z-r*.md":
                    "2026-10-06-plan-review-z-r1.md"
            })

    def test_series_zero_members_fail_naming_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-w-r*.md\n",
            )
            target = self._repo(root / "primary")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 1)
            self.assertIn("2026-10-06-plan-review-w-r*.md", err)
            self.assertIn("zero members", err)

    def test_series_highest_round_is_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-h-r*.md\n",
            )
            target = self._repo(root / "primary")
            home = target / ".ai-playbook/reviews"
            _write(home / "2026-10-06-plan-review-h-r1.md", b"r1\n")
            _write(home / "2026-10-06-plan-review-h-r3.md", b"r3\n")
            _write(home / "2026-10-06-plan-review-h-r2.md", b"r2\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            witness = list(data["series_witness"].values())[0]
            self.assertEqual(witness, "2026-10-06-plan-review-h-r3.md")

    def test_concrete_rn_citation_checked_as_exact_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nSee .ai-playbook/reviews/2026-10-06-plan-review-e-r3.md for the certified round.\n",
            )
            target = self._repo(root / "primary")
            # only r2 present: the concrete r3 citation is exact and missing
            _write(target / ".ai-playbook/reviews/2026-10-06-plan-review-e-r2.md", b"r2\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 1)
            self.assertIn("2026-10-06-plan-review-e-r3.md", err)

    def test_vacuous_pass_no_citations_no_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(repo, "# Plan\n\nNo review rounds.\n")
            target = self._repo(root / "primary")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["checked"], [])
            self.assertEqual(data["missing"], [])

    def test_missing_plan_exit2_names_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            absent = repo / "docs/history/plans/not-there.md"
            target = self._repo(root / "primary")
            code, out, err = self._run_verify(
                "--plan", str(absent), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 2)
            self.assertIn(str(absent), err)

    def test_unresolvable_facts_exit2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root, with_facts=False)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-q-r1.md\n",
            )
            target = self._repo(root / "primary", with_facts=False)
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo
            )
            self.assertEqual(code, 2)
            self.assertIn("reviews_dir", err)
            self.assertIn(".ai-playbook/facts.md", err)

    def test_claims_file_outside_entry_skipped_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(repo, "# Plan\n\nNo citations.\n")
            target = self._repo(root / "primary")
            _write(target / ".ai-playbook/reviews/claimed-r1.md", b"claimed\n")
            _write(target / "docs/elsewhere/not-a-review.md", b"other\n")
            claims = root / "claims.txt"
            claims.write_text(
                ".ai-playbook/reviews/claimed-r1.md\ndocs/elsewhere/not-a-review.md\n",
                encoding="utf-8",
            )
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target),
                "--claims", str(claims), cwd=repo,
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(len(data["checked"]), 1)
            self.assertEqual(len(data["skipped"]), 1)
            self.assertIn("outside the reviews home", err)

    def test_absent_claims_path_exit2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(repo, "# Plan\n\nNo citations.\n")
            target = self._repo(root / "primary")
            absent = root / "no-such-claims.txt"
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target),
                "--claims", str(absent), cwd=repo,
            )
            self.assertEqual(code, 2)
            self.assertIn(str(absent), err)

    def test_folded_origin_prose_paths_ignored_owned_record_checked(self):
        # the witnessed folded-origin closeout shape: a plan body citing
        # many nonexistent prose paths (folded backlog rows, archived
        # plans, tmp baselines) while its owned record is present exits 0
        # so the closeout proceeds to teardown
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-o-r*.md\n"
                "Backlog origin: docs/history/backlog/2026-10-01-folded-row.md\n"
                "Basis: docs/history/plans/completed/2026-10-02-archived-plan.md\n"
                "Baseline: docs/tmp/2026-10-03-closeout-baseline.json\n",
            )
            target = self._repo(root / "primary")
            _write(target / ".ai-playbook/reviews/2026-10-06-plan-review-o-r1.md", b"r1\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["missing"], [])
            self.assertEqual(len(data["checked"]), 1)

    def test_false_miss_prose_citations_ignored_present_owned_checked(self):
        # given a plan citing its present owned round record plus
        # nonexistent backlog, archived-plan, and tmp paths: exit 0 with
        # the owned record checked and an empty missing list
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-m-r2.md\n"
                "See docs/history/backlog/2026-10-01-gone.md and "
                "docs/history/plans/completed/2026-10-02-gone.md and "
                "docs/tmp/2026-10-03-gone.json for context.\n",
            )
            target = self._repo(root / "primary")
            _write(target / ".ai-playbook/reviews/2026-10-06-plan-review-m-r2.md", b"r2\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["missing"], [])
            self.assertEqual(data["checked"], [".ai-playbook/reviews/2026-10-06-plan-review-m-r2.md"])

    def test_absolute_token_outside_home_ignored_no_crash(self):
        # given a plan body citing an absolute path token outside the
        # reviews home: exit 0 with every list empty and no traceback
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            outside = root / "elsewhere" / "note.md"
            outside.parent.mkdir(parents=True)
            _write(outside, b"note\n")
            plan = self._plan(repo, f"# Plan\n\nBasis: {outside}\n")
            target = self._repo(root / "primary")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 0)
            self.assertNotIn("Traceback", err)
            data = json.loads(out)
            self.assertEqual(data["checked"], [])
            self.assertEqual(data["missing"], [])
            self.assertEqual(data["skipped"], [])
            self.assertEqual(data["series_witness"], {})

    def test_absolute_token_under_home_present_checked_never_basename(self):
        # given an absolute path token whose file exists under the reviews
        # home: exit 0 with the token checked, never basename-verified
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            target = self._repo(root / "primary")
            record = target / ".ai-playbook/reviews/2026-10-06-plan-review-a-r1.md"
            _write(record, b"r1\n")
            plan = self._plan(repo, f"# Plan\n\nPlan review record: {record}\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["checked"], [str(record)])
            self.assertEqual(data["missing"], [])

    def test_absolute_token_under_home_absent_names_absolute_no_substitution(self):
        # given an absolute path token under the reviews home whose file is
        # absent, the token living in a home subdirectory while a different
        # existing file of the same basename sits at the home root: exit 1
        # naming the exact absolute path with no basename substitution
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            target = self._repo(root / "primary")
            home = target / ".ai-playbook/reviews"
            (home / "sub").mkdir(parents=True)
            _write(home / "2026-10-06-plan-review-b-r1.md", b"decoy\n")
            absent_token = home / "sub" / "2026-10-06-plan-review-b-r1.md"
            plan = self._plan(repo, f"# Plan\n\nPlan review record: {absent_token}\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 1)
            self.assertIn(str(absent_token), err)
            data = json.loads(out)
            self.assertEqual(data["missing"], [str(absent_token)])

    def test_missing_declared_record_survives_naming_home_path(self):
        # given a target-relative citation under the reviews home whose
        # file is absent: exit 1 naming the exact home path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-c-r1.md\n",
            )
            target = self._repo(root / "primary")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 1)
            expected = str(target.resolve() / ".ai-playbook/reviews/2026-10-06-plan-review-c-r1.md")
            self.assertIn(expected, err)
            data = json.loads(out)
            self.assertEqual(data["missing"], [expected])

    def test_existing_basename_identified_and_checked(self):
        # given a bare-basename token matching an existing review file at
        # the home: exit 0 with the token checked
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo, "# Plan\n\nRecorded in 2026-10-06-plan-review-d-r1.md.\n"
            )
            target = self._repo(root / "primary")
            _write(target / ".ai-playbook/reviews/2026-10-06-plan-review-d-r1.md", b"r1\n")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["checked"], ["2026-10-06-plan-review-d-r1.md"])
            self.assertEqual(data["missing"], [])

    def test_resolved_containment_symlinked_home_and_dotdot_citation(self):
        # (a) a facts reviews_dir that is an absolute path through a
        # symlink and a target-relative citation whose file is absent:
        # exit 1 naming the home path; (b) a ..-bearing citation that
        # lands under the home after resolution with the file absent:
        # exit 1
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_home = root / "real-home"
            (real_home / "reviews").mkdir(parents=True)
            link = root / "link-home"
            link.symlink_to(real_home)
            repo = root / "repo"
            repo.mkdir()
            _write(
                repo / ".ai-playbook/facts.md",
                f"```toml\nreviews_dir = \"{link / 'reviews'}\"\n```\n".encode("utf-8"),
            )
            plan = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-06-plan-review-s-r1.md\n",
            )
            target = root / "primary-target"
            (target / ".ai-playbook").mkdir(parents=True)
            # the target's reviews dir routes through the symlinked home
            (target / ".ai-playbook/reviews").symlink_to(real_home / "reviews")
            _write(
                target / ".ai-playbook/facts.md",
                f"```toml\nreviews_dir = \"{link / 'reviews'}\"\n```\n".encode("utf-8"),
            )
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 1)
            self.assertIn("2026-10-06-plan-review-s-r1.md", err)
            # (b) the ..-bearing citation landing under the home after
            # resolution, file absent
            plan2 = self._plan(
                repo,
                "# Plan\n\nPlan review record: .ai-playbook/reviews/../reviews/2026-10-06-plan-review-t-r1.md\n",
            )
            code, out, err = self._run_verify(
                "--plan", str(plan2), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 1)
            self.assertIn("2026-10-06-plan-review-t-r1.md", err)

    def test_escape_token_past_home_ignored(self):
        # given a ..-threaded citation escaping past the reviews home whose
        # basename matches no home file: the ignored disposition, exit 0
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(
                repo,
                "# Plan\n\nBasis: .ai-playbook/reviews/../../../elsewhere/2026-10-06-gone.md\n",
            )
            target = self._repo(root / "primary")
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target), cwd=repo,
            )
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(data["checked"], [])
            self.assertEqual(data["missing"], [])

    def test_claims_inside_entries_must_exist_present_checked(self):
        # claims-arm witness: one inside-home absent entry and one present
        # inside-home entry: exit 1 with the absent entry in missing naming
        # the target-anchored path, the present entry in checked, and an
        # empty skipped list
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._repo(root)
            plan = self._plan(repo, "# Plan\n\nNo citations.\n")
            target = self._repo(root / "primary")
            _write(target / ".ai-playbook/reviews/present-r1.md", b"present\n")
            claims = root / "claims.txt"
            claims.write_text(
                ".ai-playbook/reviews/present-r1.md\n"
                ".ai-playbook/reviews/absent-r9.md\n",
                encoding="utf-8",
            )
            code, out, err = self._run_verify(
                "--plan", str(plan), "--target", str(target),
                "--claims", str(claims), cwd=repo,
            )
            self.assertEqual(code, 1)
            data = json.loads(out)
            self.assertIn(
                str(target.resolve() / ".ai-playbook/reviews/absent-r9.md"),
                data["missing"],
            )
            self.assertIn(".ai-playbook/reviews/present-r1.md", data["checked"])
            self.assertEqual(data["skipped"], [])


class GateRemovalTest(unittest.TestCase):
    """Fixtures for the gate-removal subcommand (the worktree-removal
    migration gate): a temp-dir scratch pair of a session worktree and the
    primary home, exercising the refuse, pass, and tool-error arms."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-gate-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.worktree = self._scratch_pair_member(self.root / "wt-session")
        self.primary = self._scratch_pair_member(self.root / "primary")

    def _scratch_pair_member(self, path: Path) -> Path:
        # One member of the scratch pair: a facts-resolved checkout-shaped
        # directory (the gate reads only the facts block and the reviews
        # home; it never invokes git, so a gitless fixture is faithful).
        path.mkdir(parents=True)
        _write(
            path / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        return path

    def _plan(self, body: str) -> Path:
        plan = self.worktree / "docs/history/plans/2026-10-07-x.md"
        _write(plan, body.encode("utf-8"))
        return plan

    def _run_gate(self, plan: Path, *extra: str) -> tuple[int, str, str]:
        return _run_cli(
            "gate-removal",
            "--plan", str(plan),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            *extra,
            cwd=self.worktree,
        )

    def test_refuse_names_missing_record_repo_relative(self):
        # The record exists only under the worktree's reviews home; the
        # primary home lacks it, so the removal is refused with the missing
        # path rendered repo-relative (never absolute) and the migrate remedy.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.worktree / record, b"r1\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {record}", out)
        self.assertNotIn(str(self.primary), out, "missing path rendered absolute")
        self.assertNotIn(str(self.worktree), out, "refuse output leaked an absolute path")
        self.assertIn("worktree_closeout_migrate.py migrate", out)

    def test_pass_prints_sanctioned_removal_command(self):
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        # An on-disk worktree gets the sanctioned removal command, with the
        # operand echoed exactly as given (plan gate-removal-closeout-
        # accounting Task 2: the cleanup line stays truthful about what
        # exists on disk).
        (self.worktree.parent / "ai-playbook-wt-x").mkdir()
        code, out, err = self._run_gate(plan, "--worktree", "../ai-playbook-wt-x")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        removal_lines = [ln for ln in out.strip().splitlines() if "git worktree remove" in ln]
        self.assertEqual(removal_lines, ["removal: git worktree remove --force ../ai-playbook-wt-x"])
        # A path absent from disk is a stale registration: the pass names
        # the scoped administrative drain instead of a removal command that
        # would fail.
        shutil.rmtree(self.worktree.parent / "ai-playbook-wt-x")
        code, out, err = self._run_gate(plan, "--worktree", "../ai-playbook-wt-x")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertNotIn("git worktree remove", out)
        self.assertIn("no on-disk worktree at ../ai-playbook-wt-x", out)
        self.assertIn("stale", out)

    def test_pass_series_with_member_under_primary_home(self):
        # The production header shape: a series pattern whose highest member
        # is the witness; one member under the primary home verifies the series.
        plan = self._plan(
            "# Plan\n\nPlan review record: the staging series "
            ".ai-playbook/reviews/2026-10-07-plan-review-s-r*.md "
            "(the highest rN is the authoritative record, including any deferred-residual list)\n"
        )
        _write(self.primary / ".ai-playbook/reviews/2026-10-07-plan-review-s-r2.md", b"r2\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")

    def test_refuse_empty_owned_set_names_absent_header_line(self):
        # The fail-closed arm: no header citations and no claims is a refuse,
        # never a vacuous pass; the line names the absent header label and
        # carries the empty-set remedy (plan
        # 2026-10-27-gate-removal-empty-owned-set-remedy Task 1): the
        # citation or claims-file input that can make the set non-empty,
        # never the capture-and-migrate remedy; no migrate run can create
        # the missing inputs.
        plan = self._plan("# Plan\n\nNo review rounds.\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("empty owned set", out)
        self.assertIn("Plan review record", out)
        self.assertIn(
            "remedy: no migrate run can create the missing inputs", out,
            "empty-set refusal carried no attainable-input remedy",
        )
        self.assertIn("Plan review record:/Plan review: citation", out)
        self.assertIn("--claims file listing review-record paths", out)
        self.assertIn("then re-run gate-removal", out)
        self.assertNotIn(
            "worktree_closeout_migrate.py capture", out,
            "empty-set refusal carried the capture-and-migrate remedy",
        )
        self.assertNotIn(
            "worktree_closeout_migrate.py migrate", out,
            "empty-set refusal carried a migrate-command remedy",
        )

    def test_refuse_claims_entry_outside_reviews_home(self):
        # A claims entry outside the reviews home is refused with its path,
        # never skipped, even while the inside entry verifies.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        _write(self.primary / "docs/elsewhere/not-a-review.md", b"other\n")
        claims = self.root / "claims.txt"
        claims.write_text(
            f"{record}\ndocs/elsewhere/not-a-review.md\n",
            encoding="utf-8",
        )
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("docs/elsewhere/not-a-review.md", out)
        self.assertIn("outside the reviews home", out)

    def test_body_never_scanned_label_lines_only(self):
        # Only label lines contribute owned citations: a prose mention of an
        # absent record outside any label line must not fail the gate.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {record}\n"
            "\n"
            "Background: .ai-playbook/reviews/2026-10-07-plan-review-x-r9.md "
            "is mentioned in prose only and must stay unowned.\n"
        )
        _write(self.primary / record, b"r1\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")

    def test_plan_review_label_variant_is_extracted(self):
        record = ".ai-playbook/reviews/2026-10-07-plan-review-y-r2.md"
        plan = self._plan(f"# Plan\n\nPlan review: {record}\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertIn(f"missing: {record}", out)

    def test_series_zero_members_refuses_naming_pattern(self):
        plan = self._plan(
            "# Plan\n\nPlan review record: "
            ".ai-playbook/reviews/2026-10-07-plan-review-w-r*.md\n"
        )
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("missing: .ai-playbook/reviews/2026-10-07-plan-review-w-r*.md", out)

    def test_tool_error_missing_plan(self):
        absent = self.worktree / "docs/history/plans/not-there.md"
        code, out, err = self._run_gate(absent)
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("not found", err)

    def test_tool_error_unresolvable_target_reviews_home(self):
        # A --target whose facts block cannot resolve the reviews home is a
        # tool error, not a refuse.
        plan = self._plan(
            "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-07-plan-review-x-r1.md\n"
        )
        bare = self.root / "bare-primary"
        bare.mkdir()
        code, out, err = self._run_gate(plan, "--target", str(bare))
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("reviews_dir", err)

    def test_tool_error_missing_claims_file(self):
        plan = self._plan(
            "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-07-plan-review-x-r1.md\n"
        )
        absent = self.root / "no-such-claims.txt"
        code, out, err = self._run_gate(plan, "--claims", str(absent))
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("claims file not found", err)

    def test_usage_violation_is_tool_error_exit3(self):
        # The argparse override scoped to gate-removal: a missing required
        # argument exits 3 with the final OUTCOME line, not the legacy exit 2.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "gate-removal",
             "--target", str(self.primary), "--worktree", "../wt"],
            capture_output=True, text=True, cwd=str(self.worktree),
        )
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("usage", proc.stderr)

    def test_legacy_subcommand_usage_exit_stays_2(self):
        # The override is scoped to gate-removal: a legacy subcommand's usage
        # violation keeps the argparse exit (byte-unchanged behavior).
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "migrate", "--nope"],
            capture_output=True, text=True, cwd=str(self.worktree),
        )
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("OUTCOME:", proc.stdout)

    def test_standalone_help_presents_gate_removal_once(self):
        # Plan gate-removal-closeout-accounting Task 4: the flattened
        # parser renders the dispatch token exactly once (the baseline
        # defect printed "gate-removal gate-removal" in the usage line)
        # and --help stays a metadata exit with no OUTCOME line.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "gate-removal", "--help"],
            capture_output=True, text=True, cwd=str(self.worktree),
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("usage:", proc.stdout)
        self.assertNotIn("OUTCOME:", proc.stdout)
        self.assertEqual(proc.stdout.count("gate-removal"), 1)
        self.assertNotIn("gate-removal gate-removal", proc.stdout)

    def test_refuse_absolute_label_citation_to_existing_file_outside_primary_home(self):
        # The F1 loss class: an absolute label citation whose file exists
        # OUTSIDE the primary home (here the worktree's own staging copy)
        # must be refused, never verified through the pathlib join discard
        # that would land the check on the cited file itself; the refusal
        # renders repo-relative or basename, never the absolute path, and
        # carries the citation-correction remedy (a never-verifiable
        # citation: no migrate run can satisfy it).
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {self.worktree.resolve() / record}\n"
        )
        _write(self.worktree / record, b"r1 staged in the worktree only\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused: label citation outside the reviews home:", out)
        self.assertIn("2026-10-07-plan-review-x-r1.md", out)
        self.assertNotIn(str(self.primary), out)
        self.assertNotIn(str(self.primary.resolve()), out)
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertIn(MODULE._GATE_CITATION_REMEDY_LINE, out)
        self.assertNotIn("worktree_closeout_migrate.py migrate", out)

    def test_refuse_absolute_label_citation_resolving_under_primary_home(self):
        # An absolute citation cannot be trusted to be repo-relative: even
        # when it resolves under the primary home (the pathlib join would
        # discard the home operand), it is refused, rendered repo-relative.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-y-r2.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {self.primary.resolve() / record}\n"
        )
        _write(self.primary / record, b"r2 present under the primary home\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused: label citation outside the reviews home:", out)
        self.assertIn(record, out)
        self.assertNotIn(str(self.primary), out, "refusal rendered an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out, "refusal rendered an absolute path")

    def test_refuse_absolute_label_citation_even_with_basename_twin_in_home(self):
        # The tightened rule: an absolute token is ALWAYS refused, never
        # basename-verified; a basename twin under the primary home with
        # different bytes is not the cited file (the pathlib join would
        # discard the home operand, so the twin proves nothing about the
        # cited staging bytes).
        record = ".ai-playbook/reviews/2026-10-07-plan-review-t-r1.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {self.worktree.resolve() / record}\n"
        )
        _write(self.worktree / record, b"staged bytes in the worktree\n")
        _write(self.primary / record, b"different bytes under the primary home\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused: label citation outside the reviews home:", out)
        self.assertIn("2026-10-07-plan-review-t-r1.md", out)
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out)

    def test_refuse_relative_dotdot_citation_resolving_outside_home(self):
        # r3 fail-open closed: a relative `..` citation whose normalized
        # home join lands OUTSIDE the reviews home was verified by the
        # direct home-join arm (a lexical prefix match reads `..` as an
        # ordinary component, so `home / "../outside-x.md"` never escaped);
        # with the containment filesystem-resolved the citation is refused,
        # rendered as its own relative token, never an absolute path.
        _write(self.primary / "docs/history/outside-x.md", b"outside the reviews home\n")
        # the reviews home exists on disk: the exact shape under which the
        # lexical check fail-opened (the stat traverses home/..)
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        plan = self._plan("# Plan\n\nPlan review record: ../outside-x.md\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "refused: label citation outside the reviews home: ../outside-x.md", out
        )
        self.assertNotIn(str(self.primary), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertIn(MODULE._GATE_CITATION_REMEDY_LINE, out)

    def test_pass_relative_dotdot_citation_basename_twin_in_home(self):
        # The basename-fallback arm's directed case, live again once the
        # containment is filesystem-resolved: a relative `..` citation whose
        # resolved home join escapes the home while the basename record
        # exists under the home verifies through the HOME record, not the
        # outside file the lexical join used to stat.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-bb-r1.md"
        _write(self.primary / record, b"r1 under the primary home\n")
        _write(
            self.primary / "docs/history/2026-10-07-plan-review-bb-r1.md",
            b"a decoy twin outside the home\n",
        )
        plan = self._plan(
            "# Plan\n\nPlan review record: ../2026-10-07-plan-review-bb-r1.md\n"
        )
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")

    def test_series_absolute_citation_zero_members_missing_line_never_absolute(self):
        # A zero-member series cited by absolute path is missing, and its
        # missing line goes through the same never-absolute rendering as
        # the exact-token arm (basename here): the raw absolute citation
        # must not reach stdout.
        series = ".ai-playbook/reviews/2026-10-07-plan-review-abs-r*.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {self.worktree.resolve() / series}\n"
        )
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("missing: 2026-10-07-plan-review-abs-r*.md", out)
        self.assertNotIn(str(self.worktree), out, "missing line leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "missing line leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out)
        self.assertIn("worktree_closeout_migrate.py migrate", out)

    def test_resolved_home_missing_on_disk_is_modeled_missing_not_tool_error(self):
        # The assumptions register row's modeled-missing class: the facts
        # block resolves the reviews home but the home directory is absent
        # on disk; every owned record is then the modeled missing class
        # (exit 1 refuse), never a tool error.
        shutil.rmtree(self.primary / ".ai-playbook/reviews", ignore_errors=True)
        record = ".ai-playbook/reviews/2026-10-07-plan-review-z-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {record}", out)
        self.assertNotIn("tool_error", out)
        self.assertNotIn("Traceback", err)

    def test_multi_missing_renders_one_repo_relative_line_per_record(self):
        # Two absent owned records render two missing lines, each
        # repo-relative, never absolute.
        first = ".ai-playbook/reviews/2026-10-07-plan-review-m1-r1.md"
        second = ".ai-playbook/reviews/2026-10-07-plan-review-m2-r2.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {first}\nPlan review: {second}\n"
        )
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        missing_lines = [ln for ln in out.splitlines() if ln.startswith("missing: ")]
        self.assertEqual(
            sorted(missing_lines),
            [f"missing: {first}", f"missing: {second}"],
        )
        self.assertNotIn(str(self.primary.resolve()), out)
        self.assertNotIn(str(self.worktree.resolve()), out)

    def test_refuse_relative_dotdot_claims_entry_resolving_outside_home(self):
        # The r1 blocking claims-arm fail-open, mirrored from the exact
        # token's r3 witness: a `..`-threaded claims entry carries its
        # reviews-home prefix lexically, so the unresolved containment
        # check passed while is_file() followed the dots to the outside
        # file; with the candidate filesystem-resolved before containment
        # the entry is refused, never verified.
        _write(self.primary / "docs/history/outside-escape.md", b"outside the reviews home\n")
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        claims = self.root / "claims-dotdot.txt"
        claims.write_text(
            ".ai-playbook/reviews/../../docs/history/outside-escape.md\n",
            encoding="utf-8",
        )
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused: claims entry outside the reviews home:", out)
        self.assertIn("outside-escape.md", out)
        self.assertNotIn(str(self.primary), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertIn(MODULE._GATE_CITATION_REMEDY_LINE, out)

    def test_refuse_symlinked_series_member_resolving_outside_home(self):
        # The symlink presence fail-open, series form: a home record that
        # is a symlink into the worktree followed its link to a present
        # file and verified as a series member; with the resolved-only
        # member filter the resolution leaves the home, the series has
        # zero members, and the gate refuses with the missing line.
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        staged = ".ai-playbook/reviews/2026-10-07-plan-review-sl-r1.md"
        _write(self.worktree / staged, b"staged bytes the removal would destroy\n")
        os.symlink(
            self.worktree / staged,
            self.primary / ".ai-playbook/reviews/2026-10-07-plan-review-sl-r1.md",
        )
        series = ".ai-playbook/reviews/2026-10-07-plan-review-sl-r*.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {series}\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {series}", out)
        self.assertNotIn(str(self.worktree), out, "missing line leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "missing line leaked an absolute path")
        self.assertIn("worktree_closeout_migrate.py migrate", out)

    def test_refuse_claims_entry_through_symlinked_subdir(self):
        # The symlink presence fail-open, claims form: a symlinked
        # subdirectory of the reviews home pointing into the worktree made
        # the claimed record's is_file() true through the link; the
        # resolved containment check routes the entry to the refusal arm.
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        _write(self.worktree / ".ai-playbook/reviews/staged-claim.md", b"staged claim\n")
        os.symlink(
            self.worktree / ".ai-playbook/reviews",
            self.primary / ".ai-playbook/reviews/live",
        )
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        claims = self.root / "claims-symlinked-subdir.txt"
        claims.write_text(".ai-playbook/reviews/live/staged-claim.md\n", encoding="utf-8")
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused: claims entry outside the reviews home:", out)
        self.assertIn("staged-claim.md", out)
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")

    def test_refuse_basename_twin_symlink_resolving_outside_home(self):
        # The symlink presence fail-open, arm-2 basename-twin form: the
        # relative `..` citation's basename record under the home is
        # itself a symlink into the worktree; the resolved presence check
        # refuses the citation instead of verifying the twin's link.
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        staged = self.worktree / ".ai-playbook/reviews/2026-10-07-plan-review-bt-r1.md"
        _write(staged, b"staged bytes the removal would destroy\n")
        os.symlink(
            staged,
            self.primary / ".ai-playbook/reviews/2026-10-07-plan-review-bt-r1.md",
        )
        plan = self._plan(
            "# Plan\n\nPlan review record: ../2026-10-07-plan-review-bt-r1.md\n"
        )
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused: label citation outside the reviews home:", out)
        self.assertIn("2026-10-07-plan-review-bt-r1.md", out)
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out)
        self.assertIn(MODULE._GATE_CITATION_REMEDY_LINE, out)

    def test_refuse_target_worktree_operand_confusion(self):
        # The target-operand self-verification hole: --target naming the
        # worktree itself (or a worktree nested with the target) resolves
        # the records' home from the worktree the sanctioned command
        # removes, so the gate passed while sanctioning the destruction;
        # the equal, worktree-under-target, and target-under-worktree
        # shapes all refuse with a fail outcome.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.worktree / record, b"r1 staged in the worktree\n")
        nested = self.primary / "nested-wt"
        nested.mkdir()
        for confused in (self.primary, nested, self.root):
            code, out, err = self._run_gate(plan, "--worktree", str(confused))
            self.assertEqual(code, 1, f"confusion shape {confused} did not refuse")
            self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
            self.assertIn(
                "refused: --worktree resolves equal to or nested with the --target checkout",
                out,
            )
            self.assertNotIn(str(self.primary.resolve()), out)
            self.assertNotIn(str(self.worktree.resolve()), out)

    def test_body_label_shaped_line_does_not_seed_owned_set(self):
        # The extraction is bounded to the header region: a label-shaped
        # line after the first markdown heading never seeds the owned set,
        # so a body cite of an absent record cannot fail the gate.
        header_record = ".ai-playbook/reviews/2026-10-07-plan-review-hd-r1.md"
        body_record = ".ai-playbook/reviews/2026-10-07-plan-review-body-r1.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {header_record}\n"
            "\n"
            "## Terms\n"
            "\n"
            f"Plan review record: {body_record}\n"
        )
        _write(self.primary / header_record, b"r1 under the primary home\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertNotIn(body_record, out)

    def test_tool_error_plan_with_invalid_utf8(self):
        # The run-level catch: a plan fixture carrying invalid UTF-8 bytes
        # dies in the read and is caught to the tool-error class (exit 3,
        # the final OUTCOME line on stdout, the failure message on stderr),
        # never an unhandled traceback.
        plan = self.worktree / "docs/history/plans/2026-10-07-bad-bytes.md"
        _write(plan, b"# Plan\n\nPlan review record: \xff\xfe-broken.md\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("unexpected failure", err)
        self.assertNotIn("Traceback", err)

    def test_refuse_claims_entry_missing_inside_home(self):
        # A claims entry inside the home but absent on disk is the modeled
        # missing class (exit 1 with the missing line), never a pass.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        absent_claim = ".ai-playbook/reviews/2026-10-07-plan-review-cm-r1.md"
        claims = self.root / "claims-missing.txt"
        claims.write_text(f"{absent_claim}\n", encoding="utf-8")
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {absent_claim}", out)
        self.assertNotIn(str(self.primary.resolve()), out)

    def test_pass_claims_only_all_present(self):
        # The claims-only mirror: no header citations, every claims entry
        # present under the home is a pass printing the removal command.
        plan = self._plan("# Plan\n\nNo header citations.\n")
        claimed = ".ai-playbook/reviews/2026-10-07-plan-review-co-r1.md"
        _write(self.primary / claimed, b"claimed r1\n")
        claims = self.root / "claims-present.txt"
        claims.write_text(f"{claimed}\n", encoding="utf-8")
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("git worktree remove --force", out)

    def test_refuse_reviews_home_symlinked_into_worktree(self):
        # The r2 blocking shape, reviews-dir form: the primary's reviews
        # dir is itself a symlink into the worktree's staging tree, so the
        # resolved home anchors inside the worktree the sanctioned command
        # removes; before the guard every presence check passed and the
        # removal destroyed the only copy. The gate now refuses before any
        # presence check, names the home shape never as an absolute path,
        # and carries the operand remedy, never the migrate remedy.
        (self.primary / "docs/history").mkdir(parents=True, exist_ok=True)
        staged = ".ai-playbook/reviews/2026-10-07-plan-review-hw-r1.md"
        _write(self.worktree / staged, b"r1 staged in the worktree\n")
        os.symlink(
            self.worktree / ".ai-playbook/reviews",
            self.primary / ".ai-playbook/reviews",
        )
        plan = self._plan(f"# Plan\n\nPlan review record: {staged}\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "refused: the resolved reviews home anchors inside the --worktree tree",
            out,
        )
        self.assertIn(".ai-playbook/reviews", out)
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out, "refusal leaked an absolute path")
        self.assertIn("no migration fixes operand nesting", out)
        self.assertNotIn(
            "worktree_closeout_migrate.py migrate",
            out,
            "operand refusal carried the migrate remedy",
        )
        self.assertNotIn("OUTCOME: pass", out)

    def test_refuse_home_component_symlink_into_worktree(self):
        # The r2 blocking shape, component form: a parent component of the
        # home path (the audit home .ai-playbook/) is a symlink into the
        # worktree, so the resolved home anchors inside the worktree tree;
        # the same refusal fires before any presence check, with the
        # operand remedy and no absolute path on stdout.
        staged = ".ai-playbook/reviews/2026-10-07-plan-review-hc-r1.md"
        _write(self.worktree / staged, b"r1 staged in the worktree\n")
        shutil.rmtree(self.primary / ".ai-playbook")
        os.symlink(self.worktree / ".ai-playbook", self.primary / ".ai-playbook")
        plan = self._plan(f"# Plan\n\nPlan review record: {staged}\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "refused: the resolved reviews home anchors inside the --worktree tree",
            out,
        )
        self.assertIn(".ai-playbook/reviews", out)
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out, "refusal leaked an absolute path")
        self.assertIn("no migration fixes operand nesting", out)
        self.assertNotIn(
            "worktree_closeout_migrate.py migrate",
            out,
            "operand refusal carried the migrate remedy",
        )
        self.assertNotIn("OUTCOME: pass", out)

    def test_operand_refusal_names_operand_remedy_never_migrate(self):
        # The operand remedy on the classic confusion shape: a --worktree
        # equal to the target refuses with the operand-specific remedy
        # line, and the migrate remedy (which can never clear operand
        # nesting) stays absent from the output.
        record = ".ai-playbook/reviews/2026-10-07-plan-review-x-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.worktree / record, b"r1 staged in the worktree\n")
        code, out, err = self._run_gate(plan, "--worktree", str(self.primary))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "refused: --worktree resolves equal to or nested with the --target checkout",
            out,
        )
        self.assertIn("no migration fixes operand nesting", out)
        self.assertNotIn(
            "worktree_closeout_migrate.py migrate",
            out,
            "operand refusal carried the migrate remedy",
        )

    def test_headingless_plan_region_extends_to_end_of_file(self):
        # The header-region bound is conditional: with no post-title
        # heading the region runs to end of file, so label lines after
        # body-like prose still seed the owned set (the declared shape the
        # module docstring and the contract row scope); the present
        # record verifies while the late absent one is the missing line.
        present = ".ai-playbook/reviews/2026-10-07-plan-review-hl-r1.md"
        absent = ".ai-playbook/reviews/2026-10-07-plan-review-hl-r2.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {present}\n"
            "\n"
            "Prose paragraph with no markdown heading anywhere below the "
            "title line.\n"
            "\n"
            f"Plan review record: {absent}\n"
        )
        _write(self.primary / present, b"r1 under the primary home\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {absent}", out)
        self.assertNotIn(f"missing: {present}", out)
        self.assertNotIn(str(self.primary.resolve()), out)

    def test_header_boundary_is_first_hash_character_not_heading_parser(self):
        # The implemented header boundary is the first post-title line
        # whose first character is "#", not a general Markdown heading
        # parse: a setext underline and an indented ATX heading (both
        # headings to a Markdown parser) stay inside the region, so the
        # label line after them is still owned (the absent mid record is
        # reported missing), while a bare "#tag" line (not a CommonMark
        # heading: no space after the hash) ends the region, so the label
        # line after it is never scanned.
        present = ".ai-playbook/reviews/2026-10-07-plan-review-hb-r1.md"
        mid = ".ai-playbook/reviews/2026-10-07-plan-review-hb-r2.md"
        body = ".ai-playbook/reviews/2026-10-07-plan-review-hb-body.md"
        plan = self._plan(
            f"# Plan\n\nPlan review record: {present}\n"
            "\n"
            "Setext Heading\n"
            "---\n"
            "\n"
            "   ## Indented heading\n"
            "\n"
            f"Plan review record: {mid}\n"
            "\n"
            "#tag not-a-markdown-heading\n"
            "\n"
            f"Plan review record: {body}\n"
        )
        _write(self.primary / present, b"r1 under the primary home\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {mid}", out)
        self.assertNotIn(f"missing: {present}", out)
        self.assertNotIn(body, out, "region did not end at the first '#' character")
        self.assertNotIn(str(self.primary.resolve()), out)

    def test_reverse_containment_warns_only_and_removal_proceeds(self):
        # Reverse containment (plan gate-removal-closeout-accounting Task
        # 3): the --worktree resolves inside the absolute external reviews
        # home. The shape has no witnessed harmful catch, so the admission
        # is warning-only: the warning names the shape and the
        # machinery-admission fields (expected catch frequency low,
        # false-positive cost relocation noise, review date 2027-01-19),
        # and the run still verifies, still prints the sanctioned removal
        # command, and still passes. The blocking refusal stays reserved
        # for the opposite shape (the home inside the worktree), asserted
        # absent here.
        external_home = self.root / "external" / "reviews"
        external_home.mkdir(parents=True)
        _write(
            self.primary / ".ai-playbook/facts.md",
            (
                "```toml\n"
                f'reviews_dir = "{external_home}"\n'
                'tmp_dir = "docs/tmp/"\n'
                'metrics_dir = ".ai-playbook/metrics/"\n'
                "```\n"
            ).encode("utf-8"),
        )
        record = "2026-10-07-plan-review-rc-r1.md"
        _write(external_home / record, b"r1 in the external home\n")
        (external_home / "wt-inner").mkdir()
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        code, out, err = self._run_gate(
            plan, "--worktree", "../external/reviews/wt-inner"
        )
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("warning: reverse containment", out)
        self.assertIn("../external/reviews/wt-inner", out)
        self.assertIn("expected catch frequency low", out)
        self.assertIn("false-positive cost is relocation noise", out)
        self.assertIn("review date 2027-01-19", out)
        self.assertIn(
            "removal: git worktree remove --force ../external/reviews/wt-inner",
            out,
            "the warning blocked or displaced the sanctioned removal",
        )
        self.assertNotIn("refused:", out, "reverse containment refused")
        self.assertNotIn("anchors inside the --worktree tree", out)
        self.assertNotIn(str(self.root), out, "warning leaked an absolute path")
        # The warning is read-only visibility riding the run, never a
        # verdict: it precedes the removal line and the final outcome.
        self.assertLess(
            out.index("warning: reverse containment"),
            out.index("removal: git worktree remove"),
        )


class GateSiblingArmTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] Sibling-destruction fixtures (plan
    2026-10-16-worktree-closeout-claim-sibling-completeness): the
    gate-removal inventory derives the required ``.stats.json`` sibling of
    every verified claims entry and exact-token citation ending ``.md`` and
    refuses teardown while that sibling exists in the worktree staging home
    and is absent from the primary home, so a claim set naming records but
    not sidecars can no longer strand binding metadata. Pass shapes: a
    transferred sibling (both sides present) and the legacy sidecar-less
    record (the sibling exists nowhere) never refuse; a ``.stats.json``
    claims entry verifies as itself and derives nothing; a series citation
    with its highest-round witness present derives no siblings for any
    member, witness included."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-sibling-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.worktree = self._scratch_pair_member(self.root / "wt-session")
        self.primary = self._scratch_pair_member(self.root / "primary")

    def _scratch_pair_member(self, path: Path) -> Path:
        # One member of the scratch pair: a facts-resolved checkout-shaped
        # directory (the gate reads only the facts block and the reviews
        # home; it never invokes git, so a gitless fixture is faithful).
        path.mkdir(parents=True)
        _write(
            path / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        return path

    def _plan(self, body: str) -> Path:
        plan = self.worktree / "docs/history/plans/2026-10-16-x.md"
        _write(plan, body.encode("utf-8"))
        return plan

    def _run_gate(self, plan: Path, *extra: str) -> tuple[int, str, str]:
        return _run_cli(
            "gate-removal",
            "--plan", str(plan),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            *extra,
            cwd=self.worktree,
        )

    def _claims(self, name: str, *entries: str) -> Path:
        claims = self.root / name
        claims.write_text("\n".join(entries) + "\n", encoding="utf-8")
        return claims

    def test_refuse_claims_record_sibling_destroyed_by_removal(self):
        # Destruction refusal, claims arm: the record verifies under the
        # primary home while its .stats.json sibling sits only in the
        # worktree staging home; the gate refuses before any removal
        # verdict, naming the missing-from-home sibling path with the
        # migrate remedy, and never renders the sibling absolute.
        record = ".ai-playbook/reviews/2026-10-16-plan-review-sb-c-r1.md"
        sibling = ".ai-playbook/reviews/2026-10-16-plan-review-sb-c-r1.stats.json"
        plan = self._plan("# Plan\n\nNo header citations.\n")
        _write(self.primary / record, b"r1\n")
        _write(self.worktree / sibling, b'{"round": 1}\n')
        claims = self._claims("claims-sb-c.txt", record)
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "refused: claimed record's required stats sibling exists only "
            "in the worktree staging home:",
            out,
        )
        self.assertIn("2026-10-16-plan-review-sb-c-r1.stats.json", out)
        self.assertIn("worktree_closeout_migrate.py migrate", out, "transfer remedy absent")
        self.assertNotIn("git worktree remove", out, "removal verdict printed before the refusal")
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out)

    def test_refuse_label_cited_record_sibling_destroyed_by_removal(self):
        # Destruction refusal, exact-token arm: the same worktree and home
        # shape driven by a plan label line citing the record (no claims
        # file) takes the same sibling refusal through the exact-token arm.
        record = ".ai-playbook/reviews/2026-10-16-plan-review-sb-l-r1.md"
        sibling = ".ai-playbook/reviews/2026-10-16-plan-review-sb-l-r1.stats.json"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        _write(self.worktree / sibling, b'{"round": 1}\n')
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "refused: claimed record's required stats sibling exists only "
            "in the worktree staging home:",
            out,
        )
        self.assertIn("2026-10-16-plan-review-sb-l-r1.stats.json", out)
        self.assertIn("worktree_closeout_migrate.py migrate", out, "transfer remedy absent")
        self.assertNotIn("git worktree remove", out, "removal verdict printed before the refusal")
        self.assertNotIn(str(self.worktree), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "refusal leaked an absolute path")
        self.assertNotIn(str(self.primary.resolve()), out)

    def test_pass_sibling_transferred_to_home(self):
        # Transferred pass shape: the sibling exists at BOTH the worktree
        # staging home and the primary home, so the removal destroys no
        # only-copy and the gate passes printing the sanctioned command.
        record = ".ai-playbook/reviews/2026-10-16-plan-review-sb-t-r1.md"
        sibling = ".ai-playbook/reviews/2026-10-16-plan-review-sb-t-r1.stats.json"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        _write(self.primary / sibling, b'{"round": 1}\n')
        _write(self.worktree / sibling, b'{"round": 1}\n')
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("git worktree remove --force", out)
        self.assertNotIn("stats sibling", out)

    def test_pass_legacy_record_without_any_sibling(self):
        # Legacy sidecar-less pass shape: the sibling exists nowhere (the
        # record carries none and the worktree staging home holds nothing),
        # so the sibling arm never fires and the gate passes.
        record = ".ai-playbook/reviews/2026-10-16-plan-review-sb-legacy-r1.md"
        plan = self._plan(f"# Plan\n\nPlan review record: {record}\n")
        _write(self.primary / record, b"r1\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("git worktree remove --force", out)
        self.assertNotIn("stats sibling", out)

    def test_claims_sidecar_entry_verifies_as_itself_derives_nothing(self):
        # Sidecar-claims control: a claims entry ending .stats.json (present
        # at the primary home) verifies as itself and derives nothing: no
        # sibling refusal, a pass with the entry counted verified.
        sidecar = ".ai-playbook/reviews/2026-10-16-plan-review-sb-sc-r1.stats.json"
        plan = self._plan("# Plan\n\nNo header citations.\n")
        _write(self.primary / sidecar, b'{"round": 1}\n')
        claims = self._claims("claims-sb-sc.txt", sidecar)
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("verified 1 owned record(s) present", out)
        self.assertNotIn("stats sibling", out)
        self.assertIn("removal: git worktree remove --force", out)

    def test_aggregate_orders_missing_record_and_sibling_destruction_before_remedy(self):
        # Aggregate ordering: one absent record and one record whose
        # worktree-side sibling would be destroyed print BOTH lines (the
        # missing-record line and the sibling-destruction line) before the
        # shared remedy, and the run ends OUTCOME: fail.
        absent = ".ai-playbook/reviews/2026-10-16-plan-review-sb-ag-absent-r1.md"
        present = ".ai-playbook/reviews/2026-10-16-plan-review-sb-ag-r1.md"
        sibling = ".ai-playbook/reviews/2026-10-16-plan-review-sb-ag-r1.stats.json"
        plan = self._plan("# Plan\n\nNo header citations.\n")
        _write(self.primary / present, b"r1\n")
        _write(self.worktree / sibling, b'{"round": 1}\n')
        claims = self._claims("claims-sb-ag.txt", absent, present)
        code, out, err = self._run_gate(plan, "--claims", str(claims))
        self.assertEqual(code, 1)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {absent}", out)
        self.assertIn("2026-10-16-plan-review-sb-ag-r1.stats.json", out)
        missing_index = lines.index(f"missing: {absent}")
        sibling_index = next(
            index for index, line in enumerate(lines) if "stats sibling" in line
        )
        remedy_index = next(
            index for index, line in enumerate(lines) if line.startswith("remedy: run worktree_closeout_migrate.py capture")
        )
        self.assertLess(missing_index, remedy_index, "missing line printed after the remedy")
        self.assertLess(sibling_index, remedy_index, "sibling line printed after the remedy")
        self.assertNotIn("git worktree remove", out, "removal verdict printed before the refusal")

    def test_series_witness_present_derives_no_siblings(self):
        # Series-untouched control: a series citation whose highest-round
        # witness is present keeps the existing witness-presence verdict
        # with no sibling derivation for any member, witness included,
        # even while the witness's sibling sits only in the worktree
        # staging home.
        series = ".ai-playbook/reviews/2026-10-16-plan-review-sb-ser-r*.md"
        witness = ".ai-playbook/reviews/2026-10-16-plan-review-sb-ser-r1.md"
        witness_sibling = ".ai-playbook/reviews/2026-10-16-plan-review-sb-ser-r1.stats.json"
        plan = self._plan(f"# Plan\n\nPlan review record: {series}\n")
        _write(self.primary / witness, b"r1\n")
        _write(self.worktree / witness_sibling, b'{"round": 1}\n')
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("git worktree remove --force", out)
        self.assertNotIn("stats sibling", out)


class SeriesCitationFormsTest(unittest.TestCase):
    """Regression fixtures for the series-citation date-prefix forms (plan
    2026-10-15-closeout-gate-review-series-expansion): the plans template's
    literal ``YYYY-MM-DD`` placeholder and the ``*`` wildcard date prefix
    both expand through _series_members like a concrete date does, while a
    concrete-date citation stays exact, a member resolving outside the home
    never counts, and an absent series keeps its zero-member refusal."""

    PLACEHOLDER_SERIES = ".ai-playbook/reviews/YYYY-MM-DD-plan-review-x-r*.md"
    WILDCARD_SERIES = ".ai-playbook/reviews/*-plan-review-x-r*.md"
    CONCRETE_SERIES = ".ai-playbook/reviews/2026-10-13-plan-review-x-r*.md"

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-series-forms-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.worktree = self._scratch_pair_member(self.root / "wt-session")
        self.primary = self._scratch_pair_member(self.root / "primary")

    def _scratch_pair_member(self, path: Path) -> Path:
        # One member of the scratch pair: a facts-resolved checkout-shaped
        # directory (the gate reads only the facts block and the reviews
        # home; it never invokes git, so a gitless fixture is faithful).
        path.mkdir(parents=True)
        _write(
            path / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n",
        )
        return path

    def _plan(self, series: str) -> Path:
        plan = self.worktree / "docs/history/plans/2026-10-15-x.md"
        _write(plan, f"# Plan\n\nPlan review record: {series}\n".encode("utf-8"))
        return plan

    def _run_gate(self, plan: Path) -> tuple[int, str, str]:
        return _run_cli(
            "gate-removal",
            "--plan", str(plan),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            cwd=self.worktree,
        )

    def _run_verify(self, plan: Path) -> tuple[int, str, str]:
        return _run_cli(
            "verify-records",
            "--plan", str(plan),
            "--target", str(self.primary),
            cwd=self.worktree,
        )

    def test_placeholder_form_gate_passes_and_verify_names_dated_r1_witness(self):
        # The plans-template citation form: a home holding the dated r1
        # member satisfies a label citing the literal YYYY-MM-DD placeholder;
        # the gate passes and verify-records reports that dated member as
        # the series witness.
        _write(self.primary / ".ai-playbook/reviews/2026-10-13-plan-review-x-r1.md", b"r1\n")
        plan = self._plan(self.PLACEHOLDER_SERIES)
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        vcode, vout, _verr = self._run_verify(plan)
        self.assertEqual(vcode, 0)
        data = json.loads(vout)
        self.assertEqual(
            data["series_witness"],
            {self.PLACEHOLDER_SERIES: "2026-10-13-plan-review-x-r1.md"},
        )
        self.assertIn("2026-10-13-plan-review-x-r1.md", vout)

    def test_wildcard_form_passes_over_mixed_dates_with_highest_round_witness(self):
        # The date-agnostic citation form: mixed-date members (rounds
        # crossing midnight) all match a label citing the * wildcard date
        # prefix; the gate passes and the highest round is the witness.
        home = self.primary / ".ai-playbook/reviews"
        _write(home / "2026-10-13-plan-review-x-r1.md", b"r1\n")
        _write(home / "2026-10-14-plan-review-x-r2.md", b"r2\n")
        plan = self._plan(self.WILDCARD_SERIES)
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        vcode, vout, _verr = self._run_verify(plan)
        self.assertEqual(vcode, 0)
        data = json.loads(vout)
        self.assertEqual(
            data["series_witness"],
            {self.WILDCARD_SERIES: "2026-10-14-plan-review-x-r2.md"},
        )

    def test_concrete_date_citation_stays_exact_against_cross_date_only_home(self):
        # The exactness control: a concrete-date citation over a home holding
        # only a cross-date member is a zero-member series, so the gate
        # refuses naming the token; it never matches the other date.
        _write(self.primary / ".ai-playbook/reviews/2026-10-14-plan-review-x-r1.md", b"r1\n")
        plan = self._plan(self.CONCRETE_SERIES)
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {self.CONCRETE_SERIES}", out)

    def test_placeholder_form_member_symlinked_outside_home_never_counts(self):
        # The containment control, placeholder form: the home entry matching
        # the expanded series is a symlink into the worktree, so the
        # resolved-only member filter drops it and the gate refuses with the
        # zero-member missing line instead of sanctioning the removal.
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        staged = ".ai-playbook/reviews/2026-10-13-plan-review-x-r1.md"
        _write(self.worktree / staged, b"staged bytes the removal would destroy\n")
        os.symlink(self.worktree / staged, self.primary / staged)
        plan = self._plan(self.PLACEHOLDER_SERIES)
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {self.PLACEHOLDER_SERIES}", out)
        self.assertNotIn(str(self.worktree), out, "missing line leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "missing line leaked an absolute path")
        self.assertIn("worktree_closeout_migrate.py migrate", out)

    def test_wildcard_form_member_symlinked_outside_home_never_counts(self):
        # The containment control, wildcard form: same escape shape, the
        # member never counts and the gate refuses.
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        staged = ".ai-playbook/reviews/2026-10-14-plan-review-x-r2.md"
        _write(self.worktree / staged, b"staged bytes the removal would destroy\n")
        os.symlink(self.worktree / staged, self.primary / staged)
        plan = self._plan(self.WILDCARD_SERIES)
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {self.WILDCARD_SERIES}", out)
        self.assertNotIn(str(self.worktree), out, "missing line leaked an absolute path")
        self.assertNotIn(str(self.worktree.resolve()), out, "missing line leaked an absolute path")
        self.assertIn("worktree_closeout_migrate.py migrate", out)

    def test_absent_series_refuses_zero_members_in_each_form(self):
        # The zero-member control in both new forms: a genuinely absent
        # series stays a missing record naming the token.
        for series in (self.PLACEHOLDER_SERIES, self.WILDCARD_SERIES):
            with self.subTest(series=series):
                plan = self._plan(series)
                code, out, _err = self._run_gate(plan)
                self.assertEqual(code, 1)
                self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
                self.assertIn(f"missing: {series}", out)

    def _run_copy_cited(self, plan: Path, source: Path, target: Path) -> tuple[int, str, str]:
        return _run_cli(
            "copy-cited-records",
            "--plan", str(plan),
            "--source", str(source),
            "--target", str(target),
            cwd=source,
        )

    def _run_verify_target(self, plan: Path, target: Path) -> tuple[int, str, str]:
        return _run_cli(
            "verify-records",
            "--plan", str(plan),
            "--target", str(target),
            cwd=target,
        )

    def test_copy_cited_records_bridges_primary_home_record_into_run_home(self):
        # The lesson-270 bridge: a plan citing a series whose members exist
        # only in the primary reviews home copies them run-side, and the
        # verify-records leg whose containment resolves the home from the run
        # root passes after the copy arm; a second run is idempotent
        # (already-present rows, exit 0).
        _write(self.primary / ".ai-playbook/reviews/2026-10-13-plan-review-x-r1.md", b"r1\n")
        plan = self._plan(self.PLACEHOLDER_SERIES)
        code, out, _err = self._run_copy_cited(plan, self.primary, self.worktree)
        self.assertEqual(code, 0)
        self.assertIn("transferred", out)
        copied = self.worktree / ".ai-playbook/reviews/2026-10-13-plan-review-x-r1.md"
        self.assertTrue(copied.is_file())
        vcode, vout, _verr = self._run_verify_target(plan, self.worktree)
        self.assertEqual(vcode, 0)
        self.assertIn("2026-10-13-plan-review-x-r1.md", vout)
        code2, out2, _err2 = self._run_copy_cited(plan, self.primary, self.worktree)
        self.assertEqual(code2, 0)
        self.assertIn("already present", out2)
        self.assertNotIn("copy-cited-records: transferred ", out2)

    def test_copy_cited_records_copies_exact_home_citation_and_ignores_outsiders(self):
        # Exact-path citations resolving under the source home copy to the
        # same home-relative path; tokens outside the home (and absent
        # tokens) are ignored without manufacturing candidates, mirroring
        # the verify-records containment.
        _write(self.primary / ".ai-playbook/reviews/2026-10-27-exec-review-r1.md", b"record\n")
        plan = self.worktree / "docs/history/plans/2026-10-27-x.md"
        _write(
            plan,
            (
                "# Plan\n\n"
                "Plan review record: .ai-playbook/reviews/2026-10-27-exec-review-r1.md\n"
                "See also: docs/tmp/execute-plan/x/manifest.md and .ai-playbook/reviews/2026-10-27-absent-r9.md\n"
            ).encode("utf-8"),
        )
        code, out, _err = self._run_copy_cited(plan, self.primary, self.worktree)
        self.assertEqual(code, 0)
        copied = self.worktree / ".ai-playbook/reviews/2026-10-27-exec-review-r1.md"
        self.assertTrue(copied.is_file())
        self.assertFalse(
            (self.worktree / "docs/tmp/execute-plan/x/manifest.md").exists()
        )
        self.assertFalse(
            (self.worktree / ".ai-playbook/reviews/2026-10-27-absent-r9.md").exists()
        )
        self.assertIn("transferred=1", out)

    def test_copy_cited_records_fails_closed_on_unresolvable_target_facts(self):
        # Fail-closed home resolution: a target without a facts block is a
        # named rc 2, never a guessed default or a silent no-op.
        _write(self.primary / ".ai-playbook/reviews/2026-10-13-plan-review-x-r1.md", b"r1\n")
        plan = self._plan(self.PLACEHOLDER_SERIES)
        bare_target = self.root / "no-facts-target"
        bare_target.mkdir()
        code, _out, err = self._run_copy_cited(plan, self.primary, bare_target)
        self.assertEqual(code, 2)
        self.assertIn("cannot resolve reviews_dir", err)

    def test_copy_cited_records_keys_symlink_member_dest_to_cited_path(self):
        # The no-mirror corpus home is symlink-bearing by design: a cited
        # series member that is an in-home symlink copies under the cited
        # top-level name (the name the verify leg's series scan reads),
        # never under its resolved subdirectory location, and the
        # verify-records leg against the run root passes after the copy arm.
        home = self.primary / ".ai-playbook/reviews"
        _write(home / "sub/2026-10-13-plan-review-y-r1.md", b"r1\n")
        os.symlink("sub/2026-10-13-plan-review-y-r1.md", home / "2026-10-13-plan-review-y-r1.md")
        plan = self.worktree / "docs/history/plans/2026-10-15-y.md"
        _write(
            plan,
            "# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-13-plan-review-y-r*.md\n".encode("utf-8"),
        )
        code, out, _err = self._run_copy_cited(plan, self.primary, self.worktree)
        self.assertEqual(code, 0)
        self.assertTrue(
            (self.worktree / ".ai-playbook/reviews/2026-10-13-plan-review-y-r1.md").is_file()
        )
        self.assertFalse((self.worktree / ".ai-playbook/reviews/sub").exists())
        vcode, vout, _verr = self._run_verify_target(plan, self.worktree)
        self.assertEqual(vcode, 0)
        self.assertIn("2026-10-13-plan-review-y-r1.md", vout)


class TemplateCitationFormTests(SeriesCitationFormsTest):
    """Regression fixtures for the plans template's citation form with the
    bracketed optional-token segment left literal (the witnessed
    empty-stem closeout refusal, row
    2026-10-19-closeout-citation-template-form-empty-stem): the tokenizer
    captures the template citation as one series token, the bracketed
    segment translates to an optional fragment, a placeholder segment
    matches a slug-shaped run, and a bare ``-r*.md`` fragment with no slug
    warns and skips instead of surfacing a zero-member refusal."""

    TEMPLATE_TOKEN_SERIES = (
        ".ai-playbook/reviews/2026-10-19-pcdd5309a[-p<identity-token>]-r*.md"
    )
    TEMPLATE_PLACEHOLDER_SERIES = (
        ".ai-playbook/reviews/YYYY-MM-DD-<artifact-slug>[-p<identity-token>]-r*.md"
    )
    def test_template_form_with_tokened_members_resolves(self):
        # The witnessed shape: the citation leaves the bracketed segment
        # literal while the home's members carry the -p infix; verify
        # resolves the series and the gate passes.
        home = self.primary / ".ai-playbook/reviews"
        _write(home / "2026-10-19-pcdd5309a-ptok-r1.md", b"r1\n")
        _write(home / "2026-10-19-pcdd5309a-ptok-r2.md", b"r2\n")
        plan = self._plan(self.TEMPLATE_TOKEN_SERIES)
        vcode, vout, _verr = self._run_verify(plan)
        self.assertEqual(vcode, 0)
        data = json.loads(vout)
        self.assertEqual(
            data["series_witness"],
            {self.TEMPLATE_TOKEN_SERIES: "2026-10-19-pcdd5309a-ptok-r2.md"},
        )
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")

    def test_template_form_with_omitted_infix_resolves(self):
        # The actually-witnessed members: the home holds the series without
        # the optional -p infix at all; the bracketed segment is optional,
        # so the citation still resolves.
        home = self.primary / ".ai-playbook/reviews"
        _write(home / "2026-10-19-pcdd5309a-r1.md", b"r1\n")
        _write(home / "2026-10-19-pcdd5309a-r5.md", b"r5\n")
        plan = self._plan(self.TEMPLATE_TOKEN_SERIES)
        vcode, vout, _verr = self._run_verify(plan)
        self.assertEqual(vcode, 0)
        data = json.loads(vout)
        self.assertEqual(
            data["series_witness"],
            {self.TEMPLATE_TOKEN_SERIES: "2026-10-19-pcdd5309a-r5.md"},
        )

    def test_template_form_with_placeholder_slug_resolves(self):
        # The fully un-instantiated template form: the date and the slug
        # both stay placeholders and still resolve against the dated,
        # concretely named members.
        home = self.primary / ".ai-playbook/reviews"
        _write(home / "2026-10-19-pcdd5309a-r1.md", b"r1\n")
        plan = self._plan(self.TEMPLATE_PLACEHOLDER_SERIES)
        vcode, vout, _verr = self._run_verify(plan)
        self.assertEqual(vcode, 0)
        data = json.loads(vout)
        self.assertEqual(
            data["series_witness"],
            {self.TEMPLATE_PLACEHOLDER_SERIES: "2026-10-19-pcdd5309a-r1.md"},
        )

    def test_template_form_absent_series_still_refuses_zero_members(self):
        # The fail-closed control: a template-form citation over a home
        # with no matching members keeps the zero-members refusal.
        plan = self._plan(self.TEMPLATE_TOKEN_SERIES)
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {self.TEMPLATE_TOKEN_SERIES}", out)

    def test_bare_empty_prefix_fragment_warns_and_skips(self):
        # The warn-and-skip control: a bare -r*.md fragment with no slug
        # never surfaces as a zero-members refusal; it is skipped with a
        # named note on stderr and in the skipped list, and the run exits 0.
        (self.primary / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
        _write(self.primary / ".ai-playbook/reviews/2026-10-19-x-r1.md", b"r1\n")
        plan = self._plan("-r*.md")
        vcode, vout, verr = self._run_verify(plan)
        self.assertEqual(vcode, 0)
        data = json.loads(vout)
        self.assertEqual(data["missing"], [])
        self.assertEqual(len(data["skipped"]), 1)
        self.assertIn("empty-prefix series token skipped", data["skipped"][0])
        self.assertTrue(data["skipped"][0].endswith(": -r*.md"))
        self.assertIn("empty-prefix series token skipped", verr)

    def test_concrete_citation_keeps_exact_behavior(self):
        # The exactness control: a fully concrete citation over a home
        # holding only a cross-date member still refuses; the template
        # translation never widens a concrete citation.
        _write(self.primary / ".ai-playbook/reviews/2026-10-14-plan-review-x-r1.md", b"r1\n")
        plan = self._plan(self.CONCRETE_SERIES)
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {self.CONCRETE_SERIES}", out)


class SeriesTokenIdentityTest(unittest.TestCase):
    """Plan 2026-10-18-closeout-gate-series-token-infix: the closeout matcher
    recognizes canonical tokened series members for a tokenless citation (the
    zero-member false refusal repaired), and a read-only source-identity
    diagnostic reports foreign or unresolved records without filtering
    members or changing any selection, exit status, or consumer result."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-series-token-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.worktree = self._member(self.root / "wt-session")
        self.primary = self._member(self.root / "primary")
        subprocess.run(["git", "init", "-q", str(self.worktree)], check=True)
        self.plan_rel = "docs/history/plans/2026-10-19-x.md"
        self.plan = self.worktree / self.plan_rel
        self._write_plan(".ai-playbook/reviews/YYYY-MM-DD-plan-review-x-r*.md")
        self.token = review_plan_identity.identity_token(self.plan_rel)
        self.home = self.primary / ".ai-playbook/reviews"

    def _member(self, path: Path) -> Path:
        path.mkdir(parents=True)
        _write(
            path / ".ai-playbook/facts.md",
            b'```toml\nreviews_dir = ".ai-playbook/reviews/"\ntmp_dir = "docs/tmp/"\nmetrics_dir = ".ai-playbook/metrics/"\n',
        )
        return path

    def _write_plan(self, series: str) -> None:
        self.plan.parent.mkdir(parents=True, exist_ok=True)
        _write(self.plan, f"# Plan\n\nPlan review record: {series}\n".encode("utf-8"))

    def _record_name(self, tok: str | None, r: int = 1) -> str:
        infix = f"-p{tok}" if tok else ""
        return f"2026-10-13-plan-review-x{infix}-r{r}.md"

    def _write_record(
        self,
        name: str,
        *,
        sidecar_identity: str | None = None,
        metadata: bytes = b"",
        body: bytes = b"",
    ) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        text = b"# Plan Review\n\n## Metadata\n- Type: Plan Review\n" + metadata + b"\n" + body
        _write(self.home / name, text)
        if sidecar_identity is not None:
            _write(
                self.home / (name[: -len(".md")] + ".stats.json"),
                json.dumps({"extensions": {"plan_identity": sidecar_identity}}).encode("utf-8"),
            )

    def _run_gate(self) -> tuple[int, str, str]:
        return _run_cli(
            "gate-removal",
            "--plan", str(self.plan),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            cwd=self.worktree,
        )

    def _run_verify(self) -> tuple[int, str, str]:
        return _run_cli(
            "verify-records",
            "--plan", str(self.plan),
            "--target", str(self.primary),
            cwd=self.worktree,
        )

    def test_tokenless_citation_accepts_canonical_tokened_member(self):
        # The zero-member false refusal repaired: a tokenless citation
        # recognizes the canonical tokened record and the witness is that
        # tokened member; no identity warning fires for the plan's own record.
        name = self._record_name(self.token)
        self._write_record(name, sidecar_identity=self.plan_rel)
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertNotIn("series-identity", out)
        vcode, vout, verr = self._run_verify()
        self.assertEqual(vcode, 0, verr)
        data = json.loads(vout)
        self.assertEqual(data["missing"], [])
        self.assertEqual(
            data["series_witness"],
            {".ai-playbook/reviews/YYYY-MM-DD-plan-review-x-r*.md": name},
        )
        self.assertNotIn("series-identity", vout)

    def test_foreign_identity_warns_without_filtering(self):
        name = self._record_name(self.token)
        self._write_record(
            name, sidecar_identity="docs/history/plans/2026-10-01-other.md"
        )
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("series-identity", out)
        self.assertIn(name, out)
        self.assertIn("docs/history/plans/2026-10-01-other.md", out)
        vcode, vout, verr = self._run_verify()
        self.assertEqual(vcode, 0, verr)
        data = json.loads(vout)
        self.assertEqual(data["missing"], [])
        self.assertEqual(
            data["series_witness"],
            {".ai-playbook/reviews/YYYY-MM-DD-plan-review-x-r*.md": name},
        )

    def test_unresolved_identity_warns(self):
        name = self._record_name(self.token)
        self._write_record(name)
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("series-identity", out)
        self.assertIn("unresolved", out)
        vcode, vout, verr = self._run_verify()
        self.assertEqual(vcode, 0, verr)
        self.assertIn("series-identity", verr)
        json.loads(vout)

    def test_body_or_fenced_identity_text_is_ignored(self):
        # Identity binds from the Metadata section or the stats sidecar
        # only: the same URL or Artifact line in body content never
        # becomes the record's identity, so the member reports unresolved.
        name = self._record_name(self.token)
        self._write_record(
            name,
            body=b"## Findings\n\n- URL or Artifact: docs/history/plans/2026-10-01-other.md\n",
        )
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, err)
        self.assertIn("series-identity", out)
        self.assertIn("unresolved", out)
        self.assertNotIn("2026-10-01-other.md", out.split("series-identity", 1)[1].splitlines()[0])

    def test_higher_round_foreign_record_warns_without_changing_selection(self):
        own = self._record_name(self.token, r=1)
        foreign = self._record_name(self.token, r=2)
        self._write_record(own, sidecar_identity=self.plan_rel)
        self._write_record(
            foreign, sidecar_identity="docs/history/plans/2026-10-01-other.md"
        )
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, err)
        identity_lines = [line for line in out.splitlines() if line.startswith("series-identity")]
        self.assertEqual(len(identity_lines), 1)
        self.assertIn(foreign, identity_lines[0])
        vcode, vout, verr = self._run_verify()
        self.assertEqual(vcode, 0, verr)
        data = json.loads(vout)
        self.assertEqual(data["missing"], [])
        witness = next(iter(data["series_witness"].values()))
        self.assertEqual(witness, foreign, "highest round stays the witness")

    def test_explicit_token_citation_stays_exact(self):
        tokened = self._record_name(self.token)
        self._write_record(tokened, sidecar_identity=self.plan_rel)
        self._write_plan(
            f".ai-playbook/reviews/YYYY-MM-DD-plan-review-x-p{self.token}-r*.md"
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0)
        self.assertNotIn("series-identity", out)
        # A different valid token does not match the citation's token: the
        # zero-member refusal is preserved for the mismatched series (the
        # home holds only the citation token's member here).
        self._write_plan(
            ".ai-playbook/reviews/YYYY-MM-DD-plan-review-x-pffffffff-r*.md"
        )
        code, out, err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertIn("missing:", out)
        vcode, vout, verr = self._run_verify()
        self.assertEqual(vcode, 1)
        self.assertIn("zero members", vout + verr)
        data = json.loads(vout)
        self.assertTrue(any("zero members" in m for m in data["missing"]))
        # Malformed token-like text stays literal: a p-prefixed but
        # non-hex citation segment never accepts a canonical member.
        self._write_plan(
            ".ai-playbook/reviews/YYYY-MM-DD-plan-review-x-pzzzzzzzz-r*.md"
        )
        code, _out, _err = self._run_gate()
        self.assertEqual(code, 1)

    def test_gate_plan_identity_flag_drives_diagnostics(self):
        # The completed-twin runner passes the original repository-relative
        # plan path beside the temporary --plan copy; the flag alone must
        # drive the same diagnostic (and its absence in a gitless target
        # must never fail the gate).
        name = self._record_name(self.token)
        self._write_record(
            name, sidecar_identity="docs/history/plans/2026-10-01-other.md"
        )
        code, out, err = _run_cli(
            "gate-removal",
            "--plan", str(self.plan),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            "--plan-identity", self.plan_rel,
            cwd=self.worktree,
        )
        self.assertEqual(code, 0, err)
        self.assertIn("series-identity", out)

    def _write_completed_plan(self) -> Path:
        # The archived shape: the same basename directly under the completed
        # archive, citing the same series; its records stay tokened to the
        # plans-root path.
        completed = self.worktree / "docs/history/plans/completed" / self.plan.name
        completed.parent.mkdir(parents=True, exist_ok=True)
        _write(completed, self.plan.read_bytes())
        return completed

    def test_completed_archive_plan_path_derives_plans_root_identity(self):
        # A direct gate or verify run on the completed-archive path derives
        # the plans-root identity the records carry, so the plan's own
        # tokened record raises no foreign-identity warning.
        completed = self._write_completed_plan()
        self._write_record(self._record_name(self.token), sidecar_identity=self.plan_rel)
        code, out, err = _run_cli(
            "gate-removal",
            "--plan", str(completed),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            cwd=self.worktree,
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertNotIn("series-identity", out)
        vcode, vout, verr = _run_cli(
            "verify-records",
            "--plan", str(completed),
            "--target", str(self.primary),
            cwd=self.worktree,
        )
        self.assertEqual(vcode, 0, verr)
        self.assertNotIn("series-identity", verr)
        self.assertEqual(json.loads(vout)["missing"], [])

    def test_completed_archive_derivation_control_without_fix_shape(self):
        # Negative control: a record tokened to a foreign plans-root plan
        # still warns under the completed-archive derivation, so the fix
        # narrows the derivation without silencing the diagnostic.
        completed = self._write_completed_plan()
        self._write_record(
            self._record_name(self.token),
            sidecar_identity="docs/history/plans/2026-10-01-other.md",
        )
        code, out, err = _run_cli(
            "gate-removal",
            "--plan", str(completed),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            cwd=self.worktree,
        )
        self.assertEqual(code, 0, err)
        self.assertIn("series-identity", out)
        self.assertIn(f"expected {self.plan_rel}", out)

    def test_plan_identity_flag_overrides_completed_derivation(self):
        # The override still wins over the completed-archive derivation.
        completed = self._write_completed_plan()
        self._write_record(self._record_name(self.token), sidecar_identity=self.plan_rel)
        code, out, err = _run_cli(
            "gate-removal",
            "--plan", str(completed),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            "--plan-identity", "docs/history/plans/2026-10-01-other.md",
            cwd=self.worktree,
        )
        self.assertEqual(code, 0, err)
        self.assertIn("series-identity", out)
        self.assertIn("expected docs/history/plans/2026-10-01-other.md", out)

    def test_twin_runner_passes_original_plan_identity(self):
        # _run_gate_on_twin seeds the gate child with the original
        # repository-relative plan path beside its temporary --plan file.
        observed: dict[str, object] = {}

        class _FakeProc:
            returncode = 0
            stdout = "OUTCOME: pass\n"
            stderr = ""

        real_run = MODULE.subprocess.run

        def fake_run(argv, **kwargs):
            if argv[:2] == [sys.executable, str(MODULE.__file__)]:
                observed["argv"] = argv
                return _FakeProc()
            return real_run(argv, **kwargs)

        plan_dir = Path(self.worktree)  # unused; the twin reads HEAD bytes
        completed = MODULE._COMPLETED_DIR + "/2026-10-19-x.md"

        class _SweepStub:
            def __call__(self, target, *args, **kwargs):
                if args[:2] == ("cat-file", "blob"):
                    return subprocess.CompletedProcess(
                        args, 0,
                        stdout="# Plan\n\nPlan review record: series\n",
                        stderr="",
                    )
                return MODULE._sweep_git_orig(target, *args, **kwargs)

        MODULE._sweep_git_orig = MODULE._sweep_git
        MODULE.subprocess_run_orig = MODULE.subprocess.run
        MODULE._sweep_git = _SweepStub()
        MODULE.subprocess.run = fake_run
        try:
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                gate_class, _evidence, _disposition = MODULE._run_gate_on_twin(
                    Path(self.worktree), "2026-10-19-x.md", str(plan_dir)
                )
        finally:
            MODULE._sweep_git = MODULE._sweep_git_orig
            MODULE.subprocess.run = MODULE.subprocess_run_orig
            del MODULE._sweep_git_orig, MODULE.subprocess_run_orig
        self.assertEqual(gate_class, "pass", buf.getvalue())
        argv = observed["argv"]
        self.assertIn("--plan-identity", argv)
        self.assertEqual(argv[argv.index("--plan-identity") + 1], self.plan_rel)


class SweepTest(unittest.TestCase):
    """Fixtures for the sweep subcommand: a real git fixture repository with
    ad-hoc-shaped worktrees beside a primary checkout, a completed twin in
    the primary HEAD tree, and controlled done-lock and merge-lock roots."""

    # 2026-01-01T00:00:00Z, the fixture's base committer date: the twin's
    # introduction commit and the branch's plan commit share it, so the
    # post-landing arm passes on equality and fails only on newer dates.
    EPOCH = 1767225600

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    SWEEP_ENV_VARS = (
        "DONE_LOCK_DIR",
        "DONE_LOCK_TOKEN",
        "DONE_LOCK_ROOT",
        "DONE_LOCK_SCRIPT",
        "MERGE_LOCK_ROOT",
        "MERGE_LOCK_DIR",
        "MERGE_LOCK_TOKEN",
        "MERGE_LOCK_HOLDER_PID",
    )

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrs-sweep-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        self._git(self.primary, "init", "-q")
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        # The done-lock script copy the sweep resolves repo-locally for its
        # merge-acquire; the fixture controls the merge lock root by env.
        (self.primary / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            SCRIPT_PATH.parent / "done-lock.sh",
            self.primary / "scripts" / "done-lock.sh",
        )
        self._commit_all(self.primary, "init: fixture repo", date=self.EPOCH)
        self.done_lock_root = self.root / "done-locks"
        self.done_lock_root.mkdir(parents=True)
        self.merge_lock_root = self.root / "merge-locks"
        self.merge_lock_root.mkdir(parents=True)

    # -- fixture primitives -------------------------------------------------

    def _git(self, repo: Path, *args: str, date: int | None = None, check: bool = True):
        env = _hermetic_git_env(self.root, **self.GIT_IDENTITY)
        if date is not None:
            stamp = f"{date} +0000"
            env["GIT_AUTHOR_DATE"] = stamp
            env["GIT_COMMITTER_DATE"] = stamp
        proc = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env
        )
        if check and proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc

    def _commit_all(self, repo: Path, message: str, date: int | None = None) -> None:
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-q", "-m", message, date=date)

    def _toplevel(self, repo: Path | None = None) -> str:
        return self._git(repo or self.primary, "rev-parse", "--show-toplevel").stdout.strip()

    def _registered_paths(self) -> list[str]:
        out = self._git(self.primary, "worktree", "list", "--porcelain").stdout
        return [line[len("worktree "):] for line in out.splitlines() if line.startswith("worktree ")]

    def _porcelain_path(self, path: Path) -> str:
        """The registered spelling of a fixture worktree (git physicalizes
        paths; the sweep's verdict lines carry the registered spelling)."""
        want = str(Path(path).resolve())
        for registered in self._registered_paths():
            if str(Path(registered).resolve()) == want:
                return registered
        raise AssertionError(f"worktree not registered: {path}")

    def seed_twin(self, basename: str, cites: str | None = ".ai-playbook/reviews/2026-10-01-alpha-r1.md", write_record: bool = True) -> None:
        # Fold r1 F2a (2026-10-08): the twin's introduction commit must
        # model the witnessed squash landing, which touches every file its
        # branch touched. The plan's plans-root vintage is authored in the
        # primary first, then the landing commit moves it into completed/
        # beside the review record, so the introduction commit's touched
        # set contains the plans-root path the candidate branch re-adds and
        # the arm-6 content-scope check passes the eligible shape. The
        # plans root ends this helper empty, so a worktree created after it
        # still models a branch with zero plan files until one is written.
        body = "# Plan\n\n"
        if cites:
            body += f"Plan review record: {cites}\n"
        else:
            body += "No review rounds.\n"
        plans_root_copy = self.primary / "docs/history/plans" / basename
        _write(plans_root_copy, body.encode("utf-8"))
        self._commit_all(self.primary, f"plan: author {basename} at the plans root", date=self.EPOCH)
        plans_root_copy.unlink()
        _write(self.primary / "docs/history/plans/completed" / basename, body.encode("utf-8"))
        if cites and write_record:
            _write(self.primary / cites, b"r1\n")
        self._commit_all(self.primary, f"plan: seed twin {basename}", date=self.EPOCH)

    def add_worktree(self, slug: str, branch: str | None = None, detach: bool = False, name: str | None = None, parent: Path | None = None) -> Path:
        dirname = name or f"proj-wt-{slug}"
        path = (parent or self.root) / dirname
        args = ["worktree", "add", "-q"]
        if detach:
            args.append("--detach")
        else:
            args += ["-b", branch or f"wt-{slug}"]
        args.append(str(path))
        self._git(self.primary, *args)
        return path

    def write_candidate_plan(self, path: Path, basename: str, body: str = "# Plan worktree copy\n", date: int | None = None) -> None:
        _write(Path(path) / "docs/history/plans" / basename, body.encode("utf-8"))
        self._commit_all(path, "plan: candidate plan file", date=self.EPOCH if date is None else date)

    def eligible_candidate(self, slug: str = "alpha", basename: str = "2026-10-01-alpha.md") -> Path:
        self.seed_twin(basename)
        path = self.add_worktree(slug, branch=f"wt-{slug}")
        self.write_candidate_plan(path, basename)
        return path

    def exact_tree_candidate(self, slug: str = "alpha", basename: str = "2026-10-01-alpha.md") -> Path:
        """A candidate whose tip tree equals a destination-history commit's
        tree while the branch is not an ancestor: the worktree branches
        before the twin seeding, then commits the identical plans-root
        vintage the seeding's first landing commit carries, so both trees
        match and no archive twin is needed for the accounting."""
        path = self.add_worktree(slug, branch=f"wt-{slug}")
        self.seed_twin(basename)
        cites = f".ai-playbook/reviews/2026-10-01-{slug}-r1.md"
        _write(
            Path(path) / "docs/history/plans" / basename,
            f"# Plan\n\nPlan review record: {cites}\n".encode("utf-8"),
        )
        self._commit_all(path, "plan: identical plans-root vintage", date=self.EPOCH)
        return path

    def write_slug_manifest(self, basename: str, branch: str, worktree: Path) -> Path:
        """The candidate's migration manifest at the slug-resolved session
        directory (Task 2: the sweep passes it to the twin gate run)."""
        slug = MODULE._plan_session_slug(Path(basename))
        manifest_dir = self.primary / "docs/tmp/execute-plan" / slug
        manifest_dir.mkdir(parents=True, exist_ok=True)
        path = manifest_dir / "closeout-migration.json"
        path.write_text(
            json.dumps(
                {
                    "migrated": [],
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [{"branch": branch, "source": str(worktree)}],
                }
            ),
            encoding="utf-8",
        )
        return path

    def branch_oid(self, branch: str) -> str:
        return self._git(self.primary, "rev-parse", branch).stdout.strip()

    def hold_env(self, token: str = "sweep-token-1", repo_root: str | None = None, metaless: bool = False) -> dict[str, str]:
        """An authentic-hold export set for the primary checkout, derived
        exactly as the done-lock script derives it (toplevel digest under
        the controlled lock root)."""
        toplevel = self._toplevel()
        repo_id = hashlib.sha256(toplevel.encode("utf-8")).hexdigest()[:16]
        lock_dir = self.done_lock_root / repo_id
        lock_dir.mkdir(parents=True, exist_ok=True)
        if not metaless:
            _write(
                lock_dir / "meta.env",
                f"lock_token={token}\nrepo_root={repo_root or toplevel}\nlabel=sweep-fixture\n".encode("utf-8"),
            )
        return {
            "DONE_LOCK_ROOT": str(self.done_lock_root),
            "DONE_LOCK_DIR": str(lock_dir),
            "DONE_LOCK_TOKEN": token,
            "MERGE_LOCK_ROOT": str(self.merge_lock_root),
        }

    def run_sweep(self, *extra: str, env_overrides: dict[str, str] | None = None, target: Path | None = None):
        # Hermetic env (plan 2026-10-19-gate-removal-closeout-accounting
        # Task 2): the sweep subprocess (and every git it spawns) inherits
        # the cleared-GIT_*, fixture-local-HOME, deterministic-locale env.
        env = _hermetic_git_env(self.root)
        # Hermetic lock pins (plan 2026-10-10-done-closeout-lock-span Task 1):
        # the merge-lock root lives in the fixture tmp tree and the done-lock
        # script is the repo-local copy; --apply fixtures override the root
        # through hold_env after these defaults.
        env.pop("DONE_LOCK_ROOT", None)
        env["DONE_LOCK_SCRIPT"] = str(DONE_LOCK_SCRIPT_PATH)
        env["MERGE_LOCK_ROOT"] = str(self.merge_lock_root)
        env["MERGE_LOCK_POLL_SECS"] = "1"
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "sweep", "--target", str(target or self.primary), *extra],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.root),
        )

    def assertOutcome(self, proc, code: int, outcome: str) -> None:
        self.assertEqual(proc.returncode, code, proc.stderr)
        self.assertEqual(
            [line for line in proc.stdout.splitlines() if line.startswith("OUTCOME:")],
            [f"OUTCOME: {outcome}"],
            "exactly one final OUTCOME line expected",
        )

    def _branch_gone(self, branch: str) -> bool:
        return self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode != 0

    # -- enumeration and the six-arm chain ----------------------------------

    def test_sweep_report_mode_enumeration_keeps_only_adhoc_shape(self):
        eligible = self.eligible_candidate()
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        wrong_parent = self.add_worktree("orphan", branch="wt-orphan", parent=elsewhere)
        wrong_name = self.add_worktree("misfit", branch="wt-misfit", name="sibling-wt-misfit")
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {self._porcelain_path(eligible)}: operator-controlled worktree retained",
            proc.stdout,
        )
        self.assertNotIn(str(wrong_parent.resolve()), proc.stdout)
        self.assertNotIn(str(wrong_name.resolve()), proc.stdout)

    def test_sweep_no_candidates_is_pass(self):
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertEqual(proc.stdout.strip().splitlines(), ["OUTCOME: pass"])

    def test_sweep_report_only_default_never_removes(self):
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: operator-controlled worktree retained "
            "(on-disk worktree and artifacts preserved; branch refs are never removed by the sweep)",
            proc.stdout,
        )
        self.assertTrue(Path(path).is_dir(), "report mode removed the worktree")
        self.assertIn(registered, self._registered_paths())
        self.assertFalse(self._branch_gone("wt-alpha"))
        self.assertEqual(list((self.primary / "docs/tmp").glob("sweep-twin-*")), [])

    def test_sweep_dirty_worktree_skip(self):
        path = self.eligible_candidate()
        _write(Path(path) / "scratch-untracked.md", b"untracked\n")
        registered = self._porcelain_path(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: dirty worktree", proc.stdout)
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: the
        # branch-backed skip also reports the branch-report line carrying
        # the branch, the resolved tip OID, and the skip reason.
        self.assertIn(
            f"branch-report: branch wt-alpha: skipped at "
            f"{self.branch_oid('wt-alpha')}; reason: dirty worktree",
            proc.stdout,
        )
        # Fold r1 F8: the verdict line alone cannot witness survival (a
        # mutant deleting the candidate in report mode would pass), so the
        # registration and the on-disk tree are asserted after the run.
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir(), "report mode removed the skipped candidate")

    def test_sweep_ignored_staging_artifacts_skip_and_survive_apply(self):
        # Fold r1 F1: the six-arm chain is blind to the gitignored staging
        # corpus (a dead-session worktree whose .ai-playbook/reviews holds
        # an untracked-but-ignored record is clean by porcelain), so the
        # staging-corpus arm probes both surfaces directly; the candidate
        # is reported with the exact reason and survives --apply.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        _write(Path(path) / ".gitignore", b".ai-playbook/reviews/2026-10-01-ignored-r1.md\n")
        self._commit_all(path, "chore: ignore the staged review record", date=self.EPOCH)
        _write(
            Path(path) / ".ai-playbook/reviews/2026-10-01-ignored-r1.md",
            b"staged review bytes the removal would destroy\n",
        )
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: unmigrated ignored artifacts present", proc.stdout
        )
        self.assertTrue(Path(path).is_dir(), "the worktree with ignored artifacts was removed")
        self.assertIn(registered, self._registered_paths())
        self.assertFalse(self._branch_gone("wt-alpha"))

    def test_sweep_clean_staging_surfaces_unaffected(self):
        # Fold r1 F1: the staging arm keys on ignored entries only. The
        # eligible candidate's checkout carries the tracked review record
        # under .ai-playbook/reviews (the landed vintage) and no docs/tmp
        # content, both clean staging surfaces, so the chain proceeds past
        # the staging arm and the worktree is reported as retained.
        path = self.eligible_candidate()
        self.assertTrue(
            (Path(path) / ".ai-playbook/reviews/2026-10-01-alpha-r1.md").is_file()
        )
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {self._porcelain_path(path)}: operator-controlled worktree retained",
            proc.stdout,
        )

    def test_sweep_locked_registration_skip(self):
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self._git(self.primary, "worktree", "lock", str(path))
        shutil.rmtree(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: locked registration", proc.stdout)
        self.assertIn(registered, self._registered_paths())

    def test_sweep_locked_on_disk_registration_skip_report_mode(self):
        # Fold r1 F4: the porcelain `locked` attribute is consulted at arm 2
        # for on-disk candidates too, so a locked worktree is reported with
        # the exact reason instead of walking the whole chain and only
        # failing at removal time.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self._git(self.primary, "worktree", "lock", str(path))
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: locked registration", proc.stdout)
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir(), "report mode removed the locked candidate")

    def test_sweep_locked_stale_deleted_branch_reports_unknown_oid(self):
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: the
        # locked arm stops before the branch resolution, so a stale locked
        # registration whose branch ref was deleted out-of-band still
        # reports the branch name with the explicit unknown OID; the
        # unresolvable ref is an observation, never a tool error or an
        # invented OID.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self._git(self.primary, "worktree", "lock", str(path))
        shutil.rmtree(path)
        self._git(self.primary, "update-ref", "-d", "refs/heads/wt-alpha")
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: locked registration", proc.stdout)
        self.assertIn(
            "branch-report: branch wt-alpha: skipped at unknown; "
            "reason: locked registration",
            proc.stdout,
        )
        self.assertIn(registered, self._registered_paths())

    def test_sweep_stale_detached_registration_skip(self):
        path = self.add_worktree("loose", detach=True)
        registered = self._porcelain_path(path)
        shutil.rmtree(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: stale detached registration", proc.stdout)
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: no
        # branch identity, so no branch-report line and no invented branch
        # or OID.
        self.assertNotIn("branch-report:", proc.stdout)

    def test_sweep_detached_on_disk_worktree_skip(self):
        self.seed_twin("2026-10-01-alpha.md")
        path = self.add_worktree("loose", detach=True)
        self.write_candidate_plan(path, "2026-10-01-alpha.md")
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {self._porcelain_path(path)}: detached HEAD worktree", proc.stdout)
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: no
        # branch identity, so no branch-report line and no invented branch
        # or OID.
        self.assertNotIn("branch-report:", proc.stdout)

    def test_sweep_zero_plan_files_on_branch_skip(self):
        self.seed_twin("2026-10-01-alpha.md")
        path = self.add_worktree("empty", branch="wt-empty")
        registered = self._porcelain_path(path)
        shutil.rmtree(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: zero plan files on branch", proc.stdout)

    def test_sweep_multiple_plan_files_on_branch_skip(self):
        self.seed_twin("2026-10-01-alpha.md")
        path = self.add_worktree("two", branch="wt-two")
        self.write_candidate_plan(path, "2026-10-01-alpha.md")
        self.write_candidate_plan(path, "2026-10-01-beta.md")
        registered = self._porcelain_path(path)
        shutil.rmtree(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: multiple plan files on branch", proc.stdout)

    def test_sweep_no_completed_twin_skip(self):
        self.seed_twin("2026-10-01-alpha.md")
        path = self.add_worktree("other", branch="wt-other")
        self.write_candidate_plan(path, "2026-10-01-beta.md")
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {self._porcelain_path(path)}: no completed twin in the primary HEAD tree",
            proc.stdout,
        )
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: the
        # branch-backed skip also reports the branch-report line carrying
        # the branch, the resolved tip OID, and the skip reason.
        self.assertIn(
            f"branch-report: branch wt-other: skipped at "
            f"{self.branch_oid('wt-other')}; reason: no completed twin in "
            "the primary HEAD tree",
            proc.stdout,
        )

    def test_sweep_live_session_execution_claim_skip(self):
        path = self.eligible_candidate()
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        claims = self.primary / "docs/tmp/execution-claims"
        claims.mkdir(parents=True, exist_ok=True)
        _write(
            claims / "2026-10-01-alpha.md",
            (
                "session: sess-sweep-test\n"
                "plan: docs/history/plans/2026-10-01-alpha.md\n"
                f"created: {stamp}\n"
                f"updated: {stamp}\n"
            ).encode("utf-8"),
        )
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {self._porcelain_path(path)}: live-session evidence: execution-claims claim 2026-10-01-alpha.md",
            proc.stdout,
        )
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: the
        # branch-backed skip also reports the branch-report line carrying
        # the branch, the resolved tip OID, and the skip reason.
        self.assertIn(
            f"branch-report: branch wt-alpha: skipped at "
            f"{self.branch_oid('wt-alpha')}; reason: live-session evidence: "
            "execution-claims claim 2026-10-01-alpha.md",
            proc.stdout,
        )
        # Fold r1 F8: the skip verdict must witness the candidate's
        # survival in report mode.
        self.assertIn(self._porcelain_path(path), self._registered_paths())
        self.assertTrue(Path(path).is_dir(), "report mode removed the skipped candidate")

    def test_sweep_live_session_done_lock_witness_freshness_bound(self):
        path = self.eligible_candidate()
        cand_toplevel = self._toplevel(path)
        keyed = self.done_lock_root / hashlib.sha256(cand_toplevel.encode("utf-8")).hexdigest()[:16]
        keyed.mkdir(parents=True)
        # The lock root resolves through DONE_LOCK_ROOT exactly as the
        # script resolves it, so the run carries the fixture's root the way
        # a done run that acquired with a custom root carries its env.
        root_env = {"DONE_LOCK_ROOT": str(self.done_lock_root)}
        proc = self.run_sweep(env_overrides=root_env)
        self.assertOutcome(proc, 0, "pass")
        self.assertIn("live-session evidence: a done lock keyed to this worktree", proc.stdout)
        # Past the freshness bound the witness no longer holds.
        stale_stamp = time.time() - 3 * 3600
        os.utime(keyed, (stale_stamp, stale_stamp))
        proc = self.run_sweep(env_overrides=root_env)
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {self._porcelain_path(path)}: operator-controlled worktree retained",
            proc.stdout,
        )

    def test_sweep_post_landing_commits_on_branch_skip(self):
        path = self.eligible_candidate()
        _write(Path(path) / "notes.md", b"post-landing work\n")
        self._commit_all(path, "work past the landing", date=self.EPOCH + 100)
        registered = self._porcelain_path(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: post-landing commits on branch",
            proc.stdout,
        )
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: the
        # branch-backed skip also reports the branch-report line carrying
        # the branch, the resolved tip OID, and the skip reason.
        self.assertIn(
            f"branch-report: branch wt-alpha: skipped at "
            f"{self.branch_oid('wt-alpha')}; reason: post-landing commits "
            "on branch",
            proc.stdout,
        )
        # Fold r1 F8: the skip verdict must witness the candidate's
        # survival in report mode.
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir(), "report mode removed the skipped candidate")

    def test_sweep_pre_landing_out_of_scope_commit_reported(self):
        # Fold r1 F2a: the committer date is not a content check. A branch
        # commit at or before the twin's introduction whose content never
        # reached the landing passes the date arm, so the content-scope
        # sub-arm requires every changed path since the merge base to sit
        # inside the introduction commit's touched set; an out-of-scope
        # path is reported and the candidate is never removed.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        _write(Path(path) / "extra-unlanded.md", b"work that never landed\n")
        self._commit_all(path, "out-of-scope pre-landing work", date=self.EPOCH)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: branch content outside the landing's file set",
            proc.stdout,
        )
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir(), "report mode removed the reported candidate")

    def test_sweep_readded_twin_anchors_on_earliest_add(self):
        # Fold r1 F2b: a delete-plus-re-add of the completed twin re-anchors
        # the previous `-1` form on the re-add, widening the post-landing
        # window; the anchor is the MINIMUM %ct across every add commit, so
        # a branch commit predating the re-add (EPOCH+10 vs the EPOCH add)
        # is a post-landing commit, not a removable one.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self.write_candidate_plan(
            path,
            "2026-10-01-alpha.md",
            body="# Plan worktree copy, amended vintage\n",
            date=self.EPOCH + 10,
        )
        completed = self.primary / "docs/history/plans/completed" / "2026-10-01-alpha.md"
        self._git(self.primary, "rm", "-q", str(completed))
        self._commit_all(self.primary, "plan: drop the completed twin", date=self.EPOCH + 20)
        _write(completed, b"# Plan\n\nre-added vintage\n")
        self._commit_all(self.primary, "plan: re-add the completed twin", date=self.EPOCH + 30)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: post-landing commits on branch", proc.stdout
        )
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir(), "report mode removed the reported candidate")

    def test_sweep_poison_stale_registration_reported_enumeration_continues(self):
        # Fold r1 F3: one stale registration whose branch ref no longer
        # resolves (the loose ref deleted out-of-band while the
        # registration stands) raises a git plumbing failure during that
        # candidate's evaluation; the candidate is reported with the
        # evaluation-error reason, later candidates still get verdicts, and
        # the run ends exit 0 OUTCOME: pass instead of aborting
        # mid-enumeration.
        first = self.eligible_candidate(slug="one", basename="2026-10-01-one.md")
        second = self.eligible_candidate(slug="two", basename="2026-10-01-two.md")
        first_registered = self._porcelain_path(first)
        second_registered = self._porcelain_path(second)
        shutil.rmtree(first)
        shutil.rmtree(second)
        self.assertEqual(self._git(self.primary, "rev-parse", "--verify", "wt-one", check=False).returncode, 0)
        ref = self.primary / ".git" / "refs" / "heads" / "wt-one"
        self.assertTrue(ref.is_file(), "expected a loose branch ref to delete")
        ref.unlink()
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {first_registered}: evaluation error: ", proc.stdout)
        self.assertIn(
            f"report {second_registered}: stale registration drain eligible",
            proc.stdout,
        )
        self.assertIn(first_registered, self._registered_paths())
        self.assertIn(second_registered, self._registered_paths())
        # The apply behaves the same for the unreadable candidate: its
        # registration survives the evaluation error while the eligible
        # sibling drains with its ref preserved.
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {first_registered}: evaluation error: ", proc.stdout)
        self.assertIn(f"remove {second_registered}", proc.stdout)
        self.assertIn(first_registered, self._registered_paths())
        self.assertNotIn(second_registered, self._registered_paths())
        self.assertFalse(self._branch_gone("wt-two"))

    # -- the authentic-hold refusal under --apply (four shapes) -------------

    def test_sweep_apply_missing_exports_refuses_naming_requirement(self):
        path = self.eligible_candidate()
        proc = self.run_sweep("--apply")
        self.assertOutcome(proc, 3, "tool_error")
        self.assertIn("authentic hold", proc.stderr)
        self.assertIn("DONE_LOCK_DIR", proc.stderr)
        self.assertTrue(Path(path).is_dir(), "removal happened without an authentic hold")

    def test_sweep_apply_meta_less_lock_refuses(self):
        path = self.eligible_candidate()
        proc = self.run_sweep("--apply", env_overrides=self.hold_env(metaless=True))
        self.assertOutcome(proc, 3, "tool_error")
        self.assertIn("authentic hold", proc.stderr)
        self.assertIn("meta.env", proc.stderr)
        self.assertTrue(Path(path).is_dir())

    def test_sweep_apply_token_mismatched_lock_refuses(self):
        path = self.eligible_candidate()
        env = self.hold_env(token="the-real-token")
        env["DONE_LOCK_TOKEN"] = "a-forged-token"
        proc = self.run_sweep("--apply", env_overrides=env)
        self.assertOutcome(proc, 3, "tool_error")
        self.assertIn("lock_token", proc.stderr)
        self.assertTrue(Path(path).is_dir())

    def test_sweep_apply_repo_root_mismatched_lock_refuses(self):
        path = self.eligible_candidate()
        proc = self.run_sweep(
            "--apply", env_overrides=self.hold_env(repo_root="/elsewhere/other-repo")
        )
        self.assertOutcome(proc, 3, "tool_error")
        self.assertIn("repo_root", proc.stderr)
        self.assertTrue(Path(path).is_dir())

    # -- removal, both candidate kinds, and the merge lock ------------------

    def test_sweep_apply_preserves_on_disk_candidate_full_pass(self):
        # Plan gate-removal-closeout-accounting Task 2: the apply mode
        # removes only stale registrations. A fully passing on-disk
        # candidate keeps its worktree, its registration, and its branch
        # ref (the OUTCOME: pass never infers a deletion); the run still
        # cleans up the twin temp file and never takes the merge lock
        # without a registration drain.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        oid_before = self.branch_oid("wt-alpha")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: operator-controlled worktree retained "
            "(on-disk worktree and artifacts preserved; branch refs are never removed by the sweep)",
            proc.stdout,
        )
        self.assertNotIn(f"remove {registered}", proc.stdout)
        self.assertTrue(Path(path).is_dir(), "the on-disk worktree was removed")
        self.assertIn(registered, self._registered_paths())
        self.assertFalse(self._branch_gone("wt-alpha"))
        self.assertEqual(self.branch_oid("wt-alpha"), oid_before, "the branch ref moved")
        self.assertEqual(list((self.primary / "docs/tmp").glob("sweep-twin-*")), [], "twin temp file leaked")
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the merge lock was taken without a drain")

    def test_sweep_apply_removes_stale_registration_scoped(self):
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        oid_before = self.branch_oid("wt-alpha")
        shutil.rmtree(path)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"remove {registered}", proc.stdout)
        self.assertNotIn(registered, self._registered_paths())
        admin = self.primary / ".git" / "worktrees" / Path(registered).name
        self.assertFalse(admin.exists(), "the administrative dir survived the scoped release")
        # The branch ref is preserved with an unchanged OID: the drain
        # never infers a branch deletion from the gate's OUTCOME: pass.
        self.assertIn(
            f"registration: drained {registered} (stale registration "
            "only; branch refs are never removed by the sweep)",
            proc.stdout,
        )
        self.assertFalse(self._branch_gone("wt-alpha"))
        self.assertEqual(self.branch_oid("wt-alpha"), oid_before, "the stale drain moved the branch ref")
        self.assertFalse(Path(path).exists(), "the stale release recreated a tree")

    def test_sweep_stale_siblings_drain_together(self):
        first = self.eligible_candidate(slug="one", basename="2026-10-01-one.md")
        second = self.eligible_candidate(slug="two", basename="2026-10-01-two.md")
        first_registered = self._porcelain_path(first)
        second_registered = self._porcelain_path(second)
        first_oid = self.branch_oid("wt-one")
        second_oid = self.branch_oid("wt-two")
        shutil.rmtree(first)
        shutil.rmtree(second)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"remove {first_registered}", proc.stdout)
        self.assertIn(f"remove {second_registered}", proc.stdout)
        # Both drains preserve their branch refs unchanged.
        self.assertFalse(self._branch_gone("wt-one"))
        self.assertFalse(self._branch_gone("wt-two"))
        self.assertEqual(self.branch_oid("wt-one"), first_oid)
        self.assertEqual(self.branch_oid("wt-two"), second_oid)

    def test_sweep_foreign_prunable_registration_defers_stale_release(self):
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        shutil.rmtree(path)
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        foreign = self.add_worktree("foreign", branch="wt-foreign", parent=elsewhere)
        foreign_registered = self._porcelain_path(foreign)
        shutil.rmtree(foreign)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: foreign prunable registration present: ", proc.stdout)
        self.assertIn(foreign_registered, proc.stdout)
        # The deferred stale candidate stays registered, and the foreign
        # registration survives: a destructive prune would have removed it.
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(
            (self.primary / ".git" / "worktrees" / Path(registered).name).exists(),
            "the deferred stale release removed the administrative dir",
        )
        self.assertTrue(
            (self.primary / ".git" / "worktrees" / "proj-wt-foreign").exists(),
            "a destructive prune removed the foreign registration",
        )

    def test_sweep_locked_on_disk_registration_skip_under_apply(self):
        # Fold r1 F4 re-aim (2026-10-08): a locked on-disk candidate is now
        # skipped at arm 2 with the exact `locked registration` reason in
        # both modes, so this former removal-failure test (which walked the
        # whole chain and only died at removal time, degrading the run to
        # OUTCOME: fail) pins the new skip under --apply instead.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self._git(self.primary, "worktree", "lock", str(path))
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: locked registration", proc.stdout)
        self.assertTrue(Path(path).is_dir(), "the locked worktree was removed")
        self.assertIn(registered, self._registered_paths())
        self.assertFalse(self._branch_gone("wt-alpha"))
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the merge lock was taken without removals")

    def test_sweep_merge_lock_held_refusal_is_tool_error(self):
        # The apply mode queues stale-registration drains only, so the
        # contended merge-lock acquire is reached with a stale candidate:
        # the held merge lock refuses it as a tool error and the
        # registration and the branch ref both survive.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        oid_before = self.branch_oid("wt-alpha")
        shutil.rmtree(path)
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        acquired = subprocess.run(
            ["bash", str(self.primary / "scripts" / "done-lock.sh"), "merge-acquire", "--label", "blocker"],
            capture_output=True,
            text=True,
            cwd=str(self.primary),
            env={
                **os.environ,
                "MERGE_LOCK_ROOT": str(self.merge_lock_root),
                "MERGE_LOCK_HOLDER_PID": str(holder.pid),
            },
        )
        self.assertEqual(acquired.returncode, 0, acquired.stderr)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 3, "tool_error")
        merge_lines = [line for line in proc.stderr.splitlines() if line.startswith("merge-lock: ")]
        self.assertTrue(merge_lines, "no merge-lock re-prefixed evidence on stderr")
        self.assertNotIn("OUTCOME: fail", proc.stderr, "the acquire's final OUTCOME line was not dropped")
        self.assertIn(registered, self._registered_paths(), "a drain ran while the merge lock was held")
        self.assertFalse(self._branch_gone("wt-alpha"))
        self.assertEqual(self.branch_oid("wt-alpha"), oid_before, "the branch ref moved")

    # -- the gate on the completed twin -------------------------------------

    def test_sweep_gate_empty_owned_set_is_permanent_skip(self):
        self.seed_twin("2026-10-01-alpha.md", cites=None)
        path = self.add_worktree("alpha", branch="wt-alpha")
        self.write_candidate_plan(path, "2026-10-01-alpha.md")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {self._porcelain_path(path)}: no owned review citations",
            proc.stdout,
        )
        self.assertTrue(Path(path).is_dir(), "a citation-less plan was removed")

    def test_sweep_gate_fail_evidence_reprefixed_and_never_removes(self):
        # The twin cites a record absent from the primary reviews home.
        self.seed_twin(
            "2026-10-01-alpha.md",
            cites=".ai-playbook/reviews/2026-10-01-missing-r1.md",
            write_record=False,
        )
        path = self.add_worktree("alpha", branch="wt-alpha")
        self.write_candidate_plan(path, "2026-10-01-alpha.md")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {self._porcelain_path(path)}: gate-removal fail", proc.stdout)
        self.assertIn(
            "gate: missing: .ai-playbook/reviews/2026-10-01-missing-r1.md",
            proc.stdout,
        )
        self.assertNotIn("OUTCOME: fail", proc.stdout, "a mid-stream gate OUTCOME line leaked")
        self.assertTrue(Path(path).is_dir(), "a gate-failed candidate was removed")

    def test_sweep_gate_tool_error_evidence_carries_stderr(self):
        # Fold r1 F5: the gate child prints its tool_error diagnostics on
        # stderr, so the evidence duty must capture the second stream. An
        # unresolvable reviews home (an empty reviews_dir facts key) makes
        # the gate child exit tool_error with its diagnostic on stderr and
        # no stdout evidence, so every `gate: ` line here is necessarily
        # stderr-sourced.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \"\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: gate-removal tool_error", proc.stdout)
        gate_lines = [line for line in proc.stdout.splitlines() if line.startswith("gate: ")]
        self.assertTrue(gate_lines, "no gate: evidence line for a tool_error gate child")
        self.assertTrue(
            any("cannot resolve reviews_dir" in line for line in gate_lines),
            f"the gate child's stderr diagnostic is missing from the evidence: {gate_lines}",
        )
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir(), "a gate tool_error candidate was removed")

    # -- invocation surface -------------------------------------------------

    # -- Task 2: exact-tree accounting, retained tips, and the hermetic env -

    def test_hermetic_git_env_clears_inherited_and_pins_home_locale(self):
        # Plan gate-removal-closeout-accounting Task 2: the fixture env
        # helper clears every inherited GIT_* variable, moves HOME into the
        # fixture tree, pins the deterministic locale and timezone, and
        # still applies the caller's explicit extras.
        os.environ["GIT_TRACE_TASK2_LEAK"] = "1"
        try:
            env = _hermetic_git_env(self.root, GIT_AUTHOR_NAME="t")
        finally:
            os.environ.pop("GIT_TRACE_TASK2_LEAK", None)
        self.assertNotIn("GIT_TRACE_TASK2_LEAK", env)
        self.assertEqual(Path(env["HOME"]), self.root / "fixture-home")
        self.assertTrue((self.root / "fixture-home").is_dir())
        for key, value in FIXTURE_LOCALE_ENV.items():
            self.assertEqual(env[key], value)
        self.assertEqual(env["GIT_AUTHOR_NAME"], "t")
        # A git subprocess launched with the helper's env sees the pinned
        # identity, never the host's.
        env = _hermetic_git_env(self.root, **self.GIT_IDENTITY)
        proc = subprocess.run(
            ["git", "var", "GIT_AUTHOR_IDENT"],
            capture_output=True, text=True, env=env, cwd=str(self.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("<t@t>", proc.stdout)

    def test_sweep_exact_tree_candidate_reported_and_retained(self):
        # Plan gate-removal-closeout-accounting Task 2: a tip whose complete
        # tree equals a destination-history commit's tree is accounted
        # without ancestry or an archive twin, and the non-ancestor branch
        # stays retained in report mode.
        path = self.exact_tree_candidate()
        registered = self._porcelain_path(path)
        self.write_slug_manifest("2026-10-01-alpha.md", "wt-alpha", path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: operator-controlled worktree retained",
            proc.stdout,
        )
        self.assertIn(
            "branch-report: branch wt-alpha: disposition exact-tree-accounted at ",
            proc.stdout,
        )
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir())
        self.assertFalse(self._branch_gone("wt-alpha"))

    def test_sweep_exact_tree_candidate_apply_preserves_worktree_and_ref(self):
        # The apply mode reports the exact-tree disposition and preserves
        # the on-disk worktree, its artifacts, and the branch ref.
        path = self.exact_tree_candidate()
        registered = self._porcelain_path(path)
        self.write_slug_manifest("2026-10-01-alpha.md", "wt-alpha", path)
        oid_before = self.branch_oid("wt-alpha")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: operator-controlled worktree retained",
            proc.stdout,
        )
        self.assertIn(
            "branch-report: branch wt-alpha: disposition exact-tree-accounted at ",
            proc.stdout,
        )
        self.assertNotIn(f"remove {registered}", proc.stdout)
        self.assertTrue(Path(path).is_dir())
        self.assertIn(registered, self._registered_paths())
        self.assertEqual(self.branch_oid("wt-alpha"), oid_before)

    def test_sweep_legacy_only_candidate_reports_evidence_and_retains(self):
        # A branch accounted ONLY by the legacy changed-path scope: the
        # disposition reports the evidence and the retention, and neither
        # the worktree nor the ref is removed.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self.write_slug_manifest("2026-10-01-alpha.md", "wt-alpha", path)
        oid_before = self.branch_oid("wt-alpha")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: operator-controlled worktree retained",
            proc.stdout,
        )
        self.assertIn("disposition retained at", proc.stdout)
        self.assertIn("legacy changed-path scope is accounting evidence only", proc.stdout)
        self.assertTrue(Path(path).is_dir())
        self.assertEqual(self.branch_oid("wt-alpha"), oid_before)

    def test_sweep_advanced_candidate_retained_under_apply(self):
        # A branch that advanced past the landing (post-landing commits): a
        # chain skip in both modes; the apply preserves the worktree and the
        # ref.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        _write(Path(path) / "advanced.md", b"post-landing work\n")
        self._commit_all(path, "work past the landing", date=self.EPOCH + 100)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: post-landing commits on branch", proc.stdout)
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir())
        self.assertFalse(self._branch_gone("wt-alpha"))

    def test_sweep_moved_ref_apply_preserves_worktree_and_artifacts(self):
        # A moved ref (the branch tip re-pointed at an advanced commit
        # before the run): the moved tip is reported and the apply preserves
        # the worktree, its artifacts, and the moved ref itself.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self.write_slug_manifest("2026-10-01-alpha.md", "wt-alpha", path)
        _write(Path(path) / "moved.md", b"unlanded tip work\n")
        self._commit_all(path, "work: moved tip", date=self.EPOCH + 500)
        moved_oid = self.branch_oid("wt-alpha")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: post-landing commits on branch", proc.stdout)
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir())
        self.assertEqual(self.branch_oid("wt-alpha"), moved_oid)

    def test_sweep_sibling_checkout_reports_shared_branch_and_retains(self):
        # A sibling worktree checkout on the same branch: the gate's guard
        # names the sibling, the disposition is retained, and the candidate
        # worktree and ref both survive the apply.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self.write_slug_manifest("2026-10-01-alpha.md", "wt-alpha", path)
        sibling = self.add_worktree("sib", branch="wt-sib-tmp")
        self._git(sibling, "checkout", "-q", "--ignore-other-worktrees", "wt-alpha")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            f"report {registered}: operator-controlled worktree retained",
            proc.stdout,
        )
        self.assertIn("branch shared with 1 live worktree(s)", proc.stdout)
        self.assertIn(str(sibling.resolve()), proc.stdout)
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir())
        self.assertFalse(self._branch_gone("wt-alpha"))

    def test_sweep_dirty_state_preserved_under_apply(self):
        # Dirty/active state: the apply preserves the dirty worktree and the
        # ref exactly like report mode.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        _write(Path(path) / "scratch-untracked.md", b"untracked\n")
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: dirty worktree", proc.stdout)
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir())
        self.assertFalse(self._branch_gone("wt-alpha"))

    def test_sweep_passes_legacy_manifest_filename_for_slug_twin(self):
        # The twin's temporary filename differs from the candidate's slug;
        # the sweep resolves the candidate's manifest at the LEGACY filename
        # and the gate still binds the branch (the disposition flows).
        path = self.exact_tree_candidate()
        registered = self._porcelain_path(path)
        manifest = self.write_slug_manifest("2026-10-01-alpha.md", "wt-alpha", path)
        manifest.rename(manifest.parent / "migration-manifest.json")
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(
            "branch-report: branch wt-alpha: disposition exact-tree-accounted at ",
            proc.stdout,
        )
        self.assertIn(
            f"report {registered}: operator-controlled worktree retained",
            proc.stdout,
        )

    def test_sweep_manifest_identity_mismatch_is_preserved(self):
        # A manifest binding a foreign branch: the identity mismatch refuses
        # the twin gate run and the apply preserves the worktree, the
        # registration, and the real branch.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self.write_slug_manifest("2026-10-01-alpha.md", "wt-foreign-branch", path)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: gate-removal fail", proc.stdout)
        self.assertIn("exact-branch identity mismatch", proc.stdout)
        self.assertIn("wt-foreign-branch", proc.stdout)
        self.assertIn(registered, self._registered_paths())
        self.assertTrue(Path(path).is_dir())
        self.assertFalse(self._branch_gone("wt-alpha"))

    def test_sweep_stale_drain_carries_disposition_and_preserves_ref(self):
        # A stale registration drain under --apply carries the gate's
        # disposition into the registration line and preserves the branch
        # ref with an unchanged OID.
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        self.write_slug_manifest("2026-10-01-alpha.md", "wt-alpha", path)
        oid_before = self.branch_oid("wt-alpha")
        shutil.rmtree(path)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"remove {registered}", proc.stdout)
        self.assertIn(
            f"registration: drained {registered} (stale registration "
            f"only; branch wt-alpha ref preserved, disposition retained at {oid_before})",
            proc.stdout,
        )
        self.assertNotIn(registered, self._registered_paths())
        self.assertEqual(self.branch_oid("wt-alpha"), oid_before)

    def test_sweep_usage_missing_target_is_tool_error(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "sweep", "--apply"],
            capture_output=True,
            text=True,
            cwd=str(self.root),
        )
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("usage", proc.stderr)
        self.assertIn("--target", proc.stderr)

    def test_sweep_help_is_metadata_exit(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "sweep", "--target", str(self.primary), "--help"],
            capture_output=True,
            text=True,
            cwd=str(self.root),
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("usage:", proc.stdout)
        self.assertNotIn("OUTCOME:", proc.stdout)

    def test_sweep_unresolvable_target_is_tool_error(self):
        proc = self.run_sweep(target=self.root / "no-such-checkout")
        self.assertOutcome(proc, 3, "tool_error")
        self.assertIn("target directory not found", proc.stderr)


class _BranchCloseoutFixture:
    """Shared git fixture for the exact-branch closeout witnesses: a primary
    checkout plus a run worktree whose migration manifest records the branch
    at transfer time. Carries only helpers, never test methods, so each
    concrete class collects its own tests."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-branch-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        self._git(self.primary, "init", "-q", "-b", "main")
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        self._commit_all(self.primary, "init: fixture repo")
        self.worktree = self.root / "proj-wt-run"
        self._git(self.primary, "worktree", "add", "-q", "-b", "wt-run", str(self.worktree))

    def _git(self, repo: Path, *args: str, check: bool = True):
        env = _hermetic_git_env(self.root, **self.GIT_IDENTITY)
        proc = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env
        )
        if check and proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc

    def _commit_all(self, repo: Path, message: str) -> None:
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-q", "-m", message)

    def _branch_oid(self, branch: str) -> str:
        return self._git(self.primary, "rev-parse", branch).stdout.strip()

    def _rebind_manifest_branch(self, manifest_path: Path, branch: str) -> None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["branch"][-1]["branch"] = branch
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def _seed_migration_manifest(self, landed: bool) -> Path:
        """A migration manifest at the derived gate path: the branch record
        binds the worktree to wt-run at transfer time, one migrated entry
        verified under the target; when landed, the branch's work commit is
        cherry-picked into the primary so the branch is content-scope
        accounted, and the archive twin exists for that proof."""
        reviews = self.primary / ".ai-playbook/reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        record = reviews / "2026-10-08-plan-review-x-exec-r1.md"
        _write(record, b"r1\n")
        plan_rel = "docs/history/plans/2026-10-08-x.md"
        _write(
            self.primary / plan_rel,
            b"# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md\n",
        )
        if landed:
            # The branch's work commit FIRST (it must predate the landing's
            # introduction commit for the post-landing arm), mirrored into
            # the primary by content: the branch commit stays
            # merge-unreachable, so the removable arm exercises the
            # content-scope proof against a single squash landing commit
            # whose touched set covers the branch's file.
            _write(self.worktree / "feature.txt", b"work\n")
            self._commit_all(self.worktree, "work: branch feature")
        self._commit_all(self.primary, "plan bytes at the plans root (landing)")
        (self.primary / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
        self._git(self.primary, "mv", plan_rel, "docs/history/plans/completed/2026-10-08-x.md")
        # One squash landing commit: the archive move plus the branch's
        # feature file (written now, committed with the move), so the
        # touched set models the witnessed squash shape (a squash landing
        # touches every file its branch touched).
        if landed:
            _write(self.primary / "feature.txt", b"work\n")
        self._commit_all(self.primary, "land: squash (archive move + feature)")
        # The gate reads the run's own plan copy in the worktree for its
        # owned citations; the landed bytes live in the primary tree.
        _write(
            self.worktree / plan_rel,
            b"# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md\n",
        )
        # The producer contract's slug directory: the gate's default lookup
        # derives <PLAN_SLUG> = x from the dated plan 2026-10-08-x.md
        # (leading date and extension stripped), so the manifest binds only
        # when it sits under the date-stripped session directory.
        manifest_dir = self.primary / "docs/tmp/execute-plan/x"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "closeout-migration.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "migrated": [
                        {
                            "source": ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                            "destination": ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                            "verified": True,
                        }
                    ],
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [{"branch": "wt-run", "source": str(self.worktree)}],
                }
            ),
            encoding="utf-8",
        )
        return manifest_path

    def _run_gate(self, *extra: str) -> tuple[int, str, str]:
        plan = self.worktree / "docs/history/plans/2026-10-08-x.md"
        return _run_cli(
            "gate-removal",
            "--plan", str(plan),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            *extra,
            cwd=self.worktree,
        )

    def _run_gate_branch_only(self, branch: str, manifest: Path | None = None) -> tuple[int, str, str]:
        plan = getattr(
            self, "branch_only_plan",
            self.primary / "docs/history/plans/completed/2026-10-08-x.md",
        )
        return _run_cli(
            "gate-removal",
            "--plan", str(plan),
            "--target", str(self.primary),
            "--branch", branch,
            "--migration-manifest", str(manifest or (self.primary / "docs/tmp/execute-plan/x/closeout-migration.json")),
            cwd=self.primary,
        )

    def _run_gate_with_midcheck_mutation(self, mutate) -> tuple[int, str, str]:
        """Run cmd_gate_removal in-process with a subprocess.run wrapper
        that mutates the repository immediately after the proven-OID
        capture, so the ref re-compare arm is exercisable deterministically.
        The mutate callable receives the hermetic run helper to use for its
        own git calls."""
        real_run = subprocess.run
        state = {"fired": False}

        def hermetic_run(argv, *a, **k):
            if "env" not in k:
                k["env"] = _hermetic_git_env(self.root)
            return real_run(argv, *a, **k)

        def fake_run(argv, *a, **k):
            proc = hermetic_run(argv, *a, **k)
            if (
                not state["fired"]
                and isinstance(argv, list)
                and argv[:2] == ["git", "-C"]
                and "rev-parse" in argv
                and "--verify" in argv
                and proc.returncode == 0
            ):
                state["fired"] = True
                mutate(hermetic_run)
            return proc

        argv = [
            # The flat parser (Task 4) takes the gate's options only; main
            # consumes the dispatch token before parsing.
            "--plan", str(self.worktree / "docs/history/plans/2026-10-08-x.md"),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
        ]
        args = MODULE.build_gate_removal_parser().parse_args(argv)
        with mock.patch.object(MODULE.subprocess, "run", side_effect=fake_run):
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                with contextlib.redirect_stderr(io.StringIO()) as errbuf:
                    code = MODULE.cmd_gate_removal(args)
        return code, buf.getvalue(), errbuf.getvalue()


class GateRemovalBranchCloseoutTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] Exact-branch closeout witnesses (plan
    done-closeout-ceremony-friction Task 3, re-aimed by
    gate-removal-closeout-accounting Task 2): a real git fixture pair of a
    primary checkout and a run worktree whose migration manifest records the
    branch at transfer time, exercising the ancestry-accounted,
    exact-tree-accounted, legacy-evidence, preserve (shared branch), preserve
    (unlanded work), and identity-mismatch arms plus the ref re-compare
    anomalies."""

    def test_legacy_content_scope_is_evidence_only(self):
        # Plan gate-removal-closeout-accounting Task 2: the fixture's
        # squash-landed branch is accounted ONLY by the legacy changed-path
        # scope, which is evidence now: the branch is retained with the
        # evidence named, no force-delete instruction is printed, and the
        # worktree cleanup stays authorized beside the branch verdict.
        self._seed_migration_manifest(landed=True)
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("branch-closeout: preserve branch wt-run at ", out)
        self.assertIn(
            "changed-path scope: content landed inside the landing's file set "
            "(legacy evidence only)",
            out,
        )
        self.assertIn("never permits deleting a non-ancestor branch", out)
        self.assertNotIn("git branch -D", out)
        self.assertNotIn("proof-checked force delete", out)
        self.assertNotIn("removable", out)
        self.assertIn(
            "branch-disposition: branch=wt-run disposition=retained oid=", out
        )
        self.assertIn("removal: git worktree remove --force", out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", "wt-run", check=False).returncode,
            0,
            "the evidence-only proof deleted the branch",
        )

    def test_ancestry_accounted_branch_reports_proof_and_expected_oid(self):
        # An ancestry-accounted branch (its tip is an ancestor of
        # destination history) reports the proof and the proven OID, and the
        # operator closeout line names the expected-OID delete.
        self._seed_migration_manifest(landed=True)
        self._git(self.primary, "merge", "-q", "--no-edit", "wt-run")
        expected = self._branch_oid("wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch wt-run ancestry-accounted at {expected}", out)
        self.assertIn(f"expected OID {expected}", out)
        self.assertIn(
            f"branch-disposition: branch=wt-run disposition=ancestry-accounted oid={expected}",
            out,
        )
        self.assertNotIn("git branch -D", out)

    def test_accounted_worktree_report_states_only_branch_evidence(self):
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 1: the
        # ancestry statement carries only verified branch facts (branch,
        # proven OID, ancestry result) in linked-worktree mode too - the
        # guard checks report the worktree and artifact facts themselves,
        # so the verdict sentence claims neither. The removal instruction
        # and the structured disposition stay intact.
        self._seed_migration_manifest(landed=True)
        self._git(self.primary, "merge", "-q", "--no-edit", "wt-run")
        expected = self._branch_oid("wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch wt-run ancestry-accounted at {expected}", out)
        self.assertNotIn("worktree binds", out)
        self.assertNotIn("migrated artifacts verified", out)
        self.assertIn(
            f"branch: operator closeout may delete branch wt-run at "
            f"expected OID {expected}",
            out,
        )
        self.assertIn(
            f"branch-disposition: branch=wt-run disposition=ancestry-accounted oid={expected}",
            out,
        )

    def test_exact_tree_branch_accounted_without_twin_or_ancestry(self):
        # Plan gate-removal-closeout-accounting Task 2: a tip whose complete
        # tree equals a destination-history commit's tree is landed WITHOUT
        # ancestry or an archive twin, while the non-ancestor branch itself
        # stays retained.
        self._seed_migration_manifest(landed=True)
        landing_tree = self._git(self.primary, "rev-parse", "HEAD^{tree}").stdout.strip()
        root = self._git(self.primary, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
        snap = self._git(
            self.primary, "commit-tree", landing_tree, "-p", root, "-m", "snapshot vintage"
        ).stdout.strip()
        self._git(self.primary, "branch", "wt-snap", snap)
        self._git(self.worktree, "checkout", "-q", "wt-snap")
        self._rebind_manifest_branch(
            self.primary / "docs/tmp/execute-plan/x/closeout-migration.json", "wt-snap"
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch wt-snap exact-tree-accounted at {snap}", out)
        self.assertIn("the non-ancestor branch is retained", out)
        self.assertIn(
            f"branch-disposition: branch=wt-snap disposition=exact-tree-accounted oid={snap}",
            out,
        )
        # No archive twin is needed for the accounting: the landing's
        # completed twin predates this fixture branch, and the verdict names
        # the tree match, not the twin.
        self.assertNotIn("git branch -D", out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", "wt-snap", check=False).returncode,
            0,
            "the exact-tree-only branch was deleted",
        )

    def test_shared_branch_preserved(self):
        # A live sibling worktree on the same branch: the records and
        # identity verify, the branch verdict is preserve naming the
        # sibling, and the failed guard holds the worktree removal (the
        # on-disk worktree stays retained with the ref).
        self._seed_migration_manifest(landed=True)
        sibling = self.root / "proj-wt-sibling"
        # Git refuses a second checkout of one branch by default; the
        # duplicated-branch porcelain state this arm models is real but
        # reachable only through the operator override flag.
        self._git(self.primary, "worktree", "add", "-q", "-b", "wt-temp-sib", str(sibling))
        self._git(sibling, "checkout", "-q", "--ignore-other-worktrees", "wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch-closeout: preserve branch wt-run", out)
        self.assertIn("live worktree(s)", out)
        self.assertIn(str(sibling), out)
        self.assertIn("held: the branch disposition above names a failed guard", out)
        self.assertNotIn("removal: git worktree remove", out)

    def test_unlanded_branch_preserved_and_reported(self):
        # Branch commits the landing does not account for: the identity and
        # records verify, and the branch is retained with the unaccounted
        # reason reported (post-landing activity or content outside the
        # landing's file set), never silently deleted.
        self._seed_migration_manifest(landed=True)
        _write(self.worktree / "unlanded.txt", b"not landed\n")
        self._commit_all(self.worktree, "work: not landed anywhere")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertIn("branch-closeout: preserve branch wt-run", out)
        self.assertIn("branch: preserve wt-run and report", out)
        self.assertTrue(
            "outside the landing's file set" in out or "post-landing commits" in out,
            out,
        )

    def test_identity_mismatch_refuses_removal(self):
        # The manifest binds the worktree to wt-run but the checkout was
        # re-bound to another branch: the exact-branch identity refuses the
        # removal outright (OUTCOME: fail).
        self._seed_migration_manifest(landed=True)
        self._git(self.worktree, "checkout", "-q", "-b", "wt-other")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("exact-branch identity mismatch", out)
        self.assertIn("wt-other", out)
        self.assertIn("wt-run", out)

    def test_missing_artifact_guard_holds_worktree_removal(self):
        # A migrated artifact recorded verified whose destination is absent
        # under the target: the guard retains the branch, names the missing
        # destination, and holds the worktree removal (the failed artifact
        # check withdraws the cleanup authorization; the on-disk worktree
        # stays retained with the ref and the run fails).
        manifest_path = self._seed_migration_manifest(landed=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["migrated"].append(
            {
                "source": ".ai-playbook/reviews/2026-10-08-vanished-artifact.md",
                "destination": ".ai-playbook/reviews/2026-10-08-vanished-artifact.md",
                "verified": True,
            }
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch-closeout: preserve branch wt-run at ", out)
        self.assertIn("migrated artifact(s) missing under the target", out)
        self.assertIn(
            "branch-disposition: branch=wt-run disposition=retained oid=", out
        )
        self.assertIn("held: the branch disposition above names a failed guard", out)
        self.assertNotIn("removal: git worktree remove", out)
        self.assertTrue(
            Path(self.worktree).is_dir(), "the guarded worktree was removed"
        )

    def test_expired_gate_report_destination_reports_only_and_passes(self):
        # The cross-run swept-artifact shape (the 2026-10-31 closeout-gates
        # trio, landed 52750a1fe; shared-slug second witness): a verified destination under the done-session
        # gate-reports home expired by the sanctioned docs/tmp sweep is the
        # owning run's disposition - report-only, never a hold on this
        # run's branch or worktree removal.
        manifest_path = self._seed_migration_manifest(landed=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["migrated"].append(
            {
                "source": "docs/tmp/done-session/gate-reports/report.txt",
                "destination": (
                    "docs/tmp/done-session/gate-reports/"
                    "run-20261031T085111Z-foreign-review-staging-full.txt"
                ),
                "verified": True,
            }
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertIn(
            "expired gate-report destination(s) missing under the target",
            out,
        )
        self.assertIn("report-only", out)
        self.assertNotIn("migrated artifact(s) missing under the target", out)
        self.assertNotIn("held: the branch disposition above names a failed guard", out)
        self.assertIn("removal: git worktree remove", out)

    def test_unreadable_ref_at_capture_retains_branch_and_worktree(self):
        # The proven OID cannot be captured (the ref does not resolve): the
        # accounting is unknown, the gate refuses, and the branch and the
        # on-disk worktree both stay for operator resolution.
        self._seed_migration_manifest(landed=True)
        real_run = subprocess.run

        def kill_capture(argv, *a, **k):
            if "rev-parse" in argv and "--verify" in argv:
                return subprocess.CompletedProcess(argv, 1, stdout="", stderr="fatal: gone")
            return real_run(argv, *a, **k)

        args = MODULE.build_gate_removal_parser().parse_args(
            [
                "--plan", str(self.worktree / "docs/history/plans/2026-10-08-x.md"),
                "--target", str(self.primary),
                "--worktree", str(self.worktree),
            ]
        )
        with mock.patch.object(MODULE.subprocess, "run", side_effect=kill_capture):
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                code = MODULE.cmd_gate_removal(args)
        out = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch ref unreadable: wt-run does not resolve", out)
        self.assertIn("branch-disposition: branch=wt-run disposition=unknown-ref", out)
        self.assertNotIn("git worktree remove", out)
        self.assertTrue(Path(self.worktree).is_dir(), "the on-disk worktree was removed")

    def test_moved_ref_during_checks_refuses_and_retains(self):
        # Plan gate-removal-closeout-accounting Task 2: the branch moves
        # after the proven-OID capture; the re-compare reports changed,
        # refuses the removal, and retains the branch and the on-disk
        # worktree for operator resolution.
        self._seed_migration_manifest(landed=True)
        proven = self._branch_oid("wt-run")

        def move_ref(run):
            # update-ref is the plumbing: unlike branch -f it can move a
            # ref a linked worktree still holds, which is exactly the
            # out-of-band move this arm guards.
            run(["git", "-C", str(self.primary), "commit", "-q", "--allow-empty", "-m", "move"])
            head = run(
                ["git", "-C", str(self.primary), "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            run(["git", "-C", str(self.primary), "update-ref", "refs/heads/wt-run", head])

        code, out, _err = self._run_gate_with_midcheck_mutation(move_ref)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch ref changed during the closeout checks", out)
        self.assertIn(f"proven OID {proven}", out)
        self.assertIn("branch-disposition: branch=wt-run disposition=ref-changed", out)
        self.assertNotIn("git worktree remove", out)
        self.assertTrue(Path(self.worktree).is_dir(), "the on-disk worktree was removed")
        self.assertNotEqual(self._branch_oid("wt-run"), proven)

    def test_ref_deleted_at_recheck_reports_unknown_and_retains(self):
        # The ref turns unreadable between the capture and the recheck: the
        # closeout reports the unknown ref, refuses, and retains.
        self._seed_migration_manifest(landed=True)

        def delete_ref(run):
            run(["git", "-C", str(self.primary), "update-ref", "-d", "refs/heads/wt-run"])

        code, out, _err = self._run_gate_with_midcheck_mutation(delete_ref)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch ref unreadable at the closeout recheck", out)
        self.assertIn("branch-disposition: branch=wt-run disposition=unknown-ref", out)
        self.assertTrue(Path(self.worktree).is_dir(), "the on-disk worktree was removed")


class GateRemovalAttributionScopeTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] Run-attribution scoping of the
    missing-destination hold (plan
    2026-11-01-gate-removal-inherited-manifest-rows): the shared manifest is
    append-only per canonical session slug, so the hold covers only rows
    stamped for the adjudicated branch record (the manifest's last) plus all
    rows of a single-record legacy manifest (the done-session gate-report
    exception stays report-only inside this population), while a prior run's stamped rows
    and unattributable rows in multi-record manifests demote to a report-only
    foreign note naming the missing destinations and the
    attributed/unattributed counts."""

    RECORD_REL = ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md"
    DRAINED_REL = "docs/tmp/done-session/run-1-worktree-staging.txt"
    RUN2_MISSING_REL = "docs/tmp/run-2/vanished.md"
    COMPLETED_PLAN_REL = "docs/history/plans/completed/2026-10-08-x.md"

    @staticmethod
    def _row(destination: str, index: int | None) -> dict:
        """One migrated row: verified with the given destination and an
        explicit stamp (None models a legacy row written before the stamp
        existed)."""
        row = {"source": destination, "destination": destination, "verified": True}
        if index is not None:
            row["record_index"] = index
        return row

    def _two_records(self) -> list[dict]:
        """Two branch records for the same worktree/branch: the re-run shape
        the shared canonical session slug produces."""
        return [
            {"branch": "wt-run", "source": str(self.worktree)},
            {"branch": "wt-run", "source": str(self.worktree)},
        ]

    def _author_manifest(
        self, migrated: list[dict], branch: list[dict]
    ) -> Path:
        """Rewrite the seeded fixture manifest's migrated rows and branch
        records, keeping the git/citation/accounting setup untouched."""
        manifest_path = self._seed_migration_manifest(landed=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["migrated"] = migrated
        manifest["branch"] = branch
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def _run_migrate(self, baseline: Path, manifest_path: Path) -> None:
        code, out, err = _run_cli(
            "migrate",
            "--baseline", str(baseline),
            "--source", str(self.worktree),
            "--target", str(self.primary),
            "--manifest", str(manifest_path),
            cwd=self.root,
        )
        self.assertEqual(code, 0, out + err)

    def test_two_run_drained_destination_reports_only_and_passes(self):
        # Pass path: two real migrate runs into one shared-slug session
        # manifest. Run 1 migrates the cited review record and a done-session
        # artifact (a non-gate-report shape); the sanctioned docs/tmp
        # lifecycle drains the artifact under the target; run 2 re-runs the
        # plan into the same manifest. The drained destination is stamped for
        # branch record 0 while the gate adjudicates record 1: report-only
        # note naming the drained destination, never a hold, the removal
        # authorization still printed.
        _write(
            self.worktree / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\n"
            b"metrics_dir = \".ai-playbook/metrics/\"\n"
            b"review_certs_dir = \".ai-playbook/review-certs/\"\n```\n",
        )
        baseline1 = self.root / "baseline-1.json"
        _capture_baseline(self.worktree, baseline1)
        _write(self.worktree / self.RECORD_REL, b"r1\n")
        _write(
            self.worktree / "docs/history/plans/2026-10-08-x.md",
            b"# Plan\n\nPlan review record: " + self.RECORD_REL.encode("utf-8") + b"\n",
        )
        _write(self.worktree / self.DRAINED_REL, b"run-1 staging\n")
        manifest_path = (
            self.primary / "docs/tmp/execute-plan/x/closeout-migration.json"
        )
        self._run_migrate(baseline1, manifest_path)
        # The sanctioned docs/tmp sweep lifecycle drains the run-1 artifact
        # under the target between the runs.
        (self.primary / self.DRAINED_REL).unlink()
        baseline2 = self.root / "baseline-2.json"
        _capture_baseline(self.worktree, baseline2)
        self._run_migrate(baseline2, manifest_path)
        # Two runs extended ONE manifest; each run's rows carry that run's
        # branch-record index (run 2's zero delta appends only its record).
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [row.get("record_index") for row in manifest["migrated"]], [0, 0]
        )
        self.assertEqual(
            [record.get("record_index") for record in manifest["branch"]], [0, 1]
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn(
            "unattributed migration destination(s) missing under the target", out
        )
        self.assertIn(self.DRAINED_REL, out)
        self.assertIn(
            "missing attributed to the adjudicated record: 0; unattributed: 1",
            out,
        )
        self.assertNotIn("migrated artifact(s) missing under the target", out)
        self.assertNotIn(
            "held: the branch disposition above names a failed guard", out
        )
        self.assertTrue(Path(self.worktree).is_dir())

    def test_adjudicated_stamped_missing_destination_holds(self):
        # Hold path (a): the adjudicated run's own stamped destination
        # missing in a multi-record manifest keeps today's fail-closed hold -
        # exact text, retained disposition, held removal - and no note prints
        # because nothing unattributed is missing.
        self._author_manifest(
            [
                self._row(self.RECORD_REL, 0),
                self._row(self.RUN2_MISSING_REL, 1),
            ],
            self._two_records(),
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch-closeout: preserve branch wt-run at ", out)
        self.assertIn(
            "migrated artifact(s) missing under the target: "
            + self.RUN2_MISSING_REL,
            out,
        )
        self.assertIn(
            "held: the branch disposition above names a failed guard", out
        )
        self.assertNotIn("removal: git worktree remove", out)
        self.assertNotIn("unattributed migration destination(s)", out)
        self.assertTrue(
            Path(self.worktree).is_dir(), "the guarded worktree was removed"
        )

    def test_single_record_legacy_manifest_holds_all_rows(self):
        # Hold path (b): a single-record legacy manifest (unstamped rows)
        # keeps today's hold for ALL its rows - an unstamped missing
        # destination refuses exactly as before the stamp existed.
        manifest_path = self._seed_migration_manifest(landed=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["migrated"].append(self._row("docs/tmp/legacy/vanished.md", None))
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "migrated artifact(s) missing under the target: "
            "docs/tmp/legacy/vanished.md",
            out,
        )
        self.assertIn(
            "held: the branch disposition above names a failed guard", out
        )
        self.assertNotIn("removal: git worktree remove", out)

    def test_multi_record_all_unstamped_manifest_reports_only(self):
        # Transition (a), the disclosed posture change: a multi-record
        # legacy manifest (every row unstamped) reports its unattributable
        # missing rows as a report-only note and passes, where the same
        # missing row in a single-record manifest still refuses.
        manifest_path = self._seed_migration_manifest(landed=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["migrated"].append(self._row(self.DRAINED_REL, None))
        manifest["branch"].append(
            {"branch": "wt-run", "source": str(self.worktree)}
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn(
            "unattributed migration destination(s) missing under the target",
            out,
        )
        self.assertIn(self.DRAINED_REL, out)
        self.assertIn(
            "missing attributed to the adjudicated record: 0; unattributed: 1",
            out,
        )
        self.assertNotIn("migrated artifact(s) missing under the target", out)
        self.assertNotIn(
            "held: the branch disposition above names a failed guard", out
        )

    def test_mixed_legacy_and_stamped_manifest_passes_with_note(self):
        # Transition (b): unstamped record-0 rows (one drained, non-gate-
        # report) beside stamped record-1 rows (all present) - the note names
        # the drained legacy destination and the gate passes.
        self._author_manifest(
            [
                self._row(self.RECORD_REL, None),
                self._row(self.DRAINED_REL, None),
                self._row(self.COMPLETED_PLAN_REL, 1),
            ],
            self._two_records(),
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn(
            "unattributed migration destination(s) missing under the target",
            out,
        )
        self.assertIn(self.DRAINED_REL, out)
        self.assertIn(
            "missing attributed to the adjudicated record: 0; unattributed: 1",
            out,
        )
        self.assertNotIn("migrated artifact(s) missing under the target", out)
        self.assertNotIn(
            "held: the branch disposition above names a failed guard", out
        )

    def test_mixed_manifest_with_missing_adjudicated_destination_refuses_with_note(self):
        # Transition (c): the same mixed shape with a stamped adjudicated
        # destination missing - the hold fires with today's text AND the
        # unattributed (legacy) note still prints beside it, with both
        # counts.
        self._author_manifest(
            [
                self._row(self.RECORD_REL, None),
                self._row(self.DRAINED_REL, None),
                self._row(self.COMPLETED_PLAN_REL, 1),
                self._row(self.RUN2_MISSING_REL, 1),
            ],
            self._two_records(),
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "migrated artifact(s) missing under the target: "
            + self.RUN2_MISSING_REL,
            out,
        )
        self.assertIn(
            "held: the branch disposition above names a failed guard", out
        )
        self.assertNotIn("removal: git worktree remove", out)
        self.assertIn(
            "unattributed migration destination(s) missing under the target",
            out,
        )
        self.assertIn(self.DRAINED_REL, out)
        self.assertIn(
            "missing attributed to the adjudicated record: 1; unattributed: 1",
            out,
        )


class GateRemovalPreventedClobbersTeardownTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] The teardown summary line at gate-removal
    (plan 2026-11-02-closeout-migrate-clobber-guard-restore-arms Task 4):
    the adjudicated run's non-empty prevented_clobbers manifest rows surface
    as a report-only summary naming the restored paths and the
    operator-decide note, never a hold (warning-first per the machinery
    admission protocol); prevented rows stamped for prior runs' branch
    records report as foreign, never attributed to the adjudicated run's
    teardown evidence (the unattributable-rows report-only demotion
    shape). Stamp-less rows (a legacy row written before the stamp
    existed) fall to the single-record rule - attributed in a
    single-record manifest, foreign beside any second branch record -
    pinned in both directions (plan
    2026-11-04-closeout-clobber-guard-review-residual-trio Task 3)."""

    PREVENTED_REL = "docs/tmp/execute-plan/x/rewound-record.md"

    def _prevented_row(self, index: int | None, rel: str | None = None) -> dict:
        """One prevented_clobbers row in the producer's shape: the absolute
        destination the guard records ((target / rel).as_posix()) and the
        run-attribution stamp (None models a legacy row written before the
        stamp existed). ``rel`` overrides the default destination path so a
        fixture can author more prevented rows than the notes' slice."""
        row = {
            "destination": (self.primary / (rel or self.PREVENTED_REL)).as_posix(),
            "action": "restored-from-HEAD",
        }
        if index is not None:
            row["record_index"] = index
        return row

    def _two_records(self) -> list[dict]:
        """Two branch records for the same worktree/branch: the re-run shape
        the shared canonical session slug produces (record 0 is the prior
        run, record 1 the adjudicated run)."""
        return [
            {"branch": "wt-run", "source": str(self.worktree)},
            {"branch": "wt-run", "source": str(self.worktree)},
        ]

    def _author_manifest(
        self,
        prevented: list[dict],
        two_records: bool = True,
        failures: list[dict] | None = None,
    ) -> Path:
        """Rewrite the seeded fixture manifest's prevented_clobbers rows and,
        by default, extend it to two branch records (the re-run shape);
        ``two_records=False`` keeps the seeded single-record legacy manifest.
        ``failures`` seeds the prevented_clobber_failures section (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1).
        The git/citation/accounting setup stays untouched."""
        manifest_path = self._seed_migration_manifest(landed=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["prevented_clobbers"] = prevented
        if failures is not None:
            manifest["prevented_clobber_failures"] = failures
        if two_records:
            manifest["branch"] = self._two_records()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def test_adjudicated_run_prevented_rows_surface_report_only(self):
        # The adjudicated run's own stamped prevented row (record index 1,
        # the manifest's last branch record) surfaces at the teardown
        # decision: a report-only summary naming the restored path and the
        # operator-decide note, the removal authorization still printed, no
        # hold, and no foreign note (nothing unattributed).
        self._author_manifest([self._prevented_row(1)])
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn("branch-closeout: prevented clobber(s) this run restored from HEAD", out)
        self.assertIn((self.primary / self.PREVENTED_REL).as_posix(), out)
        self.assertIn("the operator decides", out)
        self.assertNotIn("held:", out)
        self.assertNotIn("never this run's teardown evidence", out)
        self.assertTrue(Path(self.worktree).is_dir())

    def test_prior_run_prevented_rows_report_foreign(self):
        # A prevented row stamped for the prior run (record index 0) reports
        # as foreign: the foreign note names it, the adjudicated-run summary
        # line never prints, and the row is never attributed to this run's
        # teardown evidence.
        self._author_manifest([self._prevented_row(0)])
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn(
            "branch-closeout: prevented clobber(s) attributed to prior "
            "run(s) in the shared manifest",
            out,
        )
        self.assertIn((self.primary / self.PREVENTED_REL).as_posix(), out)
        self.assertIn("never this run's teardown evidence", out)
        self.assertNotIn("prevented clobber(s) this run restored from HEAD", out)
        self.assertNotIn("held:", out)
        self.assertTrue(Path(self.worktree).is_dir())

    def test_single_record_manifest_unstamped_prevented_row_attributed(self):
        # A stamp-less prevented row (record_index absent, the legacy row
        # written before the stamp existed) in a single-record manifest
        # falls to the single-record rule len(records) == 1: attributed to
        # this run's teardown evidence, so the summary line prints and no
        # foreign note does.
        self._author_manifest([self._prevented_row(None)], two_records=False)
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn("branch-closeout: prevented clobber(s) this run restored from HEAD", out)
        self.assertIn((self.primary / self.PREVENTED_REL).as_posix(), out)
        self.assertIn("the operator decides", out)
        self.assertNotIn("never this run's teardown evidence", out)
        self.assertNotIn("held:", out)
        self.assertTrue(Path(self.worktree).is_dir())

    def test_two_record_manifest_unstamped_prevented_row_foreign(self):
        # The same stamp-less prevented row beside a second branch record
        # (len(records) == 2) fails the single-record rule: it demotes to
        # the report-only foreign note and is never attributed to this
        # run's teardown evidence.
        self._author_manifest([self._prevented_row(None)])
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn(
            "branch-closeout: prevented clobber(s) attributed to prior "
            "run(s) in the shared manifest",
            out,
        )
        self.assertIn((self.primary / self.PREVENTED_REL).as_posix(), out)
        self.assertIn("never this run's teardown evidence", out)
        self.assertNotIn("prevented clobber(s) this run restored from HEAD", out)
        self.assertNotIn("held:", out)
        self.assertTrue(Path(self.worktree).is_dir())

    def test_prevented_notes_print_first_five_paths_plus_total(self):
        """[class: REPOSITORY_TEST] The prevented notes' remainder counts
        (plan 2026-11-04-closeout-clobber-guard-review-residual-trio R2):
        more than five prevented paths in either prevented clobber(s) note
        print the first five paths plus a parenthesized total, following
        the sibling unattributed_missing note's slice-then-parenthesized-
        count convention in this note's own (total: N) form; the pre-fix
        note sliced at five paths with no count, so paths six and beyond
        vanished from the operator's teardown evidence."""
        rels = [f"docs/tmp/execute-plan/x/rewound-{n}.md" for n in range(7)]
        restored = [self._prevented_row(1, rel=rel) for rel in rels]
        foreign = [self._prevented_row(0, rel=rel) for rel in rels]
        self._author_manifest(restored + foreign)
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        for note_prefix in (
            "branch-closeout: prevented clobber(s) this run restored from HEAD",
            "branch-closeout: prevented clobber(s) attributed to prior "
            "run(s) in the shared manifest",
        ):
            with self.subTest(note=note_prefix[:60]):
                note_line = next(
                    line for line in out.splitlines()
                    if line.startswith(note_prefix)
                )
                for rel in rels[:5]:
                    self.assertIn((self.primary / rel).as_posix(), note_line)
                for rel in rels[5:]:
                    self.assertNotIn(
                        (self.primary / rel).as_posix(), note_line,
                        "paths beyond the first five must not print "
                        "verbatim; the count carries them",
                    )
                self.assertIn(
                    "(total: 7)", note_line,
                    "the note must carry the total count, following the "
                    "sibling unattributed_missing note's slice-then-count "
                    "convention in this note's own (total: N) form",
                )

    def _failure_row(self, index: int | None, rel: str) -> dict:
        """One prevented_clobber_failures row in the producer's shape (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1):
        the absolute destination, a named action, an error, and the
        run-attribution stamp (None models a legacy unstamped row)."""
        row = {
            "destination": (self.primary / rel).as_posix(),
            "action": "guard-failed",
            "error": "OSError: simulated guard spawn failure",
        }
        if index is not None:
            row["record_index"] = index
        return row

    def test_guard_failure_rows_surface_beside_prevented_rows_report_only(self):
        """[class: REPOSITORY_TEST] The teardown summary's additive
        prevented_clobber_failures read (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1):
        guard-failure rows reach the teardown decision beside the prevented
        rows in the same report-only summary - the adjudicated run's rows
        name the failure destinations, rows stamped for prior runs report as
        foreign, and neither ever holds the branch."""
        self._author_manifest(
            [self._prevented_row(1)],
            failures=[
                self._failure_row(
                    1, rel="docs/tmp/execute-plan/x/guard-crash-own.md"),
                self._failure_row(
                    0, rel="docs/tmp/execute-plan/x/guard-crash-prior.md"),
            ],
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("removal: git worktree remove", out)
        self.assertIn("branch-closeout: prevented clobber(s) this run restored from HEAD", out)
        self.assertIn("clobber-guard failure(s) this run recorded", out)
        self.assertIn(
            (self.primary / "docs/tmp/execute-plan/x/guard-crash-own.md").as_posix(),
            out,
        )
        self.assertIn("clobber-guard failure(s) attributed to prior run(s)", out)
        self.assertIn(
            (self.primary / "docs/tmp/execute-plan/x/guard-crash-prior.md").as_posix(),
            out,
        )
        self.assertNotIn("held:", out)
        self.assertTrue(Path(self.worktree).is_dir())


class ManifestRecordIndexStampTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] The run-attribution stamp at the manifest
    persistence choke point (plan
    2026-11-01-gate-removal-inherited-manifest-rows): an append carrying a
    `branch` list stamps every appended row of every list section with the
    incoming branch record's index (the current branch-list length); an
    append without a `branch` section stays unstamped; the `interrupted`
    bool marker is not a row and stays verbatim while `incomplete` rows
    carry the stamp."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-stamp-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_branch_carrying_append_stamps_rows_at_incoming_index(self):
        path = self.root / "closeout-migration.json"
        MODULE._append_manifest(
            path,
            {
                "migrated": [{"destination": "a", "verified": True}],
                "renamed": [],
                "skipped": [{"reason": "x"}],
                "failed": [],
                "branch": [{"branch": "wt", "source": "/s1"}],
                "interrupted": True,
                "incomplete": [{"error": "boom"}],
            },
        )
        manifest = json.loads(path.read_text(encoding="utf-8"))
        # The interrupted marker is a bool, not a list section: it stays
        # verbatim, while every list-section row (incomplete included) is
        # stamped with the incoming record's index 0.
        self.assertIs(manifest["interrupted"], True)
        for section in ("migrated", "skipped", "failed", "branch", "incomplete"):
            for row in manifest[section]:
                self.assertEqual(row.get("record_index"), 0, section)
        # A second extend stamps at the new index and never rewrites the
        # prior rows (the manifest stays append-only).
        MODULE._append_manifest(
            path,
            {
                "migrated": [{"destination": "b", "verified": True}],
                "branch": [{"branch": "wt", "source": "/s2"}],
            },
        )
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            [row["record_index"] for row in manifest["migrated"]], [0, 1]
        )
        self.assertEqual(
            [row["record_index"] for row in manifest["branch"]], [0, 1]
        )
        self.assertEqual(
            [row["record_index"] for row in manifest["skipped"]], [0]
        )
        self.assertEqual(
            [row["destination"] for row in manifest["migrated"]], ["a", "b"]
        )

    def test_append_without_branch_section_stays_unstamped(self):
        # The no-branch callers (the in-place no-op shape) append unstamped,
        # exactly as before the stamp existed.
        path = self.root / "closeout-migration.json"
        MODULE._append_manifest(path, {"noop": [{"note": "in-place"}]})
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("record_index", manifest["noop"][0])
        self.assertNotIn("branch", manifest)

    def test_migrate_runs_stamp_rows_with_incoming_record_index(self):
        # End to end: consecutive migrate runs into one manifest stamp each
        # run's rows with that run's incoming branch-record index.
        source = self.root / "src"
        target = self.root / "tgt"
        manifest = self.root / "closeout-migration.json"
        baseline1 = self.root / "baseline-1.json"
        _write(
            baseline1,
            json.dumps(
                {
                    "captured_at": "2026-11-01T00:00:00+00:00",
                    "dirs": ["docs/tmp"],
                    "files": {},
                }
            ).encode("utf-8"),
        )
        _write(source / "docs/tmp/a.md", b"a\n")
        self.assertEqual(_migrate(source, target, baseline1, manifest), 0)
        baseline2 = self.root / "baseline-2.json"
        _write(
            baseline2,
            json.dumps(
                {
                    "captured_at": "2026-11-01T00:00:00+00:00",
                    "dirs": ["docs/tmp"],
                    "files": {"docs/tmp/a.md": _digest(b"a\n")},
                }
            ).encode("utf-8"),
        )
        _write(source / "docs/tmp/b.md", b"b\n")
        self.assertEqual(_migrate(source, target, baseline2, manifest), 0)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            [Path(row["destination"]).name for row in data["migrated"]],
            ["a.md", "b.md"],
        )
        self.assertEqual(
            [row["record_index"] for row in data["migrated"]], [0, 1]
        )
        self.assertEqual(
            [record["record_index"] for record in data["branch"]], [0, 1]
        )


class GateOperatorCloseoutTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] Operator-closeout witnesses (plan
    gate-removal-closeout-accounting Task 2): a sibling worktree attaching
    after gate success but before quiescence retains the ref, and any
    inventoried ignored or untracked file lacking a verified destination
    retains the worktree and the ref."""

    def test_sibling_attach_after_gate_success_retains_ref(self):
        # The gate authorizes the operator closeout (ancestry-accounted,
        # expected OID named); a sibling worktree then attaches before the
        # quiesce point. The pre-delete confirmation re-runs the gate in
        # branch-only mode, the linked-worktree guard fires, and the ref is
        # retained.
        self._seed_migration_manifest(landed=True)
        self._git(self.primary, "merge", "-q", "--no-edit", "wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        expected_oid = self._branch_oid("wt-run")
        self.assertIn(f"expected OID {expected_oid}", out)
        # The sibling attaches after the gate success, before quiescence.
        sibling = self.root / "proj-wt-sibling"
        self._git(self.primary, "worktree", "add", "-q", "-b", "wt-temp-sib", str(sibling))
        self._git(sibling, "checkout", "-q", "--ignore-other-worktrees", "wt-run")
        code, out, _err = self._run_gate_branch_only("wt-run")
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch shared with 2 live worktree(s)", out)
        self.assertIn(str(sibling), out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", "wt-run", check=False).returncode,
            0,
            "the ref was deleted while a sibling worktree held it",
        )
        self.assertEqual(self._branch_oid("wt-run"), expected_oid, "the ref moved")

    def test_unverified_ignored_file_retains_worktree_and_ref(self):
        # An ignored staging record in the worktree with no verified
        # destination under the primary home: the records gate fails, and
        # the operator closeout retains the worktree and the ref.
        self._seed_migration_manifest(landed=True)
        record = ".ai-playbook/reviews/2026-10-08-ignored-unverified-r1.md"
        _write(self.worktree / ".gitignore", f"{record}\n".encode("utf-8"))
        self._commit_all(self.worktree, "chore: ignore the staged record")
        _write(self.worktree / record, b"staged bytes never migrated\n")
        plan = self.worktree / "docs/history/plans/2026-10-08-x.md"
        _write(plan, f"# Plan\n\nPlan review record: {record}\n".encode("utf-8"))
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {record}", out)
        self.assertNotIn("git worktree remove", out)
        self.assertTrue(Path(self.worktree).is_dir(), "the worktree was removed")
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", "wt-run", check=False).returncode,
            0,
            "the ref was deleted over an unverified ignored artifact",
        )

    def test_unverified_untracked_file_retains_worktree_and_ref(self):
        # An untracked file the run owns whose bytes exist nowhere at the
        # destination: the records gate fails on its citation and the
        # worktree and ref are retained.
        self._seed_migration_manifest(landed=True)
        record = ".ai-playbook/reviews/2026-10-08-untracked-unverified-r1.md"
        _write(self.worktree / record, b"untracked bytes never migrated\n")
        plan = self.worktree / "docs/history/plans/2026-10-08-x.md"
        _write(plan, f"# Plan\n\nPlan review record: {record}\n".encode("utf-8"))
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {record}", out)
        self.assertNotIn("git worktree remove", out)
        self.assertTrue(Path(self.worktree).is_dir(), "the worktree was removed")
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", "wt-run", check=False).returncode,
            0,
            "the ref was deleted over an unverified untracked artifact",
        )


class BranchOnlyGateTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] Branch-only gate mode witnesses (plan
    gate-removal-closeout-accounting Task 2): explicit --branch plus
    --migration-manifest and no --worktree adjudicates a ref with no linked
    worktree under the full guard chain; an accounted branch reports its
    proof and expected OID; missing proof or any failed guard retains the
    ref."""

    def _manifest_for(self, branch: str, destination: str | None = None) -> Path:
        manifest_dir = self.primary / "docs/tmp/execute-plan/branch-only"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        path = manifest_dir / "closeout-migration.json"
        migrated = [
            {
                "source": ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                "destination": destination
                or ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                "verified": True,
            }
        ]
        path.write_text(
            json.dumps(
                {
                    "migrated": migrated,
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [{"branch": branch, "source": "branch-only"}],
                }
            ),
            encoding="utf-8",
        )
        return path

    def _seed_records(self) -> None:
        reviews = self.primary / ".ai-playbook/reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        _write(
            reviews / "2026-10-08-plan-review-x-exec-r1.md",
            b"r1\n",
        )
        plan_rel = "docs/history/plans/2026-10-08-x.md"
        _write(
            self.primary / plan_rel,
            b"# Plan\n\nPlan review record: .ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md\n",
        )
        self._commit_all(self.primary, "plan: seed the plan and its record")
        self.branch_only_plan = self.primary / plan_rel

    def setUp(self) -> None:
        super().setUp()
        self._seed_records()

    def test_accounted_branch_reports_proof_and_expected_oid(self):
        branch = "wt-done"
        self._git(self.primary, "branch", branch, "HEAD")
        expected = self._branch_oid(branch)
        manifest = self._manifest_for(branch)
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch {branch} ancestry-accounted at {expected}", out)
        self.assertIn(f"expected OID {expected}", out)
        self.assertIn(
            f"branch-disposition: branch={branch} disposition=ancestry-accounted oid={expected}",
            out,
        )
        self.assertNotIn("git worktree remove", out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode,
            0,
        )

    def test_accounted_branch_only_report_states_only_branch_evidence(self):
        # Plan 2026-10-29-gate-removal-task2-review-residues Task 1: in
        # branch-only mode (no linked worktree) the ancestry-accounted
        # report names the branch, the proven OID, and the ancestry result
        # only - it claims neither a live worktree nor migrated artifacts.
        # The removal instruction and the structured disposition stay
        # intact.
        branch = "wt-done"
        self._git(self.primary, "branch", branch, "HEAD")
        expected = self._branch_oid(branch)
        manifest = self._manifest_for(branch)
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch {branch} ancestry-accounted at {expected}", out)
        self.assertNotIn("worktree binds", out)
        self.assertNotIn("migrated artifacts verified", out)
        self.assertIn(
            f"branch: operator closeout may delete branch {branch} at "
            f"expected OID {expected}",
            out,
        )
        self.assertIn(
            f"branch-disposition: branch={branch} disposition=ancestry-accounted oid={expected}",
            out,
        )

    def test_exact_tree_only_branch_reported_and_retained(self):
        tree = self._git(self.primary, "rev-parse", "HEAD^{tree}").stdout.strip()
        root = self._git(self.primary, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
        snap = self._git(
            self.primary, "commit-tree", tree, "-p", root, "-m", "snapshot vintage"
        ).stdout.strip()
        branch = "wt-snap"
        self._git(self.primary, "branch", branch, snap)
        manifest = self._manifest_for(branch)
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch {branch} exact-tree-accounted at {snap}", out)
        self.assertIn("the non-ancestor branch is retained", out)
        self.assertIn(
            f"branch-disposition: branch={branch} disposition=exact-tree-accounted oid={snap}",
            out,
        )
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode,
            0,
            "the exact-tree-only branch was deleted",
        )

    def test_missing_proof_retains_ref(self):
        branch = "wt-unaccounted"
        self._git(self.primary, "branch", branch, "HEAD")
        # Commit the unlanded work ON the branch through a scratch worktree
        # that is removed again, so the branch tip carries a commit no
        # destination history contains while no worktree stays linked.
        scratch = self.root / "proj-wt-scratch"
        self._git(self.primary, "worktree", "add", "-q", str(scratch), branch)
        _write(scratch / "unlanded.txt", b"never landed\n")
        self._commit_all(scratch, "work: unlanded everywhere")
        self._git(self.primary, "worktree", "remove", "--force", str(scratch))
        manifest = self._manifest_for(branch)
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"branch-closeout: preserve branch {branch} at ", out)
        self.assertIn(
            f"branch-disposition: branch={branch} disposition=retained oid=",
            out,
        )
        self.assertIn("branch: preserve", out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode,
            0,
            "the ref was deleted without proof",
        )

    def test_linked_worktree_guard_retains_ref(self):
        branch = "wt-linked"
        self._git(self.primary, "branch", branch, "HEAD")
        linked = self.root / "proj-wt-linked"
        self._git(self.primary, "worktree", "add", "-q", str(linked), branch)
        manifest = self._manifest_for(branch)
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("branch shared with 1 live worktree(s)", out)
        self.assertIn(str(linked), out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode,
            0,
            "the ref was deleted while a worktree held it",
        )

    def test_missing_artifact_guard_retains_ref(self):
        branch = "wt-artifact"
        self._git(self.primary, "branch", branch, "HEAD")
        manifest = self._manifest_for(branch, destination=".ai-playbook/reviews/vanished.md")
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("migrated artifact(s) missing under the target", out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode,
            0,
        )

    def test_identity_binding_refuses_foreign_branch(self):
        self._git(self.primary, "branch", "wt-bound", "HEAD")
        manifest = self._manifest_for("wt-bound")
        code, out, _err = self._run_gate_branch_only("wt-somewhere-else", manifest)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("exact-branch identity mismatch", out)
        self.assertIn("wt-bound", out)
        self.assertIn("wt-somewhere-else", out)

    def test_missing_manifest_file_fails_branch_only_mode(self):
        # A skip shape with no disposition (the explicit
        # --migration-manifest path names an absent file; plan
        # gate-removal-closeout-accounting Task 2: missing proof retains
        # the ref): branch-only mode fails, it never passes without
        # branch accounting.
        branch = "wt-no-manifest"
        self._git(self.primary, "branch", branch, "HEAD")
        absent = self.primary / "docs/tmp/execute-plan/branch-only/absent-closeout.json"
        code, out, _err = self._run_gate_branch_only(branch, absent)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "branch-closeout: skipped (no migration manifest at the "
            f"explicit --migration-manifest path {absent}",
            out,
        )
        self.assertIn(
            "refused: branch-only closeout produced no branch disposition", out
        )
        self.assertNotIn("branch-disposition:", out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode,
            0,
            "the ref was deleted over a skip shape with no disposition",
        )

    def test_manifest_without_branch_record_fails_branch_only_mode(self):
        # A skip shape with no disposition (the manifest carries no branch
        # record; plan gate-removal-closeout-accounting Task 2: missing
        # proof retains the ref): branch-only mode fails, it never passes
        # without branch accounting.
        branch = "wt-no-record"
        self._git(self.primary, "branch", branch, "HEAD")
        manifest_dir = self.primary / "docs/tmp/execute-plan/branch-only"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = manifest_dir / "no-branch-record-closeout.json"
        manifest.write_text(
            json.dumps({"migrated": [], "renamed": [], "skipped": [], "failed": []}),
            encoding="utf-8",
        )
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(
            "branch-closeout: skipped (migration manifest carries no branch "
            "record; legacy shape)",
            out,
        )
        self.assertIn(
            "refused: branch-only closeout produced no branch disposition", out
        )
        self.assertNotIn("branch-disposition:", out)
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", branch, check=False).returncode,
            0,
            "the ref was deleted over a skip shape with no disposition",
        )

    def test_usage_violations_are_tool_errors(self):
        manifest = self._manifest_for("wt-any")
        # --branch without --migration-manifest.
        code, out, err = _run_cli(
            "gate-removal", "--plan", "plan.md", "--target", str(self.primary),
            "--branch", "wt-any", cwd=self.primary,
        )
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("--migration-manifest", err)
        # --branch together with --worktree.
        code, out, err = _run_cli(
            "gate-removal", "--plan", "plan.md", "--target", str(self.primary),
            "--branch", "wt-any", "--worktree", "somewhere", cwd=self.primary,
        )
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("mutually exclusive", err)
        # Neither --branch nor --worktree.
        code, out, err = _run_cli(
            "gate-removal", "--plan", "plan.md", "--target", str(self.primary),
            cwd=self.primary,
        )
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("--worktree", err)
        self.assertIsNotNone(manifest)

    def test_zero_plan_skeleton_shape_adjudicates_exact_tree(self):
        # The zero-plan producer's emitted skeleton shape (lesson 289's
        # hand-build remedy): only the branch record and an empty migrated
        # list, no migrated/renamed/skipped/failed twin keys - the shape
        # done_run.sh writes beside the run-ID skip record - and the
        # branch-only pass adjudicates it to exact-tree-accounted.
        tree = self._git(self.primary, "rev-parse", "HEAD^{tree}").stdout.strip()
        root = self._git(self.primary, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
        snap = self._git(
            self.primary, "commit-tree", tree, "-p", root, "-m", "zero-plan snapshot vintage"
        ).stdout.strip()
        branch = "wt-zero-skeleton"
        self._git(self.primary, "branch", branch, snap)
        manifest_dir = self.primary / "docs/tmp/done-session"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = manifest_dir / "worktree-migrate-baseline-run-z1-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "branch": [
                        {"branch": branch, "source": str(self.root / "proj-wt-zero")}
                    ],
                    "migrated": [],
                }
            ),
            encoding="utf-8",
        )
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch {branch} exact-tree-accounted at {snap}", out)

    def test_zero_plan_skeleton_with_scoped_copy_entry_adjudicates(self):
        # The scoped-copy arm's append (the Worktree-first standard's
        # baseline-less closeout arm): each verified transfer adds its
        # migrated entry to the skeleton's migrated list, and the appended
        # shape still adjudicates - the entry's destination verifies under
        # the target.
        tree = self._git(self.primary, "rev-parse", "HEAD^{tree}").stdout.strip()
        root = self._git(self.primary, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
        snap = self._git(
            self.primary, "commit-tree", tree, "-p", root, "-m", "zero-plan snapshot vintage"
        ).stdout.strip()
        branch = "wt-zero-scoped"
        self._git(self.primary, "branch", branch, snap)
        record_rel = ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md"
        digest = hashlib.sha256((self.primary / record_rel).read_bytes()).hexdigest()
        manifest_dir = self.primary / "docs/tmp/done-session"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = manifest_dir / "worktree-migrate-baseline-run-z2-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "branch": [
                        {"branch": branch, "source": str(self.root / "proj-wt-zero")}
                    ],
                    "migrated": [
                        {
                            "destination": record_rel,
                            "verified": True,
                            "sha256": digest,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch {branch} exact-tree-accounted at {snap}", out)


class CloseoutReferenceStateTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] Closeout reference-state resolver witnesses
    (plan 2026-10-29-done-gate-report-retention Task 1): the resolver
    extracted from the gate's inline adjudication reports the LATEST branch
    record and every verified migrated/renamed destination, and resolves
    absent, unreadable, and malformed manifest shapes to unresolved/no
    destinations without normalizing them (the gate keeps its shape-specific
    skip, refusal, and tool-error outcomes; the consumer parity is pinned by
    CloseoutReferenceConsumerParityTest)."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-refstate-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _manifest(self, body: bytes) -> Path:
        path = self.root / "closeout-migration.json"
        _write(path, body)
        return path

    def _checkout_shape(self, name: str) -> Path:
        # A facts-resolved checkout-shaped directory (the gitless fixture
        # shape GateManifestSlugResolutionTest pins): the candidate resolver
        # reads only the facts block, never a git probe.
        path = self.root / name
        path.mkdir(parents=True)
        _write(
            path / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        return path

    def test_resolvable_manifest_reports_latest_record_and_all_verified_destinations(self):
        # Repeated branch records: the LATEST record is the authoritative
        # binding. Every verified migrated and renamed destination remains
        # represented, in manifest order, duplicates preserved; unverified
        # rows, non-dictionary rows, and skipped-section rows are never
        # references; the truthiness of the verified mark is judged exactly
        # as the inline comprehension judged it.
        manifest_path = self._manifest(
            json.dumps(
                {
                    "migrated": [
                        {"destination": "docs/tmp/a.md", "verified": True},
                        "a-string-row",
                        {"destination": "docs/tmp/b.md", "verified": False},
                        {"destination": "docs/tmp/a.md", "verified": True},
                        {"destination": "docs/tmp/c.md", "verified": "truthy-mark"},
                    ],
                    "renamed": [
                        {"destination": "docs/tmp/r.md", "verified": True},
                        {"destination": "docs/tmp/unverified-r.md"},
                    ],
                    "skipped": [
                        {"destination": "docs/tmp/skipped.md", "verified": True},
                    ],
                    "failed": [],
                    "branch": [
                        {"branch": "wt-old", "source": "/stale"},
                        {"branch": "wt-run", "source": "/run"},
                    ],
                }
            ).encode("utf-8")
        )
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsNone(state["read_error"])
        self.assertIsNone(state["shape_error"])
        self.assertIsNone(state["destinations_error"])
        self.assertEqual(state["recorded"], "wt-run")
        self.assertEqual(state["record"], {"branch": "wt-run", "source": "/run"})
        self.assertEqual(
            state["verified_destinations"],
            ["docs/tmp/a.md", "docs/tmp/a.md", "docs/tmp/c.md", "docs/tmp/r.md"],
        )
        # verified_rows is the same collection as dictionaries beside their
        # destinations (plan 2026-11-01-gate-removal-inherited-manifest-
        # rows): same order, duplicates preserved, additive only.
        self.assertEqual(
            state["verified_rows"],
            [
                {"destination": "docs/tmp/a.md", "verified": True},
                {"destination": "docs/tmp/a.md", "verified": True},
                {"destination": "docs/tmp/c.md", "verified": "truthy-mark"},
                {"destination": "docs/tmp/r.md", "verified": True},
            ],
        )

    def test_absent_manifest_resolves_unresolved(self):
        # A path with no file behind it is an unresolved read (the OSError
        # family the consumer refuses on): no record, no destinations.
        state = MODULE._resolve_closeout_reference_state(self.root / "absent.json")
        self.assertIsInstance(state["read_error"], OSError)
        self.assertIsNone(state["recorded"])
        self.assertEqual(state["record"], {})
        self.assertEqual(state["verified_destinations"], [])
        self.assertIsNone(state["shape_error"])
        self.assertIsNone(state["destinations_error"])

    def test_unreadable_json_resolves_unresolved(self):
        # Unreadable JSON (the ValueError family): unresolved, no
        # destinations; the consumer keeps its named unreadable refusal.
        manifest_path = self._manifest(b"{not json")
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsInstance(state["read_error"], ValueError)
        self.assertIsNone(state["recorded"])
        self.assertEqual(state["verified_destinations"], [])
        self.assertIsNone(state["shape_error"])
        self.assertIsNone(state["destinations_error"])

    def test_array_root_resolves_unresolved_shape_error(self):
        # A parsed array root is a shape error, never normalized: the
        # resolver returns no references and carries the same AttributeError
        # the inline manifest access raised (the consumer re-raises it so
        # the caught OUTCOME: tool_error shape is preserved).
        manifest_path = self._manifest(b"[]")
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsNone(state["read_error"])
        self.assertIsInstance(state["shape_error"], AttributeError)
        self.assertEqual(state["verified_destinations"], [])
        self.assertIsNone(state["destinations_error"])
        self.assertEqual(state["record"], {})
        self.assertIsNone(state["recorded"])

    def test_non_list_branch_field_leaves_record_unusable(self):
        # A non-list truthy branch field (a string, a dict) resolves to an
        # unusable record (record {} / recorded None) with no shape error:
        # the consumer's named no-branch-record legacy skip keys off exactly
        # this state; no shape is normalized.
        for body in (
            json.dumps({"branch": "wt-run", "migrated": []}).encode("utf-8"),
            json.dumps({"branch": {"branch": "wt-run"}}).encode("utf-8"),
        ):
            state = MODULE._resolve_closeout_reference_state(self._manifest(body))
            self.assertIsNone(state["shape_error"])
            self.assertEqual(state["record"], {})
            self.assertIsNone(state["recorded"])

    def test_string_latest_branch_record_leaves_record_unusable(self):
        # A non-dictionary latest branch record (append semantics gone
        # wrong) resolves to an unusable record while the raw records value
        # and the readable destinations stay factual.
        manifest_path = self._manifest(
            json.dumps(
                {
                    "migrated": [{"destination": "docs/tmp/a.md", "verified": True}],
                    "branch": [{"branch": "wt-old"}, "stale-late-record"],
                }
            ).encode("utf-8")
        )
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsNone(state["shape_error"])
        self.assertEqual(state["records"], [{"branch": "wt-old"}, "stale-late-record"])
        self.assertEqual(state["record"], {})
        self.assertIsNone(state["recorded"])
        self.assertEqual(state["verified_destinations"], ["docs/tmp/a.md"])

    def test_string_row_in_migrated_is_ignored(self):
        # A string row inside migrated is ignored exactly as the inline
        # comprehension ignored it: never a reference, never an error.
        manifest_path = self._manifest(
            json.dumps(
                {
                    "branch": [{"branch": "wt-run"}],
                    "migrated": ["stray-row", {"destination": "docs/tmp/a.md", "verified": True}],
                }
            ).encode("utf-8")
        )
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsNone(state["destinations_error"])
        self.assertEqual(state["verified_destinations"], ["docs/tmp/a.md"])

    def test_integer_migrated_section_resolves_no_destinations(self):
        # A non-iterable migrated section is a destinations error carrying
        # the same TypeError the inline comprehension raised: no
        # destinations resolve, the record stays usable (the consumer
        # re-raises at its guard-check point), no normalization.
        manifest_path = self._manifest(
            json.dumps({"branch": [{"branch": "wt-run"}], "migrated": 5}).encode("utf-8")
        )
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsNone(state["read_error"])
        self.assertIsNone(state["shape_error"])
        self.assertIsInstance(state["destinations_error"], TypeError)
        self.assertEqual(state["verified_destinations"], [])
        self.assertEqual(state["verified_rows"], [])
        self.assertEqual(state["recorded"], "wt-run")

    def test_integer_renamed_section_discards_partial_destinations(self):
        # A non-iterable renamed section after readable migrated rows
        # discards the partial collection: an unsupported shape resolves to
        # no destinations, never to a half-read reference set.
        manifest_path = self._manifest(
            json.dumps(
                {
                    "branch": [{"branch": "wt-run"}],
                    "migrated": [{"destination": "docs/tmp/a.md", "verified": True}],
                    "renamed": 7,
                }
            ).encode("utf-8")
        )
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsInstance(state["destinations_error"], TypeError)
        self.assertEqual(state["verified_destinations"], [])

    def test_typeerror_resolves_prevented_rows_empty_loop_order_invariant(self):
        # Loop-order invariant (plan
        # 2026-11-04-closeout-clobber-guard-review-residual-trio Task 4):
        # given the resolver state after a TypeError, prevented_rows is
        # empty. The prevented_clobbers read sits AFTER the migrated/renamed
        # reads inside the same TypeError guard, so a non-iterable migrated
        # section aborts the guard before any prevented row is collected
        # even though this manifest carries a collectible prevented row;
        # the handler's reset covers the key symmetrically once landed.
        # GREEN-first: this passes before the reset lands (the prevented
        # loop never runs past the raising read), so its one RED credential
        # is the in-task reorder mutation run before the apply bullet
        # (prevented read hoisted ahead of the migrated/renamed reads with
        # the reset absent); a future edit turns it RED only by BOTH
        # reordering the prevented read ahead of the migrated/renamed reads
        # AND dropping the prevented_rows reset.
        manifest_path = self._manifest(
            json.dumps(
                {
                    "branch": [{"branch": "wt-run"}],
                    "prevented_clobbers": [
                        {
                            "destination": "docs/tmp/execute-plan/x/rewound-record.md",
                            "action": "restored-from-HEAD",
                        },
                    ],
                    "migrated": 5,
                }
            ).encode("utf-8")
        )
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertIsInstance(state["destinations_error"], TypeError)
        self.assertEqual(state["prevented_rows"], [])

    def test_skipped_section_rows_are_never_references(self):
        # skipped-section rows carry no presence requirement: their
        # destinations are never references.
        manifest_path = self._manifest(
            json.dumps(
                {
                    "branch": [{"branch": "wt-run"}],
                    "migrated": [],
                    "renamed": [],
                    "skipped": [
                        {"destination": "docs/tmp/skipped.md", "verified": True}
                    ],
                }
            ).encode("utf-8")
        )
        state = MODULE._resolve_closeout_reference_state(manifest_path)
        self.assertEqual(state["verified_destinations"], [])

    def test_manifest_candidate_selection(self):
        # The "which manifest" half of the reference state: the explicit
        # --migration-manifest operand is authoritative (an absent explicit
        # file yields (None, True) so the caller reports its distinct
        # explicit-path skip and never falls back), the derived lookup
        # probes the canonical closeout-migration.json first and the legacy
        # migration-manifest.json twin second.
        target = self._checkout_shape("primary")
        plan = target / "docs/history/plans/2026-10-29-feat.md"
        derived = target / "docs/tmp/execute-plan/feat/closeout-migration.json"
        _write(derived, b"{}")
        override = self.root / "override.json"
        _write(override, b"{}")
        chosen, explicit = MODULE._closeout_manifest_candidate(target, plan, str(override))
        self.assertEqual(chosen, override)
        self.assertTrue(explicit)
        absent = self.root / "absent-override.json"
        chosen, explicit = MODULE._closeout_manifest_candidate(target, plan, str(absent))
        self.assertIsNone(chosen)
        self.assertTrue(explicit)
        legacy = target / "docs/tmp/execute-plan/feat/migration-manifest.json"
        _write(legacy, b"{}")
        chosen, explicit = MODULE._closeout_manifest_candidate(target, plan, None)
        self.assertEqual(chosen, derived)
        self.assertFalse(explicit)
        derived.unlink()
        chosen, explicit = MODULE._closeout_manifest_candidate(target, plan, None)
        self.assertEqual(chosen, legacy)
        self.assertFalse(explicit)
        legacy.unlink()
        chosen, explicit = MODULE._closeout_manifest_candidate(target, plan, None)
        self.assertIsNone(chosen)
        self.assertFalse(explicit)


class CloseoutReferenceConsumerParityTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] Consumer byte-parity witnesses (plan
    2026-10-29-done-gate-report-retention Task 1): routing the gate's
    exact-branch adjudication through the extracted reference resolver keeps
    every outcome identical - the latest record governs liveness over
    repeated records, every verified migrated and renamed destination stays
    presence-checked, skipped entries impose no presence requirement, and
    the malformed shapes keep their named skips, the unreadable refusal, and
    the caught tool-error class. Branch-only mode adjudicates the same way
    and gains no retention behavior."""

    def _manifest_path(self) -> Path:
        return self.primary / "docs/tmp/execute-plan/x/closeout-migration.json"

    def _rewrite_manifest(self, mutate) -> Path:
        path = self._manifest_path()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        mutate(manifest)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_repeated_records_latest_governs_liveness(self):
        # Repeated branch records with a resolvable recorded ref: the
        # LATEST record governs (the stale earlier record never refuses)
        # while the verified migrated destination stays presence-checked.
        self._seed_migration_manifest(landed=True)
        self._rewrite_manifest(
            lambda m: m.update(
                branch=[
                    {"branch": "wt-stale", "source": "/stale"},
                    {"branch": "wt-run", "source": str(self.worktree)},
                ]
            )
        )
        self._git(self.primary, "merge", "-q", "--no-edit", "wt-run")
        expected = self._branch_oid("wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch wt-run ancestry-accounted at {expected}", out)
        self.assertIn(
            f"branch-disposition: branch=wt-run disposition=ancestry-accounted oid={expected}",
            out,
        )

    def test_repeated_records_latest_mismatch_refuses(self):
        # When the LATEST record binds a different branch, the identity
        # binding refuses against it - proof the last record, not an
        # earlier one, governs.
        self._seed_migration_manifest(landed=True)
        self._rewrite_manifest(
            lambda m: m.update(
                branch=[
                    {"branch": "wt-run", "source": str(self.worktree)},
                    {"branch": "wt-stale", "source": "/stale"},
                ]
            )
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("exact-branch identity mismatch", out)
        self.assertIn("wt-stale", out)
        self.assertIn("wt-run", out)

    def test_renamed_verified_destination_presence_enforced(self):
        # A verified renamed destination missing under the target refuses
        # exactly like a migrated one: every verified destination from both
        # sections remains represented.
        self._seed_migration_manifest(landed=True)
        self._rewrite_manifest(
            lambda m: m["renamed"].append(
                {
                    "source": "docs/tmp/vanished-renamed-source.md",
                    "destination": "docs/tmp/vanished-renamed.md",
                    "verified": True,
                }
            )
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("migrated artifact(s) missing under the target", out)
        self.assertIn("docs/tmp/vanished-renamed.md", out)

    def test_skipped_entry_imposes_no_presence_requirement(self):
        # A skipped-section entry is no reference: its destination imposes
        # no presence requirement and the accounted closeout passes.
        self._seed_migration_manifest(landed=True)
        self._rewrite_manifest(
            lambda m: m.update(
                skipped=[
                    {
                        "source": "docs/tmp/never-existed.md",
                        "destination": "docs/tmp/never-existed.md",
                        "verified": True,
                    }
                ]
            )
        )
        self._git(self.primary, "merge", "-q", "--no-edit", "wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("ancestry-accounted", out)
        self.assertNotIn("missing under the target", out)
        self.assertNotIn("never-existed.md", out)

    def test_unreadable_manifest_refuses(self):
        # Unreadable JSON at the derived manifest path: the named unreadable
        # refusal (OUTCOME: fail), unchanged through the resolver.
        self._seed_migration_manifest(landed=True)
        self._manifest_path().write_bytes(b"{not json")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("unreadable", out)
        self.assertIn("exact-branch binding cannot be verified", out)

    def test_array_root_reaches_tool_error(self):
        # A parsed array root reaches the caught tool-error class (exit 3)
        # at the same point the inline manifest access raised: no
        # normalization, no new refusal class.
        self._seed_migration_manifest(landed=True)
        self._manifest_path().write_bytes(b"[]")
        code, out, err = self._run_gate()
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("AttributeError", err)

    def test_integer_migrated_section_reaches_tool_error(self):
        # A non-iterable migrated section reaches the caught tool-error
        # class only after the identity binding passes - the inline
        # guard-check ordering, preserved through the resolver.
        self._seed_migration_manifest(landed=True)
        self._rewrite_manifest(lambda m: m.update(migrated=5))
        code, out, err = self._run_gate()
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("TypeError", err)

    def test_non_list_branch_field_skips(self):
        # A non-list truthy branch field keeps the named no-branch-record
        # legacy skip; worktree mode passes with the skip line and no
        # disposition.
        self._seed_migration_manifest(landed=True)
        self._manifest_path().write_bytes(
            json.dumps({"branch": "wt-run", "migrated": [], "renamed": []}).encode("utf-8")
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(
            "branch-closeout: skipped (migration manifest carries no branch "
            "record; legacy shape)",
            out,
        )
        self.assertNotIn("branch-disposition:", out)

    def test_string_latest_branch_record_skips(self):
        # A non-dictionary latest branch record keeps the named
        # recorded-branch-unresolved legacy skip.
        self._seed_migration_manifest(landed=True)
        self._rewrite_manifest(
            lambda m: m.update(
                branch=[
                    {"branch": "wt-run", "source": str(self.worktree)},
                    "stale-late-record",
                ]
            )
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(
            "branch-closeout: skipped (recorded branch unresolved at "
            "transfer; legacy shape)",
            out,
        )
        self.assertNotIn("branch-disposition:", out)

    def test_string_row_in_migrated_is_ignored(self):
        # A string row inside migrated is ignored: no missing-destination
        # reason, no tool error, and the real verified row still binds the
        # accounted closeout.
        self._seed_migration_manifest(landed=True)
        self._rewrite_manifest(
            lambda m: m.update(
                migrated=["stray-row"] + [
                    {
                        "source": ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                        "destination": ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                        "verified": True,
                    }
                ]
            )
        )
        self._git(self.primary, "merge", "-q", "--no-edit", "wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("ancestry-accounted", out)
        self.assertNotIn("missing under the target", out)

    def test_branch_only_repeated_records_latest_governs(self):
        # Branch-only mode binds the LATEST record too, and gains no new
        # behavior: the accounted verdict is unchanged (branch-only
        # retention stays deferred to the linked follow-up item).
        self._seed_migration_manifest(landed=False)
        branch = "wt-done"
        self._git(self.primary, "branch", branch, "HEAD")
        expected = self._branch_oid(branch)
        manifest_dir = self.primary / "docs/tmp/execute-plan/branch-only-parity"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = manifest_dir / "closeout-migration.json"
        manifest.write_text(
            json.dumps(
                {
                    "migrated": [
                        {
                            "source": ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                            "destination": ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md",
                            "verified": True,
                        }
                    ],
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [
                        {"branch": "wt-other", "source": "branch-only"},
                        {"branch": branch, "source": "branch-only"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        code, out, _err = self._run_gate_branch_only(branch, manifest)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"branch-closeout: branch {branch} ancestry-accounted at {expected}", out)


class TeardownRecordMirrorEndToEndTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] The record-preservation contract end to end
    (plan 2026-10-30-execute-plan-teardown-staging-record-mirror Task 3):
    a real git primary plus a registered run worktree drive the production
    sequence over the four run-produced review path classes Task 1 names -
    the review staging document, its .stats.json sidecar, the producing
    round's review-certs seal entry, and the Phase 4 plans-egress pointer.
    The boundary-mirror operands carry exactly those four paths (never a
    directory copy), the closeout migration records the byte-identical
    receipt-backed primary copies as verified migrated rows, and
    gate-removal passes over the manifest only while every destination
    stands, refusing and retaining the worktree and branch when one does
    not."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    RUN_SESSION_ID = "sess-record-mirror-e2e-1"
    PLAN_REL = "docs/history/plans/2026-10-30-record-mirror-e2e.md"
    SESSION_DIR_REL = "docs/tmp/execute-plan/record-mirror-e2e"

    # The four Task 1 path classes, one boundary-mirror operand each, at the
    # homes the fixture facts resolve: the review staging document and its
    # .stats.json sidecar twin, the producing round's review-certs seal
    # entry, and the Phase 4 plans-egress pointer written before the archive
    # move.
    REVIEW_DOC_REL = ".ai-playbook/reviews/2026-10-30-plan-review-record-mirror-e2e-code-review-r1.md"
    # The sidecar twin grammar the staging validator and the gate's
    # sibling arm enforce: the .md suffix is replaced, not appended.
    STATS_SIDECAR_REL = str(Path(REVIEW_DOC_REL).with_suffix(".stats.json"))
    SEAL_ENTRY_REL = ".ai-playbook/review-certs/record-mirror-e2e.wt-proj-wt-run.md"
    EXEC_POINTER_REL = ".ai-playbook/reviews/2026-10-30-plan-review-record-mirror-e2e-exec-r1.md"

    RECORD_BYTES = {
        REVIEW_DOC_REL: b"code review round r1: verdict yes\n",
        STATS_SIDECAR_REL: b'{"round": 1, "verdict": "yes"}\n',
        SEAL_ENTRY_REL: (
            b"## round 1\n"
            b"artifact: docs/history/plans/2026-10-30-record-mirror-e2e.md\n"
            b"round_start_commit: abc1234def\n"
            b"round_close_commit: abc1234def\n"
        ),
        EXEC_POINTER_REL: (
            b"plans-egress pointer: the plan archive commit carries these bytes\n"
        ),
    }

    MIRROR_OPERANDS = [
        REVIEW_DOC_REL,
        STATS_SIDECAR_REL,
        SEAL_ENTRY_REL,
        EXEC_POINTER_REL,
    ]

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-record-mirror-e2e-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        env = _hermetic_git_env(self.root, **self.GIT_IDENTITY)
        subprocess.run(
            ["git", "-C", str(self.primary), "init", "-q", "-b", "main"],
            capture_output=True, env=env, check=True,
        )
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\n"
            b'reviews_dir = ".ai-playbook/reviews/"\n'
            b'tmp_dir = "docs/tmp/"\n'
            b'metrics_dir = ".ai-playbook/metrics/"\n'
            b'review_certs_dir = ".ai-playbook/review-certs/"\n'
            b"```\n",
        )
        (self.primary / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(DONE_LOCK_SCRIPT_PATH, self.primary / "scripts" / "done-lock.sh")
        _write(self.primary / self.PLAN_REL, self._plan_bytes())
        self._git(self.primary, "add", "-A")
        self._git(self.primary, "commit", "-q", "-m", "init: fixture repo")
        self.worktree = self.root / "proj-wt-run"
        self._git(self.primary, "worktree", "add", "-q", "-b", "wt-run", str(self.worktree))
        session_dir = self.worktree / self.SESSION_DIR_REL
        _write_session_manifest(
            session_dir / "manifest.md",
            [],
            run_worktree=str(self.worktree),
            run_session_id=self.RUN_SESSION_ID,
            plan_path=self.PLAN_REL,
        )
        self.baseline = session_dir / "closeout-baseline.json"
        _capture_baseline(self.worktree, self.baseline)
        self.migration_manifest = (
            self.primary / self.SESSION_DIR_REL / "closeout-migration.json"
        )
        pins = _hermetic_lock_env(self.root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _plan_bytes(self) -> bytes:
        return (
            "# Plan: record-mirror e2e fixture\n"
            "\n"
            f"Plan review record: {self.REVIEW_DOC_REL}\n"
        ).encode("utf-8")

    def _git(self, repo: Path, *args: str, check: bool = True):
        env = _hermetic_git_env(self.root, **self.GIT_IDENTITY)
        proc = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env
        )
        if check and proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc

    def _facts_home_dirs(self) -> dict[str, str]:
        text = (self.worktree / ".ai-playbook/facts.md").read_text(encoding="utf-8")
        homes: dict[str, str] = {}
        for line in text.splitlines():
            for key in ("reviews_dir", "review_certs_dir"):
                prefix = key + " = "
                if line.startswith(prefix):
                    homes[key] = line[len(prefix):].strip().strip('"')
        return homes

    def _produce_run_records(self) -> None:
        """The run's Phase 3/4 outputs: the four record files appear in the
        worktree only after the Phase 0 baseline capture."""
        for rel, data in self.RECORD_BYTES.items():
            _write(self.worktree / rel, data)

    def _boundary_row_lines(self) -> list[str]:
        manifest = self.worktree / self.SESSION_DIR_REL / "manifest.md"
        return [
            line.strip()
            for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("task_boundary:")
        ]

    def _run_boundary_mirror(self) -> tuple[int, str, str]:
        """The real boundary-mirror operation over exactly the four Task 1
        operands, in-process under the hermetic lock env."""
        argv = [
            "boundary-mirror",
            "--worktree", str(self.worktree),
            "--target", str(self.primary),
            "--manifest", str(self.worktree / self.SESSION_DIR_REL / "manifest.md"),
            "--run-session-id", self.RUN_SESSION_ID,
            "--plan-path", self.PLAN_REL,
            "--run-worktree", str(self.worktree),
            "--boundary-note", "task 1 commit abc1234 verification: pass",
        ]
        for rel in self.MIRROR_OPERANDS:
            argv += ["--mirror-path", rel]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = MODULE.main(argv)
        return code, out.getvalue(), err.getvalue()

    def _run_gate(self) -> tuple[int, str, str]:
        return _run_cli(
            "gate-removal",
            "--plan", str(self.worktree / self.PLAN_REL),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            "--migration-manifest", str(self.migration_manifest),
            cwd=self.root,
        )

    def _resources_registered(self) -> tuple[bool, bool]:
        """(worktree registered, branch live), read with the gate's own
        identity-binding predicate."""
        registered = any(
            Path(entry["path"]).resolve() == self.worktree.resolve()
            for entry in MODULE._parse_worktree_entries(self.primary)
        )
        branch_live = self._git(
            self.primary, "rev-parse", "--verify", "--quiet", "refs/heads/wt-run", check=False
        ).returncode == 0
        return registered, branch_live

    def _drive_to_migrated_state(self) -> None:
        """Produce the four records, boundary-mirror them by exact path,
        then migrate over the byte-identical primary copies: the state both
        Task 3 witnesses start from."""
        self._produce_run_records()
        code, _out, err = self._run_boundary_mirror()
        self.assertEqual(code, 0, err)
        code = _migrate(self.worktree, self.primary, self.baseline, self.migration_manifest)
        self.assertEqual(code, 0)

    def test_four_class_record_set_mirrors_migrates_and_gates_clean(self):
        """[class: REPOSITORY_TEST] The complete end-to-end pass: the four
        Task 1 operands produce verified mirror receipts, the closeout
        migration records every byte-identical primary copy as a verified
        migrated destination without rewriting it, and gate-removal passes
        with the removal disposition while every destination exists."""
        self._produce_run_records()
        code, out, err = self._run_boundary_mirror()
        self.assertEqual(code, 0, out + err)
        # Verified receipts: one complete row carrying exactly the four
        # operands, each item verified with the produced bytes' digest.
        rows = self._boundary_row_lines()
        self.assertEqual(len(rows), 1)
        status, items = MODULE._parse_mirror_row(rows[0])
        self.assertEqual(status, "complete")
        self.assertEqual([item["path"] for item in items], self.MIRROR_OPERANDS)
        for item in items:
            self.assertEqual(item["status"], "verified")
            self.assertEqual(item["sha256"], _digest(self.RECORD_BYTES[item["path"]]))
        # The primary homes hold byte-identical copies; freeze their mtimes
        # so the no-rewrite property below is observable.
        for rel in self.MIRROR_OPERANDS:
            self.assertEqual((self.primary / rel).read_bytes(), self.RECORD_BYTES[rel])
            os.utime(self.primary / rel, (1000, 1000))
        code = _migrate(self.worktree, self.primary, self.baseline, self.migration_manifest)
        self.assertEqual(code, 0)
        data = json.loads(self.migration_manifest.read_text(encoding="utf-8"))
        self.assertEqual(data.get("replaced"), [])
        self.assertEqual(data.get("renamed"), [])
        self.assertEqual(data.get("failed"), [])
        migrated = {entry["source"]: entry for entry in data.get("migrated", [])}
        for rel in self.MIRROR_OPERANDS:
            with self.subTest(path_class=rel):
                self.assertIn(rel, migrated)
                self.assertTrue(migrated[rel]["verified"])
                self.assertEqual(
                    migrated[rel]["destination"],
                    (self.primary.resolve() / rel).as_posix(),
                )
                self.assertEqual((self.primary / rel).read_bytes(), self.RECORD_BYTES[rel])
                self.assertEqual(
                    os.stat(self.primary / rel).st_mtime,
                    1000,
                    "the byte-identical primary copy was rewritten",
                )
        # The manifest-backed gate passes while every destination stands.
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(
            f"removal: git worktree remove --force {shlex.quote(str(self.worktree))}",
            out,
        )
        self.assertIn("branch wt-run ancestry-accounted at", out)
        for rel in self.MIRROR_OPERANDS:
            self.assertTrue((self.primary / rel).is_file())

    def test_missing_migrated_destination_refuses_and_retains_per_path_class(self):
        """[class: REPOSITORY_TEST] The missing-primary-artifact control
        after migration, once per Task 1 path class: removing one mirrored
        destination from the primary home makes gate-removal refuse with
        that exact path named, while the source worktree and its branch
        stay registered for recovery. The cited document and its sidecar
        are caught by the gate's pre-existing records arms (the document's
        missing-record refusal, the sidecar's destroyed-sibling refusal);
        the uncited seal entry and plans-egress pointer are caught only by
        the migration-manifest destination guard this plan binds, whose
        held disposition retains both resources."""
        self._drive_to_migrated_state()
        expectations = {
            self.REVIEW_DOC_REL: (
                "missing: " + self.REVIEW_DOC_REL,
                None,
            ),
            self.STATS_SIDECAR_REL: (
                "refused: claimed record's required stats sibling exists only "
                "in the worktree staging home: " + self.STATS_SIDECAR_REL,
                None,
            ),
            self.SEAL_ENTRY_REL: (
                "migrated artifact(s) missing under the target: "
                + (self.primary.resolve() / self.SEAL_ENTRY_REL).as_posix(),
                "held:",
            ),
            self.EXEC_POINTER_REL: (
                "migrated artifact(s) missing under the target: "
                + (self.primary.resolve() / self.EXEC_POINTER_REL).as_posix(),
                "held:",
            ),
        }
        for rel, (evidence, extra) in expectations.items():
            with self.subTest(path_class=rel):
                destination = self.primary / rel
                destination.unlink()
                try:
                    code, out, _err = self._run_gate()
                    self.assertEqual(code, 1, out)
                    self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
                    self.assertIn(evidence, out)
                    if extra is not None:
                        self.assertIn(extra, out)
                    registered, branch_live = self._resources_registered()
                    self.assertTrue(
                        registered, "the refused gate dropped the worktree registration"
                    )
                    self.assertTrue(branch_live, "the refused gate removed the branch ref")
                finally:
                    # Restore so the next path class starts from the complete
                    # set, even when a subTest assertion fails.
                    _write(destination, self.RECORD_BYTES[rel])

    def test_boundary_mirror_operands_carry_exactly_the_four_task1_path_classes(self):
        """[class: REPOSITORY_TEST] Caller path completeness: the
        boundary-mirror operand list is exactly one path per Task 1 class -
        the review staging document, its .stats.json sidecar twin, the
        producing round's review-certs seal entry, and the Phase 4
        plans-egress pointer - each under the facts home its class is
        produced in, with no directory operand and no extra paths."""
        operands = self.MIRROR_OPERANDS
        homes = self._facts_home_dirs()
        self.assertEqual(len(operands), 4)
        self.assertEqual(len(set(operands)), 4, "a duplicate or directory operand")
        for rel in operands:
            self.assertFalse(rel.endswith("/"), "a whole-directory operand")
        self.assertEqual(operands[0], self.REVIEW_DOC_REL)
        self.assertEqual(operands[1], self.STATS_SIDECAR_REL)
        self.assertEqual(operands[2], self.SEAL_ENTRY_REL)
        self.assertEqual(operands[3], self.EXEC_POINTER_REL)
        reviews_dir = homes["reviews_dir"].rstrip("/")
        certs_dir = homes["review_certs_dir"].rstrip("/")
        self.assertTrue(self.REVIEW_DOC_REL.startswith(reviews_dir + "/"))
        self.assertTrue(self.STATS_SIDECAR_REL.startswith(reviews_dir + "/"))
        self.assertTrue(self.EXEC_POINTER_REL.startswith(reviews_dir + "/"))
        self.assertTrue(self.SEAL_ENTRY_REL.startswith(certs_dir + "/"))
        # The sidecar is the document's .stats.json twin, not a loose file.
        self.assertEqual(
            Path(self.STATS_SIDECAR_REL).name,
            Path(self.REVIEW_DOC_REL).with_suffix(".stats.json").name,
        )
        # The plans-egress pointer carries the Phase 4 naming grammar.
        self.assertRegex(
            Path(self.EXEC_POINTER_REL).name,
            r"^\d{4}-\d{2}-\d{2}-plan-review-.+-exec-r\d+\.md$",
        )


class ZeroPlanMigrateSkeletonProducerTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] The done_run.sh zero/multi-plan producer's
    migrate-shape twin (lesson 289's witnessed hand-build): the bash function
    is extracted with its two manifest helpers and exercised against fixture
    manifests, pinning the emitted file the branch-only pass consumes."""

    @staticmethod
    def _extract_functions() -> str:
        text = (SCRIPT_PATH.parent / "done_run.sh").read_text(encoding="utf-8")
        lines = text.splitlines()
        blocks = []
        for name in (
            "manifest_scalar",
            "manifest_field",
            "write_zero_multi_plan_skip_record",
        ):
            start = next(
                i for i, ln in enumerate(lines) if ln.startswith(f"{name}() {{")
            )
            end = next(i for i in range(start, len(lines)) if lines[i] == "}")
            blocks.append("\n".join(lines[start : end + 1]))
        return "\n".join(blocks)

    def _run_producer(
        self, session: Path, manifest: Path, cwd: Path
    ) -> subprocess.CompletedProcess:
        script = (
            f"{self._extract_functions()}\n"
            f"write_zero_multi_plan_skip_record {shlex.quote(str(session))} "
            f"{shlex.quote(str(manifest))}\n"
        )
        return subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            cwd=str(cwd),
            env=_hermetic_git_env(session.parent),
        )

    @staticmethod
    def _manifest_fixture(path: Path, owned: list[str]) -> Path:
        path.write_text(
            json.dumps({"run_id": "run-z9", "owned_plan_paths": owned}),
            encoding="utf-8",
        )
        return path

    def _init_fixture_repo(self, root: Path, branch: str) -> Path:
        repo = root / "proj"
        repo.mkdir()
        env = _hermetic_git_env(root)
        subprocess.run(["git", "init", "-q", "-b", branch, str(repo)], check=True, env=env)
        _write(repo / "seed.txt", b"seed\n")
        subprocess.run(
            ["git", "-C", str(repo), "-c", "user.email=t@fixture", "-c",
             "user.name=t", "add", "-A"],
            check=True, env=env,
        )
        subprocess.run(
            ["git", "-C", str(repo), "-c", "user.email=t@fixture", "-c",
             "user.name=t", "commit", "-q", "-m", "init: fixture repo"],
            check=True, env=env,
        )
        return repo

    def test_zero_plan_run_emits_skeleton_beside_skip_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._init_fixture_repo(root, "wt-zero-plan-x")
            session = root / "docs/tmp/done-session"
            session.mkdir(parents=True)
            manifest = self._manifest_fixture(session / "run-manifest.json", [])
            proc = self._run_producer(session, manifest, cwd=repo)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("migrate-shape manifest skeleton present", proc.stderr)
            skeleton = session / "worktree-migrate-baseline-run-z9-manifest.json"
            self.assertTrue(skeleton.is_file(), proc.stdout + proc.stderr)
            data = json.loads(skeleton.read_text(encoding="utf-8"))
            self.assertEqual(
                data,
                {
                    "branch": [
                        {"branch": "wt-zero-plan-x", "source": str(repo.resolve())}
                    ],
                    "migrated": [],
                },
            )
            self.assertTrue(
                (session / "worktree-migrate-baseline-run-z9-skip.json").is_file()
            )

    def test_skeleton_write_is_idempotent_per_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._init_fixture_repo(root, "wt-zero-plan-x")
            session = root / "docs/tmp/done-session"
            session.mkdir(parents=True)
            manifest = self._manifest_fixture(session / "run-manifest.json", [])
            first = self._run_producer(session, manifest, cwd=repo)
            self.assertEqual(first.returncode, 0, first.stderr)
            skeleton = session / "worktree-migrate-baseline-run-z9-manifest.json"
            bytes_first = skeleton.read_bytes()
            second = self._run_producer(session, manifest, cwd=repo)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(skeleton.read_bytes(), bytes_first)
            self.assertNotIn("migrate-shape manifest skeleton present", second.stdout)

    def test_single_plan_run_writes_neither_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self._init_fixture_repo(root, "wt-one-plan-x")
            session = root / "docs/tmp/done-session"
            session.mkdir(parents=True)
            manifest = self._manifest_fixture(
                session / "run-manifest.json", ["docs/history/plans/2026-10-29-x.md"]
            )
            proc = self._run_producer(session, manifest, cwd=repo)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(
                sorted(p.name for p in session.iterdir()), ["run-manifest.json"]
            )

    def test_no_git_checkout_skips_skeleton_and_keeps_skip_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = root / "docs/tmp/done-session"
            session.mkdir(parents=True)
            manifest = self._manifest_fixture(session / "run-manifest.json", [])
            proc = self._run_producer(session, manifest, cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(
                (session / "worktree-migrate-baseline-run-z9-skip.json").is_file()
            )
            self.assertFalse(
                (session / "worktree-migrate-baseline-run-z9-manifest.json").exists()
            )
            self.assertIn("skeleton not written", proc.stderr)


class GateManifestSlugResolutionTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] Manifest-slug resolution and citation-remedy
    witnesses (plan gate-removal-closeout-accounting Task 1): the default
    migration-manifest lookup keys the execute-plan session directory by the
    canonical <PLAN_SLUG> (a dated plan file loses its leading date and
    extension; a dated plan directory's PLAN.md charter loses the leading
    date from the directory name), the explicit --migration-manifest operand
    stays authoritative with no fallback, and a never-verifiable citation
    carries a correction remedy distinct from the migrate remedy."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-slug-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.worktree = self._scratch_pair_member(self.root / "wt-session")
        self.primary = self._scratch_pair_member(self.root / "primary")

    def _scratch_pair_member(self, path: Path) -> Path:
        # One member of the scratch pair: a facts-resolved checkout-shaped
        # directory (the gate reads only the facts block, the reviews home,
        # and the manifest file on this path; the branch-closeout skip arms
        # under test run before any git probe, so a gitless fixture is
        # faithful).
        path.mkdir(parents=True)
        _write(
            path / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        return path

    def _plan(self, plan_rel: str, record_rel: str) -> Path:
        # A plan under the worktree citing one review record, with the
        # record present under the PRIMARY home, so the records gate
        # verifies and the run reaches the branch-closeout lookup.
        _write(self.primary / record_rel, b"r1\n")
        plan = self.worktree / plan_rel
        _write(plan, f"# Plan\n\nPlan review record: {record_rel}\n".encode("utf-8"))
        return plan

    def _manifest(self, session_dir_rel: str, name: str, body: bytes) -> Path:
        path = self.primary / "docs/tmp" / session_dir_rel / name
        _write(path, body)
        return path

    @staticmethod
    def _manifest_body() -> bytes:
        # A manifest carrying no branch record: reading it yields the named
        # no-branch-record skip, the observable that proves WHICH file the
        # lookup opened (distinct from the no-manifest legacy skip).
        return json.dumps(
            {"migrated": [], "renamed": [], "skipped": [], "failed": []}
        ).encode("utf-8")

    def _run_gate(self, plan: Path, *extra: str) -> tuple[int, str, str]:
        return _run_cli(
            "gate-removal",
            "--plan", str(plan),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
            *extra,
            cwd=self.worktree,
        )

    NO_BRANCH_RECORD_SKIP = (
        "branch-closeout: skipped (migration manifest carries no branch "
        "record; legacy shape)"
    )
    NO_MANIFEST_SKIP = (
        "branch-closeout: skipped (no migration manifest found; the "
        "sweep arm owns legacy shapes)"
    )

    def test_date_prefixed_plan_resolves_to_stripped_session_dir(self):
        # The gate should resolve a date-prefixed plan named
        # 2026-10-19-feature to the feature execute-plan session directory:
        # a manifest written under docs/tmp/execute-plan/feature/ is found
        # (its no-branch-record skip prints), never the no-manifest legacy
        # skip the dated-stem lookup would take.
        plan = self._plan(
            "docs/history/plans/2026-10-19-feature.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-feature-r1.md",
        )
        self._manifest("execute-plan/feature", "closeout-migration.json", self._manifest_body())
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0, out)
        self.assertIn(self.NO_BRANCH_RECORD_SKIP, out)
        self.assertNotIn(self.NO_MANIFEST_SKIP, out)

    def test_dated_directory_charter_resolves_to_stripped_session_dir(self):
        # The gate should resolve a dated directory plan's charter operand
        # (PLAN.md inside 2026-10-19-dirplan/) to the date-stripped session
        # directory: the manifest under docs/tmp/execute-plan/dirplan/ is
        # read, never the no-manifest skip (a PLAN stem lookup would miss).
        plan = self._plan(
            "docs/history/plans/2026-10-19-dirplan/PLAN.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-dirplan-r1.md",
        )
        self._manifest("execute-plan/dirplan", "closeout-migration.json", self._manifest_body())
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0, out)
        self.assertIn(self.NO_BRANCH_RECORD_SKIP, out)
        self.assertNotIn(self.NO_MANIFEST_SKIP, out)

    def test_present_manifest_used_and_absent_reports_named_legacy_skip(self):
        # Present manifest: used (the no-branch-record skip names it).
        # Absent manifest: the named legacy skip, verbatim.
        plan = self._plan(
            "docs/history/plans/2026-10-19-present.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-present-r1.md",
        )
        self._manifest(
            "execute-plan/present", "closeout-migration.json", self._manifest_body()
        )
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0, out)
        self.assertIn(self.NO_BRANCH_RECORD_SKIP, out)
        absent_plan = self._plan(
            "docs/history/plans/2026-10-19-absent.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-absent-r1.md",
        )
        code, out, _err = self._run_gate(absent_plan)
        self.assertEqual(code, 0, out)
        self.assertIn(self.NO_MANIFEST_SKIP, out)

    def test_missing_citation_keeps_migrate_remedy(self):
        # A missing migration record keeps the migrate remedy: capture then
        # migrate can land the record, so the citation-correction remedy is
        # never printed for it.
        plan_rel = "docs/history/plans/2026-10-19-missing.md"
        record = ".ai-playbook/reviews/2026-10-19-plan-review-missing-r1.md"
        plan = self.worktree / plan_rel
        _write(plan, f"# Plan\n\nPlan review record: {record}\n".encode("utf-8"))
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(f"missing: {record}", out)
        self.assertIn("remedy: run worktree_closeout_migrate.py capture", out)
        self.assertNotIn(MODULE._GATE_CITATION_REMEDY_LINE, out)

    def test_never_verifiable_citation_gets_correction_remedy(self):
        # A never-verifiable citation (an absolute header citation is always
        # refused) carries the citation-specific attainable remedy and never
        # the migrate remedy no migrate run can make attainable.
        record = ".ai-playbook/reviews/2026-10-19-plan-review-abs-r1.md"
        plan = self.worktree / "docs/history/plans/2026-10-19-abs.md"
        _write(
            plan,
            f"# Plan\n\nPlan review record: {self.worktree.resolve() / record}\n".encode("utf-8"),
        )
        _write(self.worktree / record, b"r1 staged in the worktree only\n")
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused: label citation outside the reviews home:", out)
        self.assertIn(MODULE._GATE_CITATION_REMEDY_LINE, out)
        self.assertNotIn("remedy: run worktree_closeout_migrate.py capture", out)

    def test_explicit_manifest_used_when_both_paths_exist(self):
        # Precedence: with both the derived slug-directory manifest and the
        # explicit override present, the override is read (its unreadable
        # bytes refuse the run), never silently swapped for the derived one.
        plan = self._plan(
            "docs/history/plans/2026-10-19-both.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-both-r1.md",
        )
        self._manifest("execute-plan/both", "closeout-migration.json", self._manifest_body())
        override = self.root / "override-both.json"
        override.write_bytes(b"{not json")
        code, out, _err = self._run_gate(plan, "--migration-manifest", str(override))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("unreadable", out)
        self.assertNotIn(self.NO_BRANCH_RECORD_SKIP, out)

    def test_valid_override_without_derived_manifest(self):
        # A valid override with no derived manifest adjudicates through the
        # override (its no-branch-record skip prints), never the no-manifest
        # legacy skip.
        plan = self._plan(
            "docs/history/plans/2026-10-19-ovr.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-ovr-r1.md",
        )
        override = self.root / "override-ovr.json"
        override.write_bytes(self._manifest_body())
        code, out, _err = self._run_gate(plan, "--migration-manifest", str(override))
        self.assertEqual(code, 0, out)
        self.assertIn(self.NO_BRANCH_RECORD_SKIP, out)
        self.assertNotIn(self.NO_MANIFEST_SKIP, out)

    def test_missing_override_with_derived_manifest_is_distinct_skip(self):
        # A missing override with a present derived manifest produces the
        # DISTINCT explicit-path skip without falling back to the derived
        # manifest: the explicit operand is authoritative, so the derived
        # file is not consulted behind its back.
        plan = self._plan(
            "docs/history/plans/2026-10-19-gone.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-gone-r1.md",
        )
        self._manifest("execute-plan/gone", "closeout-migration.json", self._manifest_body())
        absent_override = self.root / "override-gone.json"
        code, out, _err = self._run_gate(
            plan, "--migration-manifest", str(absent_override)
        )
        self.assertEqual(code, 0, out)
        self.assertIn("explicit --migration-manifest", out)
        self.assertIn("no fallback", out)
        self.assertNotIn(self.NO_BRANCH_RECORD_SKIP, out)
        self.assertNotIn(self.NO_MANIFEST_SKIP, out)

    def test_legacy_migration_manifest_filename_accepted(self):
        # Legacy compatibility: migration-manifest.json in the slug session
        # directory is probed second and still binds (its no-branch-record
        # skip prints).
        plan = self._plan(
            "docs/history/plans/2026-10-19-legacyname.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-legacyname-r1.md",
        )
        self._manifest(
            "execute-plan/legacyname", "migration-manifest.json", self._manifest_body()
        )
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0, out)
        self.assertIn(self.NO_BRANCH_RECORD_SKIP, out)
        self.assertNotIn(self.NO_MANIFEST_SKIP, out)

    def test_legacy_skip_when_neither_supported_name_exists(self):
        # With neither supported manifest filename in the slug session
        # directory (a foreign file only), the named legacy no-manifest skip
        # reports and the run keeps its informational pass.
        plan = self._plan(
            "docs/history/plans/2026-10-19-none.md",
            ".ai-playbook/reviews/2026-10-19-plan-review-none-r1.md",
        )
        self._manifest("execute-plan/none", "other-file.json", b"{}\n")
        code, out, _err = self._run_gate(plan)
        self.assertEqual(code, 0, out)
        self.assertIn(self.NO_MANIFEST_SKIP, out)

    def test_plan_session_slug_forms(self):
        # The canonical <PLAN_SLUG> derivation, direct: a dated plan file
        # loses the leading date and extension; the dated directory's
        # PLAN.md charter resolves to the date-stripped directory name; an
        # undated file keeps its stem; an undated charter keeps the
        # directory name.
        self.assertEqual(
            MODULE._plan_session_slug(Path("docs/history/plans/2026-10-19-feature.md")),
            "feature",
        )
        self.assertEqual(
            MODULE._plan_session_slug(Path("docs/history/plans/feature.md")), "feature"
        )
        self.assertEqual(
            MODULE._plan_session_slug(
                Path("docs/history/plans/2026-10-19-dirplan/PLAN.md")
            ),
            "dirplan",
        )
        self.assertEqual(
            MODULE._plan_session_slug(Path("docs/history/plans/plain/PLAN.md")), "plain"
        )


class SkillSlugContractTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] The skill-text side of the canonical
    <PLAN_SLUG> rule (plan gate-removal-closeout-accounting Task 1):
    execute-plan's bootstrap and done's gate invocation agree on the
    date-stripped directory slug and the PLAN.md charter operand, and the
    agent log guide resolves <PLAN_SLUG> by linking the canonical
    definition instead of restating a filename-only rule."""

    REPO_ROOT = SCRIPT_PATH.parent.parent

    def _read(self, rel: str) -> str:
        return (self.REPO_ROOT / rel).read_text(encoding="utf-8")

    def test_execute_plan_defines_canonical_slug_rule(self):
        skill = self._read("agents/skills/execute-plan/SKILL.md")
        # Dated-file arm: strip the leading date and the .md extension.
        self.assertIn("strip the leading date and the `.md` extension", skill)
        # Dated-directory arm: the PLAN.md charter, date-stripped directory.
        self.assertIn("dated plan directory", skill)
        self.assertIn("`PLAN.md` charter", skill)
        self.assertIn("from the directory name after stripping the leading date", skill)
        # Explicit override and legacy skip remain distinct.
        self.assertIn("--migration-manifest", skill)
        self.assertIn("legacy skip", skill)

    def test_execute_plan_bootstrap_and_done_invocation_agree(self):
        skill = self._read("agents/skills/execute-plan/SKILL.md")
        done_text = self._read("agents/skills/done/SKILL.md")
        # Both surfaces carry the prescribed gate invocation operand shape
        # and the charter-file resolution for a dated directory plan.
        self.assertIn(
            "python3 scripts/worktree_closeout_migrate.py gate-removal "
            "--plan <plan> --target <primary> --worktree <worktree>",
            done_text,
        )
        self.assertIn("PLAN.md", done_text)
        self.assertIn("date-stripped", done_text)
        self.assertIn("per the execute-plan canonical session-slug rule", done_text)
        self.assertIn("`PLAN.md` charter", skill)
        # The done invocation names the same canonical rule execute-plan
        # defines, so both producers and the consumer derive one slug.
        self.assertIn("PLAN_SLUG", skill)
        self.assertIn("PLAN_SLUG", done_text)

    def test_agent_logs_guide_resolves_slug_and_links_canonical_definition(self):
        guide = self._read("agents/skills/execute-plan/agent-logs.md")
        # The filename-only restatement is gone; the guide derives <PLAN_SLUG>
        # through the canonical rule and names its home.
        self.assertNotIn("kebab-case slug from the plan filename", guide)
        self.assertIn("canonical", guide)
        self.assertIn("Step 0.4", guide)
        self.assertIn("SKILL.md", guide)
        self.assertIn("PLAN.md", guide)
        self.assertIn("strip the leading date", guide)


    def test_operator_closeout_and_retained_branch_reporting_are_pinned(self):
        # Plan gate-removal-closeout-accounting Task 2: done carries the
        # operator branch closeout (quiesce, inventory, no-force removal,
        # expected-OID delete) as the only sanctioned deletion, and
        # execute-plan carries the retained-branch reporting duty into the
        # final closeout.
        done_text = self._read("agents/skills/done/SKILL.md")
        self.assertIn("Operator branch closeout", done_text)
        self.assertIn("expected-OID compare", done_text)
        self.assertIn("branch-only", done_text)
        self.assertIn("retains the worktree and the ref", done_text)
        skill = self._read("agents/skills/execute-plan/SKILL.md")
        self.assertIn("Retained-branch reporting", skill)
        self.assertIn("branch-disposition", skill)


# Plan: docs/history/plans/2026-10-29-done-gate-report-retention.md, Task 3.
# The baseline-less scoped-transfer arm routes through cmd_migrate: the
# explicitly captured scoped inventory supplies the expected transfer set
# without a baseline or a dirs requirement; every expected item is validated
# one-for-one inside the existing merge-lock transaction (a missing source or
# a digest mismatch fails the transaction and appends no verified row); an
# empty inventory appends nothing; and the whole copy/check/append span
# shares the worktree-closeout-migrate merge lock with the done-session
# sweep, so no manifest comes to cite a missing report in either race order.
# --------------------------------------------------------------------------- #
class ScopedInventoryMigrateTest(unittest.TestCase):
    """Fixture style: the MigrateMergeLockTest pattern (a fixture repo with a
    facts block and a repo-local done-lock copy, the hermetic lock env pinned
    into this process for in-process runs and passed explicitly to every
    subprocess, inherited GIT_ variables cleared for subprocess runs)."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-scoped-inv-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        env = os.environ.copy()
        env.update(self.GIT_IDENTITY)
        subprocess.run(["git", "-C", str(self.primary), "init", "-q"], capture_output=True, env=env, check=True)
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\ntmp_dir = \"docs/tmp/\"\nmetrics_dir = \".ai-playbook/metrics/\"\nreview_certs_dir = \".ai-playbook/review-certs/\"\n```\n",
        )
        (self.primary / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(DONE_LOCK_SCRIPT_PATH, self.primary / "scripts" / "done-lock.sh")
        subprocess.run(["git", "-C", str(self.primary), "add", "-A"], capture_output=True, env=env, check=True)
        subprocess.run(["git", "-C", str(self.primary), "commit", "-q", "-m", "init: fixture repo"], capture_output=True, env=env, check=True)
        self.merge_lock_root = self.root / "merge-locks"
        # In-process runs (MODULE.main) resolve the lock env from this
        # process's environment: pin it hermetically for the whole class.
        pins = _hermetic_lock_env(self.root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _write_skeleton(self, branch: str, source: str) -> Path:
        """The zero/multi-plan producer's migrate-shape skeleton (the shape
        ZeroPlanMigrateSkeletonProducerTest pins): a branch record plus an
        empty migrated list, named for the run beside the skip record."""
        manifest = self.root / "worktree-migrate-baseline-run-z3-manifest.json"
        _write(
            manifest,
            json.dumps(
                {"branch": [{"branch": branch, "source": source}], "migrated": []},
                indent=2,
            ).encode("utf-8")
            + b"\n",
        )
        return manifest

    def _write_inventory(self, rels: list[str]) -> Path:
        inventory = self.root / "scoped-inventory.json"
        _write(
            inventory,
            (json.dumps({"files": rels}, indent=2) + "\n").encode("utf-8"),
        )
        return inventory

    def _run_scoped(
        self, source: Path, inventory: Path, manifest: Path, **extra: str
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH), "migrate",
                "--inventory", str(inventory),
                "--source", str(source),
                "--target", str(self.primary),
                "--manifest", str(manifest),
                "--suffix", "z3",
            ],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root, **extra),
        )

    def _verified_destinations(self, manifest: Path) -> list[str]:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return [
            entry["destination"]
            for section in ("migrated", "renamed")
            for entry in data.get(section, [])
            if isinstance(entry, dict) and entry.get("verified") and entry.get("destination")
        ]

    def test_scoped_inventory_migrates_selected_items_and_appends_verified_rows(self):
        """[class: REPOSITORY_TEST] Given the scoped inventory of two sources,
        expects the migrate invocation (no baseline, no dirs) to copy exactly
        the selected items, to append one `verified: true` migrated row per
        item with the {source, destination, verified} field set plus the run
        attribution stamp (record_index 1: the skeleton carries one branch
        record, so the incoming record takes index 1), to leave an unselected
        source untransferred, and to append the source-binding branch
        record."""
        source = self.root / "source"
        review_rel = ".ai-playbook/reviews/2026-10-30-scoped-r1.md"
        report_rel = "docs/tmp/done-session/gate-reports/run-z3-docs-tmp-sweep-full.txt"
        unselected_rel = "docs/tmp/scratch/unselected.txt"
        _write(source / review_rel, b"review record\n")
        _write(source / report_rel, b"gate report rows\n")
        _write(source / unselected_rel, b"not selected\n")
        primary = self.primary.resolve()
        skeleton = self._write_skeleton("wt-scoped-a", str(source))
        inventory = self._write_inventory([review_rel, report_rel])

        proc = self._run_scoped(source, inventory, skeleton)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((primary / review_rel).is_file(), "selected review record copied")
        self.assertTrue((primary / report_rel).is_file(), "selected gate report copied")
        self.assertFalse(
            (primary / unselected_rel).exists(),
            "a source not selected into the inventory stays untransferred",
        )
        data = json.loads(skeleton.read_text(encoding="utf-8"))
        migrated = data["migrated"]
        self.assertEqual(len(migrated), 2, data)
        by_source = {entry["source"]: entry for entry in migrated}
        for rel in (review_rel, report_rel):
            entry = by_source[rel]
            self.assertEqual(entry["destination"], str(primary / rel))
            self.assertTrue(entry["verified"])
            # The plain migrated-row field set plus the run attribution
            # stamp (plan 2026-11-01-gate-removal-inherited-manifest-rows):
            # the append carries a branch section, so every appended row is
            # stamped with the incoming record's index (1, after the
            # producer's own record). The delivered_blob field is the
            # clobber guard's additive per-row capture (plan
            # 2026-11-02-closeout-migrate-clobber-guard-restore-arms); the
            # primary is a git target, so the sha is recorded.
            self.assertEqual(
                sorted(entry),
                ["delivered_blob", "destination", "record_index", "source", "verified"],
            )
            expected_blob = subprocess.run(
                ["git", "-C", str(primary), "hash-object", "--", rel],
                capture_output=True, text=True, check=True,
                env=_hermetic_lock_env(self.root),
            ).stdout.strip()
            self.assertEqual(
                entry["delivered_blob"], expected_blob,
                "the migrated row must carry the delivered blob sha",
            )
            self.assertEqual(entry["record_index"], 1)
        self.assertEqual(data.get("failed"), [])
        self.assertEqual(data.get("renamed"), [])
        self.assertEqual(data.get("skipped"), [])
        # The transfer-time branch record appends beside the producer's,
        # stamped at the same incoming index.
        self.assertEqual(data["branch"][-1]["source"], str(source.resolve()))
        self.assertEqual(data["branch"][-1]["record_index"], 1)
        self.assertEqual(data["branch"][0].get("record_index"), None, "the producer's own record was stamped")

    def test_scoped_identical_transfer_records_delivered_blob(self):
        """[class: REPOSITORY_TEST] The scoped identical-transfer arm (the
        expected transfer already stands at the target with identical
        bytes) records the delivered blob too: the verified migrated row
        carries the delivered_blob sha of the bytes standing at the target
        (plan 2026-11-04-closeout-clobber-guard-review-residual-trio R10
        pins this previously unasserted capture site)."""
        source = self.root / "source"
        review_rel = ".ai-playbook/reviews/2026-10-30-scoped-identical.md"
        shared = b"identical transfer bytes\n"
        primary = self.primary.resolve()
        _write(source / review_rel, shared)
        _write(primary / review_rel, shared)
        skeleton = self._write_skeleton("wt-scoped-i", str(source))
        inventory = self._write_inventory([review_rel])

        proc = self._run_scoped(source, inventory, skeleton)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(skeleton.read_text(encoding="utf-8"))
        migrated = data["migrated"]
        self.assertEqual(len(migrated), 1, data)
        entry = migrated[0]
        self.assertEqual(entry["source"], review_rel)
        self.assertEqual(entry["destination"], str(primary / review_rel))
        self.assertTrue(entry["verified"])
        expected_blob = subprocess.run(
            ["git", "-C", str(primary), "hash-object", "--", review_rel],
            capture_output=True, text=True, check=True,
            env=_hermetic_lock_env(self.root),
        ).stdout.strip()
        self.assertEqual(
            entry["delivered_blob"], expected_blob,
            "the identical-transfer migrated row must carry the delivered "
            "blob sha of the bytes standing at the target",
        )
        self.assertEqual(
            (primary / review_rel).read_bytes(), shared,
            "the identical bytes at the target must not be rewritten",
        )

    def test_scoped_inventory_empty_appends_nothing(self):
        """[class: REPOSITORY_TEST] Given an empty scoped inventory, expects
        the migration to succeed while appending no content rows at all: the
        empty skeleton stays migrated-less (no protected destination), and no
        source file is copied behind the inventory's back."""
        source = self.root / "source"
        unselected_rel = "docs/tmp/done-session/gate-reports/run-empty-docs-tmp-sweep-full.txt"
        _write(source / unselected_rel, b"aged unselected\n")
        skeleton = self._write_skeleton("wt-scoped-e", str(source))
        inventory = self._write_inventory([])

        proc = self._run_scoped(source, inventory, skeleton)

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(skeleton.read_text(encoding="utf-8"))
        self.assertEqual(data["migrated"], [], "the empty skeleton creates no protected destination")
        for section in ("renamed", "replaced", "skipped", "failed"):
            self.assertEqual(data.get(section, []), [], data)
        self.assertFalse((self.primary.resolve() / unselected_rel).exists())

    def test_scoped_inventory_operand_exclusivity_stays_usage_class(self):
        """[class: REPOSITORY_TEST] Given both transfer operands, or neither,
        expects the argparse usage-error class (exit 2, no traceback): the
        scoped arm never silently coexists with, or substitutes for, a
        fabricated baseline operand."""
        source = self.root / "source"
        _write(source / ".ai-playbook/reviews/r.md", b"r\n")
        skeleton = self._write_skeleton("wt-scoped-x", str(source))
        inventory = self._write_inventory([".ai-playbook/reviews/r.md"])
        base = [
            sys.executable, str(SCRIPT_PATH), "migrate",
            "--source", str(source), "--target", str(self.primary),
            "--manifest", str(skeleton),
        ]
        both = subprocess.run(
            base + ["--baseline", str(self.root / "absent-baseline.json"), "--inventory", str(inventory)],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root),
        )
        self.assertEqual(both.returncode, 2, both.stdout + both.stderr)
        self.assertIn("not allowed with argument", both.stderr)
        self.assertNotIn("Traceback", both.stderr)
        neither = subprocess.run(
            base, capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root),
        )
        self.assertEqual(neither.returncode, 2, neither.stdout + neither.stderr)
        self.assertIn("required", neither.stderr)
        self.assertNotIn("Traceback", neither.stderr)

    def test_scoped_inventory_missing_source_fails_without_verified_row(self):
        """[class: REPOSITORY_TEST] Given an inventory naming one present and
        one absent source, expects the transaction to fail (exit 1) with the
        missing item recorded under `failed` (verified false, named on
        stderr) and no verified row for it: no expected source is silently
        omitted, while the present item still lands its verified row inside
        the same transaction."""
        source = self.root / "source"
        present_rel = ".ai-playbook/reviews/2026-10-30-present.md"
        missing_rel = "docs/tmp/done-session/gate-reports/run-miss-docs-tmp-sweep-full.txt"
        _write(source / present_rel, b"present bytes\n")
        primary = self.primary.resolve()
        skeleton = self._write_skeleton("wt-scoped-m", str(source))
        inventory = self._write_inventory([present_rel, missing_rel])

        proc = self._run_scoped(source, inventory, skeleton)

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(missing_rel, proc.stderr)
        self.assertTrue((primary / present_rel).is_file())
        self.assertFalse((primary / missing_rel).exists())
        data = json.loads(skeleton.read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["source"] for entry in data["migrated"]], [present_rel], data
        )
        self.assertEqual(len(data["failed"]), 1, data)
        failed = data["failed"][0]
        self.assertEqual(failed["source"], missing_rel)
        self.assertFalse(failed["verified"])
        self.assertEqual(failed["error"], "missing source")
        self.assertEqual(self._verified_destinations(skeleton), [str(primary / present_rel)])

    def test_scoped_inventory_digest_mismatch_fails_without_verified_row(self):
        """[class: REPOSITORY_TEST] Given a copied item whose digest
        verification fails (the suite's established _verify_copy tamper seam,
        the checksum-mismatch-after-copy path), expects the transaction to
        fail (exit 1) with the failed row carrying no verified mark and the
        merge lock released."""
        source = self.root / "source"
        report_rel = "docs/tmp/done-session/gate-reports/run-dm-docs-tmp-sweep-full.txt"
        _write(source / report_rel, b"gate report rows\n")
        skeleton = self._write_skeleton("wt-scoped-d", str(source))
        inventory = self._write_inventory([report_rel])
        captured = io.StringIO()

        def failing_verify(src: Path, dst: Path) -> bool:
            return False

        original_verify = MODULE._verify_copy
        MODULE._verify_copy = failing_verify
        try:
            with contextlib.redirect_stderr(captured):
                code = MODULE.main(
                    [
                        "migrate",
                        "--inventory", str(inventory),
                        "--source", str(source),
                        "--target", str(self.primary),
                        "--manifest", str(skeleton),
                        "--suffix", "z3",
                    ]
                )
        finally:
            MODULE._verify_copy = original_verify
        self.assertEqual(code, 1)
        self.assertIn("checksum mismatch after copy", captured.getvalue())
        data = json.loads(skeleton.read_text(encoding="utf-8"))
        self.assertEqual(data["migrated"], [], "no verified row for the mismatched item")
        self.assertEqual(data.get("renamed", []), [])
        self.assertEqual(len(data["failed"]), 1, data)
        self.assertEqual(data["failed"][0]["source"], report_rel)
        self.assertFalse(data["failed"][0]["verified"])
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the merge lock was not released")

    def test_scoped_publication_lands_inside_merge_lock_span(self):
        """[class: REPOSITORY_TEST] The structural race-order guarantee: the
        scoped arm's copy, digest check, and verified-row append all complete
        before the migrate arm's merge-lock release, so a concurrent sweep
        holding the same lock observes either no citation with no copy, or
        the citation with the report already present - never a manifest row
        citing a report the sweep just unlinked (the lock-span equivalent of
        both subprocess race orders, per the sweep suite's structural
        precedent)."""
        source = self.root / "source"
        report_rel = "docs/tmp/done-session/gate-reports/run-span-docs-tmp-sweep-full.txt"
        _write(source / report_rel, b"gate report rows\n")
        primary = self.primary.resolve()
        report_dst = primary / report_rel
        skeleton = self._write_skeleton("wt-scoped-s", str(source))
        inventory = self._write_inventory([report_rel])
        events: list[object] = []

        def row_present() -> bool:
            data = json.loads(skeleton.read_text(encoding="utf-8"))
            return any(
                entry.get("verified") and entry.get("destination") == str(report_dst)
                for entry in data.get("migrated", [])
            )

        real_acquire = MODULE._merge_lock_wait_acquire
        real_release = MODULE._migrate_merge_lock_release

        def fake_acquire(target, label, max_wait):
            events.append("acquire")
            return real_acquire(target, label, max_wait)

        def fake_release(target, exports, started):
            # The span discriminator: the copied report and the verified
            # manifest row must already exist while the lock is still held.
            events.append(("release", report_dst.exists(), row_present()))
            real_release(target, exports, started)

        MODULE._merge_lock_wait_acquire = fake_acquire
        MODULE._migrate_merge_lock_release = fake_release
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                code = MODULE.main(
                    [
                        "migrate",
                        "--inventory", str(inventory),
                        "--source", str(source),
                        "--target", str(self.primary),
                        "--manifest", str(skeleton),
                        "--suffix", "z3",
                    ]
                )
        finally:
            MODULE._merge_lock_wait_acquire = real_acquire
            MODULE._migrate_merge_lock_release = real_release
        self.assertEqual(code, 0)
        self.assertEqual(len(events), 2, events)
        self.assertEqual(events[0], "acquire")
        release_event = events[1]
        assert isinstance(release_event, tuple)
        self.assertEqual(
            release_event,
            ("release", True, True),
            "copy and verified append must land before the merge-lock release",
        )


class ScopedPublicationSweepRaceTest(unittest.TestCase):
    """Real two-process race fixtures for the scoped publisher versus the
    done-session sweep (plan 2026-10-29-done-gate-report-retention Task 3):
    a primary fixture repo with the five-key facts block, a registered linked
    worktree as the scoped source, run-start markers anchoring the session
    window, aged gate reports, and the done-session sweep gate driven
    in-process through done_sweep_gates_lib with the runtime/user-facts pins
    the sweep suite's sweep_env carries."""

    GIT_IDENTITY = ScopedInventoryMigrateTest.GIT_IDENTITY

    ANCHOR_OFFSET_S = 3600

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-scoped-race-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        env = os.environ.copy()
        env.update(self.GIT_IDENTITY)
        subprocess.run(["git", "-C", str(self.primary), "init", "-q", "-b", "main"], capture_output=True, env=env, check=True)
        _write(self.primary / ".gitignore", b"docs/\n")
        _write(
            self.primary / ".ai-playbook/facts.md",
            (
                "```toml\n"
                'plans_dir = "docs/history/plans/"\n'
                'plans_completed_dir = "docs/history/plans/completed/"\n'
                'backlog_dir = "docs/history/backlog/"\n'
                'reviews_dir = ".ai-playbook/reviews/"\n'
                'tmp_dir = "docs/tmp/"\n'
                'base_branch = "main"\n'
                "```\n"
            ).encode("utf-8"),
        )
        (self.primary / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(DONE_LOCK_SCRIPT_PATH, self.primary / "scripts" / "done-lock.sh")
        subprocess.run(["git", "-C", str(self.primary), "add", "-A"], capture_output=True, env=env, check=True)
        subprocess.run(["git", "-C", str(self.primary), "commit", "-q", "-m", "init: fixture repo"], capture_output=True, env=env, check=True)
        self.worktree = self.root / "wt-src"
        added = subprocess.run(
            ["git", "-C", str(self.primary), "worktree", "add", str(self.worktree), "-b", "wt-scoped-race"],
            capture_output=True, env=env, check=True,
        )
        self.assertIsNotNone(added)
        # Session window: the previous-run anchor and the current-run marker.
        now = int(time.time())
        self.anchor_epoch = now - self.ANCHOR_OFFSET_S
        self._make_run_marker(now - self.ANCHOR_OFFSET_S)
        self._make_run_marker(now)
        # The aged gate report the scoped publisher will transfer, aged in the
        # source worktree (copy2 preserves the mtime, so the published copy
        # arrives aged), plus an equally aged unreferenced report at primary.
        self.report_rel = "docs/tmp/done-session/gate-reports/run-race-docs-tmp-sweep-full.txt"
        self._aged(self.worktree / self.report_rel)
        self.loose = self._aged(self.primary / self.report_rel.replace("run-race", "run-loose"))
        self.cited_dst = self.primary.resolve() / self.report_rel
        # The zero/multi-plan producer's skeleton beside the skip record home.
        self.manifest = (
            self.primary
            / "docs/tmp/done-session/worktree-migrate-baseline-run-race-manifest.json"
        )
        _write(
            self.manifest,
            (
                json.dumps(
                    {
                        "branch": [{"branch": "wt-scoped-race", "source": str(self.worktree.resolve())}],
                        "migrated": [],
                    },
                    indent=2,
                )
                + "\n"
            ).encode("utf-8"),
        )
        self.inventory = self.root / "scoped-inventory.json"
        _write(
            self.inventory,
            (json.dumps({"files": [self.report_rel]}) + "\n").encode("utf-8"),
        )
        # Hermetic lock env for every in-process resolve and subprocess.
        pins = _hermetic_lock_env(self.root)
        self._saved_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        # The sweep-lib pins (the sweep_env inventory): runtime home, user
        # facts, ambient Git selectors and repo-root overrides cleared.
        for key, value in (
            ("DONE_SWEEP_RUNTIME_HOME", str(self.root / "runtime-home")),
            ("DONE_SWEEP_USER_FACTS", str(self.root / "user-facts.md")),
            ("XDG_CONFIG_HOME", str(self.root / "xdg-config-home")),
            ("GIT_CONFIG_NOSYSTEM", "1"),
        ):
            self._saved_env[key] = os.environ.get(key)
            os.environ[key] = value
        (self.root / "runtime-home").mkdir(exist_ok=True)
        (self.root / "user-facts.md").write_text("# fixture user facts\n", encoding="utf-8")
        (self.root / "xdg-config-home").mkdir(exist_ok=True)
        for key in ("DONE_SWEEP_REPO_ROOT",):
            self._saved_env[key] = os.environ.get(key)
            os.environ.pop(key, None)
        for key in tuple(os.environ):
            if key.startswith("GIT_"):
                self._saved_env.setdefault(key, os.environ[key])
                del os.environ[key]
        self.addCleanup(self._restore_env)

    def _restore_env(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _make_run_marker(self, epoch: int) -> Path:
        marker = self.primary / "docs/tmp/done-session" / (
            "run-start-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(epoch))
        )
        _write(marker, f"{epoch} {self.primary.resolve()} {os.getpid()}\n".encode("utf-8"))
        return marker

    def _aged(self, path: Path) -> Path:
        _write(path, b"gate report rows\n")
        stale = self.anchor_epoch - 3600
        os.utime(path, (stale, stale))
        return path

    def _run_scoped(self, **extra: str) -> subprocess.Popen:
        env = _hermetic_lock_env(self.root, **extra)
        return subprocess.Popen(
            [
                sys.executable, str(SCRIPT_PATH), "migrate",
                "--inventory", str(self.inventory),
                "--source", str(self.worktree),
                "--target", str(self.primary),
                "--manifest", str(self.manifest),
                "--suffix", "race",
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            cwd=str(self.root), env=env,
        )

    def _run_scoped_sync(self, **extra: str) -> subprocess.CompletedProcess:
        proc = self._run_scoped(**extra)
        out, err = proc.communicate(timeout=120)
        return subprocess.CompletedProcess(proc.args, proc.returncode or 0, out, err)

    def _run_sweep(self):
        import done_sweep_gates_lib as sweep_lib

        ctx = sweep_lib.GateContext.discover(self.primary)
        return sweep_lib.run_gate("docs-tmp-sweep", ctx)

    def _acquire_foreign_hold(self, label: str, holder_pid: int) -> dict[str, str]:
        acquired = subprocess.run(
            ["bash", str(self.primary / "scripts" / "done-lock.sh"), "merge-acquire", "--label", label],
            capture_output=True, text=True, cwd=str(self.primary),
            env=_hermetic_lock_env(self.root, MERGE_LOCK_HOLDER_PID=str(holder_pid)),
        )
        self.assertEqual(acquired.returncode, 0, acquired.stderr)
        exports: dict[str, str] = {}
        for line in acquired.stdout.splitlines():
            for name in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
                prefix = f"export {name}="
                if line.startswith(prefix):
                    exports[name] = line[len(prefix):]
        self.assertIn("MERGE_LOCK_DIR", exports)
        self.assertIn("MERGE_LOCK_TOKEN", exports)
        return exports

    def _release_hold(self, exports: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(self.primary / "scripts" / "done-lock.sh"), "merge-release"],
            capture_output=True, text=True, cwd=str(self.primary),
            env=_hermetic_lock_env(self.root, **exports),
        )

    def _release_gate_wrapper(self) -> tuple[Path, Path]:
        """A fixture-owned DONE_LOCK_SCRIPT wrapper: every subcommand passes
        through to the real done-lock copy, except merge-release, which waits
        (bounded) for the sentinel file before delegating, so the publisher
        subprocess deterministically holds the lock while the test runs the
        concurrent sweep."""
        sentinel = self.root / "release-gate"
        wrapper = self.root / "release-gated-done-lock.sh"
        real = DONE_LOCK_SCRIPT_PATH
        wrapper.write_text(
            "#!/usr/bin/env bash\n"
            f'REAL={shlex.quote(str(real))}\n'
            'RELEASE_GATE=' + shlex.quote(str(sentinel)) + '\n'
            'if [ "$1" = "merge-release" ]; then\n'
            '  for _ in $(seq 1 600); do\n'
            '    [ -e "$RELEASE_GATE" ] && break\n'
            '    sleep 0.1\n'
            '  done\n'
            'fi\n'
            'exec bash "$REAL" "$@"\n',
            encoding="utf-8",
        )
        return wrapper, sentinel

    def test_scoped_publisher_arriving_second_refuses_then_succeeds(self):
        """[class: REPOSITORY_TEST] Race order one (the sweep's lock span goes
        first): given the merge lock held by the concurrent sweep, expects
        the scoped publisher's bounded wait to refuse with nothing copied and
        no row appended, and the same invocation after release to publish the
        verified row - the manifest never cites an absent report."""
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        exports = self._acquire_foreign_hold("docs-tmp-sweep", holder.pid)
        try:
            refused = self._run_scoped_sync(DOCS_SYNC_MERGE_MAX_WAIT="2")
        finally:
            released = self._release_hold(exports)
        self.assertEqual(released.returncode, 0, released.stderr)
        self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
        self.assertIn("timed out after 2s", refused.stderr)
        self.assertFalse(self.cited_dst.exists(), "a copy ran while the sweep's lock span held")
        self.assertEqual(
            json.loads(self.manifest.read_text(encoding="utf-8"))["migrated"],
            [],
            "no row was appended while the sweep's lock span held",
        )

        after = self._run_scoped_sync()

        self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
        self.assertTrue(self.cited_dst.exists())
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["destination"] for entry in data["migrated"]],
            [str(self.cited_dst)],
            data,
        )
        self.assertTrue(data["migrated"][0]["verified"])

    def test_scoped_publisher_holds_lock_while_sweep_arrives_then_sweep_retains(self):
        """[class: REPOSITORY_TEST] Race order two (the publisher's lock span
        goes first, through a real subprocess held open by a fixture-owned
        release gate): given the publisher mid-transaction, expects the
        concurrent sweep's lookup/unlink to refuse the lock and prune
        nothing; after the publisher releases, a later sweep retains the
        aged cited report (its verified row landed inside the transaction)
        while the unreferenced aged report is pruned, so no manifest cites a
        missing report."""
        import done_sweep_gates_lib as sweep_lib  # noqa: local import keeps collection light

        wrapper, sentinel = self._release_gate_wrapper()
        proc = self._run_scoped(DONE_LOCK_SCRIPT=str(wrapper))
        self.addCleanup(self._terminate_publisher, proc)
        try:
            deadline = time.time() + 30
            while not self.cited_dst.exists() and time.time() < deadline:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
            self.assertTrue(
                self.cited_dst.exists(),
                f"the publisher never reached its copy leg: {proc.poll()}",
            )
            self.assertTrue(proc.poll() is None, "the publisher released before the gate")

            # The concurrent sweep arrives inside the publisher's lock span.
            during = self._run_sweep()
        finally:
            sentinel.touch()
        out, err = proc.communicate(timeout=120)
        self.assertEqual(proc.returncode, 0, out + err)

        self.assertEqual(during.rc, 0, during.message)
        self.assertTrue(
            any("merge lock not acquired" in warning for warning in during.warnings),
            during.warnings,
        )
        self.assertTrue(self.loose.exists(), "no pruning while the publisher's span held")
        self.assertTrue(self.cited_dst.exists())

        # After the transaction landed, the sweep retains the cited aged
        # report and prunes the unreferenced one: no manifest cites a missing
        # report.
        after = self._run_sweep()

        self.assertEqual(after.rc, 0, after.message)
        self.assertFalse(
            any("merge lock not acquired" in warning for warning in after.warnings),
            after.warnings,
        )
        self.assertTrue(self.cited_dst.exists(), "the verified citation retains its report")
        self.assertFalse(self.loose.exists(), "the unreferenced aged report still prunes")
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            [entry["destination"] for entry in data["migrated"]],
            [str(self.cited_dst)],
            "the manifest's only verified citation names a report on disk",
        )

    def _terminate_publisher(self, proc: subprocess.Popen) -> None:
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=30)


class ScopedArmDocContractTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] The skill-text side of Task 3: the
    worktree-first standard's baseline-less scoped arm routes the transfer
    through the closeout migration's scoped `--inventory` invocation, and the
    manual copy-and-append procedure is gone."""

    REPO_ROOT = SCRIPT_PATH.parent.parent

    def _read(self) -> str:
        return (self.REPO_ROOT / "agents/skills/execute-plan/worktree-first.md").read_text(
            encoding="utf-8"
        )

    def test_scoped_arm_routes_through_migrate_inventory(self):
        text = self._read()
        self.assertIn("--inventory", text)
        self.assertIn("scoped inventory", text)
        self.assertIn("merge-lock transaction", text)
        # The manual procedure's fingerprints are gone.
        self.assertNotIn("copy each to primary, verify each digest", text)
        self.assertNotIn("each verified transfer also appends its migrated entry", text)
        # The zero/multi-plan route passes the producer skeleton as --manifest.
        self.assertIn("worktree-migrate-baseline-<run id>-manifest.json", text)


class HelpCatalogTest(unittest.TestCase):
    """Plan 2026-10-24-closeout-helper-command-discovery Task 1: the generic
    --help catalog names every command main() routes, and every direct
    command --help stays a successful usage exit through its existing
    parser; operational dispatch and exit classes are pinned elsewhere and
    are not restated here."""

    COMMANDS = (
        "capture",
        "migrate",
        "boundary-mirror",
        "verify-records",
        "copy-cited-records",
        "check-stranded-pointers",
        "gate-removal",
        "owned-files-clean",
        "sweep",
    )

    def _run_help(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True, text=True,
        )

    def test_generic_help_lists_all_nine_commands(self):
        proc = self._run_help("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn(
            "{capture,migrate,boundary-mirror,verify-records,copy-cited-records,check-stranded-pointers,gate-removal,owned-files-clean,sweep}",
            proc.stdout,
        )
        for command in self.COMMANDS:
            self.assertIn(command, proc.stdout)

    def test_all_nine_direct_help_routes_exit_zero_with_usage(self):
        for command in self.COMMANDS:
            with self.subTest(command=command):
                proc = self._run_help(command, "--help")
                self.assertEqual(proc.returncode, 0)
                self.assertIn("usage:", proc.stdout)

    def test_separator_escaped_catalog_token_keeps_exit_two(self):
        # Review r1 fold: `-- <catalog token>` bypasses main()'s tokens[0]
        # dispatch and reaches the generic parser, where the help-only entry
        # has no handler; the legacy argparse exit class (2, usage on
        # stderr, no traceback) is pinned.
        for token in ("gate-removal", "owned-files-clean", "sweep"):
            with self.subTest(token=token):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT_PATH), "--", token],
                    capture_output=True, text=True,
                )
                self.assertEqual(proc.returncode, 2)
                self.assertIn("invalid choice", proc.stderr)
                self.assertIn("usage:", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)

    def test_sweep_usage_keeps_doubled_token(self):
        # Standing constraint: the doubled `sweep` usage token is left for a
        # separate scope decision; this pins the spelling so the help-catalog
        # change cannot silently alter it.
        proc = self._run_help("sweep", "--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("usage: worktree_closeout_migrate.py sweep sweep", proc.stdout)


class NoCharterFixture:
    """Shared git fixture for the no-charter gate-removal arm (plan
    2026-10-28-plan-authoring-stand-down-before-charter Task 1): a primary
    checkout plus a pre-plan authoring worktree provisioned under the
    Worktree-first pre-plan authoring arm (worktree
    <worktree-root>/<claim-file-stem> on branch authoring/<claim-file-stem>),
    the session's authoring claim file, the frozen PLAN-PROMPTS entry, and
    the done-run manifest binding the expected plan path and start_commit.
    Carries only helpers, never test methods, so each concrete class
    collects its own tests."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    CLAIM_BASENAME = "2026-10-26-no-charter-demo.md"
    CLAIM_STEM = "2026-10-26-no-charter-demo"
    SLUG = "no-charter-demo"
    ITEM = "docs/history/backlog/2026-10-26-no-charter-demo.md"
    PLAN_REL = "docs/history/plans/2026-10-28-no-charter-demo.md"
    SESSION_ID = "0f1e2d3c-4b5a-6978-8765-4321abcdef01"
    RUN_ID = "20261026T080000Z-nocharterfixture"
    MARKER = "run-start-20261026T080000Z"

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wrmg-nocharter-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.primary = self.root / "proj"
        self.primary.mkdir(parents=True)
        self._git(self.primary, "init", "-q", "-b", "main")
        # The producer repo's wholesale-ignored surfaces (the real
        # .gitignore): done-session records live under docs/tmp/ and the
        # whole .ai-playbook/ home is ignored, so a worktree-dispatched
        # run's own records never fake worktree dirtiness and the facts
        # file is an untracked-but-present provision, not a tracked one.
        _write(self.primary / ".gitignore", b"/docs/tmp/\n/.ai-playbook/\n")
        facts_bytes = (
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\n"
            b"tmp_dir = \"docs/tmp/\"\n"
            b"metrics_dir = \".ai-playbook/metrics/\"\n"
            b"review_certs_dir = \".ai-playbook/review-certs/\"\n"
            b"plans_dir = \"docs/history/plans/\"\n"
            b"backlog_dir = \"docs/history/backlog/\"\n```\n"
        )
        _write(self.primary / ".ai-playbook/facts.md", facts_bytes)
        self._commit_all(self.primary, "init: fixture repo")
        self.branch = f"authoring/{self.CLAIM_STEM}"
        # The Worktree-first pre-plan authoring arm's placement: the worktree
        # directory is the claim-file stem, the branch is authoring/ + stem.
        self.worktree = self.root / self.CLAIM_STEM
        self._git(
            self.primary, "worktree", "add", "-q", "-b", self.branch, str(self.worktree)
        )
        # The arm provisions the (ignored) facts copy worktree-side; the
        # worktree checkout stays clean with it on disk.
        _write(self.worktree / ".ai-playbook/facts.md", facts_bytes)
        # The transfer-in provision (r2 F1): the Worktree-first transfer-in
        # copies the primary reviews and review-certs homes into the fresh
        # worktree (cp -R semantics, worktree-first.md Transfer-in
        # implementation), so a pre-plan staging home starts as byte-identical
        # mirrors of the primary records. A prior run's record and its seal
        # cert ride both sides, so the clean cases exercise the real
        # provisioning shape, never an empty staging home.
        self.prior_record_rel = (
            ".ai-playbook/reviews/2026-10-01-plan-review-prior-r1.md"
        )
        prior_bytes = b"prior run's review record\n"
        _write(self.primary / self.prior_record_rel, prior_bytes)
        _write(self.worktree / self.prior_record_rel, prior_bytes)
        self.prior_seal_rel = ".ai-playbook/review-certs/2026-10-01-plan-review-prior.md"
        seal_bytes = b"prior run's certification seal\n"
        _write(self.primary / self.prior_seal_rel, seal_bytes)
        _write(self.worktree / self.prior_seal_rel, seal_bytes)
        self.start_commit = self._git(
            self.primary, "rev-parse", self.branch
        ).stdout.strip()

    def _git(self, repo: Path, *args: str, check: bool = True):
        env = _hermetic_git_env(self.root, **self.GIT_IDENTITY)
        proc = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env
        )
        if check and proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc

    def _commit_all(self, repo: Path, message: str) -> None:
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-q", "-m", message)

    def _branch_oid(self, branch: str) -> str:
        return self._git(self.primary, "rev-parse", branch).stdout.strip()

    def _claim_path(self) -> Path:
        return self.primary / "docs/tmp/authoring-claims" / self.CLAIM_BASENAME

    def _plan_abs(self) -> Path:
        # The expected plan file: it does NOT exist (the no-charter arm's
        # entry premise); the path is what done setup declared as the run's
        # owned plan before the first plan-file write.
        return self.primary / self.PLAN_REL

    def _seed_claim(self, text: str | None = None) -> Path:
        claim = self._claim_path()
        if text is None:
            text = (
                f"session: {self.SESSION_ID}\n"
                f"item: {self.ITEM}\n"
                "created: 2026-10-26T08:00:00Z\n"
                "updated: 2026-10-26T08:00:00Z\n"
            )
        _write(claim, text.encode("utf-8"))
        return claim

    def _seed_prompt_log(self, entry_body: str | None = None) -> Path:
        log = self.primary / "docs/history/backlog/PLAN-PROMPTS.md"
        if entry_body is None:
            entry_body = (
                f"## {self.SLUG}\n"
                "\n"
                "Added: 2026-10-26, test fixture\n"
                "\n"
                f"Frozen: docs/tmp/authoring-claims/{self.CLAIM_BASENAME} "
                "(2026-10-26)\n"
                "\n"
                "Origins:\n"
                f"- {self.ITEM}\n"
                "\n"
                "Urgency: low - fixture entry for the no-charter gate arm.\n"
            )
        _write(log, entry_body.encode("utf-8"))
        return log

    def _manifest_payload(self, **overrides) -> dict:
        payload = {
            "schema": 1,
            "run_id": self.RUN_ID,
            "marker": self.MARKER,
            "created_epoch": 1790000000.0,
            "repo_root": str(self.worktree),
            "pid": 1,
            "start_commit": self.start_commit,
            "start_porcelain": [],
            "owned_paths": [],
            "owned_plan_paths": [self.PLAN_REL],
            "owned_review_paths": [],
            "foreign_review_paths": [],
            "adopted_from": None,
            "complete": False,
        }
        payload.update(overrides)
        return payload

    def _write_manifest(self, payload: dict, run_id: str | None = None) -> Path:
        session_dir = self.primary / "docs/tmp/done-session"
        path = session_dir / f"run-manifest-{run_id or payload['run_id']}.json"
        _write(path, json.dumps(payload).encode("utf-8"))
        return path

    def _write_worktree_manifest(self, payload: dict, run_id: str | None = None) -> Path:
        # The worktree-side record (r1 F1): the producer's session dir
        # resolves from the dispatching checkout's toplevel, so a
        # worktree-dispatched done run writes under the worktree's
        # docs/tmp/done-session, never the primary's.
        session_dir = self.worktree / "docs/tmp/done-session"
        path = session_dir / f"run-manifest-{run_id or payload['run_id']}.json"
        _write(path, json.dumps(payload).encode("utf-8"))
        return path

    def _digest_root(self, root: Path) -> str:
        # The done producer's real repo_root shape: the 64-hex identity
        # digest of the dispatching checkout's toplevel. Derived through the
        # producer lib's own function so the fixture cannot drift from the
        # matcher's derivation (local import keeps collection light, the
        # suite idiom).
        import done_sweep_gates_lib as sweep_lib
        return sweep_lib._repo_root_digest(root.resolve())

    def _seed_clean(self) -> Path:
        """The full clean no-charter state: claim, frozen entry, one done-run
        manifest binding the expected plan and the untouched start commit."""
        self._seed_claim()
        self._seed_prompt_log()
        return self._write_manifest(self._manifest_payload())

    def _run_gate(self, *extra: str, claim: Path | None = "default") -> tuple[int, str, str]:
        operands = [
            "gate-removal",
            "--plan", str(self._plan_abs()),
            "--target", str(self.primary),
            "--worktree", str(self.worktree),
        ]
        if claim == "default":
            claim = self._claim_path()
        if claim is not None:
            operands += ["--authoring-claim", str(claim)]
        return _run_cli(*operands, *extra, cwd=self.worktree)


class NoCharterGateTest(NoCharterFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] The verified no-charter authoring stand-down
    arm (plan 2026-10-28-plan-authoring-stand-down-before-charter Task 1):
    cleanup is accepted only when the claim, the frozen prompt entry, the
    done-run manifest identity, the placement-derived branch, and the
    artifact accounting all agree, and every disagreement preserves the
    worktree and branch with a specific refusal."""

    def test_clean_case_passes_and_leaves_unrelated_shared_record_unchanged(self):
        # The required clean case: an unrelated record in the shared primary
        # reviews home must not block the run's cleanup, and the cleanup must
        # leave that record byte-unchanged while the run owns none. The
        # worktree staging homes hold the provisioned transfer-in mirrors
        # (r2 F1: the real provisioning shape, not an empty home), and the
        # pass verdict states what was actually verified (r2 F3).
        manifest_path = self._seed_clean()
        unrelated = (
            self.primary / ".ai-playbook/reviews/2026-10-01-plan-review-unrelated-r1.md"
        )
        _write(unrelated, b"unrelated prior run's record\n")
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"authoring claim {self.CLAIM_BASENAME}", out)
        self.assertIn(f"session {self.SESSION_ID}", out)
        self.assertIn(f"origin {self.ITEM}", out)
        self.assertIn(f"frozen PLAN-PROMPTS entry {self.SLUG}", out)
        self.assertIn(f"done-run manifest {self.RUN_ID}", out)
        self.assertIn(f"plan {self.PLAN_REL}", out)
        self.assertIn(f"start commit {self.start_commit}", out)
        self.assertIn("verified 0 owned record(s)", out)
        self.assertIn("byte-identical primary twin", out)
        removal_lines = [ln for ln in out.splitlines() if "git worktree remove" in ln]
        self.assertEqual(len(removal_lines), 1, out)
        self.assertIn(str(self.worktree), removal_lines[0])
        # The unrelated shared record is untouched by the gate's verdict.
        self.assertEqual(
            unrelated.read_bytes(), b"unrelated prior run's record\n",
            "the cleanup verdict disturbed an unrelated shared record",
        )
        # The provisioned transfer-in mirrors survive byte-unchanged: the
        # gate is read-only and the pass treats them as mirrors, not
        # run-owned artifacts.
        self.assertEqual(
            (self.worktree / self.prior_record_rel).read_bytes(),
            b"prior run's review record\n",
        )
        self.assertEqual(
            (self.worktree / self.prior_seal_rel).read_bytes(),
            b"prior run's certification seal\n",
        )
        # The manifest that bound the run survives the gate (read-only gate).
        self.assertTrue(manifest_path.is_file())
        # The branch is not deleted by the gate itself (operator work only).
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", self.branch, check=False).returncode,
            0,
        )

    def test_claim_operand_with_existing_plan_keeps_ordinary_empty_set_refusal(self):
        # An ordinary plan closeout is unchanged when the claim operand rides
        # along but the plan file exists: the ordinary gate's own checks run,
        # here the empty-owned-set refusal for a plan without citations.
        self._seed_clean()
        plan = self.primary / self.PLAN_REL
        _write(plan, b"# Plan\n\nNo review rounds.\n")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("empty owned set", out)
        self.assertNotIn("git worktree remove", out)

    def test_plan_absent_without_claim_operand_stays_tool_error(self):
        # The arm's entry is the explicit claim operand: a plan-absent gate
        # run without it keeps the legacy tool-error shape byte-for-byte.
        self._seed_clean()
        code, out, err = self._run_gate(claim=None)
        self.assertEqual(code, 3)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("plan file not found", err)

    def test_missing_claim_file_preserves(self):
        self._seed_clean()
        absent = self.primary / "docs/tmp/authoring-claims/gone.md"
        code, out, _err = self._run_gate(claim=absent)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused", out)
        self.assertIn("authoring claim", out)
        self.assertNotIn("git worktree remove", out)

    def test_claim_without_parseable_session_line_preserves(self):
        self._seed_prompt_log()
        self._write_manifest(self._manifest_payload())
        claim = self._seed_claim(
            text=(
                f"item: {self.ITEM}\n"
                "created: 2026-10-26T08:00:00Z\n"
                "updated: 2026-10-26T08:00:00Z\n"
            )
        )
        code, out, _err = self._run_gate(claim=claim)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("session", out)
        self.assertNotIn("git worktree remove", out)

    def test_unfrozen_prompt_entry_preserves(self):
        # The frozen prompt binding: an entry whose body never marks the
        # claim frozen cannot authorize the pre-plan cleanup.
        self._seed_claim()
        self._seed_prompt_log(
            entry_body=(
                f"## {self.SLUG}\n"
                "\n"
                "Added: 2026-10-26, test fixture\n"
                "\n"
                "Origins:\n"
                f"- {self.ITEM}\n"
                "\n"
                "Urgency: low - fixture entry, never frozen.\n"
            )
        )
        self._write_manifest(self._manifest_payload())
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("frozen", out)
        self.assertNotIn("git worktree remove", out)

    def test_frozen_entry_without_claim_origin_preserves(self):
        # The frozen entry must bind this claim's origin: an entry frozen for
        # a different item's claim is not this run's binding evidence.
        self._seed_claim()
        self._seed_prompt_log(
            entry_body=(
                f"## {self.SLUG}\n"
                "\n"
                "Added: 2026-10-26, test fixture\n"
                "\n"
                f"Frozen: docs/tmp/authoring-claims/{self.CLAIM_BASENAME} "
                "(2026-10-26)\n"
                "\n"
                "Origins:\n"
                "- docs/history/backlog/2026-10-26-some-other-item.md\n"
                "\n"
                "Urgency: low - fixture entry frozen for another origin.\n"
            )
        )
        self._write_manifest(self._manifest_payload())
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused", out)
        self.assertIn("origin", out)
        self.assertNotIn("git worktree remove", out)

    def test_missing_done_run_manifest_preserves(self):
        self._seed_claim()
        self._seed_prompt_log()
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("done-run manifest", out)
        self.assertNotIn("git worktree remove", out)

    def test_manifest_naming_other_plan_preserves(self):
        # A done-run manifest whose owned plan is a different path is not
        # this run's binding: the expected-plan identity fails closed.
        self._seed_claim()
        self._seed_prompt_log()
        self._write_manifest(
            self._manifest_payload(
                owned_plan_paths=["docs/history/plans/2026-10-28-other-demo.md"]
            )
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertNotIn("git worktree remove", out)

    def test_two_manifests_disagreeing_on_start_commit_preserve(self):
        # Ambiguous identity: two manifests naming the expected plan with
        # different start commits cannot bind one run; the resources stay.
        self._seed_claim()
        self._seed_prompt_log()
        self._write_manifest(self._manifest_payload())
        self._write_manifest(
            self._manifest_payload(
                run_id=self.RUN_ID + "-b",
                marker=self.MARKER + "-b",
                created_epoch=1790000900.0,
                start_commit="0" * 40,
            ),
            run_id=self.RUN_ID + "-b",
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused", out)
        self.assertNotIn("git worktree remove", out)
        # Both resources stay registered and on disk.
        self.assertTrue(self.worktree.is_dir())
        names = [
            entry["branch"]
            for entry in MODULE._parse_worktree_entries(self.primary)
            if Path(entry["path"]).resolve() == self.worktree.resolve()
        ]
        self.assertEqual(names, [self.branch])

    def test_branch_past_start_commit_preserves(self):
        # Any commit landing on the authoring branch after setup voids the
        # start-commit identity: the run's content is not provably empty.
        self._seed_clean()
        _write(self.worktree / "feature.txt", b"work\n")
        self._commit_all(self.worktree, "work: authoring residue")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("start commit", out)
        self.assertNotIn("git worktree remove", out)

    def test_dirty_worktree_preserves(self):
        self._seed_clean()
        _write(self.worktree / "scratch.md", b"draft\n")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused", out)
        self.assertNotIn("git worktree remove", out)

    def test_manifest_owned_review_record_preserves(self):
        # Manifest ownership says the run owns a review record: zero-owned is
        # not proven and the staging record's only copy may live worktree-side.
        self._seed_claim()
        self._seed_prompt_log()
        self._write_manifest(
            self._manifest_payload(
                owned_review_paths=[
                    ".ai-playbook/reviews/2026-10-26-plan-review-no-charter-demo-r1.md"
                ]
            )
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("review record", out)
        self.assertNotIn("git worktree remove", out)

    def test_worktree_staging_review_record_preserves(self):
        # Actual run artifacts (r2 F1): a review record in the worktree's
        # staging reviews home with NO byte-identical twin under the primary
        # reviews home is not a provisioned transfer-in mirror - it is
        # run-created or drifted state the removal would destroy unaccounted.
        self._seed_clean()
        _write(
            self.worktree / ".ai-playbook/reviews/2026-10-26-plan-review-no-charter-demo-r1.md",
            b"staging record\n",
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("refused", out)
        self.assertIn("reviews", out)
        self.assertIn("byte-identical twin", out)
        self.assertNotIn("git worktree remove", out)

    def test_staging_record_differing_from_primary_twin_preserves(self):
        # r2 F1, the drifted-mirror half: a staging record whose primary twin
        # exists but carries different bytes is not a provisioned mirror (the
        # worktree copy is not provably the transfer-in copy), so the run
        # refuses with preservation instead of destroying the delta.
        self._seed_clean()
        _write(self.primary / self.prior_record_rel, b"primary bytes moved on\n")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("byte-identical twin", out)
        self.assertNotIn("git worktree remove", out)

    def test_staging_seal_record_without_primary_twin_preserves(self):
        # r2 F1, the review-certs seal copy: the same transfer-in contract
        # copies the seal home into the worktree, so the twin-aware scan
        # covers it too; a seal record with no primary twin refuses with
        # preservation, while the provisioned seal mirror passes in the
        # clean cases.
        self._seed_clean()
        _write(
            self.worktree / (
                ".ai-playbook/review-certs/"
                "2026-10-26-plan-review-no-charter-demo.md"
            ),
            b"run-created seal record\n",
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("review-certs", out)
        self.assertIn("byte-identical twin", out)
        self.assertNotIn("git worktree remove", out)

    def test_target_facts_without_seal_key_with_staging_seal_records_preserves(self):
        # r2 F1: with staging seal records present, an unresolvable primary
        # twin home cannot prove the transfer-in mirrors, so the run refuses
        # instead of scanning against nothing.
        _write(
            self.primary / ".ai-playbook/facts.md",
            b"```toml\nreviews_dir = \".ai-playbook/reviews/\"\n"
            b"tmp_dir = \"docs/tmp/\"\n"
            b"metrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        self._seed_clean()
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("cannot resolve review_certs_dir", out)
        self.assertIn("cannot be proven provisioned transfer-in mirrors", out)
        self.assertNotIn("git worktree remove", out)

    def test_worktree_on_foreign_branch_preserves(self):
        # Placement identity: a worktree rebound to a foreign branch does not
        # match the claim-derived authoring branch.
        self._seed_clean()
        self._git(self.worktree, "checkout", "-q", "-b", "foreign-branch")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(self.branch, out)
        self.assertNotIn("git worktree remove", out)

    def test_worktree_outside_claim_stem_shape_preserves(self):
        # The placement rule derives the worktree from the claim file stem:
        # a worktree directory named otherwise is not this claim's placement
        # (the done-run manifest is bound to the operand worktree so the
        # refusal isolates the placement shape).
        self.worktree = self.root / "proj-wt-elsewhere"
        self._git(
            self.primary, "worktree", "add", "-q", "-b", "authoring/elsewhere",
            str(self.worktree),
        )
        self._seed_clean()
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn(self.CLAIM_STEM, out)
        self.assertNotIn("git worktree remove", out)

    def test_producer_shape_digest_manifest_in_worktree_done_session_passes(self):
        # r1 F1 regression, the producer's real shape: the run-start digest
        # form of repo_root and the manifest under the dispatching worktree's
        # done-session directory (a worktree-dispatched run never records in
        # the primary's). Before the fix this refused: the matcher compared
        # the digest as a path and the scan never left the target side.
        self._seed_claim()
        self._seed_prompt_log()
        self._write_worktree_manifest(
            self._manifest_payload(repo_root=self._digest_root(self.worktree))
        )
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(f"done-run manifest {self.RUN_ID}", out)
        self.assertIn("git worktree remove", out)

    def test_primary_shape_digest_manifest_in_target_done_session_passes(self):
        # The other producer shape (r1 F1): a primary-dispatched run records
        # the primary's digest under the target-side done-session; the
        # two-arm matcher binds it through the digest arm too.
        self._seed_claim()
        self._seed_prompt_log()
        self._write_manifest(
            self._manifest_payload(repo_root=self._digest_root(self.primary))
        )
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("git worktree remove", out)

    def test_legacy_raw_path_manifest_in_worktree_done_session_passes(self):
        # r1 F1, the legacy shape: pre-digest writers recorded the raw path;
        # the matcher's raw arm keeps such records loadable on both sides of
        # the scan.
        self._seed_claim()
        self._seed_prompt_log()
        self._write_worktree_manifest(self._manifest_payload())
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("git worktree remove", out)

    def test_foreign_digest_manifest_naming_plan_preserves(self):
        # The digest arm discriminates: a 64-hex record whose digest names a
        # foreign checkout binds neither scanned root, so a manifest naming
        # the expected plan from another checkout is not this run's binding.
        self._seed_claim()
        self._seed_prompt_log()
        foreign = self.root / "foreign-checkout"
        foreign.mkdir()
        self._write_manifest(
            self._manifest_payload(repo_root=self._digest_root(foreign))
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("no done-run manifest", out)
        self.assertNotIn("git worktree remove", out)

    def test_run_manifest_matcher_dedupes_shared_identity_across_sides(self):
        # r1 F1, the dedupe rule: one producer record visible through both
        # scanned sides (a shared tmp_dir spelled twice) dedupes to one
        # binding by its run-manifest-<run_id>.json identity.
        self._seed_claim()
        self._seed_prompt_log()
        payload = self._manifest_payload(repo_root=self._digest_root(self.worktree))
        self._write_manifest(payload)
        self._write_worktree_manifest(payload)
        import done_sweep_gates_lib as sweep_lib
        matches = MODULE._no_charter_run_manifests(
            self.primary,
            self.worktree.resolve(),
            self.PLAN_REL,
            sweep_lib._repo_root_matches_value,
        )
        self.assertEqual(
            [name for name, _payload in matches],
            [f"run-manifest-{self.RUN_ID}.json"],
        )

    def test_manifest_without_owned_review_paths_key_preserves(self):
        # r1 F2: a manifest lacking the owned_review_paths key proves nothing
        # about review ownership; the run refuses with preservation instead
        # of silently proving zero.
        self._seed_claim()
        self._seed_prompt_log()
        payload = self._manifest_payload()
        del payload["owned_review_paths"]
        self._write_manifest(payload)
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("owned_review_paths", out)
        self.assertNotIn("git worktree remove", out)

    def test_manifest_with_non_list_owned_review_paths_preserves(self):
        # r1 F2, the other half: the key present but not a list is equally
        # unproven ownership, mirroring the start_commit enforcement.
        self._seed_claim()
        self._seed_prompt_log()
        self._write_manifest(self._manifest_payload(owned_review_paths="none"))
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("non-list owned_review_paths", out)
        self.assertNotIn("git worktree remove", out)

    def test_manifest_owned_run_artifact_preserves(self):
        # r2 F2: a non-empty owned_paths set names run-owned artifacts
        # outside the reviews home - ignored-path artifacts the porcelain
        # check cannot see and the staging scan does not cover - so
        # zero-owned is not proven and the refusal names them. (The empty
        # shape passes: every clean case rides the fixture's default
        # owned_paths: [].)
        self._seed_claim()
        self._seed_prompt_log()
        self._write_manifest(
            self._manifest_payload(
                owned_paths=["docs/tmp/execute-plan/scratch/state.md"]
            )
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("owned_paths", out)
        self.assertIn("docs/tmp/execute-plan/scratch/state.md", out)
        self.assertNotIn("git worktree remove", out)

    def test_manifest_without_owned_paths_key_preserves(self):
        # r2 F2, the missing-key mirror of the owned_review_paths
        # enforcement: a manifest lacking owned_paths proves nothing about
        # run-artifact ownership, so zero-owned is not proven.
        self._seed_claim()
        self._seed_prompt_log()
        payload = self._manifest_payload()
        del payload["owned_paths"]
        self._write_manifest(payload)
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("no owned_paths key", out)
        self.assertNotIn("git worktree remove", out)

    def _seed_older_generation(
        self, drop: tuple[str, ...] = (), **overrides
    ) -> str:
        # An older binding generation of the same run: same expected plan,
        # same start commit, an earlier created_epoch, a distinct run_id
        # (so the filename differs and no dedupe collapses the pair).
        # `drop` removes keys, e.g. to simulate an older manifest generation
        # that predates an owned-set field.
        run_id = self.RUN_ID + "-older"
        payload = self._manifest_payload(
            run_id=run_id,
            marker=self.MARKER + "-older",
            created_epoch=self._manifest_payload()["created_epoch"] - 100.0,
            **overrides,
        )
        for key in drop:
            payload.pop(key, None)
        self._write_manifest(payload, run_id=run_id)
        return f"run-manifest-{run_id}.json"

    def test_two_agreeing_bindings_with_empty_owned_sets_pass(self):
        # r3 F1, the agreement half: two same-plan same-start_commit
        # generations both declaring empty owned sets aggregate to zero;
        # the newest still binds the plan and start commit and the cleanup
        # passes.
        self._seed_claim()
        self._seed_prompt_log()
        self._seed_older_generation()
        self._write_manifest(self._manifest_payload())
        code, out, err = self._run_gate()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("verified 0 owned record(s)", out)
        self.assertIn("git worktree remove", out)

    def test_older_binding_declaring_owned_review_records_preserves(self):
        # r3 F1, the owned_review_paths disagreement: the newest binding
        # declares no review records, but the older generation of the same
        # run declares one; binding the newest alone would print the
        # zero-owned verdict and remove the worktree while the older
        # generation's declared record is destroyed unaccounted. The
        # aggregate across all bindings refuses with preservation.
        self._seed_claim()
        self._seed_prompt_log()
        older_name = self._seed_older_generation(
            owned_review_paths=[
                ".ai-playbook/reviews/2026-10-26-plan-review-no-charter-demo-r1.md"
            ]
        )
        self._write_manifest(self._manifest_payload())
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("review record", out)
        self.assertIn(older_name, out)
        self.assertNotIn("verified 0 owned record(s)", out)
        self.assertNotIn("git worktree remove", out)
        self.assertTrue(self.worktree.is_dir())

    def test_older_binding_declaring_owned_paths_preserves(self):
        # r3 F1, the owned_paths disagreement: an older generation's
        # non-empty run-artifact set refuses even when the newest
        # generation declares none, and the refusal names the declaring
        # manifest and the artifacts.
        self._seed_claim()
        self._seed_prompt_log()
        older_name = self._seed_older_generation(
            owned_paths=["docs/tmp/execute-plan/scratch/state.md"]
        )
        self._write_manifest(self._manifest_payload())
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("owned_paths", out)
        self.assertIn("docs/tmp/execute-plan/scratch/state.md", out)
        self.assertIn(older_name, out)
        self.assertNotIn("git worktree remove", out)

    def test_older_binding_without_owned_review_paths_key_preserves(self):
        # r3 F1, the shape half of the aggregation: every binding manifest
        # must carry the owned-set keys, so an older generation lacking
        # owned_review_paths refuses even though the newest generation's
        # key is present and empty.
        self._seed_claim()
        self._seed_prompt_log()
        self._seed_older_generation(drop=("owned_review_paths",))
        self._write_manifest(self._manifest_payload())
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("owned_review_paths", out)
        self.assertNotIn("git worktree remove", out)

    def test_worktree_facts_without_reviews_dir_preserves(self):
        # r1 F3: the staging scan never silently skips. The worktree's
        # (ignored) facts provision loses its reviews_dir key, so the worktree
        # stays clean while the staging home is unresolvable; the run refuses
        # with a specific reason instead of skipping the scan.
        facts = self.worktree / ".ai-playbook/facts.md"
        _write(
            facts,
            b"```toml\ntmp_dir = \"docs/tmp/\"\n"
            b"metrics_dir = \".ai-playbook/metrics/\"\n```\n",
        )
        self._seed_clean()
        code, out, _err = self._run_gate()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("reviews_dir", out)
        self.assertIn("cannot resolve", out)
        self.assertNotIn("git worktree remove", out)
        # The resources stay: the worktree remains registered on its branch.
        self.assertTrue(self.worktree.is_dir())
        names = [
            entry["branch"]
            for entry in MODULE._parse_worktree_entries(self.primary)
            if Path(entry["path"]).resolve() == self.worktree.resolve()
        ]
        self.assertEqual(names, [self.branch])


class NoCharterProducerWriteTest(NoCharterFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] The routed producer leg of the no-charter
    stand-down closeout (plan 2026-10-28-plan-authoring-stand-down-before-
    charter Task 3, review r1 F1): the done producer's actual write path
    (scripts/done_sweep_gates_lib.py write-manifest, the writer done_run.sh
    setup invokes at its step 7) dispatched from the placement worktree's
    CWD with the routed repo-relative ``--owned-plan`` spelling, and the
    Task 1 arm binds the record it writes. The staging homes start empty
    here (a repository with no prior review records, so the Worktree-first
    transfer-in copies nothing): the producer's claim-or-foreign gate owns
    the mirrored-home shape, the foreign-by-default split deliberately keeps
    the refuse arm for a worktree dispatch, and the routed setup leg carries
    no review operands."""

    MARKER_TS = "20261026T080000Z"

    def _clear_transfer_in_mirrors(self) -> None:
        for rel in (self.prior_record_rel, self.prior_seal_rel):
            (self.primary / rel).unlink()
            (self.worktree / rel).unlink()

    def _write_producer_run_marker(self) -> Path:
        # done_run.sh cmd_setup step 6's run-start marker recipe, verbatim:
        # the bash step writes this marker, the lib writer binds the
        # manifest to it (the digest is the sha256 of the worktree toplevel
        # with the trailing slash stripped, the same derivation the lib's
        # confirmation recomputes).
        session = self.worktree / "docs/tmp/done-session"
        session.mkdir(parents=True, exist_ok=True)
        repo_top = self._git(
            self.worktree, "rev-parse", "--show-toplevel"
        ).stdout.strip()
        repo_hash = hashlib.sha256(repo_top.rstrip("/").encode("utf-8")).hexdigest()
        marker = session / f"run-start-{self.MARKER_TS}"
        _write(marker, f"1790000000 {repo_hash} 4242\n".encode("utf-8"))
        return marker

    def _run_producer_write(self, operand: str, marker: Path) -> tuple[int, str, str]:
        # done_run.sh cmd_setup step 7's writer invocation, verbatim (the
        # same write path done setup uses), dispatched from the placement
        # worktree's CWD exactly like the routed stand-down leg.
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH.parent / "done_sweep_gates_lib.py"),
                "write-manifest",
                "--run-marker",
                str(marker),
                "--owned-plan",
                operand,
            ],
            capture_output=True,
            text=True,
            cwd=str(self.worktree),
            env=_hermetic_lock_env(self.root),
        )
        return proc.returncode, proc.stdout, proc.stderr

    def _producer_manifest_path(self, out: str) -> Path:
        line = next(ln for ln in out.splitlines() if ln.startswith("manifest: "))
        return Path(line[len("manifest: "):])

    def test_producer_write_from_worktree_with_routed_relative_plan_binds(self):
        # The routed leg's spelling (r1 F1): --owned-plan carries the
        # repo-relative dated plans path resolved from the worktree CWD, so
        # the producer's _repo_relative against its dispatching root records
        # the target-relative form the arm's binding string-matches.
        self._clear_transfer_in_mirrors()
        self._seed_claim()
        self._seed_prompt_log()
        marker = self._write_producer_run_marker()
        code, out, err = self._run_producer_write(self.PLAN_REL, marker)
        self.assertEqual(code, 0, out + err)
        manifest_path = self._producer_manifest_path(out)
        # The record lands under the dispatching worktree's gitignored
        # done-session directory, never the primary's.
        self.assertEqual(
            manifest_path.parent.resolve(),
            (self.worktree / "docs/tmp/done-session").resolve(),
        )
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["owned_plan_paths"], [self.PLAN_REL])
        import done_sweep_gates_lib as sweep_lib

        self.assertTrue(
            sweep_lib._repo_root_matches_value(
                payload["repo_root"], self.worktree.resolve()
            ),
            payload["repo_root"],
        )
        self.assertEqual(payload["start_commit"], self.start_commit)
        self.assertEqual(payload["owned_review_paths"], [])
        self.assertEqual(payload["owned_paths"], [])
        # The Task 1 arm binds the producer-written record: the clean
        # no-charter state passes end to end.
        gate_code, gate_out, gate_err = self._run_gate()
        self.assertEqual(gate_code, 0, gate_out + gate_err)
        self.assertEqual(gate_out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("done-run manifest", gate_out)
        self.assertIn("git worktree remove", gate_out)

    def test_producer_write_with_primary_absolute_plan_operand_does_not_bind(self):
        # The mis-spelling the routing pins against (r1 F1): a primary-
        # anchored absolute operand relativizes against the DISPATCHING
        # root, fails its containment check, and survives verbatim, so the
        # arm's string equality against the target-relative expected path
        # never matches and the arm refuses with preservation.
        self._clear_transfer_in_mirrors()
        self._seed_claim()
        self._seed_prompt_log()
        marker = self._write_producer_run_marker()
        code, out, err = self._run_producer_write(str(self._plan_abs()), marker)
        self.assertEqual(code, 0, out + err)
        payload = json.loads(
            self._producer_manifest_path(out).read_text(encoding="utf-8")
        )
        self.assertEqual(payload["owned_plan_paths"], [str(self._plan_abs())])
        gate_code, gate_out, _err = self._run_gate()
        self.assertEqual(gate_code, 1)
        self.assertEqual(gate_out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("no done-run manifest", gate_out)
        self.assertNotIn("git worktree remove", gate_out)


class BaselineClobberGuardTest(_StripsHostGitEnv, unittest.TestCase):
    """Fixtures for the baseline-clobber guards (entry
    closeout-migrate-baseline-tracked-clobber): the pre-flight refusal that
    keeps a baseline-relative migrate from carrying a tracked path backward
    over newer destination content, and the post-run staged-set ownership
    check that restores an owned between-snapshot rewind while leaving
    foreign staged work untouched. Both guards are inert on non-git targets."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    REL = ".ai-playbook/reviews/corpus.md"
    V0 = b"corpus v0\n"
    V2 = b"corpus v2 head bytes\n"

    # Task 2 fixtures (plan 2026-11-04-closeout-clobber-guard-review-
    # residual-trio, R9): a literally wildcard-named tracked file plus a
    # glob-matching sibling, so a bare pathspec built from the star rel
    # glob-matches the sibling.
    STAR_REL = "docs/reviews/t*.md"
    STAR_V0 = b"star v0 bytes\n"
    STAR_V2 = b"star v2 bytes\n"
    SIB_REL = "docs/reviews/tzz.md"
    SIB_V0 = b"sibling v0 bytes\n"
    SIB_V2 = b"sibling v2 bytes\n"

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-baseline-clobber-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        # In-process runs resolve the lock env from this process's
        # environment: pin it hermetically for the whole class. The guard
        # helpers' git subprocesses inherit this process env, so inherited
        # host GIT_* variables are stripped too (the in-process twin of
        # _hermetic_git_env's filter; shared twin home _StripsHostGitEnv).
        # Strip BEFORE the pins are applied so the saved map captures the
        # true host state - the pins carry their own devnull
        # GIT_CONFIG_GLOBAL/SYSTEM values.
        self.strip_host_git_env()
        self.addCleanup(self.restore_host_git_env)
        pins = _hermetic_lock_env(self.root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        return proc.stdout.strip()

    def _write_rel(self, root: Path, data: bytes) -> None:
        _write(root / self.REL, data)

    def _target_repo(self, name: str) -> Path:
        """A git-repository target holding corpus.md at v0 then v2 (the v2
        landing is the peer content a backward carry would overwrite) plus a
        second tracked path for foreign-staged fixtures."""
        target = self.root / name
        target.mkdir(parents=True)
        subprocess.run(
            ["git", "-C", str(target), "init", "-q"],
            capture_output=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        (target / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(DONE_LOCK_SCRIPT_PATH, target / "scripts" / "done-lock.sh")
        self._write_rel(target, self.V0)
        _write(target / "docs/tmp/ledger.md", b"committed ledger line\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "v0: baseline vintage")
        self._write_rel(target, self.V2)
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "v2: peer landing")
        return target

    def _source_with_baseline(self, name: str, seed: bytes) -> tuple[Path, Path]:
        """A plain source dir whose corpus.md holds the seed bytes when the
        baseline snapshot is captured (the stale baseline vintage)."""
        source = self.root / name
        self._write_rel(source, seed)
        baseline = self.root / f"{name}-baseline.json"
        _capture_baseline(source, baseline)
        return source, baseline

    def _run_migrate(self, source: Path, baseline: Path, manifest: Path, target: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH), "migrate",
                "--baseline", str(baseline),
                "--source", str(source),
                "--target", str(target),
                "--manifest", str(manifest),
            ],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root),
        )

    def _stage_rewind(self, target: Path, blob: str, rel: str | None = None) -> None:
        """Stage an older committed vintage of the tracked path while the
        worktree keeps HEAD - the between-snapshot rewind signature. --add
        also covers the e2e fixture where git rm removed the entry first.
        ``rel`` defaults to the class's corpus rel; the Task 3 combined
        fixtures stage rewinds on sibling rels with the same plumbing."""
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--add", "--cacheinfo",
             f"100644,{blob},{rel or self.REL}"],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )

    # ---- Task 2 fixture helpers (plan 2026-11-04-closeout-clobber-guard-
    # review-residual-trio, R9). Empirical substrate (git 2.56.0):
    # `git rev-parse :<rel>` echoes its argument with rc=0 when <rel> holds
    # glob metacharacters and resolves to no single stage-0 entry (the
    # wildcard-named unmerged shape and the index-absent wildcard rel
    # alike), while a plain index-absent rel exits 128; and a bare
    # `git restore -- <star rel>` pathspec glob-matches sibling paths.
    # The fixture plumbing below never lets the star path act as a
    # pathspec: it stages index shapes with update-index plumbing and
    # probes with `:(literal)` quoting of its own.

    def _wildcard_fixture(self, name: str) -> Path:
        """A target repo that additionally carries the literally wildcard-
        named tracked file docs/reviews/t*.md across two commits plus the
        glob-matching sibling docs/reviews/tzz.md across two commits."""
        target = self._target_repo(name)
        (target / "docs/reviews").mkdir(parents=True, exist_ok=True)
        _write(target / self.STAR_REL, self.STAR_V0)
        _write(target / self.SIB_REL, self.SIB_V0)
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "star v0")
        _write(target / self.STAR_REL, self.STAR_V2)
        _write(target / self.SIB_REL, self.SIB_V2)
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "star v2")
        return target

    def _stage_unmerged_wildcard(self, target: Path) -> None:
        """Put the star rel at index stages 1-3 with no stage-0 entry (a
        live merge's conflicted shape), built with update-index plumbing
        so the fixture never lets the star path act as a pathspec."""
        b1 = self._git(target, "rev-parse", f"HEAD~1:{self.STAR_REL}")
        b2 = self._git(target, "rev-parse", f"HEAD:{self.STAR_REL}")
        ours = subprocess.run(
            ["git", "-C", str(target), "hash-object", "-w", "--stdin"],
            input=b"stage-3 ours-side bytes\n", capture_output=True,
            check=True, env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--force-remove",
             self.STAR_REL],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        info = "".join(
            f"100644 {blob} {stage}\t{self.STAR_REL}\n"
            for stage, blob in ((1, b1), (2, b2),
                                (3, ours.stdout.decode().strip()))
        )
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--index-info"],
            input=info.encode(), capture_output=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        self.assertNotIn(
            " 0\t",
            self._git(target, "ls-files", "-s", "--",
                      f":(literal){self.STAR_REL}"),
            "fixture precondition: no stage-0 entry may remain",
        )
        self.assertEqual(
            len(self._git(target, "ls-files", "-u", "--",
                          f":(literal){self.STAR_REL}").splitlines()),
            3,
            "fixture precondition: the star rel must sit at stages 1-3",
        )

    def _wildcard_staged_deletion(self, target: Path) -> None:
        """Stage a deletion of the star rel (its index entry removed) and
        delete its worktree file - the witnessed `git rm` shape - with
        update-index plumbing so the star path never acts as a
        pathspec."""
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--force-remove",
             self.STAR_REL],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        (target / self.STAR_REL).unlink()
        self.assertFalse(
            (target / self.STAR_REL).exists(),
            "fixture precondition: the worktree file is missing",
        )

    def test_migrate_preflight_refuses_tracked_backward_carry(self):
        """[class: REPOSITORY_TEST] Safety witness (GREEN preservation, plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2; expected green before and after the narrowing -
        it guards the narrowing from over-shooting): a would-carry path
        whose source bytes hash to an OLDER COMMITTED VINTAGE of the tracked
        target HEAD (the target's own v0 commit, a true backward carry that
        would rewind destination content) refuses in the pre-flight: exit 2,
        both error lines, the tracked content untouched, nothing copied, and
        no manifest."""
        target = self._target_repo("target")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V0)
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn(
            f"baseline clobber pre-flight: {self.REL} is tracked at the target HEAD with different bytes",
            proc.stderr,
        )
        self.assertIn("narrow the capture dirs to untracked session surfaces", proc.stderr)
        self.assertNotIn("merge-lock", proc.stderr, "the refusal must precede the merge-lock span")
        self.assertEqual(
            (target / self.REL).read_bytes(),
            self.V2,
            "the refusal must leave the tracked content untouched",
        )
        self.assertFalse(manifest.exists(), "a refused migrate writes no manifest")

    def test_migrate_preflight_allows_byte_identical_tracked_carry(self):
        """[class: REPOSITORY_TEST] A would-carry path whose bytes equal the
        tracked target HEAD passes the pre-flight: the migrate completes and
        reports no prevented clobbers."""
        target = self._target_repo("target")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V2)
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("baseline clobber pre-flight", proc.stderr)
        self.assertEqual((target / self.REL).read_bytes(), self.V2)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["prevented_clobbers"], [])

    def test_migrate_preflight_and_guard_inert_on_non_git_target(self):
        """[class: REPOSITORY_TEST] On a plain non-git target both guards are
        inert - there are no committed bytes to compare and no index to read:
        the migrate keeps the collision behavior and emits neither guard's
        lines."""
        target = self.root / "plain-target"
        target.mkdir(parents=True)
        self._write_rel(target, b"peer landing bytes\n")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, b"corpus v1 + run row\n")
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("COLLISION", proc.stdout + proc.stderr)
        self.assertNotIn("baseline clobber pre-flight", proc.stderr)
        self.assertNotIn("prevented-clobber", proc.stdout + proc.stderr)
        self.assertEqual((target / self.REL).read_bytes(), b"peer landing bytes\n")

    def test_postrun_guard_restores_owned_rewound_staged_entry(self):
        """[class: REPOSITORY_TEST] An owned staged rewind - staged bytes an
        older committed vintage of a path this run carried - is restored from
        HEAD in both the index and the worktree and reported as a prevented
        clobber."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self.assertNotEqual(v0_blob, head_blob)
        self._stage_rewind(target, v0_blob)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        self.assertEqual(prevented, [self.REL])
        self.assertIn(f"prevented clobber: {self.REL}", captured.getvalue())
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            head_blob,
            "the index must hold HEAD after the restore",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(),
            self.V2,
            "the worktree must hold HEAD after the restore",
        )

    def test_postrun_guard_leaves_foreign_staged_entries_untouched(self):
        """[class: REPOSITORY_TEST] Foreign staged work is reported and never
        touched: a rewound vintage this run did not carry stays staged, and a
        tracked path staged with brand-new bytes stays staged."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        self._stage_rewind(target, v0_blob)
        _write(target / "docs/tmp/ledger.md", b"foreign edit never committed\n")
        self._git(target, "add", "docs/tmp/ledger.md")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(target, set())
        self.assertEqual(prevented, [])
        out = captured.getvalue()
        self.assertIn("holds a rewound staged vintage this run did not carry", out)
        self.assertIn("left untouched for the operator's revert-set machinery", out)
        self.assertIn("staged outside this run's carried outputs", out)
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            v0_blob,
            "a foreign rewind must stay staged",
        )
        self.assertEqual(
            self._git(target, "rev-parse", ":docs/tmp/ledger.md"),
            self._git(target, "hash-object", "docs/tmp/ledger.md"),
            "foreign staged new work must stay staged",
        )

    def test_migrate_postrun_reports_foreign_staged_rewind(self):
        """[class: REPOSITORY_TEST] End to end: a staged rewind this run did
        not carry (the source bytes equal HEAD, so the identical skip keeps
        the path out of the carried set) is reported report-only - the index
        still holds the rewound vintage and the manifest records no prevented
        clobbers."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        self._stage_rewind(target, v0_blob)
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V2)
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(
            "holds a rewound staged vintage this run did not carry",
            proc.stdout,
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            v0_blob,
            "a foreign rewind must survive the migrate untouched",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["prevented_clobbers"], [])

    def test_migrate_postrun_restores_owned_rewound_staged_entry_end_to_end(self):
        """[class: REPOSITORY_TEST] End to end through the CLI: a staged
        rewound vintage of a path this run carried (the worktree copy is
        absent, so the carry lands it in migrated and the index holds the
        v0 blob) is restored from HEAD, the manifest records the prevented
        clobber, and the index and worktree hold HEAD after the run."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(target, "rm", "-q", self.REL)
        self._stage_rewind(target, v0_blob)
        self.assertFalse((target / self.REL).exists(), "fixture precondition: the worktree copy is absent so the run carries the path")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V2)
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"prevented clobber: {self.REL}", proc.stdout)
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            head_blob,
            "the index must hold HEAD after the owned restore",
        )
        self.assertEqual((target / self.REL).read_bytes(), self.V2)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            data["prevented_clobbers"],
            [{
                "destination": (Path(target).resolve() / self.REL).as_posix(),
                "action": "restored-from-HEAD",
                "record_index": 0,
            }],
        )

    # ---- Guard containment and the prevented_clobber_failures manifest
    # section (plan 2026-11-05-closeout-migrate-supplemental-inventory-and-
    # guard-residuals Task 1). The witnesses inject at the module's
    # subprocess-launcher seam (or wrap MODULE._prevent_tracked_clobbers for
    # the phase flag) and run in-process via MODULE.main under the
    # setUp-pinned _hermetic_lock_env, so the fault reaches the guard's own
    # spawns and the manifest lands on disk in this process.

    def _owned_rewind_e2e_fixture(self, name: str = "target") -> tuple[Path, Path, Path, Path, str]:
        """The end-to-end owned-rewind fixture (the shape
        test_migrate_postrun_restores_owned_rewound_staged_entry_end_to_end
        pins): the target's carried rel is worktree-absent with the v0 blob
        staged in the index, and the source carries fresh v2 bytes under a
        captured baseline, so the run migrates the path and the guard sees
        an owned staged rewind. ``name`` distinguishes the fixture's target
        repo from one the calling test built itself. Returns (target,
        source, baseline, manifest, v0_blob)."""
        target = self._target_repo(name)
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        self._git(target, "rm", "-q", self.REL)
        self._stage_rewind(target, v0_blob)
        self.assertFalse(
            (target / self.REL).exists(),
            "fixture precondition: the worktree copy is absent so the run carries the path",
        )
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V2)
        manifest = self.root / "migration.json"
        return target, source, baseline, manifest, v0_blob

    def _migrate_inproc(self, source: Path, baseline: Path, manifest: Path, target: Path) -> int:
        """The in-process migrate (the fault-injection seam's requirement):
        MODULE.main under the setUp-pinned _hermetic_lock_env, so a
        subprocess-launcher patch reaches the guard's spawns."""
        return MODULE.main([
            "migrate",
            "--baseline", str(baseline),
            "--source", str(source),
            "--target", str(target),
            "--manifest", str(manifest),
            "--suffix", "1",
        ])

    def _guard_phase_wrappers(self):
        """The phase-flag plumbing the fault injections share: wrap
        MODULE._prevent_tracked_clobbers so a subprocess.run patch can fault
        only the guard's spawns, and return (guarding, phase) for the test
        to compose with its own faulty run function."""
        real_guard = MODULE._prevent_tracked_clobbers
        phase = {"in_guard": False}

        def guarding(*a, **k):
            phase["in_guard"] = True
            try:
                return real_guard(*a, **k)
            finally:
                phase["in_guard"] = False

        return guarding, phase

    def test_guard_spawn_oserror_midwalk_records_failure_and_completes_manifest(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1):
        a fault-injected OSError at the guard's subprocess-launcher seam
        mid-walk (the staged-set read succeeds, the first classification
        read dies) is contained by the guarded span: the manifest is still
        written with a {destination, action: guard-failed, error} entry in
        prevented_clobber_failures, the priors disposition runs (the discard
        arm), the run's copy work itself succeeded, and the run exits 0 with
        the loud stderr summary naming the count and the destination."""
        target, source, baseline, manifest, v0_blob = self._owned_rewind_e2e_fixture()
        guarding, phase = self._guard_phase_wrappers()
        real_run = MODULE.subprocess.run
        real_discard = MODULE._discard_prior_targets
        spawns = {"n": 0}
        discard_calls = []

        def faulty_run(argv, *a, **k):
            if phase["in_guard"]:
                spawns["n"] += 1
                if spawns["n"] > 1:
                    raise OSError("simulated guard spawn failure mid-walk")
            return real_run(argv, *a, **k)

        def spying_discard(priors):
            discard_calls.append(list(priors))
            return real_discard(priors)

        with mock.patch.object(MODULE, "_prevent_tracked_clobbers", guarding), \
                mock.patch.object(MODULE.subprocess, "run", faulty_run), \
                mock.patch.object(MODULE, "_discard_prior_targets", spying_discard):
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn(
            self.REL, [entry["source"] for entry in data["migrated"]],
            "the run's copy work itself must have succeeded",
        )
        failures = data["prevented_clobber_failures"]
        self.assertEqual(len(failures), 1, out.getvalue() + err.getvalue())
        self.assertEqual(failures[0]["action"], "guard-failed")
        self.assertEqual(failures[0]["destination"], target.resolve().as_posix())
        self.assertIn("OSError", failures[0]["error"])
        self.assertIn("simulated guard spawn failure", failures[0]["error"])
        self.assertEqual(
            data["prevented_clobbers"], [],
            "the guard died before any restore, so nothing was prevented",
        )
        self.assertEqual(
            discard_calls, [[]],
            "the priors restore-or-discard disposition must run on the "
            "guard-crash path too (the empty priors list takes the discard arm)",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"), v0_blob,
            "the staged rewind must stay (the guard died before any restore)",
        )
        err_text = err.getvalue()
        self.assertIn(
            "ERROR: 1 clobber-guard failure(s) recorded in "
            "prevented_clobber_failures",
            err_text,
            "the loud stderr summary must print on the exit-0 path",
        )
        self.assertIn(target.resolve().as_posix(), err_text)

    def test_guard_keyboard_interrupt_reraised_after_manifest_record(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1):
        a fault-injected KeyboardInterrupt at the guard's spawn seam is
        recorded in the written manifest's prevented_clobber_failures, the
        priors discard arm runs, and the interrupt is re-raised out of the
        migrate - never converted to exit 0."""
        target, source, baseline, manifest, v0_blob = self._owned_rewind_e2e_fixture()
        guarding, phase = self._guard_phase_wrappers()
        real_run = MODULE.subprocess.run
        real_discard = MODULE._discard_prior_targets
        discard_calls = []

        def interrupting_run(argv, *a, **k):
            if phase["in_guard"]:
                raise KeyboardInterrupt("simulated SIGINT at the guard's spawn seam")
            return real_run(argv, *a, **k)

        def spying_discard(priors):
            discard_calls.append(list(priors))
            return real_discard(priors)

        with mock.patch.object(MODULE, "_prevent_tracked_clobbers", guarding), \
                mock.patch.object(MODULE.subprocess, "run", interrupting_run), \
                mock.patch.object(MODULE, "_discard_prior_targets", spying_discard):
            err = io.StringIO()
            with contextlib.redirect_stderr(err), self.assertRaises(KeyboardInterrupt):
                self._migrate_inproc(source, baseline, manifest, target)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn(
            self.REL, [entry["source"] for entry in data["migrated"]],
            "the run's copy work itself must have succeeded",
        )
        failures = data["prevented_clobber_failures"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["action"], "guard-failed")
        self.assertIn("KeyboardInterrupt", failures[0]["error"])
        self.assertEqual(
            discard_calls, [[]],
            "the priors discard arm must run before the interrupt re-raises",
        )
        self.assertIn(
            "ERROR: 1 clobber-guard failure(s) recorded in "
            "prevented_clobber_failures",
            err.getvalue(),
            "the loud stderr summary must print before the re-raise",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"), v0_blob,
            "the staged rewind must stay (the guard died before any restore)",
        )

    def test_staged_set_read_failure_recorded_in_manifest_not_silent(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1):
        a staged-set read failing rc != 0 records a prevented_clobber_failures
        entry into a completed manifest - the run exits 0 but not silently:
        the loud stderr summary names the count and the destination."""
        target, source, baseline, manifest, _v0_blob = self._owned_rewind_e2e_fixture()
        guarding, phase = self._guard_phase_wrappers()
        real_run = MODULE.subprocess.run
        spawns = {"n": 0}

        def failing_read_run(argv, *a, **k):
            if phase["in_guard"]:
                spawns["n"] += 1
                if spawns["n"] == 1:
                    return subprocess.CompletedProcess(
                        argv, 1, b"", b"simulated staged-set read failure",
                    )
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE, "_prevent_tracked_clobbers", guarding), \
                mock.patch.object(MODULE.subprocess, "run", failing_read_run):
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn(
            self.REL, [entry["source"] for entry in data["migrated"]],
            "the run's copy work itself must have succeeded",
        )
        failures = data["prevented_clobber_failures"]
        self.assertEqual(len(failures), 1, out.getvalue() + err.getvalue())
        self.assertEqual(failures[0]["action"], "staged-set-read-failed")
        self.assertEqual(failures[0]["destination"], target.resolve().as_posix())
        self.assertIn("simulated staged-set read failure", failures[0]["error"])
        self.assertEqual(data["prevented_clobbers"], [])
        err_text = err.getvalue()
        self.assertIn(
            "ERROR: 1 clobber-guard failure(s) recorded in "
            "prevented_clobber_failures",
            err_text,
            "no silent exit 0: the loud stderr summary must print",
        )
        self.assertIn(target.resolve().as_posix(), err_text)

    def test_preflight_head_probe_failure_reported_not_treated_as_absent(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1,
        extended over the Task 2 batched shape): a HEAD read failing rc != 0
        - both the batched tracked-map read and the per-path fallback probe
        it degrades to - is reported by name (the WARNs) and recorded in the
        manifest's prevented_clobber_failures with the phase-provenance
        action strings (the pre-flight rows unprefixed, the in-lock re-scan
        rows under the rescan- prefix), never silently treated as absent at
        HEAD; the run still completes (the paths are skipped for the
        offender decision, the carry proceeds)."""
        target = self._target_repo("target")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V2)
        manifest = self.root / "migration.json"
        real_run = MODULE.subprocess.run

        def failing_probe_run(argv, *a, **k):
            if "ls-tree" in argv:
                if "-z" in argv:
                    # The batched map read runs bytes-mode capture; the
                    # per-path fallback probe runs text-mode.
                    return subprocess.CompletedProcess(
                        argv, 1, b"", b"simulated HEAD probe failure",
                    )
                return subprocess.CompletedProcess(
                    argv, 1, "", "simulated HEAD probe failure",
                )
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE.subprocess, "run", failing_probe_run):
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        err_text = err.getvalue()
        self.assertIn(
            "HEAD tracked map read failed", err_text,
            "the failed batched map read must be reported, never silent",
        )
        self.assertIn(
            "HEAD probe failed", err_text,
            "the failed per-path probe must be reported by name, never "
            "silently treated as absent",
        )
        self.assertIn(self.REL, err_text)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        failures = data["prevented_clobber_failures"]
        self.assertEqual(
            [entry["action"] for entry in failures],
            [
                "head-map-failed",
                "head-probe-failed",
                "rescan-head-map-failed",
                "rescan-head-probe-failed",
            ],
            "each phase must record its own probe failures under the "
            "phase-distinct action strings",
        )
        self.assertEqual(failures[1]["destination"], (target.resolve() / self.REL).as_posix())
        self.assertIn("simulated HEAD probe failure", failures[1]["error"])
        self.assertIn(
            "ERROR: 4 clobber-guard failure(s) recorded in "
            "prevented_clobber_failures",
            err_text,
            "the loud stderr summary must name the recorded failures",
        )

    def test_preflight_absent_at_head_carry_no_false_probe_warning(self):
        """[class: REPOSITORY_TEST] The probe's other shape (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1,
        pass 2): a plain new artifact absent at HEAD resolves the HEAD probe
        rc 0 with empty output and carries normally - no "HEAD probe failed"
        WARN and no prevented_clobber_failures entry. The rev-parse probe
        read exactly this shape as rc 128 "Needed a single revision",
        printing a false WARN and recording a false head-probe-failed entry
        on every normal new-artifact carry."""
        target = self._target_repo("absent-target")
        source, baseline = self._source_with_baseline("absent-source", b"corpus v1\n")
        new_rel = "docs/tmp/fresh-run-artifact.md"
        _write(source / new_rel, b"fresh run output\n")
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn(
            "HEAD probe failed", proc.stderr,
            "an absent-at-HEAD carry is not a probe failure: no false WARN",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            data["prevented_clobber_failures"], [],
            "an absent-at-HEAD carry records no head-probe-failed entry",
        )
        self.assertIn(
            new_rel, [entry["source"] for entry in data["migrated"]],
            "the new artifact must actually carry (the witness is a silent carry)",
        )

    def test_migrate_preflight_skips_dangling_symlink_like_the_carry_loop(self):
        """[class: REPOSITORY_TEST] A baseline-known path whose symlink
        dangled after the snapshot follows the carry loop's skip shape: the
        migrate completes with the loop's skipped disposition instead of a
        digest-read traceback in the pre-flight."""
        target = self._target_repo("target")
        source = self.root / "source"
        self._write_rel(source, b"corpus v1\n")
        real = source / "docs/tmp/real.md"
        _write(real, b"symlink target bytes\n")
        link = source / "docs/tmp/link.md"
        link.symlink_to(real)
        baseline = self.root / "baseline.json"
        _capture_baseline(source, baseline)
        real.unlink()
        self.assertTrue(link.is_symlink() and not link.exists(), "fixture precondition: the symlink dangles after the snapshot")
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn("docs/tmp/link.md", [entry["source"] for entry in data["skipped"]])

    def test_postrun_guard_handles_staged_deletions_by_ownership(self):
        """[class: REPOSITORY_TEST] A staged deletion of a tracked path is
        classified by ownership: an owned deletion is restored from HEAD in
        index and worktree and reported, a foreign deletion is reported and
        left deleted."""
        target = self._target_repo("target")
        ledger_rel = "docs/tmp/ledger.md"
        self._git(target, "rm", "--cached", ledger_rel)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(target, set())
        self.assertEqual(prevented, [])
        self.assertIn(f"{ledger_rel} is a staged deletion this run did not carry", captured.getvalue())
        self._git(target, "reset", "-q", "--", ledger_rel)
        self._git(target, "rm", "--cached", self.REL)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        self.assertEqual(prevented, [self.REL])
        self.assertIn(f"prevented clobber: {self.REL} (staged deletion", captured.getvalue())
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            self._git(target, "rev-parse", f"HEAD:{self.REL}"),
            "the index must hold HEAD after the owned-deletion restore",
        )
        self.assertEqual((target / self.REL).read_bytes(), self.V2)

    # ---- Task 1 pins (plan 2026-11-02-closeout-migrate-clobber-guard-
    # restore-arms): index-membership routing and the shared reclassify-
    # then-restore helper. The interception recipe is the r3 record's F6
    # pin recipe of record (.ai-playbook/reviews/2026-11-02-closeout-
    # migrate-baseline-tracked-clobber-code-review-r3.md): intercept the
    # module's subprocess.run so a restage lands after the classification
    # rev-parse returns, then assert the downgrade.

    def _peer_restage(self, target: Path, blob: str) -> None:
        """The peer's restage primitive: put one blob at stage 0 of the
        target index (update-index plumbing, the same shape _stage_rewind
        uses)."""
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--add", "--cacheinfo",
             f"100644,{blob},{self.REL}"],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )

    def _unmerged_target(self, name: str) -> Path:
        """A target repo whose REL sits at index stages 1-3 (a live
        content merge left conflicted in the worktree), with everything
        else committed-clean."""
        target = self._target_repo(name)
        branch = self._git(target, "rev-parse", "--abbrev-ref", "HEAD")
        self._git(target, "checkout", "-q", "-b", "peer-merge", "HEAD~1")
        self._write_rel(target, b"corpus peer-side edit\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "peer-side edit")
        self._git(target, "checkout", "-q", branch)
        merge = subprocess.run(
            ["git", "-C", str(target), "merge", "peer-merge"],
            capture_output=True, text=True, check=False,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        self.assertNotEqual(
            merge.returncode, 0, "fixture precondition: the merge must conflict",
        )
        self.assertNotEqual(
            self._git(target, "ls-files", "-u", "--", self.REL), "",
            "fixture precondition: the owned path must sit at stages 1-3",
        )
        return target

    def test_postrun_guard_routes_unmerged_owned_entry_report_only(self):
        """[class: REPOSITORY_TEST] An owned path sitting at index stages
        1-3 (mid-merge) is unmerged foreign state, not a staged deletion:
        the guard reports it report-only naming the unmerged state, spawns
        zero restores, and leaves the conflict - index stages and worktree
        markers - untouched."""
        target = self._unmerged_target("target")
        restore_spawns = {"n": 0}
        real_run = subprocess.run

        def counting_run(argv, *a, **k):
            if "restore" in argv:
                restore_spawns["n"] += 1
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE.subprocess, "run", new=counting_run):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        self.assertEqual(prevented, [])
        out = captured.getvalue()
        self.assertIn(f"prevented-clobber check: {self.REL}", out)
        self.assertIn("unmerged", out, "the report line must name the unmerged state")
        self.assertIn("left untouched", out)
        self.assertEqual(
            restore_spawns["n"], 0,
            "an unmerged entry must spawn zero restores",
        )
        self.assertEqual(
            len(self._git(target, "ls-files", "-u", "--", self.REL).splitlines()),
            3, "all three index stages must survive the guard",
        )
        self.assertIn(
            "<<<<<<<",
            (target / self.REL).read_text(encoding="utf-8", errors="replace"),
            "the worktree conflict markers must survive the guard",
        )

    def test_postrun_guard_downgrades_when_peer_restages_during_owned_deletion(self):
        """[class: REPOSITORY_TEST] The deletion restore arm runs the shared
        reclassify-then-restore helper (still-absent means unchanged): a
        peer restage of HEAD bytes landing after the classification read
        (the r3 F6 subprocess-run interception recipe) downgrades the arm
        to report-only - no restore, the changed-under-guard line, and the
        peer's restaged blob left in the index."""
        target = self._target_repo("target")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(target, "rm", "--cached", self.REL)
        real_run = subprocess.run
        classification_reads = {"n": 0}

        def restaging_run(argv, *a, **k):
            # Hook truth (plan 2026-11-04-closeout-clobber-guard-review-
            # residual-trio, R4, correcting the row's misstated premise):
            # the hook matches only a `rev-parse` argv carrying the `:<rel>`
            # element (element-exact list membership), so it never matches
            # `_head_blob`'s HEAD probe - an `ls-tree` argv whose pathspec
            # is `:(literal)<rel>`, a different tool and a different argv
            # string - and it does NOT match both probes as the row
            # recorded. What argv alone cannot do is distinguish the
            # classification read (the walk's _read_staged_entry) from the
            # recheck read inside _reclassify_then_restore: both pass the
            # same `:<rel>` element, so the one-shot counter below is what
            # targets the restage at the classification read (the first
            # read only).
            is_classification_read = "rev-parse" in argv and f":{self.REL}" in argv
            result = real_run(argv, *a, **k)
            if is_classification_read:
                classification_reads["n"] += 1
                if classification_reads["n"] == 1:
                    self._peer_restage(target, head_blob)
            return result

        with mock.patch.object(MODULE.subprocess, "run", new=restaging_run):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        self.assertGreaterEqual(
            classification_reads["n"], 1,
            "fixture precondition: the classification read ran",
        )
        self.assertEqual(
            prevented, [],
            "the peer restage must downgrade the arm to report-only",
        )
        self.assertIn(
            "changed under the guard between classification and restore",
            captured.getvalue(),
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            head_blob,
            "the peer's restaged blob must survive the guard",
        )
        self.assertEqual((target / self.REL).read_bytes(), self.V2)

    def test_postrun_guard_downgrades_when_peer_restages_during_owned_vintage(self):
        """[class: REPOSITORY_TEST] The vintage restore arm keeps its
        compare-then-act downgrade (the r3 F6 pin recipe of record,
        generalized into the shared helper): a peer restage of HEAD bytes
        landing after the classification read downgrades to report-only -
        no restore, the changed-under-guard line, the peer's restaged blob
        left in the index."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self.assertNotEqual(v0_blob, head_blob)
        self._stage_rewind(target, v0_blob)
        real_run = subprocess.run
        classification_reads = {"n": 0}

        def restaging_run(argv, *a, **k):
            # Same element-exact hook as the deletion arm's restaging_run
            # above (the R4 hook-truth comment lives there): only the first
            # `:<rel>` rev-parse - the classification read - is retargeted.
            is_classification_read = "rev-parse" in argv and f":{self.REL}" in argv
            result = real_run(argv, *a, **k)
            if is_classification_read:
                classification_reads["n"] += 1
                if classification_reads["n"] == 1:
                    self._peer_restage(target, head_blob)
            return result

        with mock.patch.object(MODULE.subprocess, "run", new=restaging_run):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        self.assertEqual(
            prevented, [],
            "the peer restage must downgrade the arm to report-only",
        )
        self.assertIn(
            "changed under the guard between classification and restore",
            captured.getvalue(),
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            head_blob,
            "the peer's restaged blob must survive the guard",
        )
        self.assertEqual((target / self.REL).read_bytes(), self.V2)

    def test_postrun_guard_reports_failed_restore_without_re_restoring(self):
        """[class: REPOSITORY_TEST] A restore subprocess failure is a report
        line, not a retry: the guard prints the restore-failure WARN,
        records no prevented path, spawns exactly one restore, and leaves
        the staged rewind in place. Extended (plan
        closeout-migrate-supplemental-inventory-and-guard-residuals Task 1):
        the same failed-restore shape end to end through MODULE.main writes
        the manifest with the restore failure recorded in
        prevented_clobber_failures, so the closeout reader adjudicates
        without stderr."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        self._stage_rewind(target, v0_blob)
        real_run = subprocess.run
        restore_spawns = {"n": 0}

        def failing_restore_run(argv, *a, **k):
            if "restore" in argv:
                restore_spawns["n"] += 1
                return subprocess.CompletedProcess(
                    argv, 1, "", "simulated restore failure",
                )
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE.subprocess, "run", new=failing_restore_run):
            captured = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(err):
                prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        self.assertEqual(prevented, [])
        self.assertIn(f"prevented-clobber restore failed for {self.REL}", err.getvalue())
        self.assertIn("simulated restore failure", err.getvalue())
        self.assertEqual(
            restore_spawns["n"], 1, "a failed restore must not be retried",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"), v0_blob,
            "the staged rewind must stay after the failed restore",
        )

        # End-to-end extension: the failed restore reaches the written
        # manifest's prevented_clobber_failures section beside the prevented
        # rows, the run exits 0, and nothing was prevented.
        e2e_target, source, baseline, manifest, _v0 = self._owned_rewind_e2e_fixture(
            "target-restore-failed-e2e",
        )

        def failing_restore_run_e2e(argv, *a, **k):
            if "restore" in argv:
                return subprocess.CompletedProcess(
                    argv, 1, "", "simulated restore failure",
                )
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE.subprocess, "run", new=failing_restore_run_e2e):
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, e2e_target)
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        failures = data["prevented_clobber_failures"]
        self.assertEqual(len(failures), 1, out.getvalue() + err.getvalue())
        self.assertEqual(failures[0]["action"], "restore-failed")
        self.assertEqual(failures[0]["destination"], (e2e_target.resolve() / self.REL).as_posix())
        self.assertIn("simulated restore failure", failures[0]["error"])
        self.assertEqual(data["prevented_clobbers"], [])

    def test_postrun_guard_reports_post_restore_mismatch_without_re_restoring(self):
        """[class: REPOSITORY_TEST] The helper verifies the restore outcome:
        a peer blob restaged in the window after the restore subprocess
        returns makes the post-restore re-read mismatch HEAD - a report
        line and no re-restore, the peer's bytes surviving."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        self._stage_rewind(target, v0_blob)
        _write(target / "docs/tmp/peer-restage-scratch.md", b"corpus restaged after the restore ran\n")
        peer_blob = self._git(
            target, "hash-object", "-w", "--", "docs/tmp/peer-restage-scratch.md",
        )
        (target / "docs/tmp/peer-restage-scratch.md").unlink()
        real_run = subprocess.run
        restore_spawns = {"n": 0}

        def restaging_run(argv, *a, **k):
            if "restore" in argv:
                restore_spawns["n"] += 1
                result = real_run(argv, *a, **k)
                self._peer_restage(target, peer_blob)
                return result
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE.subprocess, "run", new=restaging_run):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        self.assertEqual(prevented, [])
        out = captured.getvalue()
        self.assertIn(f"prevented-clobber check: {self.REL}", out)
        self.assertIn("did not hold HEAD after the restore", out)
        self.assertEqual(
            restore_spawns["n"], 1,
            "a post-restore mismatch must not trigger a re-restore",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"), peer_blob,
            "the peer's post-restore bytes must survive (no re-restore)",
        )

        # End-to-end extension (plan closeout-migrate-supplemental-inventory-
        # and-guard-residuals Task 1): the post-restore non-hold reaches the
        # written manifest's prevented_clobber_failures section, the run
        # exits 0, and nothing was prevented.
        e2e_target, source, baseline, manifest, _v0 = self._owned_rewind_e2e_fixture(
            "target-restore-mismatch-e2e",
        )
        _write(e2e_target / "docs/tmp/peer-restage-scratch.md", b"corpus restaged after the restore ran\n")
        e2e_peer_blob = self._git(
            e2e_target, "hash-object", "-w", "--", "docs/tmp/peer-restage-scratch.md",
        )
        (e2e_target / "docs/tmp/peer-restage-scratch.md").unlink()

        def restaging_run_e2e(argv, *a, **k):
            if "restore" in argv:
                result = real_run(argv, *a, **k)
                self._peer_restage(e2e_target, e2e_peer_blob)
                return result
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE.subprocess, "run", new=restaging_run_e2e):
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, e2e_target)
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        failures = data["prevented_clobber_failures"]
        self.assertEqual(len(failures), 1, out.getvalue() + err.getvalue())
        self.assertEqual(failures[0]["action"], "restore-mismatch")
        self.assertEqual(failures[0]["destination"], (e2e_target.resolve() / self.REL).as_posix())
        self.assertEqual(data["prevented_clobbers"], [])
        self.assertEqual(
            self._git(e2e_target, "rev-parse", f":{self.REL}"), e2e_peer_blob,
            "the peer's post-restore bytes must survive (no re-restore)",
        )

    def test_migrate_scoped_inventory_route_bypasses_the_preflight(self):
        """[class: REPOSITORY_TEST] The baseline-less scoped-inventory route
        has no baseline to move backward: a carried path tracked at the git
        target HEAD with different bytes keeps the collision disposition and
        the pre-flight never refuses."""
        target = self._target_repo("target")
        source = self.root / "source"
        self._write_rel(source, b"corpus v1 + run row\n")
        inventory = self.root / "scoped-inventory.json"
        inventory.write_text(json.dumps({"files": [self.REL]}), encoding="utf-8")
        manifest = self.root / "migration.json"
        proc = subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH), "migrate",
                "--inventory", str(inventory),
                "--source", str(source),
                "--target", str(target),
                "--manifest", str(manifest),
            ],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("baseline clobber pre-flight", proc.stderr)
        self.assertIn("COLLISION", proc.stdout + proc.stderr)

    # ---- Task 2 pins (plan 2026-11-02-closeout-migrate-clobber-guard-
    # restore-arms): the delivered-blob owned signature. The guard's vintage
    # decision compares the staged blob against the in-memory delivered blob
    # captured during the carry loop (never a manifest read); a rel absent
    # from the map keeps the vintage-only signature (the defensive absence
    # rule). The deliberate-reversal residual stands: a revert staged at a
    # committed historical vintage differing from the delivered blob still
    # restores; r2 F6's restore-only-on-delivered-match direction is
    # rejected (plan Assumptions).

    def test_migrate_records_delivered_blob_and_leaves_owned_staged_delivered_bytes(self):
        """[class: REPOSITORY_TEST] The staged-equals-delivered shape: the
        run delivers the older committed vintage's bytes (the scoped route
        rides past the pre-flight that would refuse the backward carry) and
        the staged entry then holds exactly those delivered bytes; the
        guard compares against the in-memory delivered blob recorded on the
        migrated row, leaves the run's own delivered bytes untouched with a
        report line, and restores nothing - the pre-fix guard destroyed the
        run's output by restoring HEAD (origin row
        2026-11-02-closeout-migrate-owned-vintage-restore-signature)."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self.assertNotEqual(v0_blob, head_blob)
        self._git(target, "rm", "-q", self.REL)
        self._stage_rewind(target, v0_blob)
        self.assertFalse(
            (target / self.REL).exists(),
            "fixture precondition: the worktree copy is absent so the run carries the path",
        )
        source = self.root / "source"
        self._write_rel(source, self.V0)
        inventory = self.root / "scoped-inventory.json"
        inventory.write_text(json.dumps({"files": [self.REL]}), encoding="utf-8")
        manifest = self.root / "migration.json"
        proc = subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH), "migrate",
                "--inventory", str(inventory),
                "--source", str(source),
                "--target", str(target),
                "--manifest", str(manifest),
            ],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        out = proc.stdout
        self.assertIn(
            f"prevented-clobber check: {self.REL} staged bytes equal the "
            "bytes this run delivered",
            out,
            "the delivered-equal staged shape must be reported",
        )
        self.assertIn("left untouched", out)
        self.assertNotIn(
            f"prevented clobber: {self.REL}",
            out,
            "the delivered-equal staged bytes must not be restored",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            v0_blob,
            "the staged delivered bytes must survive in the index",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(),
            self.V0,
            "the run's own delivered bytes must survive in the worktree",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        migrated = [
            entry for entry in data["migrated"] if entry["source"] == self.REL
        ]
        self.assertEqual(len(migrated), 1, data["migrated"])
        self.assertEqual(
            migrated[0]["delivered_blob"], v0_blob,
            "the migrated row must record the delivered blob captured "
            "during the carry loop",
        )
        self.assertEqual(data["prevented_clobbers"], [])

    def test_postrun_guard_restores_owned_rewind_when_staged_blob_differs_from_delivered(self):
        """[class: REPOSITORY_TEST] The tightened signature keeps the
        between-snapshot rewind catch: an owned staged vintage whose blob
        differs from the rel's in-memory delivered blob (the run delivered
        HEAD's bytes; the staged entry rewound to the older vintage) still
        restores from HEAD in index and worktree."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self.assertNotEqual(v0_blob, head_blob)
        self._stage_rewind(target, v0_blob)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.REL}, {self.REL: head_blob},
            )
        self.assertEqual(prevented, [self.REL])
        self.assertIn(f"prevented clobber: {self.REL}", captured.getvalue())
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            head_blob,
            "the index must hold HEAD after the restore",
        )
        self.assertEqual((target / self.REL).read_bytes(), self.V2)

    def test_postrun_guard_absent_delivered_blob_keeps_vintage_only_signature(self):
        """[class: REPOSITORY_TEST] The defensive absence rule: a rel with
        no entry in the in-memory delivered-blob map (an empty map, or one
        naming only other rels) keeps the current vintage-only signature -
        the owned rewind restores from HEAD. The decision never reads the
        manifest."""
        for label, delivered in (
            ("empty-map", {}),
            ("other-rels-only", {"docs/tmp/ledger.md": "0" * 40}),
        ):
            with self.subTest(map=label):
                target = self._target_repo(f"target-{label}")
                v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
                head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
                self.assertNotEqual(v0_blob, head_blob)
                self._stage_rewind(target, v0_blob)
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    prevented = MODULE._prevent_tracked_clobbers(
                        target, {self.REL}, delivered,
                    )
                self.assertEqual(prevented, [self.REL])
                self.assertIn(f"prevented clobber: {self.REL}", captured.getvalue())
                self.assertEqual(
                    self._git(target, "rev-parse", f":{self.REL}"),
                    head_blob,
                    "the index must hold HEAD after the restore",
                )
                self.assertEqual((target / self.REL).read_bytes(), self.V2)

    def test_migrate_records_delivered_blob_on_replaced_manifest_row(self):
        """[class: REPOSITORY_TEST] The receipt-proven replacement arm
        records the delivered blob too: the replaced manifest row carries
        the delivered_blob sha of the incoming bytes, computed during the
        carry loop before the manifest append (an untracked target path
        keeps the pre-flight inert so the replacement route runs)."""
        target = self._target_repo("target")
        note_rel = "docs/tmp/mirror-note.md"
        prior = b"mirror note v1\n"
        incoming = b"mirror note v2\n"
        _write(target / note_rel, prior)
        source = self.root / "source"
        _write(source / note_rel, prior)
        session_dir = source / "docs/tmp/execute-plan/mirror-fixture"
        row = (
            "task_boundary: task 1 commit abc1234 verification: pass; "
            "mirror_status=complete mirror_receipts="
            f"{_receipts_token([_file_receipt(note_rel, _digest(prior))])}"
        )
        _write_session_manifest(
            session_dir / "manifest.md", [row], run_worktree=str(source.resolve()),
        )
        baseline = session_dir / "closeout-baseline.json"
        _capture_baseline(source, baseline)
        _write(source / note_rel, incoming)
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source.resolve(), baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # The delivered blob the capture must record, derived independently
        # of the migrated file (hash a scratch copy of the incoming bytes).
        scratch = target / "docs/tmp/incoming-scratch.md"
        _write(scratch, incoming)
        incoming_blob = self._git(
            target, "hash-object", "--", "docs/tmp/incoming-scratch.md",
        )
        scratch.unlink()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        replaced = [
            entry for entry in data["replaced"] if entry["source"] == note_rel
        ]
        self.assertEqual(len(replaced), 1, proc.stdout + proc.stderr)
        self.assertEqual(
            replaced[0]["delivered_blob"], incoming_blob,
            "the replaced row must record the delivered blob captured "
            "during the carry loop",
        )
        self.assertEqual((target / note_rel).read_bytes(), incoming)
        self.assertEqual(data["prevented_clobbers"], [])

    def test_postrun_guard_emits_for_staged_new_file_absent_at_head(self):
        """[class: REPOSITORY_TEST] The staged-new-at-target shape (plan
        closeout-migrate-clobber-guard-restore-arms Task 3): a staged new
        file absent at HEAD - the head_blob-is-None skip - emits a
        prevented-clobber-check line and stays untouched under either
        owned-set argument (the staged fixture path is in neither set -
        the shape emits before any ownership check; label truth per
        T3-NIT-1: neither subTest exercises an owned fixture path);
        the pre-fix walk passed the shape silently."""
        for label, owned in (
            ("empty owned set", set()),
            ("owned set holding a different rel", {self.REL}),
        ):
            with self.subTest(owned_set=label):
                target = self._target_repo(f"target-new-at-target-{label}")
                new_rel = "docs/tmp/staged-new.md"
                _write(target / new_rel, b"staged new bytes never committed\n")
                self._git(target, "add", "-A", new_rel)
                new_blob = self._git(target, "rev-parse", f":{new_rel}")
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    prevented = MODULE._prevent_tracked_clobbers(target, owned)
                out = captured.getvalue()
                self.assertEqual(prevented, [])
                self.assertIn(
                    f"prevented-clobber check: {new_rel} is "
                    "staged-new-at-target",
                    out,
                    "the staged-new-at-target shape must emit",
                )
                self.assertIn("left untouched", out)
                self.assertEqual(
                    self._git(target, "rev-parse", f":{new_rel}"),
                    new_blob,
                    "the staged new file must stay staged",
                )

    def test_postrun_guard_emits_for_owned_staged_brand_new_bytes(self):
        """[class: REPOSITORY_TEST] The fall-past branch (plan closeout-
        migrate-clobber-guard-restore-arms Task 3): an owned path staged
        with brand-new bytes (a blob that is not a committed vintage in
        HEAD's history, so the delivered-blob vintage arm never reaches it)
        emits a prevented-clobber-check line naming
        staged-new-bytes-on-a-carried-path and stays untouched; the pre-fix
        walk fell past the report silently."""
        target = self._target_repo("target-new-bytes-carried")
        _write(target / self.REL, b"brand-new bytes never committed\n")
        self._git(target, "add", self.REL)
        staged = self._git(target, "rev-parse", f":{self.REL}")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.REL}, {self.REL: "f" * 40},
            )
        out = captured.getvalue()
        self.assertEqual(prevented, [])
        self.assertIn(
            f"prevented-clobber check: {self.REL} is staged-new-bytes-"
            "on-a-carried-path",
            out,
            "the owned brand-new-bytes shape must emit",
        )
        self.assertIn("left untouched", out)
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            staged,
            "the brand-new staged bytes must stay staged",
        )

    def test_postrun_guard_emits_for_staged_bytes_equal_to_head(self):
        """[class: REPOSITORY_TEST] The equals-HEAD shape (plan closeout-
        migrate-clobber-guard-restore-arms Task 3): a staged blob equal to
        HEAD - reachable at the walk through a mode-only change, which
        diff --cached lists even though the blob is unchanged - emits a line
        naming the no-op restage and leaves the staged entry untouched; the
        pre-fix walk passed the shape silently."""
        target = self._target_repo("target-noop-restage")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(
            target, "update-index", "--add", "--cacheinfo",
            f"100755,{head_blob},{self.REL}",
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(target, {self.REL})
        out = captured.getvalue()
        self.assertEqual(prevented, [])
        self.assertIn(
            f"prevented-clobber check: {self.REL} staged bytes equal HEAD",
            out,
            "the equals-HEAD shape must emit",
        )
        self.assertIn("no-op restage", out)
        self.assertIn("left untouched", out)
        self.assertEqual(
            self._git(target, "ls-files", "-s", "--", self.REL),
            f"100755 {head_blob} 0\t{self.REL}",
            "the mode-only restage must stay staged untouched",
        )

    # ---- Task 1 pins (plan 2026-11-04-closeout-clobber-guard-review-
    # residual-trio, R8 disposition): the deletion arm's delivered-map
    # consult. Before any restore of an owned index-absent path the arm
    # reads the on-disk bytes' blob once (the consult, the arm's only
    # worktree-byte read; the recheck observes index state only) and
    # branches four ways: delivered bytes present unstaged are kept and
    # reported, a missing file (a filesystem existence check, never
    # probe-None) restores from HEAD as the witnessed full-rewind
    # reconstruction, HEAD-equal bytes restore as loss-free cleanup, and
    # anything else is report-only operator-decide. The peer-restage
    # downgrade stays the safety witness: the existing
    # test_postrun_guard_downgrades_when_peer_restages_during_owned_deletion
    # pin keeps it, with the consult read placed before the recheck.

    def test_postrun_guard_deletion_arm_keeps_delivered_bytes_present_unstaged(self):
        """[class: REPOSITORY_TEST] The delivered-kept arm: an owned
        index-absent path whose on-disk bytes hash to the run's delivered
        blob keeps those bytes - no restore, a report line naming delivered
        bytes present unstaged, and the path absent from the prevented
        list (the plan's reproduced destruction witness: the pre-consult
        arm restored HEAD over the run's delivered bytes)."""
        target = self._target_repo("target-delivered-kept")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(target, "rm", "--cached", self.REL)
        _write(target / self.REL, b"corpus delivered unstaged bytes\n")
        delivered_blob = self._git(target, "hash-object", "--", self.REL)
        self.assertNotEqual(
            delivered_blob, head_blob,
            "fixture precondition: the delivered bytes differ from HEAD",
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.REL}, {self.REL: delivered_blob},
            )
        self.assertEqual(
            prevented, [],
            "delivered bytes present unstaged must stay absent from the "
            "prevented list",
        )
        out = captured.getvalue()
        self.assertIn(
            "delivered bytes present unstaged", out,
            "the keep report line must name delivered bytes present unstaged",
        )
        self.assertNotIn(
            f"prevented clobber: {self.REL}", out,
            "the delivered bytes must not be restored",
        )
        self.assertEqual(
            MODULE._read_staged_entry(target, self.REL), (None, False),
            "the staged deletion must stay in the index (no restore)",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(),
            b"corpus delivered unstaged bytes\n",
            "the run's delivered bytes must survive in the worktree",
        )

    def test_postrun_guard_deletion_arm_restores_missing_worktree_file(self):
        """[class: REPOSITORY_TEST] The missing-file arm (GREEN-first
        regression pin): an owned index-absent path whose worktree file
        does not exist on disk (the witnessed `git rm` shape) restores
        from HEAD exactly as today - the witnessed full-rewind
        reconstruction - and enters the prevented list; the consult must
        not widen this shape's behavior."""
        target = self._target_repo("target-deletion-missing")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(target, "rm", "-q", self.REL)
        self.assertFalse(
            (target / self.REL).exists(),
            "fixture precondition: the worktree file is missing",
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.REL}, {self.REL: head_blob},
            )
        self.assertEqual(prevented, [self.REL])
        self.assertIn(f"prevented clobber: {self.REL}", captured.getvalue())
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            head_blob,
            "the index must hold HEAD after the restore",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "the worktree must hold HEAD after the restore",
        )

    def test_postrun_guard_deletion_arm_restores_head_equal_bytes_loss_free(self):
        """[class: REPOSITORY_TEST] The HEAD-equal arm (GREEN-first
        regression pin): an owned index-absent path whose on-disk bytes
        hash to HEAD's blob (delivered unknown here) restores from HEAD as
        loss-free cleanup - the restore proceeds, the prevented list holds
        the path, and index and worktree hold HEAD after it; nothing can
        be lost because the bytes are HEAD's."""
        target = self._target_repo("target-deletion-head-equal")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(target, "rm", "--cached", self.REL)
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "fixture precondition: the on-disk bytes equal HEAD",
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.REL}, {self.REL: "f" * 40},
            )
        self.assertEqual(prevented, [self.REL])
        self.assertIn(f"prevented clobber: {self.REL}", captured.getvalue())
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"),
            head_blob,
            "the index must hold HEAD after the loss-free restore",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "the worktree must hold HEAD after the loss-free restore",
        )

    def test_postrun_guard_deletion_arm_reports_foreign_unstaged_bytes_report_only(self):
        """[class: REPOSITORY_TEST] The foreign arm: an owned index-absent
        path whose on-disk bytes hash to neither the delivered blob nor
        HEAD's blob (pinned both with the delivered blob known and with no
        delivered blob in the map - the defensive absence rule never
        licenses a restore over unknown on-disk bytes) gets the report-only
        operator-decide note, no restore, and stays absent from the
        prevented list; the foreign bytes survive untouched."""
        for label, delivered_map in (
            ("delivered-known", "head"),
            ("delivered-absent", {}),
        ):
            with self.subTest(map=label):
                target = self._target_repo(f"target-deletion-foreign-{label}")
                head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
                self._git(target, "rm", "--cached", self.REL)
                _write(target / self.REL, b"foreign unstaged bytes\n")
                foreign_blob = self._git(target, "hash-object", "--", self.REL)
                self.assertNotEqual(
                    foreign_blob, head_blob,
                    "fixture precondition: the bytes are neither delivered "
                    "nor HEAD",
                )
                mapped = (
                    {self.REL: head_blob}
                    if delivered_map == "head" else delivered_map
                )
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    prevented = MODULE._prevent_tracked_clobbers(
                        target, {self.REL}, mapped,
                    )
                self.assertEqual(
                    prevented, [],
                    "foreign unstaged bytes must stay absent from the "
                    "prevented list",
                )
                out = captured.getvalue()
                self.assertIn(
                    "operator decision required", out,
                    "the report-only note must name the operator decision",
                )
                self.assertNotIn(
                    f"prevented clobber: {self.REL}", out,
                    "the foreign bytes must not be restored",
                )
                self.assertEqual(
                    MODULE._read_staged_entry(target, self.REL), (None, False),
                    "the staged deletion must stay in the index (no restore)",
                )
                self.assertEqual(
                    (target / self.REL).read_bytes(),
                    b"foreign unstaged bytes\n",
                    "the foreign unstaged bytes must survive untouched",
                )

    def test_postrun_guard_deletion_arm_reports_unprobeable_bytes_report_only(self):
        """[class: REPOSITORY_TEST] The unprobeable arm: an owned
        index-absent path whose file exists on disk but whose hash probe
        returns None falls to the report-only operator-decide note, no
        restore, absent from the prevented list - the missing-file branch
        is decided by a filesystem existence check, never by probe-None,
        so a failed probe on a present file can never pass for the
        witnessed missing-file restore."""
        target = self._target_repo("target-deletion-unprobeable")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(target, "rm", "--cached", self.REL)
        _write(target / self.REL, b"unstaged bytes the probe cannot read\n")
        self.assertTrue(
            (target / self.REL).exists(),
            "fixture precondition: the file is present so only the probe "
            "fails",
        )
        captured = io.StringIO()
        with mock.patch.object(MODULE, "_worktree_blob", return_value=None):
            with contextlib.redirect_stdout(captured):
                prevented = MODULE._prevent_tracked_clobbers(
                    target, {self.REL}, {self.REL: head_blob},
                )
        self.assertEqual(
            prevented, [],
            "unprobeable bytes must stay absent from the prevented list",
        )
        out = captured.getvalue()
        self.assertIn(
            "operator decision required", out,
            "the report-only note must name the operator decision",
        )
        self.assertNotIn(
            f"prevented clobber: {self.REL}", out,
            "the unprobeable bytes must not be restored",
        )
        self.assertEqual(
            MODULE._read_staged_entry(target, self.REL), (None, False),
            "the staged deletion must stay in the index (no restore)",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(),
            b"unstaged bytes the probe cannot read\n",
            "the unprobeable unstaged bytes must survive untouched",
        )

    def test_postrun_guard_deletion_arm_delivered_equal_precedes_head_equal(self):
        """[class: REPOSITORY_TEST] The delivered-equals-HEAD boundary: an
        owned index-absent path whose delivered blob equals HEAD's blob
        and whose on-disk bytes hash to both takes the delivered-equal
        branch - keep and report, no prevented append - pinning the
        overlap's branch order (a HEAD-first order would restore over the
        run's delivered bytes)."""
        target = self._target_repo("target-deletion-delivered-eq-head")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self._git(target, "rm", "--cached", self.REL)
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "fixture precondition: the on-disk bytes equal HEAD",
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.REL}, {self.REL: head_blob},
            )
        self.assertEqual(
            prevented, [],
            "the delivered-equal branch must take precedence: no prevented "
            "append",
        )
        out = captured.getvalue()
        self.assertIn(
            "delivered bytes present unstaged", out,
            "the delivered-equal report line must fire at the boundary",
        )
        self.assertNotIn(
            f"prevented clobber: {self.REL}", out,
            "the delivered bytes must not be restored at the boundary",
        )
        self.assertEqual(
            MODULE._read_staged_entry(target, self.REL), (None, False),
            "the staged deletion must stay in the index (no restore)",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "the delivered bytes (equal to HEAD) must survive untouched",
        )

    def test_postrun_guard_deletion_arm_doc_surfaces_state_the_consult(self):
        """[class: REPOSITORY_TEST] The three doc surfaces state the
        four-way consult and its report-only dispositions after the
        change: the deletion-arm inline comment, the
        _prevent_tracked_clobbers docstring's arm inventory, and the
        module header's guard paragraph."""
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        arm_at = source.index("if staged_blob is None:")
        arm_window = source[arm_at:arm_at + 2000]
        for surface_name, surface in (
            ("deletion-arm inline comment", arm_window),
            (
                "_prevent_tracked_clobbers docstring",
                MODULE._prevent_tracked_clobbers.__doc__ or "",
            ),
            ("module header guard paragraph", MODULE.__doc__ or ""),
        ):
            with self.subTest(surface=surface_name):
                self.assertIn(
                    "four-way consult", surface,
                    f"the {surface_name} must state the four-way consult",
                )
                self.assertIn(
                    "report-only", surface,
                    f"the {surface_name} must state its report-only "
                    "dispositions",
                )

    # ---- Task 2 pins (plan 2026-11-04-closeout-clobber-guard-review-
    # residual-trio, R9): 40-hex blob validation in the staged-entry
    # reader and literal pathspec quoting in the probes and restore.

    def test_postrun_guard_classifies_wildcard_unmerged_report_only(self):
        """[class: REPOSITORY_TEST] A wildcard-named unmerged entry - the
        path holds glob metacharacters, so `git rev-parse :<rel>` exits 0
        echoing the argument instead of the 128 the stage-0/unmerged
        discrimination expects - classifies report-only: the reader
        rejects the non-hex stdout and falls to the `git ls-files -u`
        discriminator, the guard emits the unmerged line naming the rel,
        no staged-new misclassification fires, zero restores spawn, and
        all three index stages survive."""
        target = self._wildcard_fixture("target-wildcard-unmerged")
        self._stage_unmerged_wildcard(target)
        restore_spawns = {"n": 0}
        real_run = subprocess.run

        def counting_run(argv, *a, **k):
            if "restore" in argv:
                restore_spawns["n"] += 1
            return real_run(argv, *a, **k)

        with mock.patch.object(MODULE.subprocess, "run", new=counting_run):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                prevented = MODULE._prevent_tracked_clobbers(
                    target, {self.STAR_REL},
                )
        self.assertEqual(
            prevented, [],
            "an unmerged wildcard-named entry is report-only: the "
            "prevented list stays empty",
        )
        out = captured.getvalue()
        self.assertIn(
            f"prevented-clobber check: {self.STAR_REL}", out,
            "the report line must name the wildcard rel",
        )
        self.assertIn(
            "unmerged", out,
            "the report line must name the unmerged state",
        )
        self.assertIn("left untouched", out)
        self.assertNotIn(
            "staged-new-at-target", out,
            "the non-hex rc=0 echo must not pass for a stage-0 blob",
        )
        self.assertNotIn(
            "staged-new-bytes", out,
            "the vintage walk must not run on the echoed argument",
        )
        self.assertEqual(
            restore_spawns["n"], 0,
            "an unmerged entry must spawn zero restores",
        )
        self.assertEqual(
            len(self._git(target, "ls-files", "-u", "--",
                          f":(literal){self.STAR_REL}").splitlines()),
            3, "all three index stages must survive the guard",
        )

    def test_pathspec_literal_quoting_in_unmerged_probe_history_and_restore(self):
        """[class: REPOSITORY_TEST] The three rel-passing surfaces quote
        the rel as `:(literal)<rel>` so glob metacharacters never act as
        patterns: the `git ls-files -u` discriminator (reached only after
        the reader rejects the non-hex echo), `_blob_in_head_history`'s
        `git log`, and `_reclassify_then_restore`'s `git restore` (both
        restore arms share the helper, so the vintage arm's exposure
        closes with it)."""
        target = self._wildcard_fixture("target-pathspec-literals")
        self._stage_unmerged_wildcard(target)
        literal = f":(literal){self.STAR_REL}"
        git_argvs: list[list[str]] = []
        real_run = subprocess.run

        def recording_run(argv, *a, **k):
            if argv and argv[0] == "git":
                git_argvs.append(list(argv))
            return real_run(argv, *a, **k)

        with self.subTest(leg="ls-files -u discriminator"):
            del git_argvs[:]
            with mock.patch.object(MODULE.subprocess, "run",
                                   new=recording_run):
                entry = MODULE._read_staged_entry(target, self.STAR_REL)
            ls_argvs = [a for a in git_argvs if "ls-files" in a]
            self.assertEqual(
                len(ls_argvs), 1,
                "the rejected non-hex rc=0 echo must fall to exactly one "
                "ls-files -u discriminator read",
            )
            self.assertEqual(
                ls_argvs[0][-2:], ["--", literal],
                "the discriminator must pass the rel quoted literal",
            )
            self.assertEqual(
                entry, (None, True),
                "the wildcard-named unmerged entry must classify unmerged",
            )

        with self.subTest(leg="git log head-history probe"):
            del git_argvs[:]
            head_blob = self._git(target, "rev-parse",
                                  f"HEAD:{self.STAR_REL}")
            with mock.patch.object(MODULE.subprocess, "run",
                                   new=recording_run):
                found = MODULE._blob_in_head_history(
                    target, self.STAR_REL, head_blob,
                )
            log_argvs = [a for a in git_argvs if "log" in a]
            self.assertEqual(len(log_argvs), 1, "the log probe must run")
            self.assertEqual(
                log_argvs[0][-2:], ["--", literal],
                "the head-history probe must pass the rel quoted literal",
            )
            self.assertTrue(
                found,
                "the literal pathspec must still find the committed "
                "vintage",
            )

        with self.subTest(leg="git restore"):
            del git_argvs[:]
            self._wildcard_staged_deletion(target)
            with mock.patch.object(MODULE.subprocess, "run",
                                   new=recording_run):
                restored = MODULE._reclassify_then_restore(
                    target, self.STAR_REL, None, "pin: literal restore",
                )
            restore_argvs = [a for a in git_argvs if "restore" in a]
            self.assertEqual(
                len(restore_argvs), 1,
                "the unchanged recheck must let the restore subprocess "
                "spawn",
            )
            self.assertEqual(
                restore_argvs[0][-2:], ["--", literal],
                "the restore must pass the rel quoted literal",
            )
            self.assertTrue(
                restored, "the literal restore must land and hold",
            )

    def test_reclassify_downgrade_names_unmerged_recheck_and_restores_nothing(self):
        """[class: REPOSITORY_TEST] Behavioral witness for the unmerged
        recheck downgrade arm (T1-NIT-1's shape naming): a recheck read
        returning unmerged downgrades to the dedicated unmerged line,
        spawns no restore subprocess, and leaves the index untouched."""
        target = self._target_repo("target-unmerged-recheck")
        self._git(target, "rm", "--cached", self.REL)
        restore_spawns = {"n": 0}
        real_run = subprocess.run

        def counting_run(argv, *args, **kwargs):
            if "restore" in argv:
                restore_spawns["n"] += 1
            return real_run(argv, *args, **kwargs)

        captured = io.StringIO()
        with mock.patch.object(
            MODULE, "_read_staged_entry", return_value=(None, True)
        ), contextlib.redirect_stdout(captured), mock.patch.object(
            MODULE.subprocess, "run", new=counting_run
        ):
            restored = MODULE._reclassify_then_restore(
                target, self.REL, None, "pin: unmerged recheck downgrade",
            )
        self.assertFalse(
            restored, "an unmerged recheck must not report a restore",
        )
        self.assertIn(
            "is unmerged in the index (stages 1-3)", captured.getvalue(),
            "the downgrade must name the unmerged shape like the "
            "walk-level line",
        )
        self.assertEqual(
            restore_spawns["n"], 0, "no restore subprocess may spawn",
        )
        self.assertEqual(
            self._git(target, "ls-files", "-u", "--", self.REL),
            "", "the fixture index must stay untouched",
        )

    def test_postrun_guard_wildcard_staged_deletion_restores_only_its_own_path(self):
        """[class: REPOSITORY_TEST] An owned wildcard-named staged
        deletion (the witnessed missing-file shape) restores exactly its
        named rel: a foreign sibling staged rewind sitting on a
        glob-matching path (docs/reviews/tzz.md under the t*.md pattern)
        keeps its staged entry byte-identical - the bare pathspec a bare
        restore would pass glob-matches the sibling and would clobber its
        staged vintage."""
        target = self._wildcard_fixture("target-wildcard-deletion")
        sib_v0 = self._git(target, "rev-parse", f"HEAD~1:{self.SIB_REL}")
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--add", "--cacheinfo",
             f"100644,{sib_v0},{self.SIB_REL}"],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        self._wildcard_staged_deletion(target)
        star_head = self._git(target, "rev-parse", f"HEAD:{self.STAR_REL}")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.STAR_REL},
            )
        self.assertEqual(
            prevented, [self.STAR_REL],
            "exactly the named wildcard rel enters the prevented list",
        )
        self.assertIn(
            f"prevented clobber: {self.STAR_REL}", captured.getvalue(),
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.STAR_REL}"), star_head,
            "the star rel's index entry must hold HEAD after the restore",
        )
        self.assertEqual(
            (target / self.STAR_REL).read_bytes(), self.STAR_V2,
            "the star rel's worktree file must hold HEAD after the restore",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.SIB_REL}"), sib_v0,
            "the sibling's staged rewind must stay byte-identical",
        )
        self.assertEqual(
            (target / self.SIB_REL).read_bytes(), self.SIB_V2,
            "the sibling's worktree bytes must stay at its v2 landing",
        )

    def test_read_staged_entry_records_sha1_object_format_precondition(self):
        """[class: REPOSITORY_TEST] The blob-shape validation carries a
        reader-side clause recording the sha1 object-format precondition:
        a sha256 target is outside the guard's observed universe, the
        same repo-state scoping as the comparison's same-conversion
        precondition (doc-only: the pin holds the wording, no behavior
        beyond the 40-hex gate)."""
        doc = MODULE._read_staged_entry.__doc__ or ""
        self.assertIn(
            "40-hex", doc,
            "the reader docstring must name the 40-hex blob-shape "
            "validation",
        )
        self.assertIn(
            "sha1", doc,
            "the reader docstring must record the sha1 object-format "
            "precondition",
        )
        self.assertIn(
            "sha256", doc,
            "the reader docstring must name the sha256 target as outside "
            "the observed universe",
        )

    def test_read_staged_entry_stage0_read_unchanged(self):
        """[class: REPOSITORY_TEST] GREEN-first regression pin: a normal
        stage-0 entry reads (blob, False) exactly as today - a plain
        carried rel, a wildcard-named rel whose clean stage-0 entry
        rev-parse resolves, and the index-absent plain rel whose
        rev-parse exits 128 (the (None, False) staged-deletion
        classification)."""
        target = self._wildcard_fixture("target-stage0-unchanged")
        with self.subTest(shape="plain stage-0 rel"):
            head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
            self.assertEqual(
                MODULE._read_staged_entry(target, self.REL),
                (head_blob, False),
            )
        with self.subTest(shape="wildcard-named clean stage-0 rel"):
            star_blob = self._git(target, "rev-parse",
                                  f"HEAD:{self.STAR_REL}")
            self.assertEqual(
                MODULE._read_staged_entry(target, self.STAR_REL),
                (star_blob, False),
                "a clean stage-0 wildcard-named entry still resolves to "
                "its blob",
            )
        with self.subTest(shape="index-absent plain rel (128 path)"):
            absent = "docs/reviews/never-committed.md"
            self.assertFalse(
                (target / absent).exists(),
                "fixture precondition: the rel is index-absent",
            )
            self.assertEqual(
                MODULE._read_staged_entry(target, absent), (None, False),
            )

    # ---- Task 5 doc-wording pins (plan 2026-11-04-closeout-clobber-guard-
    # review-residual-trio, R1/R3/R6/T1-DOC-1/T1-NIT-1/T1-IOTA-1): each pin
    # greps the doc surface it corrects and is the RED/GREEN vehicle for
    # that wording edit (comment-only and doc-wording edits name no new
    # behavior; the pin holds the wording itself).

    def test_record_delivered_blob_docstring_absence_trigger_is_failed_probe(self):
        """[class: REPOSITORY_TEST] R1 docstring truth: the recorder's
        absence trigger is stated as a genuinely failed probe (an unreadable
        or missing file), never as a non-git target - `git hash-object`
        succeeds outside a repository, so a non-git target is not the
        absence trigger."""
        doc = MODULE._record_delivered_blob.__doc__ or ""
        self.assertNotIn(
            "non-git target", doc,
            "the docstring must not name a non-git target as the failed-"
            "probe case: git hash-object succeeds outside a repo",
        )
        self.assertIn(
            "unreadable", doc,
            "the absence trigger must be stated as a genuinely failed "
            "probe (an unreadable file)",
        )
        self.assertIn(
            "missing file", doc,
            "the absence trigger must be stated as a genuinely failed "
            "probe (a missing file)",
        )

    def test_delivered_bytes_comparison_comment_records_clean_filter_precondition(self):
        """[class: REPOSITORY_TEST] R3 comparison precondition: the
        delivered-bytes comparison site carries a comment stating both
        sides hash through the same clean-filter conversion (default
        `git hash-object` applies filters, so the delivered hash and the
        consult hash filter identically), whichever filters are
        configured apply equally to both sides, and the equality is
        robust under a stable filter configuration."""
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        site_at = source.index(
            "deletion_blob = _worktree_blob(target, deletion_path)"
        )
        site_window = source[site_at:site_at + 900]
        self.assertIn(
            "same clean-filter conversion", site_window,
            "the comparison site must state both sides hash through the "
            "same clean-filter conversion",
        )
        self.assertIn(
            "stable filter", site_window,
            "the comparison site must state the equality is robust under "
            "a stable filter configuration",
        )
        self.assertIn(
            "apply equally to both sides", site_window,
            "the comparison site must state whichever filters are "
            "configured apply equally to both sides",
        )
        self.assertNotIn(
            "autocrlf-unset", site_window,
            "the comparison site must not premise the equality on the "
            "repo's own filter state",
        )

    def test_module_header_vintage_sentence_names_delivered_blob_narrowing(self):
        """[class: REPOSITORY_TEST] R6 module header qualification: the
        vintage-restore sentence carries the delivered-blob clause - the
        vintage arm keeps its current decision; the delivered-blob consult
        narrows only the deletion arm."""
        header = MODULE.__doc__ or ""
        self.assertIn(
            "vintage arm keeps its current decision", header,
            "the vintage-restore sentence must record that the vintage "
            "arm keeps its current decision",
        )
        self.assertIn(
            "narrows only the deletion arm", header,
            "the vintage-restore sentence must record that the "
            "delivered-blob consult narrows only the deletion arm",
        )

    def test_guard_docstring_unmerged_route_covers_all_entries(self):
        """[class: REPOSITORY_TEST] T1-DOC-1 unmerged route wording: the
        guard docstring states the unmerged report-only route for ALL
        unmerged entries, not only owned ones."""
        doc = MODULE._prevent_tracked_clobbers.__doc__ or ""
        self.assertNotIn(
            "An owned entry sitting unmerged", doc,
            "the docstring must not scope the unmerged report-only route "
            "to owned entries: the code routes all unmerged entries",
        )
        self.assertIn(
            "Any entry sitting unmerged", doc,
            "the unmerged report-only route must be stated for all "
            "unmerged entries",
        )

    def test_reclassify_downgrade_line_names_unmerged_shape(self):
        """[class: REPOSITORY_TEST] T1-NIT-1 downgrade-line shape: the
        reclassify-then-restore downgrade line names the unmerged shape
        (stages 1-3) when the re-read returns unmerged, like the
        walk-level unmerged line does."""
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        fn_at = source.index("def _reclassify_then_restore(")
        fn_window = source[fn_at:source.index("\ndef ", fn_at + 1)]
        self.assertIn(
            "unmerged in the index", fn_window,
            "the downgrade line must name the unmerged shape like the "
            "walk-level line does",
        )
        self.assertIn(
            "stages 1-3", fn_window,
            "the downgrade line must name the stages 1-3 shape",
        )

    def test_guard_docstring_records_ita_non_coverage(self):
        """[class: REPOSITORY_TEST] T1-IOTA-1 documented non-coverage: the
        guard's walk docstring records that intent-to-add entries never
        enter the enumeration on this host's git and that widening the
        enumeration is forbidden."""
        doc = MODULE._prevent_tracked_clobbers.__doc__ or ""
        self.assertIn(
            "intent-to-add", doc,
            "the walk docstring must name intent-to-add entries",
        )
        self.assertIn(
            "never enter the enumeration", doc,
            "the walk docstring must record that intent-to-add entries "
            "never enter the enumeration on this host's git",
        )
        self.assertIn(
            "widening the enumeration is forbidden", doc,
            "the walk docstring must record that widening the "
            "enumeration is forbidden",
        )

    # ---- Task 2: direction-aware pre-flight, batched probes, and the
    # in-lock re-scan (plan 2026-11-05-closeout-migrate-supplemental-
    # inventory-and-guard-residuals). The direction witnesses pin the
    # narrowing (only an older committed vintage refuses; a forward carry
    # falls through to the collision-rename disposition), the batching
    # witnesses pin the batched probe shapes through the module's
    # subprocess-launcher seam, and the interleaving witnesses drive the
    # pre-lock window with the suite's deterministic foreign-hold idiom
    # (_acquire_foreign_hold, in-process migrate, pinned lock env, generous
    # max-wait, release) - never peer polling.

    def _acquire_foreign_hold(self, repo: Path, label: str, holder_pid: int) -> dict[str, str]:
        """Acquire the repository-keyed merge lock on ``repo`` from this
        test process (the MigrateMergeLockTest idiom): the done-lock script
        with the holder pid pinned into the hermetic env, the exports
        parsed for the release."""
        acquired = subprocess.run(
            ["bash", str(repo / "scripts" / "done-lock.sh"), "merge-acquire", "--label", label],
            capture_output=True, text=True, cwd=str(repo),
            env=_hermetic_lock_env(self.root, MERGE_LOCK_HOLDER_PID=str(holder_pid)),
        )
        self.assertEqual(acquired.returncode, 0, acquired.stderr)
        exports: dict[str, str] = {}
        for line in acquired.stdout.splitlines():
            for name in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
                prefix = f"export {name}="
                if line.startswith(prefix):
                    exports[name] = line[len(prefix):]
        self.assertIn("MERGE_LOCK_DIR", exports)
        self.assertIn("MERGE_LOCK_TOKEN", exports)
        return exports

    def _release_hold(self, repo: Path, exports: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(repo / "scripts" / "done-lock.sh"), "merge-release"],
            capture_output=True, text=True, cwd=str(repo),
            env=_hermetic_lock_env(self.root, **exports),
        )

    def _interleaved_migrate(
        self, source: Path, baseline: Path, manifest: Path, target: Path,
        window_action, counts: dict[str, int] | None = None,
    ) -> tuple[dict, list[str]]:
        """The deterministic pre-lock-window fixture: a foreign hold is
        acquired on the target first, the in-process migrate runs in a
        worker thread under the setUp-pinned lock env with a generous
        max-wait, the main thread waits until the pre-flight's pre-lock
        invocation has returned (a recording wrapper sets the event), then
        performs ``window_action`` inside the open window, releases the
        hold, and joins the worker. Returns (box, phases): box carries
        code/out/err for the finished run; phases lists each
        `_baseline_clobber_preflight` invocation's offender list (the
        pre-lock walk first, then the in-lock re-scan walk)."""
        holder = subprocess.Popen(["sleep", "120"])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        exports = self._acquire_foreign_hold(target, "blocker", holder.pid)
        preflight_done = threading.Event()
        phases: list[list[str]] = []
        real_preflight = MODULE._baseline_clobber_preflight

        def recording_preflight(*a, **k):
            scanned = real_preflight(*a, **k)
            # Shape-tolerant: the post-Task-2 scan returns (offenders,
            # snapshot-head-map, snapshot-source-blobs); the pre-Task-2
            # scan returns the bare offender list. Either way the phases
            # ledger counts invocations, which is what the re-scan
            # assertions read.
            offenders = scanned[0] if isinstance(scanned, tuple) else scanned
            phases.append(list(offenders))
            preflight_done.set()
            return scanned

        real_run = MODULE.subprocess.run

        def counting_run(argv, *a, **k):
            names = [x if isinstance(x, str) else os.fsdecode(x) for x in argv]
            if "ls-tree" in names:
                counts["ls-tree"] = counts.get("ls-tree", 0) + 1
            if "--stdin-paths" in names:
                counts["stdin-paths"] = counts.get("stdin-paths", 0) + 1
            return real_run(argv, *a, **k)

        box: dict = {}

        def run_migrate() -> None:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                box["code"] = MODULE.main([
                    "migrate",
                    "--baseline", str(baseline),
                    "--source", str(source),
                    "--target", str(target),
                    "--manifest", str(manifest),
                    "--suffix", "1",
                ])
            box["out"], box["err"] = out.getvalue(), err.getvalue()

        saved_wait = os.environ.get("DOCS_SYNC_MERGE_MAX_WAIT")
        os.environ["DOCS_SYNC_MERGE_MAX_WAIT"] = "120"
        wrappers = [
            mock.patch.object(MODULE, "_baseline_clobber_preflight", recording_preflight)
        ]
        if counts is not None:
            wrappers.append(mock.patch.object(MODULE.subprocess, "run", counting_run))
        worker = threading.Thread(target=run_migrate, daemon=True)
        worker.start()
        released = None
        try:
            with contextlib.ExitStack() as stack:
                for wrapper in wrappers:
                    stack.enter_context(wrapper)
                self.assertTrue(
                    preflight_done.wait(timeout=60),
                    "the pre-lock pre-flight never returned inside the window",
                )
                window_action()
                released = self._release_hold(target, exports)
                worker.join(timeout=120)
        finally:
            if saved_wait is None:
                os.environ.pop("DOCS_SYNC_MERGE_MAX_WAIT", None)
            else:
                os.environ["DOCS_SYNC_MERGE_MAX_WAIT"] = saved_wait
        self.assertFalse(worker.is_alive(), "the migrate thread never finished")
        if released is not None:
            self.assertEqual(released.returncode, 0, released.stderr)
        return box, phases

    def test_migrate_forward_carry_falls_through_to_collision_rename(self):
        """[class: REPOSITORY_TEST] Safety witness (the RED discriminator,
        plan 2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2): source bytes NEWER than HEAD on a tracked path -
        novel bytes that hash to no committed vintage - no longer refuse;
        the carry falls through to the concrete collision-rename
        disposition: exit 0, the destination keeps HEAD, the run's bytes
        land at the collision sibling, the renamed manifest row is recorded,
        and no prevented_clobber_failures entry exists."""
        target = self._target_repo("target")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, b"corpus v2 + run row\n")
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("COLLISION", proc.stdout)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual([entry["source"] for entry in data["renamed"]], [self.REL])
        self.assertTrue(data["renamed"][0]["collision_renamed"])
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "the destination must keep the committed HEAD bytes",
        )
        self.assertEqual(
            (target / ".ai-playbook/reviews/corpus.wt-1.md").read_bytes(),
            b"corpus v2 + run row\n",
        )
        self.assertEqual(data["prevented_clobber_failures"], [])

    def test_in_lock_rescan_refuses_when_head_moves_in_prelock_window(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2): a peer commit landing between the pre-flight
        probe and the lock acquire, changing a tracked destination, is
        refused by the in-lock re-scan before the first copy - exit 2 via
        the HEAD-drift half of the snapshot comparison (the fresh scan's
        offender set alone is empty here: the carried bytes are a forward
        carry, so only the HEAD-snapshot comparison can fire), nothing
        copied, no manifest. The fixture is the deterministic foreign-hold
        idiom, never peer polling; the counting wrapper shows both walks
        share the batched probes (one ls-tree and one --stdin-paths hash
        batch per walk, two walks total)."""
        target = self._target_repo("target")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, b"corpus v2 + run row\n")
        manifest = self.root / "migration.json"
        peer_bytes = b"corpus v3 peer landing\n"

        def land_peer_commit() -> None:
            _write(target / self.REL, peer_bytes)
            self._git(target, "add", "-A")
            self._git(target, "commit", "-q", "-m", "v3: peer landing in the pre-lock window")

        counts: dict[str, int] = {}
        box, phases = self._interleaved_migrate(
            source, baseline, manifest, target, land_peer_commit, counts,
        )
        self.assertEqual(box["code"], 2, box["out"] + box["err"])
        self.assertIn("in-lock re-scan", box["err"])
        self.assertIn("target HEAD moved during the pre-lock window", box["err"])
        self.assertIn(
            f"in-lock re-scan: committed path changed in the window: {self.REL}",
            box["err"],
        )
        self.assertNotIn(
            "source bytes changed during the pre-lock window", box["err"],
            "the HEAD-drift half fired; the source never drifted",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(), peer_bytes,
            "the refusal must leave the peer's committed content standing",
        )
        self.assertFalse(
            (target / ".ai-playbook/reviews/corpus.wt-1.md").exists(),
            "the copy must never have run (no collision sibling)",
        )
        self.assertFalse(manifest.exists(), "a refused re-scan writes no manifest")
        self.assertEqual(
            len(phases), 2,
            "the re-scan must re-invoke the same pre-flight implementation "
            "(the pre-lock walk, then the in-lock walk)",
        )
        self.assertEqual(
            (counts.get("ls-tree"), counts.get("stdin-paths")), (2, 2),
            "one ls-tree and one batched hash-object per walk: the re-scan "
            "shares the batched probes, no serial re-probe",
        )

    def test_in_lock_rescan_refuses_when_source_drifts_in_prelock_window(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2): a baseline-identical source file edited during
        the pre-lock window (HEAD unchanged) closes through the re-scan's
        source-drift half - the carried set changed under the pre-flight's
        read, so the run refuses instead of carrying blind: exit 2 naming
        the drifted path, the HEAD-drift half silent, the drifted bytes
        never land at the target, and the genuinely carried companion file
        never copies. Same deterministic foreign-hold idiom."""
        target = self._target_repo("target")
        source = self.root / "source"
        self._write_rel(source, self.V2)
        baseline = self.root / "baseline.json"
        _capture_baseline(source, baseline)
        late_rel = "docs/tmp/late-artifact.md"
        _write(source / late_rel, b"late run output\n")
        manifest = self.root / "migration.json"
        drifted = self.V2 + b"drift row\n"

        def edit_source_in_window() -> None:
            self._write_rel(source, drifted)

        box, phases = self._interleaved_migrate(
            source, baseline, manifest, target, edit_source_in_window,
        )
        self.assertEqual(box["code"], 2, box["out"] + box["err"])
        self.assertIn("in-lock re-scan", box["err"])
        self.assertIn("source bytes changed during the pre-lock window", box["err"])
        self.assertIn(
            f"in-lock re-scan: carried source path changed in the window: {self.REL}",
            box["err"],
        )
        self.assertNotIn(
            "target HEAD moved during the pre-lock window", box["err"],
            "HEAD is unchanged; only the source-drift half may fire",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "the drifted bytes must never land at the target",
        )
        self.assertFalse(
            (target / late_rel).exists(),
            "the would-be companion copy must never land (never carry blind)",
        )
        self.assertFalse(manifest.exists(), "a refused re-scan writes no manifest")
        self.assertEqual(len(phases), 2)

    def test_multi_candidate_batched_preflight_exact_offenders_and_one_batch_per_walk(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2): a multi-candidate fixture (older-vintage
        offender, baseline-identical file, dangling symlink, absent-at-HEAD
        path, forward-newer carry) produces the exact offender list and
        per-path stderr naming after batching, and the subprocess-seam
        counting wrapper pins one ls-tree and one batched hash-object call
        per walk (plus one rev-list universe pass and one per-rel
        --find-object probe for the single in-universe differ)."""
        target = self._target_repo("target")
        forward_rel = "docs/tmp/forward.md"
        _write(target / forward_rel, b"forward committed base\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "forward: tracked surface")
        source = self.root / "source"
        _write(source / "docs/tmp/ledger.md", b"committed ledger line\n")
        real = source / "docs/tmp/real.md"
        _write(real, b"symlink resolution bytes\n")
        link = source / "docs/tmp/link.md"
        link.symlink_to(real)
        self._write_rel(source, b"corpus v1\n")
        baseline = self.root / "baseline.json"
        _capture_baseline(source, baseline)
        real.unlink()
        self.assertTrue(
            link.is_symlink() and not link.exists(),
            "fixture precondition: the symlink dangles after the snapshot",
        )
        self._write_rel(source, self.V0)
        _write(source / forward_rel, b"forward run edits\n")
        _write(source / "docs/tmp/new-artifact.md", b"brand new bytes\n")
        manifest = self.root / "migration.json"
        counts: dict[str, int] = {}
        real_run = MODULE.subprocess.run

        def counting_run(argv, *a, **k):
            names = [x if isinstance(x, str) else os.fsdecode(x) for x in argv]
            if "ls-tree" in names:
                counts["ls-tree"] = counts.get("ls-tree", 0) + 1
            if "--stdin-paths" in names:
                counts["stdin-paths"] = counts.get("stdin-paths", 0) + 1
            elif "hash-object" in names:
                counts["argv-hash-object"] = counts.get("argv-hash-object", 0) + 1
            if "rev-list" in names:
                counts["rev-list"] = counts.get("rev-list", 0) + 1
            if "--find-object" in names:
                counts["find-object"] = counts.get("find-object", 0) + 1
            return real_run(argv, *a, **k)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(MODULE.subprocess, "run", counting_run):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        err_text = err.getvalue()
        self.assertEqual(code, 2, out.getvalue() + err_text)
        self.assertEqual(
            err_text.count("is tracked at the target HEAD with different bytes"), 1,
            "exactly one offender: the older vintage, not the forward carry",
        )
        self.assertIn(
            f"baseline clobber pre-flight: {self.REL} is tracked at the "
            "target HEAD with different bytes",
            err_text,
            "the offender must be named per-path on stderr",
        )
        self.assertNotIn(
            f"{forward_rel} is tracked at the target HEAD", err_text,
            "the forward-newer carry must not offend",
        )
        self.assertIn("narrow the capture dirs to untracked session surfaces", err_text)
        self.assertEqual(counts.get("ls-tree"), 1, "one batched tracked-map read per walk")
        self.assertEqual(counts.get("stdin-paths"), 1, "one batched hash pass per walk")
        self.assertEqual(counts.get("rev-list"), 1, "one exclusion-only universe pass")
        self.assertEqual(
            counts.get("find-object"), 1,
            "only the in-universe differ keeps its per-rel probe",
        )

    def test_newline_named_source_keeps_unbatched_per_path_decision(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2): a source file whose name contains a newline
        keeps the unbatched per-path decision - the hash batch cannot carry
        an LF-named path, so the batch falls back per-path for that name
        and the decision still lands: the newline-named older vintage
        refuses with its named stderr line, one batch call stands beside
        exactly one per-path argv hash for the excluded name."""
        target = self._target_repo("target")
        nl_rel = "docs/tmp/we\nird.md"
        _write(target / nl_rel, b"nl v0\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "nl v0")
        _write(target / nl_rel, b"nl v2\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "nl v2")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        _write(source / nl_rel, b"nl v0\n")
        _write(source / "docs/tmp/batched-candidate.md", b"batchable new bytes\n")
        manifest = self.root / "migration.json"
        counts: dict[str, int] = {}
        real_run = MODULE.subprocess.run

        def counting_run(argv, *a, **k):
            names = [x if isinstance(x, str) else os.fsdecode(x) for x in argv]
            if "--stdin-paths" in names:
                counts["stdin-paths"] = counts.get("stdin-paths", 0) + 1
            elif "hash-object" in names:
                counts["argv-hash-object"] = counts.get("argv-hash-object", 0) + 1
            return real_run(argv, *a, **k)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(MODULE.subprocess, "run", counting_run):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        self.assertEqual(code, 2, out.getvalue() + err.getvalue())
        self.assertIn(
            f"{nl_rel} is tracked at the target HEAD with different bytes",
            err.getvalue(),
            "the LF-named vintage must keep its named refusal",
        )
        self.assertEqual(counts.get("stdin-paths"), 1)
        self.assertEqual(
            counts.get("argv-hash-object"), 1,
            "the LF-named path must fall back to the per-path argv probe",
        )

    def test_vintage_probe_failure_falls_back_to_legacy_refusal_with_named_warning(self):
        """[class: REPOSITORY_TEST] The failed-vintage-probe shape (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2): a per-rel `git log --find-object` probe failing
        rc != 0 on a differ-from-HEAD path never reads as not-a-vintage -
        the path is reported by name (the WARN) and keeps the legacy
        byte-difference refusal (an offender), so the run still exits 2."""
        target = self._target_repo("target")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V0)
        manifest = self.root / "migration.json"
        real_run = MODULE.subprocess.run

        def failing_probe_run(argv, *a, **k):
            names = [x if isinstance(x, str) else os.fsdecode(x) for x in argv]
            if "log" in names and "--find-object" in names:
                return subprocess.CompletedProcess(
                    argv, 1, "", "simulated vintage probe failure",
                )
            return real_run(argv, *a, **k)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(MODULE.subprocess, "run", failing_probe_run):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        err_text = err.getvalue()
        self.assertEqual(code, 2, out.getvalue() + err_text)
        self.assertIn(
            f"vintage probe failed for {self.REL}", err_text,
            "the failed vintage probe must be reported by name",
        )
        self.assertIn(
            f"{self.REL} is tracked at the target HEAD with different bytes",
            err_text,
            "the legacy byte-difference refusal must stand for that path",
        )

    def test_hash_batch_failure_falls_back_per_path_and_preserves_decisions(self):
        """[class: REPOSITORY_TEST] The failed-hash-batch shape (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 2): `git hash-object --stdin-paths` failing rc != 0
        falls back per-path for every batched path - the decisions stand
        (the older vintage still refuses, exit 2) and no batch-tail path is
        silently skipped (each batched candidate keeps exactly one per-path
        argv hash)."""
        target = self._target_repo("target")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V0)
        _write(source / "docs/tmp/second-artifact.md", b"second new bytes\n")
        manifest = self.root / "migration.json"
        counts: dict[str, int] = {}
        real_run = MODULE.subprocess.run

        def failing_batch_run(argv, *a, **k):
            names = [x if isinstance(x, str) else os.fsdecode(x) for x in argv]
            if "--stdin-paths" in names:
                counts["stdin-paths"] = counts.get("stdin-paths", 0) + 1
                return subprocess.CompletedProcess(
                    argv, 1, b"", b"simulated batch failure",
                )
            if "hash-object" in names:
                counts["argv-hash-object"] = counts.get("argv-hash-object", 0) + 1
            return real_run(argv, *a, **k)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(MODULE.subprocess, "run", failing_batch_run):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        self.assertEqual(code, 2, out.getvalue() + err.getvalue())
        self.assertIn(
            f"{self.REL} is tracked at the target HEAD with different bytes",
            err.getvalue(),
            "the offender decision must survive the batch failure",
        )
        self.assertEqual(counts.get("stdin-paths"), 1)
        self.assertEqual(
            counts.get("argv-hash-object"), 2,
            "both batched candidates must fall back per-path (the vintage "
            "rel and the absent-at-HEAD artifact), never a silent "
            "batch-tail skip",
        )

    # ---- Task 3: post-run guard batching, the nested-target refusal, and
    # the GIT_* sanitization (plan 2026-11-05-closeout-migrate-supplemental-
    # inventory-and-guard-residuals). The batching witness pins the guard's
    # vintage probe batching over the staged blob set composed from the
    # Task 2 helpers (one exclusion-only prefilter pass, the per-rel
    # fallback only where the prefilter cannot exclude) with the offender
    # and prevented sets preserved exactly; the boundary witness refuses a
    # nested target before any guard or copy; the env witnesses inject
    # ambient GIT_* redirection keys through the CLI-subprocess harness's
    # _hermetic_lock_env(root, **extra) so the migrator process itself
    # carries them; the sanitize-failure refusal is fault-injected at the
    # same subprocess-launcher seam class Task 1 named.

    def _run_migrate_with_env(
        self, source: Path, baseline: Path, manifest: Path, target: Path,
        **extra: str,
    ) -> subprocess.CompletedProcess:
        """The CLI-subprocess migrate harness with extra env keys: the
        injection surface for the ambient GIT_* redirection witnesses. The
        migrator process itself carries the injected keys in its environ,
        and every git-deriving subprocess it spawns inherits them unless
        the sanitize helper drops them."""
        return subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH), "migrate",
                "--baseline", str(baseline),
                "--source", str(source),
                "--target", str(target),
                "--manifest", str(manifest),
            ],
            capture_output=True, text=True, cwd=str(self.root),
            env=_hermetic_lock_env(self.root, **extra),
        )

    def _expected_prevented_entry(self, target: Path) -> dict:
        """The restored-from-HEAD prevented_clobbers row the owned-rewind
        end-to-end fixture pins (destination absolute, record_index 0)."""
        return {
            "destination": (Path(target).resolve() / self.REL).as_posix(),
            "action": "restored-from-HEAD",
            "record_index": 0,
        }

    def test_guard_batches_vintage_probe_over_the_staged_blob_set(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3): the post-run guard's vintage probe batches over
        the staged blob set - one exclusion-only `rev-list --objects` pass
        plus the per-rel `_blob_in_head_history` fallback only for the
        candidate the prefilter cannot exclude (a committed vintage is in
        HEAD's history; brand-new staged bytes are not) - with the offender
        and prevented sets preserved exactly: the owned staged rewind still
        restores (prevented == [REL]) and the brand-new bytes on the second
        carried rel stay report-only."""
        target = self._target_repo("target")
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        self._stage_rewind(target, v0_blob)
        fresh_blob = subprocess.run(
            ["git", "-C", str(target), "hash-object", "-w", "--stdin"],
            input=b"brand-new staged bytes never committed\n",
            capture_output=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        ).stdout.decode().strip()
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--add", "--cacheinfo",
             f"100644,{fresh_blob},docs/tmp/ledger.md"],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        counts: dict[str, int] = {}
        real_run = MODULE.subprocess.run

        def counting_run(argv, *a, **k):
            names = [x if isinstance(x, str) else os.fsdecode(x) for x in argv]
            if "log" in names and "--find-object" in names:
                counts["find-object"] = counts.get("find-object", 0) + 1
            if "rev-list" in names:
                counts["rev-list"] = counts.get("rev-list", 0) + 1
            return real_run(argv, *a, **k)

        captured = io.StringIO()
        with mock.patch.object(MODULE.subprocess, "run", counting_run):
            with contextlib.redirect_stdout(captured):
                prevented = MODULE._prevent_tracked_clobbers(
                    target, {self.REL, "docs/tmp/ledger.md"},
                )
        self.assertEqual(
            prevented, [self.REL],
            "the prevented set must be preserved exactly under batching",
        )
        self.assertIn(
            "staged-new-bytes-", captured.getvalue(),
            "brand-new staged bytes on a carried rel must stay report-only",
        )
        self.assertEqual(
            (counts.get("rev-list"), counts.get("find-object")), (1, 1),
            "one rev-list prefilter pass, and the per-rel find-object "
            "fallback only for the committed-vintage candidate the "
            "prefilter cannot exclude - the brand-new blob is never "
            "probed serially",
        )

    def test_guard_divergent_sibling_vintage_stays_report_only(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3): the divergent shape - blob X committed in the
        target under a sibling path, staged on the carried rel with a
        different delivered blob - stays report-only under either batching
        variant: the name-scoped vintage probe misses it (the inherited
        conservative miss), the entry survives untouched, and the prevented
        set stays empty."""
        target = self._target_repo("target")
        sibling_rel = "docs/tmp/sibling-vintage.md"
        _write(target / sibling_rel, b"divergent vintage bytes X\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "sibling vintage X")
        x_blob = self._git(target, "rev-parse", f"HEAD:{sibling_rel}")
        delivered_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self.assertNotEqual(x_blob, delivered_blob)
        self._stage_rewind(target, x_blob)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target, {self.REL}, {self.REL: delivered_blob},
            )
        self.assertEqual(
            prevented, [],
            "a vintage committed under a sibling path and staged on the "
            "carried rel is not a name-scoped rewind: report-only, "
            "nothing prevented",
        )
        self.assertIn(
            "staged-new-bytes-on-a-carried-path", captured.getvalue(),
            "the divergent shape must read as brand-new bytes on a "
            "carried path (report-only) under either batching variant",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"), x_blob,
            "the divergent staged entry must stay untouched",
        )

    def test_guard_mixed_staged_shapes_keep_the_exact_prevented_set(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3, set equality): one walk carrying all four walked
        shapes at once - an owned staged rewind, an owned staged vintage
        equal to the delivered bytes, a foreign staged rewind, and owned
        brand-new staged bytes - produces the exact offender and prevented
        sets: only the owned rewind whose bytes differ from the delivered
        blob restores; every other shape is report-only with its index
        entry preserved."""
        target = self._target_repo("target")
        ledger_rel = "docs/tmp/ledger.md"
        second_rel = "docs/tmp/second.md"
        third_rel = "docs/tmp/third.md"
        v0_blob = self._git(target, "rev-parse", f"HEAD~1:{self.REL}")
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        ledger_v0 = self._git(target, "rev-parse", f"HEAD:{ledger_rel}")
        _write(target / ledger_rel, b"ledger v2 line\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "ledger v2")
        _write(target / second_rel, b"second v0\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "second v0")
        _write(target / second_rel, b"second v2\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "second v2")
        second_v0 = self._git(target, "rev-parse", f"HEAD~1:{second_rel}")
        _write(target / third_rel, b"third committed line\n")
        self._git(target, "add", "-A")
        self._git(target, "commit", "-q", "-m", "third baseline")
        third_head = self._git(target, "rev-parse", f"HEAD:{third_rel}")
        fresh_blob = subprocess.run(
            ["git", "-C", str(target), "hash-object", "-w", "--stdin"],
            input=b"brand-new owned staged bytes\n",
            capture_output=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        ).stdout.decode().strip()
        self._stage_rewind(target, v0_blob)
        self._stage_rewind(target, ledger_v0, ledger_rel)
        self._stage_rewind(target, second_v0, second_rel)
        subprocess.run(
            ["git", "-C", str(target), "update-index", "--add", "--cacheinfo",
             f"100644,{fresh_blob},{third_rel}"],
            capture_output=True, text=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            prevented = MODULE._prevent_tracked_clobbers(
                target,
                {self.REL, ledger_rel, third_rel},
                {self.REL: head_blob, ledger_rel: ledger_v0},
            )
        self.assertEqual(
            prevented, [self.REL],
            "only the owned staged rewind whose bytes differ from the "
            "delivered blob is prevented; the delivered-equal vintage "
            "stays untouched",
        )
        out = captured.getvalue()
        self.assertIn(f"prevented clobber: {self.REL}", out)
        self.assertIn(
            "staged bytes equal the bytes this run delivered", out,
            "the delivered-equal vintage must take the untouched arm",
        )
        self.assertIn(
            "holds a rewound staged vintage this run did not carry", out,
            "the foreign rewind on the second rel must stay report-only",
        )
        self.assertIn(
            "staged-new-bytes-", out,
            "the brand-new staged bytes on the carried third rel must "
            "stay report-only",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"), head_blob,
            "the owned rewind must hold HEAD after the restore",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{ledger_rel}"), ledger_v0,
            "the delivered-equal staged bytes must survive in the index",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{second_rel}"), second_v0,
            "the foreign rewind must survive untouched",
        )
        self.assertEqual(
            self._git(target, "rev-parse", f":{third_rel}"), fresh_blob,
            "the brand-new staged bytes must survive untouched",
        )

    def test_migrate_refuses_nested_target_before_any_guard_or_copy(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3): a target nested inside an enclosing repository
        refuses exit 2 with the named toplevel-mismatch message before any
        guard or copy runs - no merge-lock span, no pre-flight walk, no
        manifest, and no write under the nested target."""
        enclosing = self.root / "enclosing"
        enclosing.mkdir(parents=True)
        subprocess.run(
            ["git", "-C", str(enclosing), "init", "-q"],
            capture_output=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        _write(enclosing / "docs/tmp/ledger.md", b"enclosing committed line\n")
        self._git(enclosing, "add", "-A")
        self._git(enclosing, "commit", "-q", "-m", "enclosing baseline")
        nested = enclosing / "nested-target"
        nested.mkdir()
        self._write_rel(nested, b"peer landing bytes\n")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, self.V2)
        manifest = self.root / "migration.json"
        before = sorted(
            p.relative_to(nested).as_posix() for p in nested.rglob("*")
        )
        proc = self._run_migrate(source, baseline, manifest, nested)
        self.assertEqual(
            proc.returncode, 2,
            f"a nested target must refuse exit 2: {proc.stdout + proc.stderr}",
        )
        self.assertIn(
            "does not equal the resolved target path", proc.stderr,
            "the refusal must carry the named toplevel-mismatch message",
        )
        self.assertIn(
            str(enclosing.resolve()), proc.stderr,
            "the refusal must name the enclosing repository toplevel",
        )
        self.assertNotIn(
            "merge-lock", proc.stderr,
            "the refusal must precede the merge-lock span",
        )
        self.assertNotIn(
            "baseline clobber pre-flight", proc.stderr,
            "the refusal must precede the pre-flight walk",
        )
        self.assertFalse(
            manifest.exists(), "a refused nested target writes no manifest",
        )
        after = sorted(
            p.relative_to(nested).as_posix() for p in nested.rglob("*")
        )
        self.assertEqual(
            after, before, "the refusal must not write under the nested target",
        )
        self.assertEqual(
            (nested / self.REL).read_bytes(), b"peer landing bytes\n",
            "the nested target's own bytes must stay untouched",
        )

    def test_non_git_target_keeps_named_skip_path(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3, green preservation): a plain non-git target keeps
        today's named skip path - no toplevel-mismatch refusal, the named
        merge-lock skip line, and the migration completes."""
        target = self.root / "plain-target"
        target.mkdir(parents=True)
        self._write_rel(target, b"peer landing bytes\n")
        source, baseline = self._source_with_baseline("source", b"corpus v1\n")
        self._write_rel(source, b"corpus v1 + run row\n")
        manifest = self.root / "migration.json"
        proc = self._run_migrate(source, baseline, manifest, target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(
            "merge-lock: skipped (the migration target is not a git "
            "repository", proc.stderr,
            "the named non-repository skip line must keep",
        )
        self.assertNotIn(
            "does not equal the resolved target path", proc.stderr,
            "a non-git target must not take the nested-target refusal",
        )
        self.assertTrue(manifest.exists())

    def test_bogus_git_index_file_cannot_empty_the_prevented_set(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3): a bogus GIT_INDEX_FILE injected into the
        migrator's own environment must never empty the prevented set -
        the sanitize helper drops the key from every git-deriving
        subprocess (the guard's staged-set read included), so the migrate
        completes with the prevented entry recorded against the intended
        target; exit 0 with an empty prevented set is forbidden."""
        target, source, baseline, manifest, _v0 = self._owned_rewind_e2e_fixture()
        proc = self._run_migrate_with_env(
            source, baseline, manifest, target,
            GIT_INDEX_FILE=str(self.root / "bogus-index"),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"prevented clobber: {self.REL}", proc.stdout)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            data["prevented_clobbers"], [self._expected_prevented_entry(target)],
            "the prevented entry must be recorded against the intended "
            "target, never emptied by an injected index redirection",
        )
        self.assertEqual(
            data["prevented_clobber_failures"], [],
            "a bogus GIT_INDEX_FILE must not surface as a staged-set "
            "read failure either - the key never reaches the guard's "
            "subprocesses",
        )

    def test_bogus_git_dir_cannot_empty_the_prevented_set(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3): a bogus GIT_DIR injected into the migrator's own
        environment must not degrade the repository detection into the
        non-repository skip path - the sanitize helper drops the key, both
        guards resolve against the intended target, and the prevented
        entry is recorded; exit 0 with an empty prevented set is
        forbidden."""
        target, source, baseline, manifest, _v0 = self._owned_rewind_e2e_fixture()
        proc = self._run_migrate_with_env(
            source, baseline, manifest, target,
            GIT_DIR=str(self.root / "bogus.git"),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn(
            "merge-lock: skipped", proc.stderr,
            "the detection probe must not degrade to the non-repository "
            "skip path under an injected GIT_DIR",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            data["prevented_clobbers"], [self._expected_prevented_entry(target)],
            "the prevented entry must be recorded against the intended "
            "target, never emptied by an injected GIT_DIR",
        )
        self.assertEqual(data["prevented_clobber_failures"], [])

    def test_ambient_foreign_git_dir_and_work_tree_do_not_degrade_or_refuse(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3): an ambient environment exporting GIT_DIR and
        GIT_WORK_TREE at a valid foreign repository must not degrade any
        git-derived probe and must not trip a false nested-target refusal -
        the migrate completes with every probe resolved against the
        intended target and the prevented entry recorded."""
        target, source, baseline, manifest, _v0 = self._owned_rewind_e2e_fixture()
        foreign = self.root / "foreign-repo"
        foreign.mkdir(parents=True)
        subprocess.run(
            ["git", "-C", str(foreign), "init", "-q"],
            capture_output=True, check=True,
            env=_hermetic_git_env(self.root, **self.GIT_IDENTITY),
        )
        _write(foreign / "stray.md", b"foreign repo committed bytes\n")
        self._git(foreign, "add", "-A")
        self._git(foreign, "commit", "-q", "-m", "foreign baseline")
        proc = self._run_migrate_with_env(
            source, baseline, manifest, target,
            GIT_DIR=str(foreign / ".git"),
            GIT_WORK_TREE=str(foreign),
        )
        self.assertEqual(
            proc.returncode, 0,
            "a valid foreign GIT_DIR/GIT_WORK_TREE must not refuse the "
            f"migrate (no false nested-target refusal): {proc.stdout + proc.stderr}",
        )
        self.assertNotIn(
            "does not equal the resolved target path", proc.stderr,
            "the nested-target refusal must not fire on ambient "
            "redirection keys",
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            data["prevented_clobbers"], [self._expected_prevented_entry(target)],
            "every git-derived probe must resolve against the intended "
            "target: the guard restored the intended target's staged "
            "rewind",
        )
        self.assertEqual(data["prevented_clobber_failures"], [])
        head_blob = self._git(target, "rev-parse", f"HEAD:{self.REL}")
        self.assertEqual(
            self._git(target, "rev-parse", f":{self.REL}"), head_blob,
            "the intended target's index must hold HEAD after the restore",
        )
        self.assertEqual(
            (target / self.REL).read_bytes(), self.V2,
            "the intended target's worktree must hold HEAD after the "
            "restore",
        )

    def test_sanitize_failure_refuses_named_exit_2_before_any_span(self):
        """[class: REPOSITORY_TEST] Safety witness (plan
        2026-11-05-closeout-migrate-supplemental-inventory-and-guard-
        residuals Task 3): the sanitize refusal is reserved for a
        structural impossibility and carries the same fault-injection seam
        class Task 1 named - a _GitEnvSanitizeError raised at the sanitize
        seam refuses exit 2 with the named message and remedy before any
        lock span, guard, or copy."""
        target, source, baseline, manifest, _v0 = self._owned_rewind_e2e_fixture()

        def impossible(*a, **k):
            raise MODULE._GitEnvSanitizeError(
                "simulated structural impossibility constructing the "
                "sanitized git child env"
            )

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(MODULE, "_sanitize_git_child_env", impossible):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = self._migrate_inproc(source, baseline, manifest, target)
        err_text = err.getvalue()
        self.assertEqual(code, 2, out.getvalue() + err_text)
        self.assertIn("refusing the closeout migrate", err_text)
        self.assertIn("simulated structural impossibility", err_text)
        self.assertIn(
            "unset the GIT_* redirection keys", err_text,
            "the refusal must name the remedy",
        )
        self.assertNotIn(
            "merge-lock", err_text,
            "the sanitize refusal must precede the merge-lock span",
        )
        self.assertFalse(
            manifest.exists(), "a sanitize-refused migrate writes no manifest",
        )


class StrandedPointerCheckTest(unittest.TestCase):
    """Warning-only stranded doc-pointer check (entry stranded-doc-pointer-
    edit-orphan): a landing touching a markdown file under
    projects/.ai-playbook/ while docs/AGENTS.md holds uncommitted edits
    reports the would-strand row at file granularity and exits 0; the
    reverse arm reports index edits left uncommitted beside an index
    landing; a body with no index row and a dirty index with no paired
    landing stay informational or silent, and the failure and degraded-
    input arms keep the exit-0 contract."""

    GIT_IDENTITY = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="wcm-stranded-pointer-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.repo = self.root / "proj"
        self.repo.mkdir(parents=True)
        self.env = _hermetic_git_env(self.root, **self.GIT_IDENTITY)
        self._git("init", "-q")
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific |\n")
        self._write("projects/.ai-playbook/python_guidelines.md", "body v1\n")
        self._write("docs/other.md", "unrelated\n")
        self._git("add", "-A")
        self._git("commit", "-qm", "base")
        self.base = self._rev("HEAD")

    def _git(self, *argv: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.repo), *argv],
            capture_output=True, text=True, env=self.env, check=True,
        )

    def _rev(self, ref: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", ref],
            capture_output=True, text=True, env=self.env, check=True,
        )
        return proc.stdout.strip()

    def _write(self, rel: str, text: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _land_body_edit(self) -> str:
        self._write("projects/.ai-playbook/python_guidelines.md", "body v2\n")
        self._git("add", "projects/.ai-playbook/python_guidelines.md")
        self._git("commit", "-qm", "land body edit")
        return self._rev("HEAD")

    def _run_check(self, *extra: str) -> tuple[int, str, str]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "check-stranded-pointers",
             "--repo", str(self.repo), "--base", self.base, *extra],
            capture_output=True, text=True, cwd=str(self.root),
            env=self.env,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_forward_orphan_warns_and_exits_zero(self):
        landing = self._land_body_edit()
        # The companion index-row edit stays uncommitted in the primary.
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (updated for #41) |\n")
        rc, out, err = self._run_check("--landing", landing)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("WARN: stranded-pointer-check", out)
        self.assertIn("would-strand row", out)
        self.assertIn("python_guidelines.md landed in", out)
        self.assertIn("1 would-strand row(s)", out)

    def test_clean_landing_reports_zero_without_warn(self):
        landing = self._land_body_edit()
        rc, out, err = self._run_check("--landing", landing)
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("WARN", out)
        self.assertIn("0 would-strand row(s)", out)

    def test_reverse_index_dirt_beside_index_landing_warns(self):
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (row landed) |\n")
        self._git("add", "docs/AGENTS.md")
        self._git("commit", "-qm", "land index row")
        landing = self._rev("HEAD")
        # Further index edits miss the landing and sit uncommitted.
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (row landed; stray edit) |\n")
        rc, out, err = self._run_check("--landing", landing)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("row edits must ride their own landing change", out)
        self.assertIn("1 would-strand row(s)", out)

    def test_body_without_index_row_is_informational_only(self):
        self._write("projects/.ai-playbook/new_guidelines.md", "brand new body\n")
        self._git("add", "projects/.ai-playbook/new_guidelines.md")
        self._git("commit", "-qm", "land new body")
        landing = self._rev("HEAD")
        rc, out, err = self._run_check("--landing", landing)
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("WARN: stranded-pointer-check", out)
        self.assertIn("no docs/AGENTS.md index row references it", out)
        self.assertIn("1 informational line(s)", out)

    def test_index_dirt_without_paired_landing_is_inert(self):
        # An unrelated landing over a dirty index: no guideline body and no
        # index in the audited changed set (the index dirt is uncommitted,
        # so the diff probe never sees it), and bare index dirt pairs with
        # no landing - the check stays inert rather than warning.
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (unrelated dirt) |\n")
        self._write("docs/other.md", "unrelated v2\n")
        self._git("add", "docs/other.md")
        self._git("commit", "-qm", "land unrelated")
        other_landing = self._rev("HEAD")
        rc, out, err = self._run_check("--base", self.base, "--landing", other_landing)
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("WARN: stranded-pointer-check", out)
        self.assertIn("0 would-strand row(s)", out)

    def test_changed_paths_override_skips_the_diff_probe(self):
        self._land_body_edit()
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (updated for #41) |\n")
        rc, out, err = self._run_check(
            "--changed", "projects/.ai-playbook/python_guidelines.md",
        )
        self.assertEqual(rc, 0, out + err)
        self.assertIn("would-strand row", out)
        self.assertIn("1 would-strand row(s)", out)

    def test_probe_failure_warns_and_exits_zero(self):
        landing = self._land_body_edit()
        rc, out, err = self._run_check("--base", "nosuchref", "--landing", landing)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("changed-set probe failed", err)
        self.assertNotIn("would-strand row(s)", out)

    def test_absent_index_file_is_informational(self):
        (self.repo / "docs/AGENTS.md").unlink()
        self._git("add", "-A")
        self._git("commit", "-qm", "remove index")
        no_index_base = self._rev("HEAD")
        self._write("projects/.ai-playbook/python_guidelines.md", "body v2\n")
        self._git("add", "projects/.ai-playbook/python_guidelines.md")
        self._git("commit", "-qm", "land body edit")
        landing = self._rev("HEAD")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "check-stranded-pointers",
             "--repo", str(self.repo), "--base", no_index_base,
             "--landing", landing],
            capture_output=True, text=True, cwd=str(self.root),
            env=self.env,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("WARN: stranded-pointer-check", proc.stdout)
        self.assertIn("no docs/AGENTS.md index row references it", proc.stdout)
        self.assertIn("1 informational line(s)", proc.stdout)

    def test_staged_dirt_shape_still_warns(self):
        landing = self._land_body_edit()
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (staged edit) |\n")
        self._git("add", "docs/AGENTS.md")
        rc, out, err = self._run_check("--landing", landing)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("WARN: stranded-pointer-check", out)
        self.assertIn("1 would-strand row(s)", out)

    def test_no_base_no_changed_prints_usage_hint(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "check-stranded-pointers",
             "--repo", str(self.repo)],
            capture_output=True, text=True, cwd=str(self.root),
            env=self.env,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("nothing to audit", proc.stderr)
        self.assertNotIn("would-strand row(s)", proc.stdout)

    def test_override_pin_discriminates_probe_fallback(self):
        # Nothing committed after base, so the diff probe yields an empty
        # changed set: the WARN can only come from the explicit --changed
        # override, and a mutant that ignores --changed prints 0 and fails.
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (updated for #41) |\n")
        rc, out, err = self._run_check(
            "--base", self.base, "--landing", "HEAD",
            "--changed", "projects/.ai-playbook/python_guidelines.md",
        )
        self.assertEqual(rc, 0, out + err)
        self.assertIn("WARN: stranded-pointer-check", out)
        self.assertIn("1 would-strand row(s)", out)

    def test_head_default_landing_resolves_short_sha(self):
        self._land_body_edit()
        self._write("docs/AGENTS.md",
                    "# Index\n\n| `python_guidelines.md` | Python-specific (updated for #41) |\n")
        rc, out, err = self._run_check("--landing", "HEAD")
        self.assertEqual(rc, 0, out + err)
        short_proc = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, env=self.env, check=True,
        )
        self.assertIn(f"landed in {short_proc.stdout.strip()}", out)
        self.assertNotIn("landed in HEAD ", out)


class BranchRecordedLandingCloseoutTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] The recorded-landing closeout proofs (plan
    2026-11-04-agent-resource-cleanup-disposition Task 1): the closeout
    migration manifest's branch record carries the landing identity (the
    recorded start commit, the landing commit, and the touched path set
    measured from that start at transfer time), so the gate judges the
    branch's authored delta from the recorded start instead of the current
    merge base and authorizes a completed branch whose landing is masked by
    destination drift, while any unproven authored delta and every legacy
    manifest keep today's retain-and-report verdict."""

    PLAN_REL = "docs/history/plans/2026-10-08-x.md"
    RECORD_REL = ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md"
    PLAN_BODY = (
        b"# Plan\n\nPlan review record: "
        b".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md\n"
    )

    def _seed_drifted_landing(self, unlanded: bool = False) -> tuple[Path, str, str]:
        """The drifted-base completed-plan shape: the branch commits its
        delta (optionally one path that never lands), the destination lands
        the delta in one squash commit and then drifts on, and the landing
        commit stays unreachable from the destination tip. The manifest at
        the derived gate path records the landing identity beside the
        verified migrated row. Returns (manifest path, recorded start
        commit, branch tip)."""
        reviews = self.primary / ".ai-playbook/reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        _write(reviews / "2026-10-08-plan-review-x-exec-r1.md", b"r1\n")
        _write(self.primary / self.PLAN_REL, self.PLAN_BODY)
        self._commit_all(self.primary, "plan bytes at the plans root")
        start = self._git(self.primary, "rev-parse", "HEAD").stdout.strip()
        _write(self.worktree / "feature.txt", b"work\n")
        if unlanded:
            _write(self.worktree / "unlanded.txt", b"not landed\n")
        self._commit_all(self.worktree, "work: branch delta")
        tip = self._branch_oid("wt-run")
        # One squash landing commit on the destination: the archive move
        # plus the landed file (a squash landing touches every file its
        # branch touched), then post-landing destination drift.
        (self.primary / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
        self._git(self.primary, "mv", self.PLAN_REL, "docs/history/plans/completed/2026-10-08-x.md")
        _write(self.primary / "feature.txt", b"work\n")
        self._commit_all(self.primary, "land: squash (archive move + feature)")
        _write(self.primary / "README.md", b"post-landing drift\n")
        self._commit_all(self.primary, "drift: post-landing destination edit")
        self.assertNotEqual(
            self._git(
                self.primary, "merge-base", "--is-ancestor", tip, "HEAD", check=False
            ).returncode,
            0,
            "fixture precondition: the landing commit must be unreachable "
            "from the destination tip",
        )
        # The gate reads the run's plan copy in the worktree for its owned
        # citations; the landed bytes live in the primary tree.
        _write(self.worktree / self.PLAN_REL, self.PLAN_BODY)
        manifest_dir = self.primary / "docs/tmp/execute-plan/x"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "closeout-migration.json"
        touched = ["feature.txt"] + (["unlanded.txt"] if unlanded else [])
        manifest_path.write_text(
            json.dumps(
                {
                    "migrated": [
                        {
                            "source": self.RECORD_REL,
                            "destination": self.RECORD_REL,
                            "verified": True,
                        }
                    ],
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [
                        {
                            "branch": "wt-run",
                            "source": str(self.worktree),
                            "start_commit": start,
                            "landing_commit": tip,
                            "landing_touched": touched,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return manifest_path, start, tip

    def test_drifted_landing_deletes_through_recorded_identity(self):
        # [class: REPOSITORY_TEST] The drifted-base false positive (plan
        # 2026-11-04-agent-resource-cleanup-disposition Task 1): a
        # completed-plan branch whose tip tree equals its recorded landing
        # commit's tree, with the landing commit unreachable from the
        # destination tip and the landing identity recorded in the closeout
        # migration manifest, deletes through the closeout adjudication -
        # the recorded landing identity is the proof, and no retention
        # reason is reported.
        self._seed_drifted_landing()
        tip = self._branch_oid("wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(
            f"branch-closeout: branch wt-run exact-tree-accounted at {tip} "
            "(the tip tree equals the recorded landing commit",
            out,
        )
        self.assertIn(f"expected OID {tip}", out)
        self.assertIn(
            f"branch-disposition: branch=wt-run "
            f"disposition=exact-tree-accounted oid={tip}",
            out,
        )
        self.assertNotIn("branch-closeout: preserve branch wt-run", out)
        self.assertNotIn("legacy evidence only", out)

    def test_quoted_nonascii_touched_path_retains_when_dropped(self):
        # [class: REPOSITORY_TEST] The quoted-path fail-open fix (plan
        # 2026-11-04-agent-resource-cleanup-disposition r1 F1): a
        # landing_touched entry stored in git's C-quote form (a non-ASCII
        # path, the pre-"-z" recording shape) must resolve at proof time -
        # when the destination dropped that authored path the proof must
        # retain the branch with the unaccounted reason, never authorize
        # deletion through a both-absent-equal misread of the quoted form.
        manifest_path, start, tip = self._seed_drifted_landing()
        _write(self.worktree / "caf\u00e9.txt", b"accented work\n")
        self._commit_all(self.worktree, "work: accented delta")
        tip = self._branch_oid("wt-run")
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        record["branch"][0]["landing_commit"] = tip
        record["branch"][0]["landing_touched"] = [
            "feature.txt",
            '"caf\\303\\251.txt"',
        ]
        manifest_path.write_text(
            json.dumps(record), encoding="utf-8"
        )
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertIn("branch-closeout: preserve branch wt-run", out)
        self.assertIn(
            "branch content absent at the destination: caf\u00e9.txt", out
        )
        self.assertNotIn("exact-tree-accounted", out)

    def test_unlanded_authored_delta_retains_with_unaccounted_reason(self):
        # [class: REPOSITORY_TEST] The guard direction (plan
        # 2026-11-04-agent-resource-cleanup-disposition Task 1): the
        # branch's authored delta measured from its recorded start commit
        # contains a path absent at the destination, so the adjudication
        # retains the branch with the unaccounted reason naming the path,
        # never a deletion authorization.
        self._seed_drifted_landing(unlanded=True)
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertIn("branch-closeout: preserve branch wt-run", out)
        self.assertIn(
            "branch content absent at the destination: unlanded.txt", out
        )
        self.assertIn(
            "branch-disposition: branch=wt-run disposition=retained oid=", out
        )
        self.assertIn(
            "branch: preserve wt-run and report it in the closeout record",
            out,
        )

    def test_legacy_manifest_without_recorded_start_keeps_retain_and_report(self):
        # Compatibility (plan 2026-11-04-agent-resource-cleanup-disposition
        # Task 1): a branch with no recorded start commit and no exact-tree
        # landing proof keeps today's retain-and-report verdict - the
        # fallback is retention, never guessed ancestry.
        self._seed_migration_manifest(landed=True)
        _write(self.worktree / "unlanded.txt", b"not landed\n")
        self._commit_all(self.worktree, "work: not landed anywhere")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertIn("branch-closeout: preserve branch wt-run", out)
        self.assertIn("no ancestry or exact-tree proof", out)
        self.assertIn(
            "branch-disposition: branch=wt-run disposition=retained oid=", out
        )
        self.assertIn(
            "branch: preserve wt-run and report it in the closeout record; "
            "delete only the worktree",
            out,
        )


class BranchRecordLandingIdentityTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] The landing-identity record at transfer time
    (plan 2026-11-04-agent-resource-cleanup-disposition Task 1): a closeout
    migrate run from a git worktree into the git primary records the branch
    record's start commit (the merge base with the destination tip), the
    landing commit (the branch tip), and the touched path set measured from
    that start, so the gate's landing proof reads recorded evidence instead
    of walking only destination-reachable history."""

    def setUp(self) -> None:
        super().setUp()
        # In-process migrate runs resolve the lock script and merge-lock root
        # from this process's environment: pin them hermetically for the
        # whole class (WorktreeCloseoutTest's posture).
        lock_root = Path(tempfile.mkdtemp(prefix="wcm-landing-lock-"))
        self.addCleanup(shutil.rmtree, lock_root, ignore_errors=True)
        pins = _hermetic_lock_env(lock_root)
        self._saved_lock_env = {key: os.environ.get(key) for key in pins}
        os.environ.update(pins)
        self.addCleanup(self._restore_lock_env)

    def _restore_lock_env(self) -> None:
        for key, value in self._saved_lock_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_migrate_records_landing_identity_in_branch_record(self):
        _write(self.worktree / "feature.txt", b"work\n")
        self._commit_all(self.worktree, "work: branch feature")
        _write(self.worktree / "docs/tmp/run-artifact.md", b"artifact\n")
        baseline = self.root / "closeout-baseline.json"
        code, _stdout, stderr = _run_cli(
            "capture", "--out", str(baseline), "--dirs", "docs/tmp",
            cwd=self.worktree,
        )
        self.assertEqual(code, 0, stderr)
        manifest = self.root / "closeout-migration.json"
        self.assertEqual(_migrate(self.worktree, self.primary, baseline, manifest), 0)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        record = data["branch"][-1]
        self.assertEqual(record["branch"], "wt-run")
        self.assertEqual(record["landing_commit"], self._branch_oid("wt-run"))
        self.assertEqual(
            record["start_commit"],
            self._git(self.primary, "merge-base", "wt-run", "HEAD").stdout.strip(),
        )
        self.assertEqual(record["landing_touched"], ["feature.txt"])


class AuthoringStrandBranchRetryTest(NoCharterFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] The authoring-strand manifest binding and the
    branch-only retry it enables (plan
    2026-11-04-agent-resource-cleanup-disposition Task 1): the no-charter
    stand-down pass appends the strand's branch identity row to the primary
    slug home's existing migration manifest (the surface the execution
    strand already uses), so the branch-only retry after the worktree
    removal reads that manifest's identity row and no second evidence
    surface is created."""

    EXEC_BRANCH = "wt-exec-2026-10-28-no-charter-demo"
    EXEC_RECORD_REL = ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md"

    def _seed_execution_manifest(self) -> Path:
        """The primary slug home's existing migration manifest: the
        execution strand's branch record plus one verified migrated row
        whose destination is present under the target."""
        _write(self.primary / self.EXEC_RECORD_REL, b"r1\n")
        manifest_dir = self.primary / "docs/tmp/execute-plan" / self.SLUG
        manifest_dir.mkdir(parents=True, exist_ok=True)
        path = manifest_dir / "closeout-migration.json"
        path.write_text(
            json.dumps(
                {
                    "migrated": [
                        {
                            "source": self.EXEC_RECORD_REL,
                            "destination": self.EXEC_RECORD_REL,
                            "verified": True,
                        }
                    ],
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [
                        {
                            "branch": self.EXEC_BRANCH,
                            "source": str(self.root / "proj-wt-exec"),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return path

    def _authoring_own_manifest(self) -> Path:
        """The witnessed loss: the authoring strand's own ignored manifest,
        worktree-local, lost with the removed worktree."""
        path = (
            self.worktree / "docs/tmp/execute-plan" / self.SLUG
            / "closeout-migration.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "migrated": [],
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [
                        {"branch": self.branch, "source": str(self.worktree)}
                    ],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_removed_authoring_worktree_retry_reads_slug_home_identity(self):
        self._seed_clean()
        slug_home_manifest = self._seed_execution_manifest()
        own_manifest = self._authoring_own_manifest()
        code, out, err = self._run_gate("--migration-manifest", str(own_manifest))
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        # The pass appended the strand's identity row to the primary slug
        # home's existing manifest; the execution row is intact (the
        # manifest stays append-only, no second evidence surface).
        data = json.loads(slug_home_manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            [row["branch"] for row in data["branch"]],
            [self.EXEC_BRANCH, self.branch],
        )
        identity = data["branch"][-1]
        self.assertEqual(identity["start_commit"], self.start_commit)
        self.assertEqual(identity["landing_commit"], self.start_commit)
        self.assertEqual(identity["landing_touched"], [])
        self.assertNotIn("record_index", data["branch"][0])
        # The worktree is removed; the strand's own ignored manifest is lost
        # with it - the slug home manifest is the surviving evidence.
        self._git(self.primary, "worktree", "remove", "--force", str(self.worktree))
        self.assertFalse(self.worktree.exists())
        # The branch-only retry reads the slug home manifest's identity row:
        # the binding resolves the authoring branch and the adjudication
        # proceeds to the ancestry-accounted deletion authorization.
        retry_plan = self.primary / "docs/history/plans/2026-10-01-retry-operand.md"
        _write(
            retry_plan,
            b"# Plan\n\nPlan review record: "
            b".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md\n",
        )
        code, out, _err = _run_cli(
            "gate-removal",
            "--plan", str(retry_plan),
            "--target", str(self.primary),
            "--branch", self.branch,
            "--migration-manifest", str(slug_home_manifest),
            cwd=self.primary,
        )
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertNotIn("exact-branch identity mismatch", out)
        self.assertIn(
            f"branch-disposition: branch={self.branch} "
            "disposition=ancestry-accounted",
            out,
        )


def _branch_dispositions(out: str) -> list[dict]:
    """The machine-parseable branch dispositions a gate-removal run printed
    (the _branch_disposition_line shape), parsed so the rehearsal's
    completion-claim inventory rides the machinery's own adjudication output
    rather than test-side guesses. ``reasons`` is the line's trailing field
    and keeps its embedded spaces."""
    rows: list[dict] = []
    for line in out.splitlines():
        prefix = "branch-disposition: "
        if not line.startswith(prefix):
            continue
        head, sep, reasons = line[len(prefix):].partition(" reasons=")
        row: dict = {}
        for token in head.split(" "):
            key, eq, value = token.partition("=")
            if eq:
                row[key] = value
        if sep:
            row["reasons"] = reasons
        rows.append(row)
    return rows


class MultiResourceDispositionRehearsalTest(_BranchCloseoutFixture, unittest.TestCase):
    """[class: REPOSITORY_TEST] The acceptance rehearsal of the multi-resource
    disposition contract (plan 2026-11-04-agent-resource-cleanup-disposition
    Task 3; the contract lives in `## Resource cleanup disposition` in
    agents/skills/self-heal/SKILL.md, the adjudication steps in
    _gate_branch_closeout behind the gate-removal pass): one temporary
    repository holding a landed branch (its landing masked by destination
    drift, the landing identity recorded per Task 1), an unmerged branch, and
    an active foreign worktree. The disposition steps produce one verified
    outcome per resource - the landed branch deletes only through the
    recorded-landing proof, the unmerged branch keeps a named retention
    carrying the exact unmerged work, and the active foreign worktree stays
    retained and untouched - and the completion-claim inventory assembled
    from those dispositions enumerates every in-scope resource read from the
    run and claim records and matches each resource's verified end state."""

    LANDED_PLAN_REL = "docs/history/plans/2026-10-08-x.md"
    LANDED_RECORD_REL = ".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md"
    UNMERGED_PLAN_REL = "docs/history/plans/2026-10-09-y.md"
    UNMERGED_RECORD_REL = ".ai-playbook/reviews/2026-10-09-plan-review-y-exec-r1.md"
    FOREIGN_CLAIM_REL = "docs/tmp/execution-claims/2026-11-04-foreign-run.md"
    LANDED_PLAN_BODY = (
        b"# Plan\n\nPlan review record: "
        b".ai-playbook/reviews/2026-10-08-plan-review-x-exec-r1.md\n"
    )
    UNMERGED_PLAN_BODY = (
        b"# Plan\n\nPlan review record: "
        b".ai-playbook/reviews/2026-10-09-plan-review-y-exec-r1.md\n"
    )

    def _seed_rehearsal(self) -> tuple[str, str, str]:
        """The three-resource fixture. The landed strand follows the Task 1
        drifted-base shape: the branch commits its delta, the destination
        lands the delta in one squash commit and then drifts on, the landing
        commit stays unreachable from the destination tip, and the strand's
        manifest records the landing identity. The unmerged strand is a
        second run worktree whose branch commits one path that never lands
        anywhere, with the same recorded identity (what a real migrate run
        records at transfer time). The foreign strand is a registered
        worktree owned by another run's live claim record, holding one
        committed path of its own. Run and claim records are written after
        every git commit so `git add -A` never sweeps a runtime record into
        history. Returns (landed tip, unmerged tip, foreign tip)."""
        reviews = self.primary / ".ai-playbook/reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        # Landed strand: plan bytes, branch delta, squash landing, drift.
        _write(reviews / Path(self.LANDED_RECORD_REL).name, b"r1\n")
        _write(self.primary / self.LANDED_PLAN_REL, self.LANDED_PLAN_BODY)
        self._commit_all(self.primary, "plan bytes for the landed strand")
        landed_start = self._git(self.primary, "rev-parse", "HEAD").stdout.strip()
        _write(self.worktree / "feature.txt", b"work\n")
        self._commit_all(self.worktree, "work: landed branch delta")
        landed_tip = self._branch_oid("wt-run")
        # One squash landing commit on the destination: the archive move
        # plus the landed file (a squash landing touches every file its
        # branch touched), then post-landing destination drift.
        (self.primary / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
        self._git(
            self.primary, "mv", self.LANDED_PLAN_REL,
            "docs/history/plans/completed/2026-10-08-x.md",
        )
        _write(self.primary / "feature.txt", b"work\n")
        self._commit_all(self.primary, "land: squash (archive move + feature)")
        _write(self.primary / "README.md", b"post-landing drift\n")
        self._commit_all(self.primary, "drift: post-landing destination edit")
        self.assertNotEqual(
            self._git(
                self.primary, "merge-base", "--is-ancestor", landed_tip,
                "HEAD", check=False,
            ).returncode,
            0,
            "fixture precondition: the landing commit must be unreachable "
            "from the destination tip",
        )
        # Unmerged strand: a second run worktree whose branch commits one
        # path the destination never receives.
        _write(reviews / Path(self.UNMERGED_RECORD_REL).name, b"r1\n")
        _write(self.primary / self.UNMERGED_PLAN_REL, self.UNMERGED_PLAN_BODY)
        self._commit_all(self.primary, "plan bytes for the unmerged strand")
        unmerged_start = self._git(self.primary, "rev-parse", "HEAD").stdout.strip()
        self.unmerged_worktree = self.root / "proj-wt-unmerged"
        self._git(
            self.primary, "worktree", "add", "-q", "-b", "wt-unmerged",
            str(self.unmerged_worktree),
        )
        _write(self.unmerged_worktree / "notes.txt", b"unmerged work\n")
        self._commit_all(self.unmerged_worktree, "work: notes never land anywhere")
        unmerged_tip = self._branch_oid("wt-unmerged")
        self.assertNotEqual(
            self._git(
                self.primary, "merge-base", "--is-ancestor", unmerged_tip,
                "HEAD", check=False,
            ).returncode,
            0,
            "fixture precondition: the unmerged branch must carry work the "
            "destination never receives",
        )
        # Foreign strand: a registered worktree owned by another run's live
        # claim record, holding one committed path of its own.
        self.foreign_worktree = self.root / "proj-wt-foreign"
        self._git(
            self.primary, "worktree", "add", "-q", "-b", "wt-foreign",
            str(self.foreign_worktree),
        )
        _write(self.foreign_worktree / "foreign.txt", b"foreign active work\n")
        self._commit_all(self.foreign_worktree, "work: foreign run's active delta")
        foreign_tip = self._branch_oid("wt-foreign")
        # The gate reads each run's own plan copy in its worktree for the
        # owned citations; the primary's copies stay where the strands left
        # them (the landed plan is archived, the unmerged plan still sits at
        # the plans root because that strand never completed).
        _write(self.worktree / self.LANDED_PLAN_REL, self.LANDED_PLAN_BODY)
        _write(self.unmerged_worktree / self.UNMERGED_PLAN_REL, self.UNMERGED_PLAN_BODY)
        # The run and claim records (the runtime-neutral owner sources the
        # contract binds dispositions to).
        self.foreign_claim = self.primary / self.FOREIGN_CLAIM_REL
        _write(
            self.foreign_claim,
            (
                "session: foreign-run\n"
                f"worktree: {self.foreign_worktree}\n"
                "branch: wt-foreign\n"
                "updated: 2026-11-04T12:00:00Z\n"
            ).encode("utf-8"),
        )
        self.landed_manifest = self._write_strand_manifest(
            "x", "wt-run", self.worktree, landed_start, landed_tip,
            ["feature.txt"], self.LANDED_RECORD_REL,
        )
        self.unmerged_manifest = self._write_strand_manifest(
            "y", "wt-unmerged", self.unmerged_worktree, unmerged_start,
            unmerged_tip, ["notes.txt"], self.UNMERGED_RECORD_REL,
        )
        return landed_tip, unmerged_tip, foreign_tip

    def _write_strand_manifest(
        self,
        slug: str,
        branch: str,
        source: Path,
        start: str,
        tip: str,
        touched: list[str],
        record_rel: str,
    ) -> Path:
        """One strand's closeout migration manifest at its derived slug home:
        one verified migrated row present under the target plus the branch
        record carrying the Task 1 landing identity (start commit, landing
        commit, touched set measured from that start)."""
        manifest = (
            self.primary / "docs/tmp/execute-plan" / slug / "closeout-migration.json"
        )
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {
                    "migrated": [
                        {
                            "source": record_rel,
                            "destination": record_rel,
                            "verified": True,
                        }
                    ],
                    "renamed": [],
                    "skipped": [],
                    "failed": [],
                    "branch": [
                        {
                            "branch": branch,
                            "source": str(source),
                            "start_commit": start,
                            "landing_commit": tip,
                            "landing_touched": touched,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return manifest

    def _run_gate_for(self, worktree: Path, plan_rel: str) -> tuple[int, str, str]:
        """One gate-removal adjudication of one strand's worktree: the same
        pass the owning closeout runs before any removal."""
        return _run_cli(
            "gate-removal",
            "--plan", str(worktree / plan_rel),
            "--target", str(self.primary),
            "--worktree", str(worktree),
            cwd=worktree,
        )

    def _local_branches(self) -> set[str]:
        """The branch-ref inventory read from its runtime-neutral source."""
        out = self._git(
            self.primary, "for-each-ref", "--format=%(refname:short)", "refs/heads/"
        ).stdout
        return {line.strip() for line in out.splitlines() if line.strip()}

    def _registered_worktree_branches(self) -> dict[str, str]:
        """The worktree registration inventory read from its runtime-neutral
        source (the porcelain worktree list): resolved worktree path ->
        branch. The paths resolve because the fixture's mkdtemp root sits
        behind a macOS /var symlink the porcelain output never carries."""
        entries: dict[str, str] = {}
        path: str | None = None
        for line in self._git(
            self.primary, "worktree", "list", "--porcelain"
        ).stdout.splitlines():
            if line.startswith("worktree "):
                path = str(Path(line[len("worktree "):]).resolve())
            elif line.startswith("branch refs/heads/") and path is not None:
                entries[path] = line[len("branch refs/heads/"):]
        return entries

    def test_rehearsal_produces_one_disposition_per_resource_and_the_claim_matches(self):
        # [class: REPOSITORY_TEST] The multi-resource rehearsal (plan
        # 2026-11-04-agent-resource-cleanup-disposition Task 3): one cleanup
        # pass over a landed branch, an unmerged branch, and an active
        # foreign worktree ends with one verified outcome per resource, a
        # completion-claim inventory that enumerates the full in-scope set,
        # and every foreign or active resource preserved - the only removal
        # is the landed branch, and only because the recorded-landing proof
        # authorizes it at the recorded expected OID.
        landed_tip, unmerged_tip, foreign_tip = self._seed_rehearsal()

        # Resource 1 adjudication: the landed branch, through the
        # recorded-landing proof (Task 1). The verdict below is the only
        # removal authorization the rehearsal acts on.
        code, landed_out, _err = self._run_gate_for(
            self.worktree, self.LANDED_PLAN_REL
        )
        self.assertEqual(code, 0, landed_out)
        self.assertEqual(landed_out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn(
            f"branch-closeout: branch wt-run exact-tree-accounted at "
            f"{landed_tip} (the tip tree equals the recorded landing "
            "commit's tree and the recorded landing's touched set is "
            "present at the destination",
            landed_out,
        )
        self.assertIn(f"expected OID {landed_tip}", landed_out)
        landed_rows = _branch_dispositions(landed_out)
        self.assertEqual(len(landed_rows), 1)
        self.assertEqual(landed_rows[0]["branch"], "wt-run")
        self.assertEqual(landed_rows[0]["disposition"], "exact-tree-accounted")
        self.assertEqual(landed_rows[0]["oid"], landed_tip)
        # No other resource leaked into this adjudication.
        self.assertNotIn("wt-unmerged", landed_out)
        self.assertNotIn("wt-foreign", landed_out)

        # The sanctioned removal: the worktree removal the gate's own line
        # authorizes, then the branch deletion at the recorded expected OID
        # only after the quiesce re-check confirms the ref still sits there.
        self.assertIn(
            f"removal: git worktree remove --force "
            f"{shlex.quote(str(self.worktree))}",
            landed_out,
        )
        self._git(self.primary, "worktree", "remove", "--force", str(self.worktree))
        self.assertEqual(
            self._git(self.primary, "rev-parse", "--verify", "wt-run").stdout.strip(),
            landed_tip,
        )
        self._git(self.primary, "branch", "-D", "wt-run")

        # Resource 2 adjudication: the unmerged branch. The adjudication
        # itself passes (retention is a verdict, never a gate failure); the
        # disposition carries the named retention with the exact unmerged
        # work, and the closeout report names the preserve decision.
        code, unmerged_out, _err = self._run_gate_for(
            self.unmerged_worktree, self.UNMERGED_PLAN_REL
        )
        self.assertEqual(code, 0, unmerged_out)
        self.assertEqual(unmerged_out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("branch-closeout: preserve branch wt-unmerged", unmerged_out)
        self.assertIn(
            "branch content absent at the destination: notes.txt", unmerged_out
        )
        self.assertIn(
            "branch: preserve wt-unmerged and report it in the closeout "
            "record; delete only the worktree",
            unmerged_out,
        )
        unmerged_rows = _branch_dispositions(unmerged_out)
        self.assertEqual(len(unmerged_rows), 1)
        self.assertEqual(unmerged_rows[0]["branch"], "wt-unmerged")
        self.assertEqual(unmerged_rows[0]["disposition"], "retained")
        self.assertEqual(unmerged_rows[0]["oid"], unmerged_tip)
        # No other resource leaked into this adjudication.
        self.assertNotIn("wt-run", unmerged_out)
        self.assertNotIn("wt-foreign", unmerged_out)

        # Resource 3: the active foreign worktree. No gate run touches it -
        # the cleanup binds it to its live claim record and routes its
        # disposition to the owning authorized closeout; the survival
        # assertions at the end verify it stayed untouched.

        # The completion-claim inventory, assembled from the dispositions
        # above plus the owner-bound foreign resource: the contract's
        # vocabulary, one entry per in-scope resource.
        inventory: dict[tuple[str, str], dict] = {}
        manifest_for_branch = {
            "wt-run": self.landed_manifest,
            "wt-unmerged": self.unmerged_manifest,
        }
        for rows, resource in (
            (landed_rows, ("branch", "wt-run")),
            (unmerged_rows, ("branch", "wt-unmerged")),
        ):
            row = rows[0]
            if row["disposition"] in ("exact-tree-accounted", "ancestry-accounted"):
                inventory[resource] = {
                    "disposition": "verified-removal",
                    "evidence": (
                        f"{row['disposition']} at the proven OID {row['oid']} "
                        "through the recorded-landing proof"
                    ),
                }
            else:
                marker = "branch content absent at the destination: "
                unmerged_work = [
                    token.split(marker, 1)[1].strip()
                    for token in row.get("reasons", "").split("; ")
                    if marker in token
                ]
                # Named retention must name the exact unmerged work.
                self.assertEqual(unmerged_work, ["notes.txt"])
                inventory[resource] = {
                    "disposition": "named-retention",
                    "owner": (
                        "branch record in "
                        f"{manifest_for_branch[row['branch']].name} (its own "
                        "run's migration manifest)"
                    ),
                    "unmerged_work": unmerged_work,
                }
        inventory[("worktree", self.foreign_worktree.name)] = {
            "disposition": "named-retention",
            "owner": (
                f"live claim record ({self.FOREIGN_CLAIM_REL}); continuation "
                "through the owning authorized closeout"
            ),
        }

        # The claim is valid only when it matches the full inventory: every
        # in-scope resource read from the run and claim records (the
        # runtime-neutral sources) appears exactly once, so a partial result
        # can never read as complete.
        in_scope: set[tuple[str, str]] = set()
        for manifest_path in (self.landed_manifest, self.unmerged_manifest):
            record = json.loads(manifest_path.read_text(encoding="utf-8"))
            in_scope.add(("branch", record["branch"][-1]["branch"]))
        claim_fields: dict[str, str] = {}
        for line in self.foreign_claim.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition(": ")
            if sep:
                claim_fields[key] = value
        in_scope.add(("worktree", Path(claim_fields["worktree"]).name))
        self.assertEqual(set(inventory), in_scope)
        self.assertEqual(len(inventory), 3)

        # The claim matches each resource's verified end state, confirmed
        # from the inventory sources (branch refs, worktree registrations,
        # bytes on disk).
        branches_after = self._local_branches()
        registrations_after = self._registered_worktree_branches()
        # wt-run: verified removal - ref and registration both gone.
        self.assertNotIn("wt-run", branches_after)
        self.assertNotIn(str(self.worktree.resolve()), registrations_after)
        # wt-unmerged: named retention held - ref unmoved at its tip and the
        # registration intact; the rehearsal removed nothing for the
        # retained resource.
        self.assertEqual(self._branch_oid("wt-unmerged"), unmerged_tip)
        self.assertEqual(
            registrations_after.get(str(self.unmerged_worktree.resolve())),
            "wt-unmerged",
        )
        self.assertTrue(
            (self.unmerged_worktree / "notes.txt").is_file(),
            "the unmerged strand's work must survive the adjudication",
        )
        # wt-foreign: retained untouched - registration, ref, committed
        # bytes, and the owner claim record all survive the whole rehearsal.
        self.assertEqual(
            registrations_after.get(str(self.foreign_worktree.resolve())),
            "wt-foreign",
        )
        self.assertEqual(self._branch_oid("wt-foreign"), foreign_tip)
        self.assertEqual(
            (self.foreign_worktree / "foreign.txt").read_bytes(),
            b"foreign active work\n",
        )
        self.assertTrue(self.foreign_claim.is_file())


if __name__ == "__main__":
    unittest.main()
