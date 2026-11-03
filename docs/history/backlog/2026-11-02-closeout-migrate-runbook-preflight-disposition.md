## closeout-migrate-runbook-preflight-disposition

Added: 2026-11-02, doing-code-review r3 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F7, documentation#missing-closeout-runbook-preflight-disposition)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md)

Status: open, Priority: medium, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-finally-guard-exception-containment.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-ambient-git-env-filter.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-guard-failure-manifest-trace.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-nested-repo-toplevel-boundary.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-direction-overbreadth.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-preflight-git-probe-n-plus-one.md
- **Cluster:** docs/history/backlog/2026-11-02-closeout-migrate-prelock-head-window.md

The closeout runbook paragraph (agents/skills/execute-plan/worktree-first.md:79, the Transfer-out-and-deletion implementation) documents the migrate lock, the removal gate, and the baseline/skip rules, but not this landing's primary operator-visible behavior: the exit-2 baseline clobber pre-flight refusal (its named paths and its narrow-dirs-and-recapture remedy, documented only in the refusal's own stderr text) or the prevented_clobbers manifest section.

Scope arm: add the exit-2 disposition (narrow the capture dirs to untracked session surfaces and re-capture, with the why) and the prevented_clobbers section to the paragraph.
