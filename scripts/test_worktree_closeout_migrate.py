#!/usr/bin/env python3
"""Tests for the worktree closeout migration tool (worktree_closeout_migrate.py)."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

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


def _hermetic_lock_env(root: Path, **extra: str) -> dict[str, str]:
    """Fixture hermeticity (plan 2026-10-10-done-closeout-lock-span Task 1):
    pin the merge-lock root and poll interval into the fixture tmp tree and
    the done-lock script at the repo-local copy, so a fixture's lock activity
    never touches the host lock home."""
    env = os.environ.copy()
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
            code, _stdout, stderr = _run_cli("capture", "--out", str(baseline), cwd=root)
            self.assertEqual(code, 0, stderr)
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
        code, out, err = self._run_gate(plan, "--worktree", "../ai-playbook-wt-x")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        removal_lines = [ln for ln in out.strip().splitlines() if "git worktree remove" in ln]
        self.assertEqual(removal_lines, ["removal: git worktree remove --force ../ai-playbook-wt-x"])

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
        # never a vacuous pass; the line names the absent header label.
        plan = self._plan("# Plan\n\nNo review rounds.\n")
        code, out, err = self._run_gate(plan)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: fail")
        self.assertIn("empty owned set", out)
        self.assertIn("Plan review record", out)
        self.assertIn("worktree_closeout_migrate.py migrate", out)

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

    def test_refuse_absolute_label_citation_to_existing_file_outside_primary_home(self):
        # The F1 loss class: an absolute label citation whose file exists
        # OUTSIDE the primary home (here the worktree's own staging copy)
        # must be refused, never verified through the pathlib join discard
        # that would land the check on the cited file itself; the refusal
        # renders repo-relative or basename, never the absolute path, and
        # carries the migrate remedy.
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
        self.assertIn("worktree_closeout_migrate.py migrate", out)

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
        self.assertIn("worktree_closeout_migrate.py migrate", out)

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
        self.assertIn("worktree_closeout_migrate.py migrate", out)

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
        self.assertIn("worktree_closeout_migrate.py migrate", out)

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
                gate_class, _evidence = MODULE._run_gate_on_twin(
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
        env = os.environ.copy()
        env.update(self.GIT_IDENTITY)
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
        env = os.environ.copy()
        for var in self.SWEEP_ENV_VARS:
            env.pop(var, None)
        # Hermetic lock pins (plan 2026-10-10-done-closeout-lock-span Task 1):
        # the merge-lock root lives in the fixture tmp tree and the done-lock
        # script is the repo-local copy; --apply fixtures override the root
        # through hold_env after these defaults.
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
        self.assertIn(f"report {self._porcelain_path(eligible)}: removal eligible", proc.stdout)
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
            f"report {registered}: removal eligible (report-only mode; re-run with --apply)",
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
        # content, both clean staging surfaces, so the chain proceeds to
        # removal eligibility.
        path = self.eligible_candidate()
        self.assertTrue(
            (Path(path) / ".ai-playbook/reviews/2026-10-01-alpha-r1.md").is_file()
        )
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {self._porcelain_path(path)}: removal eligible", proc.stdout)

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

    def test_sweep_stale_detached_registration_skip(self):
        path = self.add_worktree("loose", detach=True)
        registered = self._porcelain_path(path)
        shutil.rmtree(path)
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {registered}: stale detached registration", proc.stdout)

    def test_sweep_detached_on_disk_worktree_skip(self):
        self.seed_twin("2026-10-01-alpha.md")
        path = self.add_worktree("loose", detach=True)
        self.write_candidate_plan(path, "2026-10-01-alpha.md")
        proc = self.run_sweep()
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"report {self._porcelain_path(path)}: detached HEAD worktree", proc.stdout)

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
        self.assertIn(f"report {self._porcelain_path(path)}: removal eligible", proc.stdout)

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
        self.assertIn(f"report {second_registered}: removal eligible", proc.stdout)
        self.assertIn(first_registered, self._registered_paths())
        self.assertIn(second_registered, self._registered_paths())

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

    def test_sweep_apply_removes_on_disk_candidate_full_pass(self):
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"remove {registered}", proc.stdout)
        self.assertFalse(Path(path).exists(), "the worktree survived the removal")
        self.assertNotIn(registered, self._registered_paths())
        self.assertTrue(self._branch_gone("wt-alpha"))
        self.assertEqual(list((self.primary / "docs/tmp").glob("sweep-twin-*")), [], "twin temp file leaked")
        self.assertEqual(list(self.merge_lock_root.iterdir()), [], "the merge lock was not released")

    def test_sweep_apply_removes_stale_registration_scoped(self):
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
        shutil.rmtree(path)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"remove {registered}", proc.stdout)
        self.assertNotIn(registered, self._registered_paths())
        admin = self.primary / ".git" / "worktrees" / Path(registered).name
        self.assertFalse(admin.exists(), "the administrative dir survived the scoped release")
        self.assertTrue(self._branch_gone("wt-alpha"))
        self.assertFalse(Path(path).exists(), "the stale release recreated a tree")

    def test_sweep_stale_siblings_drain_together(self):
        first = self.eligible_candidate(slug="one", basename="2026-10-01-one.md")
        second = self.eligible_candidate(slug="two", basename="2026-10-01-two.md")
        first_registered = self._porcelain_path(first)
        second_registered = self._porcelain_path(second)
        shutil.rmtree(first)
        shutil.rmtree(second)
        proc = self.run_sweep("--apply", env_overrides=self.hold_env())
        self.assertOutcome(proc, 0, "pass")
        self.assertIn(f"remove {first_registered}", proc.stdout)
        self.assertIn(f"remove {second_registered}", proc.stdout)

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
        path = self.eligible_candidate()
        registered = self._porcelain_path(path)
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
        self.assertTrue(Path(path).is_dir(), "a removal ran while the merge lock was held")
        self.assertIn(registered, self._registered_paths())

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


class GateRemovalBranchCloseoutTest(unittest.TestCase):
    """[class: REPOSITORY_TEST] Exact-branch closeout witnesses (plan
    done-closeout-ceremony-friction Task 3): a real git fixture pair of a
    primary checkout and a run worktree whose migration manifest records the
    branch at transfer time, exercising the removable, preserve (shared
    branch), preserve (unlanded work), and identity-mismatch arms."""

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
        env = os.environ.copy()
        env.update(self.GIT_IDENTITY)
        proc = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env
        )
        if check and proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc

    def _commit_all(self, repo: Path, message: str) -> None:
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-q", "-m", message)

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
        manifest_dir = self.primary / "docs/tmp/execute-plan/2026-10-08-x"
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

    def test_landed_branch_adjudicated_removable(self):
        # Ordinary completed closeout: the records verify, the manifest binds
        # the worktree to wt-run, the migrated artifact exists under the
        # target, and the branch's work is accounted (content-scope match);
        # the gate passes with the removable verdict and the deletable
        # branch command.
        self._seed_migration_manifest(landed=True)
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], "OUTCOME: pass")
        self.assertIn("branch-closeout: branch wt-run removable", out)
        # The fixture's shape is squash-accounted (the branch commit is
        # merge-unreachable), so the proof-conditioned deletion instruction
        # is the content-scope -D arm, never the plain -d that would refuse.
        self.assertIn("git branch -D", out)
        self.assertIn("proof-checked force delete", out)

    def test_shared_branch_preserved(self):
        # A live sibling worktree on the same branch: the gate still passes
        # (the records and identity verify) but the branch verdict is
        # preserve, naming the sibling.
        self._seed_migration_manifest(landed=True)
        sibling = self.root / "proj-wt-sibling"
        # Git refuses a second checkout of one branch by default; the
        # duplicated-branch porcelain state this arm models is real but
        # reachable only through the operator override flag.
        self._git(self.primary, "worktree", "add", "-q", "-b", "wt-temp-sib", str(sibling))
        self._git(sibling, "checkout", "-q", "--ignore-other-worktrees", "wt-run")
        code, out, _err = self._run_gate()
        self.assertEqual(code, 0, out)
        self.assertIn("branch-closeout: preserve branch wt-run", out)
        self.assertIn("live worktree(s)", out)
        self.assertIn(str(sibling), out)

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


if __name__ == "__main__":
    unittest.main()
