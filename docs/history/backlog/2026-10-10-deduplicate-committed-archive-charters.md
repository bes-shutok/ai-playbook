# Backlog: deduplicate committed archive charter reports

- **Filed:** 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** fresh code review finding
- **Class:** correctness
- **Driving force:** accuracy
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, `_derive_archived_plans`
- **Cluster:** docs/history/backlog/2026-10-10-consolidate-archive-index-read.md
- **Cluster:** docs/history/backlog/2026-10-10-extract-archive-evidence-assembly.md (same archive derivation function; this row covers duplicate charter reporting, while the sibling covers evidence assembly and fail-closed source handling).

## Problem

When one commit adds multiple task files to an existing archived directory plan, committed-range discovery resolves each member to the same charter. The first member adds the charter to `seen`, but the later unconditional append can still add another copy to `archives`. Checkbox validation remains correct, but the ceremony report can overstate the number of distinct archives it checked.

## Expected

Append each directory charter at most once during committed-range discovery. Keep task evidence assembly and checkbox validation unchanged.

## Workaround

Treat duplicate archive-count text as a reporting-only issue; it does not bypass or weaken archive validation. Keep the full gate suite as the verification command when fixing the deduplication.

## Source

- 2026-10-10 fresh execute-plan Phase 3 correctness review, finding `quality#duplicate-archive-entry`.
