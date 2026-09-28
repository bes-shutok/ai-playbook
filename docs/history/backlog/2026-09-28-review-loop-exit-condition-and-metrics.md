# Review-loop exit condition and metrics: stop on zero blocking findings, measure before capping

Status: open
Priority: high
Workflow: backlog
Class: simplicity
Driving force: simplicity

## Problem

Corpus measurement of 2026-09-28 over 1,616 review docs and 375 plans (regex over the `Counts:` and `Ready for execution:` lines; format drift across July-September makes blocker counts a lower bound, medium and verdict trends robust): 22 percent of plans stop at exactly the five-round cap; docs at r14-r15 still report ready=No half the time; the historical exit condition (Blocker=0 AND Medium=0) is unsatisfiable because any panel looking at changed bytes generates non-blocking findings at a roughly constant rate. The loop therefore terminates by cap, not by convergence, and rounds past two or three are dominated by fix-on-fix churn (the 2026-09-26 convergence directive diagnosed the same shape).

A hard round cap of 2-3 was proposed the same day and then consciously softened by user direction: other projects may carry more complex plans that legitimately need more rounds, and limits tuned to this repo must not be imposed on them blindly. A same-day follow-up direction re-scoped the split (user, 2026-09-28): the original strict rules stay available for personal pet projects (the operator's personal repos root, e.g. ~/Projects/myrepos/ on this machine; the owning skill resolves the root from a facts key such as personal_projects_root, never hardcoded in shared prose), while the rest (company and other projects) keep the metrics-first treatment and only gain limits later from their own measured data.

Per-project strictness split, therefore:

- Pet projects (this repo included): the full original strict package applies mechanically: blocking-only exit, default two rounds with a hard cap of three, simplify-or-rewrite instead of patching when blockers survive a verification round, and cap-closure protocol retirement in these projects' surfaces.
- All other projects: metrics-first: blocking-only exit (the unsatisfiable Medium=0 shape goes everywhere), advisory stop-and-escalate guidance, no new mechanical cap until the aggregated per-project data justifies one; limits are deferred to an evidence-cited follow-up decision per project.
- Instrumentation is global: the metrics aggregation pass runs for every project's review corpus, because pet-project data also feeds the calibration and the company-project decisions are made from their own reports.

## Observed versus expected

- Observed: readiness is judged by the (variously encoded) blocker-plus-medium exit shape; per-round counts exist in the review docs but are never aggregated; no per-project calibration exists; the mechanical five-round cap and the cap-closure protocol stand unchanged.
- Expected: readiness means zero blocking findings; ordinary (non-blocking) findings are recorded in the staging docs or backlog, never chased with new rounds. The loop is instrumented before it is limited: per-round counts are aggregated mechanically and reported periodically, segmented per project and per plan-complexity band, so a later limits decision can differ per project. Advisory (non-mechanical) stop guidance lands now: stop when the latest round produced no new blocking findings; when blockers survive a verification round, escalate to simplify or rewrite the plan instead of patching again. The existing five-round mechanical cap and the cap-closure protocol stay until a later decision cites the measured decay data and retires or lowers them deliberately.

## Suggested fix

One plan that (1) makes the blocking-only exit the mechanical rule everywhere the blocker-plus-medium shape persists (plans, review-plan, receiving-review, execute-plan re-cert arms), (2) adds a metrics aggregation pass over the review corpus (extend scripts/summarize_review_stats.py or its successor) reporting findings-per-round decay, ready-rate per round, and cap-exhaustion rate, segmented per project and complexity band, run by the maintenance loop's periodic report, (3) writes the advisory stop-and-escalate guidance into the review skills without a new mechanical gate, (4) applies the per-project strictness split: pet projects (personal repos root resolved from a facts key) get the strict package mechanically (default two rounds, hard cap three, simplify-or-rewrite on surviving blockers, cap-closure protocol retired in their surfaces), while other projects keep the advisory shape and record the explicit decision point that a later plan lowers or retires their round cap and cap-closure protocol only after that project's aggregated data confirms the direction. For non-pet projects deletion is deferred, not cancelled; the cap-closure polish family stays rejected either way as unwitnessed machinery polish.

## Additional witness: consumer plan review

Repeated review and reconciliation cycles on a consumer plan eventually converged: the latest full panel had zero blockers and was ready, with two Low findings explicitly deferred. A later full panel was triggered after removing a valid Jira hostname to satisfy a privacy scan, even though the plan contract and readiness evidence were unchanged. The extra round was caused by unnecessary sanitation, not by an unresolved plan issue. Fixing the false-positive policy addresses this witness without weakening the exact-digest review requirement.

## Environment

User direction 2026-09-28: start with less radical limitations and more metrics to confirm the direction later, per project; convergence directive 2026-09-26; the corpus measurement recorded above is the witness for authoring this item, not yet for the caps.
