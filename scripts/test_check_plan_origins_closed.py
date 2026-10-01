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
    'plans_completed_dir = "docs/history/plans/completed/"\n'
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
        self.plans_dir = self.root / "docs" / "history" / "plans" / "completed"
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

    def _rejected_top(self, name: str) -> Path:
        # The rejected archive twin: moved under rejected/ with the
        # decision recorded in the status line.
        return self._write(
            self.backlog / "rejected" / name,
            f"# Backlog: {name}\n\nStatus: rejected (2026-09-23; fixture reason)\n\nbody\n",
        )

    def _plan(
        self, name: str, origins: list[str] | None, body: str = ""
    ) -> Path:
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
        return self._write(
            self.plans_dir / name, "\n".join(lines) + body
        )

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

    def test_rejected_plan_and_backlog_origins_are_closed(self) -> None:
        # An origin moved under the backlog rejected/ archive classifies
        # as closed: the mixed plan fails only on the live open straggler
        # (no live-origin false positive), and a rejected-only origins
        # block passes. A rejected control plan under the plans rejected/
        # directory gates like any plan; its rejected origin passes.
        self._archived(ALPHA)
        self._rejected_top(BETA)
        self._open_top(GAMMA)
        mixed = self._plan(
            "2026-09-22-fixture-rejected-origins.md",
            [
                f"docs/history/backlog/{ALPHA}",
                f"docs/history/backlog/{BETA}",
                f"docs/history/backlog/{GAMMA}",
            ],
        )
        proc = self._run("--plan", str(mixed))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"straggler: {GAMMA}", proc.stdout)
        # The rejected origin is never named: it left the top level
        # through the documented rejected archive.
        self.assertNotIn(BETA, proc.stdout)
        self.assertNotIn(ALPHA, proc.stdout)
        rejected_only = self._plan(
            "2026-09-22-fixture-rejected-only.md",
            [f"docs/history/backlog/{BETA}"],
        )
        proc = self._run("--plan", str(rejected_only))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("straggler", proc.stdout)
        # A plan living under the plans rejected/ archive directory is
        # gated like any plan; its rejected origin stays closed there.
        rejected_plan_dir = self.root / "docs" / "history" / "plans" / "rejected"
        plan_lines = [
            "# Plan: fixture in the rejected archive",
            "",
            f"Backlog origins (scope of record): `docs/history/backlog/{BETA}`.",
            "",
        ]
        rejected_plan_dir.mkdir(parents=True, exist_ok=True)
        (rejected_plan_dir / "2026-09-22-fixture-rejected-plan.md").write_text(
            "\n".join(plan_lines), encoding="utf-8"
        )
        proc = self._run(
            "--plan", str(rejected_plan_dir / "2026-09-22-fixture-rejected-plan.md")
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("straggler", proc.stdout)

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

    # ------------------------------------------------------------------
    # Singular Backlog origin header form (P56 Task 3)
    # ------------------------------------------------------------------
    def _singular_plan(self, name: str, origin: str) -> Path:
        lines = [
            "# Plan: fixture-singular",
            "",
            f"Backlog origin: `{origin}`",
            "",
            "## Tasks",
            "",
            "- [ ] fixture task",
            "",
        ]
        return self._write(self.plans_dir / name, "\n".join(lines))

    def test_singular_origin_line_gates(self) -> None:
        self._open_top(ALPHA)
        plan = self._singular_plan(
            "2026-09-24-fixture-singular-open.md",
            f"docs/history/backlog/{ALPHA}",
        )
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("straggler", proc.stdout)
        self.assertIn(ALPHA, proc.stdout)

    def test_singular_origin_closed_item_passes(self) -> None:
        self._archived(ALPHA)
        plan = self._singular_plan(
            "2026-09-24-fixture-singular-closed.md",
            f"docs/history/backlog/{ALPHA}",
        )
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("1/1 origins closed", proc.stdout)

    def test_singular_origin_non_backlog_path_ignored(self) -> None:
        plan = self._singular_plan(
            "2026-09-24-fixture-singular-nonbacklog.md",
            "docs/reviews/some-review.md",
        )
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no origins block; nothing to verify", proc.stdout)


    # ------------------------------------------------------------------

    # Fold-then-delete consult canaries (P65 Task 4)
    # ------------------------------------------------------------------

    def _migrated_plan(self, name: str, origins: list[str], body: str) -> Path:
        """An archived plan with an origins block plus extra body text
        (e.g. a disposition section or a registry citation)."""
        plan = self._plan(name, origins)
        plan.write_text(plan.read_text(encoding="utf-8") + body, encoding="utf-8")
        return plan

    def _registry(self, rows: list[str]) -> Path:
        table = "\n".join(
            ["| k | src | notes |", "|---|---|---|"] + rows
        )
        return self._write(
            self.root / "docs" / "maintenance" / "document-registry.md",
            table + "\n",
        )

    def test_corpus_scan_resolves_disposition_section_origin(self) -> None:
        self._plan(
            "2026-09-19-fixture-disposition-anchored.md",
            [f"docs/history/backlog/{ALPHA}"],
            "\n## Disposition of migrated backlog items\n\n"
            f"- `docs/history/backlog/{ALPHA}`: folded into this plan; per-item file deleted\n",
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertNotIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_corpus_scan_resolves_registry_migration_audit_origin(self) -> None:
        self._plan(
            "2026-09-19-fixture-registry-anchored.md",
            [f"docs/history/backlog/{ALPHA}"],
            "",
        )
        self._registry(
            [
                f"| alpha | docs/history/backlog/{ALPHA} | "
                "user-approved 2026-09-26: migration audit - folded; per-item file deleted |"
            ]
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertNotIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_registry_consult_row_scoped(self) -> None:
        self._plan(
            "2026-09-19-fixture-row-scoped.md",
            [f"docs/history/backlog/{ALPHA}"],
            "",
        )
        self._registry(
            [
                "| anchor-row | docs/history/backlog/unrelated.md | "
                "user-approved 2026-09-26: migration audit - folded |",
                f"| src-row | docs/history/backlog/{ALPHA} | plain note |",
            ]
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_corpus_scan_still_warns_genuinely_unresolved_origin(self) -> None:
        self._plan(
            "2026-09-19-fixture-genuine-straggler.md",
            [f"docs/history/backlog/{ALPHA}"],
            "",
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_plan_mode_disposition_section_origin_passes(self) -> None:
        self._migrated_plan(
            "2026-09-19-fixture-plan-mode-disposition.md",
            [f"docs/history/backlog/{ALPHA}"],
            "\n## Disposition of migrated backlog items\n\n"
            f"- `docs/history/backlog/{ALPHA}`: folded; per-item file deleted\n",
        )
        proc = self._run(
            "--plan",
            str(self.plans_dir / "2026-09-19-fixture-plan-mode-disposition.md"),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok (1/1 origins closed)", proc.stdout)

    def test_plan_mode_registry_only_origin_still_stragglers(self) -> None:
        self._plan(
            "2026-09-19-fixture-plan-mode-registry-only.md",
            [f"docs/history/backlog/{ALPHA}"],
            "",
        )
        self._registry(
            [
                f"| alpha | docs/history/backlog/{ALPHA} | "
                "user-approved 2026-09-26: migration audit - folded |"
            ]
        )
        proc = self._run(
            "--plan",
            str(self.plans_dir / "2026-09-19-fixture-plan-mode-registry-only.md"),
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("straggler", proc.stdout)

    def test_plan_mode_open_origin_named_in_disposition_still_stragglers(self) -> None:
        self._open_top(ALPHA)
        self._migrated_plan(
            "2026-09-19-fixture-plan-mode-open-disposition.md",
            [f"docs/history/backlog/{ALPHA}"],
            "\n## Disposition of migrated backlog items\n\n"
            f"- `docs/history/backlog/{ALPHA}`: named\n",
        )
        proc = self._run(
            "--plan",
            str(self.plans_dir / "2026-09-19-fixture-plan-mode-open-disposition.md"),
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("straggler", proc.stdout)

    def test_registry_consult_requires_token_and_basename(self) -> None:
        self._plan(
            "2026-09-19-fixture-registry-no-token.md",
            [f"docs/history/backlog/{ALPHA}"],
            "",
        )
        self._registry(
            [
                f"| alpha | docs/history/backlog/{ALPHA} | "
                "plain note without the marker |"
            ]
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_corpus_scan_open_origin_in_audit_cell_still_warns(self) -> None:
        self._open_top(ALPHA)
        self._plan(
            "2026-09-19-fixture-open-audit-cell.md",
            [f"docs/history/backlog/{ALPHA}"],
            "",
        )
        self._registry(
            [
                f"| alpha | docs/history/backlog/{ALPHA} | "
                "user-approved 2026-09-26: migration audit - folded |"
            ]
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_corpus_scan_open_origin_in_disposition_section_still_warns(self) -> None:
        self._open_top(ALPHA)
        self._migrated_plan(
            "2026-09-19-fixture-open-disposition.md",
            [f"docs/history/backlog/{ALPHA}"],
            "\n## Disposition of migrated backlog items\n\n"
            f"- `docs/history/backlog/{ALPHA}`: named\n",
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_prefix_basename_near_miss_does_not_resolve(self) -> None:
        self._plan(
            "2026-09-19-fixture-prefix-near-miss.md",
            [f"docs/history/backlog/{ALPHA}"],
            "\n## Disposition of migrated backlog items\n\n"
            f"- `docs/history/backlog/prefix-{ALPHA}`: a different item\n",
        )
        self._registry(
            [
                f"| row | docs/history/backlog/prefix-{ALPHA} | "
                "user-approved 2026-09-26: migration audit - folded |"
            ]
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertIn(f"{ALPHA} unresolved", corpus.stdout)

    def test_missing_registry_leaves_consult_inert(self) -> None:
        self._plan(
            "2026-09-19-fixture-missing-registry.md",
            [f"docs/history/backlog/{ALPHA}"],
            "",
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stdout)
        self.assertIn(f"{ALPHA} unresolved", corpus.stdout)




class OriginsBlockGrammarTest(unittest.TestCase):
    """Origins-block grammar: blank-line tolerance and the undercount
    warning, exercised through the module parser and the --plan CLI."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="origins-grammar-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.backlog = self.root / "docs" / "history" / "backlog"
        self.completed = self.backlog / "completed"
        self.completed.mkdir(parents=True)
        sys.path.insert(0, str(SCRIPT_PATH.parent))
        import check_plan_origins_closed as gate

        self.gate = gate

    def _plan(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def _archived(self, name: str) -> None:
        (self.completed / name).write_text("# archived\n", encoding="utf-8")

    def test_blank_line_between_header_and_list_tolerated(self):
        self._archived(ALPHA)
        self._archived(BETA)
        text = (
            "Backlog origins (scope of record):\n"
            "\n"
            f"- `{ALPHA}`\n"
            f"- `{BETA}`\n"
            "\n"
            "## Tasks\n"
        )
        names = self.gate.extract_origin_basenames(
            text, self.backlog, self.completed
        )
        self.assertEqual(names, [ALPHA, BETA])

    def test_blank_line_between_bullets_ends_block(self):
        self._archived(ALPHA)
        self._archived(BETA)
        text = (
            "Backlog origins (scope of record):\n"
            f"- `{ALPHA}`\n"
            "\n"
            f"- `{BETA}`\n"
        )
        names = self.gate.extract_origin_basenames(
            text, self.backlog, self.completed
        )
        self.assertEqual(names, [ALPHA])

    def test_dispositions_undercount_warning(self):
        self._archived(ALPHA)
        self._archived(BETA)
        self._archived(GAMMA)
        # The blank line after the first bullet ends the origins block, so
        # the parser sees one origin while the dispositions section lists
        # three; the --plan gate warns naming both counts and exits 0.
        text = (
            "Backlog origins (scope of record):\n"
            f"- `{ALPHA}`\n"
            "\n"
            f"- `{BETA}`\n"
            f"- `{GAMMA}`\n"
            "\n"
            "## Origins dispositions\n\n"
            f"- `{ALPHA}`: routed done\n"
            f"- `{BETA}`: routed done\n"
            f"- `{GAMMA}`: routed done\n"
        )
        plan = self._plan("2026-09-25-fixture-undercount.md", text)
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--repo-root",
                str(self.root),
                "--plan",
                str(plan),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("warning", combined)
        self.assertIn("1", combined)
        self.assertIn("3", combined)


class TestOriginCoverage(unittest.TestCase):
    """The covered classification, the duplicate-origin coverage gate,
    and the mark-covered writer (plan 2026-09-30-origin-coverage)."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="origin-coverage-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.backlog = self.root / "docs" / "history" / "backlog"
        self.completed = self.backlog / "completed"
        self.active = self.root / "docs" / "history" / "plans"
        self.plans_dir = self.active / "completed"
        for directory in (self.completed, self.plans_dir, self.root / ".ai-playbook"):
            directory.mkdir(parents=True)
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )

    def _write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _open_top(self, name: str, status: str = "open") -> Path:
        return self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\nStatus: {status}\n\nbody\n",
        )

    def _rejected_top(self, name: str) -> Path:
        return self._write(
            self.backlog / "rejected" / name,
            f"# Backlog: {name}\n\nStatus: rejected (fixture reason)\n\nbody\n",
        )

    def _archived(self, name: str) -> Path:
        return self._write(
            self.completed / name,
            f"# Backlog: {name}\n\nStatus: done\n\nbody\n",
        )

    def _archived_plan(self, name: str, origin: str) -> Path:
        return self._write(
            self.plans_dir / name,
            f"# Plan: {name}\n\nBacklog origin: docs/history/backlog/{origin}\n",
        )

    def _active_plan(self, name: str, origin: str, header: str | None = None) -> Path:
        text = header if header is not None else (
            f"# Plan: {name}\n\nBacklog origin: docs/history/backlog/{origin}\n"
        )
        return self._write(self.active / name, text)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--repo-root", str(self.root)]
            + list(args),
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_classify_covered_status(self) -> None:
        self._open_top(ALPHA, 'covered (docs/history/plans/2026-01-01-a.md)')
        proc = self._run()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn(f"origin {ALPHA} unresolved", proc.stdout)

    def test_covered_is_not_closed(self) -> None:
        self._open_top(ALPHA, 'covered (docs/history/plans/2026-01-01-a.md)')
        self._active_plan("2026-01-01-a.md", ALPHA)
        self._archived_plan("2026-01-01-old.md", ALPHA)
        proc = self._run()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("closed in place", proc.stdout)
        self.assertNotIn("no longer top-level", proc.stdout)

    def _check(self, plan: str) -> subprocess.CompletedProcess:
        return self._run(
            "--check-coverage", plan,
            "--active-plans-dir", "docs/history/plans",
            "--plans-dir", "docs/history/plans/completed",
            "--backlog-dir", "docs/history/backlog",
        )

    def test_check_coverage_clean(self) -> None:
        self._open_top(ALPHA)
        self._active_plan("2026-01-01-a.md", ALPHA)
        proc = self._check("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_check_coverage_conflict(self) -> None:
        self._open_top(ALPHA)
        self._active_plan("2026-01-01-a.md", ALPHA)
        self._active_plan("2026-01-01-b.md", ALPHA)
        proc = self._check("docs/history/plans/2026-01-01-b.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("2026-01-01-a.md", proc.stdout + proc.stderr)
        self.assertIn("first-landed wins", proc.stdout + proc.stderr)

    def test_check_coverage_excludes_self(self) -> None:
        self._open_top(ALPHA)
        self._active_plan("2026-01-01-a.md", ALPHA)
        proc = self._check("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0)

    def test_check_coverage_scans_completed_and_rejected(self) -> None:
        self._open_top(ALPHA)
        self._write(
            self.plans_dir / "2026-01-01-done.md",
            f"# Plan: done\n\nBacklog origin: docs/history/backlog/{ALPHA}\n",
        )
        self._active_plan("2026-01-01-live.md", ALPHA)
        proc = self._check("docs/history/plans/2026-01-01-live.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("2026-01-01-done.md", proc.stdout + proc.stderr)
        # Rejected citer.
        self._write(
            self.active / "rejected" / "2026-01-01-rej.md",
            f"# Plan: rej\n\nBacklog origin: docs/history/backlog/{BETA}\n",
        )
        self._open_top(BETA)
        self._active_plan("2026-01-01-live2.md", BETA)
        proc = self._check("docs/history/plans/2026-01-01-live2.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("2026-01-01-rej.md", proc.stdout + proc.stderr)

    def test_check_coverage_scans_deferred(self) -> None:
        self._open_top(ALPHA)
        self._write(
            self.active / "deferred" / "2026-01-01-parked.md",
            f"# Plan: parked\n\nBacklog origin: docs/history/backlog/{ALPHA}\n",
        )
        self._active_plan("2026-01-01-live.md", ALPHA)
        proc = self._check("docs/history/plans/2026-01-01-live.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("2026-01-01-parked.md", proc.stdout + proc.stderr)
        self.assertIn("deferred", proc.stdout + proc.stderr)

    def test_coverage_extractor_parses_bare_origin_header(self) -> None:
        self._open_top(ALPHA)
        self._active_plan(
            "2026-01-01-a.md", ALPHA,
            header=(
                f"# Plan: A\n\n[github: https://example.com/repo] Origin: "
                f"docs/history/backlog/{ALPHA}\n"
            ),
        )
        proc = self._check("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0)
        # The bare header origin must have been EXTRACTED: a second citer
        # using the block form must conflict with it.
        self._active_plan("2026-01-01-b.md", ALPHA)
        proc = self._check("docs/history/plans/2026-01-01-b.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("2026-01-01-a.md", proc.stdout + proc.stderr)

    def test_coverage_extractor_ignores_bare_origin_in_body(self) -> None:
        self._open_top(ALPHA)
        self._write(
            self.active / "2026-01-01-a.md",
            "# Plan: A\n\n## Tasks\n\nOrigin: docs/history/backlog/"
            f"{ALPHA} mentioned in body prose\n",
        )
        proc = self._check("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("no origins", proc.stdout + proc.stderr)

    def test_active_and_rejected_dir_resolution(self) -> None:
        self._open_top(ALPHA)
        self._active_plan("2026-01-01-a.md", ALPHA)
        # No --active-plans-dir flag and no plans_dir facts key: the
        # default docs/history/plans must resolve (the fixture already
        # uses that layout), and rejected/deferred derive beneath it.
        proc = self._run(
            "--check-coverage", "docs/history/plans/2026-01-01-a.md",
            "--plans-dir", "docs/history/plans/completed",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self._write(
            self.active / "rejected" / "2026-01-01-rej.md",
            f"# Plan: rej\n\nBacklog origin: docs/history/backlog/{ALPHA}\n",
        )
        proc = self._run(
            "--check-coverage", "docs/history/plans/2026-01-01-a.md",
            "--plans-dir", "docs/history/plans/completed",
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("rejected", proc.stdout + proc.stderr)

    def _mark(self, plan: str) -> subprocess.CompletedProcess:
        return self._run("--mark-covered", plan)

    def test_mark_covered_flips_open(self) -> None:
        self._open_top(ALPHA)
        self._active_plan("2026-01-01-a.md", ALPHA)
        proc = self._mark("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        item = (self.backlog / ALPHA).read_text(encoding="utf-8")
        self.assertIn(
            "Status: covered (docs/history/plans/2026-01-01-a.md)", item
        )

    def test_mark_covered_flips_bullet_bold_shape(self) -> None:
        item = self._write(
            self.backlog / ALPHA,
            f"# Backlog: {ALPHA}\n\n- **Status:** open\n\nbody\n",
        )
        self._active_plan("2026-01-01-a.md", ALPHA)
        proc = self._mark("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = item.read_text(encoding="utf-8")
        self.assertIn(
            "- **Status:** covered (docs/history/plans/2026-01-01-a.md)", text
        )
        # The classification must now read covered (same-plan re-run stays
        # idempotent instead of re-flipping a corrupted line).
        proc = self._mark("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0)

    def test_mark_covered_idempotent_same_plan(self) -> None:
        self._open_top(ALPHA)
        self._active_plan("2026-01-01-a.md", ALPHA)
        self._mark("docs/history/plans/2026-01-01-a.md")
        before = (self.backlog / ALPHA).read_bytes()
        proc = self._mark("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual((self.backlog / ALPHA).read_bytes(), before)

    def test_mark_covered_refuses_conflict(self) -> None:
        self._open_top(ALPHA, 'covered (docs/history/plans/2026-01-01-other.md)')
        self._active_plan("2026-01-01-a.md", ALPHA)
        before = (self.backlog / ALPHA).read_bytes()
        proc = self._mark("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual((self.backlog / ALPHA).read_bytes(), before)
        self.assertIn("2026-01-01-other.md", proc.stdout + proc.stderr)

    def test_mark_covered_skips_non_open(self) -> None:
        self._archived(GAMMA)
        self._rejected_top(BETA)
        self._open_top(ALPHA, "closed (fixture closure)")
        missing = "2026-09-01-origin-missing.md"
        self._write(
            self.active / "2026-01-01-a.md",
            "# Plan: multi\n\nBacklog origins (scope of record): "
            f"`docs/history/backlog/{ALPHA}`, `docs/history/backlog/{BETA}`, "
            f"`docs/history/backlog/{GAMMA}`, `docs/history/backlog/{missing}`.\n",
        )
        proc = self._mark("docs/history/plans/2026-01-01-a.md")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn(f"skip: {GAMMA}: completed", combined)
        self.assertIn(f"skip: {BETA}: rejected", combined)
        self.assertIn(f"skip: {ALPHA}: closed", combined)
        self.assertIn(f"skip: {missing}: missing", combined)

    def test_corpus_covered_with_live_plan_quiet(self) -> None:
        self._open_top(ALPHA, "covered (docs/history/plans/2026-01-01-a.md)")
        self._active_plan("2026-01-01-a.md", ALPHA)
        proc = self._run()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("no longer top-level", proc.stdout)

    def test_corpus_covered_without_live_plan_warns(self) -> None:
        self._open_top(ALPHA, "covered (docs/history/plans/2026-01-01-gone.md)")
        self._archived_plan("2026-01-01-old.md", ALPHA)
        proc = self._run()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("no longer top-level", proc.stdout)
        self.assertIn("2026-01-01-gone.md", proc.stdout)


class CoveredCompletionTest(unittest.TestCase):
    """The covered straggler's fold-and-delete sharpening (plan
    2026-10-01-done-origin-fold-delete-enforcement Task 1): the archive
    gate's covered arm splits by the status-value witness.

    Fixtures pin the PRODUCTION path shapes: the gated plan is invoked at
    its completed path (under ``plans_completed_dir``) while the flip-time
    witness carries the active-prefix form ``docs/history/plans/<name>.md``,
    so only basename equality can match - raw-path equality never would.
    """

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="covered-completion-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.backlog = self.root / "docs" / "history" / "backlog"
        self.completed = self.backlog / "completed"
        self.active = self.root / "docs" / "history" / "plans"
        self.plans_dir = self.active / "completed"
        for directory in (self.completed, self.plans_dir, self.root / ".ai-playbook"):
            directory.mkdir(parents=True)
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )

    def _write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _covered_top(self, name: str, witness: str) -> Path:
        # The witness string is the flip-time active-prefix path form,
        # exactly as ``--mark-covered`` writes it while the covering plan
        # is still top-level under the active plans directory.
        return self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\nStatus: covered ({witness})\n\nbody\n",
        )

    def _gated_plan(self, name: str, origins: list[str], body: str = "") -> Path:
        """The gated plan, written at its completed path (production
        archive-gate shape)."""
        lines = ["# Plan: fixture", ""]
        lines.append(
            f"Backlog origins (scope of record): `{origins[0]}`."
        )
        lines.append("")
        lines.extend(["## Tasks", "", "- [ ] fixture task", ""])
        return self._write(self.plans_dir / name, "\n".join(lines) + body)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--repo-root", str(self.root)]
            + list(args),
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_covered_completion_self_witness_names_fold_remedy(self) -> None:
        # The gated plan itself is the witness: its basename matches even
        # though the witness path is the active-prefix form and the plan
        # file lives only at the completed path (basename equality, never
        # raw-path equality).
        gated = self._gated_plan(
            "2026-10-15-fixture-gated.md", [f"docs/history/backlog/{ALPHA}"]
        )
        self._covered_top(
            ALPHA, "docs/history/plans/2026-10-15-fixture-gated.md"
        )
        self.assertFalse(
            (self.active / "2026-10-15-fixture-gated.md").exists(),
            "fixture precondition: no active-prefix twin of the gated plan",
        )
        proc = self._run("--plan", str(gated))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"straggler: {ALPHA}", proc.stdout)
        # The detail names the fold-and-delete remedy, not the generic
        # covered line.
        self.assertIn("## Disposition of migrated backlog items", proc.stdout)
        self.assertIn("same completion pass", proc.stdout)
        self.assertNotIn(f"covered by docs/history/plans/", proc.stdout)

    def test_covered_completion_other_existing_witness_passes(self) -> None:
        # A different covering plan THAT EXISTS: its own completion pass
        # owns the fold, so the gated plan's archive must not block.
        gated = self._gated_plan(
            "2026-10-15-fixture-gated.md", [f"docs/history/backlog/{ALPHA}"]
        )
        self._covered_top(
            ALPHA, "docs/history/plans/2026-10-16-covering.md"
        )
        self._write(
            self.active / "2026-10-16-covering.md",
            "# Plan: covering\n\nbody\n",
        )
        proc = self._run("--plan", str(gated))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok (1/1 origins closed)", proc.stdout)
        self.assertNotIn("straggler", proc.stdout)

    def test_covered_completion_stale_prefix_witness_resolves_by_basename(self) -> None:
        # The discriminating fixture: the witness path is the stale
        # active-prefix form of a plan that has since archived - it exists
        # ONLY under plans_completed_dir. Corpus mode's literal-path
        # liveness reading would call it not live and refuse; the
        # basename-scoped existence rule across both trees exempts it.
        gated = self._gated_plan(
            "2026-10-15-fixture-gated.md", [f"docs/history/backlog/{ALPHA}"]
        )
        self._covered_top(
            ALPHA, "docs/history/plans/2026-10-17-archived-covering.md"
        )
        self._write(
            self.plans_dir / "2026-10-17-archived-covering.md",
            "# Plan: archived covering\n\nbody\n",
        )
        self.assertFalse(
            (self.active / "2026-10-17-archived-covering.md").exists(),
            "fixture precondition: the witness exists only at the completed path",
        )
        proc = self._run("--plan", str(gated))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok (1/1 origins closed)", proc.stdout)
        self.assertNotIn("straggler", proc.stdout)

    def test_covered_completion_nonexistent_witness_keeps_remedy_straggler(self) -> None:
        # A witness basename matching NO existing plan file: an
        # unresolvable witness is not a covering plan; nothing owns the
        # fold, so the covered straggler stays with the same remedy.
        gated = self._gated_plan(
            "2026-10-15-fixture-gated.md", [f"docs/history/backlog/{ALPHA}"]
        )
        self._covered_top(
            ALPHA, "docs/history/plans/2026-10-18-nowhere.md"
        )
        proc = self._run("--plan", str(gated))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"straggler: {ALPHA}", proc.stdout)
        self.assertIn("## Disposition of migrated backlog items", proc.stdout)
        self.assertIn("same completion pass", proc.stdout)

    def test_covered_completion_fold_then_delete_passes(self) -> None:
        # The completion shape (regression guard): the fold section is
        # present on the gated plan and the origin file is deleted, so the
        # origin reclassifies through the existing missing-plus-consult
        # path and the archive passes.
        gated = self._gated_plan(
            "2026-10-15-fixture-gated.md",
            [f"docs/history/backlog/{ALPHA}"],
            "\n## Disposition of migrated backlog items\n\n"
            f"- `docs/history/backlog/{ALPHA}`: folded; per-item file deleted\n",
        )
        self.assertFalse(
            (self.backlog / ALPHA).exists(),
            "fixture precondition: the origin file is deleted",
        )
        proc = self._run("--plan", str(gated))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok (1/1 origins closed)", proc.stdout)
        self.assertNotIn("straggler", proc.stdout)


if __name__ == "__main__":
    unittest.main()
