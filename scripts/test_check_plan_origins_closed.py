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

    def _extractors(self):
        sys.path.insert(0, str(SCRIPT_PATH.parent))
        import check_plan_origins_closed as gate

        return gate.extract_origin_basenames, gate.extract_coverage_origin_basenames

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
    # Plural origins token grammar and its coverage/archive consumers
    # ------------------------------------------------------------------

    def test_witnessed_archived_plan_parses_through_both_extractors(self) -> None:
        witnessed = (
            SCRIPT_PATH.parent.parent
            / "docs/history/plans/completed/2026-10-07-done-readiness-closeout-boundary.md"
        ).read_text(encoding="utf-8")
        extract_origin, extract_coverage = self._extractors()
        expected = [
            "2026-10-06-done-unrelated-gate-blocks-closeout.md",
            "2026-10-05-authoring-certification-staging-series-gate.md",
        ]
        self.assertEqual(
            extract_origin(witnessed, self.backlog, self.completed), expected
        )
        self.assertEqual(
            extract_coverage(witnessed, self.backlog, self.completed), expected
        )

    def test_plural_token_shapes_parse_through_both_extractors(self) -> None:
        extract_origin, extract_coverage = self._extractors()
        cases = [
            (
                "plain and mixed bullets",
                f"- docs/history/backlog/{ALPHA}\n"
                f"* `docs/history/backlog/{BETA}`; annotated\n",
                [ALPHA, BETA],
            ),
            (
                "duplicate basenames",
                f"- docs/history/backlog/{ALPHA}\n"
                f"- docs/history/backlog/completed/{ALPHA}\n",
                [ALPHA],
            ),
            (
                "compound bullet uses only its leading token",
                f"- docs/history/backlog/{ALPHA} and docs/history/backlog/{BETA}\n",
                [ALPHA],
            ),
            (
                "wrapped prose does not add trailing paths",
                f"- docs/history/backlog/{ALPHA},\n"
                f"  continuation docs/history/backlog/{BETA}\n"
                f"  wrapped reference `docs/history/backlog/{GAMMA}`\n",
                [ALPHA, GAMMA],
            ),
            (
                "non-backlog markdown token is ignored",
                f"- docs/reviews/{ALPHA}\n",
                [],
            ),
            (
                "leading-token punctuation is stripped",
                f"- docs/history/backlog/{ALPHA},\n"
                f"- docs/history/backlog/{BETA};\n"
                f"- docs/history/backlog/{GAMMA}:\n",
                [ALPHA, BETA, GAMMA],
            ),
            (
                "backticked paths accept trailing punctuation",
                f"- `docs/history/backlog/{ALPHA}`.\n"
                f"- `docs/history/backlog/{BETA}`,\n"
                f"- `docs/history/backlog/{GAMMA}`;\n"
                "- `docs/history/backlog/2026-09-02-origin-delta.md`:\n",
                [ALPHA, BETA, GAMMA, "2026-09-02-origin-delta.md"],
            ),
            (
                "punctuation inside backticks uses the bare-token arm",
                f"- `docs/history/backlog/{ALPHA},`\n",
                [ALPHA],
            ),
        ]
        for label, bullets, expected in cases:
            with self.subTest(shape=label):
                text = "Backlog origins (scope of record):\n" + bullets + "\n## Tasks\n"
                self.assertEqual(
                    extract_origin(text, self.backlog, self.completed), expected
                )
                self.assertEqual(
                    extract_coverage(text, self.backlog, self.completed), expected
                )

    def test_coverage_audit_warns_without_changing_mode_results(self) -> None:
        missing = "2026-09-01-origin-listed-only.md"
        self._open_top(missing)
        cases = [
            (
                "matched empty block",
                "Backlog origins (scope of record):\n\n"
                "## Origins dispositions\n\n"
                f"- `docs/history/backlog/{missing}`: listed\n",
                "matched origins block parsed no basenames",
            ),
            (
                "unmatched header",
                "Backlog origin list:\n\n"
                "## Origins dispositions\n\n"
                f"- `docs/history/backlog/{missing}`: listed\n",
                "origins header line was unmatched",
            ),
        ]
        for index, (label, text, diagnostic) in enumerate(cases):
            with self.subTest(shape=label):
                plan = self._write(
                    self.plans_dir / f"2026-09-22-fixture-audit-{index}.md",
                    text,
                )
                args = [
                    "--active-plans-dir", "docs/history/plans",
                    "--plans-dir", "docs/history/plans/completed",
                    "--backlog-dir", "docs/history/backlog",
                ]
                coverage = self._run("--check-coverage", str(plan), *args)
                self.assertEqual(coverage.returncode, 0, coverage.stdout + coverage.stderr)
                self.assertIn(missing, coverage.stdout + coverage.stderr)
                self.assertIn(diagnostic, coverage.stdout + coverage.stderr)
                self.assertIn("warning", coverage.stdout + coverage.stderr)

                before = (self.backlog / missing).read_bytes()
                marked = self._run("--mark-covered", str(plan))
                self.assertEqual(marked.returncode, 0, marked.stdout + marked.stderr)
                self.assertIn(missing, marked.stdout + marked.stderr)
                self.assertIn(diagnostic, marked.stdout + marked.stderr)
                self.assertIn("warning", marked.stdout + marked.stderr)
                self.assertNotIn("marked 1 origin(s) covered", marked.stdout)
                self.assertEqual((self.backlog / missing).read_bytes(), before)

    def test_plain_bullet_parse_remains_visible_to_archive_and_corpus_modes(self) -> None:
        self._open_top(ALPHA)
        plan = self._write(
            self.plans_dir / "2026-09-22-fixture-plain-bullet.md",
            "# Plan: plain bullet\n\n"
            "Backlog origins (scope of record):\n"
            f"- docs/history/backlog/{ALPHA}\n\n",
        )
        archive = self._run("--plan", str(plan))
        self.assertEqual(archive.returncode, 1, archive.stdout + archive.stderr)
        self.assertIn(f"straggler: {ALPHA}", archive.stdout)
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stderr)
        self.assertIn(f"origin {ALPHA} unresolved", corpus.stdout)


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

    def test_bare_path_leading_tokens_are_origins(self):
        self._archived(ALPHA)
        self._archived(BETA)
        text = (
            "Backlog origins (scope of record):\n"
            f"- docs/history/backlog/{ALPHA}, context follows\n"
            f"* `docs/history/backlog/{BETA}`; more context\n"
            f"+ docs/history/backlog/{ALPHA}.\n"
        )
        names = self.gate.extract_origin_basenames(
            text, self.backlog, self.completed
        )
        self.assertEqual(names, [ALPHA, BETA])

    def test_prose_leading_token_contributes_backticks_only(self):
        self._archived(ALPHA)
        self._archived(BETA)
        text = (
            "Backlog origins (scope of record):\n"
            f"- Review this item before `docs/history/backlog/{ALPHA}`\n"
            f"- This references docs/history/backlog/{BETA} in prose\n"
        )
        names = self.gate.extract_origin_basenames(
            text, self.backlog, self.completed
        )
        self.assertEqual(names, [ALPHA])

    def test_bare_path_on_non_bullet_continuation_is_ignored(self):
        self._archived(ALPHA)
        text = (
            "Backlog origins (scope of record):\n"
            f"docs/history/backlog/{ALPHA} continuation text\n"
        )
        names = self.gate.extract_origin_basenames(
            text, self.backlog, self.completed
        )
        self.assertEqual(names, [])

    def test_mixed_bare_and_backticked_paths_keep_text_order(self):
        self._archived(ALPHA)
        self._archived(BETA)
        text = (
            "Backlog origins (scope of record):\n"
            f"- docs/history/backlog/{ALPHA} then `docs/history/backlog/{BETA}`\n"
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


class CheckPlanOriginsClosedOutcomeTest(unittest.TestCase):
    """Outcome-contract fixtures (plan 2026-10-03-outcome-contract-migration-
    batch-1 Task 1): every non-metadata run ends with exactly one final
    `OUTCOME:` line; an origin unreadable at classification time is
    indeterminate (exit 2) naming the origin, dominant over stragglers (a
    mixed open + unreadable corpus names BOTH); an unreadable plans
    directory is tool error (exit 3); usage errors exit 3 through the
    argparse override; `--help` stays metadata-exempt."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="origins-outcome-fixture-"))
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

    def _write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _open_top(self, name: str) -> Path:
        return self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\nStatus: open\n\nbody\n",
        )

    def _unreadable_top(self, name: str) -> Path:
        # An origin file that exists but cannot be read at classification
        # time; permissions are restored on cleanup so rmtree succeeds.
        path = self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\nStatus: open\n\nbody\n",
        )
        path.chmod(0o000)
        self.addCleanup(path.chmod, 0o644)
        return path

    def _archived(self, name: str) -> Path:
        return self._write(
            self.completed / name,
            f"# Backlog: {name}\n\nStatus: done\n\nbody\n",
        )

    def _plan(self, name: str, origins: list[str]) -> Path:
        lines = ["# Plan: fixture", ""]
        if len(origins) == 1:
            lines.append(f"Backlog origins (scope of record): `{origins[0]}`.")
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

    @staticmethod
    def _outcome_lines(proc: subprocess.CompletedProcess) -> list[str]:
        return [
            line for line in proc.stdout.splitlines()
            if line.startswith("OUTCOME:")
        ]

    def test_pass_emits_single_final_outcome_pass(self) -> None:
        self._archived(ALPHA)
        plan = self._plan("2026-09-22-fixture-outcome-pass.md",
                          [f"docs/history/backlog/{ALPHA}"])
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: pass"])
        self.assertTrue(proc.stdout.rstrip().endswith("OUTCOME: pass"))

    def test_straggler_fail_emits_outcome_fail_with_evidence(self) -> None:
        self._open_top(BETA)
        plan = self._plan("2026-09-22-fixture-outcome-fail.md",
                          [f"docs/history/backlog/{BETA}"])
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: fail"])
        self.assertIn(f"straggler: {BETA}", proc.stdout)
        self.assertLess(proc.stdout.index("straggler:"),
                        proc.stdout.index("OUTCOME:"))

    def test_unreadable_origin_is_indeterminate(self) -> None:
        # Declared preservation exception: today this shape straggles at
        # exit 1; evidence-insufficient is the contract's indeterminate
        # definition, so it becomes exit 2 naming the origin.
        self._unreadable_top(ALPHA)
        plan = self._plan("2026-09-22-fixture-outcome-unreadable.md",
                          [f"docs/history/backlog/{ALPHA}"])
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(
            self._outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn(ALPHA, proc.stdout)
        self.assertIn("indeterminate:", proc.stdout)

    def test_mixed_corpus_is_indeterminate(self) -> None:
        # Dominance rule: one open origin and one unreadable origin report
        # indeterminate (exit 2) with BOTH named - the open origin keeps its
        # straggler evidence line, the unreadable origin its own line.
        self._unreadable_top(ALPHA)
        self._open_top(BETA)
        plan = self._plan("2026-09-22-fixture-outcome-mixed.md",
                          [f"docs/history/backlog/{ALPHA}",
                           f"docs/history/backlog/{BETA}"])
        proc = self._run("--plan", str(plan))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(
            self._outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn(f"straggler: {BETA}", proc.stdout)
        self.assertLess(proc.stdout.index(f"straggler: {BETA}"),
                        proc.stdout.index("OUTCOME:"))
        self.assertLess(proc.stdout.index(f"indeterminate: origin {ALPHA}"),
                        proc.stdout.index("OUTCOME:"))

    def test_unreadable_plans_dir_is_tool_error(self) -> None:
        # Legacy: an unreadable plans directory silently scans as empty and
        # exits 0 (pathlib rglob suppresses the permission error). Contract:
        # the check cannot run reliably, so tool error (exit 3).
        self.plans_dir.chmod(0o000)
        self.addCleanup(self.plans_dir.chmod, 0o755)
        proc = self._run()
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: tool_error"])

    def test_corpus_scan_unreadable_archived_plan_is_indeterminate(self) -> None:
        # The corpus warn arm keeps exit 0 only for fully-resolved runs:
        # observed unreadable evidence flips it to indeterminate (exit 2).
        plan = self._plan("2026-09-22-fixture-outcome-corpus.md",
                          [f"docs/history/backlog/{ALPHA}"])
        plan.chmod(0o000)
        self.addCleanup(plan.chmod, 0o644)
        proc = self._run()
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(
            self._outcome_lines(proc), ["OUTCOME: indeterminate"])
        self.assertIn(plan.name, proc.stdout + proc.stderr)

    def test_usage_error_is_tool_error_and_help_is_exempt(self) -> None:
        # Legacy: argparse exits 2 on usage errors (an absent --plan file
        # included). Contract: exit 3 with a final `OUTCOME: tool_error`
        # line; --help stays exempt.
        proc = self._run(
            "--plan", "docs/history/backlog/PLAN-PROMPTS-does-not-exist.md"
        )
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_lines(proc), ["OUTCOME: tool_error"])
        self.assertIn("--plan file not found", proc.stderr)
        help_proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(help_proc.returncode, 0, help_proc.stdout)
        self.assertEqual(self._outcome_lines(help_proc), [])


class DirectoryPlanOriginsTest(unittest.TestCase):
    """Directory-plan operands (plan-directory-shape Task 2): a `--plan`
    directory reads its origins block from the charter; the corpus walk
    treats a plans-root directory plan as one unit beside file plans; and
    the covered witness matches a covering directory plan by its slug."""

    SLUG = "2026-10-08-dir-gate"

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="origins-dir-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.backlog = self.root / "docs" / "history" / "backlog"
        self.completed = self.backlog / "completed"
        self.active = self.root / "docs" / "history" / "plans"
        self.plans_dir = self.active / "completed"
        for directory in (
            self.completed,
            self.plans_dir,
            self.root / ".ai-playbook",
        ):
            directory.mkdir(parents=True)
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        sys.path.insert(0, str(SCRIPT_PATH.parent))
        import check_plan_origins_closed as gate

        self.gate = gate

    def _write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _open_top(self, name: str) -> Path:
        return self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\nStatus: open\n\nbody\n",
        )

    def _archived(self, name: str) -> Path:
        return self._write(
            self.completed / name,
            f"# Backlog: {name}\n\nStatus: done\n\nbody\n",
        )

    def _directory_plan(self, slug: str, charter_text: str) -> Path:
        plan_dir = self.plans_dir / slug
        self._write(plan_dir / "tasks" / "01-only.md", "### Task 1: only\n")
        return self._write(plan_dir / "PLAN.md", charter_text)

    def _covered_top(self, name: str, witness: str) -> Path:
        return self._write(
            self.backlog / name,
            f"# Backlog: {name}\n\nStatus: covered ({witness})\n\nbody\n",
        )

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--repo-root", str(self.root)]
            + list(args),
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_origins_directory_archive_gate(self) -> None:
        # Arm 1: the witnessed unbackticked plural origins block (the real
        # corpus shape: prose paths, no backticks). The gate reads the
        # charter from the directory operand, never misclassifies the
        # prose paths as live origins, and passes.
        self._open_top(ALPHA)
        self._open_top(BETA)
        plan_dir = self.plans_dir / self.SLUG
        self._write(plan_dir / "tasks" / "01-only.md", "### Task 1: only\n")
        self._write(
            plan_dir / "PLAN.md",
            "# Plan: dir gate\n\n"
            "Backlog origins (scope of record): this plan covers "
            f"docs/history/backlog/{ALPHA} and absorbs one uncovered "
            f"sibling whose remedy is this plan's own task: "
            f"docs/history/backlog/{BETA}.\n\n"
            "## Tasks\n",
        )
        proc = self._run("--plan", str(plan_dir))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no origins block", proc.stdout)
        self.assertNotIn("straggler", proc.stdout)
        # Arm 2: the undercount audit fires on a dispositions/parsed gap
        # read from the charter: the block parses one (archived, closed)
        # origin while the dispositions section lists three.
        self._archived(ALPHA)
        self._archived(BETA)
        self._archived(GAMMA)
        undercount_slug = "2026-10-08-dir-undercount"
        undercount_dir = self.plans_dir / undercount_slug
        self._write(
            undercount_dir / "tasks" / "01-only.md", "### Task 1: only\n"
        )
        self._write(
            undercount_dir / "PLAN.md",
            "# Plan: dir undercount\n\n"
            "Backlog origins (scope of record):\n"
            f"- `{ALPHA}`\n"
            "\n"
            "## Origins dispositions\n\n"
            f"- `{ALPHA}`: routed done\n"
            f"- `{BETA}`: routed done\n"
            f"- `{GAMMA}`: routed done\n",
        )
        proc = self._run("--plan", str(undercount_dir))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("warning", combined)
        self.assertIn(undercount_slug, combined)
        self.assertIn("3", combined)
        self.assertIn("1", combined)

    def test_origins_directory_archive_gate_refuses_malformed(self) -> None:
        # A charterless directory operand is a named tool error, never a
        # traceback and never a trivial pass.
        charterless = self.plans_dir / "2026-10-08-charterless"
        charterless.mkdir(parents=True)
        proc = self._run("--plan", str(charterless))
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("tool_error", proc.stdout + proc.stderr)
        self.assertIn("charterless", proc.stderr)

    def test_origins_directory_witness(self) -> None:
        # A covered origin whose covering witness names a DIRECTORY plan
        # passes when the directory plan exists under the active plans
        # root: the witness match re-derives the directory slug (the
        # charter sits at <slug>/PLAN.md, so a basename-only match would
        # miss it).
        gated = self.plans_dir / "2026-10-08-dir-gated.md"
        self._write(
            gated,
            "# Plan: dir gated\n\n"
            "Backlog origins (scope of record): "
            f"`docs/history/backlog/{BETA}`.\n",
        )
        self._covered_top(BETA, "docs/history/plans/2026-10-08-dir-cover")
        covering = self._directory_plan(
            "2026-10-08-dir-cover",
            "# Plan: dir cover\n\n## Tasks\n\n- [x] done\n",
        )
        self.assertTrue(covering.is_file())
        proc = self._run("--plan", str(gated))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ok (1/1 origins closed)", proc.stdout)
        # The unit-level witness predicate matches the directory slug.
        self.assertTrue(
            self.gate._witness_plan_exists(
                "2026-10-08-dir-cover", self.active, self.plans_dir
            )
        )
        # A witness naming NO existing plan (file or directory slug) keeps
        # the fold remedy straggler.
        self._covered_top(
            GAMMA, "docs/history/plans/2026-10-08-dir-nowhere"
        )
        stranded = self.plans_dir / "2026-10-08-dir-stranded.md"
        self._write(
            stranded,
            "# Plan: dir stranded\n\n"
            "Backlog origins (scope of record): "
            f"`docs/history/backlog/{GAMMA}`.\n",
        )
        proc = self._run("--plan", str(stranded))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"straggler: {GAMMA}", proc.stdout)

    def test_corpus_scan_discovers_directory_plan(self) -> None:
        # The corpus walk treats a directory plan as ONE unit beside file
        # plans: the charter's origins block is scanned, member files never
        # scan as separate plans, and the warning names the directory slug.
        self._open_top(ALPHA)
        self._directory_plan(
            self.SLUG,
            "# Plan: dir corpus\n\n"
            "Backlog origins (scope of record): "
            f"`docs/history/backlog/{ALPHA}`.\n"
            "\n## Tasks\n",
        )
        corpus = self._run()
        self.assertEqual(corpus.returncode, 0, corpus.stdout + corpus.stderr)
        self.assertIn(self.SLUG, corpus.stdout)
        self.assertIn(f"origin {ALPHA} unresolved", corpus.stdout)
        self.assertIn("1 archived plan(s)", corpus.stdout)
        self.assertNotIn("01-only.md", corpus.stdout)
        self.assertNotIn("PLAN.md:", corpus.stdout)


if __name__ == "__main__":
    unittest.main()
