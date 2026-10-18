# Backlog: preserve the recovery boundary when deferring feature work

- **Filed:** 2026-10-15, after a user corrected a deferred implementation finding's scope and documentation handoff
- **Status:** covered (docs/history/plans/2026-10-15-deferred-feature-recovery-sot-closure.md)
- **Workflow:** plan-worthy skill improvement
- **Priority:** high
- **Origin class:** consumer-feedback (company)
- **Consumer urgency:** Consumer projects that use the shared review, planning, and execution skills need a reliable handoff for deferred feature behavior; the skills-repository priority profile must not defer this as formal-hardening.
- **Class:** fix-class
- **Driving force:** reliability (secondary: docs)
- **Severity:** Medium process defect; the user corrected the record before it became the accepted handoff.
- **Source reference:** anonymized session history, 2026-10-15; no consumer identifiers, ticket IDs, class names, or internal document paths retained.
- **Exact location:** `agents/skills/receiving-review/SKILL.md` Backlog capture; `agents/skills/plans/SKILL.md` plan authoring; `agents/skills/execute-plan/SKILL.md` task-review and Phase 3 residual closure.
- **Dedup probe:** Searched open backlog titles and Problem sections for `deferred feature`, `recovery boundary`, `backlog SOT link`, `feature-named backlog`, and `implementation review deferral`. The nearest records are `docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md` (covered: review-lens coverage for implementation invariants), `docs/history/plans/completed/2026-10-05-execute-plan-review-wave-contract-gaps.md` (covered: matching findings to explicit plan scope), and `docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md` (open: recurring SOT placement and prose hygiene); this item concerns accurate recovery semantics and the backlog-to-feature-SOT handoff after a finding is deferred.

## Problem

A valid implementation finding was correctly deferred as post-MVP, but the first backlog draft described the behavior too broadly as having no retry or reconciliation path. The current behavior already allowed a caller-triggered idempotent retry; the missing capability was automatic durable recovery when that caller did not retry. The record also initially used a task-key-oriented name and had no link from the feature's implementer source of truth. The user had to correct the recovery boundary, request a feature-based backlog name, and ask for the backlog to be linked from the source document before the handoff represented the intended follow-up accurately.

The existing review, planning, and execution rules already require findings to be verified, valid unfixed work to be backlogged, and plan scope to be reconciled with source-of-truth documentation. They do not clearly require the handoff to distinguish an existing recovery path from missing automatic recovery, or to connect a deferred feature behavior to its implementer SOT when one exists. The completed post-implementation review guidance addresses review lenses and triage consequences; it does not cover this backlog/SOT closure path.

## Expected

For a deferred feature-behavior finding, the workflow accurately states what current code and tests already recover, what remains unrecovered, who or what owns the retry/recovery, and the condition that makes the gap relevant. The durable item is named for the missing behavior and linked from the feature's implementer SOT when one exists. A plan derived from the item preserves that boundary, and execute-plan closeout confirms that the accepted deferral and its SOT pointer remain consistent. Pure implementation cleanups and findings with no feature-level SOT do not gain a needless documentation task.

## Suggested investigation

- Trace the evidence and user correction from this session, without importing consumer names, ticket identifiers, class names, or internal document titles.
- Compare the existing finding-verification, backlog-capture, plan-authoring, and execute-plan closeout duties to identify the smallest shared handoff point; include `receiving-review`, `plans`, and `execute-plan`, and check whether an existing review-agent lens needs only a pointer rather than a new duty.
- Decide how to require evidence for the current recovery path versus the missing behavior, feature-oriented naming, and a backlink to an existing implementer SOT, while allowing an explicit no-SOT disposition.
- Keep the existing review-to-plan boundary and Phase 3 process. Prefer consolidating or clarifying current prose over adding a field, checklist, review round, validator, or new artifact type.
- Validate the design against both the observed case and a counterexample: a small code-only cleanup with no deferred product behavior and no canonical SOT.

## Evidence

- `agents/skills/receiving-review/SKILL.md` requires evidence-backed backlog items, deduplication, and one file per shared root cause, but does not name a feature-SOT backlink or a recovery-boundary statement as a capture condition.
- `agents/skills/plans/SKILL.md` requires checking an origin's acceptance against current SOT placement rules and recording scope decisions, but its general authoring path does not require every deferred feature behavior to be reconciled to the SOT's current-versus-missing recovery contract.
- `agents/skills/execute-plan/SKILL.md` requires durable backlog capture for valid unfixed findings and reports residual paths at closeout, but does not require verifying that a deferred feature gap is linked from its implementer SOT.
- `docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md` is covered by `docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md`; that plan strengthens review lenses and triage without changing the plan/execution handoff.
- `docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md` concerns recurring prose and SOT placement detection; it does not own the review-to-backlog-to-plan transfer or require a code-evidenced recovery boundary before deferral.

## Why not fixed now

The user asked to record the process improvement and investigate it. Editing three shared skills ad hoc would bypass the normal plan and review workflow and could duplicate existing duties. This backlog asks for the smallest coordinated correction before any skill text changes.
