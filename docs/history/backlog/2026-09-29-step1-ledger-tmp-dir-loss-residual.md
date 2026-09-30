# Backlog: Step 1 ledger recipe TMP_DIR-loss redirect failure residual
Status: covered (docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md)

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md
Cluster: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md
Cluster: docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md
Cluster: docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md
Cluster: docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md
Cluster: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md
Cluster: docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md


Driving force: reliability

p79 r2 finding N2 (docs/reviews/2026-09-29-p79-code-review-r2-verification.md): in the done Step 1 recipe, if TMP_DIR is lost `LEDGER` misassigns to `/done-session/...` (bash 3.2 `set -u` does not flag the empty `${TMP_DIR%/}` expansion) and the run fails loudly at the ledger redirect after the commit already landed - the commit exists but its ownership witness append fails. The recovery disposition covers remediation (append the sha by hand), but a TMP_DIR presence guard before the recipe would remove the sharp edge.
