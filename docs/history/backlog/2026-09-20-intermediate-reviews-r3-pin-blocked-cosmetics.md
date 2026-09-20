# Backlog: fix the two r3 pin-blocked cosmetic findings in the intermediate-task-reviews surfaces

Status: open
Workflow: backlog
Source: code review round r3 of docs/plans/2026-09-20-execute-plan-intermediate-task-reviews.md (staging doc docs/reviews/2026-09-20-execute-plan-intermediate-task-reviews-code-review-r3.md, finding R1; triaged valid and deferred to backlog). Both are cosmetic wording fixes blocked by exact-string validation pins in the certified plan's `## Validation Commands`.
Severity: Low (two cosmetic wording fixes, bundled)
Exact location: agents/skills/execute-plan/SKILL.md heading `### Consumes \`review-panel-selection\` skill (per-task intermediate tiers)`; agents/skills/plans/SKILL.md **Review tier hint (optional)** Plan Format bullet (the sentence "The tier is a starting point only: post-implement risk signals may raise the tier and never lower it.").
Why not fixed now: V5 pins the Consumes heading string `### Consumes \`review-panel-selection\` skill (per-task intermediate tiers)` and V8 pins the plans fragment `post-implement risk signals may raise the tier and never lower it`; correcting either wording moves a pinned plan fragment, and any edit to the certified plan's Validation Commands moves the plan digest and requires a fresh review round (decision: r3 triage, 2026-09-20).
Driving force: docs

## Problem

Two residual wording defects survive r3 because an exact-string validation pin covers each site:

1. **Consumes heading names a file a "skill".** The execute-plan integration-point heading `### Consumes \`review-panel-selection\` skill (per-task intermediate tiers)` calls `agents/skills/review-agents/review-panel-selection.md` a skill; it is a reference subsection file inside the `review-agents` skill, not a `SKILL.md` package. Readers resolving the name as a skill directory fail.
2. **Plans tier-hint bullet restates one tier clause.** The plans **Review tier hint** bullet restates the tier-precedence clause ("post-implement risk signals may raise the tier and never lower it") that `review-panel-selection.md` **Per-task intermediate review selection** owns; the same bullet already directs authors to treat that subsection as the sizing authority, so the restated clause is a drift-prone duplicate (V8 pins its current wording).

## Suggested fix

In a follow-up change that edits the certified plan's Validation Commands (any edit there moves the plan digest and needs a fresh review round): re-pin V5 on the renamed heading (drop the "skill" misnomer, e.g. `### Consumes \`review-panel-selection\` (per-task intermediate tiers)`) and re-pin V8 on the trimmed plans bullet (keep the `Review tier: <L|M|H>` pin and a pointer to the selection subsection instead of the restated precedence clause). Derive every new fragment byte-exact from the then-current tree, and run the block on the unchanged tree first to prove the new pins do not over-pin.
