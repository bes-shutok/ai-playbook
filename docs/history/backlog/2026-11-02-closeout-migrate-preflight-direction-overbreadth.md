## closeout-migrate-preflight-direction-overbreadth

Added: 2026-11-02, doing-code-review r1 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F2, implementation#preflight-refusal-overbreadth)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md), docs/history/backlog/2026-10-31-closeout-zero-delta-report-arm-coverage.md

Status: open, Priority: medium, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r1.md

The pre-flight refusal is direction-blind: any would-carry path tracked at the target HEAD whose source bytes differ refuses, forward or backward, before the mirror-receipt machinery runs, so a receipt-proven replacement or a forward carry of the run's own edits to a tracked surface exits 2; the priced re-capture remedy then re-freezes the source bytes and the retry silently carries nothing.

Scope arm: make the refusal direction-aware with the post-run guard's own vintage probe (refuse only when the source bytes hash to an older committed vintage of the HEAD blob), letting forward carries fall through to the existing collision and receipt dispositions; pin both directions.
