# Backlog: budget probe pauses despite low usage and on imminent reset (margin logic ignores both signals)

Status: done (executed via docs/plans/completed/2026-09-20-quota-aware-scheduling-semantics.md, 2026-09-21)
Workflow: backlog
Source: user correction (Andrey, 2026-09-20, two messages) on the context-budget plan execution: at the Step 3.1 wave boundary the probe returned `pause_decision: pause` with the binding primary window at **15% used** and 10 minutes to the next 5h reset, and the orchestrator executed the full pause protocol (guard flag armed, boundary recorded, run stopped, cross-session resume deferred). The user ruled the pause wrong on both readings: (1) with plenty of quota remaining there was absolutely no reason to pause whatsoever; (2) an imminent reset means quota renews in minutes — ride it out, never stop the lane.
Severity: Medium (behavioral: unjustified pauses waste the execution lane, fragment runs, and force the pause/resume machinery into use exactly when it is least needed)
Exact location: `scripts/quota_window_probe.py` pause-decision logic — the `--minutes-before`/`--min-protocol-minutes` margin branches fire on CLOCK PROXIMITY ALONE, never consulting `used_percent` (the observed pause fired at 15% used) — and the pause-protocol text in `agents/skills/execute-plan/SKILL.md` (Budget gate section) that treats any `pause` verdict as a stop-and-resume-later boundary.
Why not fixed now: the executing session is mid-Phase-3 of the context-budget plan under the dispatch contract (continue, do not branch into probe rewrites); the fix changes gate machinery owned by no plan task and needs its own review round.
Driving force: efficiency

## Problem

The probe's pause decision fires when the binding window's remaining minutes fall below the protocol-completion margin (`--min-protocol-minutes`, default 10) or inside the `--minutes-before` threshold — without distinguishing "not enough quota to finish the next wave" from "plenty of quota and the window renews in N minutes". In the observed case (15% used, 10 minutes left, margin 10) the probe paused a run that had over 80% of the window unused, the lane sat idle across a reset that was minutes away, and a later session had to re-enter through the resume path with an epoch-checked guard-flag clear. Correct semantics:

1. **Usage gate first**: pause is only a candidate when the window's `used_percent` is at or above the `--max-percent` threshold (or the estimated cost of the next wave does not fit the remaining quota). Clock proximity with low usage is a continue, always.
2. **Imminent-reset ride-through**: when minutes_remaining is small and the reset is in the future, return a new decision (e.g. `pause_decision: wait-for-reset` with `wait_minutes`) instead of `pause` — the gate waits out the boundary and re-probes on the fresh window, in-session, no guard flag, no watcher, no cross-session resume.
3. Only "high usage AND reset not imminent" triggers the full pause protocol.
4. Add the discriminating tests: (a) used_percent 15 + minutes_remaining == min_protocol_minutes + future reset → continue or wait-for-reset, never pause; (b) used_percent >= max-percent + minutes_remaining < need → pause; (c) used_percent >= max-percent + imminent reset → wait-for-reset.

Trigger: next touch of `scripts/quota_window_probe.py` or the execute-plan Budget gate section.
