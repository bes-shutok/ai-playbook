# Backlog: execution claim retry ceiling exact value unpinned by the witness suite

- **Cluster:** execution-claim-reliability
- **Status:** open
- **Priority:** Low

## Main idea

The race-retry helper's three-attempt ceiling in `scripts/execution_claim.sh` (`claim_retry_gate`, `if (( count > 3 ))`) is behaviorally pinned only as "a ceiling exists and is at least 2": the review-panel testing lens mutation-tested the suite with the ceiling changed to `> 2` and `> 4` and all 39 tests still pass; at `> 1` only the lost-then-won witnesses fail. The contended witnesses pin exit class, exact refusal text, and contender survival, but no assertion observes the attempt count (the refusal carries no attempt number). A cheap pin: in the contended witnesses, use a pass-through counting `date` shim (each create's stamp read via `iso_now` is the only `date` call before the create on that path) and assert exactly 3 stamp reads; this also catches a double-increment regression in the helper. Adjacent unwitnessed window, same class: the arm-3 takeover create-fail continue and the `takeover_stale_claim`-fail continue in `acquire_claim` feed the gate without any witness driving them.

## Driving force

Witnessed 2026-10-13 by the machinery-script-refactor-program exec run's Phase 3 testing lens (round 1, worktree branch 2026-10-13-machinery-script-refactor-exec): Task 3's extraction witnesses are substantively non-vacuous on text/exit/flags, yet the full suite passes under a +/-1 ceiling mutation, so the plan's "fail on the third attempt" bar is met only by construction, not by observation.

## Expected

A witness (or witness set) in `scripts/test_execution_claim.py` that fails when the ceiling constant moves by one in either direction, and ideally drives the takeover continue sites through the gate at least once.
