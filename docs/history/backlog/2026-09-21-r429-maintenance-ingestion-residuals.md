# Backlog: r429 maintenance-side rate-pressure ingestion residuals

Driving force: harden the rate-pressure ingestion contract landed 2026-09-21 (provider-429-retry-storm-shaping, `agents/skills/maintenance/SKILL.md`): the launch-kind ingester reads free-text stop lines written by execute-plan runs, and every coupling between the two sides is currently prose-soft. Status: open

Suggested fix (one or more of):

1. Pin the writer-side stop-line token format in execute-plan (e.g. a line-initial `rate_limited:` token followed by an ISO timestamp) and mirror the pinned format in the maintenance launch-kind ingestion rule, so the execute-plan writers and the maintenance ingester cannot drift (today both sides say "a timestamped rate-limited stop line" without a fixed token shape).
2. Carry dedup keys in a ledger decoupled from the 20-entry capped `rate_limited_events` array: the ingest rule already keys entries on the `{ts, kind, target}` triple, but the capped array is its only dedup basis, so eviction at the cap can re-admit an already-ingested manifest stop line once its entry is evicted, and a long spike day re-counts evicted events.
3. Extend the Step 6 lost-update consequence enumeration (the "a lost update otherwise degrades ..." sentence) to name the rate-pressure rail: a lost `rate_limited_events` append silently lowers `rate_pressure` and can un-defer a turn the signal meant to hold.
4. Tighten the plan's witness needles to the numerals ("at most 3 concurrent subagent launches", "(floor 1)") if the `## Validation Commands` gate block of docs/plans/2026-09-19-provider-429-retry-storm-shaping.md is ever revised: today's needles ("concurrent subagent launches", "halves its fan-out cap") hold for any cap numeral, so a numeral drift would stay gate-green.
5. Define-once trims for the `rate_pressure` derivation: the "derived count of entries within the last 24 hours" definition is restated in the D1 deferral, the Step 1 retention arm, the ingestion bullet, and the state-file schema block; keep one canonical definition (the schema block) and reference it elsewhere, so a threshold or window change cannot land in one restatement and miss the others.

Source: phase 3 review round 1 (fresh-adversarial panel) of the provider-429-retry-storm-shaping execution, 2026-09-21; residuals backlogged after the r1 fix pass landed in commit c60f7f22.
