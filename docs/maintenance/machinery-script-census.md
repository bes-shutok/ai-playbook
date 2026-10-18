# Machinery script census and hot-spot inventory

Census date: 2026-10-13. Measured on the machinery-script-refactor program's execution branch at base main 383014959. Every number is a mechanical read of that tree (wc -l, definition regex counts, git log --since counts, direct span reads). Plan origin: docs/history/plans/2026-10-13-machinery-script-refactor-program.md (Task 1); backlog origin: docs/history/backlog/2026-10-13-machinery-script-refactor-census.md. This document is read-only inventory: no behavior change, and no gate is proposed anywhere in it.

## 1. Method: spot measurement where live telemetry is absent

There is no script-runtime telemetry writer today: per-script invocation frequency and wall time are unmeasured, that writer is its own plan (the script-runtime-cost-telemetry entry), and this census depends on it. Until it lands, every number here is a spot measurement taken by these mechanical means:

1. Size: wc -l over every .py and .sh file under scripts/ (162 files, 159,136 lines).
2. Function counts: regex count of def statements for python (indented or top level), and of shell function definitions (name() followed by a brace, or a function declaration, at line start).
3. Churn: git log --since commit counts per file over 30-day and 90-day windows. Caveat: a window also counts touches to files deleted inside the window; the churn table in section 3 lists existing files only.
4. Duplication: no script-corpus duplication tooling exists; scripts/skill_text_duplication.py is Markdown-scoped and does not apply to scripts. Duplication depth is measured only for the two clusters witnessed in origin rows, by direct span reads, plus one named spot measurement (section 3.3).
5. Outcome-contract adoption: register rows read from scripts/OUTCOME_CONTRACT.md, plus a mechanical grep for OUTCOME: emission per file.

When the telemetry plan lands, section 4's priority order must be re-ranked on invocation frequency and wall time; until then it rides size, churn, and witnessed duplication.

## 2. Mechanical inventory: every script under scripts/

162 scripts, 159,136 lines total. Columns: lines (wc -l), functions (counting rules in section 1), outcome-contract adoption. Adoption classes:

- row: migrated / row: born-conformant: the script carries an assumptions row in scripts/OUTCOME_CONTRACT.md. 27 files: 15 migrated, 12 born-conformant; the reverse_squash_guard.py and worktree_closeout_migrate.py rows are subcommand-scoped.
- emits OUTCOME, no row: the script prints the final OUTCOME: line but has no register row (6 files, plus run_plan_gates.sh which also acts as a contract caller). The register's own note keeps them outside the contract until their rows land.
- contract caller: the script branches on a child script's OUTCOME line without speaking the contract itself (2 files).
- exempt (probe) / exempt (report): read-only observation and telemetry scripts that classify or gate nothing (9 files; explicit decisions in section 2.1).
- exempt (library module): imported helper modules with no CLI gate of their own (8 files).
- exempt (test harness): test_ files; they assert other scripts' outcomes and sit outside the contract by design (78 files).
- no register row (legacy exits): decision-shaped checks and record- or ops-management CLIs still on their documented legacy exit semantics (31 files).

| Script | Lines | Functions | Outcome-contract adoption |
| --- | --- | --- | --- |
| `scripts/validate_review_staging.py` | 18110 | 255 | row: migrated |
| `scripts/test_done_sweep_gates_lib.py` | 11210 | 340 | none: exempt (test harness) |
| `scripts/summarize_review_stats.py` | 8996 | 213 | none: no register row (legacy exits) |
| `scripts/plan_readiness.py` | 7973 | 94 | row: migrated |
| `scripts/done_sweep_gates_lib.py` | 7650 | 154 | row: migrated (lib of the pair) |
| `scripts/check_maintenance_pins.sh` | 3710 | 14 | row: migrated |
| `scripts/skill_gate.py` | 3257 | 43 | none: no register row (legacy exits) |
| `scripts/test_plan_readiness.py` | 3150 | 150 | none: exempt (test harness) |
| `scripts/execute_plan_resume_watcher.py` | 2982 | 103 | none: no register row (legacy exits) |
| `scripts/doc_registry_validator.py` | 2695 | 36 | none: no register row (legacy exits) |
| `scripts/done-lock.sh` | 2633 | 41 | row: migrated |
| `scripts/test_quota_window_probe.py` | 2594 | 124 | none: exempt (test harness) |
| `scripts/test_worktree_closeout_migrate.py` | 2578 | 147 | none: exempt (test harness) |
| `scripts/lessons_migrate.py` | 2537 | 38 | none: no register row (legacy exits) |
| `scripts/test_reverse_squash_guard.py` | 2530 | 145 | none: exempt (test harness) |
| `scripts/worktree_closeout_migrate.py` | 2344 | 64 | row: born-conformant (gate-removal and sweep subcommands) |
| `scripts/check_backlog_inbox_location.py` | 2259 | 43 | none: no register row (legacy exits) |
| `scripts/review_usage_capture.py` | 2239 | 60 | none: no register row (legacy exits) |
| `scripts/test_review_record_selection.py` | 2132 | 75 | none: exempt (test harness) |
| `scripts/test_execute_plan_resume_watcher.py` | 2047 | 116 | none: exempt (test harness) |
| `scripts/lessons_recall.py` | 1871 | 28 | none: no register row (legacy exits) |
| `scripts/reverse_squash_guard.py` | 1832 | 65 | row: born-conformant (check-claim-fence subcommand only) |
| `scripts/test_check_plan_origins_closed.py` | 1608 | 110 | none: exempt (test harness) |
| `scripts/test_release_skill_selftest.py` | 1512 | 80 | none: exempt (test harness) |
| `scripts/test_docs_branch_sync.py` | 1344 | 89 | none: exempt (test harness) |
| `scripts/done_run.sh` | 1252 | 19 | contract caller (parses child OUTCOME line) |
| `scripts/review_record_selection.py` | 1244 | 20 | none: exempt (library module) |
| `scripts/corrections_record.py` | 1223 | 51 | row: born-conformant |
| `scripts/quota_window_probe.py` | 1202 | 37 | none: exempt (probe) |
| `scripts/test_land_squash.py` | 1178 | 55 | none: exempt (test harness) |
| `scripts/check_plan_origins_closed.py` | 1151 | 27 | row: migrated |
| `scripts/review_retention.py` | 1145 | 34 | none: no register row (legacy exits) |
| `scripts/code_delta_classifier.py` | 1142 | 43 | row: born-conformant |
| `scripts/test_tool_runtime_stats.py` | 1115 | 71 | none: exempt (test harness) |
| `scripts/land_squash.sh` | 1113 | 14 | row: born-conformant |
| `scripts/test_execution_claim.py` | 1091 | 54 | none: exempt (test harness) |
| `scripts/test_check_prompt_log_origins.py` | 1088 | 42 | none: exempt (test harness) |
| `scripts/tool_runtime_stats.py` | 954 | 42 | none: exempt (report) |
| `scripts/hooks_probe.py` | 947 | 37 | none: exempt (probe) |
| `scripts/test_done_run_wrapper.py` | 940 | 53 | none: exempt (test harness) |
| `scripts/test_reconcile_post_landing.py` | 918 | 55 | none: exempt (test harness) |
| `scripts/execution_claim.sh` | 905 | 34 | row: born-conformant |
| `scripts/check_prompt_log_origins.py` | 904 | 23 | emits OUTCOME, no row |
| `scripts/facts_paths.py` | 876 | 17 | none: exempt (library module) |
| `scripts/docs_branch_sync.sh` | 863 | 1 | none: no register row (legacy exits) |
| `scripts/scan-public-hygiene.sh` | 858 | 16 | row: migrated |
| `scripts/plan_delta_classifier.py` | 844 | 33 | row: born-conformant |
| `scripts/test_corrections_record.py` | 777 | 32 | none: exempt (test harness) |
| `scripts/test_plan_delta_classifier.py` | 711 | 34 | none: exempt (test harness) |
| `scripts/test_budget_guard_hooks.py` | 706 | 41 | none: exempt (test harness) |
| `scripts/check_cleanup_scope_baseline.py` | 697 | 10 | row: migrated |
| `scripts/test_review_retention.py` | 666 | 26 | none: exempt (test harness) |
| `scripts/friction_audit_quant.py` | 643 | 24 | none: exempt (report) |
| `scripts/reconcile_post_landing.py` | 641 | 31 | none: no register row (legacy exits) |
| `scripts/test_quota_wall_doctrine.py` | 636 | 36 | none: exempt (test harness) |
| `scripts/test_code_delta_classifier.py` | 603 | 23 | none: exempt (test harness) |
| `scripts/test_landing_parentage_gate.py` | 599 | 41 | none: exempt (test harness) |
| `scripts/lessons_classify.py` | 575 | 12 | none: no register row (legacy exits) |
| `scripts/test_rearm_on_touch.py` | 574 | 23 | none: exempt (test harness) |
| `scripts/test_execute_plan_worktree_bootstrap.py` | 546 | 12 | none: exempt (test harness) |
| `scripts/test_check_lesson_scope.py` | 544 | 44 | none: exempt (test harness) |
| `scripts/quota_governor.py` | 498 | 21 | none: no register row (legacy exits) |
| `scripts/rearm_on_touch.py` | 485 | 19 | row: migrated |
| `scripts/test_dirt_regression_gate.py` | 476 | 41 | none: exempt (test harness) |
| `scripts/test_base_reflog_audit.py` | 443 | 24 | none: exempt (test harness) |
| `scripts/release-rewrite.sh` | 439 | 5 | contract caller (re-keys scanner exits) |
| `scripts/test_harness_policy_contract.py` | 436 | 15 | none: exempt (test harness) |
| `scripts/test_review_thread_gate.py` | 426 | 32 | none: exempt (test harness) |
| `scripts/confluence-mirror-hygiene.sh` | 422 | 9 | none: no register row (legacy exits) |
| `scripts/check_backlog_root_closure.py` | 417 | 6 | none: no register row (legacy exits) |
| `scripts/execute_plan_runtime.py` | 409 | 18 | none: exempt (library module) |
| `scripts/test_rejected_archive_lifecycle.py` | 408 | 14 | none: exempt (test harness) |
| `scripts/test_plan_shape.py` | 403 | 27 | none: exempt (test harness) |
| `scripts/check_authoring_plans_liveness.py` | 395 | 9 | row: born-conformant |
| `scripts/test_check_backlog_claimed.py` | 395 | 25 | none: exempt (test harness) |
| `scripts/test_plan_task_span.py` | 392 | 24 | none: exempt (test harness) |
| `scripts/test_friction_audit_quant.py` | 390 | 14 | none: exempt (test harness) |
| `scripts/lessons_index.py` | 385 | 7 | none: no register row (legacy exits) |
| `scripts/dirt_regression_gate.py` | 381 | 12 | row: migrated |
| `scripts/test_execute_plan_precondition_cli.py` | 375 | 12 | none: exempt (test harness) |
| `scripts/plan_shape.py` | 374 | 8 | none: exempt (library module) |
| `scripts/review_thread_gate.py` | 360 | 10 | row: migrated |
| `scripts/hooks_log_summary.py` | 355 | 11 | none: exempt (report) |
| `scripts/landing_parentage_gate.py` | 353 | 14 | row: migrated |
| `scripts/test_check_run_continuity.py` | 350 | 18 | none: exempt (test harness) |
| `scripts/test_deploy_runtime_helpers.py` | 349 | 17 | none: exempt (test harness) |
| `scripts/revert_set_classifier.py` | 341 | 14 | row: migrated |
| `scripts/test_parallel_work_regressions.py` | 339 | 13 | none: exempt (test harness) |
| `scripts/test_revert_set_classifier.py` | 339 | 29 | none: exempt (test harness) |
| `scripts/check_run_continuity.py` | 338 | 16 | row: born-conformant |
| `scripts/test_authoring_plans_liveness.py` | 338 | 20 | none: exempt (test harness) |
| `scripts/test_plan_review_boundary_examples.py` | 335 | 13 | none: exempt (test harness) |
| `scripts/test_done_sweep_gates_wrapper.py` | 328 | 21 | none: exempt (test harness) |
| `scripts/machinery_inventory.py` | 322 | 14 | none: exempt (report) |
| `scripts/test_quota_governor.py` | 314 | 27 | none: exempt (test harness) |
| `scripts/session_channel.py` | 309 | 8 | none: no register row (legacy exits) |
| `scripts/test_codex_model_guard_probe.py` | 309 | 17 | none: exempt (test harness) |
| `scripts/base_reflog_audit.py` | 305 | 8 | row: born-conformant |
| `scripts/test_sync_runtime_scripts.py` | 305 | 30 | none: exempt (test harness) |
| `scripts/lessons_adopt.py` | 298 | 8 | none: no register row (legacy exits) |
| `scripts/test_review_agent_doors.py` | 291 | 19 | none: exempt (test harness) |
| `scripts/test_learn_router_dispatch.py` | 290 | 15 | none: exempt (test harness) |
| `scripts/check_backlog_claimed.py` | 287 | 8 | none: no register row (legacy exits) |
| `scripts/test_docs_branch_step2_selector.py` | 285 | 21 | none: exempt (test harness) |
| `scripts/skill_distribution_check.py` | 273 | 9 | none: no register row (legacy exits) |
| `scripts/test_review_landing_receipt.py` | 272 | 16 | none: exempt (test harness) |
| `scripts/test_prestage_freshness_gate.py` | 271 | 22 | none: exempt (test harness) |
| `scripts/test_skill_distribution_check.py` | 270 | 20 | none: exempt (test harness) |
| `scripts/runtime_capabilities.py` | 261 | 9 | none: exempt (library module) |
| `scripts/release-authoring.sh` | 260 | 2 | none: no register row (legacy exits) |
| `scripts/check_investigate_entries.py` | 255 | 6 | none: no register row (legacy exits) |
| `scripts/test_machinery_inventory.py` | 253 | 31 | none: exempt (test harness) |
| `scripts/test_review_agent_normative_example_selection.py` | 250 | 10 | none: exempt (test harness) |
| `scripts/prestage_freshness_gate.py` | 249 | 13 | row: migrated |
| `scripts/check-no-em-dash.sh` | 247 | 5 | none: no register row (legacy exits) |
| `scripts/plan_task_span.py` | 244 | 10 | emits OUTCOME, no row |
| `scripts/test_fix_plan_em_dashes.py` | 230 | 10 | none: exempt (test harness) |
| `scripts/check_review_landing_receipt.py` | 229 | 7 | none: no register row (legacy exits) |
| `scripts/gate_liveness_ledger.py` | 226 | 10 | row: born-conformant |
| `scripts/codex_model_guard_probe.py` | 214 | 11 | none: exempt (probe) |
| `scripts/quota_pressure_stats.py` | 213 | 14 | none: exempt (report) |
| `scripts/skill_text_duplication.py` | 208 | 6 | emits OUTCOME, no row |
| `scripts/test_gate_liveness_ledger.py` | 195 | 17 | none: exempt (test harness) |
| `scripts/skill_text_budget.py` | 193 | 6 | emits OUTCOME, no row (warning-only tool) |
| `scripts/check_lesson_scope.py` | 190 | 7 | none: no register row (legacy exits) |
| `scripts/test_done_lock_holder_visibility.sh` | 189 | 5 | none: exempt (test harness) |
| `scripts/check_skill_description_length.py` | 188 | 7 | none: no register row (legacy exits) |
| `scripts/test_quota_pressure_stats.py` | 188 | 18 | none: exempt (test harness) |
| `scripts/sync_runtime_scripts.sh` | 186 | 3 | none: no register row (legacy exits) |
| `scripts/test_done_router_dispatch.py` | 185 | 11 | none: exempt (test harness) |
| `scripts/staged_scope_guard.py` | 184 | 6 | emits OUTCOME, no row (exit-2 indeterminate legacy shape) |
| `scripts/deploy_runtime_helpers.sh` | 178 | 2 | emits OUTCOME, no row |
| `scripts/test_harness_detection.py` | 176 | 15 | none: exempt (test harness) |
| `scripts/lessons_corpus.py` | 173 | 3 | none: exempt (library module) |
| `scripts/fix_plan_em_dashes.py` | 172 | 5 | row: born-conformant |
| `scripts/test_skill_text_duplication.py` | 160 | 15 | none: exempt (test harness) |
| `scripts/check_review_agent_portability.py` | 157 | 3 | none: no register row (legacy exits) |
| `scripts/run_plan_gates.sh` | 154 | 2 | emits OUTCOME, no row (also a contract caller) |
| `scripts/test_run_plan_gates.sh` | 154 | 2 | none: exempt (test harness) |
| `scripts/test_check_no_em_dash.py` | 150 | 9 | none: exempt (test harness) |
| `scripts/test_lessons_recovery_contract.py` | 148 | 8 | none: exempt (test harness) |
| `scripts/test_read_freshness_probe.py` | 147 | 11 | none: exempt (test harness) |
| `scripts/check-instruction-size.sh` | 139 | 4 | none: no register row (legacy exits) |
| `scripts/test_staged_scope_guard.py` | 134 | 13 | none: exempt (test harness) |
| `scripts/read_freshness_probe.py` | 127 | 3 | none: exempt (probe) |
| `scripts/test_squash_tree_equality.py` | 121 | 11 | none: exempt (test harness) |
| `scripts/lessons.py` | 119 | 2 | none: no register row (legacy exits) |
| `scripts/harness_detection.py` | 117 | 5 | none: exempt (library module) |
| `scripts/test_check_review_agent_portability.py` | 115 | 14 | none: exempt (test harness) |
| `scripts/test_skill_text_budget.py` | 109 | 9 | none: exempt (test harness) |
| `scripts/test_skill_description_length.py` | 95 | 8 | none: exempt (test harness) |
| `scripts/test_review_contract_impact_closure.py` | 90 | 6 | none: exempt (test harness) |
| `scripts/codex_hook_config.py` | 87 | 6 | none: exempt (library module) |
| `scripts/done_sweep_gates.sh` | 84 | 2 | row: migrated (runner of the pair) |
| `scripts/test_gate_liveness_wiring.py` | 84 | 6 | none: exempt (test harness) |
| `scripts/check_authoring_gist_sample.py` | 79 | 3 | none: no register row (legacy exits) |
| `scripts/test_codex_budget_reset_guard.py` | 79 | 5 | none: exempt (test harness) |
| `scripts/test_codex_model_guard.py` | 67 | 9 | none: exempt (test harness) |
| `scripts/test_runtime_capabilities.py` | 48 | 4 | none: exempt (test harness) |
| `scripts/test_check_investigate_entries.py` | 45 | 4 | none: exempt (test harness) |
| `scripts/test_codex_hook_config.py` | 36 | 2 | none: exempt (test harness) |
| `scripts/test_hooks_probe.py` | 16 | 1 | none: exempt (test harness) |

### 2.1 Exempt-class decisions

- Probes (read-only runtime observation, explicit exemption): scripts/codex_model_guard_probe.py, scripts/hooks_probe.py, scripts/quota_window_probe.py, scripts/read_freshness_probe.py. They observe model, hook, and freshness state and report it; they classify or gate no workflow transition, so the outcome contract's scope sentence does not reach them. They keep descriptive exits.
- Reports (read-only aggregation, explicit exemption): scripts/tool_runtime_stats.py, scripts/hooks_log_summary.py, scripts/machinery_inventory.py, scripts/quota_pressure_stats.py, scripts/friction_audit_quant.py. Same basis as the probes: observation and aggregation only, no gate decision.
- The standing rule for both classes: the exemption holds only while the script reports observations. If one grows a gate or classification decision over agent work, it needs a register row in scripts/OUTCOME_CONTRACT.md in the same change.
- Library modules (8): scripts/facts_paths.py, scripts/review_record_selection.py, scripts/execute_plan_runtime.py, scripts/plan_shape.py, scripts/runtime_capabilities.py, scripts/lessons_corpus.py, scripts/harness_detection.py, scripts/codex_hook_config.py. No CLI gate of their own; their importers own the outcomes (the validators that import them carry register rows).
- Test harnesses (78 files): outside the contract by design; they assert other scripts' OUTCOME lines and exits.
- The 31 legacy-exit files split into record- and ops-management CLIs (the lessons tools, scripts/sync_runtime_scripts.sh, scripts/release-authoring.sh, scripts/docs_branch_sync.sh, scripts/session_channel.py, the watcher) and decision-shaped checks (the backlog and doc checkers, scripts/skill_gate.py, scripts/check_lesson_scope.py and siblings). The latter group is the candidate pool for future register rows, each only when its own migration lands; the census records the pool, and no gate and no deadline is attached to it.

## 3. Churn and duplication for the top offenders

30- and 90-day commit counts per file (git log --since over the branch history at the census base):

| Script | Lines | Commits 30d | Commits 90d |
| --- | --- | --- | --- |
| scripts/check_maintenance_pins.sh | 3710 | 63 | 63 |
| scripts/done_sweep_gates_lib.py | 7650 | 31 | 31 |
| scripts/plan_readiness.py | 7973 | 20 | 27 |
| scripts/validate_review_staging.py | 18110 | 18 | 35 |
| scripts/worktree_closeout_migrate.py | 2344 | 14 | 14 |
| scripts/summarize_review_stats.py | 8996 | 7 | 13 |
| scripts/doc_registry_validator.py | 2695 | 7 | 10 |
| scripts/done-lock.sh | 2633 | 7 | 10 |
| scripts/execute_plan_resume_watcher.py | 2982 | 8 | 8 |
| scripts/reverse_squash_guard.py | 1832 | 11 | 11 |
| scripts/review_record_selection.py | 1244 | 7 | 7 |
| scripts/check_backlog_inbox_location.py | 2259 | 3 | 6 |
| scripts/skill_gate.py | 3257 | 3 | 3 |
| scripts/done_run.sh | 1252 | 3 | 3 |
| scripts/execution_claim.sh | 905 | 3 | 3 |
| scripts/review_usage_capture.py | 2239 | 2 | 3 |
| scripts/lessons_migrate.py | 2537 | 1 | 1 |
| scripts/execute_plan_runtime.py | 409 | 32 | 36 |

Readings: the pins suite is the corpus churn leader (63 commits in both windows; additions and re-aims beside provenance, including the recorded-red arm that landed in the window). The two god scripts churn hardest among production libraries: validate_review_staging.py at 35 commits and plan_readiness.py at 27 commits over 90 days, and both grew inside the window (the pins suite measured 3,287 lines at the 2026-10-13 census origin row; it measures 3,710 here). execute_plan_runtime.py is the small-file churn outlier (32 commits in 30 days over a 409-line module). The origin row's audit baseline (about 84k runtime lines at 2026-10-09) against this census's 159,136 gives the corpus's growth rate.

### 3.1 Duplication cluster 1: the plan_readiness parser pair (witnessed)

Origin row: docs/history/backlog/2026-09-19-plan-readiness-parser-dedup.md. Mechanical depth at census:

- `_review_scope_task_files`: lines 718 to 797, 80 lines, the original owner of the section split and Files collection (landed 2026-09-09).
- `_plan_task_sections`: lines 949 to 962, 14 lines, the later re-implementation of the splitter (landed 2026-09-19).
- `_plan_files_items`: lines 976 to 1031, 56 lines, the later re-implementation of the Files collection.
- `_plan_path_shaped`: lines 938 to 948, 11 lines, the already-shared token normalizer.

Roughly 150 lines are implicated across the pair: the review-scope inventory (clause c) and the ownership check each run their own copy, and a one-sided fix silently diverges them. The fix shape (review_scope as a wrapper over the `_plan_*` pair) collapses the duplication into one parser implementation.

### 3.2 Duplication cluster 2: the execution claim race-retry (witnessed)

Origin row: docs/history/backlog/2026-10-07-claim-race-retry-duplication.md. Mechanical depth at census: two attempt loops in scripts/execution_claim.sh, one in acquire_claim (counter init line 551, loop at 554, increment 555, three-attempt ceiling check 556, refusal 557) and one in cmd_refresh (init 785, loop 786, increment 787, ceiling 788, refusal 789). The retry scaffolding is 6 lines per site (init, increment, ceiling, refusal), and the refusal text is byte-identical at both sites ("claims directory kept racing at $CLAIM_PATH; re-derive the state from disk"), with nothing tying the copies together.

### 3.3 Spot measurement (named as such)

Corpus-wide signature greps over scripts/ for the two clusters' literals, run at census: "kept racing" appears in exactly one file (scripts/execution_claim.sh, at exactly the two witnessed sites, no third site), and "def _review_scope_task_files" appears exactly once. No additional cluster of either witnessed shape exists in the corpus today. This is a spot measurement over signature literals, not a corpus-wide duplication scan: no such scan tool exists for scripts, and scripts/skill_text_duplication.py is Markdown-scoped.

## 4. Next decomposition targets, priority order

1. scripts/validate_review_staging.py: 18,110 lines, 255 defs, churn 18 per 30d and 35 per 90d. The corpus's largest production script; it hosts the review-cert grading machinery, so every review round pays its size. First move scoped: the calibration module extraction, this cycle's Task 4, with the coupling data in section 5.
2. scripts/plan_readiness.py: 7,973 lines, 94 defs, churn 20 per 30d and 27 per 90d. The certification oracle; carries witnessed duplication cluster 1 (about 150 lines implicated). This cycle's Task 2 single-homes the parser pair.
3. scripts/execution_claim.sh: 905 lines, 34 shell functions, churn 3 per 30d and 90d. Size and churn are low, but it is the write-enforcement gateway and carries witnessed duplication cluster 2, whose two copies must stay byte-identical. This cycle's Task 3 extracts the shared helper.
4. scripts/done_sweep_gates_lib.py: 7,650 lines, 154 defs, churn 31 per 30d and 31 per 90d, with an 11,210-line harness. The highest-churn production library, born big (the origin row's birth-rate evidence: 7.6k production lines in three weeks). Next program cycle; excluded from this plan's decomposition surface.
5. scripts/summarize_review_stats.py: 8,996 lines, 213 defs, churn 7 per 30d and 13 per 90d. The second-largest script at a slower churn rate. Next cycle; excluded from this plan's surface.

Watch items, not targets: scripts/check_maintenance_pins.sh (3,710 lines, 14 functions) is the churn leader, but its commits are pin additions and re-aims beside provenance; it is the regression suite itself, not a decomposition target; re-measure next cycle. scripts/execute_plan_runtime.py is the small-file churn outlier; watch whether it accretes. Rankings 4 and 5 are the first candidates to re-rank when the script-runtime telemetry plan lands (section 1).

## 5. Consumer-site coupling for the calibration module move

The plan's Task 4 moves the finding-record calibration vocabulary of scripts/validate_review_staging.py into a new module (working name scripts/review_staging_calibration.py). The measured coupling data:

- The vocabulary: VALID_BLAST_RADIUS, VALID_REACHABILITY, and VALID_CONFIDENCE, defined at lines 547 to 549.
- Site 1, the calibration checks in validate_current_payload: the function spans lines 5110 to 5441; the blast_radius check sits at lines 5365 to 5371, the reachability check at 5376 to 5382, and the confidence check at 5387 to 5394.
- Site 2, the in-file selftest vocabulary arms: lines 17070 to 17080 inside _selftest_embedded_recipe_example (def at 16959); they compare _embedded_example_enum_vocabs(skill_text) (def at 16932) against set(VALID_...) for all three constants.
- Site 3, the external reads: scripts/test_review_record_selection.py lines 2122, 2124, and 2127 read vrs.VALID_CONFIDENCE, vrs.VALID_REACHABILITY, and vrs.VALID_BLAST_RADIUS as validator module attributes (the vocabulary-equality arms). The moved constants must stay resolvable as validator module attributes, so the validator from-imports them (the re-export shape). That test file's other vrs. reads do not touch the vocabulary region.
- Boundary shape the data supports: the new module owns the three constants and the three checks; validate_current_payload calls into the module; both selftest arms keep reading through the validator namespace; the new module need not import the validator, so the move stays import-cycle-free. The exact boundary is finalized at Task 4 execution.

## 6. Twin-sync contract

- Deployment: scripts/sync_runtime_scripts.sh deploys the loop-consumed scripts named in the manifest scripts/runtime-scripts.list (52 entries) as per-file symlinks from the deployed home copy (the default deployed root under ~/.ai-playbook/scripts, pinnable through DEPLOYED_ROOT for tests) into the canonical repo scripts/ directory. The canonical root resolves through symlink chains (readlink -f of the invoked script's own path), so the primary invocation mode is the deployed symlink itself. The run is idempotent (current, installed, converted, left, escalated; exit 1 on any escalation); drift converts by rename-aside (a dated .bak) plus a noclobber ln -s; a deployed copy with no canonical counterpart is left untouched. A manifest entry means "an entry script the deployed copy must expose", never a library module.
- The property the no-bespoke-deployment claim rests on: python resolves the invoked script's path through symlinks before computing sys.path[0], so an entry script launched through its deployed symlink imports sibling modules from the canonical scripts/ directory. Verified empirically at census: a probe script invoked through a symlink placed outside the scripts directory reported the resolved real directory as sys.path[0] on both available interpreters, the system python3 3.9.6 and Homebrew python3 3.15.0.
- Interpreter floor: any interpreter used for deployed-path invocations must resolve the invoked script's symlinks when computing sys.path[0]; both fleet interpreters tested satisfy it. Consequence for this program: when Task 4's module file lands, the deployed-path invocation imports it with no sync run and no manifest change; adding a manifest entry for a library module would be wrong (it would deploy a library as an entry point). Task 4's own verification creates a temporary symlink outside the scripts directory and confirms the import resolves through it.

## 7. Governance asymmetry (operator finding, no gate)

Skill text is governed: scripts/skill_text_budget.py plus scripts/skill_text_budget_caps.json enforce per-file byte caps over the skill Markdown corpus (currently warning-only, with a documented promotion path to blocking), and scripts/skill_text_duplication.py reports duplication over that corpus. The script corpus has neither: no byte budget covers scripts/*.py or scripts/*.sh, and no duplication scanner runs over them. At census the corpus measures 162 scripts and 159,136 lines, of which 103,146 lines are non-test (the origin row's audit baseline counted about 84k runtime lines at 2026-10-09); on that same non-test basis the corpus grew roughly 23 percent over the four days to 2026-10-13.

This is recorded as an operator finding and nothing more. Extending budget or duplication machinery to scripts would be new blocking machinery: it must pass the repository's Machinery admission protocol on its own witnessed incident, with catch frequency, false-positive cost, and a sunset named. The witnessed costs today are review rounds and churn (sections 3 and 4), which the decomposition program addresses without a new gate. This census proposes no gate, budget, ledger, or validator.
