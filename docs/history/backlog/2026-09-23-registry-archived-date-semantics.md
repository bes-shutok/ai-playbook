# Registry archived-date semantics: execution date vs authoring date

Driving force: code-review r1 F2 of docs/plans/2026-09-22-execute-plan-driver-batch-3.md (docs/reviews/2026-09-23-code-review-execute-plan-driver-batch-3-r1.md).

- **Observed**: three completed rows added 2026-09-23 for the 2026-09-18 backlog origins carry `archived = 2026-09-22` because the implementing plan's Task 2 prescribed "date 2026-09-22" verbatim; the nearest precedent row (tool-script-runtime-statistics) uses the actual archive date. The column header comment says "archived date from the filename date prefix" but no row follows it.
- **Expected**: one unambiguous semantics for the registry completed-row date column, followed by all rows.

## Direction

Pick one semantics (actual archive/move date recommended, matching the newest precedent) and normalize the completed rows' date column to it; amend the column header comment to state the chosen semantics; fold plan templates that prescribe a literal date to instead say "actual archive date".

## Evidence

- docs/maintenance/document-registry.md rows for the three 2026-09-18 slugs (date column 2026-09-22, moves executed 2026-09-23).

Status: open
