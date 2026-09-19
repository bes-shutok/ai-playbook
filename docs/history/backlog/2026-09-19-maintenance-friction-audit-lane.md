# Backlog: recurring cross-session friction audit lane in the maintenance loop

Captured: 2026-09-19 (user direction: make the one-off friction audit a standing maintenance-lane step between authoring and execution; keep scan-range records in `.ai-playbook/`)
Status: open
Priority: medium (user direction 2026-09-19)

Workflow: backlog

## What was witnessed

The 2026-09-19 one-off audit (5,434 sessions, 117k tool_usage rows, 1,776 typed prompts, 7 days of app logs) produced 10 backlog items (commit 64c74d2d) and proved the mining recipe works. But it was entirely manual: nothing schedules a re-run, nothing remembers which data ranges were already scanned, and a naive re-run re-spends heavy tokens (each mining sub-agent burned 700k-950k tokens; one died to a `[1302]` rate limit). Meanwhile the corrections-mining pass showed the correction rate stayed flat across three months precisely because friction fixes land as one-off snapshots. Without watermarks plus a cadence, the audit decays into exactly that.

## Suggested fix

Make the audit a bounded, watermark-driven lane of the maintenance skill, feeding the existing pipeline: audit findings -> backlog items -> authoring -> execution.

1. **Audit lane and cadence.** The scheduler turn consults the audit state file's `next_due` during the survey; when due (suggested: every 7 days) and lanes allow, it dispatches one audit child with the same dispatch discipline as authoring (claim check before dispatch, at most one audit child, `children[]` entry in the scheduler state file, park/retain on quota pressure). Idle/off-peak lane preferred: the audit is deferrable and token-heavy.

2. **Watermark state in `.ai-playbook/`** (runtime-local and gitignored, same as `facts.md` - verified line 9 of `.gitignore`). Suggested: a new facts key `friction_audit_dir` owned by `bootstrap-ai-playbook` (same resolution pattern as `tmp_dir`), with `state.json` plus per-run digests inside. Per-source watermarks, advanced only after a source is fully processed:
   - db sessions: max `time_created` scanned, plus row count for drift detection;
   - tool_usage: max `started_at` included in aggregates;
   - app logs: last daily log file fully mined (logs are per-day files, so deltas are whole files);
   - typed prompts: max `time_created` in `session_input`;
   - transcripts: newest sampled `sess_*` mtime (always bounded sampling, never full-corpus);
   - run bookkeeping: findings, items created/updated, tokens burned, next_due.
   Missing state file means cold start: full-corpus audit, same semantics as other maintenance state files.

3. **Deterministic quantitative pass as a script** (scripts-over-prose preference). A small script (sqlite3/python, repo scripts convention) recomputes what the 2026-09-19 audit did by hand: error rates and error-message classes per tool, retry/cancellation counts, duration percentiles, per-day log event histograms (filtering `session.event.persistence.*` noise first, ~28 percent of lines), 429 `[1302]`/`[1308]` counts, and correction-heuristic candidates from `session_input`. It writes a digest (markdown + machine-readable counts) under the audit dir; the model pass reads only the digest plus targeted samples.

4. **Qualitative pass, bounded.** Read correction-flavored prompts since the watermark (keyword heuristics from the 2026-09-19 pass), sample logs/transcripts only where the quantitative pass shows anomalies. Hard caps: e.g. at most 2 sub-agents and a total token budget recorded in the state file, run off-peak - the audit must not become the new bottleneck it measures.

5. **Dedupe and fold discipline.** Before creating items, check the open backlog plus `completed/` and `deferred/` (the 2026-09-19 pass avoided duplicates this way). Growing evidence on existing items becomes a dated evidence line on that item, not a new item; sub-noise findings stay in the digest only.

6. **Registration.** Maintenance `SKILL.md` gains the audit-lane paragraph in the survey/lane section; the runtime overlay gains the recipe (db path and table shapes, log location and event schema, the persistence-noise filter, provider code meanings, watermark rules). The recipe must live in the skill layer, not in agent memory: memory is machine-local and does not survive to fresh environments.

7. **Safety rails.** The audit child inherits standing pre-authorization; on quota pressure it parks like `pending_dispatch`; its own rate-limit deaths are caught by the next turn's darkness/park-guard semantics.

## Acceptance

- The state file records per-source watermarks; a second run processes only the delta and finishes at a small fraction of cold-start cost.
- A scheduled audit child creates or updates backlog items only for genuinely new friction (dedupe pass evidenced) and leaves a digest under the audit dir.
- The skill and overlay document the lane, cadence, and recipe; no audit logic lives only in agent memory.
- Token burn per run is capped and recorded in the state file.
