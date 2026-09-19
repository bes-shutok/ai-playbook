# Backlog: enforce the peak-window pricing check on every child dispatch path

Status: open
Priority: high

Workflow: backlog
Source: witnessed 2026-09-16 morning: a resume execution child was dispatched at 07:38 local - inside the weekday peak window (Mon-Fri 14:00-18:00 UTC+8 = 07:00-11:00 local at UTC+1, where GLM-5.3-Flash deducts at 1.2x instead of 0.4x, a 3x cost differential) - and ran plan-execution tokens at peak rates. The user halted the run and directed scheduling the continuation at 11:00 local (the first off-peak minute). The off-peak preference EXISTS in the maintenance skill's quota leg (agents/skills/maintenance/zcode.md: defer fire times landing inside the peak window to the window's end, starvation exception), but it only binds SCHEDULER turns running the full skill; operator-driven and resume dispatches (a turn answering a user request, a child continuation) skipped it entirely.
Severity: High (up to 3x token cost on the most expensive workloads the repo runs)

## The gap, precisely

1. **The pricing rule is skill-scoped, not dispatch-scoped.** The quota leg runs inside maintenance scheduler turns. A manual session, an operator turn, or a resume dispatch creates clocked children without ever consulting the peak window. Witnessed three times on 2026-09-15/16: the 07:38 resume child, the 17:53 dispatch-ladder experiment (fine by luck, off-peak), and the original hourly-cadence children.
2. **The 5-minute floor amplifies exposure.** The dispatch floor was lowered from 30 to 5 minutes (2026-09-15, user request for fast pickup). A quick dispatch now lands inside whatever pricing window is current, with no buffer to reconsider.
3. **The fire-time horizon rule covers exhaustion but not price.** The quota leg defers when `minutes_remaining` at fire time is under 60 (exhaustion risk) and when the probe says pause - but pause_decision "continue" with 200+ minutes remaining is exactly when a peak-window fire slips through at 3x cost.
4. **Probe exit code is 1 even on usable output**, so ad-hoc dispatches that "check the probe" tend to treat it as broken and skip it.

## Fix candidates (in preference order)

1. **Make Step 4 (quota leg) unconditional for every clocked child dispatch, from any session type.** Restate in SKILL.md Step 5 (scheduling) and the runtime overlay: before creating ANY clocked child (scheduler turn, operator request, resume continuation), compute the fire time's position against the pinned peak window (Mon-Fri 14:00-18:00 UTC+8, converted to local at runtime); if the final fire time lands inside the window, defer to the window's end unless the starvation exception applies (>24h since the last execution dispatch) or the user explicitly overrides in the same request. The 11:00-local boundary is the natural default deferral target in the UTC+1 morning window.
2. **Pin a tiny helper script** (`scripts/peak_window_check.py`, or extend quota_window_probe.py with a `--fire-at <iso>` mode): given a proposed fire time, print `peak|off-peak` plus the defer-to timestamp, exit 0 when off-peak, exit 2 when peak (a distinct code so "probe dead" is never confused with "peak"). The scheduler turn, the backlog-driven dispatches, and manual sessions all call one command - no timezone arithmetic in agent heads (the UTC-vs-local year-roll trap already bit once).
3. **Carry the check into dispatch tooling discipline:** the dispatch-ladder step 1 text gains "run the peak-window check first; on peak, schedule at the window end and say so in the state file's decision_reason (`quota_status: deferred-peak`)" so the deferral is auditable in the state file.
4. **Backfill the state schema:** `quota_status` gains the `deferred-peak` value alongside `ok|unknown`, and the children entry records the original requested time alongside the deferred fire time, making peak-avoidance measurable.

## Acceptance criteria

- No clocked child (from any dispatch path) fires inside the weekday peak window unless the starvation exception or an explicit same-request user override is recorded in the state file.
- A single script answers "is this fire time peak?" for any proposed time, used by the scheduler turn, the resume/continuation dispatches, and manual sessions; the pins suite covers its contract.
- This incident is the witness: the 07:38 peak-window resume run, halted by the user, resumed at 11:00 local as the first off-peak minute.
