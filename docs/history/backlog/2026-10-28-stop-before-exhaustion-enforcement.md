# Sessions run past the 5h-window stop: enforce stop-before-exhaustion

Added: 2026-10-28 (operator ask: "most of the sessions fail to stop before token amounts runs out")

## Problem

The stop doctrine on record keys the stop to remaining GLM token percentage, not wall-clock time (operator correction 2026-10-12; memory note "quota-not-time-stop-threshold": stop when remaining drops below ~5 percent, schedule the resume at the next 5h window start), and the machinery to support it exists: `scripts/quota_window_probe.py` (window percent and minutes-to-reset), `scripts/quota_governor.py` (account-wide pressure classes), and the budget_pause/pause-boundary records. In practice, sessions still routinely exhaust their token budget mid-task: they either never re-probe after the opening read, treat the opening probe as valid for the whole run, or keep starting new lane work (the next pick of a mandate) after the point where the window can no longer fit a typical run. Witnessed repeatedly 2026-10-24 through 2026-10-28: quota-dead sessions mid-execution (the 17:06 pick-2 resume, the 19:53 carrier), stranding review rounds and parked resumes for later takeovers.

Gap: no in-run checkpoint duty requires a fresh probe read before starting each new significant work item (each plan execution, each authoring phase, each review round), and no hard stop arm converts a below-threshold reading into an immediate park of the remaining mandate with a recorded resume point. The degradation-arm thresholds exist in policy; the enforcement cadence does not.

## Expected outcome

- A mandated probe cadence: every lane decision and every new pick/phase reads a fresh probe (never a cached one older than the cadence period) before committing to the work.
- A hard park arm: a probe reading at or below the operator's stop threshold parks the remaining mandate through the existing budget_pause/resume machinery (timed resume at window start), instead of continuing until the host cuts the session off.
- The failure mode made visible: a recorded reason token (e.g. `stop-before-exhaustion`) on the park, so stranding-vs-enforcement is distinguishable in audits.

## Non-goals

- No change to the threshold value itself (operator-set, currently ~5 percent remaining).
- No new state file; the budget_pause record and children[] entries carry the evidence.

## Witness

- Operator ask 2026-10-28 (this row's Added line); quota-dead sessions 2026-10-24 (pick-2 resume holder), 2026-10-27 21:00 carrier (probe usable at dispatch, session dead before payload work), the 19:53 quota-dead carrier; memory notes "usage-wall-probe-before-timed-resume" and "quota-not-time-stop-threshold".
