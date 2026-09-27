# Backlog: plan's residual-closure ledger carries no coverage basis and lags later rounds' findings arrays

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: correctness

## Problem

The certification-machinery plan's `## Residual findings (cap closure)` section lists exactly the r5 sidecar's 17 staged patterns. When the gate's disposition-accounting conjunct (plan Task 1) runs against a LATER round's sidecar carrying the `extensions.cap_closure` declaration, the under-reporting conjunct fails until the section is amended (one stranded finalize plus a reconcile pass); if the plan instead lands clean via the ordinary arm, the landed bytes carry a ledger claiming a cap-closure finalize that covers no round the landing history actually has. The gate is fail-closed, so no wrong behavior ships.

## Observed versus expected

- Observed: r7 correctness-completeness finding (Low, plausible-edge); the current execution path reads the latest round (r7, clean, no declaration), so nothing strands today.
- Expected: the section states its coverage basis (which sidecar round's findings array it claims to cover), or the gate's declaration-round conjunct ties the section to the declared round's sidecar only (which Task 1's round floor already approximates).

## Suggested fix

Add one coverage-basis line to the residual section (naming the r5 sidecar as the covered record) in a follow-up docs edit, or fold the basis sentence into Task 1's probe wording when the plan executes.

## Environment

r7 execution-time re-cert round, 2026-09-27; deferred per the backlog-deferral default.
