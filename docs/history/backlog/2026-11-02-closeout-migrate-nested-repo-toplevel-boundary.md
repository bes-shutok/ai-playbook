## closeout-migrate-nested-repo-toplevel-boundary

Added: 2026-11-02, doing-code-review r2 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F4, architecture#unenforced-toplevel-boundary)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: open, Priority: medium, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-runbook-preflight-disposition.md

Both guards silently degrade on a `--target` nested inside a repository: the probes and the merge lock resolve through the enclosing worktree, so the guards read and restore against the wrong index boundary while reporting target-relative success.

Scope arm: refuse (or explicitly scope) a target whose `rev-parse --show-toplevel` does not equal the resolved target path; pin with a nested-target fixture.
