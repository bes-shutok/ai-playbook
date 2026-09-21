#!/usr/bin/env python3
"""Tests for the origins-closure gate (check_plan_origins_closed.py).

Five fixture cases mirror the plan's Task 1 checkboxes: all-closed passes,
an open straggler fails (and warns under --warn), a closed-in-place item
passes, a plan with no origins block passes trivially, and an unrelated
archived plan's stragglers never block the plan under test (the corpus
warn arm reports them while still exiting 0). Fixtures live under mkdtemp
with explicit teardown; the script runs as a subprocess against a scratch
repo root, so no network and no real repo state are involved.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "check_plan_origins_closed.py"

# Scratch facts file: TOML keys the gate resolves, mirroring the real
# facts document's shape (fenced toml block, trailing-slash values).
FACTS_BODY = (
    "```toml\n"
    'backlog_dir = "docs/history/backlog/"\n'
    'backlog_completed_dir = "docs/history/backlog/completed/"\n'
    'plans_completed_dir = "docs/plans/completed/"\n'
    "```\n"
)

ALPHA = "2026-09-01-origin-alpha.md"
BETA = "2026-09-01-origin-beta.md"
GAMMA = "2026-09-01-origin-gamma.md"


class PlanOriginsClosedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="origins-gate-fixture-"))
        # Explicit teardown: rmtree runs on every exit path, success or
        # failure, via addCleanup.
        self.addCleanup(shutil.rmtree, self.root, True)
        self.backlog = self.root / "docs" / "history" / "backlog"
        self.completed = self.backlog / "completed"
        self.plans_dir = self.root / "docs" / "plans" / "completed"
        for directory in (
            self.completed,
            self.plans_dir,
            self.root / ".ai-playbook",
        ):
            directory.mkdir(parents=True)
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # Fixture helpers
    # ------------------------------------------------------------------

    def _write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _open_top(self, name: str) -> Path:
        # The bullet-bold shape mirrors the real corpus (a top-level item
        # may declare its status as ``- **Status:** open``).
        return self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\n- **Status:** open\n\nbody\n",
        )

    def _closed_top(self, name: str) -> Path:
        return self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\nStatus: closed (fixed by the fixture plan)\n\nbody\n",
        )

    def _archived(self, name: str) -> Path:
        return self._write(
            self.completed / name,
            f"# Backlog: {name}\n\nStatus: done\n\nbody\n",
        )

    def _plan(self, name: str, origins: list[str] | None) -> Path:
        lines = ["# Plan: fixture", ""]
        if origins:
            if len(origins) == 1:
                lines.append(
                    f"Backlog origins (scope of record): `{origins[0]}`."
                )
            else:
                lines.append(
                    f"Backlog origins (scope of record): `{origins[0]}`,"
                )
                for origin in origins[1:-1]:
                    lines.append(f"`{origin}`,")
                lines.append(f"`{origins[-1]}`.")
            lines.append("")
        lines.extend(["## Tasks", "", "- [ ] fixture task", ""])
        return self._write(self.plans_dir / name, "\n".join(lines))

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--repo-root", str(self.root)]
            + list(args),
            capture_output=True,
            text=True,
            timeout=60,
        )

    # ------------------------------------------------------------------
    # The five named cases
    # ------------------------------------------------------------------

    def test_all_closed_passes(self) -> None:
        self._archived(ALPHA)
        self._archived(BETA)
        plan = self._plan(
            "2026-09-22-fixture-all-closed.md",
            [
                f"docs/history/backlog/{ALPHA}",
                f"docs/history/backlog/{BETA}",
            ],
        )
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("straggler", proc.stdout)

    def test_open_straggler_fails(self) -> None:
        self._archived(ALPHA)
        self._open_top(BETA)
        plan = self._plan(
            "2026-09-22-fixture-straggler.md",
            [
                f"docs/history/backlog/{ALPHA}",
                f"docs/history/backlog/{BETA}",
            ],
        )
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"straggler: {BETA}", proc.stdout)
        # The closed sibling origin is never listed; the gate names the
        # stragglers of the plan under test only.
        self.assertNotIn(ALPHA, proc.stdout)
        # --warn downgrades the same verdict to warn-and-exit-0.
        warned = self._run("--plan", str(plan), "--warn")
        self.assertEqual(warned.returncode, 0, warned.stdout + warned.stderr)
        self.assertIn("warning", warned.stdout)
        self.assertIn(BETA, warned.stdout)
        # Explicit facts-resolution arguments override the facts file and
        # keep the verdict.
        explicit = self._run(
            "--plan",
            str(plan),
            "--backlog-dir",
            str(self.backlog),
            "--completed-dir",
            str(self.completed),
        )
        self.assertEqual(explicit.returncode, 1, explicit.stdout + explicit.stderr)
        self.assertIn(f"straggler: {BETA}", explicit.stdout)

    def test_closed_status_in_place_passes(self) -> None:
        self._closed_top(ALPHA)
        plan = self._plan(
            "2026-09-22-fixture-closed-in-place.md",
            [f"docs/history/backlog/{ALPHA}"],
        )
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("straggler", proc.stdout)

    def test_no_origins_block_trivial(self) -> None:
        plan = self._plan("2026-09-22-fixture-no-origins.md", None)
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no origins block", proc.stdout)

    def test_unrelated_plans_stragglers_do_not_block(self) -> None:
        clean = self._plan("2026-09-22-fixture-clean.md", None)
        self._open_top(GAMMA)
        self._plan(
            "2026-09-22-fixture-unrelated.md",
            [f"docs/history/backlog/{GAMMA}"],
        )
        # Plan mode gates only the plan under test: the unrelated archived
        # plan's open origin neither fails nor names the clean run.
        proc = self._run("--plan", str(clean))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("straggler", proc.stdout)
        self.assertNotIn(GAMMA, proc.stdout)
        # The corpus-wide scan warns on the unrelated origin and exits 0
        # (the maintenance survey's warn arm owns this surface).
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stderr)
        self.assertIn("warning", corpus.stdout)
        self.assertIn(GAMMA, corpus.stdout)


if __name__ == "__main__":
    unittest.main()
