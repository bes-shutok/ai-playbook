# Backlog: drain r2 residual - stale-row-partial-drain-note
Cluster: docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md; docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md; docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md; docs/history/backlog/2026-11-02-drain-r2-legacy-manifest-name-blindspot.md; docs/history/backlog/2026-11-02-drain-r2-marker-grammar-third-copy.md; docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md; docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md; docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md; docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md; docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md (same-day review family)

Status: open
Priority: Low (non-blocking r2 residual; lands as a follow-up tidy)
Severity: Low
Origin: code review r2 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (premortem#stale-row-direction-misses-partial-drain).
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-legacy-manifest-name-blindspot.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-marker-grammar-third-copy.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md

## Direction

The stale-snapshot row's remediation names session_remains_terminal_discardable but the partial member drain unlinks with no freshness recheck. When closing docs/history/backlog/2026-11-02-docs-tmp-drain-stale-registration-snapshot.md, extend the freshness term (or an explicit revalidate) to the partial member loop, not just the full drain.
