# Backlog: execution design review after the mechanism-defining task

- **Filed:** 2026-10-05, from the review-cert-graded-binding execution retrospective
- **Status:** done (executed and archived as docs/history/plans/completed/2026-10-05-execute-plan-execution-cost-boundaries.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed execution-cost finding
- **Class:** execute-plan review-pipeline efficiency
- **Driving force:** efficiency + token-usage
- **Impact on the witnessed run:** highest. The Phase 3 panel's two BLOCKING findings (a consistent seal-entry move re-binding arbitrary edits; the operator-ack path unreachable through every shipped CLI) were both architectural and visible once Task 1 defined the corrections-record mechanism. Caught at hour 3 instead of hour 13, the 17M-token six-file r1 fold becomes a task-2-local fold; roughly 2h wall and an order of magnitude of fold tokens avoided.

## Problem

The execute-plan pipeline's first architecture-level adversarial review today happens in Phase 3, after every task built consumers on the core mechanism. Per-task intermediate reviews (Step 1.2b) are task-local by design and correctly missed cross-task systemic flaws on the witnessed run. The result: systemic defects surface only after maximum code depends on them, so the fold is the most expensive edit of the run.

## Evidence

- Witnessed run: plan docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md, landed as 9d6cdc75; the r1 panel (2 blocking, 1 major) and its fold commit are described in the landing message.
- agents/skills/execute-plan/SKILL.md, Phase 3: the panel runs only after all tasks; Step 1.2b scopes intermediate reviews to the single task diff.
- agents/skills/execute-plan/subagent-prompts.md: lens templates exist and are reusable for an early architecture lens.

## Expected

After the first task that defines the run's core mechanism (a plan-declared property, e.g. a `Design review anchor: after Task N` header line or a convention defaulting to the first task whose Files introduce a new module consumed by later tasks), the orchestrator launches one architecture-lens review scoped to the mechanism against the plan's threat model and contract terms, with findings folded before consumer tasks start. Keep Phase 3 as the final fresh adversarial gate unchanged.

## Why not fixed now

Retrospective turn; the change is a skill-pipeline edit that deserves its own authored plan.

## Source

- docs/tmp retrospective of the witnessed run (gitignored; facts restated here).
- Landing commit 9d6cdc75.
