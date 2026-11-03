# Backlog: drain r2 residual - marker-grammar-third-copy
Cluster: docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md; docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md; docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md; docs/history/backlog/2026-11-02-drain-r2-legacy-manifest-name-blindspot.md; docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md; docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md; docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md; docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md; docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md; docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md (same-day review family)

Status: open
Priority: Low (non-blocking r2 residual; lands as a follow-up tidy)
Severity: Low
Origin: code review r2 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (architecture#marker-grammar-copy-remains + simplification#field-count-rederivation).
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-legacy-manifest-name-blindspot.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md

## Direction

_marker_records_other_repo_content (scripts/done_sweep_gates_lib.py:746, pre-existing) still carries a full hand-rolled structural parse beside _marker_struct; the strict parser also re-tokenizes content to recover the field count. Rewrite the helper over _marker_struct and let the struct expose the digest-token shape.
