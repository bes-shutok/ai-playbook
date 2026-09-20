# Backlog: pin stale-claim reason code on the readiness contention arm

- **Status:** open
- **Origin:** execute-plan task 6 intermediate review (Step 1.2b, testing lens, 2026-09-20)

## Finding

`test_readiness_blocked_while_manifest_lock_held` (scripts/test_execute_plan_runtime.py:4017) pins decision `recovery` and recovery action `resumable-conflict` on the readiness contention envelope but not `reason_code == "stale-claim"`; the reason code is pinned only at the shared `_mutation_unavailable`/`_stale_claim_outcome` level through other paths. A regression changing only the readiness arm's reason code would pass the suite and the contract probe.

## Driving force

The contract's CD5-2 scoping sentence names `stale-claim` with `resumable-conflict` as the contention contract; an unpinned arm lets the envelope's reason code drift away from the documented contract silently.

## Suggested fix

Add `assertEqual(outcome["reason_code"], "stale-claim")` to the readiness contention test.
