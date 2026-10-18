# Backlog: consolidate archive index reads

- **Filed:** 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** fresh code review finding
- **Class:** maintainability
- **Driving force:** simplicity
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, `_archive_text_at_index_or_worktree`
- **Cluster:** docs/history/backlog/2026-10-10-deduplicate-committed-archive-charters.md

- **Cluster:** docs/history/backlog/2026-10-10-extract-archive-evidence-assembly.md (backlog-wide survey: done archive evidence assembly)
## Problem

The indexed-mode validation and blob-read sequence is duplicated for the initial lookup and the post-worktree-read race check. Future changes to regular-file validation or error handling could diverge between the two paths.

## Expected

Extract a focused helper for indexed regular-file reads and preserve the distinct diagnostics for the initial lookup and post-read race.

## Workaround

The duplicate paths currently enforce the same regular-mode and blob-read rules. Keep both regression paths covered until the helper extraction is implemented.

## Source

- 2026-10-10 fresh execute-plan Phase 3 design review, finding `simplification#shrink`.
