## closeout-migrate-finally-guard-exception-containment

Added: 2026-11-02, doing-code-review r2/r3 panels over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (r2 finding F2; r3 finding F4)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: covered (docs/history/plans/2026-11-05-closeout-migrate-supplemental-inventory-and-guard-residuals.md)

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-runbook-preflight-disposition.md

The transfer finally runs the post-run guard block (ownership normalization plus `_prevent_tracked_clobbers`' serial git spawns and full-history walks) before the manifest write with no exception containment: a SIGINT mid-walk (the migrate arm arms no signal bridge), a spawn OSError, or a decode error escapes the finally, so a fully-copied migration ends with no manifest, replacement priors neither restored nor discarded, and the interrupted-marker path never runs.

Scope arm: contain the guard block the way the manifest write already is - record the failure into the manifest (folding the guard-failure-manifest-trace row's failures section) and always proceed to the sections build and `_append_manifest`, running the priors restore-or-discard on the guard-crash path too; pin with a fault-injected guard spawn.
