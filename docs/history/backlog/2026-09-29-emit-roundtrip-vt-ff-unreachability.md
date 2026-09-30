# Backlog: emit roundtrip guard VT/FF term unreachable via CLI enumeration
Status: covered (docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md)

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md
Cluster: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md
Cluster: docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md
Cluster: docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md
Cluster: docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md
Cluster: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md
Cluster: docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md


Driving force: code-quality

p79 r2 finding N1 (docs/reviews/2026-09-29-p79-code-review-r2-verification.md): the `[\v\f]\.md$` term in the emit-foreign-candidates roundtrip abort is CLI-unreachable - vertical-tab/form-feed/newline-named candidates under a gitignored reviews dir drop out at the frozen `ls-files` enumeration (git octal-escapes; `_ignored_paths` never unquotes). The guard term is predicate-level only; a pre-existing frozen-surface shape. Either unquote octal-escaped enumeration output before classification or drop the term and document the enumeration-side behavior.
