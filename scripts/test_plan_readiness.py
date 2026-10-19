"""Unit tests for the plan_readiness scope-classification probe.

Covers the classification-tag placement check of
``scope_classification_problem`` (the enforcement side of the plans
skill's Classification tag rule): a ``[class: ...]`` tag must sit on a
task checklist item's first (checkbox-marker) line; a tag wrapped onto
a continuation line is reported as a placement problem instead of
classifying the item untagged, a tag mention inside backtick spans is a
quote and never trips, and a genuinely untagged item still fails.

Run from the repository root:

    PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import runtime_capabilities
from execute_plan_runtime import _named_evidence_limit_error
from plan_readiness import (
    _clean_reviews_dir,
    _write_clean_state,
    evaluate_readiness,
    scope_classification_problem,
)


def _plan_with_task_section(task_body: str) -> str:
    """Minimal plan text carrying one task section with ``task_body``."""
    return (
        "# P\n\n"
        "## Tasks\n\n"
        "### Task 1: Do the thing\n\n"
        f"{task_body}\n"
    )


class ScopeClassificationPlacementTest(unittest.TestCase):
    """Placement of the classification tag on a checklist item."""

    def test_continuation_line_tag_reports_placement(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module with care\n"
            "  and diligence. [class: IMPLEMENTATION_REQUIRED]\n"
        )
        reason = scope_classification_problem(plan)
        self.assertIsNotNone(reason)
        self.assertIn("non-checkbox line", reason)
        self.assertIn("Task 1", reason)

    def test_first_line_tag_clears(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module with care and diligence. "
            "[class: IMPLEMENTATION_REQUIRED]\n"
        )
        self.assertIsNone(scope_classification_problem(plan))

    def test_backticked_tag_mention_in_prose_clears(self):
        plan = _plan_with_task_section(
            "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
            "\n"
            "Remember: every item carries `[class: ...]` at its end.\n"
        )
        self.assertIsNone(scope_classification_problem(plan))

    def test_untagged_item_still_fails(self):
        plan = _plan_with_task_section("- [ ] Write the module.\n")
        reason = scope_classification_problem(plan)
        self.assertIsNotNone(reason)
        self.assertIn("carries no", reason)


# --------------------------------------------------------------------------- #
# Fence-balance structural failure (both readiness entries, CLI level).
# --------------------------------------------------------------------------- #

import contextlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path

import plan_readiness

FACTS_BODY = (
    "# facts\n\n```toml\n"
    'plans_dir = "plans"\n'
    'reviews_dir = "reviews"\n'
    "```\n"
)

# A plan whose structural probes all pass cleanly, plus a trailing fenced
# block whose closer was dropped. The opener's line number is asserted
# verbatim in the failure message.
BALANCED_PLAN = (
    "# P\n\n"
    "## Assumptions\n\n"
    "Decision points requiring a grill: none remain.\n\n"
    "## Tasks\n\n"
    "### Task 1: Do the thing\n\n"
    "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
)
UNCLOSED_TAIL = "\n```bash\necho never closed\n"


class PlanReadinessFenceBalanceTest(unittest.TestCase):
    """An unclosed fence fails closed naming the opener line; a balanced
    document runs the structural probes over the full text."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="fence-balance-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        (self.root / "plans").mkdir()
        (self.root / "reviews").mkdir()

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_fixture(self, plan_text: str) -> Path:
        plan, _ = plan_readiness._write_clean_state(
            self.root / "plans",
            self.root / "reviews",
            plan_text=plan_text,
            date="2026-09-25",
        )
        return plan

    def test_unclosed_fence_fails_closed_naming_line(self):
        plan_text = BALANCED_PLAN + UNCLOSED_TAIL
        opener_line = plan_text.split("\n").index("```bash") + 1
        plan = self._write_fixture(plan_text)
        rc, out, err = self._run_main([str(plan)])
        self.assertNotEqual(rc, 0, (out, err))
        self.assertIn("unclosed fence", err)
        self.assertIn(f"line {opener_line}", err)
        # Pre-round entry: same structural failure through the pre-round
        # channel, before any probe evaluates the stripped text.
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertNotEqual(rc, 0, (out, err))
        self.assertIn(
            f"readiness PRE-ROUND FAILED: unclosed fence opener at line "
            f"{opener_line}",
            err,
        )

    def test_balanced_fences_still_pass(self):
        plan = self._write_fixture(BALANCED_PLAN)
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertNotIn("unclosed fence", err)
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))

    def test_pre_round_declaration_decisions_match_runtime_grammar(self):
        # The pre-round surface decides every declaration shape exactly as the
        # hardened runtime parser does (same accept, or the same named
        # refusal), so a seeded declaration cannot pass one gate and fail the
        # other. Entries sit immediately after the heading: the runtime block
        # grammar refuses a blank line before a later entry, and the parity
        # shapes here must stay inside the one documented grammar.
        def declaration_plan(files_body: str, review_scope: str) -> str:
            return (
                "# P\n\n"
                "## Assumptions\n\n"
                "Decision points requiring a grill: none remain.\n\n"
                "## Tasks\n\n"
                "### Task 1: Do the thing\n\n"
                f"{files_body}\n"
                "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
                "\n"
                "## Review Scope\n\n"
                "**Production code:**\n\n"
                f"{review_scope}"
            )

        acceptance = {
            "plain annotated": (
                "Files:\n- `src/new.py` *(new)*",
                "- src/new.py *(new)*\n",
            ),
            "elaborated annotated": (
                "Files:\n- `src/new.py` *(new; this plan)*",
                "- src/new.py *(new)*\n",
            ),
            "indented entries": (
                "Files:\n  - `src/new.py` *(new)*",
                "- src/new.py *(new)*\n",
            ),
        }
        for name, (files_body, review_scope) in acceptance.items():
            plan = self._write_fixture(declaration_plan(files_body, review_scope))
            rc, out, err = self._run_main(["--pre-round", str(plan)])
            self.assertEqual(rc, 0, (name, out, err))

        divergence = {
            "duplicate heading": (
                "Files:\n- `src/new.py` *(new)*\nFiles:\n- `src/second.py`",
                "- src/new.py *(new)*\n- src/second.py\n",
                "duplicate Files: heading",
            ),
            "indented opener": (
                "    Files:\n- `src/new.py` *(new)*",
                "- src/new.py *(new)*\n",
                "an indented 'Files:' line is not a block opener",
            ),
            "case variant opener": (
                "files:\n- `src/new.py` *(new)*",
                "- src/new.py *(new)*\n",
                "case variant",
            ),
            "uppercase case variant opener": (
                "FILES:\n- `src/new.py` *(new)*",
                "- src/new.py *(new)*\n",
                "case variant",
            ),
        }
        for name, (files_body, review_scope, expected_problem) in divergence.items():
            plan = self._write_fixture(declaration_plan(files_body, review_scope))
            rc, out, err = self._run_main(["--pre-round", str(plan)])
            self.assertNotEqual(rc, 0, (name, out, err))
            self.assertIn("readiness PRE-ROUND FAILED:", err, (name, out, err))
            self.assertIn(expected_problem, err, (name, out, err))

        # The indented-entry skip is stopped: an indented entry IS collected,
        # so an indented entry omitted from the Review Scope inventory refuses
        # with the inventory reason instead of being silently skipped.
        unlisted_plan = declaration_plan(
            "Files:\n  - `src/unlisted.py`",
            "- src/second.py\n",
        )
        plan = self._write_fixture(unlisted_plan)
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertNotEqual(rc, 0, (out, err))
        self.assertIn("src/unlisted.py", err, (out, err))
        self.assertIn("Review Scope", err, (out, err))


# --------------------------------------------------------------------------- #
# Pre-round execution budget sizing warnings: the non-blocking stderr warning
# class over the optional `Execution budget:` header line (strictly-greater
# thresholds: total over 3.0h, largest task over 1.5h, task count over 4).
# --------------------------------------------------------------------------- #


def _budget_plan_text(
    budget_line: str | None,
    task_count: int = 1,
    *,
    drop_trailer: bool = False,
) -> str:
    """Plan text with an optional `Execution budget:` line in the header
    region (between the title line and the first `## ` heading), N task
    sections, and an Assumptions trailer that can be dropped to force a
    structural-probe failure."""
    tasks = "".join(
        f"### Task {n}: Do the thing\n\n"
        "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n\n"
        for n in range(1, task_count + 1)
    )
    header = "# P\n\n"
    if budget_line is not None:
        header += f"{budget_line}\n\n"
    trailer = (
        "Decision points requiring a grill: none remain.\n\n"
        if not drop_trailer
        else "Some high-confidence assumption with its basis.\n\n"
    )
    return (
        f"{header}"
        "## Assumptions\n\n"
        f"{trailer}"
        "## Tasks\n\n"
        f"{tasks}"
    )


class PreRoundExecutionBudgetTest(unittest.TestCase):
    """The pre-round sizing warnings: one stderr line per breached
    threshold, silent when the line is absent, never blocking."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="pre-round-budget-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        (self.root / "plans").mkdir()
        (self.root / "reviews").mkdir()

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_fixture(self, plan_text: str) -> Path:
        plan, _ = plan_readiness._write_clean_state(
            self.root / "plans",
            self.root / "reviews",
            plan_text=plan_text,
            date="2026-09-26",
            slug="budget-sizing",
        )
        return plan

    def test_pre_round_budget_warning_over_total(self):
        plan = self._write_fixture(
            _budget_plan_text("Execution budget: 4.0h total, largest task 1.0h")
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(
            err.count("readiness PRE-ROUND WARNING:"), 1, err
        )
        self.assertIn(
            "execution budget total 4.0h exceeds the 3.0h plan cap", err
        )
        # The stdout OK line is unchanged: warnings never block.
        self.assertIn(
            "readiness PRE-ROUND OK: structural checks clean "
            "(review record not consulted)",
            out,
        )

    def test_pre_round_budget_warning_largest_task(self):
        plan = self._write_fixture(
            _budget_plan_text("Execution budget: 2.0h total, largest task 1.6h")
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(
            err.count("readiness PRE-ROUND WARNING:"), 1, err
        )
        self.assertIn(
            "execution budget largest task 1.6h exceeds the 1.5h task cap",
            err,
        )

    def test_pre_round_budget_warning_task_count(self):
        plan = self._write_fixture(
            _budget_plan_text(
                "Execution budget: 1.0h total, largest task 0.5h",
                task_count=5,
            )
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(
            err.count("readiness PRE-ROUND WARNING:"), 1, err
        )
        self.assertIn(
            "execution budget task count 5 exceeds the 4-task cap", err
        )

    def test_pre_round_budget_absent_silent(self):
        plan = self._write_fixture(_budget_plan_text(None))
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        # Byte-identical to the pre-plan behavior: the exact OK line plus
        # the outcome contract's OUTCOME line on stdout and nothing on
        # stderr.
        self.assertEqual(
            out,
            "readiness PRE-ROUND OK: structural checks clean "
            "(review record not consulted)\nOUTCOME: pass\n",
        )
        self.assertEqual(err, "")

    def test_pre_round_budget_malformed_warns(self):
        plan = self._write_fixture(
            _budget_plan_text("Execution budget: TBD")
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(
            err.count("readiness PRE-ROUND WARNING:"), 1, err
        )
        self.assertIn("does not match the required grammar", err)
        self.assertIn("non-negative decimal hours", err)

    def test_pre_round_budget_at_threshold_silent(self):
        plan = self._write_fixture(
            _budget_plan_text(
                "Execution budget: 3.0h total, largest task 1.5h",
                task_count=4,
            )
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        # At-threshold values are silent (strictly-greater comparisons).
        self.assertEqual(err, "")

    def test_pre_round_budget_integer_hours_in_grammar(self):
        plan = self._write_fixture(
            _budget_plan_text("Execution budget: 4h total, largest task 1h")
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        # Integers parse as whole hours; 4h is over the 3.0h total cap,
        # 1h is not over the 1.5h task cap, so exactly one warning.
        self.assertEqual(
            err.count("readiness PRE-ROUND WARNING:"), 1, err
        )
        self.assertIn(
            "execution budget total 4h exceeds the 3.0h plan cap", err
        )

    def test_pre_round_budget_multi_breach_order(self):
        plan = self._write_fixture(
            _budget_plan_text(
                "Execution budget: 4.0h total, largest task 1.6h",
                task_count=5,
            )
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        warnings = [
            line
            for line in err.splitlines()
            if line.startswith("readiness PRE-ROUND WARNING:")
        ]
        self.assertEqual(len(warnings), 3, err)
        # Declared order: total, then largest task, then task count.
        self.assertIn("plan cap", warnings[0], err)
        self.assertIn("task cap", warnings[1], err)
        self.assertIn("task count", warnings[2], err)

    def test_pre_round_budget_failure_path_no_warnings(self):
        plan = self._write_fixture(
            _budget_plan_text(
                "Execution budget: 4.0h total, largest task 1.0h",
                drop_trailer=True,
            )
        )
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("readiness PRE-ROUND FAILED:", err)
        self.assertNotIn("PRE-ROUND WARNING:", err)
        self.assertNotIn("readiness PRE-ROUND OK", out)


# --------------------------------------------------------------------------- #
# Files:-coverage warning arm (machinery registry row
# script:plan-files-coverage-arm): the warning-only report naming
# acceptance-item path tokens missing from task Files: lists, driven through
# BOTH CLI entries (the pre-round gate and the full gate's main path).
# --------------------------------------------------------------------------- #


def _coverage_task(title: str, files: list, items: list) -> str:
    """One task section: a `Files:` block (each entry `*(new)*` so the
    ownership existence check passes in the scratch root) followed by the
    acceptance checkboxes."""
    parts = [f"### {title}\n\n"]
    if files:
        parts.append("Files:\n")
        parts.extend(f"- `{path}` *(new)*\n" for path in files)
        parts.append("\n")
    parts.extend(
        f"- [ ] {item} [class: IMPLEMENTATION_REQUIRED]\n" for item in items
    )
    return "".join(parts)


def _coverage_plan_text(*tasks: str) -> str:
    """Plan text whose Tasks section carries the given task sections."""
    return (
        "# P\n\n"
        "## Assumptions\n\n"
        "Decision points requiring a grill: none remain.\n\n"
        "## Tasks\n\n" + "".join(tasks)
    )


_COVERAGE_LOUD_ITEM = "Update `src/module.py` now"


class PlanFilesCoverageTest(unittest.TestCase):
    """The Files:-coverage arm at the CLI boundary: the loud warning
    naming task, path, and quoting item and the softened sibling variant
    fire on BOTH entries with unchanged exits; the silent boundaries (a
    conforming task, prose without path-shaped tokens, an unbackticked
    path, a scheme-bearing token) print zero lines; every failure path
    prints zero warning lines."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="files-coverage-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        (self.root / "plans").mkdir()
        (self.root / "reviews").mkdir()

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_fixture(self, plan_text: str) -> Path:
        plan, _ = plan_readiness._write_clean_state(
            self.root / "plans",
            self.root / "reviews",
            plan_text=plan_text,
            date="2026-09-26",
            slug="files-coverage",
        )
        return plan

    @staticmethod
    def _coverage_lines(text: str) -> list:
        return [
            line
            for line in text.splitlines()
            if line.startswith("readiness FILES-COVERAGE WARNING:")
        ]

    def _loud_plan(self) -> str:
        return _coverage_plan_text(
            _coverage_task(
                "Task 1: Do the thing",
                ["src/other.py"],
                [_COVERAGE_LOUD_ITEM],
            )
        )

    def test_loud_warning_on_both_entries(self):
        plan = self._write_fixture(self._loud_plan())
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        lines = self._coverage_lines(err)
        self.assertEqual(len(lines), 1, err)
        self.assertIn("Task 1", lines[0])
        self.assertIn("`src/module.py`", lines[0])
        self.assertIn(_COVERAGE_LOUD_ITEM, lines[0])
        self.assertIn("readiness PRE-ROUND OK", out)
        # Full-gate main path: same bytes, same single warning, stderr
        # only, unchanged exit contract.
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 0, (out, err))
        lines = self._coverage_lines(err)
        self.assertEqual(len(lines), 1, err)
        self.assertIn("Task 1", lines[0])
        self.assertIn("`src/module.py`", lines[0])
        self.assertIn(_COVERAGE_LOUD_ITEM, lines[0])
        self.assertNotIn("FILES-COVERAGE", out)
        self.assertIn("readiness OK", out)
        self.assertTrue(out.rstrip().endswith("OUTCOME: pass"), out)

    def test_sibling_variant_on_both_entries(self):
        plan = self._write_fixture(
            _coverage_plan_text(
                _coverage_task(
                    "Task 1: Write the module",
                    ["src/module.py"],
                    ["Write the module"],
                ),
                _coverage_task(
                    "Task 2: Polish the module",
                    ["src/other.py"],
                    ["Polish `src/module.py` again"],
                ),
            )
        )
        for argv in (["--pre-round", str(plan)], [str(plan)]):
            rc, out, err = self._run_main(argv)
            self.assertEqual(rc, 0, (out, err))
            lines = self._coverage_lines(err)
            self.assertEqual(len(lines), 1, err)
            # The softened variant names the quoting task, the path, and
            # the declaring sibling; the loud wording never fires.
            self.assertIn("Task 2", lines[0])
            self.assertIn("`src/module.py`", lines[0])
            self.assertIn("Task 1's Files: list", lines[0])
            self.assertIn("sibling-declared", lines[0])
            self.assertNotIn("no task's Files: list declares it", err)

    def _assert_silent_both_entries(self, plan_text: str) -> None:
        plan = self._write_fixture(plan_text)
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(err, "")
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(err, "")
        self.assertTrue(out.rstrip().endswith("OUTCOME: pass"), out)

    def test_conforming_task_silent_on_both_entries(self):
        self._assert_silent_both_entries(
            _coverage_plan_text(
                _coverage_task(
                    "Task 1: Do the thing",
                    ["src/module.py"],
                    [_COVERAGE_LOUD_ITEM],
                )
            )
        )

    def test_prose_without_path_token_silent(self):
        self._assert_silent_both_entries(
            _coverage_plan_text(
                _coverage_task(
                    "Task 1: Do the thing",
                    ["src/other.py"],
                    ["Write the module with care"],
                )
            )
        )

    def test_unbackticked_path_silent(self):
        # Plain-prose tokens are out of scope (the _plan_item_path_tokens
        # divergence of record): an unbackticked path never warns.
        self._assert_silent_both_entries(
            _coverage_plan_text(
                _coverage_task(
                    "Task 1: Do the thing",
                    ["src/other.py"],
                    ["Update src/module.py in place"],
                )
            )
        )

    def test_scheme_bearing_token_silent(self):
        # The scheme exclusion: a URI is not a repository path even though
        # its slashes are path-shaped.
        self._assert_silent_both_entries(
            _coverage_plan_text(
                _coverage_task(
                    "Task 1: Do the thing",
                    ["src/other.py"],
                    ["See `https://example.com/docs/module.md` for context"],
                )
            )
        )

    def test_pre_round_failure_path_no_coverage_warnings(self):
        plan_text = (
            "# P\n\n"
            "## Assumptions\n\n"
            "Some high-confidence assumption with its basis.\n\n"
            "## Tasks\n\n"
            + _coverage_task(
                "Task 1: Do the thing",
                ["src/other.py"],
                [_COVERAGE_LOUD_ITEM],
            )
        )
        plan = self._write_fixture(plan_text)
        rc, out, err = self._run_main(["--pre-round", str(plan)])
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("readiness PRE-ROUND FAILED:", err)
        self.assertNotIn("FILES-COVERAGE", err)

    def test_full_gate_failure_path_no_coverage_warnings(self):
        plan, _ = plan_readiness._write_clean_state(
            self.root / "plans",
            self.root / "reviews",
            plan_text=self._loud_plan(),
            verdict="no",
            date="2026-09-26",
            slug="files-coverage",
        )
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("readiness FAILED:", err)
        self.assertNotIn("FILES-COVERAGE", err)

    def test_full_gate_undecodable_plan_skips_arm(self):
        plan, review = plan_readiness._write_clean_state(
            self.root / "plans",
            self.root / "reviews",
            plan_text=self._loud_plan(),
            date="2026-09-26",
            slug="files-coverage",
        )
        plan_bytes = b"\xff\xfe undecodable files-coverage plan"
        plan.write_bytes(plan_bytes)
        sidecar = review.with_suffix(".stats.json")
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        payload["source_digest"] = vrs.compute_source_digest(
            "plan", plan_bytes
        )
        sidecar.write_text(json.dumps(payload), encoding="utf-8")
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("cannot read plan bytes", err)
        self.assertNotIn("FILES-COVERAGE", err)


# --------------------------------------------------------------------------- #
# --check-review-name probe: one round pair re-verified against the gate's
# own discovery shape (filename glob, sidecar presence, sidecar artifact_slug,
# coverage self-references) before the loop folds findings or relaunches.
# --------------------------------------------------------------------------- #

CANONICAL_ROUND_NAME = "2026-09-01-plan-review-fixture-feature-r1.md"
SHORT_SLUG_ROUND_NAME = "2026-09-01-plan-review-fixture-r1.md"
REVIEW_NAME_ROUND_MD = (
    "# Plan Review: fixture feature\n\n"
    "## Summary\n\n"
    "- ready=yes\n"
)


class ReviewNameCheckTest(unittest.TestCase):
    """The ``--check-review-name`` probe binds one written round pair to
    the plan's feature slug through the gate's own discovery shape."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="review-name-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()
        self.plan = self.plans / "2026-09-01-fixture-feature.md"
        self.plan.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main(argv)
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_round(self, name, sidecar, directory=None):
        """One round Markdown plus its ``.stats.json`` sidecar.

        ``sidecar`` is JSON-serialized when it is an object, written
        verbatim when it is a string, and skipped when ``None``.
        """
        round_path = (directory or self.reviews) / name
        round_path.write_text(REVIEW_NAME_ROUND_MD, encoding="utf-8")
        if sidecar is not None:
            sidecar_text = (
                sidecar if isinstance(sidecar, str) else json.dumps(sidecar)
            )
            round_path.with_suffix(".stats.json").write_text(
                sidecar_text, encoding="utf-8"
            )
        return round_path

    def _run_probe(self, round_path):
        return self._run_main(
            [str(self.plan), "--check-review-name", str(round_path)]
        )

    def _dangling_path(self):
        return self.reviews / "2026-08-01-plan-review-older-feature-r1.md"

    def test_accepts_canonical_pair(self):
        round_path = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture-feature"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("review name check OK", out)

    def test_rejects_short_slug(self):
        round_path = self._write_round(
            SHORT_SLUG_ROUND_NAME, {"artifact_slug": "fixture"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("fixture-feature", err)
        self.assertIn("discovery shape", err)

    def test_rejects_missing_sidecar(self):
        round_path = self._write_round(CANONICAL_ROUND_NAME, None)
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("missing stats sidecar", err)

    def test_rejects_sidecar_slug_mismatch(self):
        round_path = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture"}
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("artifact_slug", err)
        self.assertIn("expected 'fixture-feature'", err)

    def test_rejects_dangling_inherited_coverage(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "inherited_coverage": [
                        {"lens": "testing", "artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_dangling_attempt_reference(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "attempts": [
                        {"attempt_id": 1, "artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_dangling_replacement_reference(self):
        dangling = str(self._dangling_path())
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {
                "artifact_slug": "fixture-feature",
                "coverage": {
                    "replacement": [
                        {"lens": "testing", "original_artifact": dangling}
                    ]
                },
            },
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(dangling, err)

    def test_rejects_corrupt_sidecar(self):
        round_path = self._write_round(CANONICAL_ROUND_NAME, "{not json")
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("malformed stats sidecar", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("Traceback", out)

    def test_rejects_round_outside_reviews_dir(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        round_path = self._write_round(
            CANONICAL_ROUND_NAME,
            {"artifact_slug": "fixture-feature"},
            directory=elsewhere,
        )
        rc, out, err = self._run_probe(round_path)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("reviews directory", err)

    def test_rejects_symlinked_round_identity(self):
        # F1 canary: identity (parent + filename) is judged on the path as
        # claimed, never the symlink target, so a symlink named like a
        # nonexistent round cannot borrow a clean pair's identity.
        target = self._write_round(
            CANONICAL_ROUND_NAME, {"artifact_slug": "fixture-feature"}
        )
        claimed = self.reviews / "2026-09-01-plan-review-fixture-feature-r9.md"
        os.symlink(target, claimed)
        rc, out, err = self._run_probe(claimed)
        self.assertEqual(rc, 1, (out, err))
        # The claimed pair is judged under the claimed names: the symlink
        # borrows the target's identity checks but its own r9 sidecar is
        # missing, which is the fail.
        self.assertIn("missing stats sidecar", err)
        self.assertIn("r9", err)

    def test_missing_plan_path_is_usage_error(self):
        round_path = self.reviews / CANONICAL_ROUND_NAME
        with self.assertRaises(SystemExit) as caught:
            self._run_main(["--check-review-name", str(round_path)])
        # Renewed legacy arm: the argparse usage override exits 3 (tool
        # error), never argparse's default exit 2.
        self.assertEqual(caught.exception.code, 3)

    def test_mode_combination_is_usage_error(self):
        round_path = self.reviews / CANONICAL_ROUND_NAME
        for flag in ("--selftest", "--sweep", "--pre-round"):
            with self.subTest(flag=flag):
                with self.assertRaises(SystemExit) as caught:
                    self._run_main(
                        [
                            str(self.plan),
                            flag,
                            "--check-review-name",
                            str(round_path),
                        ]
                    )
                # Renewed legacy arm: the argparse usage override exits 3.
                self.assertEqual(caught.exception.code, 3)


# --------------------------------------------------------------------------- #
# Cap-closure terminal shape (certification machinery contract-collisions
# plan, Task 1): the ``extensions.cap_closure`` sidecar contract in the
# staging validator and the readiness-gate acceptance built on it. The
# staged patterns, the residual section body, and the declared residuals
# count are reconciled by the gate probe; the four guards in
# ``CapClosureReadinessTest`` pin today's behavior and must keep passing
# before and after the change.
# --------------------------------------------------------------------------- #

import re

import validate_review_staging as vrs

CAP_CLOSURE_SECTION = "## Residual findings (cap closure)"
CAP_CLOSURE_SLUG = "cap-closure-fixture"
CAP_CLOSURE_ROUND = 5
CAP_CLOSURE_ROUND_SUFFIX = "r5"
CAP_CLOSURE_DATE = "2026-09-01"
CAP_CLOSURE_MODERN_DATE = "2026-09-08"
CAP_CLOSURE_PATTERN = "testing#weak-assertion"
CAP_CLOSURE_BLOCK_PATTERN = "quality#cap-blocker"
# Pre-fold plan bytes: their digest is the declaration's pre_fold_digest,
# always different from the digest of the current (post-fold) plan bytes.
CAP_CLOSURE_PRE_FOLD_BYTES = b"# Cap closure fixture (pre-fold plan bytes)\n"
CAP_CLOSURE_THIRD_BYTES = b"# Cap closure fixture (third recorded state)\n"
_MALFORMED_SIDECAR_PREFIX = (
    "malformed stats sidecar (schema validation failed) for round "
    f"r{CAP_CLOSURE_ROUND_SUFFIX[1:]}: "
)


def _cap_closure_pre_fold_digest():
    return vrs.compute_source_digest("plan", CAP_CLOSURE_PRE_FOLD_BYTES)


def _cap_closure_declaration(**overrides):
    """Conforming ``extensions.cap_closure`` declaration for the fixtures."""
    declaration = {
        "plan_section": CAP_CLOSURE_SECTION,
        "round": str(CAP_CLOSURE_ROUND),
        "residuals": 1,
        "pre_fold_digest": _cap_closure_pre_fold_digest(),
    }
    declaration.update(overrides)
    return declaration


def _cap_closure_finding(**overrides):
    """One valid version-1 finding row mirrored into the review Markdown."""
    finding = vrs._current_finding(
        pattern=CAP_CLOSURE_PATTERN, triage="fixed"
    )
    finding.update(overrides)
    return finding


class PlanReviewSourceIdentityTest(unittest.TestCase):
    """Regression for the 2026-10-15 duplicate-r1 cross-plan interruption.

    The two evidence-recovery plans had one canonical slug, so the selector
    combined their rounds and refused before it could emit a staging path.
    """

    def test_discovery_and_name_probe_bind_same_slug_to_plan_path(self):
        import subprocess
        import plan_readiness
        from review_plan_identity import identity_token

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            plans = root / "docs" / "plans"
            reviews = root / ".ai-playbook" / "reviews"
            plans.mkdir(parents=True)
            reviews.mkdir(parents=True)
            plan_a = plans / "2026-10-14-same-feature.md"
            plan_b = plans / "2026-10-15-same-feature.md"
            plan_a.write_text("A", encoding="utf-8")
            plan_b.write_text("B", encoding="utf-8")
            identities = [
                plan.relative_to(root).as_posix() for plan in (plan_a, plan_b)
            ]
            records = []
            for date_value, identity in zip(("2026-10-14", "2026-10-15"), identities):
                record = reviews / f"{date_value}-plan-review-same-feature-r1.md"
                record.write_text(
                    f"## Metadata\n- URL or Artifact: {identity}\n",
                    encoding="utf-8",
                )
                record.with_suffix(".stats.json").write_text(
                    json.dumps({"artifact_slug": "same-feature", "round": 1}),
                    encoding="utf-8",
                )
                records.append(record)

            for identity, expected in zip(identities, records):
                self.assertEqual(
                    plan_readiness.latest_review_round(
                        reviews, "same-feature", identity
                    ),
                    (expected, 1),
                )

            token = identity_token(identities[0])
            qualified = reviews / f"2026-10-16-plan-review-same-feature-p{token}-r2.md"
            qualified.write_text(
                f"## Metadata\n- URL or Artifact: {identities[0]}\n",
                encoding="utf-8",
            )
            qualified.with_suffix(".stats.json").write_text(
                json.dumps({
                    "artifact_slug": "same-feature",
                    "round": 2,
                    "extensions": {"plan_identity": identities[0]},
                }),
                encoding="utf-8",
            )
            self.assertEqual(
                plan_readiness.check_review_name(plan_a, qualified, reviews),
                (True, None),
            )
            ok, reason = plan_readiness.check_review_name(plan_b, qualified, reviews)
            self.assertFalse(ok)
            self.assertIn("source plan identity", reason)

    def test_discovery_resolves_pure_legacy_round_lexically_with_advisory(self):
        """Narrowed contract (must-flip pin): a series with zero
        identity-bearing records resolves the highest rN lexically with the
        advisory, and the consult never surfaces the old blanket identity
        raise; the pair is then graded on its own merits."""
        import subprocess
        import plan_readiness

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            plans = root / "docs" / "plans"
            reviews = root / ".ai-playbook" / "reviews"
            plans.mkdir(parents=True)
            reviews.mkdir(parents=True)
            plan = plans / "2026-10-15-same-feature.md"
            plan.write_text("same bytes", encoding="utf-8")
            record = reviews / "2026-10-15-plan-review-same-feature-r1.md"
            record.write_text("## Metadata\n- Type: Plan Review\n", encoding="utf-8")
            record.with_suffix(".stats.json").write_text(
                json.dumps({"round": 1, "source_digest": "a" * 64}),
                encoding="utf-8",
            )

            advisories: list[str] = []
            found = plan_readiness.latest_review_round(
                reviews,
                "same-feature",
                plan.relative_to(root).as_posix(),
                advisories,
            )
            self.assertEqual(found, (record, 1))
            self.assertEqual(len(advisories), 1)
            self.assertIn(record.name, advisories[0])
            self.assertIn("lexical", advisories[0])

            ok, reason = plan_readiness.evaluate_readiness(plan, plans, reviews)
            self.assertFalse(ok)
            self.assertIsNotNone(reason)
            self.assertNotIn("cannot resolve plan identity", reason)

    def test_record_identity_unwraps_markdown_code_span_path(self):
        from review_plan_identity import markdown_identity

        self.assertEqual(
            markdown_identity(
                "## Metadata\n- URL or Artifact: `docs/plans/2026-10-15-same-feature.md`\n"
            ),
            "docs/plans/2026-10-15-same-feature.md",
        )

    def test_pre_round_identity_collision_warning_names_other_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            plans = Path(directory) / "plans"
            completed = plans / "completed"
            plans.mkdir()
            completed.mkdir()
            active = plans / "2026-10-16-shared-feature.md"
            older = completed / "2026-10-15-shared-feature.md"
            active.write_text("# active\n", encoding="utf-8")
            older.write_text("# completed\n", encoding="utf-8")
            warnings = plan_readiness.plan_review_identity_warnings(active, plans)
            self.assertEqual(len(warnings), 1)
            self.assertIn("2026-10-15-shared-feature.md", warnings[0])
            self.assertIn("source-plan identity keeps review series separate", warnings[0])


class ReviewSeriesLegacyIdentityTest(unittest.TestCase):
    """The narrowed series-identity disposition (review-record legacy
    identity plan, Task 1).

    Every witness builds an isolated temp git home. A legacy
    identity-unresolvable record carries neither the sidecar
    ``extensions.plan_identity`` field nor the Markdown ``URL or
    Artifact:`` line (the pre-convention shape).
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="legacy-series-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        import subprocess

        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        self.plan = self.plans / "2026-10-15-same-feature.md"
        self.plan.write_text("same bytes", encoding="utf-8")
        self.identity = self.plan.relative_to(self.root).as_posix()

    def _write_pair(self, base, round_value, identity):
        """One complete round pair; ``identity=None`` is the legacy
        identity-unresolvable shape."""
        record = self.reviews / f"{base}.md"
        identity_line = (
            f"- URL or Artifact: {identity}\n" if identity is not None else ""
        )
        record.write_text(
            f"## Metadata\n{identity_line}- Type: Plan Review\n",
            encoding="utf-8",
        )
        record.with_suffix(".stats.json").write_text(
            json.dumps({"artifact_slug": "same-feature", "round": round_value}),
            encoding="utf-8",
        )
        return record

    def test_mixed_series_returns_owned_latest_and_names_excluded_legacy_records(self):
        """legacy-exclusion: every identity-unresolvable record at or below
        the resolved identity-bearing latest round is excluded from the
        identity match and named in the advisory out-parameter; no raise."""
        import plan_readiness

        legacy_low = self._write_pair(
            "2026-08-01-plan-review-same-feature-r1", 1, None
        )
        legacy_same = self._write_pair(
            "2026-08-20-plan-review-same-feature-r2", 2, None
        )
        owned = self._write_pair(
            "2026-09-01-plan-review-same-feature-r2", 2, self.identity
        )
        advisories: list[str] = []
        found = plan_readiness.latest_review_round(
            self.reviews, "same-feature", self.identity, advisories
        )
        self.assertEqual(found, (owned, 2))
        self.assertEqual(len(advisories), 2)
        self.assertIn(legacy_low.name, advisories[0])
        self.assertIn(legacy_same.name, advisories[1])

    def test_rank_guard_refuses_unresolvable_round_above_resolved_round(self):
        """Safety witness: an identity-unresolvable record whose round
        outranks the resolved identity-bearing latest round refuses with a
        named reason identifying the outranking record."""
        import plan_readiness

        self._write_pair("2026-08-01-plan-review-same-feature-r1", 1, self.identity)
        outranker = self._write_pair(
            "2026-09-01-plan-review-same-feature-r2", 2, None
        )
        with self.assertRaises(plan_readiness.AmbiguousReviewSeries) as ctx:
            plan_readiness.latest_review_round(
                self.reviews, "same-feature", self.identity
            )
        self.assertIn(outranker.name, str(ctx.exception))
        self.assertIn("outranks", str(ctx.exception))

    def test_pure_legacy_series_resolves_lexically_with_advisory(self):
        """pure-legacy lexical fallback: zero identity-bearing records of
        any plan resolves the highest rN lexically (ties by filename,
        duplicate rounds included) with the advisory naming the lexical
        resolution; an identity-less invocation keeps the silent lexical
        resolution."""
        import plan_readiness

        self._write_pair("2026-08-01-plan-review-same-feature-r1", 1, None)
        self._write_pair("2026-08-15-plan-review-same-feature-r2", 2, None)
        tie_high = self._write_pair(
            "2026-09-01-plan-review-same-feature-r2", 2, None
        )
        advisories: list[str] = []
        found = plan_readiness.latest_review_round(
            self.reviews, "same-feature", self.identity, advisories
        )
        self.assertEqual(found, (tie_high, 2))
        self.assertEqual(len(advisories), 1)
        self.assertIn(tie_high.name, advisories[0])
        self.assertIn("lexical", advisories[0])

        silent_advisories: list[str] = []
        self.assertEqual(
            plan_readiness.latest_review_round(
                self.reviews, "same-feature", None, silent_advisories
            ),
            (tie_high, 2),
        )
        self.assertEqual(silent_advisories, [])

    def test_foreign_bearing_series_keeps_no_artifact_refusal(self):
        """Safety witness: identity-bearing records for other plans plus
        identity-unresolvable strays and a consulting plan owning none keep
        the no-artifact refusal; the strays never lexical-resolve the
        series."""
        import plan_readiness

        foreign = "docs/plans/2026-10-14-other-plan.md"
        self._write_pair("2026-08-01-plan-review-same-feature-r1", 1, foreign)
        self._write_pair("2026-09-01-plan-review-same-feature-r2", 2, foreign)
        self._write_pair("2026-08-15-plan-review-same-feature-r1", 1, None)
        advisories: list[str] = []
        found = plan_readiness.latest_review_round(
            self.reviews, "same-feature", self.identity, advisories
        )
        self.assertIsNone(found)
        self.assertTrue(
            all("lexical" not in entry for entry in advisories),
            advisories,
        )

    def test_duplicate_round_raise_and_silent_mismatch_exclusion_stay(self):
        """Safety witness: the duplicate-round raise stays for
        identity-bearing records, and a record naming a different source
        plan keeps the silent mismatch exclusion without an advisory."""
        import plan_readiness

        self._write_pair("2026-08-01-plan-review-same-feature-r1", 1, self.identity)
        self._write_pair("2026-09-01-plan-review-same-feature-r1", 1, self.identity)
        with self.assertRaises(plan_readiness.AmbiguousReviewSeries) as ctx:
            plan_readiness.latest_review_round(
                self.reviews, "same-feature", self.identity
            )
        self.assertIn("duplicate round(s): r1", str(ctx.exception))

        _clean_reviews_dir(self.reviews)
        self._write_pair(
            "2026-08-15-plan-review-same-feature-r1", 1, "docs/plans/other.md"
        )
        owned = self._write_pair(
            "2026-09-15-plan-review-same-feature-r2", 2, self.identity
        )
        advisories: list[str] = []
        found = plan_readiness.latest_review_round(
            self.reviews, "same-feature", self.identity, advisories
        )
        self.assertEqual(found, (owned, 2))
        self.assertEqual(advisories, [])

    def test_evaluate_readiness_threads_advisories_on_mixed_series(self):
        """The advisory out-parameter threads through ``evaluate_readiness``
        and the consult reaches its pass verdict on a mixed series."""
        import plan_readiness

        plan, _review = plan_readiness._write_clean_state(
            self.plans, self.reviews
        )
        legacy = self._write_pair(
            "2026-08-01-plan-review-fixture-feature-r1", 1, None
        )
        advisories: list[str] = []
        ok, reason = plan_readiness.evaluate_readiness(
            plan, self.plans, self.reviews, advisories
        )
        self.assertTrue(ok, reason)
        self.assertEqual(len(advisories), 1)
        self.assertIn(legacy.name, advisories[0])

    def test_main_prints_one_advisory_line_on_pass_path(self):
        """Advisory channel shape: ``main`` owns the list and prints one
        non-blocking advisory line beside the coverage warnings on the
        consult's pass path only."""
        import plan_readiness

        plan, _review = plan_readiness._write_clean_state(
            self.plans, self.reviews
        )
        legacy = self._write_pair(
            "2026-08-01-plan-review-fixture-feature-r1", 1, None
        )
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main([str(plan)])
        finally:
            os.chdir(prev)
        self.assertEqual(rc, 0, (out.getvalue(), err.getvalue()))
        advisory_lines = [
            line
            for line in err.getvalue().splitlines()
            if "review advisory" in line
        ]
        self.assertEqual(len(advisory_lines), 1)
        self.assertIn(legacy.name, advisory_lines[0])


class CanonicalStatsSkipWaiverTest(unittest.TestCase):
    """The narrowed stats-skip waiver (review-record legacy identity plan,
    Task 2).

    Every witness starts from the clean-state fixture pair
    (``_write_clean_state``, pre-fence date 2026-09-01 so no post-fence
    Markdown obligation crowds the waiver surface), declares the waiver in
    the record's Metadata, and validates the record through the staging
    validator directly. The Metadata ``Record kind:`` twin line is the only
    kind signal a sidecar-less record carries.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="stats-skip-waiver-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        import subprocess

        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        plan, review = _write_clean_state(self.plans, self.reviews)
        self.plan = plan
        self.review = review
        self.sidecar = review.with_suffix(".stats.json")

    def _declare_waiver(self, record_kind=None):
        """Rewrite the record's Metadata to declare the stats-skip waiver,
        optionally preceded by the ``Record kind:`` twin line."""
        lines = "- Stats sidecar: skipped\n"
        if record_kind is not None:
            lines = f"- Record kind: {record_kind}\n" + lines
        text = self.review.read_text(encoding="utf-8")
        self.review.write_text(
            text.replace("## Metadata\n", "## Metadata\n" + lines, 1),
            encoding="utf-8",
        )

    def test_canonical_twin_waiver_without_sidecar_refuses_with_missing_sidecar(self):
        """Waiver narrowing: a record whose ``Record kind:`` twin declares
        canonical and which declares the stats-skip waiver with zero staged
        findings and no sidecar file is refused with the reason naming the
        missing sidecar; before the narrowing this record passed staging
        validation (the RED witness)."""
        import validate_review_staging as vrs

        self._declare_waiver(record_kind="canonical")
        self.sidecar.unlink()
        result = vrs.validate_staging_file(self.review)
        self.assertFalse(
            result.ok,
            "canonical record declaring the stats-skip waiver passed "
            f"staging validation: errors={result.errors}",
        )
        self.assertTrue(
            any(
                "missing required stats sidecar" in error
                for error in result.errors
            ),
            result.errors,
        )

    def test_canonical_record_with_sidecar_present_validates_unchanged(self):
        """Safety witness: a canonical record with its sidecar present keeps
        today's validation outcome; the narrowing adds no finding."""
        import validate_review_staging as vrs

        self._declare_waiver(record_kind="canonical")
        result = vrs.validate_staging_file(self.review)
        self.assertEqual(result.errors, [], result.errors)
        self.assertTrue(result.ok, result.errors)

    def test_noncanonical_kind_keeps_the_waiver(self):
        """Scope guard: a record declaring a non-canonical kind
        (worker-evidence) keeps the stats-skip waiver available unchanged."""
        import validate_review_staging as vrs

        self._declare_waiver(record_kind="worker-evidence")
        self.sidecar.unlink()
        result = vrs.validate_staging_file(self.review)
        self.assertEqual(result.errors, [], result.errors)
        self.assertTrue(result.ok, result.errors)

    def test_undeclared_kind_waiver_refused_fail_closed(self):
        """Boundary witness: a canonical-intent record declaring the waiver
        with no readable ``Record kind:`` twin on a pre-fence-dated name or
        an undated name is refused fail-closed with the missing-sidecar
        reason, never silently honored."""
        import validate_review_staging as vrs

        self._declare_waiver(record_kind=None)
        self.sidecar.unlink()
        result = vrs.validate_staging_file(self.review)
        self.assertFalse(
            result.ok,
            "waiver without a Record kind twin was silently honored: "
            f"errors={result.errors}",
        )
        self.assertTrue(
            any(
                "missing required stats sidecar" in error
                for error in result.errors
            ),
            result.errors,
        )

        undated = self.reviews / "plan-review-fixture-feature-r1.md"
        undated.write_text(
            self.review.read_text(encoding="utf-8"), encoding="utf-8"
        )
        undated_result = vrs.validate_staging_file(undated)
        self.assertFalse(
            undated_result.ok,
            "waiver on an undated name was silently honored: "
            f"errors={undated_result.errors}",
        )
        self.assertTrue(
            any(
                "missing required stats sidecar" in error
                for error in undated_result.errors
            ),
            undated_result.errors,
        )

    def test_readiness_consult_waiver_disabled_refusal_text_unchanged(self):
        """Readiness parity: the consult's existing waiver-disabled path (it
        passes the expected digest and never honored the waiver) keeps its
        refusal text for a canonical record declaring the waiver without its
        sidecar."""
        self._declare_waiver(record_kind="canonical")
        self.sidecar.unlink()
        ok, reason = evaluate_readiness(self.plan, self.plans, self.reviews)
        self.assertFalse(ok)
        self.assertIsNotNone(reason)
        self.assertIn("missing stats sidecar", reason)


class _SidecarRepairFixture:
    """Shared temp-git-home fixture for the repair-tool witness classes.

    Every witness builds an isolated temp git home holding one canonical
    plan and the witnessed defective-pair shape: a post-fence re-bind round
    whose own Markdown carries the full review metadata while its stats
    sidecar is missing (the personal-project r4 shape; the live reviews
    home is read as the record-shape reference only and is never written
    by these witnesses). Hermeticity (review-record legacy identity plan,
    Task 4): no witness ever touches a live home; the live-home operation
    is the campaign run itself, verified by its census and receipt file.
    """

    PLAN_DATE = "2026-10-17"
    SLUG = "personal-project-remote-boundary-enforcement"
    RUN_ID = "de5777c115b2412e82d8ec7d6169110a"
    # Per-round mint ids for the composed-chain witness (each review round
    # mints its own pair, so a chain can carry a predecessor run id that
    # differs from the record's own).
    R2_RUN_ID = "2" * 32
    R3_RUN_ID = "3" * 32
    LAST_FIX = "e938c6cd5c76439f772141c53908b5fee4723438"
    STARTED_AT = "1792204576342"
    SELECTION_REASON = (
        "re-bind round after the citation-only correction"
    )

    def setUp(self):
        import subprocess

        import validate_review_staging as vrs
        from review_plan_identity import identity_token

        self.root = Path(tempfile.mkdtemp(prefix="sidecar-repair-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        self.plan = self.plans / f"{self.PLAN_DATE}-{self.SLUG}.md"
        self.plan.write_text(
            "# Fixture plan\n\n"
            "## Assumptions\n\n"
            "Decision points requiring a grill: none remain.\n\n"
            "Body.\n",
            encoding="utf-8",
        )
        self.identity = self.plan.relative_to(self.root).as_posix()
        self.digest = vrs.compute_source_digest("plan", self.plan.read_bytes())
        self.token = identity_token(self.identity)

    def _record_path(self, round_no=4, *, tokened=True):
        token = f"-p{self.token}" if tokened else ""
        return self.reviews / (
            f"{self.PLAN_DATE}-plan-review-{self.SLUG}{token}"
            f"-r{round_no}.md"
        )

    def _witnessed_markdown(
        self,
        round_no=4,
        *,
        with_kind_twin=True,
        with_identity=True,
        digest=None,
        run_id=None,
    ):
        """The witnessed r4-class record: every transcribed field sits on
        the record's own lines. ``run_id`` overrides the record's own mint
        pair (the composed-chain witness mints one run id per round)."""
        digest = digest or self.digest
        run_id = run_id or self.RUN_ID
        lines = [
            f"# Plan review: {self.SLUG} (r{round_no})",
            "",
            "## Metadata",
            "- Type: Plan Review",
        ]
        if with_kind_twin:
            lines.append("- Record kind: canonical")
        lines.append(f"- Date: {self.PLAN_DATE}")
        if with_identity:
            lines.append(f"- URL or Artifact: {self.identity}")
        lines += [
            "- Depth: focused",
            "- Domains: shell, python, git",
            f"- Round: r{round_no}",
            f"- review-run-id: {run_id}",
            f"- review-started-at-ms: {self.STARTED_AT}",
            "- Review mode: fresh-adversarial",
            "- Changed-risk signals: security-or-rollout-boundary",
            "- Prior findings supplied as filter: no",
            f"- Last fix commit: {self.LAST_FIX}",
            "- Witness ledger: N/A (no public mutators)",
            "- Coverage: clean",
            "- Release-gate ledger: none",
            "- Panel mode: focused",
            f"- Selection reason: {self.SELECTION_REASON}",
            f"- Source digest: {digest}",
            "- Findings: 0",
            "- Status: STAGED",
            "",
            "## Review Statistics",
            "",
            "### Panel",
            "| Worker | Lenses | Status | Raw | Solo | Echo | Relaunch "
            "| Parent worker |",
            "|--------|--------|--------|-----|------|------|----------"
            "|--------------|",
            "| correctness-completeness | quality, implementation "
            "| complete | 0 | 0 | 0 | no | none |",
            "",
            "### Counts",
            "- Workers launched: 1",
            "- Workers skipped: 0",
            "- Raw findings (all workers): 0",
            "- Staged findings: 0",
            "- Discarded during synthesis: 0",
            "- Solo staged (unique agent origin): 0",
            "- Echo staged (multi-agent dedup): 0",
            "",
            "### Deduplication groups",
            "None (each staged finding had a single agent origin).",
            "",
            "### Discarded findings",
            "None.",
            "",
            "### Severity calibration",
            "None (agent severities matched staged severities).",
            "",
            "### Triage outcomes",
            "Re-bind round: zero findings; the certification re-binds.",
            "",
            "## Findings",
            "",
            "### Critical",
            "",
            "None.",
            "",
            "### High",
            "",
            "None.",
            "",
            "### Medium",
            "",
            "None.",
            "",
            "### Low",
            "",
            "None.",
            "",
            "### Overflow manifest",
            "None.",
            "",
            "## Summary",
            "",
            "Re-bind verification: zero findings against the live bytes.",
            "",
            "Verdict: ready=yes",
            "",
        ]
        return "\n".join(lines)

    def _run_tool(self, *args):
        import regenerate_review_sidecar as rrs

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = rrs.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def _repair_witnessed_pair(self, round_no=4):
        record = self._record_path(round_no)
        record.write_text(
            self._witnessed_markdown(round_no), encoding="utf-8"
        )
        rc, out, err = self._run_tool(str(record))
        self.assertEqual(rc, 0, (out, err))
        self.assertIn(f"repaired: {record}", out)
        return record, record.with_suffix(".stats.json"), out


class RegenerateReviewSidecarTest(
    _SidecarRepairFixture, unittest.TestCase
):
    """The defective-pair repair tool (review-record legacy identity plan,
    Task 3)."""

    def test_taxonomy_partition_covers_the_required_field_set(self):
        """Transcription taxonomy (rule-closed set): the three classes are
        pairwise disjoint and jointly cover the complete version-1 required
        top-level field set plus the extended freshness set and the fenced
        members (coverage, record_kind); no required field is unassigned."""
        import validate_review_staging as vrs
        import regenerate_review_sidecar as rrs

        required = (
            set(vrs.V1_REQUIRED_TOP_LEVEL_FIELDS)
            | set(vrs.V1_EXTENDED_REQUIRED_FIELDS)
            | {"coverage", "record_kind"}
        )
        transcribed = set(rrs.TRANSCRIBED_FIELDS)
        derived = set(rrs.DERIVED_FIELDS)
        defaulted = set(rrs.DEFAULTED_FIELDS)
        self.assertFalse(transcribed & derived, "transcribed vs derived")
        self.assertFalse(transcribed & defaulted, "transcribed vs defaulted")
        self.assertFalse(derived & defaulted, "derived vs defaulted")
        self.assertEqual(
            transcribed | derived | defaulted,
            required | {"verdict"},
            "the partition must assign every required field exactly once",
        )

    def test_transcribed_class_reads_the_record_lines_verbatim(self):
        """Transcription taxonomy (transcribed class): every transcribed
        field equals the witnessed record's own line value."""
        import json

        _record, sidecar, _out = self._repair_witnessed_pair()
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(payload["source_digest"], self.digest)
        self.assertEqual(payload["verdict"], "yes")
        self.assertEqual(payload["round"], "r4")
        self.assertEqual(payload["date"], self.PLAN_DATE)
        self.assertEqual(payload["review_type"], "Plan Review")
        self.assertEqual(payload["panel_mode"], "focused")
        self.assertEqual(payload["selection_reason"], self.SELECTION_REASON)
        self.assertEqual(payload["review_mode"], "fresh-adversarial")
        self.assertEqual(
            payload["risk_signals"], ["security-or-rollout-boundary"]
        )
        self.assertIs(payload["prior_findings_filter"], False)
        self.assertEqual(payload["last_fix_commit"], self.LAST_FIX)
        self.assertEqual(
            payload["counts"],
            {
                "workers_launched": 1,
                "raw_findings": 0,
                "staged_findings": 0,
                "discarded": 0,
                "solo_staged": 0,
                "echo_staged": 0,
            },
        )
        self.assertEqual(payload["findings"], [])
        self.assertEqual(
            payload["panel"],
            [
                {
                    "worker": "correctness-completeness",
                    "lenses": ["quality", "implementation"],
                    "parent_worker": None,
                    "status": "complete",
                    "raw": 0,
                    "solo": 0,
                    "echo": 0,
                    "relaunch": False,
                    "descendant_launches": [],
                }
            ],
        )
        self.assertEqual(
            payload["extensions"]["plan_identity"], self.identity
        )
        self.assertEqual(payload["depth"], "focused")
        self.assertEqual(payload["domains"], ["shell", "python", "git"])

    def test_derived_fields_follow_the_named_constants(self):
        """Transcription taxonomy (derived fields): schema_version 1,
        source_kind plan, record_kind canonical, artifact_slug from the
        transcribed identity's plan path, and the coverage object built
        only from the record's Coverage and panel lines."""
        import json

        _record, sidecar, _out = self._repair_witnessed_pair()
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["source_kind"], "plan")
        self.assertEqual(payload["record_kind"], "canonical")
        self.assertEqual(payload["artifact_slug"], self.SLUG)
        self.assertEqual(
            payload["coverage"],
            {
                "outcome": "clean",
                "material_lens_set": ["implementation", "quality"],
                "completed": ["implementation", "quality"],
                "missing": [],
            },
        )
        self.assertIs(
            payload["extensions"]["regenerated_from_markdown"], True
        )

    def test_defaulted_fields_carry_the_empty_forms(self):
        """Transcription taxonomy (defaulted fields): the defaulted-empty
        fields carry the empty forms; no evidence-bearing field is ever
        defaulted."""
        import json

        _record, sidecar, _out = self._repair_witnessed_pair()
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertIsNone(payload["escalation_reason"])
        for name in (
            "soften_watchlist",
            "deduplication_groups",
            "discarded",
            "overflow",
            "severity_calibration",
            "triage_outcomes",
        ):
            self.assertEqual(payload[name], [], name)

    def test_self_heal_member_follows_the_chain_rule(self):
        """Transcription taxonomy (self-heal member): a repaired round of 1
        derives the unused status bound to the record's own run id; a valid
        post-fence canonical prior round carries the prior chain state
        verbatim; unavailable prior evidence derives the unknown status
        bound to the record's own run id."""
        import json

        def _state(path):
            payload = json.loads(
                path.with_suffix(".stats.json").read_text(encoding="utf-8")
            )
            return payload["extensions"]["convergence"]["self_heal_attempt"]

        r1 = self._record_path(1)
        r1.write_text(self._witnessed_markdown(1), encoding="utf-8")
        rc, out, _err = self._run_tool(str(r1))
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            _state(r1), {"status": "unused", "run_id": self.RUN_ID}
        )

        # r3 first: its prior r2 record exists but carries no sidecar, so
        # the prior evidence is unavailable.
        r2 = self._record_path(2)
        r2.write_text(self._witnessed_markdown(2), encoding="utf-8")
        r3 = self._record_path(3)
        r3.write_text(self._witnessed_markdown(3), encoding="utf-8")
        rc, out, _err = self._run_tool(str(r3))
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            _state(r3), {"status": "unknown", "run_id": self.RUN_ID}
        )

        # Repairing r2 after r1: the valid post-fence canonical prior
        # carries its chain state verbatim (same run id and status).
        rc, out, _err = self._run_tool(str(r2))
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            _state(r2), {"status": "unused", "run_id": self.RUN_ID}
        )

    def test_record_kind_twin_append_is_the_only_markdown_write(self):
        """Record-kind twin append: a post-fence record whose Markdown
        lacks the twin gains exactly the one appended line, and the
        repaired pair passes the record-kind gate."""
        import validate_review_staging as vrs

        record = self._record_path(4)
        record.write_text(
            self._witnessed_markdown(4, with_kind_twin=False),
            encoding="utf-8",
        )
        before = record.read_text(encoding="utf-8")
        rc, out, err = self._run_tool(str(record))
        self.assertEqual(rc, 0, (out, err))
        after = record.read_text(encoding="utf-8")
        self.assertEqual(
            after,
            before.replace(
                "## Metadata\n",
                "## Metadata\n- Record kind: canonical\n",
                1,
            ),
        )
        result = vrs.validate_staging_file(
            record,
            hard=True,
            expected_digest=self.digest,
            source_kind="plan",
        )
        self.assertEqual(result.errors, [], result.errors)

    def test_record_already_carrying_the_twin_receives_no_second_line(self):
        record, _sidecar, _out = self._repair_witnessed_pair()
        self.assertEqual(
            record.read_text(encoding="utf-8").count(
                "- Record kind: canonical"
            ),
            1,
        )

    def test_dry_run_prints_both_sets_and_writes_nothing(self):
        good = self._record_path(4)
        good.write_text(self._witnessed_markdown(4), encoding="utf-8")
        stray = self._record_path(5)
        stray.write_text(
            self._witnessed_markdown(5, with_identity=False),
            encoding="utf-8",
        )
        before_good = good.read_text(encoding="utf-8")
        receipt = self.root / "receipt.md"
        rc, out, _err = self._run_tool(
            "--dry-run", "--receipt", str(receipt), str(good), str(stray)
        )
        self.assertEqual(rc, 0, out)
        self.assertIn(f"would-repair: {good}", out)
        self.assertIn(f"would-refuse: {stray}", out)
        self.assertFalse(receipt.exists(), "dry-run must write nothing")
        self.assertFalse(good.with_suffix(".stats.json").exists())
        self.assertFalse(stray.with_suffix(".stats.json").exists())
        self.assertEqual(good.read_text(encoding="utf-8"), before_good)

    def test_real_run_writes_a_receipt_beside_the_console_census(self):
        good = self._record_path(4)
        good.write_text(self._witnessed_markdown(4), encoding="utf-8")
        bad = self._record_path(5)
        bad.write_text(
            self._witnessed_markdown(5, with_identity=False),
            encoding="utf-8",
        )
        receipt = self.root / "receipt.md"
        rc, out, _err = self._run_tool(
            "--receipt", str(receipt), str(good), str(bad)
        )
        self.assertEqual(rc, 0, out)
        self.assertIn(f"repaired: {good}", out)
        self.assertIn(f"refused: {bad}", out)
        text = receipt.read_text(encoding="utf-8")
        self.assertIn(str(good), text)
        self.assertIn(str(bad), text)

    def test_stale_digest_refuses_at_repair_time_and_leaves_no_sidecar(self):
        record = self._record_path(4)
        record.write_text(
            self._witnessed_markdown(4, digest="ab" * 32), encoding="utf-8"
        )
        rc, out, _err = self._run_tool(str(record))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"refused: {record}", out)
        self.assertIn("digest", out)
        self.assertFalse(record.with_suffix(".stats.json").exists())

    def test_stale_digest_refusal_on_a_twinless_record_restores_the_markdown(self):
        """Delete-on-refusal Markdown restoration: a stale-digest refusal
        on a record whose Markdown lacks the ``Record kind:`` twin (the
        tool appends the twin, then refuses the in-place validation)
        restores the Markdown byte-identical to the original (no appended
        twin remains), leaves no sidecar file, and names the refused pair
        in the census."""
        record = self._record_path(4)
        record.write_text(
            self._witnessed_markdown(4, with_kind_twin=False, digest="ab" * 32),
            encoding="utf-8",
        )
        before = record.read_text(encoding="utf-8")
        rc, out, _err = self._run_tool(str(record))
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            record.read_text(encoding="utf-8"),
            before,
            "the Markdown must be restored byte-identical on refusal",
        )
        self.assertNotIn(
            "- Record kind: canonical",
            record.read_text(encoding="utf-8"),
            "no appended twin line may remain after the refusal",
        )
        self.assertFalse(record.with_suffix(".stats.json").exists())
        self.assertIn(f"refused: {record}", out)
        self.assertIn("digest", out)

    def test_moved_plan_refuses_with_no_sidecar(self):
        record = self._record_path(4)
        record.write_text(self._witnessed_markdown(4), encoding="utf-8")
        self.plan.unlink()
        rc, out, _err = self._run_tool(str(record))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"refused: {record}", out)
        self.assertFalse(record.with_suffix(".stats.json").exists())

    def test_incomplete_record_refuses_without_writing(self):
        record = self._record_path(4)
        text = self._witnessed_markdown(4)
        record.write_text(
            text.replace("- Source digest: ", "- Recorded digest: ", 1),
            encoding="utf-8",
        )
        before = record.read_text(encoding="utf-8")
        rc, out, _err = self._run_tool(str(record))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"refused: {record}", out)
        self.assertIn("Source digest", out)
        self.assertFalse(record.with_suffix(".stats.json").exists())
        self.assertEqual(record.read_text(encoding="utf-8"), before)

    def test_foreign_sidecar_is_never_overwritten(self):
        import json

        record = self._record_path(4)
        record.write_text(self._witnessed_markdown(4), encoding="utf-8")
        sidecar = record.with_suffix(".stats.json")
        foreign = {"schema_version": 1, "source_digest": "cd" * 32}
        sidecar.write_text(json.dumps(foreign), encoding="utf-8")
        before_md = record.read_text(encoding="utf-8")
        rc, out, _err = self._run_tool(str(record))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"refused: {record}", out)
        self.assertIn("overwrite", out)
        self.assertEqual(
            json.loads(sidecar.read_text(encoding="utf-8")), foreign
        )
        self.assertEqual(record.read_text(encoding="utf-8"), before_md)

    def test_corrected_markdown_retry_rewrites_its_own_marker_sidecar(self):
        import json

        record, sidecar, _out = self._repair_witnessed_pair()
        record.write_text(
            record.read_text(encoding="utf-8").replace(
                f"- Selection reason: {self.SELECTION_REASON}",
                "- Selection reason: corrected re-bind reason",
            ),
            encoding="utf-8",
        )
        rc, out, _err = self._run_tool(str(record))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"repaired: {record}", out)
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["selection_reason"], "corrected re-bind reason"
        )
        self.assertIs(
            payload["extensions"]["regenerated_from_markdown"], True
        )

    def test_no_identity_guess_from_the_slug(self):
        record = self._record_path(4)
        record.write_text(
            self._witnessed_markdown(4, with_identity=False),
            encoding="utf-8",
        )
        rc, out, _err = self._run_tool(str(record))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"refused: {record}", out)
        self.assertIn("guess", out.lower())
        self.assertFalse(record.with_suffix(".stats.json").exists())

    def test_repaired_pair_passes_validation_and_the_strict_consult(self):
        """The repaired pair passes the shared staging validation and the
        strict readiness consult reaches its pass verdict on the series."""
        import plan_readiness
        import validate_review_staging as vrs

        record, _sidecar, _out = self._repair_witnessed_pair()
        result = vrs.validate_staging_file(
            record,
            hard=True,
            expected_digest=self.digest,
            source_kind="plan",
        )
        self.assertEqual(result.errors, [], result.errors)
        ok, reason = plan_readiness.evaluate_readiness(
            self.plan, self.plans, self.reviews
        )
        self.assertTrue(ok, reason)


class RegeneratedSidecarIntegrationTest(
    _SidecarRepairFixture, unittest.TestCase
):
    """Task 4 integration witnesses (review-record legacy identity plan).

    The regenerated sidecar inside the validators: the taxonomy partition
    pinned against the tool's actual output, the write bounds of a real
    run, the self-heal chain rule's remaining arms (unnumbered, malformed,
    pre-fence, and non-canonical prior evidence), the composed-chain
    run-id-continuity refusal with its bounded retry, the refusal paths
    named in census and receipt, the marker tolerance asserted in both
    directions, and the regeneration notice on the consult's advisory
    channel. Every witness builds an isolated temp home; the live-home run
    is the campaign operation whose verification is its printed census and
    receipt file.
    """

    def _home_snapshot(self):
        """Working-tree file inventory of the temp home (.git excluded)."""
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and ".git" not in path.parts
        }

    def test_regenerated_payload_top_level_keys_stay_partition_assigned(self):
        """Taxonomy completeness: every top-level key of an actually
        regenerated payload is assigned within the rule-closed partition;
        ``extensions`` is its own taxonomy arm (identity, convergence chain
        state, and the regeneration marker)."""
        import json

        import regenerate_review_sidecar as rrs

        _record, sidecar, _out = self._repair_witnessed_pair()
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        assigned = (
            set(rrs.TRANSCRIBED_FIELDS)
            | set(rrs.DERIVED_FIELDS)
            | set(rrs.DEFAULTED_FIELDS)
            | set(rrs.OPTIONAL_TRANSCRIBED_FIELDS)
        )
        self.assertEqual(
            set(payload) - assigned,
            {"extensions"},
            "every top-level payload key must be partition-assigned",
        )
        self.assertIs(
            payload["extensions"]["regenerated_from_markdown"], True
        )

    def test_write_bounds_real_run_writes_sidecar_twin_line_and_receipt_only(self):
        """Safety witness (write bounds): a real run's total writes are
        exactly the sidecar, the appended twin line, and the receipt file;
        the repaired Markdown differs from the original by exactly the
        appended twin line, and the written sidecar carries the marker."""
        import json

        record = self._record_path(4)
        record.write_text(
            self._witnessed_markdown(4, with_kind_twin=False),
            encoding="utf-8",
        )
        before = self._home_snapshot()
        receipt = self.root / "receipt.md"
        rc, out, _err = self._run_tool("--receipt", str(receipt), str(record))
        self.assertEqual(rc, 0, out)
        after = self._home_snapshot()
        record_key = str(record.relative_to(self.root))
        sidecar_key = str(
            record.with_suffix(".stats.json").relative_to(self.root)
        )
        receipt_key = str(receipt.relative_to(self.root))
        self.assertEqual(
            set(after) - set(before),
            {sidecar_key, receipt_key},
            "a real run adds exactly the sidecar and the receipt file",
        )
        self.assertEqual(
            {
                name
                for name in set(before) & set(after)
                if before[name] != after[name]
            },
            {record_key},
            "a real run modifies exactly the record's Markdown",
        )
        original = before[record_key].decode("utf-8")
        self.assertEqual(
            after[record_key].decode("utf-8"),
            original.replace(
                "## Metadata\n", "## Metadata\n- Record kind: canonical\n", 1
            ),
            "the Markdown delta must be exactly the appended twin line",
        )
        payload = json.loads(after[sidecar_key].decode("utf-8"))
        self.assertIs(
            payload["extensions"]["regenerated_from_markdown"], True
        )
        self.assertIn(str(record), receipt.read_text(encoding="utf-8"))

    def test_unnumbered_round_derives_unused_status_bound_to_own_run_id(self):
        """Self-heal chain rule (unnumbered arm): a repaired record with no
        ``-rN`` suffix derives the unused status bound to its own run
        id."""
        import json

        unnumbered = self.reviews / (
            f"{self.PLAN_DATE}-plan-review-{self.SLUG}-p{self.token}.md"
        )
        unnumbered.write_text(self._witnessed_markdown(1), encoding="utf-8")
        rc, out, _err = self._run_tool(str(unnumbered))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"repaired: {unnumbered}", out)
        payload = json.loads(
            unnumbered.with_suffix(".stats.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            payload["extensions"]["convergence"]["self_heal_attempt"],
            {"status": "unused", "run_id": self.RUN_ID},
        )

    def _repair_r2_over_prior_sidecar(self, prior_sidecar_text, prior_name):
        """One r2 repair over a prior r1 whose sidecar carries
        ``prior_sidecar_text``; returns the r2 self-heal state."""
        import json

        prior = self.reviews / prior_name
        prior.write_text(self._witnessed_markdown(1), encoding="utf-8")
        prior.with_suffix(".stats.json").write_text(
            prior_sidecar_text, encoding="utf-8"
        )
        r2 = self._record_path(2)
        r2.write_text(self._witnessed_markdown(2), encoding="utf-8")
        rc, out, _err = self._run_tool(str(r2))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"repaired: {r2}", out)
        payload = json.loads(
            r2.with_suffix(".stats.json").read_text(encoding="utf-8")
        )
        return payload["extensions"]["convergence"]["self_heal_attempt"]

    def test_malformed_prior_sidecar_derives_unknown_status_bound_to_own_run_id(self):
        """Self-heal chain rule (malformed prior arm): a prior sidecar that
        is unreadable JSON derives the unknown status bound to the
        record's own run id."""
        state = self._repair_r2_over_prior_sidecar(
            "{broken",
            f"{self.PLAN_DATE}-plan-review-{self.SLUG}-p{self.token}-r1.md",
        )
        self.assertEqual(
            state, {"status": "unknown", "run_id": self.RUN_ID}
        )

    def test_pre_fence_prior_derives_unknown_status_bound_to_own_run_id(self):
        """Self-heal chain rule (pre-fence prior arm): a prior round dated
        before the self-heal fence derives the unknown status bound to the
        record's own run id."""
        import json

        state = self._repair_r2_over_prior_sidecar(
            json.dumps(
                {"record_kind": "canonical", "date": "2026-08-01"}
            ),
            f"2026-08-01-plan-review-{self.SLUG}-p{self.token}-r1.md",
        )
        self.assertEqual(
            state, {"status": "unknown", "run_id": self.RUN_ID}
        )

    def test_non_canonical_prior_derives_unknown_status_bound_to_own_run_id(self):
        """Self-heal chain rule (non-canonical prior arm): a prior round
        whose sidecar declares a non-canonical record kind derives the
        unknown status bound to the record's own run id."""
        state = self._repair_r2_over_prior_sidecar(
            '{"record_kind": "worker-evidence", "date": "%s"}'
            % self.PLAN_DATE,
            f"{self.PLAN_DATE}-plan-review-{self.SLUG}-p{self.token}-r1.md",
        )
        self.assertEqual(
            state, {"status": "unknown", "run_id": self.RUN_ID}
        )

    def test_composed_chain_run_id_continuity_refusal_and_bounded_retry(self):
        """Composed-chain witness: defective r2 and r3 beside a valid r1;
        repairing r3 then r2 leaves r3's full in-place validation refusing
        with the run-id continuity reason (r3 derived its own run id while
        r2 was unavailable), and a bounded-retry re-run of the tool on r3
        (its own marker-bearing sidecar permits the rewrite) ends with the
        full staging validation of r3 passing."""
        import json

        import validate_review_staging as vrs

        r1 = self._record_path(1)
        r1.write_text(self._witnessed_markdown(1), encoding="utf-8")
        rc, out, _err = self._run_tool(str(r1))
        self.assertIn(f"repaired: {r1}", out)
        r2 = self._record_path(2)
        r2.write_text(
            self._witnessed_markdown(2, run_id=self.R2_RUN_ID),
            encoding="utf-8",
        )
        r3 = self._record_path(3)
        r3.write_text(
            self._witnessed_markdown(3, run_id=self.R3_RUN_ID),
            encoding="utf-8",
        )

        # r3 first: its prior r2 is still sidecar-less, so r3 derives the
        # unknown status bound to its own run id and repairs.
        rc, out, _err = self._run_tool(str(r3))
        self.assertIn(f"repaired: {r3}", out)
        state = json.loads(
            r3.with_suffix(".stats.json").read_text(encoding="utf-8")
        )["extensions"]["convergence"]["self_heal_attempt"]
        self.assertEqual(
            state, {"status": "unknown", "run_id": self.R3_RUN_ID}
        )

        # r2 next: the valid post-fence canonical r1 carries its chain
        # state verbatim.
        rc, out, _err = self._run_tool(str(r2))
        self.assertIn(f"repaired: {r2}", out)

        # r3's full in-place validation now refuses with the run-id
        # continuity reason.
        result = vrs.validate_staging_file(
            r3, hard=True, expected_digest=self.digest, source_kind="plan"
        )
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            any(
                "run_id cannot change after r1" in error
                for error in result.errors
            ),
            result.errors,
        )

        # Bounded retry: r3's own marker-bearing sidecar permits the
        # rewrite, the chain rule now carries r2's state verbatim, and the
        # full staging validation of r3 passes.
        rc, out, _err = self._run_tool(str(r3))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"repaired: {r3}", out)
        state = json.loads(
            r3.with_suffix(".stats.json").read_text(encoding="utf-8")
        )["extensions"]["convergence"]["self_heal_attempt"]
        self.assertEqual(state, {"status": "unused", "run_id": self.RUN_ID})
        result = vrs.validate_staging_file(
            r3, hard=True, expected_digest=self.digest, source_kind="plan"
        )
        self.assertEqual(result.errors, [], result.errors)

    def test_stale_digest_refusal_names_the_pair_in_census_and_receipt(self):
        """Refusal-path witness (stale digest): a complete record whose
        recorded Source digest mismatches the live plan bytes is refused
        with the digest reason, named in both census and receipt, and
        leaves no sidecar file."""
        record = self._record_path(4)
        record.write_text(
            self._witnessed_markdown(4, digest="ab" * 32), encoding="utf-8"
        )
        receipt = self.root / "receipt.md"
        rc, out, _err = self._run_tool("--receipt", str(receipt), str(record))
        self.assertEqual(rc, 0, out)
        self.assertIn(f"refused: {record}", out)
        self.assertIn("digest", out)
        receipt_text = receipt.read_text(encoding="utf-8")
        self.assertIn(str(record), receipt_text)
        self.assertIn("digest", receipt_text)
        self.assertFalse(record.with_suffix(".stats.json").exists())

    def test_marker_tolerance_asserted_not_extended(self):
        """Tolerance asserted, not extended: the validator's open-extensions
        handling accepts the marker on a valid pair, and the negative
        direction is pinned (a marker-bearing sidecar with a stale digest
        or a failing gate still refuses, so no gate keys tolerance on the
        marker)."""
        import json

        import validate_review_staging as vrs

        record, sidecar, _out = self._repair_witnessed_pair()

        def _mutate(mutator):
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            mutator(payload)
            sidecar.write_text(json.dumps(payload), encoding="utf-8")

        def _validate():
            return vrs.validate_staging_file(
                record,
                hard=True,
                expected_digest=self.digest,
                source_kind="plan",
            )

        # Positive: the marker-bearing regenerated pair passes.
        self.assertEqual(_validate().errors, [])
        # Descriptive-only: flipping the marker changes nothing.
        _mutate(
            lambda payload: payload["extensions"].__setitem__(
                "regenerated_from_markdown", False
            )
        )
        self.assertEqual(_validate().errors, [])
        # Negative: a marker-bearing sidecar with a stale digest refuses.
        _mutate(
            lambda payload: (
                payload["extensions"].__setitem__(
                    "regenerated_from_markdown", True
                ),
                payload.__setitem__("source_digest", "ab" * 32),
            )
        )
        result = _validate()
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            any("digest" in error.lower() for error in result.errors),
            result.errors,
        )
        # Negative: a marker-bearing sidecar failing an unrelated gate
        # (sidecar round vs staging filename) refuses too.
        _mutate(
            lambda payload: (
                payload.__setitem__("source_digest", self.digest),
                payload.__setitem__("round", "r5"),
            )
        )
        result = _validate()
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            any("round" in error for error in result.errors), result.errors
        )

    def test_regeneration_notice_exactly_when_marker_present(self):
        """Regeneration notice: the consult resolving a marker-bearing
        sidecar appends exactly one report-only notice through the advisory
        channel (main prints it on the pass path); a sidecar without the
        marker produces no notice; the verdict never changes."""
        import json

        record, sidecar, _out = self._repair_witnessed_pair()

        def _consult():
            advisories: list[str] = []
            ok, reason = evaluate_readiness(
                self.plan, self.plans, self.reviews, advisories
            )
            return ok, reason, advisories

        ok, reason, advisories = _consult()
        self.assertTrue(ok, reason)
        notices = [entry for entry in advisories if "regenerated" in entry]
        self.assertEqual(len(notices), 1, advisories)
        self.assertIn(record.with_suffix(".stats.json").name, notices[0])

        # No marker, no notice, same verdict.
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        del payload["extensions"]["regenerated_from_markdown"]
        sidecar.write_text(json.dumps(payload), encoding="utf-8")
        ok, reason, advisories = _consult()
        self.assertTrue(ok, reason)
        self.assertEqual(
            [entry for entry in advisories if "regenerated" in entry],
            [],
            advisories,
        )

        # The notice rides main's single pass-path advisory line.
        payload["extensions"]["regenerated_from_markdown"] = True
        sidecar.write_text(json.dumps(payload), encoding="utf-8")
        import plan_readiness

        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = plan_readiness.main([str(self.plan)])
        finally:
            os.chdir(prev)
        self.assertEqual(rc, 0, (out.getvalue(), err.getvalue()))
        advisory_lines = [
            line
            for line in err.getvalue().splitlines()
            if "review advisory" in line
        ]
        self.assertEqual(len(advisory_lines), 1)
        self.assertIn("regenerated", advisory_lines[0])


class CapClosureContractTest(unittest.TestCase):
    """The ``validate_cap_closure_contract`` shape gate (contract level).

    Uses the version-1-only
    with unknown-key rejection, called with the ``payload, result,
    schema_class`` idiom. The negative cases are table-driven and include
    declarations whose unknown keys are themselves named with the routed
    literals (the producer-echo path); the routed-substring arm pins the
    negative-literal routing contract as a suite invariant: every reported
    problem is static text plus filtered echoes (no problem may contain
    the step-3 routed substrings), so the readiness mapping can never
    misclassify a declaration rejection as a stale-digest or source-kind
    failure.
    """

    def _payload(self, declaration=None, round_value=CAP_CLOSURE_ROUND):
        payload = vrs._version1_payload()
        payload["review_type"] = "plan"
        payload["source_kind"] = "plan"
        payload["round"] = round_value
        if declaration is not None:
            payload["extensions"] = {"cap_closure": declaration}
        return payload

    def _validate(self, payload, schema_class="current-v1"):
        result = vrs.ValidationResult(path=Path("cap-closure-fixture.md"))
        vrs.validate_cap_closure_contract(
            payload, result, schema_class=schema_class
        )
        return result

    @staticmethod
    def _targeted(result, fragment):
        return [
            error
            for error in result.errors
            if "extensions.cap_closure" in error and fragment in error
        ]

    def _rejection_cases(self):
        """``(name, payload, targeted fragment)`` for every rejection arm;
        shared by the malformed-declaration and routed-substring tests."""
        cases = []
        for name, key in (
            ("missing plan_section", "plan_section"),
            ("missing round", "round"),
            ("missing residuals", "residuals"),
            ("missing pre_fold_digest", "pre_fold_digest"),
        ):
            declaration = _cap_closure_declaration()
            del declaration[key]
            cases.append(
                (
                    name,
                    self._payload(declaration),
                    f"missing required key '{key}'",
                )
            )
        for name, key in (
            ("unknown key", "scheme"),
            ("unknown key named source_digest", "source_digest"),
            ("unknown key named source_kind", "source_kind"),
        ):
            unknown = _cap_closure_declaration()
            unknown[key] = "extra"
            cases.append(
                (
                    name,
                    self._payload(unknown),
                    "accepts only the keys",
                )
            )
        cases.append(
            (
                "wrong plan_section literal",
                self._payload(
                    _cap_closure_declaration(plan_section="## Wrong section")
                ),
                "must be exactly",
            )
        )
        cases.append(
            (
                "float round",
                self._payload(_cap_closure_declaration(round=1.5)),
                "must be an integer or a string",
            )
        )
        cases.append(
            (
                "boolean round",
                self._payload(_cap_closure_declaration(round=True)),
                "boolean excluded",
            )
        )
        cases.append(
            (
                "round differs from sidecar",
                self._payload(_cap_closure_declaration(round="6")),
                "must equal the sidecar round",
            )
        )
        cases.append(
            (
                "unparsable round",
                self._payload(
                    _cap_closure_declaration(round="cap"), round_value="cap"
                ),
                "does not parse as an integer",
            )
        )
        for name, value in (
            ("negative residuals", -1),
            ("string residuals", "1"),
            ("boolean residuals", True),
        ):
            cases.append(
                (
                    name,
                    self._payload(_cap_closure_declaration(residuals=value)),
                    "must be a non-negative integer",
                )
            )
        for name, value in (
            ("non-hex pre_fold_digest", "not-hex"),
            ("uppercase pre_fold_digest", "A" * 64),
        ):
            cases.append(
                (
                    name,
                    self._payload(
                        _cap_closure_declaration(pre_fold_digest=value)
                    ),
                    "must be a lowercase 64-character hex",
                )
            )
        cases.append(
            (
                "pre_fold_digest equals the bound digest",
                self._payload(
                    _cap_closure_declaration(pre_fold_digest="0" * 64)
                ),
                "must differ",
            )
        )
        return cases

    def test_cap_closure_contract_rejects_malformed_declarations(self):
        """Every malformed declaration reports its specific problem, and
        every problem names ``extensions.cap_closure``."""
        for name, payload, fragment in self._rejection_cases():
            with self.subTest(case=name):
                result = self._validate(payload)
                self.assertFalse(result.ok, result.errors)
                self.assertTrue(
                    self._targeted(result, fragment), result.errors
                )

    def test_cap_closure_contract_enforces_minimum_round_floor(self):
        """The floor pins both directions: "2"/2 fails, "3"/3 passes."""
        below = self._payload(
            _cap_closure_declaration(round="2"), round_value=2
        )
        result = self._validate(below)
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            self._targeted(result, "below CAP_CLOSURE_MIN_ROUND"),
            result.errors,
        )
        at = self._payload(
            _cap_closure_declaration(round="3"), round_value=3
        )
        result = self._validate(at)
        self.assertEqual([], result.errors)

    def test_cap_closure_contract_rejections_avoid_routed_substrings(self):
        """Every reported problem across all rejection arms avoids the
        step-3 routed substrings (``source_digest``, ``source_kind``,
        ``missing the required 'coverage' object``) and names
        ``extensions.cap_closure``, so the readiness error mapping can
        never route a declaration rejection into the wrong family. The
        arms include unknown keys named with the routed literals
        themselves (the producer-echo path: rejection messages are static
        templates plus filtered echoes and never repeat such text)."""
        collected = []
        for _name, payload, _fragment in self._rejection_cases():
            collected.extend(self._validate(payload).errors)
        versionless = self._payload(_cap_closure_declaration())
        del versionless["schema_version"]
        collected.extend(
            self._validate(versionless, schema_class="legacy").errors
        )
        self.assertTrue(collected)
        for error in collected:
            with self.subTest(error=error):
                self.assertIn("extensions.cap_closure", error)
                self.assertNotIn("source_digest", error)
                self.assertNotIn("source_kind", error)
                self.assertNotIn(
                    "missing the required 'coverage' object", error
                )

    def test_cap_closure_contract_accepts_int_typed_declaration_round(self):
        """Sidecar round ``"5"`` (string) with declaration round ``5``
        (integer): both sides normalize through ``str()``, the mirrored
        pairing of the string-declaration accept arm."""
        payload = self._payload(
            _cap_closure_declaration(round=5), round_value="5"
        )
        result = self._validate(payload)
        self.assertEqual([], result.errors)

    def test_cap_closure_contract_rejects_versionless_carrier(self):
        """A versionless legacy payload carrying ``extensions.cap_closure``
        fails closed at the version boundary (mirrors the sibling's
        schema-version-removed case)."""
        payload = self._payload(_cap_closure_declaration())
        del payload["schema_version"]
        result = self._validate(payload, schema_class="legacy")
        self.assertFalse(result.ok, result.errors)
        self.assertTrue(
            self._targeted(result, "version boundary"), result.errors
        )


class CapClosureReadinessTest(unittest.TestCase):
    """The readiness-gate acceptance of the cap-closure terminal shape.

    Fixture recipe (per the plan): full version-1 records adapted from
    ``vrs._version1_payload`` (``review_type``/``source_kind`` plan,
    ``verdict`` matching the arm, ``artifact_slug``/``round`` matching the
    fixture slug and round grammar, ``source_digest`` bound to the fixture
    plan bytes, findings mirrored into the review Markdown), with BOTH the
    sidecar ``date`` and the round filename's leading date below the
    structural fences so the gated probes stay exempt. Blocking rows in
    accept-derived arms carry a resolved ``fixed`` triage on both record
    surfaces. Guards (ordinary rounds, no-verdict-without-declaration,
    stale digest, conforming yes verdict) pin today's behavior; every
    other arm was RED before the gate probe existed (RED-first witness).
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="cap-closure-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.plans = self.root / "plans"
        self.reviews = self.root / "reviews"
        self.plans.mkdir()
        self.reviews.mkdir()

    # -- fixture builders --------------------------------------------------

    def _plan_text(
        self,
        patterns=(CAP_CLOSURE_PATTERN,),
        *,
        omit_section=False,
        body=None,
        trailer=False,
        first_empty_second_body=None,
    ):
        parts = ["# Cap closure fixture plan", "", "Body."]
        if trailer:
            parts.extend(
                [
                    "",
                    "## Assumptions",
                    "",
                    "Decision points requiring a grill: none remain.",
                ]
            )
        if not omit_section:
            parts.extend(["", CAP_CLOSURE_SECTION, ""])
            if first_empty_second_body is not None:
                # First section stays empty; a later identical heading
                # carries the body (the first occurrence must govern).
                parts.extend(
                    ["", CAP_CLOSURE_SECTION, "", first_empty_second_body]
                )
            elif body is not None:
                parts.append(body)
            else:
                parts.extend(
                    f"- {pattern} (disposition: accepted)"
                    for pattern in patterns
                )
        return "\n".join(parts) + "\n"

    def _quote_only_plan_text(self):
        """The heading appears only inside a fenced block and as a ``###``
        heading; neither is a line-anchored level-2 heading."""
        return (
            "# Cap closure fixture plan\n\nBody.\n\n"
            "```markdown\n"
            f"{CAP_CLOSURE_SECTION}\n"
            f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)\n"
            "```\n\n"
            f"### {CAP_CLOSURE_SECTION[3:]}\n\n"
            f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)\n"
        )

    def _markdown(self, findings):
        """Review Markdown mirroring ``findings`` (id, severity, blocking,
        triage, and the ``- **Pattern**:`` bullet per finding)."""
        md = vrs._current_findings_markdown(findings, title=CAP_CLOSURE_SLUG)
        patterns = {
            row["id"]: row["pattern"]
            for row in findings
            if isinstance(row, dict) and "pattern" in row
        }
        if not patterns:
            return md
        out = []
        current = None
        for line in md.splitlines():
            out.append(line)
            header = re.match(r"#### F(\d+)\.", line)
            if header:
                current = int(header.group(1))
            elif line.startswith("- **Triage**:") and current in patterns:
                out.append(f"- **Pattern**: {patterns[current]}")
                current = None
        return "\n".join(out) + "\n"

    def _sidecar(
        self,
        digest_source_bytes,
        findings,
        declaration,
        *,
        verdict="no",
        round_value=CAP_CLOSURE_ROUND,
        date=CAP_CLOSURE_DATE,
        extensions=None,
    ):
        """Full version-1 sidecar adapted from ``vrs._version1_payload``."""
        payload = vrs._version1_payload()
        payload["review_type"] = "plan"
        payload["source_kind"] = "plan"
        payload["verdict"] = verdict
        payload["artifact_slug"] = CAP_CLOSURE_SLUG
        payload["round"] = round_value
        payload["date"] = date
        payload["source_digest"] = vrs.compute_source_digest(
            "plan", digest_source_bytes
        )
        payload["findings"] = findings
        payload["counts"]["staged_findings"] = len(findings)
        if extensions is not None:
            payload["extensions"] = extensions
        else:
            payload["extensions"] = {"cap_closure": declaration}
        return payload

    def _stage(
        self,
        plan_text,
        sidecar,
        markdown,
        *,
        date=CAP_CLOSURE_DATE,
        binary_plan_bytes=None,
    ):
        plan = self.plans / f"{date}-{CAP_CLOSURE_SLUG}.md"
        if binary_plan_bytes is not None:
            plan.write_bytes(binary_plan_bytes)
        else:
            plan.write_text(plan_text, encoding="utf-8")
        review = self.reviews / (
            f"{date}-plan-review-{CAP_CLOSURE_SLUG}-"
            f"{CAP_CLOSURE_ROUND_SUFFIX}.md"
        )
        review.write_text(markdown, encoding="utf-8")
        review.with_suffix(".stats.json").write_text(
            json.dumps(sidecar), encoding="utf-8"
        )
        return plan

    def _accept_fixture(
        self,
        *,
        verdict="no",
        patterns=(CAP_CLOSURE_PATTERN,),
        plan_text=None,
        declaration=None,
        date=CAP_CLOSURE_DATE,
    ):
        """The accept-arm fixture: one non-blocking triaged finding mirrored
        on both surfaces, a conforming declaration, and a residual section
        listing every staged pattern with an ``accepted`` disposition."""
        findings = [_cap_closure_finding()] if patterns else []
        if plan_text is None:
            plan_text = self._plan_text(patterns=patterns)
        if declaration is None:
            declaration = _cap_closure_declaration(residuals=len(patterns))
        sidecar = self._sidecar(
            plan_text.encode("utf-8"), findings, declaration,
            verdict=verdict, date=date,
        )
        return self._stage(
            plan_text, sidecar, self._markdown(findings), date=date
        )

    def _evaluate(self, plan):
        return plan_readiness.evaluate_readiness(plan, self.plans, self.reviews)

    # -- guards (pass today, must keep passing) ----------------------------

    def test_ordinary_rounds_unaffected_by_cap_closure_rule(self):
        """A normal ready=yes sidecar without any extensions object keeps
        today's outcome: the new rule does not over-block ordinary rounds."""
        plan, _review = plan_readiness._write_clean_state(
            self.plans, self.reviews
        )
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    def test_gate_rejects_verdict_no_without_cap_closure(self):
        """verdict "no" with only ``extensions.convergence`` fails with
        today's verdict reason, unchanged; the reason discriminates the
        key name (an any-extensions-key gate would wrongly pass)."""
        plan_text = self._plan_text()
        findings = [_cap_closure_finding()]
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            None,
            verdict="no",
            extensions={"convergence": {"rounds": 3}},
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("verdict field reports 'no'", reason)
        self.assertNotIn("cap closure", reason)

    def test_gate_rejects_stale_digest_under_cap_closure(self):
        """A sidecar whose ``source_digest`` still records the pre-fold
        bytes fails on the digest arm: the re-bind is load-bearing and the
        shared gate stays the single digest authority."""
        plan_text = self._plan_text()
        findings = [_cap_closure_finding()]
        stale_digest = _cap_closure_pre_fold_digest()
        declaration = _cap_closure_declaration(
            pre_fold_digest=vrs.compute_source_digest(
                "plan", CAP_CLOSURE_THIRD_BYTES
            )
        )
        sidecar = self._sidecar(
            CAP_CLOSURE_PRE_FOLD_BYTES, findings, declaration
        )
        self.assertEqual(stale_digest, sidecar["source_digest"])
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("is stale", reason)

    def test_gate_accepts_yes_verdict_sidecar_with_conforming_cap_closure(
        self,
    ):
        """The same fixture fully conforming under a yes verdict passes:
        the probe keys on declaration presence, not the verdict value."""
        plan = self._accept_fixture(verdict="yes")
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    # -- new gate arms (RED before the probe existed) -----------------------

    def test_gate_accepts_cap_closure_terminal_shape(self):
        """The generic shape passes without project-type facts: verdict "no"
        with a conforming declaration passes, and the sidecar
        round deliberately uses the paired-but-different type (sidecar the
        integer ``5``, declaration ``"5"``), proving string normalization
        is load-bearing."""
        self.assertEqual(
            {"plan_section", "round", "residuals", "pre_fold_digest"},
            set(_cap_closure_declaration()),
        )
        plan = self._accept_fixture()
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    def test_gate_rejects_cap_closure_without_plan_section(self):
        """Removing the section literal from the plan bytes fails naming
        the missing terminal state, never the verdict reason."""
        plan = self._accept_fixture(
            plan_text=self._plan_text(omit_section=True)
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("terminal state missing", reason)
        self.assertIn(CAP_CLOSURE_SECTION, reason)
        self.assertNotIn("verdict field reports", reason)

    def test_gate_rejects_cap_closure_heading_with_empty_body(self):
        """Heading present with an empty body under ``residuals: 1`` fails
        naming the missing-or-empty terminal state and the declared
        residual count; a ``###`` sub-heading body would count as body
        text, but there is none here."""
        plan = self._accept_fixture(plan_text=self._plan_text(body=""))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("missing or empty", reason)
        self.assertIn(CAP_CLOSURE_SECTION, reason)
        self.assertIn("claims 1 residual", reason)

    def test_gate_rejects_first_conforming_heading_governs(self):
        """An empty first section is never rescued by a non-empty body
        under a later identical conforming heading."""
        plan = self._accept_fixture(
            plan_text=self._plan_text(
                first_empty_second_body=(
                    f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)"
                )
            ),
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("missing or empty", reason)
        self.assertIn("claims 1 residual", reason)

    def test_gate_rejects_cap_closure_under_reporting_staged_findings(self):
        """A body that does not list the staged patterns with dispositions
        fails with the dedicated under-reporting reason (``residuals: 0``
        with an empty body passes only when the round staged zero
        findings)."""
        plan = self._accept_fixture(
            plan_text=self._plan_text(body="No residual findings remain.")
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("under-reports", reason)
        self.assertIn(CAP_CLOSURE_PATTERN, reason)

    def test_gate_rejects_pattern_listed_without_disposition(self):
        """Listing every staged pattern but leaving one list entry without
        ``folded`` or ``accepted`` still under-reports: the disposition
        check is per pattern (same list entry as its pattern)."""
        plan_text = self._plan_text(
            body=(
                f"- {CAP_CLOSURE_PATTERN}\n"
                "Resolved outside the section."
            )
        )
        plan = self._accept_fixture(plan_text=plan_text)
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("under-reports", reason)
        self.assertIn(CAP_CLOSURE_PATTERN, reason)

    def test_gate_rejects_cap_closure_disposition_outside_accepted_vocabulary(
        self,
    ):
        """A ``disposition: deferred`` marker and a bare pattern both
        under-report: the pinned disposition enum is ``folded``/
        ``accepted``, and words outside it are rejected while parsing."""
        plan_text = self._plan_text(
            body=(
                f"- {CAP_CLOSURE_PATTERN} (disposition: deferred)\n"
                f"- {CAP_CLOSURE_BLOCK_PATTERN}"
            )
        )
        findings = [
            _cap_closure_finding(pattern=CAP_CLOSURE_PATTERN),
            _cap_closure_finding(
                id=2, pattern=CAP_CLOSURE_BLOCK_PATTERN
            ),
        ]
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            _cap_closure_declaration(residuals=0),
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("under-reports", reason)
        self.assertIn(CAP_CLOSURE_PATTERN, reason)

    def test_gate_rejects_residuals_count_mismatch(self):
        """The declared ``residuals`` count is tied to the accepted-entry
        tally the gate parses: 0 with one ``accepted`` entry fails, and 2
        with three ``accepted`` entries fails."""
        zero_plan = self._accept_fixture(
            declaration=_cap_closure_declaration(residuals=0)
        )
        ok, reason = self._evaluate(zero_plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("residuals count mismatch", reason)
        self.assertIn("claims 0 accepted", reason)
        self.assertIn("carries 1", reason)
        three_body = "\n".join(
            [
                f"- {CAP_CLOSURE_PATTERN} (disposition: accepted)",
                "- quality#extra-one (disposition: accepted)",
                "- quality#extra-two (disposition: accepted)",
            ]
        )
        two_plan = self._accept_fixture(
            plan_text=self._plan_text(body=three_body),
            declaration=_cap_closure_declaration(residuals=2),
        )
        ok, reason = self._evaluate(two_plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("residuals count mismatch", reason)
        self.assertIn("claims 2 accepted", reason)
        self.assertIn("carries 3", reason)

    def test_gate_accepts_cap_closure_with_zero_residuals_and_empty_body(
        self,
    ):
        """A genuinely finding-free round with ``residuals: 0`` and an
        empty section body passes."""
        plan = self._accept_fixture(
            patterns=(),
            plan_text=self._plan_text(patterns=(), body=""),
            declaration=_cap_closure_declaration(residuals=0),
        )
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)

    def test_gate_rejects_cap_closure_only_as_quoted_or_misleveled_mention(
        self,
    ):
        """A fenced copy and a ``###`` heading never satisfy the conjunct:
        the gate still fails naming the missing terminal state."""
        plan = self._accept_fixture(
            plan_text=self._quote_only_plan_text()
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("terminal state missing", reason)
        self.assertIn(CAP_CLOSURE_SECTION, reason)

    def test_gate_rejects_cap_closure_with_unresolved_blocking(self):
        """One blocking finding left unresolved (mirrored on both record
        surfaces with the version-1 finding shape) fails on the blocking
        consistency arm, unchanged."""
        findings = [
            _cap_closure_finding(
                blocking=True,
                severity="High",
                triage="pending",
                pattern=CAP_CLOSURE_BLOCK_PATTERN,
            )
        ]
        plan_text = self._plan_text(patterns=(CAP_CLOSURE_BLOCK_PATTERN,))
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            _cap_closure_declaration(),
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("unresolved blocking findings", reason)

    def test_gate_rejects_cap_closure_with_pending_triage(self):
        """Flipping one blocking finding's triage back to ``pending`` on
        both record surfaces fails at the ``is_review_ready`` reason: the
        composite requires the folded findings' triage resolved on both
        surfaces, not just in the residual section."""
        findings = [
            _cap_closure_finding(blocking=True, severity="High",
                                 triage="pending")
        ]
        plan_text = self._plan_text()
        sidecar = self._sidecar(
            plan_text.encode("utf-8"),
            findings,
            _cap_closure_declaration(),
        )
        plan = self._stage(plan_text, sidecar, self._markdown(findings))
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("unresolved blocking findings", reason)

    def test_gate_rejects_malformed_cap_closure_declaration(self):
        """Non-conforming declarations fail with the step-3 mapped reason;
        each full mapped reason names ``extensions.cap_closure`` and lands
        in the malformed-sidecar family, never the stale-digest family."""
        differ_declaration = _cap_closure_declaration(pre_fold_digest=None)
        plan_text = self._plan_text()
        differ_declaration["pre_fold_digest"] = vrs.compute_source_digest(
            "plan", plan_text.encode("utf-8")
        )
        cases = (
            (
                "wrong plan_section literal",
                _cap_closure_declaration(plan_section="## Wrong section"),
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure 'plan_section' must be exactly "
                    "'## Residual findings (cap closure)'; "
                    "got '## Wrong section'"
                ),
            ),
            (
                "round mismatching the sidecar",
                _cap_closure_declaration(round="6"),
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure 'round' must equal the sidecar "
                    "round after string normalization (sidecar round 5 vs "
                    "declaration round '6')"
                ),
            ),
            (
                "unknown extension key",
                _cap_closure_declaration(scheme="extra"),
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure accepts only the keys "
                    "plan_section, round, residuals, pre_fold_digest"
                ),
            ),
            (
                "pre_fold_digest equal to the bound digest",
                differ_declaration,
                _MALFORMED_SIDECAR_PREFIX
                + (
                    "extensions.cap_closure 'pre_fold_digest' must differ "
                    "from the digest bound to the reviewed bytes: it "
                    "records the pre-fold state, not the folded state"
                ),
            ),
        )
        for name, declaration, expected in cases:
            with self.subTest(case=name):
                findings = [_cap_closure_finding()]
                sidecar = self._sidecar(
                    plan_text.encode("utf-8"), findings, declaration
                )
                plan = self._stage(
                    plan_text, sidecar, self._markdown(findings)
                )
                ok, reason = self._evaluate(plan)
                self.assertFalse(ok, reason is None and "unexpected pass")
                self.assertEqual(expected, reason)

    def test_gate_rejects_yes_verdict_sidecar_with_violating_cap_closure(
        self,
    ):
        """A yes-verdict sidecar whose residual section body is emptied
        under a nonzero ``residuals`` fails with the dedicated
        terminal-state reason, never a pass via the yes verdict."""
        plan = self._accept_fixture(
            verdict="yes",
            plan_text=self._plan_text(body=""),
            declaration=_cap_closure_declaration(residuals=2),
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("missing or empty", reason)
        self.assertIn("claims 2 residual", reason)

    def test_gate_accepts_cap_closure_on_modern_plan_with_structural_gates(
        self,
    ):
        """On/after ``DECISION_MARKER_MIN_DATE`` the trailer gate runs
        after a satisfied cap-closure conjunct: the conforming fixture
        passes, and removing the trailer line yields the trailer reason
        (fall-through, not early return)."""
        plan_text = self._plan_text(trailer=True)
        plan = self._accept_fixture(
            plan_text=plan_text, date=CAP_CLOSURE_MODERN_DATE
        )
        ok, reason = self._evaluate(plan)
        self.assertTrue(ok, reason)
        twin_text = plan_text.replace(
            "Decision points requiring a grill: none remain.\n", ""
        )
        twin = self._accept_fixture(
            plan_text=twin_text, date=CAP_CLOSURE_MODERN_DATE
        )
        ok, reason = self._evaluate(twin)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("decision-points trailer", reason)

    def test_gate_names_undecodable_plan_bytes_under_cap_closure(self):
        """Undecodable plan bytes with a matching sidecar return the named
        cannot-read-plan-bytes reason instead of raising: the
        declaration-gated decode keeps today's failure shape for
        declaration-free rounds, and the undecodable-bytes reason fires
        only when the declaration routes the probe at the bytes."""
        plan_bytes = b"\xff\xfe\x00 undecodable cap closure plan"
        findings = [_cap_closure_finding()]
        sidecar = self._sidecar(
            plan_bytes, findings, _cap_closure_declaration()
        )
        plan = self._stage(
            None,
            sidecar,
            self._markdown(findings),
            binary_plan_bytes=plan_bytes,
        )
        ok, reason = self._evaluate(plan)
        self.assertFalse(ok, reason is None and "unexpected pass")
        self.assertIn("cannot read plan bytes", reason)


# --------------------------------------------------------------------------- #
# Outcome-contract fixtures (outcome-contract migration batch 2, Task 2):
# the four-outcome exit vocabulary and the final `OUTCOME:` line on stdout
# for every non-metadata run; `--help` stays metadata-exempt.
# --------------------------------------------------------------------------- #


def _outcome_rows(text: str) -> list:
    return [ln for ln in text.splitlines() if ln.startswith("OUTCOME:")]


class OutcomeContractTest(unittest.TestCase):
    """The migrated CLI vocabulary: readiness verdicts keep 0 pass and 1
    fail with a final stdout `OUTCOME:` line; usage and mutual-exclusion
    violations exit 3 (the argparse override) with `OUTCOME: tool_error` on
    stderr; a sibling-compatibility mismatch is tool error (exit 3), never
    a readiness fail; `--sweep` keeps its modeled verdicts and gains the
    same final-line and usage rules."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="outcome-contract-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / ".ai-playbook").mkdir()
        (self.root / ".ai-playbook" / "facts.md").write_text(
            FACTS_BODY, encoding="utf-8"
        )
        (self.root / "plans").mkdir()
        (self.root / "reviews").mkdir()

    def _run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    rc = plan_readiness.main(argv)
                except SystemExit as exc:
                    rc = exc.code
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def _write_state(self, **kwargs):
        return plan_readiness._write_clean_state(
            self.root / "plans", self.root / "reviews", **kwargs
        )

    def test_ready_plan_emits_outcome_pass(self):
        plan, _ = self._write_state()
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: pass"])
        self.assertTrue(out.rstrip().endswith("OUTCOME: pass"), out)
        self.assertIn("readiness OK", out)

    def test_failed_condition_emits_outcome_fail(self):
        plan, _ = self._write_state(verdict="no")
        rc, out, err = self._run_main([str(plan)])
        self.assertEqual(rc, 1, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: fail"])
        self.assertTrue(out.rstrip().endswith("OUTCOME: fail"), out)
        # The named first-failed condition stays on stderr.
        self.assertIn("readiness FAILED:", err)
        self.assertIn("does not report a ready=yes verdict line", err)

    def test_usage_violation_exits_3_tool_error(self):
        # A missing plan operand is a parse-time usage violation: argparse's
        # exit 2 is overridden to tool error (exit 3), the OUTCOME line
        # riding the stderr usage text.
        rc, out, err = self._run_main([])
        self.assertEqual(rc, 3, (out, err))
        self.assertEqual(_outcome_rows(out), [])
        self.assertIn("OUTCOME: tool_error", err)
        # A forbidden mode combination (--pre-round with --selftest) is the
        # same parse-time tool error.
        rc, out, err = self._run_main(
            ["--pre-round", "plans/2026-09-01-x.md", "--selftest"]
        )
        self.assertEqual(rc, 3, (out, err))
        self.assertEqual(_outcome_rows(out), [])
        self.assertIn("OUTCOME: tool_error", err)
        self.assertIn("--pre-round must not be combined with --selftest", err)

    def test_help_stays_metadata_exempt(self):
        rc, out, err = self._run_main(["--help"])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(_outcome_rows(out), [])
        self.assertEqual(_outcome_rows(err), [])

    def test_sibling_compat_failure_is_tool_error(self):
        # The compat seam monkeypatches the sibling compatibility constant
        # the way plan_readiness.py's own selftest fixtures do (set
        # vrs.COMPAT_VERSION, restore in finally).
        plan, _ = self._write_state()
        saved = vrs.COMPAT_VERSION
        vrs.COMPAT_VERSION = 999
        try:
            rc, out, err = self._run_main([str(plan)])
        finally:
            vrs.COMPAT_VERSION = saved
        self.assertEqual(rc, 3, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: tool_error"])
        self.assertTrue(out.rstrip().endswith("OUTCOME: tool_error"), out)
        self.assertIn("compatibility FAILED", err)
        self.assertIn("999", err)

    def test_sweep_keeps_modeled_verdicts_and_gains_the_line(self):
        plan, review = self._write_state()
        rc, out, err = self._run_main(["--sweep"])
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: pass"])
        self.assertTrue(out.rstrip().endswith("OUTCOME: pass"), out)
        # The drift verdict keeps its modeled fail: a Summary whose ready=
        # mention yields no verdict token is an anomaly at exit 1, and the
        # OUTCOME line stays the final stdout row.
        review.write_text(
            "# Plan Review\n\n## Summary\n\n- ready=\nyes\n",
            encoding="utf-8",
        )
        rc, out, err = self._run_main(["--sweep"])
        self.assertEqual(rc, 1, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: fail"])
        self.assertTrue(out.rstrip().endswith("OUTCOME: fail"), out)
        self.assertIn("sweep FAILED", out)


# --------------------------------------------------------------------------- #
# Graded readiness fixtures (review-cert-graded-binding plan, Task 6): the
# full readiness gate over hermetic scratch git repos whose committed plan
# history and certification seal the shared verifier re-derives from git.
# --------------------------------------------------------------------------- #

import collections
import subprocess
import sys

import corrections_record as cr

_GRADED_DATE = "2026-09-22"
_GRADED_SLUG = "acme-plan"
_GRADED_PLAN_NAME = "2026-09-22-acme-plan.md"
_GRADED_PLAN_REL = "docs/history/plans/" + _GRADED_PLAN_NAME
# The em dash is built from an escape at run time: these fixture bytes never
# carry the character itself. D2 is the typography-only comma form of D1;
# D3 is the smuggled shape, a plain Assumptions word change no exempt class
# can prove.
_GRADED_PLAN_HEAD = (
    "# P\n\n"
    "## Assumptions\n\n"
    "Decision points requiring a grill: none remain.\n\n"
)
_GRADED_PLAN_TAIL = (
    "\n## Tasks\n\n"
    "### Task 1: Do the thing\n\n"
    "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
)
_GRADED_D1 = (
    _GRADED_PLAN_HEAD + "alpha \u2014 bravo." + _GRADED_PLAN_TAIL
).encode("utf-8")
_GRADED_D2 = (
    _GRADED_PLAN_HEAD + "alpha, bravo." + _GRADED_PLAN_TAIL
).encode("utf-8")
_GRADED_D3 = (
    _GRADED_PLAN_HEAD + "alpha omega." + _GRADED_PLAN_TAIL
).encode("utf-8")
_GRADED_FACTS_BODY = (
    "# facts\n\n```toml\n"
    'plans_dir = "docs/history/plans"\n'
    'reviews_dir = ".ai-playbook/reviews"\n'
    "```\n"
)

GradedFixture = collections.namedtuple(
    "GradedFixture", "repo plans_dir reviews_dir start close hop"
)


def _graded_payload(digest: str, *, last_fix: str | None = None) -> dict:
    """A current-v1 clear-review sidecar carrying the graded fields (the
    Task 5 fixture shape): the declared source kind and digest, the round,
    and the artifact slug the certification seal resolves by."""
    payload = vrs._post_window_fixture_payload("plan")
    payload["schema_version"] = 1
    payload["review_type"] = "Branch Review"
    payload["artifact_slug"] = _GRADED_SLUG
    payload["round"] = "r1"
    payload["source_kind"] = "plan"
    payload["source_digest"] = digest
    payload["verdict"] = "yes"
    payload["deduplication_groups"] = []
    payload["discarded"] = []
    payload["severity_calibration"] = []
    payload["triage_outcomes"] = []
    payload["soften_watchlist"] = []
    if last_fix is not None:
        payload["last_fix_commit"] = last_fix
    return payload


def _graded_markdown(last_fix: str | None = None) -> str:
    """The Markdown twin of ``_graded_payload`` (the Task 5 fixture shape),
    with the ``Last fix commit`` Metadata line re-pointed when the fixture
    declares one, so the cross-surface agreement gate sees one surface."""
    markdown = vrs._post_window_fixture_markdown("plan")
    if last_fix is not None:
        markdown = markdown.replace(
            "- Last fix commit: none",
            "- Last fix commit: %s" % last_fix,
            1,
        )
    return markdown


class PlanReadinessGradedTest(unittest.TestCase):
    """The five graded full-gate fixtures over scratch repos: the
    typography re-bind passes, the honest clean shape passes with no
    record, the same edit without the record keeps the stale reason, a row
    claiming exempt over a word change takes the corrections classification
    family, a bare digest rewrite refuses as an unwitnessed mutation, a
    vacuous hop refuses naming its leg, and a moved seal anchor passes
    undetected since the history-witness retirement; the
    routing-order pin holds the caller dispatch, and the graded
    indeterminate class maps to exit 2."""

    def _graded_fixture(
        self,
        *,
        hop_bytes: bytes | None = _GRADED_D2,
        with_seal: bool = True,
        seal_after_hop: bool = False,
    ) -> GradedFixture:
        """The shared fixture recipe: a scratch git repo (hermetic builder,
        TemporaryDirectory with addCleanup teardown) holding the D1 plan
        bytes committed with explicit author and committer dates, the
        round-close commit, the on-disk seal entry for the fixture round
        (round-start commit and digest) so the anchor locator resolves, and
        the committed hop to the current bytes. ``seal_after_hop`` mints
        the seal entry after the hop: the moved-anchor shape (undetected
        since the history-witness retirement)."""
        repo = cr.build_scratch_repo(self)
        plans_dir = repo.root / "docs" / "history" / "plans"
        reviews_dir = repo.root / ".ai-playbook" / "reviews"
        plans_dir.mkdir(parents=True)
        reviews_dir.mkdir(parents=True)
        (repo.root / ".ai-playbook").mkdir(exist_ok=True)
        (repo.root / ".ai-playbook" / "facts.md").write_text(
            _GRADED_FACTS_BODY, encoding="utf-8"
        )
        start = repo.commit_file(_GRADED_PLAN_REL, _GRADED_D1, "seed plan")
        close = repo.commit_allow_empty("round 1 close")
        hop = None
        if with_seal and not seal_after_hop:
            # Fixture shape: the seal entry is committed in the fixture at
            # round close, before any correction hop it anchors (production
            # writes the seal as an untracked run artifact).
            repo.append_seal_entry(
                _GRADED_SLUG, 1, _GRADED_PLAN_REL, start,
                cr.sha256_hex(_GRADED_D1), close,
            )
        if hop_bytes is not None:
            hop = repo.commit_file(
                _GRADED_PLAN_REL, hop_bytes, "apply the correction"
            )
        if with_seal and seal_after_hop:
            # The moved anchor: the seal entry is minted after the hop it
            # claims to anchor (the tamper shape; the gate no longer dates
            # the entry's introduction, so nothing refuses it).
            self.assertIsNotNone(hop)
            repo.append_seal_entry(
                _GRADED_SLUG, 1, _GRADED_PLAN_REL, start,
                cr.sha256_hex(_GRADED_D1), close,
            )
        return GradedFixture(
            repo=repo,
            plans_dir=plans_dir,
            reviews_dir=reviews_dir,
            start=start,
            close=close,
            hop=hop,
        )

    def _write_round(self, fx: GradedFixture, payload: dict, markdown: str):
        review = fx.reviews_dir / (
            "%s-plan-review-%s-r1.md" % (_GRADED_DATE, _GRADED_SLUG)
        )
        if "- URL or Artifact:" not in markdown:
            markdown = markdown.replace(
                "## Metadata\n",
                "## Metadata\n- URL or Artifact: %s\n" % _GRADED_PLAN_REL,
                1,
            )
        review.write_text(markdown, encoding="utf-8")
        review.with_suffix(".stats.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        return review

    def _mint_row(self, fx: GradedFixture) -> dict:
        """The CLI-produced correction row anchored at D1 (the classifier
        CLI is the only row producer), minted through the real
        ``--emit-row`` subprocess inside the fixture repo."""
        script = (
            Path(plan_readiness.__file__).resolve().parent
            / "plan_delta_classifier.py"
        )
        proc = subprocess.run(
            [
                sys.executable, str(script),
                "--plan", str(fx.repo.root / _GRADED_PLAN_REL),
                "--since", fx.start,
                "--emit-row",
            ],
            capture_output=True,
            text=True,
            env=cr.hermetic_git_env(),
        )
        self.assertEqual(proc.returncode, 0, (proc.stdout, proc.stderr))
        rows = [
            line.split(": ", 1)[1]
            for line in proc.stdout.splitlines()
            if line.startswith("corrections-row-json: ")
        ]
        self.assertEqual(len(rows), 1, proc.stdout)
        return json.loads(rows[0])

    def _run_gate(self, fx: GradedFixture):
        """The full readiness gate pointed at the fixture through its
        resolved repository root (the facts block resolves against the
        scratch repo the process cwd lands in)."""
        out, err = io.StringIO(), io.StringIO()
        prev = os.getcwd()
        os.chdir(fx.repo.root)
        try:
            with contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                rc = plan_readiness.main(
                    [str(fx.plans_dir / _GRADED_PLAN_NAME)]
                )
        finally:
            os.chdir(prev)
        return rc, out.getvalue(), err.getvalue()

    def test_typography_record_passes(self):
        fx = self._graded_fixture()
        row = self._mint_row(fx)
        self._write_round(
            fx,
            _graded_payload(cr.sha256_hex(_GRADED_D1))
            | {"extensions": {"corrections": [row]}},
            _graded_markdown(),
        )
        rc, out, err = self._run_gate(fx)
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: pass"])

    def test_clean_pass_with_seal(self):
        # The honest clean shape: the declared digest equals both the
        # current bytes and the seal's round-start digest, with no record.
        fx = self._graded_fixture(hop_bytes=None)
        self._write_round(
            fx,
            _graded_payload(cr.sha256_hex(_GRADED_D1)),
            _graded_markdown(),
        )
        rc, out, err = self._run_gate(fx)
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: pass"])

    def test_same_edit_without_record_fails(self):
        # The identical typography edit with the record stripped keeps
        # today's stale reason family.
        fx = self._graded_fixture()
        self._write_round(
            fx,
            _graded_payload(cr.sha256_hex(_GRADED_D1)),
            _graded_markdown(),
        )
        rc, out, err = self._run_gate(fx)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("sidecar source_digest is stale", err)
        self.assertNotIn(cr.MARKER_PREFIX, err)

    def test_smuggled_edit_fails(self):
        # A row claiming exempt over an Assumptions word change: every
        # digest leg binds (the row was composed over the true hop bytes),
        # and the classification leg refuses it.
        fx = self._graded_fixture(hop_bytes=_GRADED_D3)
        row = {
            "kind": cr.KIND_SCRIPT_VERIFIED,
            "before_digest": cr.sha256_hex(_GRADED_D1),
            "after_digest": cr.sha256_hex(_GRADED_D3),
            "evidence_commit": fx.hop,
            "hunks": [{"header": "@@ -7 +7 @@",
                       "digest": cr.sha256_hex(b"hunk-bytes")}],
            "recorded_at": "2026-10-04T00:00:00Z",
            "recorded_by": "plan_delta_classifier",
        }
        self._write_round(
            fx,
            _graded_payload(cr.sha256_hex(_GRADED_D3))
            | {"extensions": {"corrections": [row]}},
            _graded_markdown(),
        )
        rc, out, err = self._run_gate(fx)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(cr.MARKER_PREFIX, err)
        self.assertIn("classification", err)
        self.assertIn("not exempt", err)

    def test_bare_rewrite_refuses(self):
        # The declared digest equals the current bytes while the
        # round-anchored locator resolves a different digest: an
        # unwitnessed sidecar digest mutation.
        fx = self._graded_fixture()
        self._write_round(
            fx,
            _graded_payload(cr.sha256_hex(_GRADED_D2)),
            _graded_markdown(),
        )
        rc, out, err = self._run_gate(fx)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(cr.MARKER_PREFIX, err)
        self.assertIn("bare rewrite", err)

    def test_moved_anchor_and_vacuous_hop_refuse(self):
        # Witness-retirement fence (2026-10-11 seal-home re-point): the
        # seal is read from the working tree and the committed-history
        # witness (the introductions walk and its dating legs) is retired,
        # so the moved-anchor tamper below is undetectable by design; this
        # arm asserts the post-retirement pass instead of the former
        # seal-leg refusal. The row is still composed with the true hop
        # digests (the classifier CLI cannot mint here: its evidence
        # resolution reads HEAD, which the postdated seal commit now is),
        # so a pass proves every surviving digest leg binds.
        fx = self._graded_fixture(seal_after_hop=True)
        row = {
            "kind": cr.KIND_SCRIPT_VERIFIED,
            "before_digest": cr.sha256_hex(_GRADED_D1),
            "after_digest": cr.sha256_hex(_GRADED_D2),
            "evidence_commit": fx.hop,
            "hunks": [{"header": "@@ -7 +7 @@",
                       "digest": cr.sha256_hex(b"hunk-bytes")}],
            "recorded_at": "2026-10-04T00:00:00Z",
            "recorded_by": "plan_delta_classifier",
        }
        self._write_round(
            fx,
            _graded_payload(cr.sha256_hex(_GRADED_D1), last_fix=fx.hop)
            | {"extensions": {"corrections": [row]}},
            _graded_markdown(last_fix=fx.hop),
        )
        rc, out, err = self._run_gate(fx)
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(_outcome_rows(out), ["OUTCOME: pass"])
        self.assertNotIn(cr.MARKER_PREFIX, err)
        # Vacuous hop: a record whose before and after digests are equal
        # names the vacuous rule.
        fx2 = self._graded_fixture()
        row2 = dict(self._mint_row(fx2),
                    before_digest=cr.sha256_hex(_GRADED_D2))
        self._write_round(
            fx2,
            _graded_payload(cr.sha256_hex(_GRADED_D2))
            | {"extensions": {"corrections": [row2]}},
            _graded_markdown(),
        )
        rc, out, err = self._run_gate(fx2)
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(cr.MARKER_PREFIX, err)
        self.assertIn("vacuous", err)

    def test_graded_indeterminate_names_where_and_exits_2(self):
        # A declared record whose round has no resolvable seal entry is the
        # graded arm's indeterminate class: the gate refuses (never
        # passes), and the CLI maps it to exit 2 naming where.
        fx = self._graded_fixture(with_seal=False)
        row = self._mint_row(fx)
        self._write_round(
            fx,
            _graded_payload(cr.sha256_hex(_GRADED_D1))
            | {"extensions": {"corrections": [row]}},
            _graded_markdown(),
        )
        rc, out, err = self._run_gate(fx)
        self.assertEqual(rc, 2, (out, err))
        self.assertTrue(out.rstrip().endswith("OUTCOME: indeterminate"), out)
        self.assertIn(cr.MARKER_PREFIX, err)
        self.assertIn("no resolvable entry", err)

    def test_marker_check_outranks_the_substring_branches(self):
        # Routing home: the corrections marker check is the FIRST test in
        # the caller-level dispatch, before the coverage, source_kind, and
        # source_digest substring branches. The fixture reason deliberately
        # carries the banned routing literal "source_digest": production
        # verifier reasons never carry it (pinned in corrections_record's
        # MarkerConstantsTest); this one test-only string exists to prove
        # the marker check outranks the source_digest substring branch.
        synthetic = cr.MARKER_PREFIX + (
            "anchor leg refused: bare rewrite of source_digest"
        )
        reason = plan_readiness._first_gate_error_reason(
            synthetic, {"source_kind": "plan"}, 3
        )
        self.assertEqual(reason, synthetic)
        # The pre-existing digest families keep their routing on
        # marker-free errors (the stale family unchanged).
        stale = plan_readiness._first_gate_error_reason(
            "current sidecar source_digest is stale (mismatch vs "
            "expected_digest)",
            {"source_kind": "plan"},
            3,
        )
        self.assertIn("sidecar source_digest is stale", stale)
        self.assertIn("r3", stale)
        self.assertNotIn(cr.MARKER_PREFIX, stale)


# --------------------------------------------------------------------------- #
# --print-artifact-slug: the read-only slug SOT flag (CLI level).
# --------------------------------------------------------------------------- #

class TestPrintArtifactSlug(unittest.TestCase):
    """The read-only slug print answers the canonical artifact slug."""

    def test_flag_prints_canonical_slug(self):
        root = Path(tempfile.mkdtemp(prefix="slug-flag-fixture-"))
        self.addCleanup(shutil.rmtree, root, True)
        plan = root / "2026-09-01-DEMO-609-Fixture-Story.md"
        plan.write_text("# Fixture story\n", encoding="utf-8")
        script = Path(__file__).resolve().parent / "plan_readiness.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--print-artifact-slug", str(plan)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.splitlines()[0], "demo-609-fixture-story")
        self.assertTrue(
            proc.stdout.rstrip().endswith("OUTCOME: pass"), proc.stdout
        )


# --------------------------------------------------------------------------- #
# Directory-form plan operands (plan-directory-shape plan, Task 1): the
# readiness gate and the pre-round path accept a charter-plus-tasks
# directory beside the single-file shape (sections from the charter, tasks
# from the sorted task files, slug from the directory name, per-file fence
# scanning, manifest digest, directory ordinal grammar), while single-file
# behavior stays byte-identical.
# --------------------------------------------------------------------------- #

import contextlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import plan_readiness
import validate_review_staging as vrs

_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
_LANDED_COMPLETED_PLAN = _REPOSITORY_ROOT / (
    "docs/history/plans/completed/"
    "2026-10-05-plan-sizing-execution-budget.md"
)
# Fires all three date-gated probes (trailer 2026-09-08, Review Scope
# 2026-09-09, plan structure 2026-09-19) while matching the in-file
# selftest's gated-arm sidecar shape (plain _clear_sidecar at 2026-09-19).
_GATED_SIDECAR_DATE = "2026-09-19"

_DIRECTORY_CHARTER = (
    "# Plan: directory fixture\n"
    "\n"
    "Backlog origin: none\n"
    "Driving force: efficiency\n"
    "\n"
    "## Terms\n"
    "\n"
    "none.\n"
    "\n"
    "## Why\n"
    "\n"
    "The fixture proves the directory shape passes readiness end to end.\n"
    "\n"
    "## Gist & Examples\n"
    "\n"
    "TLDR: charter sections plus task files pass the gate, efficiency.\n"
    "\n"
    "## Outcome\n"
    "\n"
    "The readiness gate reads the shared sections from the charter and the"
    " tasks from the files.\n"
    "\n"
    "## Assumptions\n"
    "\n"
    "- assume the charter carries the shared sections; basis: the fixture"
    " contract.\n"
    "\n"
    "Decision points requiring a grill: none remain.\n"
    "\n"
    "## Evaluation Criteria\n"
    "\n"
    "**Done when:**\n"
    "- the readiness gate passes this fixture.\n"
    "\n"
    "## Review Scope\n"
    "\n"
    "**Production code:**\n"
    "- `scripts/fixture_module.py` *(new)*\n"
    "\n"
    "**Tests:**\n"
    "- `scripts/test_fixture_module.py` *(new)*\n"
    "\n"
    "## Validation Commands\n"
    "\n"
    "- python3 -m pytest scripts/test_fixture_module.py -q\n"
)

_DIRECTORY_TASKS = {
    "01-module.md": (
        "### Task 1: the module (TDD)\n"
        "\n"
        "Files:\n"
        "- `scripts/fixture_module.py` *(new)*\n"
        "\n"
        "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
    ),
    "02-tests.md": (
        "### Task 2: the tests (TDD)\n"
        "\n"
        "Files:\n"
        "- `scripts/test_fixture_module.py` *(new)*\n"
        "\n"
        "- [ ] Pin the module contract. [class: REPOSITORY_TEST]\n"
    ),
}


def _directory_plan_fixture(
    plans_dir: Path,
    slug: str = "2026-09-19-dirfixture",
    charter_text: str | None = None,
    task_texts: dict[str, str] | None = None,
) -> Path:
    """Write a directory-form plan under plans_dir and return its path."""
    plan_dir = plans_dir / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        charter_text if charter_text is not None else _DIRECTORY_CHARTER,
        encoding="utf-8",
    )
    texts = task_texts if task_texts is not None else _DIRECTORY_TASKS
    for name, text in texts.items():
        (plan_dir / "tasks" / name).write_text(text, encoding="utf-8")
    return plan_dir


def _write_directory_clean_state(
    plans_dir: Path,
    reviews_dir: Path,
    slug: str = "2026-09-19-dirfixture",
    charter_text: str | None = None,
    task_texts: dict[str, str] | None = None,
    verdict: str = "yes",
    date: str = _GATED_SIDECAR_DATE,
) -> Path:
    """Directory plan plus a clear review round bound to its manifest digest."""
    import plan_shape  # in-function: the single-file suite collects before the resolver lands

    plan_dir = _directory_plan_fixture(
        plans_dir, slug=slug, charter_text=charter_text, task_texts=task_texts
    )
    shape = plan_shape.resolve_plan_operand(plan_dir)
    digest = vrs.compute_source_digest("plan", shape.digest_payload)
    sidecar = plan_readiness._clear_sidecar(digest)
    sidecar["date"] = date
    slug_name = plan_readiness.feature_slug(plan_dir)
    review = reviews_dir / f"{date}-plan-review-{slug_name}-r1.md"
    review.write_text(
        plan_readiness._review_markdown(verdict=verdict), encoding="utf-8"
    )
    review.with_suffix(".stats.json").write_text(
        json.dumps(sidecar), encoding="utf-8"
    )
    return plan_dir


class ReadinessDirectoryEndToEndTest(unittest.TestCase):
    """test_readiness_directory_end_to_end: the full gate passes a directory."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dirshape-e2e-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.plans_dir = self.root / "plans"
        self.reviews_dir = self.root / "reviews"
        self.plans_dir.mkdir()
        self.reviews_dir.mkdir()

    def test_full_gate_passes_well_formed_directory_plan(self):
        plan_dir = _write_directory_clean_state(
            self.plans_dir, self.reviews_dir
        )
        ok, reason = plan_readiness.evaluate_readiness(
            plan_dir, self.plans_dir, self.reviews_dir
        )
        self.assertTrue(ok, f"reason={reason}")
        self.assertIsNone(reason)

    def test_pre_round_passes_directory_plan_with_charter_sections(self):
        plan_dir = _directory_plan_fixture(self.plans_dir)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = plan_readiness.run_pre_round(plan_dir, self.plans_dir)
        self.assertEqual(rc, 0, err.getvalue())
        self.assertEqual(err.getvalue(), "")

    def test_charter_fence_imbalance_names_the_file(self):
        charter = _DIRECTORY_CHARTER + "```python\nunterminated = true\n"
        plan_dir = _directory_plan_fixture(
            self.plans_dir, charter_text=charter
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = plan_readiness.run_pre_round(plan_dir, self.plans_dir)
        self.assertEqual(rc, 1)
        self.assertIn("PLAN.md", err.getvalue())
        self.assertIn("unclosed fence opener", err.getvalue())


class ReadinessDirectoryOrdinalGrammarTest(unittest.TestCase):
    """test_readiness_directory_ordinal_grammar: the deliberate divergence."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dirshape-ordinal-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.plans_dir = self.root / "plans"
        self.reviews_dir = self.root / "reviews"
        self.plans_dir.mkdir()
        self.reviews_dir.mkdir()

    def test_task_file_missing_ordinal_refuses_naming_the_file(self):
        task_texts = {
            "01-module.md": _DIRECTORY_TASKS["01-module.md"],
            "02-tests.md": "no task heading in this file\n",
        }
        plan_dir = _directory_plan_fixture(
            self.plans_dir, task_texts=task_texts
        )
        ok, reason = plan_readiness.evaluate_readiness(
            plan_dir, self.plans_dir, self.reviews_dir
        )
        self.assertFalse(ok)
        self.assertIsNotNone(reason)
        self.assertIn("tasks/02-tests.md", reason)

    def test_duplicate_ordinal_refuses_naming_both_files(self):
        task_texts = {
            "01-module.md": _DIRECTORY_TASKS["01-module.md"],
            "02-tests.md": (
                "### Task 1: the tests (TDD)\n"
                "\n"
                "Files:\n"
                "- `scripts/test_fixture_module.py` *(new)*\n"
                "\n"
                "- [ ] Pin the module contract. [class: REPOSITORY_TEST]\n"
            ),
        }
        plan_dir = _directory_plan_fixture(
            self.plans_dir, task_texts=task_texts
        )
        ok, reason = plan_readiness.evaluate_readiness(
            plan_dir, self.plans_dir, self.reviews_dir
        )
        self.assertFalse(ok)
        self.assertIsNotNone(reason)
        self.assertIn("tasks/01-module.md", reason)
        self.assertIn("tasks/02-tests.md", reason)
        self.assertIn("Task 1", reason)

    def test_single_file_repeated_ordinals_still_accepted(self):
        plan_text = (
            "# Plan: repeated ordinals\n"
            "\n"
            "## Assumptions\n"
            "\n"
            "Decision points requiring a grill: none remain.\n"
            "\n"
            "## Review Scope\n"
            "\n"
            "**Production code:**\n"
            "- `scripts/fixture_module.py` *(new)*\n"
            "\n"
            "## Tasks\n"
            "\n"
            "### Task 1: the module (TDD)\n"
            "\n"
            "Files:\n"
            "- `scripts/fixture_module.py` *(new)*\n"
            "\n"
            "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
            "\n"
            "### Task 1: the module, revisited\n"
            "\n"
            "- [ ] Extend the module. [class: IMPLEMENTATION_REQUIRED]\n"
        )
        plan, _review = plan_readiness._write_clean_state(
            self.plans_dir, self.reviews_dir, plan_text=plan_text
        )
        ok, reason = plan_readiness.evaluate_readiness(
            plan, self.plans_dir, self.reviews_dir
        )
        self.assertTrue(ok, f"reason={reason}")
        self.assertIsNone(reason)


class ReadinessSingleFileUnchangedTest(unittest.TestCase):
    """Single-file gate surfaces over the landed completed plan byte-shape."""

    def test_landed_plan_pre_round_refuses_on_envelope(self):
        """The landed plan (over-cap acceptance criteria, 538 and 981 bytes) refuses
        --pre-round with step 9's byte-identical envelope label: the
        pre-round-gate-dimension-parity plan extends the pre-round mode
        with the plan-private step 9 probes, and the former exit-0
        byte-identical pin encoded the pre-extension surface (its own
        docstring records that history; the measured 7-of-16 corpus
        refusal rate in that plan's Gate delta prices this flip)."""
        script = Path(__file__).resolve().parent / "plan_readiness.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--pre-round", str(_LANDED_COMPLETED_PLAN)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(
            "readiness PRE-ROUND FAILED:", proc.stderr
        )
        self.assertIn(
            "evidence criterion exceeds UTF-8 item byte limit", proc.stderr
        )
        self.assertEqual(proc.stdout, "OUTCOME: fail\n")

    def test_file_operand_digest_matches_raw_bytes(self):
        import plan_shape

        raw = _LANDED_COMPLETED_PLAN.read_bytes()
        shape = plan_shape.resolve_plan_operand(_LANDED_COMPLETED_PLAN)
        self.assertEqual(
            vrs.compute_source_digest("plan", shape.digest_payload),
            vrs.compute_source_digest("plan", raw),
        )

    def test_full_gate_passes_single_file_plan(self):
        root = Path(tempfile.mkdtemp(prefix="dirshape-single-"))
        self.addCleanup(shutil.rmtree, root, True)
        plans_dir = root / "plans"
        reviews_dir = root / "reviews"
        plans_dir.mkdir()
        reviews_dir.mkdir()
        plan_text = (
            "# Plan: single file\n"
            "\n"
            "## Assumptions\n"
            "\n"
            "Decision points requiring a grill: none remain.\n"
            "\n"
            "## Review Scope\n"
            "\n"
            "**Production code:**\n"
            "- `scripts/fixture_module.py` *(new)*\n"
            "\n"
            "## Tasks\n"
            "\n"
            "### Task 1: the module (TDD)\n"
            "\n"
            "Files:\n"
            "- `scripts/fixture_module.py` *(new)*\n"
            "\n"
            "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
        )
        plan, _review = plan_readiness._write_clean_state(
            plans_dir, reviews_dir, plan_text=plan_text
        )
        ok, reason = plan_readiness.evaluate_readiness(
            plan, plans_dir, reviews_dir
        )
        self.assertTrue(ok, f"reason={reason}")
        self.assertIsNone(reason)


class ExecutePlanProfilePlacementCompatibilityTest(unittest.TestCase):
    """Pin the declared profile eligibility rule, the shared placement
    resolution matrix, and the profile-specific primary-placement branch
    arms (personal/pet base-branch only; company operator task-branch
    choice) plus the company maintenance guard."""

    def test_direct_execution_matrix_preserves_all_profile_placement_pairs(self):
        root = Path(__file__).resolve().parents[1]
        execute_plan = (root / "agents/skills/execute-plan/SKILL.md").read_text(encoding="utf-8")
        maintenance = (root / "agents/skills/maintenance/SKILL.md").read_text(encoding="utf-8")
        policy_start = execute_plan.index("**Project worktree policy (consulted at dispatch):**")
        policy_end = execute_plan.index("\n\n", policy_start)
        placement_policy = execute_plan[policy_start:policy_end]
        profile_start = execute_plan.index("**Profile and placement:**")
        profile_contract = execute_plan[profile_start:policy_start]

        self.assertIn("direct execute-plan invocation remains available under personal and company profiles", profile_contract)
        self.assertIn("Resolve placement independently under this paragraph", profile_contract)
        # Primary-placement branch requirements vary by profile: personal and
        # pet runs are valid only from the base branch, while a company run
        # gains the per-run operator choice and records its task branch.
        self.assertIn("for personal and pet profiles, a primary-placement run is valid only when the primary checkout's current branch is the base branch at run start", placement_policy)
        self.assertIn("a company-profile primary-placement run gains the per-run operator choice beside that base-branch-only rule", placement_policy)
        self.assertIn("the chosen or created task branch records into the execution claim and the manifest identity block", placement_policy)
        self.assertIn("a resume finding the shared checkout on any other branch stands down naming the recorded branch", placement_policy)

        maintenance_mode = next(
            line for line in maintenance.splitlines() if line.startswith("Mode binding.")
        )
        self.assertIn("survey-only", maintenance_mode)
        self.assertIn("class-guard-survey-only", maintenance_mode)

        # This declared cross-product is valid because profile eligibility is
        # separate from placement, and the placement resolutions below are the
        # shared matrix both profiles consult; only the primary-placement
        # branch requirement differs by profile (pinned above).
        cases = (
            ("personal", "worktrees", "`worktree_policy = \"worktrees\"` (enabling ad-hoc worktrees"),
            ("personal", "primary", '`worktree_policy = "primary"` runs all its work, ordinary and named lanes including plan authoring and plan execution, in the primary checkout on its current branch'),
            ("company", "worktrees", "`worktree_policy = \"worktrees\"` (enabling ad-hoc worktrees"),
            ("company", "primary", '`worktree_policy = "primary"` runs all its work, ordinary and named lanes including plan authoring and plan execution, in the primary checkout on its current branch'),
        )
        for profile, policy_name, policy_resolution in cases:
            with self.subTest(profile=profile, policy=policy_name):
                self.assertIn(profile, profile_contract)
                self.assertIn(policy_resolution, placement_policy)


class ReviewTrajectoryPolicyFixtureTest(unittest.TestCase):
    """Pin paired no-progress cases at and between configured checkpoints."""

    def test_no_progress_stop_requires_checkpoint_pause(self):
        fixture = Path(__file__).with_name("review_policy_sample_contexts.md").read_text(encoding="utf-8")
        self.assertIn("A cap is never a stop by itself", fixture)
        self.assertIn("Total-round checkpoints: r5, r10, r15", fixture)
        self.assertIn("Full-panel checkpoints: F5, F10, F15", fixture)
        self.assertIn("one reflection at each checkpoint", fixture)
        self.assertIn("r5", fixture)
        self.assertIn("pause for operator direction", fixture)
        self.assertIn("H1, pause at checkpoint", fixture)
        self.assertIn("H2, pause between checkpoints", fixture)
        self.assertIn("Cap closure is unavailable; pause only under the independent operator request", fixture)
        self.assertIn("| C, r15 | Full/F9; R=15, F=9 | Both intervals due; emit one reflection", fixture)
        self.assertIn("| I, r15 | Full/F15; R=15, F=15 | R15 and F15 coincide", fixture)
        self.assertIn("| I, complete 5/3 schedule | Full panel each round | Full-panel F3/F6/F9/F12/F15", fixture)
        self.assertIn("| I, r3 | Full/F3; R=3, F=3 | Full-panel first hit; total counter remains below 5", fixture)
        self.assertIn("| I, r5 | Full/F5; R=5, F=5 | Total first hit while F remains below 6", fixture)
        self.assertIn("total R5/R10/R15", fixture)
        self.assertIn("Coincidences at r5 and r15", fixture)
        self.assertIn("r10 is a total-round-only reflection", fixture)
        self.assertIn("reflect for F3 while R=3 is below 5", fixture)
        self.assertIn("reflect for R5 while F=5 is below 6", fixture)
        self.assertIn("Continue the next review without asking", fixture)
        self.assertIn("| J, fresh loop r1 | Positive blockers; no prior blocker count and no churn or recurrence trigger", fixture)
        self.assertIn("Continue one round, then apply the measured convergence rule", fixture)
        self.assertIn("Active churn overrides blocker decline", fixture)
        self.assertIn("falling blocker count", fixture)
        self.assertIn("| H1, r5 | No progress; independent operator pause coincides", fixture)
        self.assertIn("| H2, r4 | No progress; independent operator pause before any checkpoint", fixture)
        execute_plan = Path(__file__).resolve().parents[1] / "agents/skills/execute-plan/SKILL.md"
        policy = execute_plan.read_text(encoding="utf-8")
        self.assertIn("At every configured `max_review_rounds` or `max_full_panel_rounds` interval", policy)
        self.assertIn("record the reflection before deciding whether to continue", policy)
        self.assertIn("launches one host-native implementation worker at a time, in plan order", policy)
        self.assertIn("native delegation is unavailable before launch", policy)
        self.assertIn("a timed-out worker is verified terminal", policy)
        self.assertIn("If liveness is unknown, do not edit task paths or launch a duplicate", policy)
        self.assertIn("Review-panel workers may run in parallel", policy)

    def test_self_heal_trajectories_are_bounded_to_one_attempt(self):
        fixture = Path(__file__).with_name("review_policy_sample_contexts.md").read_text(encoding="utf-8")
        self.assertIn("find none, then pause", fixture)
        self.assertIn("same blockers remain, so pause", fixture)
        self.assertIn("| G, authorized attempt | New artifact chain starts at r1 with unused state bound to its `review-run-id` | Reserve consumed state with the stable `run_id` before mutation | Apply one attempt and carry the consumed state unchanged |", fixture)
        self.assertIn("| G, unauthorized attempt | Plan does not authorize; state is unused | The authorization gate prevents mutation | Pause before changing the branch |", fixture)
        self.assertIn("| G, resumed after attempt | Latest state is consumed for r3 with stable `run_id` and digest | Resume reads and preserves the consumed marker | Pause before a second attempt |", fixture)
        self.assertIn("| G, new invocation | A new artifact chain starts at r1 with a newly minted `review-run-id` | Orchestrator writes `unused` with matching `run_id` | New invocation receives its own one-attempt allowance |", fixture)
        self.assertIn("| G, legacy resume | Prior record or sidecar is missing or malformed | Record `unknown` with this round's `review-run-id`; validator rejects `unused` | Pause before self-heal |", fixture)
        self.assertIn("| Fold-defect plus wording must be strictly greater than half of staged findings | 2 of 4 is exactly half | 3 of 4 is greater than half | 2 of 4 does not trigger; 3 of 4 triggers reconciliation |", fixture)
        self.assertIn("| Staged finding totals are checked across the two most recent rounds | 4 to 3 decreases | 4 to 4 is flat; 4 to 5 increases | 4 to 3 does not trigger; 4 to 4 and 4 to 5 trigger reconciliation |", fixture)
        self.assertIn("| Positive blocker counts are checked across two consecutive rounds | 2 to 1 decreases | 2 to 2 stays positive and flat | 2 to 1 does not trigger; 2 to 2 triggers reconciliation |", fixture)
        root = Path(__file__).resolve().parents[1]
        review_plan = (root / "agents/skills/review-plan/SKILL.md").read_text(encoding="utf-8")
        plans = (root / "agents/skills/plans/SKILL.md").read_text(encoding="utf-8")
        review_loop = (root / "agents/skills/review-loop/SKILL.md").read_text(encoding="utf-8")
        execute_plan = (root / "agents/skills/execute-plan/SKILL.md").read_text(encoding="utf-8")
        receiving_review = (root / "agents/skills/receiving-review/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("When no prior blocker count exists, continue one review round to establish the trajectory baseline", review_plan)
        self.assertIn("at most one concrete simplification or refactor attempt", review_plan)
        self.assertIn("pause for operator direction before another change or review", review_plan)
        self.assertIn("for the entire review run", review_plan)
        self.assertIn("never renews across later rounds or triggers", review_plan)
        self.assertIn("the run-wide `self_heal_attempt` member", review_plan)
        self.assertIn('"status":"consumed","run_id":"<stable-run-id>","round":"rN","source_digest":"<sha256>"', review_plan)
        self.assertIn("A resumed post-fence workflow reads the latest value", review_plan)
        self.assertIn("it is consumed or unknown", review_plan)
        self.assertIn("resume records `status:\"unknown\"` with the current round's `review-run-id`", review_plan)
        self.assertIn("Use the active mechanical-churn and recurrence triggers, convergence decisions, and bounded self-heal rule defined in `review-plan`", plans)
        self.assertIn("review-plan`'s Scope and complexity policy", plans)
        self.assertIn("review-plan`’s Scope and complexity policy", review_loop)
        self.assertIn("per review-plan's Scope and complexity policy pause duty", execute_plan)
        self.assertNotIn("must reduce the nonnegative blocker count", plans)
        self.assertNotIn("at most one concrete simplification or refactor", review_loop)
        self.assertNotIn("at most one concrete simplification or refactor", execute_plan)
        self.assertNotIn("Before a sixth full-panel round, stop for user direction", plans)
        self.assertIn("Reflect at every configured total-round and full-panel interval; intervals are checkpoints, not stop limits", review_loop)
        self.assertNotIn("Max 5 full-panel rounds", review_loop)
        self.assertIn("the execution plan expressly authorizes", receiving_review)


class PlanLaunchTemplateRecordContractWitnessTest(unittest.TestCase):
    """The Plan Quality Gate's sub-agent launch template carries the staging
    record contract, and a record shaped exactly by that template validates
    clean on the first pass while a missing required field is rejected."""

    def test_launch_template_carries_validator_contract(self):
        plans = (Path(__file__).resolve().parents[1] / "agents/skills/plans/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("review_usage_capture.py mint", plans)
        self.assertIn("- review-run-id:", plans)
        self.assertIn("- review-started-at-ms:", plans)
        self.assertIn("- Record kind: canonical", plans)
        self.assertIn("a `## Findings` section carrying", plans)
        self.assertIn("populated `### Witness ledger` section", plans)
        self.assertIn("top-level `record_kind` field", plans)
        self.assertIn("- Coverage:", plans)
        self.assertIn("- Witness ledger:", plans)
        self.assertIn("- **Consequence**:", plans)
        self.assertIn("- **Blocking**: true|false", plans)
        self.assertIn("- **Reachability**:", plans)
        self.assertIn("- **Blast radius**:", plans)
        self.assertIn("- **Confidence**:", plans)
        self.assertIn("- **Pattern**:", plans)
        self.assertIn("- **Triage**:", plans)
        self.assertIn("#### Comment", plans)
        self.assertIn("#### Analysis", plans)
        self.assertIn("`blocking`, `consequence`, `reachability`, `blast_radius`, `confidence`", plans)
        self.assertIn("extensions.convergence.self_heal_attempt", plans)
        self.assertIn("schema source of truth", plans)

    def test_template_shaped_record_validates_clean_and_rejects_missing_field(self):
        import hashlib
        import json
        import subprocess
        import sys
        import tempfile
        from datetime import date

        root = Path(__file__).resolve().parents[1]
        validator = Path(__file__).with_name("validate_review_staging.py")
        run_id = "0f1e2d3c4b5a69788796a5b4c3d2e1f0"
        started_ms = "1791632600000"
        slug = "launch-template-witness"
        record_date = date.today().isoformat()
        plan_text = (
            "# Witness plan\n\n"
            "A minimal plan artifact shaped for the plans-skill launch-template contract witness.\n"
            "\n"
            "### Task 1: record a sample finding\n\n"
            "Files:\n"
            "- docs/example.md\n"
        )
        digest = hashlib.sha256(plan_text.encode("utf-8")).hexdigest()
        markdown = f"""# Plan Review: launch template witness (r1)

## Metadata
- Type: Plan Review
- Record kind: canonical
- Date: {record_date}
- URL or Artifact: plan.md
- Depth: full
- Domains: review-staging
- Round: r1
- Review mode: fresh-adversarial
- Changed-risk signals: none
- Prior findings supplied as filter: no
- Last fix commit: N/A
- Witness ledger: N/A (no public mutators)
- Coverage: clean
- Panel mode: focused
- Selection reason: single-worker witness fixture under the shared selection rules
- review-run-id: {run_id}
- review-started-at-ms: {started_ms}
- Source digest: {digest}
- Findings: 1
- Status: STAGED

## Review Statistics

### Panel
| Worker | Lenses | Parent worker | Status | Raw | Solo | Echo | Relaunch |
|--------|--------|---------------|--------|-----|------|------|----------|
| correctness-completeness | quality, implementation | none | complete | 1 | 1 | 0 | no |

### Counts
- Workers launched: 1
- Workers skipped: 0
- Raw findings (all workers): 1
- Staged findings: 1
- Discarded during synthesis: 0
- Solo staged (unique agent origin): 1
- Echo staged (multi-agent dedup): 0

### Deduplication groups
None (each staged finding had a single agent origin).

### Discarded findings
None.

### Severity calibration
None (agent severities matched staged severities).

### Triage outcomes
| Worker | Lens | Staged | Fixed | Dropped | Deferred | Pending |
|--------|------|--------|-------|---------|----------|---------|
| correctness-completeness | quality | 1 | 0 | 0 | 0 | 1 |

## Findings

### Critical

None.

### High

None.

### Medium

#### F1. Sample finding for the launch-template witness
- **Severity**: Medium
- **Blocking**: false
- **Consequence**: A template-launched worker could omit the field and fail the staging gate after the round.
- **Reachability**: common
- **Blast radius**: single-service
- **Confidence**: verified
- **Pattern**: quality#sample-witness-gap
- **Workers**: correctness-completeness
- **Triage**: pending
- **Anchor**: plan.md, the Task 1 heading
- **Source**: [Prose]

#### Comment (posted as-is when approved)
Keep the witness fixture aligned with the validator's current contract.

#### Analysis (not posted)
The block mirrors the launch template's field bullets so the validator's finding gate exercises the same shape a template-launched worker emits.

### Low

None.

## Summary
Counts (Critical | High | Medium | Low): 0 | 0 | 1 | 0
Blocking findings: none
Verdict: ready=no (one pending non-blocking sample finding exercises the finding gate)

## Verdict for this round (before fixes)
ready=no (the sample finding is the fixture's finding-gate exercise, not a defect report)
"""
        sidecar = {
            "schema_version": 1,
            "review_type": "Plan Review",
            "date": record_date,
            "artifact_slug": slug,
            "round": "r1",
            "depth": "full",
            "domains": ["review-staging"],
            "panel_mode": "focused",
            "selection_reason": "single-worker witness fixture under the shared selection rules",
            "source_kind": "plan",
            "source_digest": digest,
            "escalation_reason": "none; single-worker witness fixture",
            "review_mode": "fresh-adversarial",
            "risk_signals": [],
            "prior_findings_filter": False,
            "last_fix_commit": None,
            "record_kind": "canonical",
            "coverage": {
                "outcome": "clean",
                "material_lens_set": ["quality", "implementation"],
                "completed": ["quality", "implementation"],
                "missing": [],
            },
            "counts": {
                "workers_launched": 1,
                "raw_findings": 1,
                "staged_findings": 1,
                "discarded": 0,
                "solo_staged": 1,
                "echo_staged": 0,
            },
            "panel": [
                {
                    "worker": "correctness-completeness",
                    "lenses": ["quality", "implementation"],
                    "parent_worker": None,
                    "descendant_launches": [],
                    "status": "complete",
                    "raw": 1,
                    "solo": 1,
                    "echo": 0,
                    "relaunch": False,
                }
            ],
            "deduplication_groups": [],
            "discarded": [],
            "severity_calibration": [],
            "triage_outcomes": [
                {
                    "worker": "correctness-completeness",
                    "lens": "quality",
                    "staged": 1,
                    "fixed": 0,
                    "dropped": 0,
                    "deferred": 0,
                    "pending": 1,
                }
            ],
            "findings": [
                {
                    "id": 1,
                    "severity": "Medium",
                    "blocking": False,
                    "consequence": "A template-launched worker could omit the field and fail the staging gate after the round.",
                    "reachability": "common",
                    "blast_radius": "single-service",
                    "confidence": "verified",
                    "pattern": "quality#sample-witness-gap",
                    "workers": ["correctness-completeness"],
                    "triage": "pending",
                    "theme": "Launch-template witness",
                }
            ],
            "overflow": [],
            "soften_watchlist": [],
            "verdict": "no",
            "extensions": {
                "raw_findings": 1,
                "staged_findings": 1,
                "blocking": 0,
                "nonblocking": 1,
                "convergence": {
                    "self_heal_attempt": {"status": "unused", "run_id": run_id}
                },
            },
        }

        def run_validator(staging_path, plan_path):
            return subprocess.run(
                [sys.executable, str(validator), "--hard", "--source-plan", str(plan_path), str(staging_path)],
                capture_output=True,
                text=True,
                cwd=str(root),
            )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            plan_path = tmp_dir / "plan.md"
            plan_path.write_text(plan_text, encoding="utf-8")
            staging_path = tmp_dir / f"{record_date}-plan-review-{slug}-r1.md"
            staging_path.write_text(markdown, encoding="utf-8")
            sidecar_path = tmp_dir / f"{record_date}-plan-review-{slug}-r1.stats.json"
            sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
            clean = run_validator(staging_path, plan_path)
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            self.assertIn("OUTCOME: pass", clean.stdout)
            mutated = json.loads(sidecar_path.read_text(encoding="utf-8"))
            del mutated["findings"][0]["consequence"]
            sidecar_path.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
            rejected = run_validator(staging_path, plan_path)
            self.assertNotEqual(rejected.returncode, 0, rejected.stdout)
            self.assertIn("OUTCOME: fail", rejected.stdout)



def _named_evidence_label(criteria):
    """The driver's full named Phase 0 evidence-refusal label for the
    criteria, built through the same single-homed wrap the create boundary
    raises."""
    try:
        runtime_capabilities.evidence_criterion_ids(list(criteria))
    except ValueError as error:
        return str(_named_evidence_limit_error({"task-1": {"required_criteria": list(criteria)}}, error))
    raise AssertionError("fixture criteria must exceed an evidence limit")


class ExtractionRuleParityTest(unittest.TestCase):
    """Parity fixtures (contract single-sourcing Task 2): a plan the create
    boundary refuses at Phase 0 on an extraction-rule ground fails
    certification with the same full label text. The classification labels
    are witnessed at unit level over the SAME owned function both surfaces
    call (the create boundary's --plan path derives matching actions, so
    those labels are seeding-shape grounds not expressible as plan files);
    the clone-signature arm is the plan's recorded residual (its inputs are
    discovery-internal)."""

    def _readiness_reason(self, plan_text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        plans_dir = Path(tmp.name) / "plans"
        reviews_dir = Path(tmp.name) / "reviews"
        plans_dir.mkdir()
        reviews_dir.mkdir()
        plan, _ = _write_clean_state(plans_dir, reviews_dir, plan_text=plan_text)
        reason = evaluate_readiness(plan, plans_dir, reviews_dir)[1]
        _clean_reviews_dir(reviews_dir)
        return reason

    def test_evidence_item_bytes_parity(self):
        criterion = "x" * 600
        reason = self._readiness_reason(
            "# Fixture plan\n\n### Task 1: fixture\n\n- [ ] " + criterion + "\n"
        )
        expected = _named_evidence_label([criterion])
        self.assertIsNotNone(reason, "certification must fail on the item-bytes ground")
        self.assertIn(expected, reason)

    def test_evidence_aggregate_bytes_parity(self):
        criteria = [f"c{index}-" + "y" * 500 for index in range(9)]
        body = "\n".join(f"- [ ] {criterion}" for criterion in criteria)
        reason = self._readiness_reason("# Fixture plan\n\n### Task 1: fixture\n\n" + body + "\n")
        expected = _named_evidence_label(criteria)
        self.assertIsNotNone(reason, "certification must fail on the aggregate-bytes ground")
        self.assertIn(expected, reason)

    def test_evidence_criteria_count_parity(self):
        criteria = [f"criterion-{index:03d}" for index in range(101)]
        body = "\n".join(f"- [ ] {criterion}" for criterion in criteria)
        reason = self._readiness_reason("# Fixture plan\n\n### Task 1: fixture\n\n" + body + "\n")
        expected = _named_evidence_label(criteria)
        self.assertIsNotNone(reason, "certification must fail on the count ground")
        self.assertIn(expected, reason)

    def test_clean_plan_certifies_past_extraction_arm(self):
        reason = self._readiness_reason(
            "# Fixture plan\n\n### Task 1: fixture\n\n- [ ] small criterion\n- [ ] Commit: land the fixture\n"
        )
        self.assertIsNone(reason, f"a clean plan must certify: {reason}")

    def test_classification_labels_unit_parity(self):
        # The classification labels are single-homed: the same function the
        # driver's create boundary calls raises the exact strings, and the
        # driver's create manifest surfaces them unchanged for a seeding
        # shape that skips discovery.
        item = {"task_body": "- [ ] do a thing\n", "checklist_actions": None}
        with self.assertRaises(ValueError) as refused:
            runtime_capabilities.check_checklist_action_classification("task-1", item)
        self.assertEqual(str(refused.exception), "task task-1 has unclassified checklist actions")
        item = {"task_body": "- [ ] do a thing\n", "checklist_actions": [{"text": "other", "owner": "worker"}]}
        with self.assertRaises(ValueError) as refused:
            runtime_capabilities.check_checklist_action_classification("task-1", item)
        self.assertEqual(str(refused.exception), "task task-1 checklist action classification is incomplete")
        item = {"task_body": "", "checklist_actions": [{"text": "", "owner": "worker"}]}
        with self.assertRaises(ValueError) as refused:
            runtime_capabilities.check_checklist_action_classification("task-1", item)
        self.assertEqual(str(refused.exception), "task task-1 has an unclassified checklist action")


if __name__ == "__main__":

    unittest.main()
