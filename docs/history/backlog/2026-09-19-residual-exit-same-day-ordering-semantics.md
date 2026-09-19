# Backlog: residual-acceptance exit same-day ordering semantics

Status: open
Origin: P11 execution review r1 (docs/reviews/2026-09-19-execute-plan-orchestration-authority-loop-bounds-release-gates-code-review-r1.md, F4; workers correctness-completeness + risk, dedup group 3)
Date: 2026-09-19

The pre-archive gate's ordering proof is strict at day precision against UTC-midnight of the sidecar date, so the skill-prescribed flow (record `residual_policy:` before the verification round runs) refuses whenever policy and round share a day - the normal record-then-round shape - and the UTC-midnight anchor makes the boundary timezone-dependent (in UTC+8 an early-morning recording passes, an afternoon one refuses). The gate fails closed and a later-day focused round recovers, but the current shape pressures orchestrators toward backdating `recorded_at`, an input the driver cannot verify.

Fix shape (decision needed): either compare against the round-day end (same-day recording permitted, strict the next day), or amend the execute-plan skill prose and runtime contract to require prior-day recording explicitly, pinning the same-day shape in a test either way.

Trigger: next execute-plan run that attempts a residual-acceptance exit, or any edit to the OR-branch ordering proof.
