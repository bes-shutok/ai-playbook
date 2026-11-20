# Backlog: drain r2 residual - dead-code-tidy
Cluster: docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md; docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md; docs/history/backlog/2026-11-02-drain-r2-legacy-manifest-name-blindspot.md; docs/history/backlog/2026-11-02-drain-r2-marker-grammar-third-copy.md; docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md; docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md; docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md; docs/history/backlog/2026-11-02-drain-r2-report-only-witness-birth-mock.md; docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md; docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md (same-day review family)

Status: open
Priority: Low (non-blocking r2 residual; lands as a follow-up tidy)
Severity: Low
Origin: code review r2 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (quality#unreachable-guard-resurrected + quality#dead-store).
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
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md

## Direction

Two dead-code residues of the r1 fold: the unreachable tail of _proof_family_session_decision (registered_elsewhere is always False past the earlier keep, so the tail keep at ~4746 never runs) and the never-read root_changed = False declaration in _consume_never_synced (~3700). Delete both; zero behavior delta.
