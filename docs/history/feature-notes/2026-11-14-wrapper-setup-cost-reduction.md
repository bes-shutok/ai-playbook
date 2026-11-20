# Wrapper setup-cost reduction: the six slow required-suite classes

Date: 2026-11-19. Plan: docs/history/plans/2026-11-14-required-test-suite-five-minute-residual.md, Task 3. Origin: docs/history/backlog/2026-11-09-required-test-suite-five-minute-residual.md (setup-cost arm). Branch: 2026-11-14-required-test-suite-residual at the Task 1-2 boundary (Tasks 1-2 landed; this task's own commit lands the wrapper change).

Scope: scripts/test_done_run_wrapper.py, the six named classes only (DoneRunRollingLogRefBoundCommitTest, DoneRunDirtCorrectionSetTest, DoneRunDescriptionLengthCatchTest, DoneRunDirtCachedDiffAuthorizationSeparationTest, DoneRunDeclaredStageChannelTest, DoneRunDeclaredStageRecoveryReplayTest). All other classes and the module's collection surface are frozen. Invariant: no changed line inside any test method body, the body range running from each `def test_` line through the last non-blank line before the next `def test_`, `class `, or zero-indentation statement, blank lines never terminating a range.

## Characterization baseline (before any edit)

Focused path (the plan's execution-selected command, run at the clean Task 1-2 tree):

```
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py -k "RollingLogRefBoundCommit or DirtCorrectionSet or DescriptionLengthCatch or DirtCachedDiffAuthorizationSeparation or DeclaredStageChannel or DeclaredStageRecoveryReplay" -q
```

Observed: `51 passed, 227 deselected in 124.57s`. GREEN before any edit, as required.

Per-class walls (one pytest invocation per class, same interpreter and venv):

| Class | Tests | Wall | Mean per test |
|---|---|---|---|
| DoneRunRollingLogRefBoundCommitTest | 23 | 55.90s | 2.43s |
| DoneRunDirtCorrectionSetTest | 12 | 23.26s | 1.94s |
| DoneRunDescriptionLengthCatchTest | 6 | 17.00s | 2.83s |
| DoneRunDirtCachedDiffAuthorizationSeparationTest | 3 | 8.18s | 2.73s |
| DoneRunDeclaredStageChannelTest | 2 | 4.66s | 2.33s |
| DoneRunDeclaredStageRecoveryReplayTest | 5 | 11.80s | 2.36s |

Duration map cross-reference (docs/history/feature-notes/2026-11-10-test-done-run-wrapper-case-durations.csv, the 2026-11-10 eight-worker diagnostic, SHA-256 c1ea9cf9b833ce5e13996959743fae222284421ba4e56d94a2f64041a3275f94): the map carries 46 rows across these classes (RollingLog 18, DirtCorrectionSet 12, DescriptionLengthCatch 6, RecoveryReplay 5, DirtCachedDiffSeparation 3, DeclaredStageChannel 2) with per-class elapsed sums of 105.20s, 61.44s, 41.91s, 33.23s, 21.61s, 12.34s. Those are worker-parallel elapsed slices captured when the module had 145 wrapper tests; the live module has 150 (five `log_expected` tests were added to RollingLog after the capture, see the ID-set section), so map sums and today's serial walls are directional context, not a like-for-like comparison.

## Setup-share profile

Targeted per-component timing (scratch profiler, gitignored run scratch; each cost measured on fresh fixtures with the test venv interpreter):

| Component | Observed cost |
|---|---|
| TestCase setUp (mkdtemp + env scrub) | 0.4 to 0.8ms |
| init_fixture_repo, first call per process (template build) | 81.0 to 84.2ms |
| init_fixture_repo, warm (template copytree) | 13.6 to 21.2ms |
| init_fixture_repo warm plus `checkout -qb` branch | 24.8 to 25.5ms |
| one helper `git` subprocess call | 5.3 to 7.1ms |
| seed_setup_session (real lock subprocess plus in-process manifest writer) | 187.3 to 199.7ms |
| setup_session (full `bash done_run.sh setup` runner subprocess) | 614.6 to 619.8ms |
| one commit-subcommand runner invocation (behavior under test floor) | about 1346ms |

The dominant reducible setup item is the full runner setup subprocess: about 620ms per test, of which the existing seed helper delivers the same boundary for about 195ms. Per-test setup share before the reduction (component arithmetic against the per-class means; estimates):

| Class | Setup path per test | Est. setup cost before | Share of mean wall | Reducible delta per test |
|---|---|---|---|---|
| RollingLogRefBoundCommit (21 of 23 tests) | init (no branch) + 4 git calls + full setup | about 670ms | 28% | about 425ms |
| DirtCorrectionSet (6 of 12 tests via correction_fixture) | init+branch + about 10 git calls + full setup | about 730ms | 38% | about 425ms |
| DescriptionLengthCatch (all 6 via refusing_session) | init+branch + writes + full setup | about 655ms | 23% | about 425ms |
| DirtCachedDiffSeparation (all 3 via dual_guard_fixture) | init+branch + about 7 git calls + full setup | about 700ms | 26% | about 425ms |
| RecoveryReplay (4 of 5 via replay_fixture) | init+branch + 3 git calls + full setup | about 670ms | 28% | about 425ms |
| DeclaredStageChannel (both tests) | init+branch + 3 git calls + seed (already reused) | about 245ms | 11% | none left |

The remaining per-test time is the commit-subcommand runner invocations (about 1.35s each, one to three per test) plus the assertion Git reads; those runs are the behavior under test and are not setup.

Equivalence differentials between the full setup and the seed path, measured before the swap (same fixture shape, `--owned-path work.txt`): the export key sets are identical (DONE_LOCK_DIR, DONE_LOCK_TOKEN, DONE_RUN_ID, DONE_RUN_MANIFEST, DONE_RUN_MARKER on both paths, values volatile by construction); the done-session tree carries the same file shapes (run manifest, worktree-migrate-baseline skip and manifest sidecars, one run-start marker); the run-start marker is structurally identical on both paths (three whitespace-separated fields: 10-digit epoch second, 64-hex repo-root digest, pid). The dozens of already-green commit-driven tests on the seed path (including both DeclaredStageChannel tests in this task's scope) corroborate that the commit side cannot distinguish the two boundaries.

## Reduction landed

Design chosen at execution: setup reuse through the module's existing shared seed helper (`seed_setup_session`, whose documented contract is a valid Step 0 boundary with the real lock acquisition and the real manifest writer when setup itself is not under test), replacing the full runner setup subprocess in the fixture helpers of the six classes. No shared class fixture: every test mutates its fixture repo (commits, index, branches), so per-test isolation must stay, and the template copytree behind init_fixture_repo (about 21ms warm) is already the cheap part.

Five hunks, all inside fixture helper methods (never a test body), each replacing one `self.setup_session(` call with `self.seed_setup_session(` plus a two-line rationale comment:

1. `refusing_session` (DoneRunDescriptionLengthCatchTest): covers all 6 tests.
2. `replay_fixture` (DoneRunDeclaredStageRecoveryReplayTest): covers 4 of 5 tests (the no-manifest arm runs no setup by design).
3. `correction_fixture` (DoneRunDirtCorrectionSetTest): covers 6 tests.
4. `dual_guard_fixture` (DoneRunDirtCachedDiffAuthorizationSeparationTest): covers all 3 tests.
5. `log_fixture` (DoneRunRollingLogRefBoundCommitTest): covers 21 of 23 tests.

Post-edit module SHA-256: 2a25931951fdbb6d4d2e12559bee9003faecebddf7053fcbdb6f5fbc3329d7d3.

## Discriminating check for assertion preservation

A throwaway checker (gitignored scratch: docs/tmp/execute-plan/required-test-suite-five-minute-residual/scratch/check_test_bodies_untouched.py) implements the invariant literally: it computes body ranges on both sides (HEAD content via `git show HEAD:scripts/test_done_run_wrapper.py` and the working tree) with the plan's rule (start at each `def test_` line; end at the last non-blank line before the next `def test_`, `class `, or zero-indentation statement; blank lines never terminate; zero-indent comments are not statements and do not terminate, the stricter reading), parses `git diff -U0 HEAD -- scripts/test_done_run_wrapper.py`, and fails if any hunk's old-side or new-side range intersects any same-side body range.

Observed on the landed diff: `body ranges on HEAD side: 278 test bodies`, `body ranges on worktree side: 278 test bodies`, `hunks ... 5`, all five hunks `OUTSIDE all body ranges`, `CHECK PASS: zero hunks intersect any test-method body range`, exit 0.

Discriminating witness (the check catches violations, it is not vacuous): with a one-line comment planted inside `test_over_cap_refusal_records_catch_before_refusing`'s body, the same checker printed `CHECK FAIL`, named the hunk as intersecting that body on both diff sides (HEAD body lines 2354-2375, worktree body lines 2356-2377), and exited 1; after restoring the file it returned to `CHECK PASS`, exit 0.

Two candidate swaps were dropped by this check's rule rather than forced: the helpers `binding_mutation_fixture` and `authorized_blob_fixture` (DoneRunDirtCorrectionSetTest, 3 tests) sit between test methods, so the invariant's body-range rule places their lines inside the preceding test's body range, and hunks there intersect by definition. They stay on the full setup; see Disposition.

## Wrapper ID-set preservation

The runner's own collection is unchanged by the diff: live collection was captured before any edit and after the edit with the plan's check 2 derivation; the two sorted ID files compare byte-identical under `cmp` (150 IDs each).

The plan's Validation check 2, run verbatim, currently fails before and after this task, on pre-existing source drift, not on this diff:

- Observed: `docs/tmp/rts-live-wrapper-count.txt` holds `150`; `grep -qx "145"` fails; `cmp` of the live sorted set against the duration map's ID column fails.
- The delta is exactly five IDs, all in DoneRunRollingLogRefBoundCommitTest: `test_log_expected_advisory_binds_to_staged_blob_not_commit_time_worktree_bytes`, `test_log_expected_deletion_shape_advises_and_lands`, `test_log_expected_malformed_blob_id_refuses_usage`, `test_log_expected_match_passes_silently`, `test_log_expected_mismatch_advises_once_and_lands`. They were added to the module after the 2026-11-10 capture (the clean Task 1-2 tree, before any edit of this task, already collects 150).
- Per the plan's validation preamble this is source drift to re-pin through a plan correction, never by editing the CSV; this task neither edits the CSV nor the plan, and flags the re-pin to the run's parent. Task 3's own preservation obligation, the byte-identical before/after collection, holds.

## After-measurement

Same commands as the baseline, run on the landed state (one invocation per class, then the combined focused path):

| Class | Tests | Wall before | Wall after | Delta |
|---|---|---|---|---|
| DoneRunRollingLogRefBoundCommitTest | 23 | 55.90s | 47.49s | -8.41s (-15.0%) |
| DoneRunDirtCorrectionSetTest | 12 | 23.26s | 20.36s | -2.90s (-12.5%) |
| DoneRunDescriptionLengthCatchTest | 6 | 17.00s | 14.04s | -2.96s (-17.4%) |
| DoneRunDirtCachedDiffAuthorizationSeparationTest | 3 | 8.18s | 6.86s | -1.32s (-16.1%) |
| DoneRunDeclaredStageChannelTest | 2 | 4.66s | 4.68s | +0.02s (no change landed; run noise) |
| DoneRunDeclaredStageRecoveryReplayTest | 5 | 11.80s | 9.88s | -1.92s (-16.3%) |

Combined focused path after: `51 passed, 227 deselected in 99.77s` (before: 124.57s; -24.80s, about -20% on that path, of which about 3s is the run-to-run noise band these classes show between invocations). Per-class pass counts are identical to the baseline everywhere (23, 12, 6, 3, 2, 5), the plan's GREEN-with-same-counts gate. No runtime target was gated; deltas are informational.

Focused runner contract suite after the task (plan evaluation criterion): `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_required_test_suite.py -q` observed `39 passed, 8 subtests passed in 21.13s`.

Commands and digests of record:

- Baseline and after runs: the focused-path command above; per-class variant `python3 -m pytest scripts/test_done_run_wrapper.py::<ClassName> -q`.
- Profiler (component table source): docs/tmp/execute-plan/required-test-suite-five-minute-residual/scratch/profile_setup_share.py (gitignored scratch; the load-bearing numbers are recorded in this file's tables).
- Body-invariant checker and witness: docs/tmp/execute-plan/required-test-suite-five-minute-residual/scratch/check_test_bodies_untouched.py (gitignored scratch; rule and observed outputs recorded above).
- scripts/test_done_run_wrapper.py after edit: SHA-256 2a25931951fdbb6d4d2e12559bee9003faecebddf7053fcbdb6f5fbc3329d7d3.
- Duration map (read-only input): SHA-256 c1ea9cf9b833ce5e13996959743fae222284421ba4e56d94a2f64041a3275f94.

## Disposition

Reductions landed: the full-runner setup subprocess was replaced by the shared seed boundary in five fixture helpers (`refusing_session`, `replay_fixture`, `correction_fixture`, `dual_guard_fixture`, `log_fixture`), moving 40 of the 51 baseline tests off the about 620ms repeated setup while keeping every test body byte-identical (checker-enforced), all 51 pass counts unchanged, and the focused path about 20% faster. DoneRunDeclaredStageChannelTest needed no new reduction: it already rides the seed path, and its remaining per-test setup (about 245ms of real lock acquisition plus fixture Git calls) is the boundary its commits validate.

Classes and arms left unreduced, with reasons:

- DoneRunDirtCorrectionSetTest `binding_mutation_fixture` and `authorized_blob_fixture` (3 tests): rejected here. Both helpers sit between test methods, so the invariant's body-range rule covers their lines, and the discriminating check would fail on any hunk; the swap is behaviorally proven (same differential evidence) but is not enforceable under this task's invariant, and the residual saving (about 1.3s) does not warrant an invariant change. A future plan that redefines the body-range rule to terminate at any method-level `def` may land the same two one-line swaps.
- DoneRunDirtCorrectionSetTest's three usage-error tests: nothing to reduce; they run init_fixture_repo only (about 25ms) before a fast usage refusal.
- RollingLog's two non-log_fixture tests: their setup is already the shared helper surface; no full-runner setup remains to remove.

No machinery, gate, lock, or state-schema bytes were added; the duration map and the pinned ID count were not edited; the live-versus-CSV drift re-pin (five post-CSV `log_expected` rows) is flagged for a plan correction and is not routed as a backlog row (the correction belongs to the plan that pinned the count).
