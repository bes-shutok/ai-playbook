# Backlog: preservation pins for the r4 scoping fixes are born GREEN

Status: open
Workflow: backlog
Origin: 2026-09-16-maintenance-scheduler-liveness r1 review (finding T-3, deferred to backlog by the triage)
Severity: Low (test-discrimination gap, not a product gap)
Scope: scripts/check_maintenance_pins.sh

## Problem

Two preservation pins in the maintenance pins suite were born GREEN: the
spans they require (the ambiguous-outcome carve-out's "treat the child as
dispatched" span in zcode.md, and the "counts as success only after one more
listing confirms" span in prompt-templates.md) existed identically on main
before the liveness plan landed. The r4 scoping fixes refined the sentences
around those spans (the carve-out became scoped to cap-shaped refusals or
listing-verified success; the success-via-existing clause gained the failed-
confirmation escalation route), but the pins only require the common span to
be present, so they cannot distinguish the scoped rewrite from the older
unscoped text. A regression that reverts the surrounding sentence to its
unscoped form while preserving the pinned span keeps the suite green.

## Consequence

The suite's guarantee for these two invariants is presence-only: a manual
edit or a bad merge that restores the pre-r4 unscoped wording passes the
pins. The r1 address pass added an rc-aware negative pin for the superseded
listing-driven re-arm span (the same pattern this fix sketch needs), so the
mechanism exists; the missing piece is the negative pins for these two
older superseded wordings.

## Fix sketch

1. Extract the exact pre-r4 unscoped wordings from git history (the zcode.md
   and prompt-templates.md revisions on main before the liveness plan's
   Task 2 and Task 3 commits), choosing minimal spans that contain the
   unscoped clause but cannot appear in the current scoped text.
2. Add one `expect_absent`-style rc-aware negative pin per span (rc 0 =
   fail, rc 1 = pass, rc >= 2 = error/fail), mirroring the negative pin
   added 2026-09-17 for the superseded re-arm wording.
3. Verify the new pins are RED against a scratch copy carrying the pre-r4
   text and GREEN on the current tree before committing.
