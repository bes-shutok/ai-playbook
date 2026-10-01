# Plan: Codex model-guard runtime alignment

Backlog origin: docs/history/backlog/2026-09-23-codex-model-guard-runtime-alignment.md
Driving force: automation + code-quality
Plan review record: docs/reviews/2026-10-01-plan-review-codex-model-guard-runtime-alignment-r*.md
Gate delta: expand the existing `runtime-policy-unavailable` refusal surface with Codex-only read-only checks at preflight, direct claim, and handoff-producing completion boundaries, preventing a mismatch from creating or rotating run state. Document operator guidance to keep host policy files stable while claims or handoff intents are active; this is advisory, not an enforced gate. The additions are paid by the completed integrity failure in `docs/history/plans/completed/2026-09-28-execute-plan-preflight-mandate-and-driver-resolution.md` (Gist, witnessed 2026-09-28 chain): an adapter's `runtime-policy-unavailable` rejection left a persisted claim stranded because prelaunch reclaim refused before lease expiry. No safe class-default exit applies to the original mismatch: allowing launch trusts an unverified active guard, treating drift as a false positive is impossible until target and bytes match, and removing the checks leaves the witnessed claim/recovery failure intact. Add no host mutation, launch-boundary check, adapter denial protocol, schema field, or recovery transition; remove no existing guard.

## Outcome
Plan execution adds an early, read-only check that the active Codex worker-model guard is the versioned guard and that Codex can read its selected worker model.

- Aligned hosts pass preflight and continue through the existing claim and handoff flow.
- Drift or missing policy is reported before those state changes, with a recovery route that keeps the launch guard fail-closed.

## Terms

- **Selected worker model:** The single policy value in Codex configuration, `agents.default_subagent_model`.
- **Versioned guard:** The source hook in `agents/hooks/codex-model-guard/require-luna.py`.
- **Installed guard:** The script path Codex resolves from its active hook registration.
- **Alignment probe:** A read-only check of the active hook target, installed guard bytes, and selected worker-model setting.

## Assumptions

- assume Codex configuration remains the only source of the selected worker model; basis: the current guard reads `default_subagent_model` from Codex configuration and does not hardcode a second allowed model.
- assume the installed guard is expected to match the versioned guard byte for byte; basis: the hook README design and the current host files, whose hashes match.
- assume the probe runs with local read access to the target host's Codex hook and config files, while tests use isolated fixtures; basis: this is a local Codex hook and runtime task.
- assume no separate ticket or migration is required; basis: the backlog item is the sole open origin and the existing runtime owns preflight.

Decision points requiring a grill: include the read-only probe and prelaunch refusal; exclude automatic host synchronization; user accepted this scope after clarifying that the model is configured once and the two guard files are program copies; source: user decision; date: 2026-10-01; affected sections: scope, tasks, review scope.

## Gist & Examples

TLDR: Check the active worker-model guard before a plan can claim work, using automation to detect host drift before it blocks recovery.

**Before (today):** A plan run can pass the existing run-state preflight even if Codex is configured to invoke an installed guard copy that no longer matches the versioned guard. If that copy rejects a worker launch, the run can be left with a claim that needs recovery, while the runtime has no early check identifying the stale hook copy.

**After (this plan):** The read-only preflight resolves the active hook command, confirms its target matches the versioned guard, and reads the one selected worker model from Codex config. For example, if Codex points at `~/.codex/hooks/require-luna.py` and that file differs from `agents/hooks/codex-model-guard/require-luna.py`, preflight returns `runtime-policy-unavailable`, emits no continuation command, and leaves claims and handoffs unchanged. The result names the drift and the operator recovery step. When the files match and the setting is readable, preflight proceeds and the existing worker guard still checks each requested model against the selected value.

The probe resolves the effective config exactly as the guard does: `CODEX_CONFIG` when set, otherwise `~/.codex/config.toml`. A relative `CODEX_CONFIG` is resolved against the Codex worker process working directory; runtime preflight normalizes it against `repo_root` to an absolute path before both probe and worker launch. On success, it reports the relevant hook path, effective config path, and selected model with a passing status. On refusal, it reports the failed check and bounded recovery details without returning host paths. Neither result includes transcript history or unrelated configuration data. The user-selected model stays in Codex config; the two compared files are copies of the guard program, not independent allowed-model settings. The current recovery incident involved a PreToolUse denial that prevented ordinary in-session recovery. The probe therefore has a direct, read-only CLI entrypoint an operator can run from outside that blocked session; the execute-plan driver also runs it before state mutation.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: aligned policy passes; wrong hook target, differing installed bytes, absent or malformed selected model, and unreadable policy inputs fail closed with a specific cause.
- Safety: a failing preflight emits no continuation command and does not mutate manifests, claims, or handoffs; failing claim and completion checks stop their respective mutation before it occurs; worker launch enforcement remains fail-closed.
- Privacy: successful output includes only the relevant hook path, effective config path, selected model, and status; refusal output names the failed check and bounded recovery details without host paths; neither includes transcript or unrelated configuration data.
- Recoverability: an operator can restore the installed guard from the versioned source and rerun preflight without bypassing or weakening the guard.

**Done when:**
- The repository probe and runtime preflight have hermetic positive and negative coverage, including byte-identity for run state after failure.
- `runtime-policy-unavailable` identifies the failed alignment check and a safe operator recovery action.
- The execute-plan and model-guard documentation describes when to run the probe and how to recover.

**Ship when:**
- [class: EXTERNAL_RELEASE_GATE] Evidence owner: target-host Codex operator. Closure evidence: record the successful read-only probe result showing the active registration resolves directly to the installed guard, installed bytes match the versioned guard, and the selected worker model is readable from the same effective config path the guard uses. The operator keeps hook/config files stable while execute-plan claims or handoff intents are active; after drift, the operator follows the existing receipt-bound recovery route before continuing. This confirms deployment on the target host.

## Review Scope

**Explicit must-fix:** valid findings on these paths are in scope.

**Production code:**
- `scripts/codex_model_guard_probe.py` *(new)*
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`

**Tests:**
- `scripts/test_codex_model_guard_probe.py` *(new)*
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_codex_model_guard.py`

**Documentation:**
- `agents/hooks/codex-model-guard/README.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `docs/maintenance/codex-worker-model-guard.md`

**Plan-related extension:** changes to `scripts/codex_hook_config.py` and its tests are in scope only if needed to reuse the fixture-based hook/config parsing without adding a second policy source.

**Out of scope; reject unless plan-related:**
- `~/.codex/config.toml` and `~/.codex/hooks.json`: operator-owned host files; read only.
- Automatic host synchronization, model selection changes, other agent providers, and transcript-based policy inference.
- Unrelated execute-plan runtime activation or capacity behavior.

## Validation Commands

Run from the repository root:

```bash
python3 scripts/test_codex_model_guard_probe.py
python3 scripts/test_codex_model_guard.py
python3 scripts/test_execute_plan_runtime.py
python3 scripts/test_execute_plan_runtime_codex.py
python3 scripts/test_codex_hook_config.py
python3 scripts/plan_readiness.py docs/history/plans/2026-10-01-codex-model-guard-runtime-alignment.md
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-01-codex-model-guard-runtime-alignment.md
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files docs/history/plans/2026-10-01-codex-model-guard-runtime-alignment.md
```

### Task 1: Add an isolated read-only guard alignment probe [class: IMPLEMENTATION_REQUIRED]

Files:
- `scripts/codex_model_guard_probe.py` *(new)*
- `scripts/test_codex_model_guard_probe.py` *(new)*

Evidence:
- `python3 scripts/test_codex_model_guard_probe.py`; covers direct active-target resolution, wrapper/compound-command refusal, byte comparison, `CODEX_CONFIG` absolute, relative-to-repo-root, and default-path parity with the guard, policy parsing, privacy-bounded output, and fail-closed errors.
- `python3 scripts/test_codex_hook_config.py`; covers compatibility with the existing fixture-based hook/config contract if that module is changed.

- [x] `CodexModelGuardProbeTest#test_aligned_runtime_passes`; given a fixture hook registration targeting a byte-identical installed guard and a readable selected model, expects a passing result naming the target and model. [class: REPOSITORY_TEST]
- [x] `CodexModelGuardProbeTest#test_wrong_target_or_guard_drift_fails_closed`; given a missing, unexpected, or byte-different active guard target, expects `runtime-policy-unavailable` with the failed check identified. [class: REPOSITORY_TEST]
- [x] `CodexModelGuardProbeTest#test_registration_must_match_worker_launch`; given no `PreToolUse` row, the wrong event, a matcher that does not select `Agent`, a command that resolves elsewhere, or a wrapper/compound command that merely mentions the expected guard, expects refusal; a command passes only when the probe can prove the exact active executable resolves directly to the installed guard. [class: REPOSITORY_TEST]
- [x] `CodexModelGuardProbeTest#test_effective_config_path_matches_guard`; given absolute and relative `CODEX_CONFIG` overrides plus an unset-override default fixture, expects the probe to read the same effective config path as `require-luna.py`; runtime resolves relative overrides against `repo_root` before invoking the probe. [class: REPOSITORY_TEST]
- [x] `CodexModelGuardProbeTest#test_missing_or_malformed_selected_model_fails_closed`; given invalid TOML, absent `[agents]`, a missing or non-string `default_subagent_model`, or a blank value, expects refusal; any nonempty string remains policy data and is not checked against a hardcoded allowlist. [class: REPOSITORY_TEST]
- [x] `CodexModelGuardProbeTest#test_output_excludes_transcript_and_unrelated_config`; given fixture host files containing unrelated and transcript-like data, expects output limited to policy status, relevant path/model fields, and recovery guidance. [class: REPOSITORY_TEST]
- [x] `CodexModelGuardProbeTest#test_cli_reports_bounded_json_and_exit_status_for_aligned_and_drifted_policy`; given aligned and byte-drifted fixture host files in a controlled child environment with a test-root `HOME`, fixed locale, and `os.defpath`, expects the process-level CLI to return valid JSON with the success or refusal key allowlist, include the effective config path on success while omitting it on refusal, use exit status 0 for alignment and 1 for refusal, exclude transcript/unrelated fixture values, and leave policy files unchanged. [class: REPOSITORY_TEST]
- [x] The probe accepts explicit fixture roots for tests and reads host files only; it never writes, repairs, or synchronizes the hook or config. Its registration check verifies that an enabled `PreToolUse` row has a matcher that can select the worker-creation tool and that the active command resolves directly to the installed guard. Wrapper and compound commands refuse unless the probe can prove the exact invoked executable and rule out additional command behavior; a registration for another event or a non-matching tool is insufficient. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Gate Codex claim and handoff mutations on model policy [class: IMPLEMENTATION_REQUIRED]

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime_codex.py`

Evidence:
- `python3 scripts/test_execute_plan_runtime.py`; covers read-only preflight and every Codex claim/handoff mutation boundary, including parallel-group claim, post-worker completion retry, and idempotent completed-task replay, with unchanged run-state bytes on drift and aligned-path success. Codex runtime tests inject fixture policy inputs or pin `HOME` and `CODEX_CONFIG` to isolated fixtures containing hook registration, installed guard, and config; the adapter resolves a relative `CODEX_CONFIG` against `repo_root`, normalizes it to an absolute path, passes that exact path to both the probe and sanitized worker environment, and tests prove parity even when the caller cwd differs from `repo_root`, without host-file reads. Non-Codex cases use an isolated `HOME` without Codex files.
- `python3 scripts/test_execute_plan_runtime_codex.py`; covers relative-path normalization against `repo_root`, the sanitized worker environment receiving the normalized `CODEX_CONFIG`, and adapter-policy behavior.

- [x] `ExecutePlanRuntimeTest#test_codex_preflight_blocks_guard_drift_before_claim`; given a Codex run with a stale installed guard, expects `runtime-policy-unavailable`, no continuation command, and byte-identical state. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_claim_refuses_guard_drift_before_write`; given a direct Codex claim operation with a stale guard, expects refusal before any claim or manifest bytes change. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_parallel_group_claim_refuses_guard_drift_before_write` and an aligned-policy counterpart; stale policy returns `runtime-policy-unavailable` with byte-identical manifest, claims, group state, and handoff intents; aligned policy creates the expected group claims. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_done_refuses_guard_drift_before_successor_handoff`; exercise the real `record_done` completion flow that calls `_prepare_handoff_locked`, with stale Codex guard policy, and expect refusal before completion, successor claim, or handoff-intent bytes change. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_commit_reconciliation_refuses_guard_drift_before_successor_handoff`; exercise `reconcile_commit_before_checkpoint` under stale policy and expect refusal before checkpoint, successor claim, or handoff-intent bytes change. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_non_codex_runtime_skips_codex_guard_probe`; given a non-Codex runtime and no Codex host files, expects existing preflight and claim behavior to remain unchanged. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_preflight_allows_aligned_guard`; given aligned hook code and a readable selected model, expects ordinary readiness checks to continue and the canonical continuation command to be emitted. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_aligned_guard_allows_claim`; given a Codex run with aligned hook bytes and readable selected model, expects the claim and manifest transition to succeed. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_aligned_guard_allows_done_successor_handoff`; given aligned policy and valid completion evidence for a task with a successor, expects `record_done` to complete and persist the expected prepared successor claim and handoff intent. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_aligned_guard_allows_commit_reconciliation`; given aligned policy and matching commit evidence for a task with a successor, expects `reconcile_commit_before_checkpoint` to complete and persist the expected prepared successor claim and handoff intent. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_done_replay_with_drift_is_idempotent` and `test_codex_commit_reconciliation_replay_with_drift_is_idempotent`; after the completed result and successor handoff are already recorded, replay under drift returns the existing receipt read-only, does not rotate or re-emit a successor handoff, and leaves manifest/claim/intent bytes unchanged. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_done_drift_then_aligned_retry_completes_once` and `test_codex_reconcile_commit_drift_then_aligned_retry_completes_once`; refusal under drift leaves the original claim, worker evidence, commit identity, and handoff bytes unchanged; after policy is aligned, retrying the same receipt-bound transition completes once and creates only one successor handoff. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_policy_probe_failure_is_fail_closed_and_read_only`; given an unreadable or malformed policy input, expects a named refusal and no manifest, claim, or handoff mutation. [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_execute_plan_runtime.py` fails on the new model-policy preflight cases while existing preflight cases remain unchanged. [class: REPOSITORY_TEST]
- [x] Pass the resolved adapter into the Codex preflight path and place the probe behind the canonicalized Codex runtime identity; non-Codex runtime preflight does not read Codex host files. [class: IMPLEMENTATION_REQUIRED]
- [x] Enforce the read-only policy result at both `claim_next_task` (including its batch path) and `claim_parallel_group`, and before mutation in `record_done` and `reconcile_commit_before_checkpoint`, the real callers that can reach `_prepare_handoff_locked`; do not put the check only inside that helper, because callers have already changed in-memory manifest state by then. Direct and group claim entrypoints cannot bypass the check or persist claims, task/group state, or successor handoff intent under drift. A pre-mutation refusal at `record_done` or `reconcile_commit_before_checkpoint` preserves the original claim and validated worker evidence for retry after policy is restored. Preserve the existing retry behavior for an already completed task. Reuse `runtime-policy-unavailable` without changing the existing fail-closed worker-launch comparison. [class: IMPLEMENTATION_REQUIRED]
- [x] Codex runtime integration tests inject fixture policy inputs or pin `HOME` and `CODEX_CONFIG` to temporary fixtures containing registration, installed guard, and config; assert the probe and launched worker guard use the same effective config in absolute override, relative override, and fallback cases, that the adapter passes the normalized absolute override through its sanitized child environment even when caller cwd differs from `repo_root`, and that the only policy reads are those three fixture files; the probe may additionally read the versioned guard source for byte comparison. Non-Codex tests use an isolated `HOME` with no Codex files. [class: IMPLEMENTATION_REQUIRED]
- [x] `ExecutePlanRuntimeTest#test_codex_policy_probe_uses_only_injected_fixture_files`; assert probe/runtime integration does not read host Codex files, and the non-Codex fixture performs no Codex-file reads. [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_codex_probe_and_guard_share_config_override` and default-path counterpart; runtime probe and launched worker guard resolve the same fixture path with absolute and relative `CODEX_CONFIG` values and with the variable unset; the relative case is resolved against `repo_root` despite a different caller cwd. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py` and any changed Codex adapter suite pass. [class: REPOSITORY_TEST]

### Task 3: Document operator recovery and run-boundary behavior [class: IMPLEMENTATION_REQUIRED]

Files:
- `agents/hooks/codex-model-guard/README.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `docs/maintenance/codex-worker-model-guard.md`
- `scripts/test_codex_model_guard.py`

Evidence:
- `python3 scripts/test_codex_model_guard.py`; confirms existing worker-launch policy still fails closed after the documentation and wiring contract changes.
- `rg -n 'runtime-policy-unavailable|alignment probe|operator recovery|default_subagent_model|program copies|allowed model set|active parent model|Luna' agents/hooks/codex-model-guard/README.md agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md docs/maintenance/codex-worker-model-guard.md`; locates the refusal, recovery, config-source, copy-identity, and legacy maintenance claims for direct content review.

- [x] `CodexModelGuardTest#test_worker_matching_selected_policy_is_allowed`, `test_worker_mismatch_is_denied_before_invocation`, and `test_missing_worker_model_or_selected_policy_fails_closed`; confirm a matching explicit model is allowed while mismatched, missing, or unavailable policy refuses before invocation. [class: REPOSITORY_TEST]
- [x] Documentation explains that Codex config owns one selected-model value while the installed and versioned guards are program copies that must match. [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile the existing maintenance note’s “allowed model set”, “active parent model”, and Luna-specific claims with the implementation: the guard compares each explicit worker-launch model against `agents.default_subagent_model`; do not leave contradictory policy descriptions. [class: IMPLEMENTATION_REQUIRED]
- [x] Operator recovery gives a direct CLI invocation that can run outside the blocked Codex session, tells the operator how to refresh the installed copy from the versioned source and rerun the probe, and never asks a blocked agent to edit its own guard or weaken the policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Document the existing recovery path if policy drifts after a claim but before worker launch: restore aligned policy outside the blocked session, inspect the durable claim/group receipt, use the existing direct prelaunch reclaim or blocked non-resumable group-member reclaim only when its driver eligibility and evidence requirements hold, then rerun preflight and invoke only its emitted command. Otherwise use ordinary lease-gated reclaim. If a valid worker result or commit exists but policy drift blocks `record_done` or `reconcile_commit_before_checkpoint`, restore alignment outside the blocked session and retry that same receipt-bound operation with the original claim identity and evidence; use commit reconciliation when the commit already landed. Do not reclaim, rerun implementation, hand-edit manifests, bypass the guard, or add a new recovery transition. Preserve idempotent retries for completed tasks: a replayed done or commit-reconciliation result returns its recorded outcome without another state mutation or handoff rotation even if current policy has drifted. [class: IMPLEMENTATION_REQUIRED]
- [x] Execute-plan guidance requires policy verification before any Codex claim or handoff mutation and names the retry path after an operator resolves drift; other runtime identities retain their existing behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Operator guidance recommends checking that no Codex execute-plan run has active claims or handoff intents before changing host hook/config files, and rerunning the probe before the next run; this is documented advice, not an enforced runtime gate, and the probe never edits host files. [class: IMPLEMENTATION_REQUIRED]
- [x] No automatic host-file write or synchronization is added. [class: IMPLEMENTATION_REQUIRED]

## Backlog disposition

- `docs/history/backlog/2026-09-23-codex-model-guard-runtime-alignment.md`: completed by this plan; implementation and documentation landed on main in squash commit `50b2b6bc` on 2026-10-01. The backlog file is deleted per the fold-then-delete lifecycle.
- `docs/history/backlog/2026-10-01-codex-model-guard-refusal-contract-edges.md`: remains open for the two low-priority R7 review findings; it is separate follow-up work and does not block this plan's repository completion.
