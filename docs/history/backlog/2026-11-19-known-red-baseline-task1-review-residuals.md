# Backlog: known-red baseline Task 1 review residuals

Driving force: code-quality (witnessed by the Task 1 intermediate review r1, 2026-11-19, worktree run known-red-gates-consumed-baseline, commit 2d592869e; log `docs/tmp/execute-plan/known-red-gates-consumed-baseline/review-task1-r1.log.md` in the run worktree, mirrored at the reviews home at Phase 3).

Minor findings (non-blocking, valid, unfixed):

1. `render_baseline` matches an unavailable-trigger marker at any stdout position while the register row declares the producers' final `OUTCOME:` line; observably equivalent for the byte-frozen producers, but the row wording and the matcher should agree.
2. Relative `--render-baseline` output paths resolve against the primary checkout ROOT; Task 2's landed "Render resolution scope" wording must describe the landed root-resolution (Task 2 owns the clause, no script edit needed).
3. `load_tests` docstring pins "exactly the pre-render 24 tests" but the fixture arm now carries 25.
4. The Terms embedding clause (embedded other-producer lines classify under the owning producer's section) is implemented but unasserted; the fixture already produces embedded budget lines in the pins stream, so a one-line assertion pins it.

Backlogged candidates: register-row born-conformant arms (usage-error exit-3 remap, unresolvable-primary tool_error) smoke-tested only; capture classes PIN WARN / CEILING BREACH / lower-case `pin fail:` / PILOT OVER never exercised live in the fixture (plan priced exactly the delivered floor).

Cluster: known-red-gates-consumed-baseline
