## closeout-migrate-guard-failure-manifest-trace

Added: 2026-11-02, doing-code-review r1 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F9, security#guard-failure-warn-only-no-manifest-trace); amended 2026-11-02 per the r3 panel (F11 adds the pre-flight's silent probe-failure arm)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: covered-pending-execution (docs/history/plans/2026-11-05-closeout-migrate-supplemental-inventory-and-guard-residuals.md), Priority: low, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r1.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-runbook-preflight-disposition.md

Three guard failure paths print to stderr and otherwise vanish: the post-run guard's unreadable staged set and failed restore print a WARN (the run exits 0 and prevented_clobbers cannot distinguish no-rewind from rewind-found-but-undone), and the pre-flight's failed HEAD probe returns None - indistinguishable from absent-at-HEAD - so the path silently exits the offender scan exactly when git is unhappy.

Scope arm: record failures durably in a prevented_clobber_failures manifest section (destination, action, error) so the closeout reader adjudicates without stderr, and distinguish probe rc!=0 from empty output in the pre-flight (WARN or refuse); pin all three failure shapes.
