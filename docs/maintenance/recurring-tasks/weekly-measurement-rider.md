```toml
id = "weekly-measurement-rider"
cadence_days = 7
kind = "rider"
```

# Recurring task: weekly measurement rider lane

You are running the `recurring task weekly-measurement-rider lane` in the repository at <REPO_ROOT> (the resolved repository root; this body runs verbatim in a fresh session with only that root). The registry consult owns this task's due-read; due rider entries execute at the maintenance skill's Step 7 in-turn and fail open. The Throughput block's "state file" is the scheduler state file `.ai-playbook/scheduler-state.json` at the resolved repository root (project runtime dir; gitignored). The rider never creates an automation, never registers a hook, and never adds a crontab entry.

## Run procedure

Weekly gate (the task's own due-read): when the newest prior report under the report home (`tool-runtime-stats/` under the resolved tmp directory, newest = lexicographically greatest run-stamped filename) is absent or at least 7 days old, run `python3 scripts/tool_runtime_stats.py` (offline; the store path resolves from the `session_store_path` facts key, fallback `$HOME/.zcode/cli/db/db.sqlite`). The rider never creates an automation, never registers a hook, and never adds a crontab entry.

On success: append the digest as one new section to `docs/maintenance/tool-runtime-stats-log.md` (create-if-absent; aggregates only), and for every candidate at or above the filing threshold (total >= 300 seconds/day, or mean >= 10 seconds at >= 50 calls/day) file one backlog item under the resolved backlog directory with a header matching the newest existing backlog item's header fields (newest = the backlog item whose filename sorts last lexicographically), with its `Origin class:` line set per receiving-review's capture rule (a measurement-rider filing is self-serving unless the measured cost was witnessed in a consumer project), naming the measured row, the proposed replacement shape, and the estimated saving. When no candidate clears the threshold, record one no-action verdict line, naming the report's top row and its measured cost, in the same digest-log section as the appended digest.

Review-metrics pass (the same due-read): run `python3 scripts/summarize_review_stats.py --metrics --metrics-markdown <report-home>/review-metrics-<run-stamp>.md` and append one aggregates-only section to `docs/maintenance/review-metrics-log.md` (create-if-absent; findings-per-round decay, ready-rate per round, cap-exhaustion share, segmented by complexity band, the resolved project key riding the section header), sharing the tool-runtime-stats rider's guard, cadence, and fail-open semantics. `<report-home>` is the resolved metrics report directory, `~/.ai-playbook/review-telemetry/reports/` (the write creates a fresh tree, so a first run never fails on a missing directory).

## Throughput block

Throughput block (added 2026-09-28, the maintenance autonomous pipeline plan): after the digest (and the no-action verdict line when one is recorded), append a throughput block to the same digest-log section the rider already writes (aggregates only; no new script, no new file), opening with the literal heading `Throughput`. Per period, the block records the count of `children[]` entries by kind and evidenced outcome, the authoring completions and the execution completions, an entry evidencing its completion per the state-file arm's evidence classes (an author-kind entry by its target plan passing the certification oracle, an execute-kind entry by its target plan archived); the count is stated as a lower bound over the state file's retention window, the `children` array keeping the last 20 entries, and the block names that bound so no reader takes the number as a true period total. The block next records the count of entries whose outcome records a `turn_error` or a parked recovery: an entry whose outcome is `failed`, an entry whose `outcome_reason` records a park (the `deferred` unblock deferral or the covered-stand-down park), beside the state file's standing `turn_error` value and any parked record (`pending_dispatch`, `pending_rearm`) read at report time. This count is the durable-source-driven proxy for the origin's "manual interventions required" measure, and the block records that proxy decision so no reader mistakes it for a direct measure: the state file keeps no per-turn error ledger, so the retention-window failure and park entries stand in. The block last records the current queue depth, ready prompt-log entries, plan-uncovered open backlog items, and open top-level plans (the per-turn queue-depth token's three counts), which reads live state and has no retention bound.

## Fail open

Fail open: a rider error is reported in the turn output without failing the turn; the turn's decisions and state are never blocked by measurement. Absent store or tables produce the script's own one-line report and exit 0. A failed pass records `last_result` and takes the consult's one-day failure advance, so a persistently failing rider does not re-execute every turn.

## State advance

State advance: stamp `next_due` at completion plus the task's `cadence_days` through the record's atomic-replace rules; on the first completed run, stamp `next_due` from the newest existing report's date plus the cadence when one exists, otherwise completion plus the cadence; set `last_run_at`, a one-line `last_result`, and reset `consecutive_failures` on completion.
