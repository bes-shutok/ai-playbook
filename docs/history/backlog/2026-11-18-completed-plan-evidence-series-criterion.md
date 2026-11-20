# Backlog: Align the completed-plan evidence-series criterion with persisted evidence

- **Filed:** 2026-11-18, execute-plan Phase 3 code review
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** code-review-finding
- **Driving force:** code-quality (primary), efficiency (secondary)
- **Source reference:** `.ai-playbook/reviews/2026-11-18-handoff-reconciler-dead-drift-mappings-code-review-r1.md`, F4
- **Exact location:** `docs/history/plans/2026-11-13-handoff-reconciler-dead-drift-mappings.md`, Task 4 contract-semantics criterion

## Problem statement

The completed plan says the accepted completion's evidence trail remains in the plan review-staging series after requeue and later acceptance. The implementation stores the original worker-receipt digest, effect verdicts, and review binding in `scope_recovery`; later acceptance replaces `terminal_receipt`. The plan review records do not contain the worker receipt or effect-evidence map, so the stated evidence destination is not demonstrated.

## Expected behavior

The plan's audit-trail claim names an evidence home that the implementation and its witnesses actually preserve, or the runtime contract persists the promised evidence in the review series.

## Suggested fix

Re-derive the intended audit-trail contract. Either narrow the completed-plan criterion to name the runtime-state and session-log evidence that is preserved, or define and implement a producer that carries the accepted completion evidence into the plan review series. Do not change a completed task's launch scope without a separately reviewed disposition.

## Why not fixed now

Task 4 is already complete and its accepted scope receipt is bound to the reviewed task section. Editing that task text during this execution would invalidate the receipt without a sanctioned post-completion scope-reconciliation path. Resolve this in a separate authoring pass.
