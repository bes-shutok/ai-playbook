## closeout-migrate-guard-ambient-git-env-filter

Added: 2026-11-02, doing-code-review r2/r3 panels over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (r2 finding F7; r3 finding F3, two-worker dedup group lead)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: open, Priority: medium, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-runbook-preflight-disposition.md

Every guard git subprocess (the three blob probes, the staged-set read, the `:rel` probes, both restores, and `_target_is_git_repository`) inherits the caller's ambient GIT_* environment: GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE redirect the probes and the index-mutating restore to another repository or scratch index while the run reports success for the intended target, and a non-repository target can classify as a repository and arm both guards. The suite strips inherited GIT_* for exactly this hazard; the r1 receipt's "in-process GIT_* env strip" claim landed test-side only.

Scope arm: one sanitize helper dropping the redirection keys (GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, GIT_OBJECT_DIRECTORY, GIT_ALTERNATE_OBJECT_DIRECTORIES, GIT_COMMON_DIR, GIT_CEILING_DIRECTORIES) passed to every guard subprocess; pin with a bogus-GIT_DIR fixture asserting inert or fail-closed.
