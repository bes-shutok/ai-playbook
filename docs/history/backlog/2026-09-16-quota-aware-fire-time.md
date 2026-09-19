# Backlog: scheduler turn does not compare child runtime against the quota window's remaining minutes

Status: open
Priority: high (user re-affirmed 2026-09-16: run execution always when possible - assess the current 5h window, the next reset, and current token cost, and schedule the next execution as soon as it makes sense rather than sticking to the origin cadence)
Workflow: backlog
Source: scheduler turn 2026-09-15T07:15Z: the probe read primary 89% used with roughly 80 minutes left in the 5h window; the turn deferred the authoring dispatch for PRICING and then lost it to the selection loop, and never asked the quota question "can a 30-120 minute authoring child even finish in the remaining window?" The window reset a few hours later; the 2026-09-16T11:15Z turn found the window fresh (1% used, 299 minutes left) - firing immediately was quota-optimal and required no deferral at all.
Severity: Low-Medium (a child fired into a near-exhausted window is guaranteed a mid-run budget pause and resume cycle, or a quota death like the 429 kill witnessed 2026-09-15)
Scope: agents/skills/maintenance/SKILL.md (Step 4 quota leg), agents/skills/maintenance/zcode.md (Quota leg)

## Problem

The Step 4 quota leg only defers when the probe's pause_decision says pause (used >=
budget_pause_max_used_percent, default 90) or for pricing windows. Between "fresh window" and
"pause threshold" there is a band (roughly 60-90% used) where the clocked child fires into a
window that cannot fit its expected runtime, guaranteeing a mid-run pause/resume (or death)
that the child-side budget guard then has to clean up.

## Suggested fix

- Add a runtime-comparison rule to the quota leg: estimate the child's expected runtime
  (execution 1-4h per the lane guards; authoring 30-120m observed) and, when
  minutes_remaining at the planned fire time is less than that estimate, fire at
  reset_at_epoch instead (quota-fresh), regardless of pricing preference; record the
  comparison in the state file's decision reason.
- Mirror the same comparison in the execute-plan and plans Budget gates' resume scheduling so
  a paused child resumes into a window with enough minutes, not just after the reset minute.

## Related

- 2026-09-15-maintenance-indefinite-operation.md (FIX-6 liveness; the 429 death witness)
- backlog peak-window dispatch discipline item (pricing check - this item adds the quota-duration check)
- 2026-09-18-maintenance-quota-aware-lane-decisions.md (decision-layer consumption of the same quota numbers - per-lane bias and recorded decision-time quota state)
