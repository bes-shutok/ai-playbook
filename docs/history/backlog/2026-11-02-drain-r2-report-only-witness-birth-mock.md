# Backlog: drain r2 residual - report-only-witness-birth-mock
Cluster: docs/history/backlog/2026-11-02-drain-r2-dead-code-tidy.md; docs/history/backlog/2026-11-02-drain-r2-dead-root-recheck-root-field.md; docs/history/backlog/2026-11-02-drain-r2-docs-branch-query-duplication.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-manifest-read.md; docs/history/backlog/2026-11-02-drain-r2-duplicate-primary-resolution.md; docs/history/backlog/2026-11-02-drain-r2-legacy-manifest-name-blindspot.md; docs/history/backlog/2026-11-02-drain-r2-marker-grammar-third-copy.md; docs/history/backlog/2026-11-02-drain-r2-off-posture-undocumented.md; docs/history/backlog/2026-11-02-drain-r2-partial-drain-reporting-gap.md; docs/history/backlog/2026-11-02-drain-r2-partial-row-arm-token.md; docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md; docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md (same-day review family)

Status: open
Priority: Medium (non-blocking r2 residual; lands as a follow-up tidy)
Severity: Low
Origin: code review r2 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (testing#platform-dependent-fixture).
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
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-stale-row-partial-drain-note.md
- **Cluster:** docs/history/backlog/2026-11-02-drain-r2-window-overclaim-arm3.md

## Direction

The report-only never-synced witness test (test_docs_tmp_never_synced_report_only_would_drain) omits the _entry_birth_epoch monkeypatch its siblings carry, passing on darwin only because os.utime clamps st_birthtime; on Linux the arm keeps fail-closed and the test fails. Add the same one-line monkeypatch the on-posture witness at scripts/test_done_sweep_gates_lib.py:17952 carries.
