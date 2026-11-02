## closeout-migrate-foreign-staged-report-coverage

Added: 2026-11-02, doing-code-review r2/r3 panels over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (r2 finding F9; r3 finding F9)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md), docs/history/backlog/2026-11-02-closeout-migrate-deletion-arm-recheck-parity.md, docs/history/backlog/2026-11-02-closeout-migrate-owned-vintage-restore-signature.md, docs/history/backlog/2026-11-02-closeout-migrate-prevented-clobber-teardown-consumer.md

Status: covered (docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md)

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md

The foreign staged work report has holes against its own "reported, never touched" contract: a staged new file absent at HEAD skips before any ownership check with no output, and an owned path staged with brand-new bytes (neither HEAD nor a historical vintage) falls past the report branch silently - the two shapes the doc surfaces over-claim coverage for.

Scope arm: emit the prevented-clobber-check line for both silent branches (distinguishing staged-new-at-target from staged-new-bytes-on-a-carried-path) and align the three doc surfaces' claim; pin both shapes.
