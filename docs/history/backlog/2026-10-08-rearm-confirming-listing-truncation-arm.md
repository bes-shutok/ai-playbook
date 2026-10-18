# Backlog: re-arm confirming listing needs a truncation arm

- **Filed:** 2026-10-08
- **Status:** covered (docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed decision-input gap
- **Class:** fence-class
- **Driving force:** reliability
- **Cluster:** docs/history/backlog/2026-10-16-automation-create-misroute-after-carrier-delete.md (the same re-arm ladder's listing-as-decision-input steps; the misroute row's probe arm extends the truncation arm)

## Problem

The re-arm ladder's confirming-listing step, the turn-start carrier re-arm duty's listing arms, and the pending-rearm armed verification all treat the automation listing as binary evidence: a recognition match restores the carrier, no match escalates. The listing primitive's output is capped by the platform's result budget, and a session whose own spawner record carries a large prompt echo can receive a listing truncated inside the automations array while the call itself exits clean, so records past the cap are invisible. The duty then faces a partial-evidence decision with no written arm: reading absence from the truncated listing risks creating a duplicate parent, and re-polling burns the dispatch-discipline loop budget against the same cap.

## Evidence

- Observed 2026-10-08 during a scheduled execution child's FIRST ACTION re-arm: the confirming listing returned truncated inside the session's own spawner echo (a multi-tens-of-KB prompt payload), leaving the automations array past the cut unverifiable; no compact alternative surface exists (no CLI subcommand for automations, no queryable store table).
- The session resolved by convergent recorded state: the state file's children[] record documenting the parent's delete-plus-create earlier the same day, the sole-restorer condition, and the safe-direction arm (park `pending_rearm` with the paired payload copy), recording the truncation itself in `rearm_note`. The decision rule is captured as user-level lesson #541.
- Second divergence input, witnessed 2026-10-14: a re-arm create landed (a later touch's listing shows the ENABLED recognition match, correct title, template opening line, and future fire time) while its paired targeted state edit never did - the state file kept the dead parent id, a standing `parent_absent_since`, and the parked `pending_rearm` + `rearm_note`, so the rearm-on-touch check classified darkness from state alone. The standing park's mandated armed-verification listing self-healed the shape: the touch re-observed the live carrier, applied only the bookkeeping edits (parent re-key, absent/park/note cleared in one targeted edit), and consumed the paired payload copy - no duplicate create. The residual exposure is the crash window between a create and its state edit; the same fail-safe adjudication arm this row asks for covers it.

## Expected

Give the re-arm ladder a written truncation arm for every listing-as-decision-input step: on a truncated listing, do not read absence from the visible prefix and do not re-poll; adjudicate from the recorded mutation journal plus the actor map, prefer the arm that fails safe (a park a later primitive-capable actor discharges beats a duplicate create), and record the truncation in `rearm_note`. Mirror the arm in the turn-start carrier re-arm duty and the pending-rearm armed verification, which share the shape.

## Why not fixed now

The active request is a done closeout. The ladder text is dense, plan-rewritten policy that belongs to an authoring cycle, and the loop is currently parked (`pending_rearm` stands in the state file), so no live actor is blocked by the gap today.

## Source

- Observed 2026-10-08 during a scheduled execution child's re-arm duty in this repository.
