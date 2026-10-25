# state-file children schema reconciliation (outcome enum, worktree-field writer enumeration)

Added: 2026-10-25, the child-outcome-evidence-resolution ad-hoc landing's deferred review finding (r1 F1, watchlist).

Cluster: docs/history/backlog/2026-10-24-maintenance-state-notes-schema-contract.md (same surface and defect class: the canonical state-file.md schema declarations lagging the live contract; that row owns the omitted `notes` field, this row the outcome enum and the worktree-field writer enumeration)

## Finding

agents/skills/maintenance/state-file.md lags the values and writers the landed failure-cap text references, in two places:

1. The children[] schema declares `"outcome": "pending|progress|failed"` (state-file.md, the schema line) while the widened early outcome checks (agents/skills/maintenance/failure-cap.md, landed def5dce98) evaluate `pending` or `in_progress`, and observed entries carry `in_progress` (witnessed 2026-10-23: the docs-branch-witness author entry sat at `in_progress` for about two days; origin row docs/history/backlog/2026-10-25-child-outcome-check-evidence-resolution-gaps.md lines 18-19, deleted by its covering landing).
2. The `worktree` field paragraph names the dispatched execution child as the field's writer, while the landed resolver arm adds a second writer: the child-outcome check's first-observation backfill of a claim-derived worktree path onto a null `worktree` field (failure-cap.md, the rate-limited ingestion bullet's resolution order).

## Suggested fix

Two-line state-file.md reconciliation: the schema enum gains `in_progress`; the `worktree` field paragraph's writer sentence names the check-side backfill beside the child-side recording. Both are prose edits to one pinned module; run the pins suite (pre-existing authoring stand-down gate span red expected at HEAD) and the em-dash added-lines gate.

## Witness

Landing def5dce98 (failure-cap arms) and its review record .ai-playbook/reviews/2026-10-25-child-outcome-evidence-resolution-code-review-r1.md (F1, Low, deferred).
