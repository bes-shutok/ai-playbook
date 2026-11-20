# Test Suite Runtime Reduction Follow-up

## Task 1: Fresh complete-suite baseline and residual profile

### Authorization and scope

The user replied “yes” to the question whether to execute this follow-up plan now. This is the exact receipt for the plan's bounded protocol: one fresh complete-suite baseline, and at most one final complete-suite comparison only if a candidate passes the predeclared selection rule. The earlier “Accept 44.10% for now” remains an interim acceptance; it does not authorize a second baseline or automatically authorize a final run.

No harness, test, runner, or production configuration was changed. The only full-suite invocation in this task was the single serial 88-suite sequence below.

### Baseline result

| Measure | Result |
|---|---:|
| Source revision | `25f09b395788233b2c09c7b9f3651440d1633973` |
| Started / ended (UTC) | 2026-11-07 23:08:42 / 23:37:50 |
| Complete inventory | 88 suites; inventory SHA-256 `08f371ba74ffb32a4ce9fcac9779539e78b0d377634b29da9ec4c43ed2596a75` |
| Runner split | 73 `unittest` class-only suites; 14 function-only `pytest` suites; 1 mixed suite via `pytest` |
| Runner-reported cases | 3,541 |
| Failures / errors / skips | 0 / 0 / 1 |
| Suite sequence wall time | **1,748.107 seconds** (29 min 8.1 sec) |
| Sum of per-suite wall times | 1,747.875 seconds; 0.232 seconds difference is the driver’s between-command and result-persistence overhead |
| Summed process user / system CPU | 571.31 / 642.51 seconds |
| Wall time beyond summed CPU | 534.06 seconds; this includes waits, scheduling, and other non-CPU time and cannot be assigned to one cause from this run |
| Host load average at start / finish | 12.115 / 10.946 / 10.011; 14.001 / 15.792 / 15.035 |
| Host | macOS 26.6.2 arm64; 12 logical CPUs; Python 3.14.10; pytest 9.1.1 |

The sole skip was `test_docs_branch_sync.py::DocsBranchSyncTests.test_fixed_reviews_symlink_to_configured_root_is_archived_once_at_target`, which skips when the host cannot create the symlink. There were no failed suite commands. The case total uses each runner's native summary: `unittest` counts test methods and does not count successful subtests as separate outcomes. It is therefore not directly comparable to the prior report's JUnit aggregate, which included subtests.

**Runner comparability limitation:** current repository guidance requires pytest for plain-function suites and unittest discovery for class-style suites. This run followed that guidance. The accepted 2026-11-06 full-suite comparison used pytest for all 88 files. Although this run keeps all 88 suite files, serial one-process-per-suite execution, and the same host class, changing the runner for 73 suites and observing different shared-host load means the elapsed time is not a strict like-for-like comparison with 2,036.658 seconds. The new number is a fresh baseline for this runner policy; it does not replace the accepted 44.10% result or establish a candidate's final gain.

A separate pytest process for `test_done_run_wrapper.py` was observed during the wrapper suite, and other separate test processes were observed during later suites. They were not part of this run, were not signaled, and add shared-host contention uncertainty. The baseline itself remained serial. Start and finish load averages also rose during the sequence. The data does not quantify how many seconds this contention added.

### Per-suite inventory and outcomes

The table records every discovered suite, runner, runner-reported test count, skips, command status, and elapsed time. Test counts are not normalized across pytest and unittest; the complete file inventory and all suite outcomes are accounted for.

| Suite | Runner | Tests | Fail | Error | Skip | Wall (s) | Result |
|---|---|---:|---:|---:|---:|---:|---|
| `test_authoring_continuation_ownership.py` | unittest | 9 | 0 | 0 | 0 | 0.062 | PASS |
| `test_authoring_plans_liveness.py` | unittest | 13 | 0 | 0 | 0 | 1.498 | PASS |
| `test_authoring_raced_pick_continuation.py` | unittest | 9 | 0 | 0 | 0 | 0.058 | PASS |
| `test_base_reflog_audit.py` | unittest | 14 | 0 | 0 | 0 | 4.865 | PASS |
| `test_budget_guard_hooks.py` | unittest | 24 | 0 | 0 | 0 | 2.340 | PASS |
| `test_check_backlog_claimed.py` | unittest | 13 | 0 | 0 | 0 | 1.083 | PASS |
| `test_check_investigate_entries.py` | pytest | 2 | 0 | 0 | 0 | 1.422 | PASS |
| `test_check_lesson_scope.py` | unittest | 38 | 0 | 0 | 0 | 1.454 | PASS |
| `test_check_no_em_dash.py` | unittest | 6 | 0 | 0 | 0 | 0.551 | PASS |
| `test_check_plan_origins_closed.py` | unittest | 81 | 0 | 0 | 0 | 6.238 | PASS |
| `test_check_prompt_log_origins.py` | pytest | 108 | 0 | 0 | 0 | 43.910 | PASS |
| `test_check_review_agent_portability.py` | pytest | 12 | 0 | 0 | 0 | 0.834 | PASS |
| `test_check_run_continuity.py` | unittest | 9 | 0 | 0 | 0 | 2.426 | PASS |
| `test_claimed_target_skip_and_continue.py` | unittest | 7 | 0 | 0 | 0 | 0.061 | PASS |
| `test_code_delta_classifier.py` | unittest | 22 | 0 | 0 | 0 | 6.412 | PASS |
| `test_codex_budget_reset_guard.py` | unittest | 4 | 0 | 0 | 0 | 0.530 | PASS |
| `test_codex_hook_config.py` | unittest | 2 | 0 | 0 | 0 | 0.059 | PASS |
| `test_codex_model_guard.py` | unittest | 8 | 0 | 0 | 0 | 0.853 | PASS |
| `test_codex_model_guard_probe.py` | unittest | 12 | 0 | 0 | 0 | 0.497 | PASS |
| `test_corrections_record.py` | unittest | 92 | 0 | 0 | 0 | 108.243 | PASS |
| `test_debugging_lesson_recall.py` | unittest | 4 | 0 | 0 | 0 | 0.056 | PASS |
| `test_deploy_runtime_helpers.py` | unittest | 28 | 0 | 0 | 0 | 14.667 | PASS |
| `test_dirt_regression_gate.py` | unittest | 54 | 0 | 0 | 0 | 13.968 | PASS |
| `test_dispatch_admission.py` | pytest | 13 | 0 | 0 | 0 | 0.780 | PASS |
| `test_docs_branch_sync.py` | unittest | 54 | 0 | 0 | 1 | 53.569 | PASS |
| `test_done_router_dispatch.py` | unittest | 6 | 0 | 0 | 0 | 0.150 | PASS |
| `test_done_run_wrapper.py` | unittest | 263 | 0 | 0 | 0 | 692.935 | PASS |
| `test_done_sweep_gates_lib.py` | pytest | 474 | 0 | 0 | 0 | 108.449 | PASS |
| `test_done_sweep_gates_wrapper.py` | pytest | 9 | 0 | 0 | 0 | 2.856 | PASS |
| `test_execute_plan_precondition_cli.py` | unittest | 10 | 0 | 0 | 0 | 1.242 | PASS |
| `test_execute_plan_referral_contract.py` | unittest | 15 | 0 | 0 | 0 | 0.056 | PASS |
| `test_execute_plan_resume_watcher.py` | unittest | 72 | 0 | 0 | 0 | 1.559 | PASS |
| `test_execute_plan_worktree_bootstrap.py` | unittest | 5 | 0 | 0 | 0 | 1.687 | PASS |
| `test_execution_claim.py` | unittest | 83 | 0 | 0 | 0 | 93.452 | PASS |
| `test_fix_plan_em_dashes.py` | unittest | 7 | 0 | 0 | 0 | 0.745 | PASS |
| `test_friction_audit_quant.py` | unittest | 6 | 0 | 0 | 0 | 0.196 | PASS |
| `test_gate_liveness_ledger.py` | unittest | 27 | 0 | 0 | 0 | 2.166 | PASS |
| `test_gate_liveness_wiring.py` | unittest | 5 | 0 | 0 | 0 | 0.112 | PASS |
| `test_harness_detection.py` | unittest | 12 | 0 | 0 | 0 | 0.521 | PASS |
| `test_harness_policy_contract.py` | unittest | 9 | 0 | 0 | 0 | 0.092 | PASS |
| `test_hooks_probe.py` | unittest | 1 | 0 | 0 | 0 | 0.053 | PASS |
| `test_invocation_telemetry.py` | pytest | 25 | 0 | 0 | 0 | 26.808 | PASS |
| `test_land_squash.py` | unittest | 65 | 0 | 0 | 0 | 88.400 | PASS |
| `test_landing_parentage_gate.py` | unittest | 29 | 0 | 0 | 0 | 8.629 | PASS |
| `test_learn_router_dispatch.py` | unittest | 8 | 0 | 0 | 0 | 0.175 | PASS |
| `test_lessons_recovery_contract.py` | unittest | 4 | 0 | 0 | 0 | 0.059 | PASS |
| `test_machinery_inventory.py` | unittest | 25 | 0 | 0 | 0 | 8.396 | PASS |
| `test_maintenance_fire_outcomes.py` | pytest | 43 | 0 | 0 | 0 | 0.487 | PASS |
| `test_maintenance_runtime_scope.py` | unittest | 10 | 0 | 0 | 0 | 0.052 | PASS |
| `test_parallel_work_regressions.py` | unittest | 3 | 0 | 0 | 0 | 1.598 | PASS |
| `test_plan_delta_classifier.py` | unittest | 40 | 0 | 0 | 0 | 4.216 | PASS |
| `test_plan_readiness.py` | unittest | 202 | 0 | 0 | 0 | 23.663 | PASS |
| `test_plan_review_boundary_examples.py` | unittest | 8 | 0 | 0 | 0 | 0.135 | PASS |
| `test_plan_shape.py` | unittest | 21 | 0 | 0 | 0 | 0.212 | PASS |
| `test_plan_task_span.py` | unittest | 14 | 0 | 0 | 0 | 1.411 | PASS |
| `test_prestage_freshness_gate.py` | unittest | 15 | 0 | 0 | 0 | 3.791 | PASS |
| `test_produce_exec_review_record.py` | unittest | 40 | 0 | 0 | 0 | 5.449 | PASS |
| `test_quota_governor.py` | pytest | 76 | 0 | 0 | 0 | 3.414 | PASS |
| `test_quota_pressure_stats.py` | pytest | 15 | 0 | 0 | 0 | 0.363 | PASS |
| `test_quota_wall_doctrine.py` | pytest | 24 | 0 | 0 | 0 | 1.097 | PASS |
| `test_quota_window_probe.py` | unittest | 111 | 0 | 0 | 0 | 10.495 | PASS |
| `test_read_freshness_probe.py` | unittest | 4 | 0 | 0 | 0 | 0.893 | PASS |
| `test_rearm_on_touch.py` | pytest | 16 | 0 | 0 | 0 | 1.252 | PASS |
| `test_reconcile_execute_plan_handoff.py` | unittest | 30 | 0 | 0 | 0 | 5.749 | PASS |
| `test_reconcile_post_landing.py` | unittest | 82 | 0 | 0 | 0 | 44.905 | PASS |
| `test_rejected_archive_lifecycle.py` | unittest | 4 | 0 | 0 | 0 | 0.553 | PASS |
| `test_release_skill_selftest.py` | unittest | 75 | 0 | 0 | 0 | 124.015 | PASS |
| `test_reverse_squash_guard.py` | unittest | 127 | 0 | 0 | 0 | 39.749 | PASS |
| `test_revert_set_classifier.py` | unittest | 22 | 0 | 0 | 0 | 6.467 | PASS |
| `test_review_agent_doors.py` | unittest | 16 | 0 | 0 | 0 | 0.060 | PASS |
| `test_review_agent_normative_example_selection.py` | unittest | 6 | 0 | 0 | 0 | 0.055 | PASS |
| `test_review_contract_impact_closure.py` | unittest | 5 | 0 | 0 | 0 | 0.083 | PASS |
| `test_review_landing_receipt.py` | pytest | 12 | 0 | 0 | 0 | 0.786 | PASS |
| `test_review_record_selection.py` | unittest | 93 | 0 | 0 | 0 | 16.709 | PASS |
| `test_review_retention.py` | unittest | 11 | 0 | 0 | 0 | 1.214 | PASS |
| `test_review_thread_gate.py` | unittest | 23 | 0 | 0 | 0 | 1.350 | PASS |
| `test_runtime_capabilities.py` | unittest | 5 | 0 | 0 | 0 | 0.068 | PASS |
| `test_skill_description_length.py` | pytest | 10 | 0 | 0 | 0 | 0.680 | PASS |
| `test_skill_distribution_check.py` | pytest | 16 | 0 | 0 | 0 | 1.533 | PASS |
| `test_skill_text_budget.py` | unittest | 7 | 0 | 0 | 0 | 0.609 | PASS |
| `test_skill_text_duplication.py` | unittest | 12 | 0 | 0 | 0 | 0.569 | PASS |
| `test_squash_tree_equality.py` | unittest | 4 | 0 | 0 | 0 | 1.346 | PASS |
| `test_stack_primary_placement.py` | unittest | 9 | 0 | 0 | 0 | 0.059 | PASS |
| `test_staged_scope_guard.py` | unittest | 6 | 0 | 0 | 0 | 1.790 | PASS |
| `test_step31_record_validation_gate.py` | unittest | 21 | 0 | 0 | 0 | 0.206 | PASS |
| `test_sync_runtime_scripts.py` | unittest | 20 | 0 | 0 | 0 | 2.702 | PASS |
| `test_tool_runtime_stats.py` | unittest | 46 | 0 | 0 | 0 | 1.117 | PASS |
| `test_worktree_closeout_migrate.py` | unittest | 439 | 0 | 0 | 0 | 131.799 | PASS |

### Residual cost profile

The ten longest suites used 1,489.7 seconds, about 85.2% of this run's summed per-suite wall time. `test_done_run_wrapper.py` alone used 692.935 seconds (39.7%). The next largest were `test_worktree_closeout_migrate.py` at 131.799 seconds, `test_release_skill_selftest.py` at 124.015 seconds, `test_done_sweep_gates_lib.py` at 108.449 seconds, `test_corrections_record.py` at 108.243 seconds, `test_execution_claim.py` at 93.452 seconds, `test_land_squash.py` at 88.400 seconds, `test_docs_branch_sync.py` at 53.569 seconds, `test_reconcile_post_landing.py` at 44.905 seconds, and `test_check_prompt_log_origins.py` at 43.910 seconds.

`/usr/bin/time -l` wrapped each suite, capturing elapsed time, user/system CPU, memory, and process counts; pytest suites also wrote JUnit XML. No profiler was enabled during the complete run. Summed user and system CPU was 1,213.82 seconds against 1,747.875 seconds wall. This leaves 534.06 seconds that includes blocking waits, subprocess coordination, filesystem and Git work, and scheduling. CPU totals alone do not separate Python test logic from child-process work. The wrapper suite's own recorded usage was 261.09 seconds user and 252.51 seconds system against 692.935 seconds wall (263 test methods); both CPU and non-CPU time are substantial there.

Focused diagnostics after the baseline (not another complete-suite run):

- Five bare interpreter launches (`python3 -c pass`) took 0.0190–0.0298 seconds; median 0.0202 seconds. This measures process startup only, not Python collection or the full suite.
- Three `pytest --collect-only` runs for `scripts/test_quota_pressure_stats.py` collected 15 tests in 0.17, 0.17, and 0.20 seconds externally (median 0.17 seconds). Pytest reported 0.01 seconds for collection itself. These are a small function-suite sample, not an estimate for all 88 files.
- Three unprofiled and three cProfile-instrumented runs of the single `DoneRunSetupTest.test_happy_path_writes_marker_manifest_and_exports` test took 0.83–1.00 seconds and 0.84–0.96 seconds externally, respectively. Medians were 0.92 and 0.90 seconds; the ranges overlap, so this small sample does not quantify a reliable cProfile overhead. In one cProfile trace, eight `subprocess.run` calls accumulated 0.873 seconds, subprocess communication 0.859 seconds, and selector polling 0.795 seconds; fixture Git initialization accounted for about 0.090 seconds. This specific case spends most of its elapsed time waiting for subprocesses, but it is one representative path and not a profile of every slow test.
- Test instrumentation in the baseline was limited to `/usr/bin/time -l`, JUnit output for the 15 pytest suites, and per-suite stdout/stderr capture. Their incremental cost was not independently measured.

The profile points first toward the measured large suites and process/subprocess boundaries, while leaving the exact wait, Git, filesystem, and interpreter shares uncertain. Bare Python startup is small in the sampled cases, but this does not rule out aggregate Python collection or interpreter work across the full inventory. Process-level parallelism remains the first option to test, using independent high-cost suites, explicit worker/resource bounds, full failure propagation, and repeated isolation checks. This baseline intentionally ran serially and provides no parallel speedup evidence. Startup reuse, caching, and Go/Rust alternatives remain unmeasured; a language prototype should wait for evidence that Python-specific work is material.

### What the previous optimization evidence establishes

The accepted prior run remains **44.10% lower** than its 3,643.556-second baseline, with a final serial total of 2,036.658 seconds. Its useful measured changes were per-case `HOME`/`XDG_CONFIG_HOME` isolation and test-only lock timing pins in the dominant wrapper fixture, plus a landing-suite mixin that retained all 65 unique methods while removing 114 repeated inherited executions. Those changes reduced host-specific work and exact duplicate executions without replacing the tested process, Git, filesystem, and lock behavior.

The prior standalone home-isolation experiment was slower when it retained default wait/grace settings; the result does not show that home isolation itself is harmful. The other 86 suites summed to 50.367 seconds more in the old comparison, but the evidence does not establish causality or a regression. Parallel execution, startup reuse, caching, and alternate-language cost were not measured.

### Original completion conditions

The accepted 44.10% remains interim. The original **50% reduction condition remains unmet**, and the alternative condition that further reduction would unacceptably harm coverage or reliability also remains **unestablished**. This new 1,748.107-second observation is numerically below the historical 1,821.778-second 50% threshold, but the changed runner and unpaired shared-host conditions prevent treating it as a comparable final candidate run. No candidate has yet completed the plan's selection rule.

## Task 2: Focused process parallelism and startup reuse experiments

### Selection and method

The pilot paired two focused cases with different purposes: `scripts/test_done_run_wrapper.py::DoneRunSetupTest.test_happy_path_writes_marker_manifest_and_exports` came from the dominant 692.935-second suite and was the case directly profiled for subprocess and Git activity; `scripts/test_execution_claim.py::TestExecutionClaim.test_conversion_refuses_without_provider_configuration` exercised claim refusal behavior in a separate 93.452-second suite. This was not a top-two suite selection: `test_worktree_closeout_migrate.py` took 131.799 seconds and was larger than `test_execution_claim.py`. The pairing was intended to sample a dominant wrapper path and a distinct claim-refusal path, not to rank all process-heavy candidates. The cases remained unchanged and do not alter the required suite inventory or runner policy. Each method was invoked separately with the documented `unittest` discovery runner and `-k` selecting exactly one method.

The serial control ran those two commands sequentially, each in a fresh Python process. The parallel pilot used a two-job process pool to run the same commands concurrently. The collector waited for every result, sorted outcomes by stable case label, and returned nonzero if any child failed. The predeclared resource acceptance bound was at most two test-runner processes, no more than 512 MiB peak resident memory for either worker, and no more than 1 GiB as the sum of the two workers' peak RSS values. The memory bound was checked from `/usr/bin/time -l`; it is an acceptance bound, not an OS-enforced limit. Fixture roots were compared before and after each run. The pre-run process scans did not show an unrelated child pytest, unittest, or suite-driver process before each timing batch. A later process-sequence audit found an otherwise-unclassified Python 3.15 process (`Python -u -`) still resident at snapshots from 00:38:05 through 00:42:12 UTC on 2026-11-08; its observed elapsed time grew from 23:04 to 27:11. At three snapshots it coincided with unrelated pytest runs of `test_release_skill_selftest.py`, `test_reverse_squash_guard.py`, and `test_worktree_closeout_migrate.py`. These captures establish long-lived host-side test activity, but do not show process parentage or identify which focused trials overlapped it. Per-trial contention therefore remains unknown. The 1-minute host load average ranged from 8.864 to 21.524 during measurements.

The exact per-case command shape was:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p test_done_run_wrapper.py -k test_happy_path_writes_marker_manifest_and_exports -v
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p test_execution_claim.py -k test_conversion_refuses_without_provider_configuration -v
```

`/usr/bin/time -l` wrapped each case command. Three paired repetitions ran with the same two case identities and settings. Wall time below is the focused pair duration; CPU is the sum of worker user/system CPU seconds. The load column is the 1-minute average at the start of that mode.

| Repetition | Serial wall (s) | Serial CPU user/system (s) | Parallel wall (s) | Parallel CPU user/system (s) | Reuse wall (s) | Reuse CPU user/system (s) | Load start, serial/parallel/reuse |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 2.512 | 0.778 / 0.802 | 2.698 | 0.904 / 1.554 | 2.197 | not captured | 10.955 / 8.864 / 12.297 |
| 2 | 2.388 | 0.785 / 0.766 | 1.578 | 0.776 / 0.763 | 1.875 | not captured | 19.312 / 21.524 / 18.081 |
| 3 | 2.235 | 0.799 / 0.797 | 1.278 | 0.794 / 0.797 | 2.074 | 0.675 / 0.677 | 14.692 / 15.517 / 16.943 |

Every serial and parallel case invocation reported `Ran 1 test`, `OK`, exit 0, and zero skips. Parallel peak RSS values by repetition were 96,321,536, 96,927,744, and 97,796,096 bytes when summing the two per-worker peaks. Every worker stayed below 512 MiB, every sum stayed below 1 GiB, all results were collected in deterministic label order, and fixture roots were unchanged after each mode. The parallel candidate met the declared worker and memory checks. Its outcomes and selected case coverage matched the serial controls.

### Selection result and failure propagation

The serial median was 2.388 seconds with a 0.277-second range. The parallel median was 1.578 seconds with a 1.420-second range. The 0.810-second median gain did not exceed the larger range (1.420 seconds), so the candidate fails the plan's selection rule. One parallel sample was slower than its serial control; the other two were faster. This is not a measured complete-suite reduction and does not justify advancing parallelism to the final complete-suite comparison.

A controlled collector probe ran one child that printed a marker and exited 7 beside a delayed child that printed a second marker and exited 0. The collector waited for and recorded both outputs, sorted them deterministically, and produced aggregate exit code 1. The probe passed. This demonstrates failure propagation and collection behavior for the temporary pilot; it does not validate a production runner change, and none was made.

### Startup reuse and cache disposition

A reversible same-interpreter pilot loaded the two selected test cases from their source modules and ran them sequentially in one Python 3.14.10 `unittest` process. All three repetitions ran both exact test identities successfully. The serial median was 2.388 seconds (range 0.277); same-process reuse median was 2.074 seconds (range 0.322). Its 0.314-second median gain did not exceed the larger range of 0.322 seconds.

The repository and test fixture state stayed separate: the execution-claim case created its own scratch primary and lock home, the done-run case created a different scratch repository and lock roots, their tests asserted their respective claim and manifest outcomes, the two fixture roots were distinct, and all temporary fixture roots were removed. The environment check failed on all three reuse repetitions. The pilot seeded a caller value for `EXECUTION_CLAIM_LOCK_HOME`; the execution-claim fixture replaces this variable with its own lock home, then its cleanup removes the variable instead of restoring the caller value. In repetition 3, per-case snapshots showed the environment differed after both cases, and the final value was unset. Separate-process serial and parallel runs contain this mutation within each child process. Same-interpreter reuse is therefore rejected on environment isolation even though the test assertions pass. No shared manifest or lock file remained because each case's state lived below its distinct temporary repository and both roots were cleaned.

A changed-input invalidation probe copied the wrapper test module outside the repository, appended a harmless comment to the copy, and compared SHA-256 fingerprints. The key changed from `46921e68c0217f3efd14c3d4a15c45874f41b9017d98f78488dea016b67714fa` to `8e3cd50d1b81b69f0192d479ada08cce54620dfed850175247c9a44b48fd1d68`; the tracked source stayed byte-identical and the temporary copy was removed. A source fingerprint can invalidate reuse when code changes, but result caching was rejected: these tests assert fresh repository, manifest, environment, and lock behavior, so cached passing outcomes would skip the behavior under test even with a correct code fingerprint.

### Recommendation and limits

Neither candidate passes the plan's statistical gate. Parallel process execution remains a possible future option, but these short samples vary too much under high and changing host load to recommend it or authorize a full-suite comparison. The later-discovered controller makes the comparison context less reliable; the records cannot assign its effect to any specific trial. Same-process startup reuse has a directly observed caller-environment leak and no gain beyond its run-to-run variation. The Task 1 profile attributes substantial subprocess calls and polling to the profiled wrapper case only; it did not profile the execution-claim case, so that attribution must not be generalized to both cases. Bare Python startup was about 0.0202 seconds in the small Task 1 sample, but neither aggregate Python collection nor interpreter work across the suite was isolated. The temporary pilots introduced no dependencies, source changes, runner changes, or retained cache. Any future parallel pilot should first account for long-lived test controllers and process trees, then repeat the focused comparison under lower, measured contention with resource limits enforced by the runner. No candidate was advanced, and Task 2 ran no complete suite.


## Task 3: Conditional language option and recommendation

### Language option disposition

The profile does not establish a material Python-specific hotspot. The only direct Python-startup probe recorded a median of about 0.0202 seconds; multiplying by the 88 suite launches gives about 1.78 seconds, under 1% of the 214.880-second gap between the accepted 2,036.658-second result and the original 50% target. This is an order-of-magnitude startup estimate, not a measured saving: raw startup samples were not retained, the current and historical suite runners differ, and the profile did not isolate Python collection and interpreter CPU across the complete inventory. The focused pytest collection sample was only one small function suite.

On this evidence, a Go or Rust prototype is not justified for this plan. This is a decision that no material language-specific cost has been demonstrated, not evidence that another language would be ineffective. A prototype would add a second implementation language, compiler/toolchain setup, cross-platform build and CI ownership, and a maintenance boundary for behavior currently exercised through Python test fixtures. No portability or build cost was measured, so this comparison is qualitative. Reconsider a prototype only after a repeatable profile attributes a meaningful portion of the remaining target gap to Python collection or interpreter work and defines semantic-parity cases before implementation.

### Candidate and full-suite decision

No Task 2 candidate passed the selection rule. The exact three-run summaries are:

| Candidate | Median | Range | Median gain over serial | Selection result |
|---|---:|---:|---:|---|
| Serial control | 2.388139 s | 0.276784 s | n/a | reference |
| Two-process parallel | 1.578428 s | 1.419996 s | 0.809711 s | reject: gain does not exceed the larger range |
| Same-interpreter reuse | 2.073690 s | 0.322041 s | 0.314449 s | reject: gain does not exceed the larger range; environment leak also fails isolation |

Caching was rejected because it would skip test behavior under changed repository, manifest, environment, or lock state. Although the parallel pilot met the declared worker and memory bounds and preserved failure collection, the timing rule failed. The reuse pilot also leaked the caller's `EXECUTION_CLAIM_LOCK_HOME` value. In addition, the later-discovered long-lived pytest controller was absent from the earlier child-process scans; timing records show high and variable load, but do not identify which trial overlapped the controller. The candidate comparison is therefore inconclusive about best-case parallel performance and still fails the plan's advancement rule.

Because no candidate qualifies, the conditional final complete-suite comparison was not run. The plan authorized that comparison only after a candidate passed its selection criteria. No test suite or benchmark was run in Task 3. The historical 44.10% reduction remains the accepted interim result; its original 50% condition is still unmet, while the alternative condition that further in-scope reduction would harm coverage or reliability is not established. The fresh 1,748.107-second baseline is not a comparable final candidate measurement because it used the current mixed runner policy and different shared-host conditions.

### Recommendation and stopping point

Stop this plan without changing the harness or launching a final candidate-comparison suite; the required execute-plan Phase 2 validation suite is separate and has passed. The evidence supports retaining the successful earlier changes: per-case home/configuration isolation and test-only lock timing pins reduced host-specific work, and the landing mixin removed 114 repeated inherited executions while keeping all 65 unique methods. The default-wait home-isolation variant was slower, the remaining 86-suite aggregate moved by 50.367 seconds without causal evidence, parallel and reuse did not clear the measured selection threshold, and caching would erase behavior under test. Aggregate Python-only work could not be separated from test and child-process work, so it did not meet the plan’s 5% evidence threshold for prototyping; this does not establish that the share is below 5%.

For a later optimization effort, first re-profile the dominant `test_done_run_wrapper.py` path with retained raw samples and explicit child-process attribution, and include `test_worktree_closeout_migrate.py` among candidate comparisons because it was the second-longest suite. A bounded parallelism follow-up should run only after its contention detector sees long-lived controllers as well as child pytest/unittest processes; compare repeated runs on a quieter host, keep full failure accounting, and require median gain to exceed observed variation. Consider Go or Rust only if profiling attributes at least 5% of comparable serial-suite time to Python-specific collection, interpreter, or process-startup work; if that share cannot be separated from test work or noise, treat it as unproven and do not prototype. Preserve the 88-suite inventory and every distinct process, Git, filesystem, lock, refusal, and failure-propagation signal. This is a measured stopping point for this plan, not proof that the residual 214.880-second target gap is irreducible.
