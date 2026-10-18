# Backlog: batch checkbox-flip-only done steps

Cluster: docs/history/backlog/2026-10-05-done-guard-stack-liveness-economics.md
Cluster: docs/history/backlog/2026-10-05-post-landing-staging-owned-plan-refusal.md
Cluster: docs/history/backlog/2026-10-05-done-dirt-regression-cli-path-usage.md

- **Filed:** 2026-10-05, from the review-cert-graded-binding execution retrospective
- **Status:** done (executed and archived as docs/history/plans/completed/2026-10-05-execute-plan-execution-cost-boundaries.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed execution-cost finding
- **Class:** execute-plan done-step efficiency
- **Driving force:** efficiency + token-usage
- **Impact on the witnessed run:** high. Nine done sub-agents, each 2-6 minutes and ~300k tokens, each producing a one-file commit whose content the parent had verified minutes earlier; roughly 35 minutes and ~2.5M tokens across the run, recurring on every multi-task execution.

## Problem

Step 1.4 launches a full done sub-agent per task even when the done commit carries only the task's own checkbox flips in the plan file and the implement work is already committed and verified. The per-task done boundary exists (introduced fe61c847) to give learn a per-task log handoff and keep a defect boundary per task; both goals survive batching, but the sub-agent spawn for a trivial commit does not pay for itself.

## Evidence

- Witnessed run: nine done commits (one per task) each spun a dedicated sub-agent; commit subjects in the 9d6cdc75 squash.
- agents/skills/execute-plan/SKILL.md Step 1.4 and agents/skills/done/SKILL.md: the done flow reads the preceding log, verifies, commits, updates the manifest.
- agents/skills/execute-plan/agent-logs.md: the log-handoff contract the batching arm must preserve.

## Expected

When the task's done delta is exactly the plan file's own checkbox flips (the classifier's checkbox-flip class over the task section) and the implement commit is verified, the parent performs the done commit itself under a scripted verification (log exists and non-empty, checkboxes confined to the task section, tests green) and records the manifest row; a done sub-agent launches only when the delta is broader or the log/verification contract cannot be met mechanically. Learn's per-task capture contract keeps its per-task log inputs either way.

## Why not fixed now

Retrospective turn; the change edits the execute-plan/done contract pair and needs its own authored plan.

## Source

- Landing commit 9d6cdc75.
- agents/skills/done/SKILL.md
