Status: open
Priority: medium
Class: fix-class
Origin class: residual scope split from a partially covered backlog origin

# Backlog: Add focused coverage for remaining handoff reconciler refusals

Driving force: code-quality

## Problem

The origin row `docs/history/backlog/2026-10-31-handoff-reconciler-refusal-coverage-trio.md` records three uncovered refusal classes. The plan `docs/history/plans/2026-11-08-handoff-reconciler-date-stripped-plan-slug.md` addresses the `plan-identity-mismatch` defect and its dated-path false refusal. Two independent coverage gaps remain: `artifact-slug-unusable` and the reachable `review-evidence-drift` outcome when a same-digest review round lands between reads.

## Remedy

Add focused regressions for both remaining classes, or record the covered set in the test docstring as the origin requested. Preserve each refusal's existing no-mutation and receipt/evidence behavior. This residual item owns only these two independent test gaps; the separate plan-identity fix is out of scope.

Source: split from docs/history/plans/completed/2026-11-08-handoff-reconciler-date-stripped-plan-slug.md after the identity defect was fixed and archived on 2026-11-08.

Dedup probe: searched `docs/history/backlog/` and `docs/history/plans/` for `artifact-slug-unusable`, `review-evidence-drift`, and same-digest review drift on 2026-11-08; only the source origin row contained both residual classes, so this item preserves that exact remainder after the identity scope is promoted.
