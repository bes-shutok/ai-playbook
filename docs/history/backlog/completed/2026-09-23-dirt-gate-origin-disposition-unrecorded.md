# Dirt-gate fix origin left open with no recorded disposition

Status: done (resolved via docs/plans/completed/2026-09-24-p54-scheduler-loop-continuity-directives.md, Task 8)
Workflow: backlog
Disposition: 2026-09-24 (routed via docs/plans/2026-09-24-closure-strays-disposition-routing.md, Task 3): the requested routing was executed by P54 Task 8 on main at df664ad5: the twin 2026-09-22-dirt-gate-staged-deletion-edge moved to docs/history/backlog/completed/ with Status done (executed via the friction-audit plan's Task 4) and registry row dirt-gate-staged-deletion-edge; this item records that completion and routes itself closed.

## Problem statement

`docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md` (Status: open) is the origin of the Task 4 dirt-gate fix on branch `2026-09-23-ai-harness-friction-audit` (the fix is cited by the new dirt-gate regression test), but its implemented-by-this-plan disposition is recorded nowhere: the plan has no origins block and no item-by-item decision list naming it, the audit report's lifecycle summary does not mention it, and the registry has no row for it. The audit report's claim that item-by-item lifecycle decisions live in the implementation plan and the normal archive locations is therefore inaccurate for this item, and nothing mechanical forces the routing when the plan completes (the origin is absent from Task 2's initial-candidate Files list, so no task owns its move).

Evidence: grep over the plan, the audit report, and the registry finds no reference to the `2026-09-22-dirt-gate-staged-deletion-edge` basename; the plan's other three routed "done" origins and one "superseded" origin all carry correct Status lines and registry rows.

## Location

- `docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md` (Status header stays `open`)
- `docs/plans/2026-09-23-ai-harness-friction-audit.md` (no origins block)
- audit report `docs/history/reviews/`-archived lifecycle summary for this plan (over-claims decision coverage)

## Suggested fix

At plan completion, move the origin to `docs/history/backlog/completed/` with `Status: done (executed via docs/plans/2026-09-23-ai-harness-friction-audit.md, Task 4)` plus the ownership-registry row; or, if the deferral is deliberate, correct the audit report's lifecycle sentence so the record does not over-claim.

## Severity and source reference

Low. Source: code review round r1 finding F3 (workers correctness-completeness + contract-docs, deduplicated), `docs/reviews/2026-09-23-code-review-ai-harness-friction-audit-r1.md`. Capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

Non-blocking Low finding triaged to backlog capture by the r1 address-phase instruction (fix F1/F2 only; capture F3-F6 durably). The routing decision (completion-pass move vs report correction) belongs to the plan-completion pass, which the orchestrator owns; deciding it inside the fix round would preempt that pass.

Driving force: docs (source-of-truth drift), secondary: maintainability
