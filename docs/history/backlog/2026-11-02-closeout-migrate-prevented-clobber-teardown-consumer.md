## closeout-migrate-prevented-clobber-teardown-consumer

Added: 2026-11-02, doing-code-review r3 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F5)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md), docs/history/backlog/2026-11-02-closeout-migrate-deletion-arm-recheck-parity.md, docs/history/backlog/2026-11-02-closeout-migrate-owned-vintage-restore-signature.md, docs/history/backlog/2026-11-02-closeout-migrate-foreign-staged-report-coverage.md

Status: covered (docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md)

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md

The prevented_clobbers manifest section has no downstream consumer: the removal gate's presence check walks migrated/renamed only, so a prevented clobber - evidence a between-snapshot rewind actually happened in the run's window - cannot influence the teardown decision it exists to protect, and the source worktree is deleted exactly like a clean run.

Scope arm: gate-removal (or the closeout reader) holds or refuses teardown when prevented_clobbers is non-empty, report-only naming the restored paths, the operator deciding; pin with a manifest carrying a prevented entry.
