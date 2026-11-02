## closeout-migrate-prelock-head-window

Added: 2026-11-02, doing-code-review r1 panel over the closeout-migrate-baseline-tracked-clobber ad-hoc landing (finding F5, security#preflight-unlocked-head-window); amended 2026-11-02 per the r2/r3 panels (r2 F1 priced the window as including the bounded 300s lock wait and recommended promotion; r3's overflow adds the source-moving half)

Cluster: scripts/worktree_closeout_migrate.py (baseline clobber guards; family record: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md), docs/history/backlog/2026-11-02-landing-reconcile-phantom-recurrence.md

Status: open, Priority: high, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r1.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r2.md; .ai-playbook/reviews/2026-11-02-closeout-migrate-baseline-tracked-clobber-code-review-r3.md

The pre-flight reads HEAD and source bytes before the merge-lock span and the carry never re-reads HEAD, so a peer landing that commits inside the pre-lock window re-creates a tracked destination with newer bytes the copy then overwrites and the staged-set guard cannot see (no staged entry exists for a committed change); the overwritten bytes survive only in git history. The window spans the pre-flight probe fan-out plus the bounded merge-lock wait (300s default), and has a second half: a source file baseline-identical at pre-flight and edited during the same window is carried at new bytes with no HEAD re-comparison (r3 overflow premortem#preflight-source-drift-escapes-offender-set).

Scope arm: inside the lock span after acquire, re-run the offender comparison for the carried set (or compare the pre-flight HEAD capture against HEAD at acquire and re-scan on change), refusing exit 2 before the first copy - the in-lock re-scan closes both halves; pin the interleaving with a fixture commit between the probe points.
