# Run-session tmp evidence lost mid-run, wiper unverified

- Cluster: removed (covering plan docs/history/plans/2026-10-19-executor-landing-helper-routing-gap.md executed and landed 2026-10-19; the done/executor boundary family; shared surface is the done runner's steps around the run's own record surfaces)
- Added: 2026-10-19
- Origin: the 2026-10-18 two-plan execution run (sess_e0cf1ac8; landings 5cd467d91 + 8802fee54)
- **Status:** open

## Witness

During the 2026-10-18 execution of plan-declared-missing-input-fallback, the run's session directory under `docs/tmp/execute-plan/<plan-slug>/` was emptied twice across done boundary steps: the recorded pins-suite baseline file written at Task 1 was gone by the Task 3 battery, and the session manifest written after it was gone immediately after the next done commit. The baseline was recovered only by re-running the suite at the merge base in a scratch checkout and byte-comparing the tail. The wiper is unverified: the done runner's visible `rm -rf` sites target its own mktemp scratch, and the setup's worktree residue sweep reported a tool error both times (fail-open, applied nothing), so no audited mechanism matches the witnessed deletion.

## Problem

Evidence a later phase must consult (a recorded baseline, the session manifest) lives only in the run's gitignored scratch, and something in the boundary toolchain removes it mid-run. The execute-plan skill's own anti-pattern table forbids deleting the session tmp before Phase 5, so the loss contradicts a standing rule whose enforcement no audited component owns. Recovery cost is a full re-derivation from the base commit, and a run that fails to re-derive loses its verification record silently.

## Expected

The wiper is identified from records or a reproduction, and exactly one of: the deleting component is scoped to exclude the live run's session directory, the rule gains an enforcement owner matching the real mechanism, or the run contract makes the durable-copy discipline mechanical (evidence lands outside the scratch as part of the boundary step, not by session discipline). The fix names the mechanism as its incident witness; no blocker is guessed at.

## Suggested direction

First archaeology, then the smallest arm: reproduce the loss across a setup-plus-commit pair with a canary file in the run tmp, identify the deleting step from the canary's death time, and scope that step (or add the durable-copy duty to the boundary it belongs to) with the witnessed deletion as the admission incident.
