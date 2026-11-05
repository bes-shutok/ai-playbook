## closeout-migrate-preflight-git-probe-n-plus-one

Added: 2026-11-02, doing-code-review r1 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F4, quality#catalog-loop-n-plus-one); amended 2026-11-02 per the r2/r3 panels (r2's overflow security#guard-span-cost-lock-hold and r3 F8 add the postrun in-span surface; r3 F16 fixes the priority divergence from the r1 staged Medium)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: covered-pending-execution (docs/history/plans/2026-11-05-closeout-migrate-supplemental-inventory-and-guard-residuals.md), Priority: medium, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r1.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-runbook-preflight-disposition.md

The pre-flight spawns up to two git subprocesses per would-carry path (rev-parse HEAD:rel, hash-object), so a large late-run delta pays hundreds of serial spawns before the lock span; and the post-run guard repeats the shape inside the held merge-lock span - per staged entry differing from HEAD it spawns rev-parse plus a full-history `git log --find-object` walk (including for foreign brand-new staged files, a guaranteed miss), stretching the held span toward the 300s bounded wait other acquirers use. The same file already batches tree reads elsewhere (ls-tree, diff --cached -z).

Scope arm: pre-flight - read the HEAD tracked map once with git ls-tree -r -z and batch-hash the walk's files with git hash-object --stdin-paths, keeping the per-path decisions; postrun - batch the vintage probe over the blob set (one log --find-object pass per batch or a rev-list --objects prefilter) or move the guard outside the held span with its own short lock; pin the offender set is unchanged and the prevented set is unchanged.
