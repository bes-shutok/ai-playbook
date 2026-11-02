# Backlog: drain r2 residual - duplicate-primary-resolution
Cluster: docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md; docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md; docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md; docs/history/backlog/2026-11-02-drain-r2-legacy-manifest-name-blindspot.md; docs/history/backlog/2026-11-02-drain-r2-marker-grammar-third-copy.md; docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md; docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md; docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md; docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md; docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md; docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md (same-day review family)

Status: open
Priority: Low (non-blocking r2 residual; lands as a follow-up tidy)
Severity: Low
Origin: code review r2 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (architecture#duplicate-primary-resolution).

## Direction

_sweep_execute_plan_sessions resolves the primary checkout back-to-back with _snapshot_candidate_checkout_roots, which already resolves it internally. Return the resolved primary alongside the snapshot triple and drop the second call.
