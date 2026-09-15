# Backlog: review-runner coverage plan residuals (r7 non-blocking findings)

Status: open
Priority: low
Workflow: backlog
Origin: docs/reviews/2026-09-14-plan-review-review-runner-bounded-timeout-fallback-r7.md - round r7 certified the plan `docs/plans/2026-09-14-review-runner-bounded-timeout-fallback.md` ready=yes with zero blocking findings; these four non-blocking findings were captured instead of folded so the certified digest stays intact (backlog capture rule).

## Findings (all non-blocking, fail-closed direction or cosmetic)

1. `consistency#coverage-union-asymmetry` (Medium): the plan's reconciliation rule union (`missing` / `replacement[].lens` / `completed`) omits `inherited_coverage[].lens` while the verdict cross-field union includes it, so a round with its own failed worker row for a validly inherited lens is forced into degraded/no. Fail-closed direction; no false-yes path. Anchor: plan Task 2 cross-field rules.
2. `quality#elapsed-unit-ambiguity` (Low): the attempt `elapsed` bound references `retry_budget.per_attempt_timeout_minutes` but the unit of `elapsed` is not pinned (minutes implied). Anchor: plan Task 2 attempt required-field rule; Terms attempt record.
3. `testing#partial-negative-arm-coverage` (Low): Task 6's negative fixture arms enumerate 4 of roughly 9 failure modes of the attempt required-field rule; the remaining modes (missing `attempt_id`, missing `started_at`, missing `outcome`, missing `attempt_number`, negative `elapsed`) are unpinned. Anchor: plan Task 6 prompt-scope family.
4. `consistency#sanitization-claim-overreach` (Low): the plan's allowlist bullet claims sanitization is "structurally enforced" while `prompt_scope` remains a free-form string field; reword to name the remaining free-form field or constrain it. Anchor: plan Task 2 allowlist bullet.

## Disposition note

These residuals belong to the implementation plan's own text and fixtures. They can be folded whenever the plan is next edited for cause (a fold re-opens certification, so folding only these does not justify its own review round now).
