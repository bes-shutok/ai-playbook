# Backlog: branch-only closeout receipt plan certification residuals

Status: open
Workflow: backlog
Priority: low
Origin class: plan-review residual
Class: fix-class
Driving force: code-quality

## Problem and evidence

The r4 certification round of `docs/history/plans/2026-11-08-branch-only-closeout-gate-report-retention.md` (plan bytes sha256 f0be69b5365c82ef699a122e2741c197be14df6ab1bf56d730cfe35948092ac1) staged no blocking finding and carried six non-blocking findings; the r1 round carried one more. Each premise was re-verified from disk before routing:

1. Exitless stamped-empty retention (Medium, r4 F1): once a branch-only pass stamps the empty `terminal_completion_receipts` section and the branch ref is deleted without a later accounted pass, every later pass yields `unknown-ref` (an accounted disposition needs `_capture_branch_oid` to resolve the ref), so no receipt can ever be written and the session's aged reports are retained on every sweep; the Gate delta's "bounded by the operator resolving the closeout" cost claim does not hold for this abandoned shape.
2. Unpinned fail-closed witness (Medium, r4 F2): Task 4's safety witness (a failed receipt append or stamp refuses rather than reporting completion) has no RED test in Tasks 2 or 3, so an implementation that swallows the append error passes every named gate.
3. Refresh versus append-only (Low, r4 F3): Task 4's "a repeated pass refreshes, never duplicates" contradicts Assumption 1's append-only discipline and `_append_manifest`'s never-rewrite contract; the two readings keep different timestamps.
4. Consult scope (Low, r4 F4): the Gist's unqualified "consults the section on manifests that carry it" diverges from Task 4's no-worktree-match scope on the theoretical re-registered-worktree shape.
5. Discrimination channel and stale prose (Low, r4 F5): Task 3 test 1's "consulted justification" leg is only writable as the differential against test 3 (removed reports carry no reason text), and the kept-reason string ("cited by a live registered-worktree closeout manifest") plus `_closeout_reference_hold`'s deferral docstring sentence go stale with no Task 4 bullet updating them.
6. Dangling origin citation (Low, r4 overflow): Review Scope cites "origin scope arm (4)", but the origin row has no numbered arms; the intended clause is the origin's Expected preserve-clause.
7. Unlocked append (Low, r1 F6): the receipt append rides `_append_manifest`'s unlocked read-modify-write, so a concurrent manifest writer can drop the receipt.

## Correction

At plan execution, the executor folds items 1-5 into the Task 2 through Task 4 work: one Assumptions or Gate delta sentence naming the exitless state and its exits (restore the ref and complete an accounted pass, or manual cleanup outside the sweep) with the 2027-02-08 admission review as the revisit bound; one RED bullet injecting an append and a stamp failure; the skip-duplicate shape (the first accounted pass's timestamp stays); the scoped (retain) reading for a worktree-matched marker-carrying manifest; test 1 written as the differential pair, and the kept-reason string and docstring updated in the same change. Item 6 is plan-text wording fixed through the normal plan edit and review lifecycle; never silently mutate certified bytes. Item 7 stays a recorded residual unless the execution review finds a concurrent writer in the branch-only path.

Dedup probe: searched open backlog for `terminal_completion_receipts`, branch-only closeout, receipt, and gate-report retention; the only related open row is the origin row (`docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md`, which this plan covers).
