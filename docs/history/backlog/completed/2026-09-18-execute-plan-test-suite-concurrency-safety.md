# execute-plan driver suite is not concurrency-safe (r5 CC5-1, deferred at round cap)

Status: done (executed 2026-09-23 via docs/plans/completed/2026-09-22-execute-plan-driver-batch-3.md)

Evidence: scripts/test_execute_plan_runtime.py:1112 writes the fixture manifest to a fixed name (runtime_state.json) in the SHARED TMPDIR, outside the per-test temp dir; two simultaneous suite instances clobber it (8 concurrent pair-runs reproduced 11 failures, KeyError 'token' at :1116; leftover file persists in $TMPDIR). Separately, 4 of 8 suite runs during a concurrent peer-validation window returned success-instead-of-blocked from ArchiveGatePreArchiveTest refusal tests (open-claims and commit-pending subtests); the mechanism is unconfirmed (never reproduced serially, ~25 runs) but a wrong-direction result in terminal-gate tests warrants investigation. Serial suite is the Validation GREEN gate and is stable.

Direction: write the fixture manifest inside the per-test temp dir or a uuid-suffixed name (pattern exists at :3494), delete leftover $TMPDIR/runtime_state.json, re-run twice in parallel to confirm zero failures; then investigate the success-instead-of-blocked observations under controlled concurrency before trusting concurrent suite results.

## Implementation

Implementation source: docs/plans/2026-09-22-execute-plan-driver-batch-3.md (### Task 4); closed by the executed plan's implement worker in the `2026-09-23-execute-plan-driver-batch-3` worktree.

Investigation outcome:

- Fixture hygiene landed on main before this plan via commit 82b4876c: uuid-suffixed fixture manifests and per-test `TemporaryDirectory` placement removed the shared-temp collision surface this item described (the fixed-name `runtime_state.json` in the shared `TMPDIR`), and no leftover shared fixture regenerated.
- The concurrency smoke harness landed via this plan's Task 1: `scripts/test_execute_plan_suite_concurrency_smoke.py`.
- Concurrency smoke: 3 rounds x 2 plus 1 round x 8 concurrent refusal-subset instances (`ArchiveGatePreArchiveTest`) per execution, each instance with its `TMPDIR` bound to its own distinct mktemp root; executed twice, all instances exit 0 with zero escaped `runtime_state.json` fixtures.
- Parallel pair-run: 2 concurrent full-suite instances on the shared ambient temp directory, both exit 0 (341 tests each).
- Investigation verdict: not-reproduced. No success-instead-of-blocked outcome appeared in any smoke round or pair-run. The original 2026-09-18 observation was 8 concurrent full-suite runs (4 of 8 returned success-instead-of-blocked from refusal subtests, never reproduced serially in about 25 runs); this investigation sampled the refusal subset at up to 8-way concurrency and the full suite at 2-way concurrency, and the exact original shape (8 concurrent full-suite runs) was not re-sampled. Evidence: docs/tmp/execute-plan/2026-09-22-execute-plan-driver-batch-3/task1-implement.log.md.
