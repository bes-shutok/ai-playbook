# Test-suite runtime baseline and optimization choices

Baseline measured on 2026-11-07. The complete serial run took **3,643.556 seconds (60 minutes 43.6 seconds)**. All 88 discovered suites ran; four suites failed. This is a complete measured baseline, **not a passing baseline**. No optimization has been implemented in this report.

The runner reports 4,000 outcomes including subtests: 3,991 passing, eight failing and one skipped. Its XML contains 3,651 top-level test cases; the remaining 349 counted outcomes are subtests. The wrapper reports 263 passing cases and two passing subtests, and the landing suite reports 179 passing cases.

## Reproduction and environment

- Execution revision: `1933ba5f4c5b4a75a6a1948da34238ede9aa8782`. All 88 test-file SHA-256 values still match the recorded inventory after the run.
- Interpreter: Python 3.14.10; collector: pytest 9.1.1; host: macOS-26.6.2-arm64-arm-64bit-Mach-O, 12 logical CPUs. No dependency installation was performed.
- Sequence: sorted `scripts/test_*.py`, one independent pytest process per file, serially, without stopping on failure. There were no suite retries or omitted inventory entries.
- Timing: monotonic elapsed time from immediately before the first suite command until the last suite exits and its result is recorded. It includes pytest startup, per-case setup/teardown, child processes, waiting and result-file writes. Inventory/version discovery precedes that interval.
- Resource capture: `/usr/bin/time -l` around each suite; pytest `--durations=0` and JUnit XML. These lightweight instruments are identical inputs for the final comparison; focused profiler overhead is excluded from this baseline.
- Initial load averages: `15.995 / 15.202 / 13.628`; final: `8.795 / 10.403 / 10.902`. This is a shared-host observation, with no repeat-run confidence interval.
- The only untracked execution tool at launch was the benchmark driver under repository-root `tmp/`; tracked source files were unchanged.

For each inventory entry, run the following command with the documented test virtual environment prepended to `PATH`. Keep going after a nonzero result and record it. Enclose the entire sorted loop in one monotonic timer; summing rounded suite times is not the end-to-end measurement.

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" /usr/bin/time -l \
  python3 -m pytest "$suite" -q --durations=0 --junitxml="$output/$name.xml"
```

The exact argument arrays, inventory hashes, timestamps and environment are in [metadata](../../../.ai-playbook/metrics/test-suite-runtime-reduction/baseline/metadata.json), [append-only suite results](../../../.ai-playbook/metrics/test-suite-runtime-reduction/baseline/suite-results.jsonl), [sequence timing](../../../.ai-playbook/metrics/test-suite-runtime-reduction/baseline/summary.json), and [resource/outcome analysis](../../../.ai-playbook/metrics/test-suite-runtime-reduction/baseline/analysis.json). Raw per-suite stdout, stderr and XML share that baseline directory. The exact [baseline driver](../../../.ai-playbook/metrics/test-suite-runtime-reduction/provenance/test-suite-baseline.py), [focused experiment driver](../../../.ai-playbook/metrics/test-suite-runtime-reduction/provenance/test-suite-focused.py), and [Bash trace setup](../../../.ai-playbook/metrics/test-suite-runtime-reduction/provenance/bash-profile-env.sh) are retained as benchmark provenance rather than a new repository runner. Portable copies replace host repo, home, virtual-environment, installation and temporary-directory paths plus hostname with named placeholders. The [redaction/input-digest manifest](../../../.ai-playbook/metrics/test-suite-runtime-reduction/portable-evidence-manifest.json) binds each original input SHA-256 to its portable copy; original raw files remain in session storage until closeout. Counts, timings, test identities, revisions and failure evidence are retained.

## Dominant measured costs

| Suite | Wall seconds | Share of complete sequence |
|---|---:|---:|
| `test_done_run_wrapper.py` | 2330.721 | 63.97% |
| `test_land_squash.py` | 228.124 | 6.26% |
| `test_worktree_closeout_migrate.py` | 148.463 | 4.07% |
| `test_corrections_record.py` | 136.317 | 3.74% |
| `test_release_skill_selftest.py` | 131.600 | 3.61% |
| `test_done_sweep_gates_lib.py` | 101.481 | 2.79% |
| `test_execution_claim.py` | 94.721 | 2.60% |
| `test_docs_branch_sync.py` | 80.820 | 2.22% |
| `test_check_prompt_log_origins.py` | 55.511 | 1.52% |
| `test_reconcile_post_landing.py` | 43.136 | 1.18% |

The wrapper and landing suites together consumed 2,558.845 seconds, 70.23% of the sequence. Summed child resource measurements were 1,414.83 user CPU seconds and 945.47 system CPU seconds. The largest reported per-suite maximum resident set size was 209,977,344 bytes (200.25 MiB). CPU totals and maximum resident measurements are not additive wall time or a simultaneous whole-run memory peak.

### Test contributors

| Test | Recorded case seconds |
|---|---:|
| `DoneRunSetupTest.test_held_lock_refuses_with_lock_evidence_and_writes_nothing` | 93.593 |
| `DoneRunFinalizeTest.test_finalize_squash_proof_window_bound_pins_500_commit_scan` | 48.274 |
| `AnchorLegTest.test_resolution_scan_caps_history` | 43.687 |
| `DoneRunRollingLogRefBoundCommitTest.test_log_writer_waits_without_staging_while_consumer_holds` | 38.935 |
| `DoneRunRollingLogRefBoundCommitTest.test_done_consumer_refuses_before_mutation_while_log_write_holds` | 38.655 |
| `AnchorLegTest.test_resolution_scan_includes_candidate_400` | 31.694 |
| `DoneRunSetupTerminalReleaseTest.test_orphan_classification_stop_releases_and_reentry_holds` | 19.944 |
| `DoneRunSetupTerminalReleaseTest.test_unreadable_manifest_fail_closed_releases_the_acquired_lock` | 14.987 |
| `DoneRunSetupAdoptionTest.test_adopt_corrupt_boundary_fails_closed` | 14.177 |
| `DoneRunSetupManifestStateTest.test_adopted_newest_manifest_continues_with_state_named` | 14.104 |

### Attribution and focused experiments

Read-only process samples during the wrapper run observed `done_run.sh setup` invoking the runtime deployment advisory and `verify_runtime_deployment.py` against the real runtime home. The fixture pins `DONE_SWEEP_RUNTIME_HOME` but does not pin `HOME`; the advisory follows the user-facts resolution chain to the primary checkout. That repeats host deployment/import probes in tests whose assertions concern the wrapper protocol. Sampling was sparse and is not an exhaustive exclusive-time profile.

The unchanged wrapper fixture also inherits the production done-lock poll interval (30 seconds), short-agent wait (90 seconds) and dead-holder grace (five seconds). The 93.593-second held-lock test measures the resulting real contention path. Two other contention cases took 38.935 and 38.655 seconds. Any shortened fixture clocks must retain actual lock acquisition/refusal, preserve deliberately overridden clocks, and keep production defaults unchanged.

Focused experiments ran on the same unchanged test-file digest after the named external test process exited. Each command used the recorded virtual environment and selected only the nodes below. Fixture candidates were in-memory `runner_env` patches: `home` supplies a case-local HOME/XDG directory; `timing` supplies poll=1s, agent wait=1s and dead-holder grace=0s; `combined` supplies both. Production code and test-file bytes were unchanged.

| Experiment | Selected cases | Wall seconds | Result |
|---|---|---:|---|
| Unchanged characterization | Happy setup + resume classification | 18.311 | 2 passed |
| Same pair, cProfile + Bash DEBUG side channel | Happy setup + resume classification | 19.042 | 2 passed |
| Home isolation only | Happy setup + resume classification | 33.857 | 2 passed |
| Short clocks only | Happy setup + resume classification | 18.523 | 2 passed |
| Combined candidate | Happy setup + resume classification | 3.118 | 2 passed |
| Combined candidate, same instrumentation | Happy setup + resume classification | 3.217 | 2 passed |
| Unchanged contention characterization | Held lock refuses with evidence and writes nothing | 94.582 | 1 passed |
| Short-clock contention candidate | Same real held-lock refusal case | 3.249 | 1 passed |

The targeted contention pair demonstrates the measured waiting cost while preserving the real holder, refusal, evidence and no-write assertions. It does not establish complete-suite improvement. The quick pair is an interaction/attribution witness, not a representative performance claim: clocks alone leave it effectively unchanged, and home isolation alone makes it slower. Faster isolated setup reaches the existing five-second dead-holder grace before it expires, which the 30-second poll rounds upward. The joint candidate removes the incidental host probe and this new wait; the combined trace contains zero verifier calls and zero sleep commands.

| Attributed surface in the unchanged instrumented pair | Measurement | Boundary |
|---|---:|---|
| Fixture `setUp`, two cases | 0.002s cumulative | Temporary-tree creation and environment preparation. |
| Repository initialization, two cases | 0.262s cumulative | Includes ten direct Git launches totaling about 0.258s; filesystem writes are inside this fixture cost. |
| Real wrapper setup, three invocations | 18.483s cumulative | Shell, child startup, deployment advisory, marker and manifest work; 97% of instrumented pair wall time. |
| Host verifier nested in those setup invocations | Three calls, coarse shell intervals 5s + 5s + 4s | Bash `SECONDS` has one-second granularity; this is attribution, not an exclusive high-resolution subtotal. The joint candidate makes zero such calls and its three setup invocations total 2.819s. |
| Direct child creation, seventeen launches | 0.043s cumulative in `Popen._execute_child` | Excludes startup performed by nested shell/verifier children; already contained in command totals. |
| Test-method Python bodies | Less than 0.001s exclusive across the pair | Assertions/orchestration outside the measured child calls. |
| Cleanup, two cases | 0.052s cumulative | Real chmod/remove operations. |
| Waiting/contention | 94.582s unchanged versus 3.249s short-clock selected case | The separate held-lock case isolates the configured wait path; no lock behavior is mocked. |

These overlapping call-boundary measurements must not be added as exclusive full-run percentages. Profiling overhead is separated: the unchanged instrumented pair is 0.730s (4.0%) above its uninstrumented pair; the instrumented joint pair is 0.099s above its uninstrumented pair. These are single observed deltas with host noise, not calibrated confidence intervals. Focused load averages ranged from about 5.55 to 17.20 during the experiments, so no full-suite extrapolation is justified. Exact nodes, arguments, source hashes, loads, outputs, shell traces and profile statistics are in the [focused analysis](../../../.ai-playbook/metrics/test-suite-runtime-reduction/profiling/analysis.json) and neighboring experiment directories.

## Option decisions

| Option | Evidence and disposition | Coverage, reliability, portability and maintenance |
|---|---|---|
| Fixture refactoring | Select the joint fixture correction for Task 2: isolate each wrapper case's HOME/XDG inputs together with test-only lock clocks. Standalone home isolation is rejected by the measured grace/poll regression. The wrapper is 63.97% of full wall time, process samples show repeated host advisory probes, and contention cases expose default waits. | Preserve real subprocess/Git/lock boundaries and case-local mutable state. Dedicated home/clock overrides must still run. Standard environment pins are portable; avoid replacing production guards. The measured contention pair and paired call attribution support the choice; complete-wrapper and complete-suite improvement remain unmeasured. |
| Removal/consolidation | Select exact inherited repetitions for characterization: the landing suite collects 179 cases from 65 unique test methods. Two subclasses each repeat the concrete base's 57 tests. | Retain every unique method and all three concrete classes; share a helper-only mixin. No collection suppression, skip marker or dynamic method deletion. Explicit mapping is required before removing 114 duplicate executions. |
| Bounded parallelism | Unmeasured; do not select while serial fixture corrections address the dominant cost. | Ambient process-environment mutation and lock tests make same-process threads unsafe without redesign. A future process-based proposal needs bounded resource use, complete failure accounting and three repeated isolation runs; no claim it is ineffective. |
| Process/startup reuse | Unmeasured beyond the observed repeated advisory invocations; prefer removing accidental host work before persisting a runner process. | Real shell/Python process boundaries are regression signals. Reusing a production runner would change lifecycle/ownership semantics; maintenance cost and cross-platform process behavior need separate evidence. |
| Caching | Unmeasured; no cache selected. Repeated advisory work arises from ambient input resolution, so input isolation is the narrower candidate. | Mutable repositories, manifests and lock generations remain per case. Any future immutable-input cache needs invalidation and mutation-isolation witnesses. |
| Changed-scope selection | Rejected as the claimed full-suite optimization: selecting fewer unrelated suites does not reduce cost of the same complete inventory. | Ordinary focused validation policy remains unchanged. Useful operator selection is distinct from retaining every complete-suite regression signal; no runner or policy change is included. |
| Go/Rust ports or replacement runner | Unmeasured implementation follow-up, outside this plan. The observed external advisory/wait work is a Python-language-independent target. | A port must demonstrate semantic parity, boundary coverage, portability and a maintenance advantage after measuring residual startup/CPU cost. No claim that a port cannot help. |

## Proposed landing coverage accounting

The complete baseline JUnit records all 179 landing identities. AST inspection finds 57 test methods on `LandSquashHelperTest`, four additional methods on `ReconcileTailGateTest`, and four on `LandLockOwnershipTest`. The two subclasses override neither the base test bodies nor its setup/helpers. Each inherited repetition therefore has an existing concrete base-class witness with the same body and fixture behavior.

The [57-row proposed mapping](../../../.ai-playbook/metrics/test-suite-runtime-reduction/baseline/landing-inheritance-map.json) names each retained concrete test ID, both duplicate collected IDs, the source line and method-body digest. It accounts for 114 proposed removed executions and retains all 65 unique methods. This is a proposal only; Task 2 owns implementation and Task 3 must reconcile final collection and retained assertions.

## Baseline failures and skip

These failures predate any optimization in this run. They are retained as comparison inputs; they do not become passing results through filtering or an elapsed-time improvement.

| Suite | Failing case(s) | Observed failure |
|---|---|---|
| `test_invocation_telemetry.py` | `test_finalize_no_ledger_closeout_appends_one_closeout_line`; `test_finalize_no_landing_cost_closeout_appends_one_closeout_line`; `test_finalize_landing_bearing_keeps_landing_cost_line_beside_closeout`; `test_finalize_no_manifest_closeout_appends_one_closeout_line`; `test_finalize_telemetry_failure_leaves_contract_and_landing_cost_intact` | Exact-output snapshots omit the finalization marker emitted by the unchanged runner. |
| `test_learn_router_dispatch.py` | `DispatchParityTest.test_module_headings_byte_identical` | The step-completion heading snapshot omits the capture-freshness subsection. |
| `test_machinery_inventory.py` | `RealTreeCheck.test_real_tree_checks_green` | Inventory check reports unregistered `scripts/maintenance_fire_outcomes.py`. |
| `test_quota_governor.py` | `test_version_skew_fails_closed` | The unknown-runtime reason precedes the expected future-schema reason in this invocation environment. |

The sole skip is `DocsBranchSyncTests.test_intermediate_symlink_then_parent_traversal_refuses_without_ref_change`: its fixture symlink creation raised ENOENT, which the test labels unavailable. This does not establish that host symlinks are generally unavailable. The final run must account for this same skip and any changed failures separately.

## Complete measured inventory

Counts below are JUnit-reported outcomes including subtests. Status is the actual per-suite process exit; no row is omitted for failure.

| Suite under `scripts/` | Wall seconds | Outcomes | Failures | Skips | Exit |
|---|---:|---:|---:|---:|---:|
| `test_authoring_continuation_ownership.py` | 0.328 | 9 | 0 | 0 | 0 |
| `test_authoring_plans_liveness.py` | 2.270 | 13 | 0 | 0 | 0 |
| `test_authoring_raced_pick_continuation.py` | 0.252 | 9 | 0 | 0 | 0 |
| `test_base_reflog_audit.py` | 8.894 | 14 | 0 | 0 | 0 |
| `test_budget_guard_hooks.py` | 3.384 | 24 | 0 | 0 | 0 |
| `test_check_backlog_claimed.py` | 1.776 | 13 | 0 | 0 | 0 |
| `test_check_investigate_entries.py` | 4.667 | 2 | 0 | 0 | 0 |
| `test_check_lesson_scope.py` | 2.998 | 38 | 0 | 0 | 0 |
| `test_check_no_em_dash.py` | 1.143 | 6 | 0 | 0 | 0 |
| `test_check_plan_origins_closed.py` | 7.726 | 91 | 0 | 0 | 0 |
| `test_check_prompt_log_origins.py` | 55.511 | 108 | 0 | 0 | 0 |
| `test_check_review_agent_portability.py` | 1.091 | 12 | 0 | 0 | 0 |
| `test_check_run_continuity.py` | 3.503 | 12 | 0 | 0 | 0 |
| `test_claimed_target_skip_and_continue.py` | 0.199 | 7 | 0 | 0 | 0 |
| `test_code_delta_classifier.py` | 8.327 | 22 | 0 | 0 | 0 |
| `test_codex_budget_reset_guard.py` | 1.151 | 7 | 0 | 0 | 0 |
| `test_codex_hook_config.py` | 0.203 | 2 | 0 | 0 | 0 |
| `test_codex_model_guard.py` | 1.356 | 8 | 0 | 0 | 0 |
| `test_codex_model_guard_probe.py` | 0.835 | 12 | 0 | 0 | 0 |
| `test_corrections_record.py` | 136.317 | 92 | 0 | 0 | 0 |
| `test_debugging_lesson_recall.py` | 0.284 | 4 | 0 | 0 | 0 |
| `test_deploy_runtime_helpers.py` | 17.915 | 28 | 0 | 0 | 0 |
| `test_dirt_regression_gate.py` | 18.730 | 54 | 0 | 0 | 0 |
| `test_dispatch_admission.py` | 0.964 | 13 | 0 | 0 | 0 |
| `test_docs_branch_sync.py` | 80.820 | 82 | 0 | 1 | 0 |
| `test_done_router_dispatch.py` | 0.396 | 6 | 0 | 0 | 0 |
| `test_done_run_wrapper.py` | 2330.721 | 265 | 0 | 0 | 0 |
| `test_done_sweep_gates_lib.py` | 101.481 | 474 | 0 | 0 | 0 |
| `test_done_sweep_gates_wrapper.py` | 4.042 | 9 | 0 | 0 | 0 |
| `test_execute_plan_precondition_cli.py` | 1.532 | 20 | 0 | 0 | 0 |
| `test_execute_plan_referral_contract.py` | 0.173 | 54 | 0 | 0 | 0 |
| `test_execute_plan_resume_watcher.py` | 1.604 | 80 | 0 | 0 | 0 |
| `test_execute_plan_worktree_bootstrap.py` | 1.895 | 5 | 0 | 0 | 0 |
| `test_execution_claim.py` | 94.721 | 107 | 0 | 0 | 0 |
| `test_fix_plan_em_dashes.py` | 0.847 | 7 | 0 | 0 | 0 |
| `test_friction_audit_quant.py` | 0.256 | 6 | 0 | 0 | 0 |
| `test_gate_liveness_ledger.py` | 2.430 | 27 | 0 | 0 | 0 |
| `test_gate_liveness_wiring.py` | 0.237 | 5 | 0 | 0 | 0 |
| `test_harness_detection.py` | 0.750 | 12 | 0 | 0 | 0 |
| `test_harness_policy_contract.py` | 0.238 | 9 | 0 | 0 | 0 |
| `test_hooks_probe.py` | 0.173 | 1 | 0 | 0 | 0 |
| `test_invocation_telemetry.py` | 27.499 | 24 | 5 | 0 | 1 |
| `test_land_squash.py` | 228.124 | 179 | 0 | 0 | 0 |
| `test_landing_parentage_gate.py` | 7.672 | 29 | 0 | 0 | 0 |
| `test_learn_router_dispatch.py` | 0.424 | 8 | 1 | 0 | 1 |
| `test_lessons_recovery_contract.py` | 0.185 | 8 | 0 | 0 | 0 |
| `test_machinery_inventory.py` | 8.722 | 25 | 1 | 0 | 1 |
| `test_maintenance_fire_outcomes.py` | 3.223 | 43 | 0 | 0 | 0 |
| `test_maintenance_runtime_scope.py` | 0.164 | 18 | 0 | 0 | 0 |
| `test_parallel_work_regressions.py` | 1.363 | 3 | 0 | 0 | 0 |
| `test_plan_delta_classifier.py` | 4.190 | 40 | 0 | 0 | 0 |
| `test_plan_readiness.py` | 22.950 | 260 | 0 | 0 | 0 |
| `test_plan_review_boundary_examples.py` | 0.272 | 8 | 0 | 0 | 0 |
| `test_plan_shape.py` | 0.257 | 21 | 0 | 0 | 0 |
| `test_plan_task_span.py` | 1.065 | 14 | 0 | 0 | 0 |
| `test_prestage_freshness_gate.py` | 2.952 | 15 | 0 | 0 | 0 |
| `test_produce_exec_review_record.py` | 3.837 | 40 | 0 | 0 | 0 |
| `test_quota_governor.py` | 3.280 | 76 | 1 | 0 | 1 |
| `test_quota_pressure_stats.py` | 0.298 | 15 | 0 | 0 | 0 |
| `test_quota_wall_doctrine.py` | 0.923 | 24 | 0 | 0 | 0 |
| `test_quota_window_probe.py` | 10.878 | 147 | 0 | 0 | 0 |
| `test_read_freshness_probe.py` | 1.027 | 4 | 0 | 0 | 0 |
| `test_rearm_on_touch.py` | 1.325 | 16 | 0 | 0 | 0 |
| `test_reconcile_execute_plan_handoff.py` | 4.973 | 35 | 0 | 0 | 0 |
| `test_reconcile_post_landing.py` | 43.136 | 82 | 0 | 0 | 0 |
| `test_rejected_archive_lifecycle.py` | 0.705 | 4 | 0 | 0 | 0 |
| `test_release_skill_selftest.py` | 131.600 | 75 | 0 | 0 | 0 |
| `test_reverse_squash_guard.py` | 42.323 | 127 | 0 | 0 | 0 |
| `test_revert_set_classifier.py` | 7.567 | 22 | 0 | 0 | 0 |
| `test_review_agent_doors.py` | 0.226 | 16 | 0 | 0 | 0 |
| `test_review_agent_normative_example_selection.py` | 0.197 | 6 | 0 | 0 | 0 |
| `test_review_contract_impact_closure.py` | 0.191 | 5 | 0 | 0 | 0 |
| `test_review_landing_receipt.py` | 0.825 | 12 | 0 | 0 | 0 |
| `test_review_record_selection.py` | 16.866 | 93 | 0 | 0 | 0 |
| `test_review_retention.py` | 1.243 | 11 | 0 | 0 | 0 |
| `test_review_thread_gate.py` | 1.461 | 23 | 0 | 0 | 0 |
| `test_runtime_capabilities.py` | 0.187 | 5 | 0 | 0 | 0 |
| `test_skill_description_length.py` | 0.614 | 10 | 0 | 0 | 0 |
| `test_skill_distribution_check.py` | 1.688 | 16 | 0 | 0 | 0 |
| `test_skill_text_budget.py` | 0.764 | 7 | 0 | 0 | 0 |
| `test_skill_text_duplication.py` | 0.692 | 12 | 0 | 0 | 0 |
| `test_squash_tree_equality.py` | 1.447 | 4 | 0 | 0 | 0 |
| `test_stack_primary_placement.py` | 0.169 | 36 | 0 | 0 | 0 |
| `test_staged_scope_guard.py` | 1.785 | 6 | 0 | 0 | 0 |
| `test_step31_record_validation_gate.py` | 0.323 | 59 | 0 | 0 | 0 |
| `test_sync_runtime_scripts.py` | 2.467 | 20 | 0 | 0 | 0 |
| `test_tool_runtime_stats.py` | 0.808 | 46 | 0 | 0 | 0 |
| `test_worktree_closeout_migrate.py` | 148.463 | 482 | 0 | 0 | 0 |

## Comparison limits and next step

A single before/after pair on a shared host cannot establish a statistical confidence interval. The baseline begins under higher load than it ends. Its incidental deployment advisory can observe peer landings in the primary checkout; a read-only sample observed primary HEAD movement while the execution worktree and all 88 test-file hashes stayed fixed. Isolating that ambient input is an intended fixture correction, not a reason to mislabel the baseline as hermetic.

Proceed only with explicit failure/skip and inventory accounting. Candidate measurements must distinguish unchanged characterization, instrumented profiling and in-memory fixture experiments. Neither candidate timing nor deletion of duplicate collection establishes the final full-suite speedup. The final report must compare the complete normalized inventory, disclose new or changed failures, and preserve every unique regression signal.
