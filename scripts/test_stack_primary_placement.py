"""Regression checks pinning primary placement in the stack workflow.

The stack placement policy is authored as Markdown rather than executable code, so
these tests pin the normative wording directly: each pin is a normative token
substring checked inside its owning span. The Task 2 to Task 4 pins are copied
verbatim from the prescribed insertion wording in
docs/history/plans/2026-11-06-primary-placement-stack-execution.md, so the suite
fails until that wording lands and matches it exactly afterwards. The
safety-preservation pins are byte-identical to today's text and anchor only on
sentences no task rewrites, so a later edit that weakens them fails.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STACK_SKILL = (ROOT / "agents/skills/execute-plan-stack/SKILL.md").read_text(encoding="utf-8")
RUNTIME_CONTRACT = (ROOT / "agents/skills/execute-plan/runtime-contract.md").read_text(encoding="utf-8")
EXECUTE_PLAN_SKILL = (ROOT / "agents/skills/execute-plan/SKILL.md").read_text(encoding="utf-8")
WORKTREE_FIRST = (ROOT / "agents/skills/execute-plan/worktree-first.md").read_text(encoding="utf-8")


def section_span(text: str, heading: str) -> str:
    """Return the span from the `## <heading>` line to the next `## ` heading."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f"## {heading}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end])


def numbered_step_span(text: str, number: int) -> str:
    """Return the span of the workflow step `<number>. ` through its indented continuations."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(f"{number}. "))
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if re.match(r"\d+\. ", lines[i]) or lines[i].startswith("## ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def paragraph_span(text: str, prefix: str) -> str:
    """Return the paragraph starting at the line beginning with `prefix`, to the next blank line."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].strip()), len(lines))
    return "\n".join(lines[start:end])


STACK_STEP_2 = numbered_step_span(STACK_SKILL, 2)
STACK_STEP_4 = numbered_step_span(STACK_SKILL, 4)
RUNTIME_CONTRACT_STACK_ENTRY = section_span(RUNTIME_CONTRACT, "Stack-task entry point")
EXECUTE_PLAN_STACK_ENTRY = section_span(EXECUTE_PLAN_SKILL, "Stack-task entry point")
PROJECT_WORKTREE_POLICY = paragraph_span(WORKTREE_FIRST, "**Project worktree policy")

# Task 2, step 2: the by-reference citation of execute-plan's Worktree-first policy,
# the resolved-placement adoption span, and the primary-resolution adoption span
# naming the recorded primary checkout and company task branch.
STEP_2_PLACEMENT_TOKENS = (
    "resolve the placement through execute-plan's Worktree-first policy by reference",
    "the policy paragraph in `agents/skills/execute-plan/worktree-first.md`",
    "adopting the established registered worktree, run context, and claim under the worktrees resolution",
    "the recorded primary checkout, company task branch, and run context under the primary resolution",
)

# Task 2, step 4: the transition runs in the resolved placement. The probe span
# carries `--skip-worktree-checks` on a primary-placement run, the manifest span
# carries the no-worktree primary form in `run_worktree`, and the preservation
# spans keep the claim refresh, transition row, predecessor order, and probe.
STEP_4_TRANSITION_TOKENS = (
    "the continuity probe verifies the current placement and recorded branch",
    "taking `--skip-worktree-checks` on a primary-placement run",
    "the manifest's `run_worktree` carrying the no-worktree primary form under the primary resolution",
    "the claim refresh and manifest identity update stay as written",
    "the transition row, predecessor order, and pre-worker probe stay as written",
)

# Task 3, runtime-contract Stack-task entry point: the adoption span accepts the
# recorded primary placement beside the worktree form and the entry's placement
# language and adoption arm cover both resolutions.
RUNTIME_CONTRACT_STACK_ENTRY_TOKENS = (
    "accept the recorded primary placement",
    "the primary checkout, company task branch, and no-worktree `run_worktree` form",
    "beside the registered worktree form",
    "the adoption arm cover both resolutions",
)

# Task 3, execute-plan SKILL.md Stack-task entry point: the same placement-neutral
# adoption wording, and the unchanged-receipt span keeping the transition receipt,
# claim agreement, probe, and validation duties.
EXECUTE_PLAN_STACK_ENTRY_TOKENS = (
    "accept the recorded primary placement",
    "beside the registered worktree form",
    "the transition receipt requirement, claim and manifest agreement, continuity probe",
    "Inclusion Hard Gate, and validation duties byte-identical",
)

# Task 4, Project worktree policy paragraph: the fresh-config consult span, covering
# the initially configured primary project and the configuration change landing
# while the bootstrap answer is pending.
POLICY_FRESH_CONSULT_TOKENS = (
    "when a placement question is outstanding",
    "re-read the project facts immediately before provisioning",
    "an initially configured primary project",
    "a configuration change landing while the answer is pending",
)

# Task 4, same paragraph: the explicit-direction precedence span, with the
# retained-placement exception named inline as its antecedent.
POLICY_DIRECTION_PRECEDENCE_TOKENS = (
    "an operator's current placement direction outranks the paragraph's resumed-run adoption rule",
    "the exception that keeps an established run's placement across a resume or stack-task adoption",
    "retained-run identity prevents duplicate ownership",
    "never authorizes refusing an operator-directed relocation",
)

# Safety preservation, byte-identical to today's text: the step 4 branch-selection
# sentence and the transition-row span, both kept as written by Task 2.
STEP_4_PRESERVED_TOKENS = (
    "serially create or switch to a task branch based on the immediate predecessor branch (first task uses the configured base)",
    "record one `stack_branch_transition:` row naming the old branch, new branch, predecessor, and task",
)

# Safety preservation, byte-identical: the policy paragraph's serialization-refusal
# span, kept as written by Task 4.
POLICY_SERIALIZATION_REFUSAL = "a fresh run in the primary checkout refuses to start while another live execution claim or recorded witness occupies the primary checkout"


class StackPrimaryPlacementTest(unittest.TestCase):
    """Keep primary placement pinned inside each owning span of the stack workflow."""

    def assert_tokens(self, span_name: str, span: str, tokens: tuple[str, ...]) -> None:
        for token in tokens:
            with self.subTest(span=span_name, token=token):
                self.assertIn(token, span, f"{span_name} is missing the pinned token: {token!r}")

    def test_owning_spans_extract_the_pinned_sections(self) -> None:
        self.assertTrue(STACK_STEP_2.startswith("2. Run execute-plan setup"))
        self.assertTrue(STACK_STEP_4.startswith("4. For each task in plan order"))
        self.assertIn("## Stack-task entry point", RUNTIME_CONTRACT_STACK_ENTRY)
        self.assertIn("## Stack-task entry point", EXECUTE_PLAN_STACK_ENTRY)
        self.assertTrue(PROJECT_WORKTREE_POLICY.startswith("**Project worktree policy"))
        self.assertIn("the primary placement is serialized by the existing execution-claim rules", PROJECT_WORKTREE_POLICY)

    def test_step_2_resolves_placement_through_the_execute_plan_policy(self) -> None:
        self.assert_tokens("execute-plan-stack step 2", STACK_STEP_2, STEP_2_PLACEMENT_TOKENS)

    def test_step_4_transition_runs_in_the_resolved_placement(self) -> None:
        self.assert_tokens("execute-plan-stack step 4", STACK_STEP_4, STEP_4_TRANSITION_TOKENS)

    def test_runtime_contract_stack_entry_accepts_the_recorded_primary_placement(self) -> None:
        self.assert_tokens(
            "runtime-contract Stack-task entry point",
            RUNTIME_CONTRACT_STACK_ENTRY,
            RUNTIME_CONTRACT_STACK_ENTRY_TOKENS,
        )

    def test_execute_plan_skill_stack_entry_accepts_the_recorded_primary_placement(self) -> None:
        self.assert_tokens(
            "execute-plan SKILL.md Stack-task entry point",
            EXECUTE_PLAN_STACK_ENTRY,
            EXECUTE_PLAN_STACK_ENTRY_TOKENS,
        )

    def test_policy_paragraph_states_the_fresh_config_consult(self) -> None:
        self.assert_tokens(
            "Project worktree policy paragraph (fresh-config consult)",
            PROJECT_WORKTREE_POLICY,
            POLICY_FRESH_CONSULT_TOKENS,
        )

    def test_policy_paragraph_states_the_explicit_direction_precedence(self) -> None:
        self.assert_tokens(
            "Project worktree policy paragraph (explicit-direction precedence)",
            PROJECT_WORKTREE_POLICY,
            POLICY_DIRECTION_PRECEDENCE_TOKENS,
        )

    def test_step_4_branch_selection_and_transition_row_are_preserved(self) -> None:
        self.assert_tokens("execute-plan-stack step 4 (preserved)", STACK_STEP_4, STEP_4_PRESERVED_TOKENS)

    def test_policy_paragraph_serialization_refusal_is_preserved(self) -> None:
        self.assertIn(
            POLICY_SERIALIZATION_REFUSAL,
            PROJECT_WORKTREE_POLICY,
            "Project worktree policy paragraph is missing the pinned serialization refusal",
        )


if __name__ == "__main__":
    unittest.main()
