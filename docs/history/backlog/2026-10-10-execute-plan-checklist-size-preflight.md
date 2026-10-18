# Backlog: validate execute-plan checklist size before plan certification

- **Filed:** 2026-10-10, observed during execution of the plan-scope gist surface
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** observed execution preflight failure
- **Class:** fix-class
- **Driving force:** reliability
- **Cluster:** docs/history/plans/completed/2026-10-12-pre-round-gate-dimension-parity.md; docs/history/plans/completed/2026-10-13-plan-review-cross-task-lifecycle.md

- **Cluster:** docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md (backlog-wide survey: readiness and preflight gate surface)
## Problem

The plan's first acceptance criterion was 558 bytes, above the execute-plan runtime manifest's 512-byte per-item limit. The run could not seed its execution manifest until the criterion was decomposed. That edit changed the already reviewed plan and forced a fresh review cycle before implementation could start.

The limit is enforced at execution admission, after plan authoring and review have treated the checklist as ready. The plan author therefore receives no early signal that its structure cannot be represented by the execution contract.

## Expected

Validate each task acceptance item against the execute-plan manifest's actual size and shape constraints during plan authoring or readiness, before the final plan review. Report the offending item and limit with a clear correction path. Keep the plan's semantic acceptance criteria intact when translating them into machine-readable task records; do not silently truncate or weaken them.

## Evidence

- Plan: `docs/history/plans/2026-10-10-plan-scope-gist-surface.md`.
- Observed 2026-10-10: execute-plan refused to seed its manifest because Task 1's criterion was 558 bytes and the runtime item limit was 512 bytes.
- Decomposing the criterion changed the reviewed plan digest and required a fresh plan-review round before execution.

## Recurrence witness (2026-10-17, learn Step 1.8 dedupe)

Third cycle with the same failure class: the 2026-10-17 authoring cycle spent five more gate-time splits (the plan readiness gate's per-item byte cap) across three commits, with the project corpus measure-while-drafting rule already in place. The plans skill's authoring guidance still carries no measurement duty, so the signal reaches the author only at gate time; routed to the exec log as a composition-time duty entry (Priority re-affirmed at normal).
