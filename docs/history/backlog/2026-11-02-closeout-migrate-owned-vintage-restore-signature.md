## closeout-migrate-owned-vintage-restore-signature

Added: 2026-11-02, doing-code-review r2 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F6, security#owned-vintage-restore-conflates-reversal)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md), docs/history/backlog/2026-11-02-closeout-migrate-deletion-arm-recheck-parity.md, docs/history/backlog/2026-11-02-closeout-migrate-foreign-staged-report-coverage.md, docs/history/backlog/2026-11-02-closeout-migrate-prevented-clobber-teardown-consumer.md

Status: covered (docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md)

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md

The owned-vintage restore cannot distinguish the incident rewind (a peer's between-snapshot staged older vintage) from a deliberate staged reversal (the operator reverting a carried change): both present as an owned path staged at a historical vintage, and the guard restores from HEAD in both cases, undoing the operator's revert.

Scope arm: tighten the owned signature to the incident shape by comparing the staged blob against the digest the run actually delivered (record each carried rel's delivered digest in the manifest); note this flips the pre-staged-rewind fixture's expectation, so it is a semantic decision to take deliberately (r2's pricing).
