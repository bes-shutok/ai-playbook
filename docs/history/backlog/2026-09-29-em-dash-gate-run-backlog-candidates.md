# Backlog: em-dash gate mode-selection run deferred review candidates
Status: covered (docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md)

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md
Cluster: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md
Cluster: docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md
Cluster: docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md
Cluster: docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md
Cluster: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md
Cluster: docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md


Driving force: reliability + robustness

Two backlogged candidates accepted during the execute-plan run of docs/history/plans/2026-09-28-em-dash-whole-file-gate-added-lines-selection.md (branch 2026-09-29-em-dash-gate-mode-selection, intermediate reviews r1 of Tasks 1 and 2):

1. `gate_em_dash_scan` ls-files failure polarity (Task 2 r1): when `git ls-files --others --exclude-standard` fails, the partition treats every hit as tracked, and an added-lines probe on an untracked path scans no diff lines and returns clean, so the hit would be misreported as pre-existing. Fail-closed variant: treat an ls-files failure as "everything untracked" (all hits fail with the untracked marker). Practically unreachable today (the touched probe already ran against the same repo) but a cheap hardening.

2. Plan-prose count drift (Task 1 r1): the plan's verbatim Task 1 commit message says "six appositive em dashes" but the branch carried only two (four were already colonized on main between authoring main 07885e0f and execution main 1966beac); the commit used corrected wording. Future plans quoting exact counts against a moving main should prefer "all remaining" phrasing or re-derive counts at execution time.

Whole-plan review r1 (docs/reviews/2026-09-29-code-review-em-dash-whole-file-gate-added-lines-selection-r1.md) added two LOW candidates:

3. The anti-mutation >10-hits property (fallback must partition the probe's complete stdout, not the last-10 tail) has no standing canary; r1 proved it only with an ephemeral fixture. A fifth canary would make the property standing.

4. Refined item 1: when `git ls-files --others` fails, the per-path added-lines probe still exits 2 on untracked pathspecs ("pathspec matches no tracked file"), so the hit fails rc 1 regardless; residual harm is only a mislabeled reason marker. Fail-closed either way; hardening is cosmetic.
