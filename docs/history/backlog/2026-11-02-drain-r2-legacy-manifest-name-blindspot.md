# Backlog: drain r2 residual - legacy-manifest-name-blindspot
Cluster: docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md; docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md; docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md; docs/history/backlog/2026-11-02-drain-r2-marker-grammar-third-copy.md; docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md; docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md; docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md; docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md; docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md; docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md (same-day review family)

Status: open
Priority: Low (non-blocking r2 residual; lands as a follow-up tidy)
Severity: Low
Origin: code review r2 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (implementation#legacy-manifest-name-blindspot).
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-marker-grammar-third-copy.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md

## Direction

migration_branch_source() and the partial keep-set recognize only closeout-migration.json while the closeout consumer also probes the legacy migration-manifest.json twin, so a mixed-vintage session with a legacy-named manifest full-drains in on posture. Extract the branch through the consumer's two-name probe or name the canonical-only scope in the promotion census.
