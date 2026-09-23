#!/usr/bin/env python3
"""Tests for the backlog duplicate sweep (docs_branch_backlog_dedupe.py)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "docs_branch_backlog_dedupe.py"


def _load_dedupe_module():
    # Collection-time pin: loading the module by path while it is still
    # missing makes the RED run fail at collection with a loud module
    # error instead of skipping every arm silently.
    spec = importlib.util.spec_from_file_location(
        "docs_branch_backlog_dedupe_under_test", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE_UNDER_TEST = _load_dedupe_module()

BASE_ITEM = (
    "# 2026-09-10 Example backlog item\n\n"
    "Status: done\n\n"
    "Durable rule one: verify the archive twin before removing a stale copy.\n\n"
    "Durable rule two: surface deeper mismatches instead of deleting them.\n"
)

# Same body as BASE_ITEM with only the Status line changed: the bodies
# match once Status lines are dropped, but the Status values differ, so
# the pair is a surface-and-keep case, never a removal. When both copies
# carry the same variant, Status values are equal and the pair sweeps.
STATUS_VARIANT = BASE_ITEM.replace("Status: done", "Status: in-progress")

# Same Status line as BASE_ITEM but a drifted body line: a deeper
# mismatch that must be surfaced, never deleted.
BODY_MISMATCH = (
    "# 2026-09-10 Example backlog item\n\n"
    "Status: done\n\n"
    "Durable rule one: verify the archive twin before removing a stale copy.\n\n"
    "Durable rule two: the top-level copy drifted from the archived twin here.\n"
)


class BacklogDedupeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.wt = Path(self._tmp.name) / "wt"
        self.backlog = self.wt / "docs" / "history" / "backlog"
        (self.backlog / "completed").mkdir(parents=True)
        (self.backlog / "deferred").mkdir(parents=True)
        (self.backlog / "rejected").mkdir(parents=True)

    def _write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _top(self, name: str) -> Path:
        return self.backlog / name

    def _completed(self, name: str) -> Path:
        return self.backlog / "completed" / name

    def _deferred(self, name: str) -> Path:
        return self.backlog / "deferred" / name

    def _rejected(self, name: str) -> Path:
        return self.backlog / "rejected" / name

    def _sweep(self) -> tuple[int, str, str]:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--worktree-root",
                str(self.wt),
                "--backlog-dir",
                "docs/history/backlog",
            ],
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def _snapshot(self) -> dict[str, bytes]:
        return {
            str(p.relative_to(self.backlog)): p.read_bytes()
            for p in sorted(self.backlog.rglob("*"))
            if p.is_file()
        }

    def test_removes_top_level_when_archived_twin_identical(self) -> None:
        self._write(self._top("2026-09-10-example.md"), BASE_ITEM)
        self._write(self._completed("2026-09-10-example.md"), BASE_ITEM)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertFalse(self._top("2026-09-10-example.md").exists())
        self.assertTrue(self._completed("2026-09-10-example.md").exists())
        self.assertEqual(
            self._completed("2026-09-10-example.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )
        self.assertIn("REMOVED", out)
        self.assertIn("2026-09-10-example.md", out)

    def test_status_only_difference_keeps_both(self) -> None:
        # Inverted by the status-match fix: a re-opened item whose top
        # copy differs from its archived twin only in the Status value is
        # a legitimate live copy, so both copies survive and the sweep
        # reports an informational surface-and-keep line, not the
        # mismatch warning and not a removal.
        self._write(self._top("2026-09-10-example.md"), STATUS_VARIANT)
        self._write(self._completed("2026-09-10-example.md"), BASE_ITEM)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("KEPT", out)
        self.assertIn("2026-09-10-example.md", out)
        self.assertNotIn("REMOVED", out)
        self.assertEqual(
            self._top("2026-09-10-example.md").read_text(encoding="utf-8"),
            STATUS_VARIANT,
        )
        self.assertEqual(
            self._completed("2026-09-10-example.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )

    def test_matching_status_removed(self) -> None:
        # Equal bodies and equal Status values: the stale top-level copy
        # is removed even when the shared Status is not the BASE_ITEM
        # default, so the status agreement requirement does not narrow
        # the existing sweep.
        self._write(self._top("2026-09-10-example.md"), STATUS_VARIANT)
        self._write(self._completed("2026-09-10-example.md"), STATUS_VARIANT)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertFalse(self._top("2026-09-10-example.md").exists())
        self.assertTrue(self._completed("2026-09-10-example.md").exists())
        self.assertEqual(
            self._completed("2026-09-10-example.md").read_text(encoding="utf-8"),
            STATUS_VARIANT,
        )
        self.assertIn("REMOVED", out)
        self.assertIn("2026-09-10-example.md", out)

    def test_keeps_and_surfaces_on_body_mismatch(self) -> None:
        self._write(self._top("2026-09-10-example.md"), BODY_MISMATCH)
        self._write(self._completed("2026-09-10-example.md"), BASE_ITEM)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertIn("WARN", err)
        self.assertIn("2026-09-10-example.md", err)
        self.assertNotIn("REMOVED", out)
        self.assertEqual(
            self._top("2026-09-10-example.md").read_text(encoding="utf-8"),
            BODY_MISMATCH,
        )
        self.assertEqual(
            self._completed("2026-09-10-example.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )

    def test_no_twin_left_untouched(self) -> None:
        self._write(self._top("2026-09-10-example.md"), BASE_ITEM)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(
            self._top("2026-09-10-example.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )

    def test_deferred_twin_same_rules(self) -> None:
        # Removal arm: an identical deferred twin sweeps the top copy.
        self._write(self._top("a-item.md"), BASE_ITEM)
        self._write(self._deferred("a-item.md"), BASE_ITEM)
        # Surfacing arm: a deferred twin with a drifted body is kept.
        self._write(self._top("b-item.md"), BODY_MISMATCH)
        self._write(self._deferred("b-item.md"), BASE_ITEM)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertFalse(self._top("a-item.md").exists())
        self.assertEqual(
            self._deferred("a-item.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )
        self.assertIn("REMOVED", out)
        self.assertIn("a-item.md", out)
        self.assertIn("WARN", err)
        self.assertIn("b-item.md", err)
        self.assertEqual(
            self._top("b-item.md").read_text(encoding="utf-8"),
            BODY_MISMATCH,
        )
        self.assertEqual(
            self._deferred("b-item.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )

    def test_rejected_twin_same_rules(self) -> None:
        # A rejected backlog twin follows the same matching and mismatch
        # rules as completed/deferred: a top-level copy matching its
        # rejected twin in body and Status is a stale duplicate of the
        # archive move and is removed from the overlay; a Status-only
        # difference or a drifted body is retained and surfaced, never
        # deleted.
        # Removal arm: an identical rejected twin sweeps the top copy.
        self._write(self._top("r-item.md"), BASE_ITEM)
        self._write(self._rejected("r-item.md"), BASE_ITEM)
        # Surfacing arm: a rejected twin with a drifted body is kept.
        self._write(self._top("s-item.md"), BODY_MISMATCH)
        self._write(self._rejected("s-item.md"), BASE_ITEM)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertFalse(self._top("r-item.md").exists())
        self.assertEqual(
            self._rejected("r-item.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )
        self.assertIn("REMOVED", out)
        self.assertIn("r-item.md", out)
        self.assertIn("WARN", err)
        self.assertIn("s-item.md", err)
        self.assertEqual(
            self._top("s-item.md").read_text(encoding="utf-8"),
            BODY_MISMATCH,
        )
        self.assertEqual(
            self._rejected("s-item.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )

    def test_idempotent_second_run_noop(self) -> None:
        self._write(self._top("c-item.md"), BASE_ITEM)
        self._write(self._completed("c-item.md"), BASE_ITEM)
        first_code, _first_out, first_err = self._sweep()
        self.assertEqual(first_code, 0)
        self.assertEqual(first_err, "")
        self.assertFalse(self._top("c-item.md").exists())
        before = self._snapshot()
        second_code, second_out, second_err = self._sweep()
        self.assertEqual(second_code, 0)
        self.assertEqual(second_err, "")
        self.assertNotIn("REMOVED", second_out)
        self.assertEqual(self._snapshot(), before)

    def test_always_warn_and_continue(self) -> None:
        # The mismatched pair comes first in sorted order so the sweep
        # must warn and keep going, then still sweep the matching pair.
        self._write(self._top("mismatch-item.md"), BODY_MISMATCH)
        self._write(self._completed("mismatch-item.md"), BASE_ITEM)
        self._write(self._top("match-item.md"), BASE_ITEM)
        self._write(self._deferred("match-item.md"), BASE_ITEM)
        code, out, err = self._sweep()
        self.assertEqual(code, 0)
        self.assertIn("WARN", err)
        self.assertIn("mismatch-item.md", err)
        self.assertFalse(self._top("match-item.md").exists())
        self.assertEqual(
            self._deferred("match-item.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )
        self.assertEqual(
            self._top("mismatch-item.md").read_text(encoding="utf-8"),
            BODY_MISMATCH,
        )
        self.assertEqual(
            self._completed("mismatch-item.md").read_text(encoding="utf-8"),
            BASE_ITEM,
        )
        self.assertIn("match-item.md", out)


if __name__ == "__main__":
    unittest.main()
