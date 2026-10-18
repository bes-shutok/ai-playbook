```toml
id = "friction-audit"
cadence_days = 7
kind = "audit"
state_file = ".ai-playbook/friction-audit/state.json"
```

# Recurring task: friction-audit lane

You are running the `recurring task friction-audit lane` in the repository at <REPO_ROOT> (the resolved repository root; this body runs verbatim in a fresh session with only that root). The registry consult in the maintenance skill owns this task's due-read and dispatch; this file is the procedure of record for the run.

## Run procedure

Run the quantitative pass first, then the qualitative pass, then file findings.

Cost-question rule (added 2026-10-10; origin `docs/history/backlog/2026-10-10-landing-cost-telemetry.md`, machinery audit Part 4 item 8's item-7 replacement intent): per-landing ceremony cost questions answer from `.ai-playbook/metrics/landing-costs.jsonl` (a local read; one JSON line per landing, every field nullable, absence reasons carried as named notes) - never from a store-wide mining pass. The mining passes above stay scoped to their non-cost sources: the watermarks, the token-budget accounting, and every non-cost source byte-untouched. This body is also the monthly machinery review's operative input home: the review reads `.ai-playbook/metrics/landing-costs.jsonl` as its measured input (delete-bottom-quartile-by-catch-count evidence) and enforces the writer duty's sunset (three consecutive monthly reviews with no removal or demotion decision citing the JSONL remove the done skill's writer duty; the machinery registry's removals row carries it). Invocation telemetry rides the same review cadence and the same writer-duty sunset enforcement shape the landing-cost rule already carries: the same monthly review reads `.ai-playbook/metrics/invocation-costs.jsonl` as a measured input from a bounded trailing window, names the top ten scripts by total wall time (invocation count times duration) from that window, and prunes `.ai-playbook/metrics/invocation-costs.jsonl` to that window in the same review pass; the invocation-telemetry writer duty removes itself on the same sunset predicate shape (three consecutive monthly reviews with no review decision, optimization or removal or demotion, citing the invocation-costs.jsonl readout; the 90-day idle-data review; the machinery registry's removals row carries it).

Script invocation and reading order: run `python3 scripts/friction_audit_quant.py --db <db> --logs-dir <logs dir> --out-dir <audit dir> --cadence-days "${FRICTION_AUDIT_CADENCE_DAYS:-7}"` (the cadence variable carries the `friction_audit_cadence_days` facts key with the 7-day fallback inlined, so a non-default value reaches the script and an unset environment still yields the canonical cadence; tilde-form documented defaults; never write a resolved absolute path into a committed file), then read `digest.md` first and `counts.json` for exact figures; the model pass samples raw rows, log lines, or transcripts only where the digest shows an anomaly, never as a full re-scan. The qualitative pass stays inside the audit lane's caps (at most 2 sub-agents, the recorded token budget, idle/off-peak preferred).

## Data map

Store locator (pinned): the session store is the SQLite database `~/.zcode/cli/db/db.sqlite` (the same locator the Context measurement primitive pins, with its `-wal`/`-shm` siblings), opened read-only; the audit never writes the store.
Table shapes: `session` carries one row per session keyed by `id` with `time_created` (epoch milliseconds); `tool_usage` carries one row per tool call keyed by `id` with `session_id`, `tool_name`, `status`, `started_at` (epoch milliseconds), `completed_at`, `duration_ms`, `retry_count`, `retryable`, `cancelled_by_user`, `error_type`, `error_code`, and `error_message`; `session_input` carries one row per typed prompt keyed by `id` with `session_id`, `kind`, `payload`, and `time_created` (epoch milliseconds); `message` carries the persisted transcript events keyed by `session_id` with payload in `data`, ordered by `sequence` (the Context measurement primitive's shape).
Log location and event schema: the app logs are per-day JSONL files named `zcode-YYYY-MM-DD.jsonl` under `~/.zcode/cli/log/`; each line is one JSON object carrying `timestamp`, `level`, `event`, `module`, and `message` (the Store-level darkness-triage witness above reads the same files). Logs are per-day files, so deltas are whole files: a day counts as processed only when its file has been mined to the end.
Persistence-noise filter: the per-day event histograms exclude persistence and compaction bookkeeping events whose `event` value carries the `session.event.persistence.` or `session.event.compaction.` prefix (observed: `session.event.persistence.started` and `session.event.persistence.completed`, together roughly 28 percent of a day's lines); the pattern list is owned by the quant script's `NOISE_PATTERNS` module constant, so this prose and the code cannot drift.
Provider code meanings: in `tool_usage.error_code` and in surfaced stop lines, `1302` is the per-request 429 rate limit (retryable; the axis the provider-429-retry-storm-shaping work owns) and `1308` is 5-hour usage-quota exhaustion (the axis the Quota leg already shapes); both are counted per code and never conflated.
Watermark rules: the audit state file `state.json` under the runtime's `friction_audit_dir` records per-source watermarks: `tool_usage`'s max `started_at` included in aggregates, `session_input`'s max `time_created` scanned, and the last daily log file fully mined (only complete UTC days advance the log watermark; the current day's partially grown file is re-mined in full on the next run, so its later appended tail is picked up). Watermarks advance only after a source is fully processed; a missing state file means cold start (the full corpus, the same semantics as the other maintenance state files).
`next_due` write rule: the quant script stamps `next_due` in `state.json` at each processing completion as the completion time plus the cadence (the `--cadence-days` argument; default 7, the `friction_audit_cadence_days` facts key). The scheduler turn's survey consult reads that value; nothing recomputes it mid-interval.

## Filing rule

Dedupe-and-fold: evidence on existing items becomes a dated evidence line, new items only after checking open plus completed plus deferred, composed per receiving-review's Backlog capture required content with its `Origin class:` line set per that rule (an audit-lane filing is self-serving unless the witnessed defect was seen in a consumer project).

## Guard liveness read-side

After the quantitative pass and before filing findings, run `python3 scripts/gate_liveness_ledger.py show` (repo-local copy first, then the deployed home copy), read the per-guard tallies from its output, and read the ledger's `window.started` field and close-date presence from the ledger JSON: every guard with zero `catch` rows across the observation window is a removal-or-narrow candidate, named in this run's report with its guard name, its incident count, and the window start date. While the observation window is open (the ledger's `window` object records no `closed` date), candidates are report-only; when the observation window closes (the operator records a `closed` date in the ledger's `window` object), each zero-catch-row candidate is filed per the Filing rule as a removal-or-narrow backlog item carrying the section 64 adjudication (the fewer-moving-artifacts ranking against the guard's witnessed harm class, with the honest-concurrency, fail-closed, and accidental-damage carve-outs checked before any retirement proposal). The read side never writes to the ledger; a ledger that cannot be read is reported as this run's tool evidence and never fabricated.

## Caps

Hard caps: at most 2 sub-agents and a total token budget recorded in the audit state; idle/off-peak preferred.

## State advance

State advance: stamp `next_due` at completion plus the task's `cadence_days` through the record's existing atomic-replace rules (temp file plus atomic replace), set `last_run_at` and a one-line `last_result`, and reset `consecutive_failures` to 0. On failure the body writes `last_result` and increments `consecutive_failures` while the consult owns the one-day `next_due` failure advance.
