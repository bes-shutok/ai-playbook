# pins-gate pinned baseline stale: FINAL STEP prefix count red

Status: open
Priority: low
Class: known-red-baseline
Cluster: docs/history/backlog/2026-11-20-known-red-baseline-stales-under-landing-traffic.md (the same baseline-drift family)
Driving force: the pins suite now prints `PIN FAIL: FINAL STEP prefix count` on primary main (verified 2026-11-20 on the unmodified primary checkout and at execution base 16dcaaa04, needle 3 at authoring base a774c701a, 2 at execution base), while the plan-pin whitelists only the healed all-served stale-entry line; landing 51d5e3e29 recorded the drift. Every 2026-11-18-or-later plan pinning the baseline-relative pins gate fails its pins line until the pinned baseline is refreshed.

## Acceptance
- The owning maintenance surface refreshes the pinned baseline for the pins gate (the whitelisted known-red line set) to the current tree's standing failures, or the FINAL STEP prefix count red is repaired to three occurrences, so plans pinning the gate pass with zero unexplained failure lines.
- The refresh or repair is witnessed in the pins checker's own output (the filtered run prints no failure lines on main).
