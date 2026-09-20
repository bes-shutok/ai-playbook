#!/usr/bin/env python3
"""Tests for the worktree closeout migration tool (worktree_closeout_migrate.py)."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "worktree_closeout_migrate.py"

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
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
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
    def test_capture_records_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs/reviews/notes.md", b"review notes\n")
            _write(root / "docs/tmp/scratch.md", b"scratch pad\n")
            baseline = root / "baseline.json"
            code, _stdout, stderr = _run_cli("capture", "--out", str(baseline), cwd=root)
            self.assertEqual(code, 0, stderr)
            data = json.loads(baseline.read_text(encoding="utf-8"))
            self.assertEqual(data["dirs"], ["docs/reviews", "docs/tmp"])
            files = data["files"]
            self.assertIn("docs/reviews/notes.md", files)
            self.assertIn("docs/tmp/scratch.md", files)
            self.assertEqual(
                files["docs/reviews/notes.md"],
                hashlib.sha256(b"review notes\n").hexdigest(),
            )
            self.assertEqual(
                files["docs/tmp/scratch.md"],
                hashlib.sha256(b"scratch pad\n").hexdigest(),
            )

    def test_migrate_copies_new_and_modified_with_checksum_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / "docs/reviews/keep.md", b"unchanged\n")
            _write(source / "docs/reviews/edit.md", b"old edit\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / "docs/reviews/edit.md", b"new edit\n")
            _write(source / "docs/reviews/fresh.md", b"fresh file\n")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            self.assertEqual((target / "docs/reviews/edit.md").read_bytes(), b"new edit\n")
            self.assertEqual((target / "docs/reviews/fresh.md").read_bytes(), b"fresh file\n")
            self.assertFalse((target / "docs/reviews/keep.md").exists())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            migrated = {entry["source"] for entry in data["migrated"]}
            self.assertEqual(migrated, {"docs/reviews/edit.md", "docs/reviews/fresh.md"})

    def test_migrate_skips_identical_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / "docs/reviews/same.md", b"v1\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / "docs/reviews/same.md", b"v2\n")
            _write(target / "docs/reviews/same.md", b"v2\n")
            os.utime(target / "docs/reviews/same.md", (1000, 1000))
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            stat = os.stat(target / "docs/reviews/same.md")
            self.assertEqual(stat.st_mtime, 1000, "identical target was rewritten")
            self.assertFalse(
                any(path.name.startswith("same.wt-") for path in (target / "docs/reviews").iterdir())
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            skipped = {entry["source"] for entry in data.get("skipped", [])}
            self.assertIn("docs/reviews/same.md", skipped)

    def test_migrate_renames_on_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / "docs/reviews/collide.md", b"incoming content\n")
            _write(target / "docs/reviews/collide.md", b"existing different\n")
            _write(target / "docs/reviews/collide.wt-9.md", b"prior run copy\n")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest, suffix="9")
            self.assertEqual(code, 0)
            self.assertEqual(
                (target / "docs/reviews/collide.md").read_bytes(),
                b"existing different\n",
            )
            self.assertEqual(
                (target / "docs/reviews/collide.wt-9.md").read_bytes(),
                b"prior run copy\n",
                "pre-existing .wt- copy was overwritten",
            )
            self.assertEqual(
                (target / "docs/reviews/collide.wt-9-2.md").read_bytes(),
                b"incoming content\n",
            )
            data = json.loads(manifest.read_text(encoding="utf-8"))
            renamed = {entry["source"] for entry in data.get("renamed", [])}
            self.assertIn("docs/reviews/collide.md", renamed)
            renamed_entry = next(
                entry
                for entry in data["renamed"]
                if entry["source"] == "docs/reviews/collide.md"
            )
            self.assertTrue(renamed_entry["destination"].endswith("collide.wt-9-2.md"))

    def test_migrate_preserves_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir(parents=True)
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / "docs/reviews/real.md", b"linked content\n")
            os.symlink("real.md", source / "docs/reviews/link.md")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            dst_link = target / "docs/reviews/link.md"
            self.assertTrue(dst_link.is_symlink(), "symlink was dereferenced into a regular file")
            self.assertEqual(os.readlink(dst_link), "real.md")
            self.assertTrue((target / "docs/reviews/real.md").is_file())

    def test_migrate_missing_baseline_fails_loud(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / "docs/reviews/only.md", b"content\n")
            missing = root / "does-not-exist.json"
            manifest = root / "manifest.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, missing, manifest)
            self.assertNotEqual(code, 0)
            self.assertIn(str(missing), stderr.getvalue())
            self.assertFalse((target / "docs/reviews/only.md").exists())

    def test_migrate_markdown_manifest_fails_loud_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            _write(source / "docs/reviews/keep.md", b"unchanged\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / "docs/reviews/fresh.md", b"fresh file\n")
            manifest = root / "manifest.json"
            manifest.write_text("# session manifest\n", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, target, baseline, manifest)
            self.assertNotEqual(code, 0)
            self.assertIn(str(manifest), stderr.getvalue())
            self.assertFalse(
                (target / "docs/reviews/fresh.md").exists(),
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
            _write(source / "docs/reviews/victim.md", b"original bytes\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / "docs/reviews/victim.md", b"modified bytes\n")
            manifest = root / "manifest.json"
            original_copy = MODULE._copy_file

            def tampered_copy(src, dst):
                dst.write_bytes(b"tampered bytes\n")

            MODULE._copy_file = tampered_copy
            try:
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = _migrate(source, target, baseline, manifest)
            finally:
                MODULE._copy_file = original_copy
            self.assertNotEqual(code, 0)
            self.assertIn("verification failed", stderr.getvalue())
            self.assertEqual(
                (source / "docs/reviews/victim.md").read_bytes(),
                b"modified bytes\n",
                "source file was moved instead of copied",
            )

    def test_migrate_noop_when_source_equals_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            _write(source / "docs/reviews/solo.md", b"content\n")
            baseline = root / "baseline.json"
            _capture_baseline(source, baseline)
            _write(source / "docs/reviews/solo.md", b"changed content\n")
            manifest = root / "manifest.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = _migrate(source, source, baseline, manifest)
            self.assertEqual(code, 0)
            self.assertIn("no-op", stderr.getvalue().lower())
            self.assertEqual((source / "docs/reviews/solo.md").read_bytes(), b"changed content\n")
            self.assertFalse(
                any(path.name.startswith("solo.wt-") for path in (source / "docs/reviews").iterdir())
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
            _write(source / "docs/reviews/one.md", b"one\n")
            _write(source / "docs/tmp/two.md", b"two\n")
            manifest = root / "manifest.json"
            code = _migrate(source, target, baseline, manifest)
            self.assertEqual(code, 0)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            migrated = {entry["source"]: entry for entry in data["migrated"]}
            self.assertEqual(set(migrated), {"docs/reviews/one.md", "docs/tmp/two.md"})
            for entry in migrated.values():
                self.assertTrue(entry["verified"])
                self.assertEqual(
                    hashlib.sha256(Path(entry["destination"]).read_bytes()).hexdigest(),
                    hashlib.sha256((source / entry["source"]).read_bytes()).hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
