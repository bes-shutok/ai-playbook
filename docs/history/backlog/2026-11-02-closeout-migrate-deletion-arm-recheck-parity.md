## closeout-migrate-deletion-arm-recheck-parity

Added: 2026-11-02, doing-code-review r2/r3 panels over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (r2 findings F5/F8/F14 + overflow unmerged; r3 findings F1/F2/F6, three-worker dedup group lead)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md), docs/history/backlog/2026-11-02-closeout-migrate-owned-vintage-restore-signature.md, docs/history/backlog/2026-11-02-closeout-migrate-foreign-staged-report-coverage.md, docs/history/backlog/2026-11-02-closeout-migrate-prevented-clobber-teardown-consumer.md

Status: covered (docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md)

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md

The restore arms race a peer restage: the owned-deletion arm restores from HEAD with no compare-then-act recheck (classification read at the `rev-parse :rel` probe, restore spawn one subprocess later), the vintage arm's recheck still leaves a recheck-to-restore span, and the downgrade witness is absent (deleting the recheck block keeps all ten pins green). An unmerged index entry (rev-parse exit 128 "not at stage 0") is classified as a staged deletion: on an owned path mid-conflict the guard's restore silently resolves the operator's merge to HEAD's side in index and worktree (live-probe verified at certification).

Scope arm: one shared reclassify-then-restore helper covering both arms (deletion recheck: still-absent means unchanged; post-restore re-read or index-lock across the span for the residual window); route non-stage-0 entries to the report-only foreign path via a stage-0 probe; pin the downgrade with a subprocess-run interception restaging after the classification read (recipe in the r3 record F6), plus an unmerged-entry pin.
