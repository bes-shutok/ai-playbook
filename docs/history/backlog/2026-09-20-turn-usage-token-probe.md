# Backlog: probe turn_usage as a runtime-reported context-size source for the measurement primitive

Status: open
Workflow: backlog
Source: Task 5 Step 1.2b intermediate review of docs/plans/2026-09-19-context-budget-and-telemetry-long-running-skills.md (contract-docs lens, 2026-09-20; triaged valid off-plan candidate, deferred per the backlog-deferral default — the plan bullet explicitly permits the char-count-proxy path, so the landed section is plan-conformant and the refinement is not a review fix).
Severity: Low
Exact location: agents/skills/maintenance/zcode.md `## Context measurement primitive` (stats-surface claim, proxy locator, and Proxy-ratio rationale, lines ~55-57); if adopted, also execute-plan's `Context budget checkpoints` measurement sentence.
Why not fixed now: adopting a runtime-reported token source requires its own live verification round (whether `turn_usage.input_tokens` or `computed_total_tokens` tracks context size, and how the cache-creation/cache-read columns behave) before any text changes — not doable inside a review fix.
Driving force: efficiency

## Problem

The new measurement primitive pins the chars/4 estimate while runtime-reported per-turn token counts exist in `turn_usage` (columns `input_tokens`, `output_tokens`, `computed_total_tokens`, keyed by `session_id`, plus cache-creation/cache-read columns) in the very store the section pins (`~/.zcode/cli/db/db.sqlite`; verified via `PRAGMA table_info`, read-only, 2026-09-20). Every checkpoint of every execute-plan run, review-loop round, and plans-authoring child on this host therefore carries avoidable estimation error, and the Proxy-ratio bullet's rationale ("so the corpus never mistakes proxy counts for runtime-reported token stats") reads as though runtime-reported token stats do not exist on this host — at the same locator they do. Reachability: every checkpoint. The proxy pinned the first workable table (`message`) one table away from a better source (`turn_usage`). The construct-level defect behind the ratio question was measured in the Phase 3 r1 code review: the message-table sum is cumulative persisted history (append-only, rows survive compaction), so it cannot observe shedding or compaction even at perfect ratio accuracy — adopting a runtime-reported source is the actual fix, not a ratio refinement.

Fix path: run a live verification round comparing `turn_usage` per-session sums against the known quota-window usage totals (scripts/review_usage_capture.py already reads this DB; the quota probe itself reads the Z.ai monitor endpoint, not the DB); if a column tracks context size, change the measurement primitive to read runtime-reported tokens first, keeping the char-count proxy as the `est_`-labeled fallback (and update the ratio rationale wording), then re-run the affected gates.
