# finalize deferred-squash honesty: test-coverage residuals from the 2026-10-26 landing panel

- **Status:** open
- **Workflow:** backlog
- **Priority:** high (re-affirmed 2026-10-26 by the item 5 witness: a false deferral fires on every rebased landing)
- **Skill/step:** `scripts/done_run.sh` finalize leg (deferred-squash honesty arms); `scripts/test_done_run_wrapper.py` DoneRunFinalizeTest
- **Class:** fix-class (item 5, a behavior defect) plus test-coverage residuals (items 1-4, watchlist of the ad-hoc landing panel, non-blocking)
- **Origin class:** panel watchlist capture
- **Driving force:** reliability

## Problem

The 2026-10-26 ad-hoc landing of the deferred-squash honesty arms folded its blocking-class finding (the resume-completion regression, r1 F1) and the child-corner deferral emission (r1 C1 code arm), but the panel's remaining test-coverage asks stayed open per the non-blocking watchlist policy. Four coverage gaps remain untested:

1. Fail-open arm: no test drives finalize with a ledger landing commit and an unresolvable base branch (no facts `base_branch`, no origin/HEAD) or an unreadable ledger tip, asserting the "honesty check is skipped" warning, the complete marking, and the `landing_commit=` summary.
2. origin/HEAD fallback: no test resolves the base through `refs/remotes/origin/HEAD` without the facts key (fixture pattern exists in `test_already_staged_branch_added_deletion_lands_end_to_end`).
3. Fresh-recompute naming and the child-corner deferral: no test combines the guard-firing child-commit path with a resolvable base on a run branch, asserting the summary's `branch_commit=` naming and the summary-block `LANDING DEFERRED` emission that fires when the ledger's first line postdates the marking decision.
4. Squash-proof bound: the 500-commit tree-scan window is untested at its boundary; a squash that falls out of the window classifies as pending on every re-run, and no test or warning documents the recovery.
5. Rebase-invalidated proof (witnessed 2026-10-26, a second ad-hoc exec session; behavior defect, not coverage): the squash proof keys on the ledger tip's tree, and the owned-commits ledger holds the shas `done_run.sh commit` recorded before any rebase. The base-freshness gate forces a rebase whenever peers land first (this landing rebased twice), the rebase rewrites every recorded commit and tree, and the squash that then lands carries the post-rebase tree; the scan finds the pre-rebase tree absent, prints `LANDING DEFERRED ... the branch tip is <pre-rebase sha>`, and withholds the manifest's complete marking although `git diff main <branch>` is empty and the `land-worktree` receipt names the new tip. The printed resume duty (re-run finalize) can never succeed on that ledger. Expected: the proof compares content, not identity (the branch delta's patch-id against each scanned commit's first-parent delta), or the rebase step rewrites the ledger lines with the post-rebase tips before finalize runs. Project lesson 256 is the corpus witness.

## Suggested fix

Fix item 5 first: switch the squash proof from tree identity to a patch-id comparison of the branch delta against each scanned commit's first-parent delta (a rebased branch then still proves its squash), with one regression that rebases the run branch onto an advanced base before the squash and asserts the complete marking and `landing_commit=` summary; the smaller alternative is a ledger refresh at the rebase step. Then add the four focused regressions to `DoneRunFinalizeTest` (the fixture pieces each need already exist in the class), or record the bound's recovery in the deferral warning's wording if the window is accepted as a known limitation.

## Why not fixed now

The landing run folded the blocking-class and silent-success-class findings; these four are additive coverage of edge arms, priced per the review budget policy (non-blocking findings fold into the watchlist and never force a re-round), and the landing was operator-bounded to one pick.

## Dedup probe

No other open row tracks finalize-leg test coverage; the sibling residuals row (Cluster line above) owns carried-arm message verification and unrelated closeout corners.

## Source

Witnessed by the 2026-10-26 focused landing panel over the deferred-squash honesty branch (testing r1 findings F2-F5, correctness r1 finding C1's test-coverage ask; staging record in `.ai-playbook/reviews/`).
