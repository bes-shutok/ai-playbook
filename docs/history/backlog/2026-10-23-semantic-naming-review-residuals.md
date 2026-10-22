# Semantic-naming review residuals (byte-balance shave, dropped one-line carve-out)

Added: 2026-10-23, Phase 3 round 3 of docs/history/plans/2026-10-21-semantic-naming-and-analogous-class-review.md

Status: open
Priority: low
Cluster: docs/history/backlog/2026-10-23-quality-ownership-line-vs-naming-items.md (same surface: the quality catalog's naming checklist in agents/skills/review-agents/quality.md)

Driving force: code-quality. Two Low non-blocking residuals from the execution review, deliberately backlogged instead of fixed post-clean-round:

1. Byte-balance is near-zero but not net-zero (quality.md +22, review-panel-selection.md +66 against their base blobs); the Done-when clause is satisfied in spirit (>97 percent paid in-file, far under caps) but a strict net-zero reading wants a final ~90-byte shave in review-panel-selection.md.
2. The method-readability condensation dropped the carve-out sentence "Keep clear, pure one-line mappings and guards inline." (introduced 867f8ed7e, unpinned corpus-wide); the retained trigger predicates already exclude pure one-liners, so the flagging surface is unchanged, but the explicit false-positive guard is gone.

Fix shape: one small docs change restoring the carve-out sentence and shaving the residual bytes, with pin and frozen-span gates re-run.
