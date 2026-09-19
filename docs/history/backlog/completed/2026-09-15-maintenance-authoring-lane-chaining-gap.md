# Backlog: authoring lane does not chain promptly after an authoring child completes

Status: done (executed via docs/plans/completed/2026-09-16-maintenance-scheduler-liveness.md, 2026-09-17)
Workflow: backlog
Source: user observation 2026-09-15 (~20:35Z): "since one plan is authored we should have immediately scheduled another; since it didn't happen" — captured after the plan-readiness legacy-verdict-grammar authoring child (automation-6a6135ce, fired 17:12:28Z) finished its full workflow (plan certified r5 ready=yes, committed to main fb887813 at ~19:52Z) without any follow-up authoring dispatch.
Severity: Medium (authoring throughput loses up to ~5h per completed child; the plan queue drains slower than the 2h cadence allows)
Scope: agents/skills/maintenance/SKILL.md, agents/skills/maintenance/zcode.md

## Problem

When a clocked authoring child completes early, the authoring lane stays closed until the next
scheduler turn AFTER the child's 6-hour outcome horizon, and the turns in between stand the lane
down for reasons that do not survive inspection. Witnessed chain on 2026-09-15:

1. Outcome horizon holds the lane: the child-outcome check runs only for pending children whose
   `fire_at` plus 6 hours has passed (SKILL.md "Failure detection and the failure cap"). The
   authoring child stayed `outcome: pending` until 23:12Z, and the state-file arm of `G1a` keeps
   the lane busy while a pending child's `fire_at` + 6h has not elapsed. The horizon is sized for
   execution children (observed runs of one to four hours); an authoring child runs 30 to 120
   minutes, so up to ~5 hours of authoring-lane capacity are wasted per completed child.
2. Deliverable attribution fails across sessions: the 19:32:16Z scheduler turn stood authoring
   down with "its plan deliverable remains in peer hands (untracked file)". The turn saw the
   freshly authored but not-yet-committed plan file and could not attribute it to the completed
   child (sessions are isolated), so it treated the deliverable as a peer's in-flight work.
3. Stale idle-task attribution: the same turn recorded "OffPeak slot held by the queued
   watchdog". The watchdog (offpeak-ae6b76c6) belongs to the dead 16:44Z session; the one-idle-
   task-slot conflict is per session ("This session already has a pending idle-time task"), so a
   fresh automation-born scheduler turn is not actually blocked by it, but the turn conservatively
   counted it.

## Suggested fix

- Early authoring outcome checks: once a pending authoring child's `fire_at` has passed (not +6h),
  each scheduler turn evaluates the SKILL.md progress predicate directly (a top-level plan now
  references the target item, or the item left the backlog top level) and records
  `outcome: progress` + `outcome_checked_at` on observe. The state-file arm then releases the lane
  on the next decision, because it only holds the lane while the outcome is still pending. Keep
  the 6-hour horizon as the failure threshold for children that never show progress.
- Per-session idle-slot attribution: the idle-lane check (zcode.md "Idle-time lane visibility")
  counts only idle-time tasks whose `sessionId` matches the current session as blockers for
  OffPeakCreate; foreign-session queued tasks are reported, not treated as lane-occupying.
- Deliverable attribution becomes unnecessary once the early progress check exists (the plan file
  plus a conforming sidecar is objective evidence, independent of which session committed it); if
  attribution is still wanted, the authoring child's done pass may record `outcome: progress` on
  its own state-file row as a targeted field edit.

## Notes

- The 19:32Z turn's caution was correct under the rules as written; this item changes the rules.
- Parent availability interacted with the same window (the 429-killed vrs child died before its
  re-arm; its requeue hit the action-selection loop captured in
  `2026-09-15-maintenance-rearm-action-selection-loop.md`; the review-runner execution child
  armed 20:41Z carries the re-arm duty). That is a separate failure family and is not fixed here.
- Queue position: this item is dated 2026-09-15, so oldest-first selection reaches it after the
  2026-09-13 and 2026-09-14 items; the owner may want to prioritize it given it costs ~5h of
  authoring-lane time per cycle until fixed.
