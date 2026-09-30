# Backlog: p79 validation gates tolerate silent revert of r1-fix behaviors
Status: covered (docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md)

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md
Cluster: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md
Cluster: docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md
Cluster: docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md
Cluster: docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md
Cluster: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md
Cluster: docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md


Driving force: code-quality

p79 r2 finding N3 (docs/reviews/2026-09-29-p79-code-review-r2-verification.md): the plan's Validation Commands pins are green with live content today, but no gate pins the r1-fix behaviors (schema bool/float rejection, roundtrip rendering sanitization, ledger guard placement, receipt scoping, emit echo-capture guidance, `_repo_root_matches_value` sharing) - a silent revert of any of them passes all gates. G8+G9 also tolerate stubbed test bodies. Candidate remedy: extend the selftest suite with assertions over the fix behaviors (suite-level pins are stronger than grep pins for behavior).
