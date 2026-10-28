# Backlog: the prune audit stayed green through two same-day receipt-ledger losses; promote the receipt-removal check to a flagged class

- **Cluster:** docs/history/backlog/completed/2026-10-15-plan-prompts-prune-end-anchor-overreach.md, docs/history/backlog/completed/2026-10-20-prompt-log-pending-prune-audit-warning.md, docs/history/backlog/completed/2026-10-22-prune-audit-landing-token-never-resolves.md (same prune-audit surface: this row records the promotion evidence the 2026-10-20 row pre-registered)
- **Filed:** 2026-10-28, investigate pass over the 2026-10-28 authoring run's teardown
- **Status:** covered (docs/history/plans/2026-10-28-pending-receipt-removal-audit-promotion.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** execution-run finding
- **Class:** fix-class

## Problem

The prune audit (`scripts/check_prompt_log_origins.py --prune-audit`) classifies only removed `## <slug>` entry headings; deleted `PLAN-PROMPTS-PRUNE:` receipt-ledger lines are invisible in both of its layers. The pending-layer scan (`pending_receipt_removal_warnings`, landed 256c1abaf on 2026-10-27 covering the completed 2026-10-20 row) warns only on the HEAD-vs-index-vs-worktree delta, so a receipt-line deletion that reaches HEAD before the audit runs is never surfaced by any layer.

Two same-day instances, both caught only by post-hoc teardown forensics, neither by the audit:

1. A landing's own-entry prune deleted heading-to-end-of-file and swept five foreign receipt lines off the log tail; the deletion landed certified, and the audit stayed green. Restored byte-exact the same day (repair b4c137a30).
2. The next entry's freeze commit, composed on a stale pre-prune copy of the log, reverted the previous landing's prune: it restored two landed-plan entries, dropped their two receipts, and (incidentally) restored three receipts the previous prune had swept. The committed-layer walk never saw it: the freeze deleted receipt lines but removed no entry heading, so no classification arm applies. Repaired the same day (repair 42610a0a2).

## Expected

The audit flags receipt-ledger-line deletions as a fail-closed class in both layers: the pending scan's warning becomes a flagged class (exit 1), and the committed walk (base..HEAD) gains a receipt-line-deletion arm, since the freeze instance shows a committed receipt deletion that no existing arm can see. A receipt line's removal is always anomalous: the charter makes the ledger append-only, one line per removed entry, and no sanctioned operation deletes one.

## Fix shape

Extend `check_prompt_log_origins.py`: promote the pending receipt-removal scan from warning-only to a flagged class, and add a committed-walk arm that classifies deleted receipt-ledger lines in log-touching commits (witness: the receipts stay present at the removal commit's parent or are re-added by a repair commit, which the two same-day repairs model). Update the selftest for both arms and the pins where the audit's outcome contract is pinned. This is a guard-outcome change on a gate-bearing surface, so it is not ad-hoc-eligible; it routes through a plan.

## Machinery admission (the promotion leg)

- Incident: the two same-day instances above (repairs b4c137a30 and 42610a0a2), with the completed 2026-10-15 row as the founding witness and the 2026-10-19 witness in development_lessons.md #111.
- Expected catch frequency: every receipt-ledger-line deletion in any layer; three production instances in thirteen days, all caught outside the audit.
- False-positive cost: a sanctioned receipt-line deletion would block a landing; none is known to exist (the ledger is append-only by charter), and a repair re-add is legible as a re-add in the committed walk.
- Sunset/review: review at the next prune-audit surface touch beside the completed 2026-10-22 row's descendants.

## Constraint

The repository guidelines' Machinery admission protocol requires a promoted blocker to retire or demote an existing blocker in the same change, or explicit operator approval of net growth after a true catch. The true catch exists; no demotion candidate is identified on this surface (the entry-removal witness flag is a different class and stays), so the promotion arm needs the operator's net-growth approval at dispatch time, recorded in the plan or its origin row.
