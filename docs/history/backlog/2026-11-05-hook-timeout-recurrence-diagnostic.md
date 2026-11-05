Status: open
Priority: low
Class: fix-class (bounded diagnostic; no behavior change)
Origin class: witnessed defect (24h runtime telemetry, 2026-11-05 harvest pass)

# PreToolUse hook timeouts recur under parallel-session load; the degraded-consult cost is unmeasured

## Problem

Six PreToolUse hook timeouts on 2026-11-04 between 14:37 and 15:47 UTC, each surfacing as a failed Edit tool call, concentrated in the parallel-session windows. The timeout pins themselves are correct (5s and 10s, exactly the skill-gate README's own rule: a hung core must degrade to a missed consult, not block a Write/Edit for the default long timeout), so this is not a misconfiguration row. The residual question is why the hook core exceeds its 5-10s budget repeatedly under parallel load, because each timeout costs a blocked edit, a failed tool call, and a retry turn, and the frequency (six in one afternoon) suggests a slow path in the hot consult flow rather than ambient load.

## Observed vs expected

Observed: recurring bounded timeouts with no record of what the core was doing when the budget expired.
Expected: one diagnostic pass identifies the slow path (the git resolver subprocess, the marker window scan, or session-channel derivation under contention); if the cause is a fixable slow path, narrow it without changing the guard's decision semantics; if not, document the degraded-consult frequency as accepted cost in the hook README's outcomes section.

## Evidence (trimmed)

- Telemetry 2026-11-04: hook.run.failed with timeout cause at 14:37:42 (x2), 14:37:52 (x2), 14:48:32, 15:47:01, spanning four sessions; same-day Edit tool.call.failed count 39 (the day's largest tool-failure bucket; the timeout subset is the six above).
- The pins are already right: the runtime config carries 5s (first hook) and 10s (second hook), matching `agents/hooks/skill-gate/README.md` ("Host hook timeout", the r15-M4 kill-after-resolver-timeout semantics).

## Suspected root area

`agents/hooks/skill-gate/` core consult path (the git resolver and the marker freshness window are the two known subprocess steps). Guard-bearing path, so the row routes to a plan, never the ad-hoc lane, even for the diagnostic pass.

## Ship when

The README's outcomes section names the measured timeout cause and either the narrowed path (with the pins suite green) or the accepted-cost note; no decision-semantics change.
