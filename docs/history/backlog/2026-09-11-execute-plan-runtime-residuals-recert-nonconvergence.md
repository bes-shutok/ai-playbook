Status: open
Priority: high
Created: 2026-09-11
Origin: execution of docs/plans/2026-09-11-execute-plan-runtime-residuals-prose-residual-rider.md (Task 3 re-cert loop)

# execute-plan-runtime-residuals re-cert loop stopped in fix-generates-findings non-convergence

The rider plan's Task 1-2 folds landed cleanly (commits 51fac72, 4efaf17..2c7d3a5 chain on branch `2026-09-11-runtime-residuals-prose-rider`). The blind full-panel re-cert loop then ran six rounds (r9-r14, 2026-09-11) without reaching a fresh `ready=yes` zero-blocking round: each round's blocking folds manufactured the next round's mechanical blocking findings on the anchor/seed-token mechanism (r13's codex-only fixture wording was reversed by r14 F1; r12's sibling sweep produced r14 F2; r13's seed token produced r14 F4 and F6). Per ADR-0002 the loop stopped at the cap with the stop-and-ask default resolved to backlog deferral.

## Pending blocking findings (r14, none folded)

- F1 Task 6: the driver suite does carry an approval-receipt fixture; the r13 "codex-only" fixture wording is wrong and must be reverted to both suites.
- F2 Task 2: the sibling sweep flocks a manifest whose path no longer resolves (no lockable object); prescribe an adjacent path-keyed lockfile and require the anchor to record the resolved manifest path.
- F3 Task 4: post-window locked mutations must re-read the manifest and fail closed `stale-claim` on generation change (stale snapshot write-back).
- F4 Tasks 2/8: the seed-token minting forward-depends on Task 8's `create`; scope Task 2 to the test seeding helper, move parity into Task 8 with a witness, reword the seed-conveniences invariant.
- F5 Task 2: its Run gates never exercise the registry suite it edits.

Plus r14 non-blocking pending: validation-block selftest HOME pin, seed-token mode/layout pins, receipt-rejection reason classification, crash-window digest staging, Task 9 selftest cases, cleanup-ledger additions.

## Deferred design-alternative family (regenerating class)

Task 2/5 bundle splitting; seed-marked anchor instead of a second token file; sweep moved off the launch path or non-blocking; non-reentrant lock replacing the held-set; uniform deferral encoding; allowlist enforcement at the import seam. Each is coherent alone and mutually exclusive with mechanisms landed by r10-r13 blocking folds.

## DESIGN DECISION 2026-09-11 (user): threat model narrowed

Malicious same-user worker defenses are deferred (see 2026-09-11-deferred-malicious-worker-hardening.md; guidelines section 64). Driving principles: efficiency, token usage, simplicity.

## Next step

Shrink the fold target to the deferred-free shape: Task 2 keeps only the launch-record snapshot + baseline/generation change witnesses (the entire out-of-tree anchor apparatus, seed tokens, sibling sweep, and TOFU migration move to the deferred backlog); Task 4 adopts the structural non-reentrant lock with post-window re-read; re-derive all counts and cross-references; then run review-reconciliation over r9-r14 with the new threat model as the filter, fold the surviving mechanical findings (Task 6 driver fixture, gate coverage, ledger), and run one fresh blind exit round.
