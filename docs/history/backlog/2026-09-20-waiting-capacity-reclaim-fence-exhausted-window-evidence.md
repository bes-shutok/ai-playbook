# Backlog: waiting-capacity reclaim fence evidence imprecision in the exhausted window

- **Status:** open
- **Origin:** execute-plan task 3 intermediate review (Step 1.2b, correctness-completeness lens, 2026-09-20)

## Finding

The `waiting-capacity` reclaim fence (`scripts/execute_plan_runtime.py:4386-4399`) refuses a reclaim unconditionally while the claim is parked, including the window after the retry budget is exhausted (`attempts_remaining: 0`) but before the fifth capacity receipt transitions the claim to `blocked`. In that window the refusal evidence still claims a live bounded retry policy and in-place resume, and the contract sentence scopes the refusal to "while the retry policy is live", which the window contradicts. Behaviorally harmless: continue still works, and the next capacity receipt lands the claim in `blocked`, which is reclaimable.

## Driving force

An operator reading the refusal evidence (or the contract sentence) in the exhausted window is told a retry policy is live when no attempts remain, which misdirects the recovery choice at exactly the moment the durable state is about to change.

## Suggested fix

Vary the refusal evidence by remaining budget (name the exhausted window explicitly), or narrow the contract sentence to the pre-exhaustion window and describe the exhausted window's transition to `blocked`.
