# The memory index has a load budget but no retirement pass: fired carrier records accumulate and their pre-fire phrasing goes stale

- **Filed:** 2026-11-08, learn Step 1.9 capture (24h session-pattern harvest REM run)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (chronic index truncation at load, no writer blocked; stale do-NOT-redo markers cost redundant caution only)
- **Cluster:** docs/history/backlog/2026-11-05-memory-index-lane-charter-review-residue.md (same surface family; that row owns the charter file's paperkeeping residue list, this row owns the index content lifecycle)
- **Origin class:** self-serving
- **Class:** fix-class
- **Surface:** the maintenance-side memory-write convention (the repository AGENTS.md section) and the memory-index-audit lane file (`docs/maintenance/recurring-tasks/memory-index-audit.md`)
- **Source reference:** the index measured 763 lines and about 192 KB at 2026-11-08 02:00 WET with the load warning truncating at 674 lines; the executed consolidation (`docs/history/plans/completed/2026-11-02-memory-index-load-budget-consolidation.md`, landing 0a3fa6aa1, 2026-11-05) set the load budget and landed no recurring retirement arm, and roughly 25 to 30 records append per day; stale-record witness: the 22:30 WET twin carriers' index lines still read "scheduled not executed" after both runs dispatched and failed at 2026-11-07 22:30 (automation_runs: outcome failed, attempts 0, empty error)
- **Dedup probe:** searched open backlog rows for memory-index retirement and GC arms; only the charter-residue sibling and the write-convention copy-drift row exist; neither owns index-content retirement or fired-record refresh
- **Why not fixed now:** the retirement threshold and fold shape are open design choices that interact with the convention's sanctioned-edit vocabulary; they belong to an authoring lane

## Problem

The append-first one-line convention keeps the index growing monotonically while completed-run and fired-carrier records never retire: a fired one-shot carrier's record has no further recall value after its do-NOT-redo window, yet its line stays forever. The load-budget consolidation set a byte budget and an audit lane, but the audit only measures; nothing removes. Within three days of the consolidation landing, the index is back over its budget and truncates at load, which means older records (including live paused-run and pending-rearm markers near the file's tail under the newest-first ordering) fall out of the loaded context. Separately, a scheduled carrier's record reads "scheduled not executed" until someone edits it, and no duty refreshes it at fire time, so the witnessed twin carriers' lines now misstate their runs.

## Expected

A recurring retirement pass folds completed-run and fired-carrier records older than a threshold into their topic files (the do-NOT-redo semantics ride the topic file) and drops their index lines through the convention's sanctioned targeted edits. A fired carrier's own run refreshes its record's outcome line at fire time, so a pre-fire "scheduled not executed" line never survives a dispatch.

## Suggested fix

Define the retirement threshold and the per-record fold inside the write convention's existing vocabulary (index line dropped, topic file keeps the semantics), bind the fire-time record refresh to the fire path's existing outcome recording, and keep the append-first convention and the load budget unchanged. Re-derive the current index size at authoring time.
