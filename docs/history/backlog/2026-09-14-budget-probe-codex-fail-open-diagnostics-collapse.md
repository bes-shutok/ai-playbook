# Backlog: budget probe, codex fail-open reason collapses two distinct diagnostics

Status: open
Origin: execute-plan Phase 3 r5 review of docs/plans/2026-09-13-budget-gate-quota-fixes.md (design-simplicity lens, F2); deferred at the round cap (round 5 of 5; folding would mutate the digest and require a sixth round).

## Finding

Since the per-entry drop arms landed (r2/r3), `probe_codex` (~L423) emits "rollout carried no rate_limits record" for BOTH "the newest rollout has no rate_limits record" AND "a record exists but every window dropped per-entry validation" (non-mapping window, missing resets_at, non-finite/out-of-range used_percent). Pre-branch, malformed window values surfaced as the accurate "codex rollout parse failed: ...". The zcode sibling distinguishes its shapes ("zcode quota response carried no usable limits"). Operator impact: a codex-path status:unknown cannot be diagnosed without opening the rollout.

## Recipe

Track whether parse_codex_rollout saw a rate_limits record that yielded zero windows; emit a distinct reason (align with the zcode wording, e.g. "rollout rate_limits record carried no usable windows") for the all-windows-dropped shape; update `test_codex_malformed_used_percent_fail_open`'s pin accordingly.

## Verification bar

A rollout fixture with one healthy + one malformed window still parses the healthy window; a record with all windows malformed yields the NEW distinct reason; a record-less rollout keeps the old reason.
