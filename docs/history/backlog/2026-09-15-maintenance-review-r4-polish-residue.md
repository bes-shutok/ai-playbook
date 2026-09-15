# Backlog: maintenance review r4 polish residue (non-blocking, loop exited clean)

**Captured:** 2026-09-15 (review-loop round 4 of the maintenance dispatch-ladder span; round 4 was the clean exit round with zero blocking findings, so these valid non-blocking findings are durably captured instead of fixed post-clean-round)
**Status:** open
**Priority:** low
**Origin:** mixed lenses (see per-item attributions; staged in docs/reviews/2026-09-15-branch-review-maintenance-dispatch-ladder-r4.md)

## Items

1. **Revisions ledger r3 gap** (design-simplicity, contract-docs): SKILL.md gained no r3 Revisions entry; the r2 entry was amended in place, now mixing rounds (the pricing-verification-failed marker is r3 work attributed to r2) and understating the r3 already-exists ENABLED-verification contract. Fix: add a review-r3 entry covering the operative changes (ambiguous carve-out, step 4 branching, watchdog guards, idle horizon alignment, Step 1 reader branch, full-span pin) and move r3-only clauses out of the r2 entry.
2. **Three unpinned r3/r4 invariants** (testing): the success-via-existing needle in the re-arm paragraphs, the pricing-verification-failed marker in zcode.md, and the ambiguous-outcome rule ("treat the child as dispatched") have no pins; paragraph parity alone passes a simultaneous revert. Fix: three cheap pins (one needles-list addition, two greps).
3. **Pins script trailing newline** (testing, risk): HEAD ends without a newline; cosmetic.
4. **Watchdog bullet garden path** (design-simplicity): "treats an already-exists refusal as success ... If the watchdog's own create is refused for any reason, no-op" reads contradictory until "the detector will not exist" resolves own-create to the arming OffPeakCreate. Fix: name the two levels explicitly.
5. **pricing-verification-failed note has no clear path** (risk, contract-docs): no instruction clears it on a later successful re-check or human re-pin, so it outlives its condition. Fix: clear-on-successful-re-verification wording plus an optional Step 1 read-back mention.
6. **already-exists verification-failure branch unspecified** (contract-docs): no behavior defined when the confirmation listing shows no ENABLED match; the natural fallback reading (escalation path) is safe but unstated. Fix: one sentence routing it to the standard retry/escalation path.
7. **Rollback refusal-kind inference scope** (correctness-completeness): the carve-out infers child success from ANY rollback refusal; the inference is only sound for the cap refusal class. Fix: scope the inference to cap-shaped refusals or verify via listing before skipping the marker writes.

## Context

Round 4 verified all round-3 blocking fixes and produced zero blocking findings; the loop exited clean per its criteria with these items backlogged rather than fixed post-clean-round. Each item is small; items 1 and 2 are the ones worth doing first (documentation-of-record completeness and drift detection).

## Open decisions for the plan author

- Whether item 1's r3 entry lands together with item 2's pins in one pass (they touch the same files).
- Whether item 5's clear-on-success belongs in the state cache refresh step or the Step 1 read-back.

8. **Lingered spawner records break the child re-arm duty (live-verified 2026-09-15 11:00)** (operator): a completed one-shot REMAINS listed (enabled false, lifecycleStatus completed) for at least tens of minutes and still binds its spawner session, so the child's re-arm-first CronCreate was refused on its first live test (the parent stayed absent until the operator deleted the lingered record and re-created the parent directly). Two fixes wanted: (a) the overlay's "completed one-shots disappear from CronList" statement must become "linger listed and still bind"; (b) the re-arm duty (and the watchdog spec) should first CronDelete the session's own lingered spawner record (identifiable by title and lifecycleStatus completed) before creating, or treat that specific refusal as retryable after self-deletion. The operator-side recovery (delete lingered record, re-create parent) worked and is the proven recipe.
