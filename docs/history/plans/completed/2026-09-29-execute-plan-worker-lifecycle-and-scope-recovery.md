# Plan: Execute-plan worker lifecycle and scope recovery

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-28-terminal-worker-launch-reservation-release.md`
- `docs/history/backlog/2026-09-28-execute-plan-evidence-recovery-closes-handoff.md`
- `docs/history/backlog/2026-09-29-execute-plan-preflight-scope-parser.md`
- `docs/history/backlog/2026-09-29-execute-plan-worker-prompt-role-contract.md`
- `docs/history/backlog/2026-09-29-execute-plan-recover-reviewed-scope-drift.md`

Predecessor plan: docs/history/plans/2026-09-28-execute-plan-preflight-mandate-and-driver-resolution.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-29-plan-review-execute-plan-worker-lifecycle-and-scope-recovery-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

An execute-plan run can recover reviewed task scope and complete worker lifecycles without widening live authority or losing the evidence needed for a safe next launch.

- Preflight compares the task's structured file declaration with its seeded scope, so commands and prose do not create false drift while real drift still refuses before claim consumption.
- A worker launches only with a validated role prompt and bounded, task-owned evidence contract; parent-owned commit and done duties remain separately checked.
- Recovery and normal completion close only exact terminal reservations and handoffs, retain historical launch receipts, and permit a safe successor launch.
- A reviewed prelaunch scope change updates the exact claim in one replay-safe transition, after surfacing the canonical path delta and verifying review evidence for the current plan bytes.

## Terms

- **claim identity:** task id, owner, token, and generation that bind one task attempt.
- **launch identity:** the claim identity plus the provider launch id and session identity recorded for that worker.
- **prelaunch claim:** a claim for which no worker launch record, active worker, or launch reservation exists.
- **evidence contract:** the digest-bound criteria and command declarations used to validate a worker result against one task.
- **failed-preflight receipt:** a driver-produced, immutable record emitted as canonical structured stdout by read-only preflight on scope-drift refusal; preflight persists nothing. The caller passes those exact receipt bytes explicitly to scope refresh. Refresh recomputes the receipt from current plan, manifest, task, and handoff state and requires byte-identical equality before using it, so caller-supplied receipt bytes alone cannot establish authenticity.
- **reviewed scope refresh:** one authorized transition that replaces canonical allowed paths and rotates one exact prelaunch claim after current plan bytes pass readiness and review checks, and the failed-preflight receipt and handoff intent bind to that claim.

## Assumptions

- assume the five listed backlog items are one follow-up group because they share the execute-plan driver, task-worker boundary, and recovery lifecycle; basis: the five origin files name these shared runtime and contract surfaces.
- assume the in-flight predecessor remains unchanged and is a prerequisite to executing this plan; before this plan is marked ready for execution or launched, re-derive its landed contract and implementation; basis: the user identified it as already in flight and requested a follow-up plan.
- assume reviewed scope recovery rotates the exact prelaunch claim while replacing canonical paths and preserves the manifest plus completed-task history; basis: user accepted this transition in the plan requirements interview on 2026-09-29.
- assume a suspicious raw process match receives one bounded fresh exact terminal observation; release requires fresh identity-matched provider-terminal proof, while a fresh live-resume observation continues to refuse release; basis: the worker-role backlog records stale raw output as a recovery stall and the existing lifecycle contract requires live-resume refusal.
- assume evidence criteria keep the existing item and aggregate byte limits; compact stable criterion ids map to full criteria through an immutable digest-bound mapping; basis: the worker-role backlog requires bounded envelopes and rejects truncation of criterion meaning.
- assume the reviewed scope refresh reuses one callable plan-readiness authority for structural checks and the latest plan-review sidecar instead of duplicating the verdict logic in the runtime; basis: `scripts/plan_readiness.py` owns latest-round discovery, sidecar schema/source-digest checks, and clean-verdict readiness today.
- assume the driver constructs a structured worker role/task/scope contract from the authoritative claim and task, then serializes it to provider prompt text after validation; basis: the driver owns those identities and the adapter accepts only prompt text.

Decision points requiring a grill: reviewed scope recovery atomically rotates the exact prelaunch claim and replaces its canonical paths while preserving the existing manifest and completed-task history; source: user confirmation, 2026-09-29; affected section: Task 7 and Design Invariants. Scope-refresh actor provenance is audit-only and must not add a human confirmation or authorization dependency; record the numeric POSIX effective UID when available and never trust caller-supplied actor fields; source: user clarification that one operator is expected and human interference should be minimized, 2026-09-29; affected section: Task 7 actor receipt and provenance tests.

## Gist & Examples

TLDR: Close execute-plan worker lifecycle and recovery gaps with exact, auditable transitions, strengthening code quality.

Before: a task declares `scripts/service.py` in `Files:` and includes a backticked command such as `grep -n 'src/module'`; the broad inline-code scan treats the command as an owned path and reports false scope drift. A reviewed plan can also add a required file after the manifest was seeded, leaving no supported way to refresh the exact unlaunched claim. A malformed worker result may leave its launched handoff unresolved, and a terminal worker may keep the next launch reservation occupied.

After: preflight reads only the structured `Files:` declaration, so the command is ignored while a genuinely undeclared file still blocks. For a reviewed change on an exact prelaunch claim, one driver operation verifies the failed-preflight receipt, handoff, current plan and review digests, and absence of launch evidence. It emits the canonical path delta before saving, then atomically rotates the claim and records the delta. If the same refresh is attempted after launch, it refuses without changing manifest bytes. The worker prompt is constructed from validated task and claim fields; terminal recovery releases and settles only exact identities, retaining historical evidence.

## Evaluation Criteria

**Quality dimensions:**

- correctness: structured file declarations pass canonicalized comparison, prose and command examples do not become paths, and a genuine out-of-scope declaration still refuses before claim consumption.
- correctness: prompt role, task identity, allowed paths, evidence owner, and criteria mapping are checked before adapter launch; missing or mismatched values leave the claim and launch state unchanged.
- reliability: recovery and normal done release only the matching task/token/generation/launch reservation; evidence-contract recovery settles only the matching parent handoff after fresh exact terminal evidence; a later ordinary continuation launches the successor.
- reliability: criteria at both UTF-8 item and envelope boundaries are accepted, over-limit or ambiguous contracts refuse before mutation, and recovery revalidates the digest-bound mapping.
- correctness: reviewed scope refresh accepts only current ready and reviewed plan bytes plus the exact failed-preflight receipt, handoff intent, and prelaunch claim; it emits the canonical delta before saving, and an end-to-end witness proves ordinary preflight and launch use the rotated token and new paths.
- reliability: stale raw process output cannot indefinitely override fresh exact terminal proof, and fresh live-resume evidence still blocks release.
- maintainability: runtime contract, adapter behavior, and execute-plan skill describe one compatible worker and recovery model without duplicating conflicting rules.

**Done when:**

- `python3 scripts/test_execute_plan_runtime.py`, `python3 scripts/test_execute_plan_runtime_codex.py`, `python3 scripts/test_runtime_capabilities.py`, and `python3 scripts/test_plan_readiness.py` pass with the new positive, refusal, replay, byte-identity, coherent-snapshot, and successor-launch witnesses.
- the execute-plan skill, runtime contract, plans contract, and Codex adapter document the same task-role, evidence-ownership, scope-refresh, and lifecycle boundaries.
- every promoted backlog origin is closed only after its work is completed or explicitly rejected with evidence; any deferred remainder has a successor backlog item recorded before the origin is closed; the plan's targeted public-hygiene and no-em-dash scans pass.

**Ship when:**

- `docs/history/plans/2026-09-28-execute-plan-preflight-mandate-and-driver-resolution.md` has landed with its reviewed contract and implementation; owner: the in-flight predecessor run; closure evidence: its landed commit plus the final review/readiness record. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/runtime_capabilities.py`
- `scripts/plan_readiness.py`

**Documentation:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`
- `agents/skills/plans/SKILL.md`

**Tests:**
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_plan_readiness.py`

**Plan-related extension:** implementation and review may change files not listed above when the causal link to a task is clear: a task implementation, a regression introduced by it, required wiring or documentation implied by an explicit must-fix change, or a contradiction of a contract this plan changes. If the link is weak or speculative, reject it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/plans/2026-09-28-execute-plan-preflight-mandate-and-driver-resolution.md`; it is the in-flight predecessor and its task history and implementation are not edited by this plan.
- consumer repository wrappers and deployment copies; this plan changes the canonical shared runtime and skills only.
- `agents/skills/grilling/SKILL.md` and `agents/skills/grill-with-docs/SKILL.md`; the acknowledgement issue is separately captured in `docs/history/backlog/2026-09-29-recommended-option-acknowledgement.md` and is unrelated to execute-plan runtime behavior.

## Design Invariants (CR Guard)

- A scope refresh never changes authority for a launched, reserved, or registered live worker; any evidence of launch or worker activity refuses without manifest mutation.
- Every recovery and release operation binds to exact task, owner, token, generation, launch, handoff, review digest, and terminal evidence required by that transition; task id alone never authorizes cleanup.
- Completed task receipts and historical launch records remain immutable audit evidence. A retired claim is ignored only when one unique receipt proves the exact recovery and a strictly newer task claim exists.
- Refusal on absent, stale, ambiguous, malformed, or foreign proof preserves manifest bytes.
- Preflight remains read-only. A reviewed refresh is a separate explicit mutation with a surfaced path delta and a replay-safe receipt.
- The worker can satisfy only task-owned implementation and evidence duties. Parent-owned commit and done responsibilities remain separately represented and verified by the parent.
- Evidence bounds remain unchanged. Criteria are not truncated or silently discarded to fit a receipt.


## Validation Commands

```bash
python3 scripts/test_execute_plan_runtime.py
python3 scripts/test_execute_plan_runtime_codex.py
python3 scripts/test_runtime_capabilities.py
python3 scripts/test_plan_readiness.py
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/subagent-prompts.md agents/skills/execute-plan/runtime-adapters/codex.md agents/skills/plans/SKILL.md scripts/execute_plan_runtime.py scripts/execute_plan_runtime_codex.py scripts/runtime_capabilities.py scripts/test_execute_plan_runtime.py scripts/test_execute_plan_runtime_codex.py scripts/test_runtime_capabilities.py scripts/test_plan_readiness.py
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/subagent-prompts.md agents/skills/execute-plan/runtime-adapters/codex.md agents/skills/plans/SKILL.md scripts/execute_plan_runtime.py scripts/execute_plan_runtime_codex.py scripts/runtime_capabilities.py scripts/test_execute_plan_runtime.py scripts/test_execute_plan_runtime_codex.py scripts/test_runtime_capabilities.py scripts/test_plan_readiness.py
```

### Task 1: Parse task-owned files from the structured declaration

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `ExecutePlanRuntimeTest#test_preflight_ignores_path_looking_prose`; given a task whose command examples and documentation citations contain slash-separated paths and file suffixes but whose `Files:` list is within seeded scope, expects preflight to pass without adding prose tokens to its path set [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_preflight_compares_structured_files`; given valid canonical paths in the task's `Files:` declaration, expects preflight to compare exactly those paths with the seeded allowlist [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_preflight_rejects_real_scope_drift_without_mutation`; given a declared path outside the seeded allowlist, expects preflight to refuse before claim consumption and preserve manifest bytes [class: REPOSITORY_TEST]
- [x] Run the three focused preflight tests; expect the prose-token canary RED against the current parser, the valid declaration witness GREEN, and the drift refusal witness GREEN before implementation [class: REPOSITORY_TEST]
- [x] Implement structured declaration extraction and canonicalization at the preflight boundary; preserve existing read-only behavior and the true drift refusal [class: IMPLEMENTATION_REQUIRED]
- [x] Run the three focused preflight tests; expect all GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: parse execute-plan scope from task declarations` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Validate worker role and task identity before adapter launch

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`

- [x] `ExecutePlanRuntimeTest#test_worker_action_ownership_refuses_unclassified_before_claim`; given an unclassified checklist action, expects claim creation to refuse without mutation [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_parent_commit_action_is_excluded_and_verified_by_done`; given a task with `Commit:`, expects it excluded from worker criteria and the exact planned commit retained and verified by the parent done receipt; missing worker-owned criteria still refuses [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_worker_launch_requires_canonical_task_role`; given an omitted, orchestrator-shaped, or mismatched worker prompt, expects refusal before adapter launch with claim and launch state unchanged; given the canonical single-task role bound to the active task, expects launch [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_worker_prompt_binds_full_task_execution_contract`; given caller prompt prose that attempts to replace task identity, task body, allowed paths, validation command, or worker-log destination, expects the driver-built prompt to contain each exact authoritative value and refuses mismatched role or scope before adapter invocation [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeCodexTest#test_launch_preserves_validated_task_role`; given a valid task-worker prompt and exact scope, expects the Codex adapter to pass that role to the launched worker; given missing role fields, expects no provider launch [class: REPOSITORY_TEST]
- [x] Run the prompt and adapter canaries; expect the missing and mismatched-role canaries RED and the valid-role boundary GREEN before implementation [class: REPOSITORY_TEST]
- [x] Implement a small structured role/task/scope contract that the driver constructs from authoritative claim and task state before launch reservation, binding the exact task body, allowed paths, declared validation command, and worker-log destination; remove orchestrator-shaped defaults, classify every checklist action as worker-owned or parent-owned, refuse unclassified actions before claim creation, retain exact parent commit obligations for done-receipt verification, validate required evidence-owner fields, and serialize to provider prompt text only after validation; never infer identity by scanning free-form prompt prose [class: IMPLEMENTATION_REQUIRED]
- [x] Update the execute-plan skill, subagent prompt, runtime contract, and Codex adapter contract to name the worker-owned task, scope, and evidence roles; explicitly retain parent-owned commit and done duties for parent verification [class: IMPLEMENTATION_REQUIRED]
- [x] Run the prompt and adapter canaries; expect all GREEN and no adapter call on refusal [class: REPOSITORY_TEST]
- [x] Commit: `fix: bind execute-plan worker launches to task role` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Keep task evidence criteria within the receipt contract

Files:
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] `RuntimeCapabilitiesTest#test_evidence_contract_enforces_utf8_item_and_envelope_limits`; given criteria at exact byte limits, expects a valid contract, and given one over-limit item or aggregate envelope, expects a named refusal without truncating text [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_create_refuses_unrepresentable_evidence_before_claim`; given a task whose full criteria cannot fit the evidence receipt contract, expects claim creation to refuse and manifest bytes to remain unchanged [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_recovery_revalidates_digest_bound_criteria_mapping`; given missing, altered, or ambiguous criterion-id mapping during recovery, expects refusal without changing claim, handoff, or manifest [class: REPOSITORY_TEST]
- [x] Run the boundary and no-mutation tests; expect over-limit, malformed-mapping, and pre-mutation refusal arms RED against current behavior, with existing in-limit contract canaries GREEN [class: REPOSITORY_TEST]
- [x] Implement full criteria preservation through stable compact ids and an immutable mapping bound to the evidence contract digest; validate item and aggregate UTF-8 sizes before create and recovery mutation, retaining existing limits [class: IMPLEMENTATION_REQUIRED]
- [x] Update runtime contract and skill guidance so the plan holds full criteria while receipts carry only digest-bound compact identifiers [class: IMPLEMENTATION_REQUIRED]
- [x] Run evidence boundary and recovery tests; expect all GREEN with byte-identical refusal [class: REPOSITORY_TEST]
- [x] Commit: `fix: validate bounded execute-plan evidence contracts` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Release only the terminal worker's reservation

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `ExecutePlanRuntimeTest#test_normal_done_releases_exact_terminal_reservation_and_launches_successor`; given a matching terminal reservation, expects normal done to release only that reservation and permit the ordinary successor launch [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_done_pending_recovery_releases_exact_terminal_reservation`; given a terminal worker and matching task/token/generation/launch reservation, expects the recovery transition to retire its capacity entry and reservation [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_done_preserves_foreign_reservation`; given a completed task and a reservation owned by another task, token, generation, or launch id, expects only the exact terminal reservation to be removed and the foreign reservation to remain byte-for-byte unchanged [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_terminal_recovery_allows_next_task_launch`; given recovery that closes one exact terminal worker, expects the ordinary driver path to reserve and launch the next eligible task [class: REPOSITORY_TEST]
- [x] Run recovery, done, and successor-launch tests; expect matching reservation cleanup and foreign-reservation preservation canaries RED before implementation [class: REPOSITORY_TEST]
- [x] Use one exact reservation-release contract from both normal done and recovery paths; implement a locked terminal lifecycle transition that binds the driver-owned terminal receipt to exact task/token/generation/launch identity, closes the matching reservation and capacity entry, and preserves unrelated or later-generation reservations [class: IMPLEMENTATION_REQUIRED]
- [x] Document the receipt and reservation-release contract in the runtime contract [class: IMPLEMENTATION_REQUIRED]
- [x] Run terminal recovery and next-launch tests; expect all GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: release exact terminal worker reservations` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Settle evidence-recovery handoffs and retire exact historical claims

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] `ExecutePlanRuntimeTest#test_evidence_recovery_closes_exact_launched_handoff`; given a malformed worker result, a launched parent handoff naming that successor claim, and fresh matching provider-terminal evidence, expects recovery to move only that handoff through `launched → ambiguous → failed`, record terminal recovery evidence, and requeue the task atomically; the receipt binds intent id/key, predecessor task/checkpoint and claim identity, successor task/token/generation/launch id, and provider terminal receipt/worker-session identity; exact replay preserves the terminal `failed` state and receipt bytes [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_evidence_recovery_closes_exact_launching_handoff`; given a malformed result with an exact handoff still in `launching` after adapter launch begins but before its launch receipt is persisted, plus fresh matching provider-session/launch terminal evidence, expects the locked recovery transition to move only that intent through `launching → ambiguous → failed` and requeue atomically; exact replay preserves `failed` and the receipt [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_evidence_recovery_refuses_mismatched_or_live_handoff`; given a foreign intent id/key, mismatched predecessor task/checkpoint/claim, successor task/token/generation/launch id, stale or mismatched provider terminal receipt/session, or a live worker, expects refusal and byte-identical manifest; include missing/stale/live provider evidence for both `launching` and `launched` handoffs [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_recovery_retired_claim_allows_newer_successor`; given one unique evidence-contract recovery receipt for a closed claim and a strictly newer pending or current claim, expects startup to ignore only the retired historical claim while preserving its launch record [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_evidence_recovery_then_ordinary_continuation_launches_new_claim`; given evidence-contract recovery of a launched handoff, expects the ordinary continuation to launch the fresh generation through the adapter, the exact old handoff to remain terminal `failed`, unrelated handoffs to remain unchanged, and historical launch evidence to remain present [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_duplicate_recovery_receipt_does_not_retire_claim`; given duplicate or mismatched recovery receipts, expects startup to retain the refusal [class: REPOSITORY_TEST]
- [x] Run exact-intent and historical-claim tests; expect new launched-handoff, launching-handoff, and retired-claim canaries RED, existing ambiguous-handoff and done-recovery fences GREEN [class: REPOSITORY_TEST]
- [x] Implement exact handoff settlement in the same locked evidence-recovery transition after fresh terminal proof for both `launched` and `launching` intents, moving each through its declared transition path (`launched → ambiguous → failed` or `launching → ambiguous → failed`); the durable receipt binds intent id/key, predecessor task/checkpoint and claim identity, successor task/token/generation/launch id, and provider terminal receipt/worker-session identity. Refuse every mismatched identity before mutation; exact replay preserves the failed state and receipt bytes. Extend startup recognition only for the exact unique recovery receipt plus a strictly newer task attempt; preserve historical launch evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Update the runtime contract and skill recovery route to describe the atomic handoff closure and exact historical-claim rule [class: IMPLEMENTATION_REQUIRED]
- [x] Run recovery replay, mismatch, terminal-proof, and successor-launch tests; expect all GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: close execute-plan handoffs during evidence recovery` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Bound terminal re-observation after suspicious process output

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/execute_plan_runtime_codex.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `ReconcileIdentityJoinTest#test_fresh_terminal_recheck_overrides_stale_raw_visibility`; given a suspicious raw process row followed by fresh exact provider-terminal evidence for the same launch identity, expects exactly one additional terminal observation, reconciliation to return, and release of the exact worker and reservation [class: REPOSITORY_TEST]
- [x] `ReconcileIdentityJoinTest#test_fresh_resume_observation_keeps_worker_quarantined`; given a live resume for the exact worker at the recheck boundary, expects no release and preserves quarantine [class: REPOSITORY_TEST]
- [x] `ReconcileIdentityJoinTest#test_missing_or_stale_terminal_recheck_refuses_release`; given missing, stale, or identity-mismatched recheck evidence, expects the worker and reservation to remain quarantined [class: REPOSITORY_TEST]
- [x] Run process identity and terminal observation tests; expect stale raw-output false-block canary RED while current live-resume refusal and stale-evidence refusal remain GREEN [class: REPOSITORY_TEST]
- [x] Implement one bounded exact re-observation after suspicious raw visibility; bind both observations to the same provider session and launch identity, and preserve quarantine for live, missing, stale, malformed, or mismatched evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Document observation order, freshness, and refusal behavior in the runtime contract [class: IMPLEMENTATION_REQUIRED]
- [x] Run process reconciliation and Codex terminal observation tests; expect all GREEN [class: REPOSITORY_TEST]
- [x] Commit: `fix: bound execute-plan terminal process rechecks` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Refresh reviewed prelaunch scope through one claim rotation

> Deferred/backlog (recorded descope disposition, 2026-09-29, operator direction; NOT completed work): Task 7 is descoped. Its origin docs/history/backlog/2026-09-29-execute-plan-recover-reviewed-scope-drift.md is carried by the successor backlog item docs/history/backlog/2026-09-29-execute-plan-reviewed-scope-recovery-successor.md (minimal sanctioned exit; residues: actor provenance, snapshot-coherent readiness capture, extended test matrix). Authorization: docs/tmp/descoping-direction-worker-lifecycle-task7-2026-09-29.md in the primary checkout. Boxes below are marked [x] as recorded descope dispositions per the run's Phase 5 deferred-item convention.

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/plans/SKILL.md`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

- [x] `ExecutePlanRuntimeTest#test_preflight_scope_drift_emits_bound_receipt`; given a scope-drift refusal, expects read-only preflight to emit canonical structured receipt bytes on stdout binding plan digest, task id, owner, claim token, generation, and handoff identity, without persisting the receipt or mutating the manifest [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_rotates_exact_prelaunch_claim`; given a current reviewed plan, the exact receipt emitted by the failed preflight, matching handoff intent, and exact unlaunched claim, expects the driver to emit and flush canonical added/removed paths as a non-authoritative proposal before its manifest save, then validate the candidate manifest before saving; atomically replace allowed paths, rotate the claim token, and record a bounded replay-safe receipt containing plan digest, review evidence, prior and new scope, the numeric POSIX effective UID as audit-only provenance when available, and recovery result; the driver obtains it from the process security context, never caller input; caller-supplied actor fields are ignored, and missing actor provenance does not block an otherwise authorized refresh; callers treat only the durable receipt and manifest as commit evidence [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_emits_delta_before_manifest_save`; given a valid refresh, expects delta emission, output flush, then the single manifest-save event in that order; injected save failure preserves manifest bytes and labels the output non-authoritative; no separate preview or confirmation operation is introduced [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_refuses_forged_or_altered_preflight_receipt`; given caller-supplied receipt bytes that differ from a fresh driver recomputation, expects refusal before mutation and byte-identical manifest [class: REPOSITORY_TEST]
- [x] `PlanReadinessSnapshotTest#test_snapshot_binds_plan_and_latest_review_bytes`; given a current ready plan and latest clean review pair, expects the readiness snapshot to identify the exact plan, review Markdown, sidecar bytes, and selected round [class: REPOSITORY_TEST]
- [x] `PlanReadinessSnapshotTest#test_snapshot_decision_uses_one_coherent_byte_set`; given the selected sidecar or Markdown is replaced during readiness evaluation, expects the authority either to decide and return identities from one captured byte set or refuse, never to validate one version and return a success verdict for another [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_refuses_review_snapshot_change_before_commit`; given the plan or selected latest review Markdown/sidecar changes after the initial readiness read but before the final authorization snapshot check, expects refusal before manifest mutation and byte-identical state; also given a newer review round appearing while the previously selected Markdown/sidecar pair remains unchanged, expects the latest-round selection change to refuse before manifest mutation and preserve manifest bytes [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_requires_latest_clean_review_sidecar`; given the latest round is missing, stale-digest, verdict `no`, or has a blocking finding, expects refusal before mutation and byte-identical manifest; given a current schema-valid ready `plan` sidecar for the exact plan bytes, expects the review proof to pass [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_refuses_missing_or_stale_review`; given missing or stale review proof, a stale plan digest, failed readiness, a missing/stale/mismatched failed-preflight receipt or handoff intent, or a different claim identity, expects refusal before mutation and byte-identical manifest [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_refuses_launched_worker`; given any launch record, worker registration, or reservation for the claim, expects refusal without changing authority, history, or manifest bytes [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_validates_candidate_manifest_before_save`; given a candidate manifest that fails validation, expects refusal before save and byte-identical manifest state [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_receipt_records_actor_and_scope_history`; given a successful refresh with a test-injected effective UID and a conflicting caller-supplied actor field, expects the bounded receipt to bind plan digest, review evidence, prior/new paths, and recovery result; when a process UID is available it records that UID as audit provenance while ignoring caller input [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_succeeds_without_actor_provenance`; given no process UID and arbitrary caller-supplied actor data, expects an otherwise authorized refresh to succeed and omit the actor field without treating actor identity as an authorization input [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_replay_is_idempotent`; given an exact successful refresh receipt replayed with the same input, expects the original transition result without a second token rotation or loss of completed-task history [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reviewed_scope_refresh_then_ordinary_launch_uses_new_scope`; given successful refresh, expects ordinary preflight and launch to use the rotated token and canonical new paths, and expects any removed path to remain outside the launched scope [class: REPOSITORY_TEST]
- [x] Run the reviewed-scope tests; expect success, stale-proof, live-worker, and replay canaries RED before implementation, with ordinary preflight drift refusal GREEN [class: REPOSITORY_TEST]
- [x] Implement one explicit locked transition that verifies current plan readiness and review digests, the exact receipt bytes explicitly supplied by the caller against a fresh driver recomputation from current plan/manifest/task/handoff state with byte-identical equality, and require the shared plan-readiness authority to validate the latest review round, current plan-byte digest, `source_kind: plan`, schema, `verdict: yes`, and zero blocking findings; that authority captures plan, selected review Markdown, and sidecar bytes once per evaluation, computes every parse, schema, digest, verdict, and blocking-finding decision from those captured buffers, and returns identities computed from the same buffers; it must not re-read any of those files while deciding. Under the manifest lock, perform a new coherent evaluation and revalidate that identity immediately before the mutation commit point; if any bytes or latest-round selection changed since initial validation, refuse without mutation. Treat this final snapshot check as the authorization linearization point: a review published afterward is ordered after the refresh. Keep review-sidecar and Markdown pairing/latest-round selection in the shared authority. Validate the handoff intent against plan digest/task/owner/token/generation/handoff identity and exact prelaunch claim identity, and absence of launch, worker, and reservation evidence; compute the canonical path delta under the lock, emit and flush the non-authoritative proposal before the manifest save, then validate the candidate manifest before saving, replace paths, rotate the claim, and record bounded audit history for plan digest, review evidence, prior/new scope, the numeric POSIX effective UID as audit-only provenance when available, and recovery result without rewriting completed history; obtain it from the POSIX process security context when available and ignore caller-supplied actor fields; on save failure the manifest stays byte-identical, while exact retries report whether they performed or replayed the transition, and only the durable receipt/manifest prove commit [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the existing callable `evaluate_readiness` authority with a snapshot-producing API that reads the plan, selected latest review Markdown, and sidecar once per evaluation, derives the readiness decision and returned identities from those exact buffers, and returns the selected round; use existing validation seams with captured bytes instead of duplicating review policy or rereading files. Keep the existing `(ok, reason)` API and CLI output unchanged for current callers. Add `PlanReadinessSnapshotTest` witnesses for latest-round selection, exact digest, clean verdict, blocking findings, snapshot binding, and a replacement during evaluation; the driver uses the snapshot API and performs a new coherent evaluation to revalidate identity at the authorization linearization point. Update the skill and runtime contract with the supported review, refresh, and preflight sequence; update the plans contract only where it owns the required review evidence shape [class: IMPLEMENTATION_REQUIRED]
- [x] Run receipt emission, shared readiness-source, reviewed refresh, output-ordering, and ordinary preflight/launch tests; expect the rotated token and paths at launch while all missing-proof, stale-proof, launched-worker, and replay refusals preserve state [class: REPOSITORY_TEST]
- [x] Commit: `feat: recover reviewed execute-plan scope drift` [class: IMPLEMENTATION_REQUIRED]

> Completion-pass note (2026-09-29): c1/c2 verified by the worker (all suites + scans green; identity fences audited). c3's origin closure executes in the archive completion pass per the promoted-backlog rule: fold dispositions into the archived plan and delete the origin files in the same pass.

### Task 8: Final validation and origin closure

Files:
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`
- `scripts/test_runtime_capabilities.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`
- `agents/skills/plans/SKILL.md`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

- [x] Run all four validation suites plus public-hygiene and no-em-dash scans from `## Validation Commands`; expect success [class: REPOSITORY_TEST]
- [x] Audit every implementation and refusal path against the Design Invariants; confirm exact reservation, handoff, review, launch, token, and generation identity is checked at its mutation boundary [class: REPOSITORY_TEST]
- [x] Verify each entry in `## Origins dispositions`; close a promoted origin only after its work is completed or rejected with evidence, or after each deferred remainder is recorded in a successor backlog item and the source is marked superseded; refuse plan completion while any promoted origin is still open, and delete/close its backlog file only in the same completion pass [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `test: verify execute-plan worker lifecycle and recovery` [class: IMPLEMENTATION_REQUIRED] (validation executed and verified in the Task 8 completion pass; the referenced commit is the archive completion pass, which folds origin closures and lands the plan move)

## Origins dispositions

- `docs/history/backlog/2026-09-28-terminal-worker-launch-reservation-release.md`: Tasks 4 and 8 own exact terminal reservation release, foreign reservation preservation, and successor launch.
- `docs/history/backlog/2026-09-28-execute-plan-evidence-recovery-closes-handoff.md`: Tasks 5 and 8 own exact handoff settlement, receipt-proven historical claim retirement, and recovery-to-successor launch.
- `docs/history/backlog/2026-09-29-execute-plan-preflight-scope-parser.md`: this plan's Task 1 owns structured task-file extraction and parser false-positive coverage; the exact done-successor activation and continuation complement belongs to the predecessor's Task 4. Verify that predecessor arm landed before closing this origin; if it remains open when this plan completes, create a successor backlog item for this follow-up plan's parser work and keep the origin open until the predecessor-owned arm is resolved, then record the split disposition before deleting the promoted backlog entry.
- `docs/history/backlog/2026-09-29-execute-plan-worker-prompt-role-contract.md`: Tasks 2, 3, 6, and 8 own worker role construction, bounded evidence criteria, and terminal observation recovery.
- `docs/history/backlog/2026-09-29-execute-plan-recover-reviewed-scope-drift.md`: Task 7 owns the receipt-fenced, replay-safe atomic refresh of one exact prelaunch claim and ordinary preflight/launch afterward.

## Origins closure (archive completion pass, 2026-09-29)

- `2026-09-28-terminal-worker-launch-reservation-release.md`: CLOSED completed. Exact terminal reservation release, foreign-reservation preservation, and successor launch landed in Task 4 (commits 4c82f8c0, 954fc84b); witnessed by the done/recovery reservation tests in scripts/test_execute_plan_runtime.py.
- `2026-09-28-execute-plan-evidence-recovery-closes-handoff.md`: CLOSED completed. Exact handoff settlement (launched and launching intents), receipt-proven historical-claim retirement, and recovery-to-successor launch landed in Task 5 (commits fbd247bf, ddeaff4a); residual identity hardening carried by docs/history/backlog/2026-09-29-execute-plan-recovery-receipt-identity-hardening.md.
- `2026-09-29-execute-plan-preflight-scope-parser.md`: CLOSED completed. Structured declaration extraction and parser false-positive coverage landed in Task 1 (commit 76779f0c); the predecessor-owned done-successor activation arm is verified landed (prepared-handoff adoption active in scripts/execute_plan_runtime.py); residual duplicate-heading hardening carried by docs/history/backlog/2026-09-29-execute-plan-preflight-declaration-parse-hardening.md.
- `2026-09-29-execute-plan-worker-prompt-role-contract.md`: CLOSED completed. Worker role construction and launch binding (Task 2, commit 637e0874), bounded evidence criteria (Task 3, commits 1e675304/62e77f62), and terminal observation recovery (Task 6, commits 4d19ffb9/39f0a6c3) landed; residual launch-boundary edges carried by docs/history/backlog/2026-09-29-execute-plan-launch-boundary-hardening.md.
- `2026-09-29-execute-plan-recover-reviewed-scope-drift.md`: CLOSED superseded per operator direction 2026-09-29 (Task 7 descoped). The minimal sanctioned exit is carried by docs/history/backlog/2026-09-29-execute-plan-reviewed-scope-recovery-successor.md; the origin file records the supersession.
