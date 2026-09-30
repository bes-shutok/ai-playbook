- **Filed:** 2026-09-30
- **Status: done (2026-10-01; executed+landed docs/history/plans/completed/2026-10-01-cited-review-receipt-integrity.md, squash main 58d56a97, exec review r1 ready=yes zero blocking)(docs/history/plans/2026-10-01-cited-review-receipt-integrity.md)
- **Workflow:** backlog
- **Priority:** high (third witness of the completion-ceremony class in one day; cited receipts unverifiable from disk)
- **Origin class:** self-serving (operator-directed audit of the 2026-09-30 evening exec batch)
- **Driving force:** correctness
- **Class:** fix-class

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md
Cluster: docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md
Cluster: docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md
Cluster: docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md
Cluster: docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md
Cluster: docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md
Cluster: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md

# Plan archive must verify its cited review receipts exist on disk

Witness (2026-09-30 19:37-19:40, investigate-cluster-survey-anchored): the plan landed (53d74e60), executed, and archived (85122e7e/15e32d4a) inside three minutes with all four task checkboxes unchecked and no completion record. The execution commit claims "exec review r1 ready=yes zero blocking" and the plan header cites docs/reviews/2026-09-30-plan-review-investigate-cluster-survey-anchored-r1.md, but no file matching survey-anchored exists in docs/reviews on main, in any commit reachable from any branch, or on the docs branch. The receipt trail claims evidence that has no bytes behind it; from disk alone a later reader cannot distinguish "the review ran and its record was never transferred out of the worktree" from "the review never ran".

This extends the two receipt-class gaps in docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md (archive-checkbox gate, archived-plan review-coverage hole) with a check neither covers: the existence of the review records the archive itself cites. The implementation was verified real (all seven Validation Commands re-run green on main by the 2026-09-30 audit session; exec squash touches exactly the two in-scope files), so this is a receipt-integrity defect, not a work-loss defect.

Asked changes:

1. Backfill: append a completion record to docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md marked as a backfill, citing the re-verification evidence above, and check the four boxes with the same marking.
2. Machinery: the archive acceptance path (the plans-archive-twin done-sweep gate and/or the plans skill archive step) verifies that every review path cited in the plan header exists on disk at archive time, fail-closed: a missing cited record blocks the archive or demotes it to an explicitly recorded reconstruction instead of a certified archive.
3. Machinery: the same existence check for exec-review records claimed by the execution closeout commit message; the done sweep's owned-commits ledger already names the landing shas, so one gate can require the claimed exec-review record to exist under docs/reviews/ before the done boundary closes.
