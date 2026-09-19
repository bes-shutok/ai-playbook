# Backlog: cache breakpoint overflow silently taxes every request

Captured: 2026-09-19 (source: cross-session friction audit - 7 days of app logs, 117k tool_usage rows, 5.4k sessions mined)
Status: open
Priority: medium

Workflow: backlog

## What was witnessed

Every single model request emits `model.sdk.warning`: "Maximum 4 cache breakpoints exceeded (found 5). This breakpoint will be ignored." - 16,288 identical warnings over 2026-09-13 → 09-19 (flat per day; 35% of all warn volume). The context assembler requests 5 cache breakpoints against a provider limit of 4, so one breakpoint is silently dropped on every request. Two costs: part of the assembled context never gets a cache breakpoint (token cost and latency on every call - this multiplies across ~30k requests/week and all parallel subagents), and 16k lines of pure log noise bury real warn signals.

## Suggested fix

Make the context assembly emit at most 4 breakpoints: merge the two least-valuable adjacent stable prefixes (or drop the lowest-value breakpoint) so the assembled context fits the provider limit deterministically. Alternatively expose a config knob selecting which context sections earn breakpoints. Then either eliminate the warning at the source or downgrade it to a single startup notice.

## Acceptance

- A 24-hour log window shows zero breakpoint-overflow warnings.
- No cache-hit regression on long sessions (spot-check token usage per turn before/after).
- Warn-level log volume drops by roughly a third.
