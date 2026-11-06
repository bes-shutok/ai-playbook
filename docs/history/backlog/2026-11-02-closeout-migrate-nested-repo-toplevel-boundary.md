## closeout-migrate-nested-repo-toplevel-boundary

Added: 2026-11-02, doing-code-review r2 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F4, architecture#unenforced-toplevel-boundary)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: covered (docs/history/plans/2026-11-05-closeout-migrate-supplemental-inventory-and-guard-residuals.md)

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-runbook-preflight-disposition.md

Both guards silently degrade on a `--target` nested inside a repository: the probes and the merge lock resolve through the enclosing worktree, so the guards read and restore against the wrong index boundary while reporting target-relative success.

Scope arm: refuse a target whose `rev-parse --show-toplevel` does not equal the resolved target path; pin with a nested-target fixture. No-exit rationale (amended in place 2026-11-06, plan docs/history/plans/2026-11-05-closeout-migrate-supplemental-inventory-and-guard-residuals.md Task 4): the explicitly-scoping alternative this arm once allowed is refused as unsafe, not an exit - explicit scoping leaves the guards reading and restoring against the enclosing worktree's index while reporting target-relative success, and no scoping re-implements index isolation, so refusal is the only safe shape.
