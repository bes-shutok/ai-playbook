# r429 plan stale text: "schema 3" and external-gate parenthetical

Driving force: the 429-retry-storm plan's Task 1 bullets 2 and 4 carry stale text — "additive under schema 3" (the state schema is 4 since the P6 landing) and "(the external-gate reason joins this list when the park-guard plan lands)" (park-guard already landed; the reason is already in the exemption list). The executed skill text is correct; only the plan prose lags. Status: open.

- Source: intermediate review (correctness-completeness + testing workers) of Task 1, 2026-09-21.
- Suggested fix: next time the plan file is touched for a digest-validating round, amend the two phrases to match reality.
- Third stale instance (review r4 address, 2026-09-21): Assumption 5's parenthetical "(the scheduler reads the report on the next turn)" contradicts the landed operator-facing-only rule (maintenance SKILL.md: the structured rate-limited end-of-run report is operator-facing only; no report-retrieval primitive exists and none is assumed, so the scheduler's durable ingestion surfaces are the surfaced stop, the child manifest's timestamped stop lines, and the state file's `rate_limited_events` append, not the report). Same suggested fix: amend the phrase next time the plan file is touched for a digest-validating round.
