# Backlog: plan_readiness internal selftest arm fails pre-existing

- **Status:** open
- **Origin:** outcome-contract-migration-batch-2 execution review r1 (docs/reviews/2026-10-04-exec-review-outcome-contract-migration-batch-2-r1.md) finding 3, non-blocking
- **Driving force:** correctness - the internal selftest arm `selftest#review_scope/uppercase_files_opener_collected` in scripts/plan_readiness.py fails identically on base main 4393c5c8 (verified byte-identical), so the embedded selftest does not fully pass on a clean tree; the arm's classification surface was frozen for the migration, so the fix belongs to its own pass

## Outcome

The uppercase-files-opener collection arm passes: either the opener pattern or the fixture expectation is corrected so `plan_readiness.py --selftest` is fully green, keeping the arm's guarded behavior.

Ship when: `--selftest` exits 0 with the arm green; no other arm's expectation loosened.
