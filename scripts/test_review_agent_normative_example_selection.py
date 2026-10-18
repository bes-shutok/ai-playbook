"""Normative-example witness suite for the review-agent catalogs.

Pins the per-task intermediate review selection rules in
review-panel-selection.md so the every-tier normative-example exception
sentence and its prose-only retention tail are carried exactly once, while
the tier table's original rows and the focused-panel Boundary rule
paragraph survive unchanged, and pins the Normative example replay section
of documentation.md so the runnable-example wrapper-replay duty and its
evidence-and-fallback bullet are carried exactly once. Doors-registry
lens-pin style: read the file, count fixed spans, fail with a clear
message when a count is wrong.
Run: python3 scripts/test_review_agent_normative_example_selection.py
"""

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "agents" / "skills" / "review-agents"
TARGET = CATALOG / "review-panel-selection.md"
DOC_TARGET = CATALOG / "documentation.md"

SECTION_HEADING = "### Per-task intermediate review selection"
TIER_HINT_ANCHOR = "The plan's Review tier hint"

REPLAY_SECTION_HEADING = "### Normative example replay (phase 1)"
REPLAY_PATTERN_ANCHOR = "Use pattern `documentation#missing-example-replay`"

RUNNABLE_DUTY_SPAN = (
    "- A changed example is **runnable** when it is presented with an "
    "invocation a reader is expected to execute (a fenced command, a "
    "shell-wrapped snippet, a documented CLI call). A runnable example is "
    "validated by replaying the complete displayed invocation context, "
    "outer shell or wrapper included, with representative fixtures,"
)
RUNNABLE_DUTY_TAIL_SPAN = (
    "and the review evidence records the exact command and its result; "
    "checking only the inner language's syntax never satisfies the duty, "
    "because quoting, substitution, and heredoc boundaries fail at the "
    "wrapper before the inner program starts."
)
REPLAY_FALLBACK_SPAN = (
    "- When replaying a runnable example is unsafe (including content "
    "from untrusted or unreviewed sources) or not meaningful in the "
    "review context, state that limitation in the review evidence and "
    "verify the wrapper's syntax or structure with a focused check; the "
    "validate-or-inventory obligation above stays for examples that are "
    "not runnable."
)

EXCEPTION_SPAN = (
    "Exception at every tier: a diff carrying a changed normative "
    "documentation example and no code-mutation signal selects "
    "`contract-docs` plus `correctness-completeness` coverage in addition "
    "to the tier's own workers,"
)
RETENTION_SPAN = (
    " never triggering the risk-signal floor's escalation; prose-only "
    "documentation without a changed normative example keeps the tier's "
    "own worker set."
)
BOUNDARY_OPENING_SPAN = (
    "Boundary: a changed normative documentation example alone "
    "(docs-only or docs-plus-scripts diffs with no code-mutation signal) "
    "escalates `contract-docs` plus `correctness-completeness` coverage"
)
BOUNDARY_PARAGRAPH_SPAN = (
    "Boundary: a changed normative documentation example alone "
    "(docs-only or docs-plus-scripts diffs with no code-mutation signal) "
    "escalates `contract-docs` plus `correctness-completeness` coverage "
    "but does not trigger the `risk-signal floor`'s worker escalation, "
    "so docs-only focused panels stay valid; a living-documentation "
    "status claim on such a diff still requires the `doing-code-review` "
    "Step 2.5 guideline checks for the changed files' overlay, without "
    "adding a `risk` worker. Within execute-plan Step 3.1 item 5, "
    "doc/skill-only plans keep grep/hygiene commands as the `testing` "
    "worker's primary evidence."
)
TIER_TABLE_HEADER = "| Tier | Trigger | Workers |"
TIER_TABLE_SEPARATOR = "|------|---------|---------|"
TIER_ROW_LEADS = ("| Tier L |", "| Tier M |", "| Tier H |")
TIER_ROW_SPANS = (
    "| Tier L | demonstrably narrow scope and low interaction/behavioral "
    "complexity, with no risk signals; docs/skill-only work is a common "
    "signal | one worker: `correctness-completeness`, or `contract-docs` "
    "for a docs-only diff |",
    "| Tier M | moderate scope or interaction/behavioral complexity, with "
    "no risk signals; file count is supporting evidence | "
    "`correctness-completeness` plus `testing` |",
    "| Tier H | any risk signal, a concurrency or transactional mutator "
    "marker, or a public-contract change | the `### Risk-signal floor` "
    "worker set; the full five-worker panel at two or more risk signals |",
)
TIER_TABLE_PIPE_LINES = 5  # header, separator, three tier rows


def target_text() -> str:
    return TARGET.read_text(encoding="utf-8")


def doc_text() -> str:
    return DOC_TARGET.read_text(encoding="utf-8")


def tier_table_slice(text: str) -> str:
    """The window from the per-task selection heading through the
    tier-hint paragraph anchor: it holds the tier table's pipe lines."""
    start = text.index(SECTION_HEADING)
    end = text.index(TIER_HINT_ANCHOR)
    if not start < end:
        raise AssertionError(
            "tier table window inverted: the section heading appears after "
            "the tier-hint anchor"
        )
    return text[start:end]


def replay_section_slice(text: str) -> str:
    """The window from the Normative example replay heading through the
    section's `documentation#missing-example-replay` pattern declaration:
    it holds the replay-duty bullets."""
    start = text.index(REPLAY_SECTION_HEADING)
    end = text.index(REPLAY_PATTERN_ANCHOR)
    if not start < end:
        raise AssertionError(
            "replay section window inverted: the section heading appears "
            "after the pattern-declaration anchor"
        )
    return text[start:end]


class NormativeExampleSelectionTest(unittest.TestCase):
    def test_every_tier_exception_sentence_carried_exactly_once(self):
        count = target_text().count(EXCEPTION_SPAN)
        self.assertEqual(
            count,
            1,
            "per-task selection must carry the every-tier normative-example "
            f"exception span exactly once, found {count} occurrences",
        )

    def test_prose_only_retention_tail_carried_exactly_once(self):
        count = target_text().count(RETENTION_SPAN)
        self.assertEqual(
            count,
            1,
            "per-task selection must carry the prose-only retention tail "
            f"exactly once, found {count} occurrences",
        )

    def test_tier_table_and_boundary_rule_paragraph_frozen(self):
        text = target_text()
        boundary_count = text.count(BOUNDARY_OPENING_SPAN)
        self.assertEqual(
            boundary_count,
            1,
            "the focused-panel Boundary rule paragraph must survive "
            f"unchanged, its opening span found {boundary_count} times",
        )
        full_boundary_count = text.count(BOUNDARY_PARAGRAPH_SPAN)
        self.assertEqual(
            full_boundary_count,
            1,
            "the focused-panel Boundary rule paragraph must survive "
            "unchanged end to end, its complete text found "
            f"{full_boundary_count} times",
        )
        table = tier_table_slice(text)
        pipe_lines = [line for line in table.splitlines() if line.startswith("|")]
        self.assertEqual(
            len(pipe_lines),
            TIER_TABLE_PIPE_LINES,
            "the tier table must keep its original five pipe lines (header, "
            f"separator, three tier rows), found {len(pipe_lines)}: {pipe_lines!r}",
        )
        for span in (TIER_TABLE_HEADER, TIER_TABLE_SEPARATOR, *TIER_ROW_LEADS):
            count = text.count(span)
            self.assertEqual(
                count,
                1,
                f"frozen tier-table span {span!r} must appear exactly once, "
                f"found {count} occurrences",
            )
        for row in TIER_ROW_SPANS:
            count = text.count(row)
            self.assertEqual(
                count,
                1,
                "frozen tier row must survive unchanged, full row "
                f"{row!r} found {count} times",
            )


class NormativeExampleReplayTest(unittest.TestCase):
    def test_runnable_example_replay_duty_carried_exactly_once(self):
        section = replay_section_slice(doc_text())
        duty_count = section.count(RUNNABLE_DUTY_SPAN)
        self.assertEqual(
            duty_count,
            1,
            "the Normative example replay section must carry the "
            "runnable-example replay duty span exactly once, found "
            f"{duty_count} occurrences",
        )
        tail_count = section.count(RUNNABLE_DUTY_TAIL_SPAN)
        self.assertEqual(
            tail_count,
            1,
            "the runnable-example replay duty must carry its wrapper "
            "rationale continuation span exactly once, found "
            f"{tail_count} occurrences",
        )

    def test_replay_fallback_bullet_carried_exactly_once(self):
        section = replay_section_slice(doc_text())
        fallback_count = section.count(REPLAY_FALLBACK_SPAN)
        self.assertEqual(
            fallback_count,
            1,
            "the Normative example replay section must carry the "
            "evidence-and-fallback bullet exactly once, found "
            f"{fallback_count} occurrences",
        )

    def test_replay_section_preserved_lines_frozen(self):
        # Certification residual r3 F2: the replay section's preserved lines
        # (validate-or-inventory bullet, conflict rule, Boundary bullet, and
        # the Use pattern paragraph) must survive executor edits.
        text = doc_text()
        section = replay_section_slice(text)
        for span in (
            "- Either **validate** the example against the active schema, classifier, or mode rules it documents (run the validator, classifier, or rule check the example claims to satisfy), or build a structured **example inventory** recording the declared mode, required headers, protected fields, and expected result class.",
            "- An example that conflicts with its declared mode or field classification is a finding even when anchors and prose are correct. A syntactically valid example that would be rejected or classified differently under the rules it illustrates is a defect in the documentation.",
            "- Boundary: where full execution is impractical in the review context, the inventory satisfies the obligation. A successful documentation review must prove examples are not merely syntactically valid.",
        ):
            self.assertEqual(
                section.count(span),
                1,
                "frozen replay-section line must survive exactly once: " + span[:60],
            )
        # The Use pattern paragraph sits at the slice boundary (the slice ends
        # at its opening anchor), so it is pinned file-wide.
        use_pattern = "Use pattern `documentation#missing-example-replay` when a changed example is neither validated nor inventoried, and `documentation#prose-example-conflict` when an example contradicts the rule it documents."
        self.assertEqual(
            text.count(use_pattern),
            1,
            "frozen Use pattern paragraph must survive exactly once",
        )
if __name__ == "__main__":
    unittest.main(verbosity=2)
