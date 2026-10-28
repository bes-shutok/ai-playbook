# Window-distribution dispatch policy: fill the 5h window, cap parallel sessions at 3

Added: 2026-10-28 (operator ask: "sessions should be distributed within 5h window to fill it with work but not trigger more than 3 parallel sessions")

## Problem

Child dispatch timing today is driven only by quota/pricing rules (the Quota leg's runtime-fit rule, peak-pricing deferral, and the governor's pressure classes). Nothing distributes fires across the account's 5-hour window: several one-shot carriers can land on the same minutes (witnessed 2026-10-27/28: five user-directed one-shots stacked between 00:21 and 05:22 local), while other stretches of the window sit idle. The fleet cap is 4 concurrent children (`agents/skills/maintenance/guards.md` fleet cap, P54); the operator wants the working ceiling at 3 and wants the window deliberately filled — work spread through the 5 hours rather than clustered at fire times.

## Expected outcome

- A scheduling rule (home: the Step 5 scheduling module or the runtime overlay) that, when choosing a fire time inside the current or next window, spreads dispatches across the remaining minutes instead of stacking them at the earliest legal slot, subject to the runtime-fit rule and pricing deferral.
- A parallel-session ceiling of 3 live children (executions + authoring + audit/re-triage combined), replacing the fleet cap's 4 as the operative dispatch bound, counted by the existing discovery/state-file/listing arms.
- The count visible to the deciding turn before every dispatch (it already is via the fleet arms; the rule change is the ceiling value plus the distribution clause).

## Non-goals

- No change to lane-independence (one execution and one authoring per turn remain the per-lane caps).
- No new probe or governor state; reuse `quota_window_probe.py`'s window bounds and the existing fleet counting.

## Witness

- Operator ask 2026-10-28 (this row's Added line); automation listing 2026-10-27/28 showing five stacked one-shot carriers (22:00, 00:21 x2, 01:00, 02:28, 05:22) against an otherwise idle window.
