# Backlog: rolling-log entries cite deleted origin rows; receipts never re-verify origin existence

- **Filed:** 2026-11-10, learn Step 1.9 capture from the 24h session-pattern harvest (playbook repo)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** record-hygiene defect
- **Class:** fix-class
- **Skill/step:** `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md` (Standing rules block: entry emission and prune-receipt edits)
- **Source reference:** verified against the 2026-11-10 corpus census: the frozen codex-quota-reset-wake PLAN entry cites two origin paths absent from disk (`2026-10-31-maintenance-autopilot-codex-same-session-compaction`, `2026-10-31-maintenance-cycle-gate-scenario-test`; both confirmed absent 2026-11-10); the ready codex-quota-wake-cross-thread-duplicate-target entry lists its single origin bullet twice
- **Why not fixed now:** harvest-only session; the tidy is bounded and ad-hoc-able
- **Dedup probe:** the `plan-prompts-wrong-location-disposition-marker` row owns wrong-location markers (a different defect); the `hygiene-scanner-accepted-residuals-durable-home` EXEC entry cites a deleted row but carries a sanctioned in-entry recovery recipe (different case); no merge

## Problem

Prune and freeze receipt edits move or delete origin rows without re-verifying the citations left behind. Frozen entries lose their provenance chain (dangling paths), and ready entries carry duplicate pointers, so the dispatch census and later archaeology read stale lineage.

## Expected

An ad-hoc tidy fixes the two named instances (re-point the dangling citations at the covering plans' completed twins, dedupe the duplicated bullet), and the Standing rules gain one line: a receipt edit that moves or deletes an origin path re-verifies every Origins line in the touched entry with an existence probe per path.

## Suggested fix

Ad-hoc-able: bounded edits to the two entries plus the one Standing-rules line, committed in the same turn per the logs' Write boundary rule.
