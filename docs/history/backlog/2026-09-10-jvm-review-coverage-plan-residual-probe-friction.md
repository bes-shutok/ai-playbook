# Backlog: jvm-review-coverage plan residual probe friction

Status: open
Workflow: backlog
Source: plan review r6 Lows from docs/reviews/2026-09-10-plan-review-strengthen-jvm-review-coverage-r6.md (plan docs/plans/2026-09-10-strengthen-jvm-review-coverage.md, certified ready=yes zero blocking)
Severity: Low
Class: validation-probe robustness

## Problem

Two non-blocking Low findings remained at plan certification and were
captured instead of folded (fold rounds r2-r5 each regenerated a new trivial
Low family; the loop exited on zero blocking per the standing churn-control
decision).

1. `implementation#validation-probe-wrap-fragility`: several `grep -qF` pins
   in the plan's Validation Commands span multi-word phrases that the target
   files render line-wrapped (for example `review-panel-selection.md` breaks
   the risk-signal sentence before "downstream"). The prescribed inserts are
   textually correct, but a differently wrapped insert would fail the probe.
   The fail direction is closed (no false pass), so this is execution
   friction only. If an execution round trips on it, flatten before matching
   (`tr '\n' ' '` with `tr -s ' '`) per the wrap-tolerance rule, or scope the
   pin to a single-line fragment.

2. `consistency#informal-evidence-class-label`: the plan's Assumptions cite
   "backlog evidence classes 1-4 and 10", but the backlog item numbers
   classes 1-9; the staging-gate class (Guideline Pack paths plus applied
   rule hints) is the unnumbered paragraph after class 9. Fixing the label in
   the plan would break the certified digest binding, so the fix belongs to a
   future plan update round (which forces a fresh certification round), not
   to the execution sessions.

## Suggested fix

Fold both into the strengthen-jvm-review-coverage plan at its next
certification-triggering update: wrap-tolerant matching for the long pins,
and renumber the Assumptions class labels to match the backlog's numbering
with an explicit name for the unnumbered staging-gate class.
