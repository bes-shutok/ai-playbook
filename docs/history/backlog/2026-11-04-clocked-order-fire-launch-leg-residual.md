# Backlog: clocked-order fire command lacks a launch-before-discharge receipt leg

Status: open
Workflow: backlog
Priority: low
Origin class: self-serving
Quarantine: 2026-11-04
Class: fix-class
Driving force: reliability
Cluster: docs/history/backlog/2026-11-05-automation-fire-time-failure-verification.md (same defect class: a fired carrier strands silently at the fire boundary; that row owns the runtime scheduler carrier, this row owns the chain fire path)

## Problem

The chain fire path records the ledger discharge event without gating on a receipt from the payload launch: a fired order can discharge cleanly and still strand the turn when the launch itself fails, a fire-boundary instance of the silent-strand class (docs/history/backlog/completed/2026-10-18-clocked-order-discharged-order-silent-strand.md; the discharge-only shape was witnessed in `build_clocked_order_fire_command` and the discharge-on-fire branch of the clocked-order operation during the 2026-11-03 authoring round r1 of the conceded duplicate plan). The 2026-11-03 activation plan priced this residual through the warning-only detector family and named it in its Edge cases sentence; this row holds the structural mitigation candidate, not a re-litigation of the activation scope.

## Expected

A fired order discharges only after a launch receipt, and a launch-failed order lands in the existing `clocked-order-due` missed marking instead of a clean discharge.

## Suggested change

Reorder the fire path to launch-before-discharge with the receipt as the discharge precondition; on launch failure record a failure event and let the due detector mark the order, per the conceded duplicate plan's launch-leg task (branch tip 87b79bd95, discarded 2026-11-04 after insight extraction; its own review series staged the leg through r4).

Adoption trigger: the activation plan's re-open trigger (a witnessed chain misfire re-opens the default via a new plan) or a recorded verify-successor catch; until then the detector family covers the gap by design.
