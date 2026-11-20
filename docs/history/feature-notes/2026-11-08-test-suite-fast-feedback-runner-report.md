# Required test suite runner report

**Status: INCOMPLETE.** This report preserves the current Task 5 evidence. The current-head full acceptance has not run. No claim is made that every required source passes within 60 seconds or that the complete `mise run test:required` command finishes within 300 seconds.

## Acceptance contract and implementation identity

The required scope is the entire repository inventory. Each source's 60-second clock starts after runner-level ready-queue and suite-slot/gate admission; it covers source discovery, per-source shard queuing and execution, output capture and descendant cleanup. Waiting for a source to be admitted and writing the final aggregate report count toward the complete `mise run test:required` limit of 300 seconds. Preserve all test IDs and behavior signals.

The active Task 5 worktree base commit is `df8be7355a3dea05b0ce1d74da68c0e6713fcdd4`; the modified implementation is pinned by the worktree file digests below. The repository task uses mise 2026.11.4, the configured project test virtual environment, 16 workers, a 60-second per-source limit and a 270-second internal suite deadline. The enclosing mise task limit is 295 seconds. Tool installation and lock resolution are outside the timed suite invocation.

| Source | SHA-256 |
|---|---|
| `mise.toml` | `bfc58eb9f59e1c5905a7f2f762d955c04606f797a16629b2a804449d126ecf1f` |
| `scripts/run_required_test_suite.py` | `e5967f4c315c22cd6c8b6b554dcfb4614797f44b3a86d31d928d851227a5e279` |
| `scripts/test_required_test_suite.py` | `c6e2df45bdd4f4881011600b398531fdbe70fb63566c029923e2bc7199e35853` |
| `scripts/test_authoring_continuation_ownership.py` | `51ba9561d8f0fb04432e6ca4ac5afc367dcc7b8d148143458e003526d2404059` |
| `scripts/test_authoring_raced_pick_continuation.py` | `432eda7449f4b86846e316e2cffd01d677581cdf59ddf45cd6b17c4fed13f7c1` |
| `scripts/test_invocation_telemetry.py` | `95e26050c7f2d68985fa84c5e74f97cd95dc38473c225b62f64d9e393289fae9` |

The source under the longest-source probe, `scripts/test_done_run_wrapper.py`, has SHA-256 `b501ac997843a2f7333ce3cdc6c9f4177f2794fe65ee6fb5d4ac777dacc1281d`. Its exact 145-ID inventory digest in the current probe is `c5ea634e7bded972321cd6c295be4d1a627670bf2a4b20f0150a4b7d9ad4ce5e`.

## Focused validation

The runner contract suite passed 25/25 tests in 18.191 seconds with:

```sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_required_test_suite.py' -q
```

The hostile-environment `mise` invocation also passed 25/25 in 17.995 seconds. Its PATH omitted the test virtual environment and the caller supplied invalid `AI_PLAYBOOK_TEST_VENV`, `PYTHONHOME` and `PYTHONPATH` values. The report records the configured interpreter and pinned import environment: `docs/tmp/test-suite-mise-hostile-path.json`, SHA-256 `978a5c3d32ada5d053b662ddb1d25daa8a0d3bd686857d6a7a6a29d1385433bd`.

## Longest-source exact-ID profiles

The probes keep the exact selected wrapper IDs fixed and retain the 60-second source deadline. Process-context sampling distinguishes clean-controller captures from runs with an unassigned controller. Host load is context only; none of the failed captures qualifies acceptance or a worker-count decision.

| Source and shard | Workers | Result | Duration and counts | Raw report |
|---|---:|---|---|---|
| `scripts/test_done_run_wrapper.py`; 16 balanced method batches plus whole-class `FixtureMixinCleanupTest` | 16 | Timeout | Source 58.150s; 55/145 IDs executed; 6/16 batches passed, 10 timed out; cleanup class passed 1/1. | `docs/tmp/test-done-run-wrapper-balanced-v5-capture.json`, SHA-256 `c7381302f128e9856cb33e2cb39d63e4f52c651178b6a3bee27368d20f242aea` |
| Same exact 145 IDs on main-refresh source digest `d0c2e53d`; 16 method batches of 9 plus whole-class cleanup | 16 | Timeout | Source 58.278s; 82/145 IDs executed; 9/16 batches passed, 7 timed out; cleanup class passed 1/1. Process capture sampled 102 states, found zero unassigned test controllers, peaked at 1,787,728 KiB owned RSS; captured host load rose from 5.66/6.55/5.87 to 23.91/11.51/7.75. | `docs/tmp/test-done-run-wrapper-main-refresh-profile.json`, SHA-256 `163dd2767fcce209ba58cafa0251f198a692db507973f067a234f0299b2d2a90` |
| Same exact 145 IDs; 32 method batches of 4–5 plus whole-class cleanup; dynamic consumer queue | 16 | Timeout, controller-contended | Source 58.235s; 71/145 IDs executed; 14/32 first-wave method batches passed and 18 timed out; cleanup class passed 1/1. Process capture sampled 98 states, found an unassigned `test_execute_plan_resume_watcher.py` controller (PID 46579), peaked at 1,805,456 KiB owned RSS; host load rose from 4.48/5.72/5.97 to 20.52/10.25/7.66. Later queued shards used the remaining source deadline without executing IDs. | `docs/tmp/test-done-run-wrapper-queue-r1.json`, SHA-256 `28364b887de6a2f6c93a36efc0457dcfb5e5feb34cca260d53caeec3ee3797f1` |
| Same exact 145 IDs; 16 method batches of 9 plus whole-class cleanup; one batch per worker (temporary runtime override; source unchanged) | 16 | Timeout, controller-contended | Source 58.056s; 118/145 IDs executed; 13/16 batches passed, 3 timed out; cleanup class passed 1/1. Process capture sampled 102 states, found an unassigned `test_execute_plan_resume_watcher.py` controller (PID 2833), peaked at 1,878,896 KiB owned RSS; captured load rose to 18.80/10.88/8.41. | `docs/tmp/test-done-run-wrapper-queue-one-per-worker-r1.json`, SHA-256 `f5cebbe11599505430582dd0718b4b191300ae1712ea6b274d444c4239be7329` |
| Same exact 145 IDs with one batch per worker (current source default) | 16 | Timeout, controller-contended | Source 58.238s; 10/145 IDs executed; 1/16 method batches and cleanup passed, 15 method batches timed out. Process capture sampled 96 states and found two unassigned `test_execute_plan_resume_watcher.py` controllers from another worktree (same parent PID); owned RSS peaked at 1,527,408 KiB. The capture began at host load 4.22/6.07/6.94 and ended at 20.79/10.87/8.68. | `docs/tmp/test-done-run-wrapper-queue-one-per-worker-final.json`, SHA-256 `73cc1d232b486432eb95c5da9553825d5ac96e335ae4da455d5e81af07b47a9e` |
| Same 145 IDs; 8 balanced method batches plus whole-class `FixtureMixinCleanupTest` | 8 | Timeout | Source 58.235s; 1/145 IDs executed; 8/8 batches timed out; cleanup class passed 1/1. | `docs/tmp/test-done-run-wrapper-workers8-capture.json`, SHA-256 `bafb7e350be73d9eee5fa2d1578d334a6b17af7510db1b5c246580177de37f43` |
| Same exact 145 IDs with one batch per worker (current source default) | 16 | Timeout, controller-contended | Source 58.238s; 10/145 IDs executed; 1/16 method batches and cleanup passed, 15 method batches timed out. Process capture sampled 96 states and found two unassigned `test_execute_plan_resume_watcher.py` controllers from another worktree; owned RSS peaked at 1,527,408 KiB. The capture began at host load 4.22/6.07/6.94 and ended at 20.79/10.87/8.68. | `docs/tmp/test-done-run-wrapper-queue-one-per-worker-final.json`, SHA-256 `73cc1d232b486432eb95c5da9553825d5ac96e335ae4da455d5e81af07b47a9e` |
| Same exact 145 IDs, source default; controller-clean retry under elevated host load | 16 | Timeout, host-contended | Source 58.208s; 46/145 IDs executed; four method batches passed, one timed out after executing all 9 IDs, and 11 timed out before collection. Process capture sampled 102 states, found zero unassigned controllers and peaked at 1,761,648 KiB owned RSS. Host load rose from 7.85/9.09/8.47 to 20.09/12.30/9.70; per-source queue wait was 0.441s. | `docs/tmp/test-done-run-wrapper-clean-retry.json`, SHA-256 `24a7ba026a150e27db47dd5b653a11f95c50e810b77711cc0a314ecdd2642da7` |
| Same exact 145 IDs, source default; second controller-clean retry at lower initial load | 16 | Timeout, host-contended | Source 58.067s; 100/145 IDs executed; 11 method batches passed and four timed out before collection; one additional batch timed out without collected IDs. Process capture sampled 103 states, found zero unassigned controllers and peaked at 1,913,744 KiB owned RSS. Host load rose from 5.32/9.29/9.16 to 17.64/12.19/10.25; per-source queue wait was 0.433s. | `docs/tmp/test-done-run-wrapper-clean-retry2.json`, SHA-256 `5f674d0c76f17017b04f579c0ce4625951a80f861645f6a666e6b9c5fb99588f` |
| Same exact 145 IDs, source default; third controller-clean retry after low 1-minute load | 16 | Timeout, host-contended | Source 58.682s; 55/145 IDs executed. Process capture sampled 101 states, found zero unassigned controllers and peaked at 1,887,792 KiB owned RSS. Host load rose from 4.52/8.33/8.98 to 25.27/13.56/10.89; per-source queue wait was 0.432s. | `docs/tmp/test-done-run-wrapper-clean-retry3.json`, SHA-256 `57ecb7e2074aca3df7b02a7d4742eabd7df4e57f8c26c875b8864eaee30b475d` |
| Same exact 145 IDs, 8 workers with eight larger method batches | 8 | Timeout, host-contended | Source 58.864s; 1/145 IDs executed; cleanup class passed, all 8/8 18-ID method batches timed out before collection. Process capture sampled 102 states, found zero unassigned controllers and peaked at 1,042,656 KiB owned RSS. Host load rose from 5.76/10.04/9.86 to 19.17/13.11/11.02; per-source queue wait was 0.448s. | `docs/tmp/test-done-run-wrapper-workers8-clean.json`, SHA-256 `eddd283e634d24f68ecc2df430d7de6f3569968763c24b77dccecfc5dd3c97e3` |
| Same exact 145 IDs, 12 workers with 12-ID method batches | 12 | Timeout, host-contended | Source 59.057s; 1/145 IDs executed; all 12/12 method batches timed out before collection. Process capture sampled 93 states, found zero unassigned controllers and peaked at 1,403,488 KiB owned RSS. Host load rose from 6.58/9.96/10.40 to 47.56/21.45/14.69; per-source queue wait was 0.487s. | `docs/tmp/test-done-run-wrapper-workers12-clean.json`, SHA-256 `0ee2f8950b6c2dddf1989281439c9c02cf853dd8fc1b46769b4598b9e41b3010` |
| Same exact 145 IDs on merged current revision `df8be735`; 16 balanced method batches plus whole-class `FixtureMixinCleanupTest` | 16 | Timeout | Source 58.745s; 19/145 IDs executed; 2/16 batches passed and 14 timed out; cleanup class passed 1/1. Accounting incomplete. Process capture found one unassigned test controller in another worktree. | `docs/tmp/test-done-run-wrapper-balanced-v6-capture.json`, SHA-256 `7ab3c080fa99777872c2b49bf518cb93356f297a62745a9ff9b034aed41aad03` |
| First exact 9-ID batch alone | 1 | Passed | 9/9 IDs in 23.087s; 43 process samples; zero unassigned controllers. | `docs/tmp/test-done-run-wrapper-balanced-v5-context.json`, SHA-256 `586a676037ea2acec5052648fbf2d55245ddf2649c023e91408e8ef41ecd2a63` |
| Earlier balanced wrapper profile without process sampling | 16 | Timeout | 37/145 IDs; 58.764s. This report is not usable for worker selection. | `docs/tmp/test-done-run-wrapper-balanced-v4.json`, SHA-256 `99180720073b52e232205f5c9ece5fd51743da801ea54ddb91c125f135d3509c` |

The v5 16-worker profile sampled 101 process states, peaked at 96 owned processes and about 1.5 GiB RSS, and saw host load peak at 21.00. The 8-worker profile sampled 103 states, peaked at 59 owned processes and about 0.9 GiB RSS, and saw host load peak at 21.67. Both v5 reports showed zero unassigned test controllers. The v6 profile sampled 101 states, peaked at 1,605,680 KiB owned RSS and host load 35.96, and reported an unassigned pytest controller running `scripts/test_profile_skill_gate_consult.py` from another worktree. The main-refresh profile had no unrelated controller but host load rose during execution. The 32-batch and both latest one-batch-per-worker profiles overlapped unrelated test controllers; the 32-batch variant also incurred a source-deadline queue tail. These runs are inconclusive, and none is acceptance evidence. The first 9-ID batch passed alone, so that isolated batch is not the reproduced failure.

The earlier Task 1 campaign passed all 145 IDs in 16 balanced batches in 51.791 seconds while host load ranged from 4.671 to 5.627. The current profiles include main commit `017fc047`, which changed the done-sweep implementation and tests even though the wrapper source digest is unchanged. The runs are not a fully matched comparison. Before v6, the parent reported a 1-minute load of 8.26 on 12 CPUs and no unrelated controller. At 22:47 WET immediately before the run, host load was 6.96/7.38/8.36; security detection used about 110.5% CPU, WindowServer 33.3%, and Trend Micro processes 32.6% and 23.8%. The v6 capture then detected an unrelated active pytest controller and host-load peak of 35.96. The probe is contended and does not establish a clean-host worker choice.

## Previous full-inventory failure

The only full-inventory JSON available is from source revision `d8e69a8f37ad03efdba077b7a8d7d332d23d551f`, before the current Task 5 changes. It inventoried 94 scripts (inventory digest `ae96a79dd7d3db0e6c21fb6bcba79d1f8a81c7364e7f9556093d038664f56731`), used 16 workers, a 60-second per-script limit and a 270-second internal deadline, then timed out at 268.395 seconds. It executed 611 cases; 11 scripts passed, 3 failed, 79 timed out and 1 had zero collection. The three slowest incomplete scripts were:

| Script | Executed | Time | Outcome |
|---|---:|---:|---|
| `scripts/test_done_run_wrapper.py` | 23 | 58.949s | Timeout |
| `scripts/test_done_sweep_gates_lib.py` | 241 | 58.936s | Timeout |
| `scripts/test_release_skill_selftest.py` | 13 | 55.312s | Timeout |

Seven assertion failures were reported in authoring-contract and invocation-telemetry tests; `scripts/test_done_run_wrapper_closeout_baseline.py` collected zero cases. The complete raw report is `docs/tmp/test-suite-fast-feedback-runner-report.json`, SHA-256 `ce6e6d3ad2992697596b1f2fd2cc9bbff5f23058349be63d707c348409662dba`; it is a historical failure report, not current-head acceptance.

## Current focused repairs and helper-suite disposition (2026-11-09)

The live inventory at this checkpoint is 94 source files with digest `39df360b7d7ea239ef4f05c64305c293cb6189cd223933a0fed42d954f02791d`. The seven historical assertion failures were reproduced and traced before correction:

- The two authoring-contract tests pinned the previous phrase `refuse to start`; the current template says `refuses the start`. Both test assertions now pin the current phrase while retaining the foreign-claim refusal and stale-takeover witnesses. Each 9-test unittest source passed.
- Four invocation-telemetry snapshots omitted the warning-only post-landing archive-ceremony evaluation line added by the archive-rider-sweep-ordering change. The snapshots now include that line; normalization masks only its dynamic timestamp and preserves the evaluated count, commit token and reviews-root assertion.
- The fifth telemetry failure came from the test fixture omitting `dispatch_admission.py`, which the current `done_sweep_gates_lib.py` imports. The fixture now includes that sibling while still omitting `invocation_telemetry.py`, so the test continues to exercise the intended fail-open telemetry-import failure. All 25 telemetry tests passed in 33.58 seconds under pytest.

The prior zero-collection result was a runner-policy bug, not an empty helper: `test_done_run_wrapper_closeout_baseline.py` uses unittest's module-level `load_tests` protocol to expose 15 tests from an imported class, while `_policy` selected pytest because the entrypoint has neither top-level `test_*` functions nor local `TestCase` classes. `_policy` now selects unittest for module-level `load_tests`; a focused regression and the full runner-contract source pass 26/26 in 17.33 seconds. The actual helper entrypoint then passed 15/15 IDs in 13.996 seconds at four workers. Its report is `docs/tmp/test-done-run-wrapper-closeout-baseline-current.json`, SHA-256 `9f1229db3e1140339db526a5da76210d3eef29892e04d4352c8a3d095d6c6594`.

These focused results establish the test-policy, assertion and fixture corrections only; the full-inventory 300-second acceptance is still open. The 32-batch retry did not improve the exact wrapper profile because the source deadline includes shard queue wait. Three source-default 16-worker retries had no unassigned controllers but reached 46/145, 100/145 and 55/145 as host load rose past 17. The 8-worker and 12-worker profiles each accounted for 1/145 and timed out all method batches before collection as host load rose sharply. All comparisons were host-contended; retain 16 as the better measured candidate and repeat only under a stable low-load window.

## Heavy command-coordination trial

Heavy 0.1.2 completed a three-pair shared-pool campaign and was rejected with disposition `reject-heavy-integration-complete-nonqualifying`. All twelve per-worktree command invocations (two worktrees for each side of three pairs) reported 18/18 with zero failures, errors and skips. The campaign finished in 133.671 seconds of its 300-second limit, but Heavy increased the median wall time from 14.741 to 29.128 seconds with one slot. The Heavy contender waited 14.247–14.671 seconds in each pair. Its cancellation canary completed as cancelled; the queued contender waited and passed. Heavy is not part of the required-suite command.

| Round | Baseline wall (s) | Heavy wall (s) | Heavy contender wait (ms) |
|---|---:|---:|---:|
| 1 | 14.966003 | 29.326428 | 14,576 |
| 2 | 14.672993 | 29.127647 | 14,671 |
| 3 | 14.740543 | 28.461513 | 14,247 |

Authoritative campaign artifacts are in `docs/tmp/test-suite-heavy-trial/`:

| Artifact | SHA-256 |
|---|---|
| `campaign.json` | `76209c85c522b0c9b21d2b4548ebe5e5ecc03c1a7c9f0ec924fff25a46437340` |
| `heavy-queue.jsonl` | `39c70f7a1546fa4e45e9f72172ae85db92b27bd129702695bfd9e58ba967462d` |
| `signal-canary-report.json` | `b368cb5d075b90126b1d796e434fa417632e19ca53c75c88f32b92537d896867` |
| `signal-contender-report.json` | `8b98c737f621ae763c488342bbe66a4d830db0928c77a7f2fe5225e7da701c3c` |

The distinct B-side raw reports copied from the detached checkout are preserved at `docs/tmp/execute-plan/test-suite-runtime-residual-optimization-path/task5-heavy-trial-reports/`. All six pass 18/18, but have no process-context samples; the campaign and queue/canary files above establish the paired aggregate result and coordination behavior.

## Decision, uncertainty and next bounded action

Do not select a worker count from the 8- or 16-worker profiles taken under heavy load. The confirmed method-local fixture proof and balanced batching remain in place; no change should downgrade general unknown suites from serial. Do not run the full current-head suite after the v6 wrapper probe missed its 60-second readiness gate and reported an unassigned controller. Parent owns any later host-readiness recheck; do not retime under the same load.

The v6 profile timed out and captured an unrelated controller. A later v7 run began with a parent-observed one-minute load of 5.36 on 12 CPUs and no active test controller, but process capture found an unassigned `test_execute_plan_resume_watcher.py` controller during the run; v7 is therefore inconclusive under the plan's controller-overlap rule. Keep the full-suite acceptance open. Any later continuation begins with a fresh parent-owned load and controller recheck. Only a future passing exact 145-ID profile can make the full `mise run test:required` acceptance ready; that command must account for all IDs, keep every admitted source at or under 60 seconds, and finish with ready-queue waits and final report writing within 300 seconds. Preserve both profiles and update the existing [residual origin](../backlog/2026-11-09-required-test-suite-five-minute-residual.md) with their digest-bound evidence.

Previous Node/direct-tool and language alternatives remain rejected or inconclusive under their existing matched-gain evidence. The current attribution points to high shell/Git/subprocess activity and host contention; it does not establish a material Python CPU share that would justify a wholesale language port. Revisit a narrow alternative only if a clean profile identifies a measurable fit.

## Final Task 5 profile and partial-closeout evidence (2026-11-10)

The current-head exact wrapper profile used 16 workers and selected all 145 IDs from `scripts/test_done_run_wrapper.py`. It executed and collected 1/145 IDs before timing out: the source elapsed 58.292 seconds against the 60-second limit; the complete report elapsed 58.787 seconds. Sixteen method shards timed out before returning accounting and the cleanup singleton passed. Process capture recorded 96 samples, zero unrelated test controllers, 1,892,608 KiB peak owned RSS and 0.444 seconds of shard queue wait. The capture began at host load 6.863/9.740/9.130 and peaked at 16.419/11.715/9.873; one process-context snapshot failed. This is a 60-second source-limit miss, not acceptance.

Raw report: `docs/tmp/test-done-run-wrapper-task5-pass3-profile.json`, SHA-256 `0fdb004d22f3a1bfc6c579b3bbcdedec676fc39e26754fbe0a95c916d41591f1`; wrapper source SHA-256 `d0c2e53de125b9cd4173f2a1e6f06fee75970b608c13461f591954730cec70d1`; inventory digest `214ac422c3f6b9e8197633c443a742e0ea1a26d8279694dfd222046636d46baf`. The full `mise run test:required` acceptance was not run because the exact profile did not pass. The 300-second target is unverified, not a measured timeout. Focused runner-contract validation passed 30/30 in 17.615 seconds. The user authorized a partial archive while these target states remain distinct; the residual backlog and ready prompt stay open for the next profile and, if it qualifies, one full-suite run.

## Recovery revalidation (2026-11-10)

The runner contract passed 31/31 in 22.258 seconds. A successful test worker that launched a detached child with redirected output now verifies that the child process group is gone before the shard passes. The validation also exposed a 25 ms process-tree snapshot timeout under a 0.1-second cleanup grace; raising the bounded snapshot minimum to 100 ms eliminated that spurious accounting failure. The synthetic queue-budget case now uses a 1-second source limit while retaining a strict queue-wait assertion.

On 2026-11-11, the cancellation integration case was extended to exercise both SIGTERM and SIGINT and to assert that the active suite is cancelled while the serial, not-started suite remains unrun and is reported cancelled. The focused runner contract passed 31/31 in 24.316 seconds with the command `python3 scripts/run_required_test_suite.py --suite scripts/test_required_test_suite.py --workers 1 --per-script-timeout 60 --suite-timeout 60 --json-report docs/tmp/test-suite-fast-feedback-runner-tests-signal-outcomes-final.json` under the configured test virtual environment. The report SHA-256 is `91f13439c094a8699db9f512b90329e1e13b48d1fa0462efa2e508f06f1a3258`. The targeted cancellation case also passed 1/1 in 6.257 seconds. This focused validation does not represent the full required-suite acceptance.

The exact 145-ID wrapper profile at 16 workers selected all live IDs and re-derived inventory digest `a896a5544c57575f560547e9e30a43eb4e4ef387841f36f99e11a4cbc7166de9`. It timed out at 55.949 seconds with 1/145 IDs executed; the complete report took 56.444 seconds. Sixteen method batches timed out before collection; the cleanup singleton passed. Process capture found zero unassigned test controllers in 91 samples; owned RSS peaked at 1,812,512 KiB and shard queue wait was 0.455 seconds. Host load at launch was 7.97/6.58/6.77. Raw report: `docs/tmp/test-done-run-wrapper-session-resume-profile.json`, SHA-256 `33489a9f94fccba99f8961cdc56cb818bacc574466518bccaeb863223de75607`. This is another 60-second miss. The full `mise run test:required` acceptance was gated and not run; its 300-second result remains unverified. The open next action is to profile stalled wrapper shards and test startup/concurrency choices under a fresh, stable, controller-clean window while preserving all 145 IDs.

## Per-test diagnostic and current worker cap (2026-11-10)

At the user's direction, the exact 145 wrapper cases ran in at most eight worker processes without per-test or worker timeouts. All 145 passed in 83.568 seconds. Individual elapsed time includes setup, test body and teardown; it excludes interpreter startup, collection and worker cleanup. Case times sum to 609.72 seconds; median 3.526 seconds, p90 8.221 seconds using the lower-order-statistic index `floor(0.90*(n-1))`, maximum 12.376 seconds. The complete case-by-case timings and outcomes are in [`2026-11-10-test-done-run-wrapper-case-durations.csv`](2026-11-10-test-done-run-wrapper-case-durations.csv). Raw diagnostic JSON: `docs/tmp/test-done-run-wrapper-case-durations-workers8.json`, SHA-256 `02e3bf694b985938258c8981b1096f46649c03accee18d2392593cd9caaeac42`.

The user set the worker ceiling to 8–10. The runner and mise task now cap at eight, chosen as the conservative option: the complete exact set finished at eight, while prior capped 16-worker attempts stalled before collection and reached 1.81–1.91 GB owned RSS. No 10-worker comparison was run. This diagnostic does not satisfy the plan's 60-second per-source limit: its full-source elapsed time was 83.568 seconds. The full 300-second acceptance was not run and remains unverified. Continue by reducing the repeated Git, checkout and process setup represented by the slowest cases in the CSV; rerun exact-source acceptance under 60 seconds before attempting the full inventory.
