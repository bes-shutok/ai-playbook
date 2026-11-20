# Backlog: maintenance works indefinitely - capacity-aware chaining for occupied lanes

- **Filed:** 2026-11-08
- **Status:** covered (docs/history/plans/2026-11-08-maintenance-capacity-aware-chaining.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** operator-directed
- **Class:** fix-class
- **Driving force:** efficiency

## Observed versus expected

Observed (witness: the 2026-11-08 12:24Z scheduler turn, sess_8ed699c9): both
lanes held at decision time by fresh peer claims, so the turn recorded two D3
deferrals and stopped, leaving the loop dark until the recurring parent's
next slot (here the following day 11:00 UTC) even though the 5h allowance had
abundant room and every peer hold was minutes-to-completion work, not a
multi-hour occupancy. The quota leg was recorded `unknown/fail-open` without
running the probe, so no capacity reasoning happened at all.

Expected: a scheduler turn whose lanes are held by occupancy or locks does
not end the loop's work for the day. It (a) runs the quota probe and reasons
capacity per the quota-aware lane decisions, (b) when the binding window fits
another typical run, arms a near-future one-shot retry carrier (the lane's
dispatch-slice payload) at the next sensible slot instead of going dark, and
(c) when the stop is the 5h wall itself, schedules the successor right after
the window reset (reset_at + the standing arming margin), per the existing
quota-aligned cadence rule extended to lane-deferral stops.

## Suggested correction

1. Add a turn-level `occupied-lane chaining` duty to the maintenance skill's
   decision step: when a lane decision resolves to a deferral whose reason is
   occupancy- or lock-shaped (fresh foreign claim, merge/done lock held,
   pending-landing occupancy) and the quota leg permits (probe used_percent
   and minutes-to-reset fit a typical run by the existing evidence standard),
   the turn arms one near-future retry one-shot for that lane (bounding: one
   retry slot per lane per turn, slot at or after the freshest blocking
   claim's likely completion, default +45 minutes) instead of ending dark.
2. Bind the 5h-wall stop to the reset-anchored successor: a stop recorded
   with quota pressure class `constrained`, `near-reset`, or `exhausted`
   arms the chain one-shot at the probe's reset_at + the standing 10-minute
   margin, reusing the quota-aligned cadence rule's arming shape.
3. Record both arms in the state file with the existing writer classes
   (children[] entry with the armed automation id, or pending_rearm park when
   the create primitive is unavailable), so the next turn's state-first read
   sees them; no new state fields.

## Witness

- The 12:24Z turn's own state-file entries (outcome deferred, quota_status
  unknown, next_turn_at pointed at the next day's recurring slot).
- The disk record at 12:26Z: peer commits 12:03Z/12:16Z/12:17Z, fresh exec
  claim 11:54Z, done lock held - the holds were real but short-lived, and
  the loop still went dark for ~22 hours.
