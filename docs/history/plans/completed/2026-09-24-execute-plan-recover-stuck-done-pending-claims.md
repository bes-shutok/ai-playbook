# Plan: Recover completed but uncommittable execute-plan claims without manual state edits

Backlog origin: docs/history/backlog/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md (stays under the backlog directory while this plan is open)
Driving force: new-capability + efficiency (reliability-led; justification: the motivating force is reliability, an observed execution deadlock at the done-pending boundary that left a terminal worker's run stuck with a manual machine-manifest edit as the only exit, and `reliability` is not in the closed taxonomy; the deliverable is a new driver-owned recovery transition, so `new-capability` is the primary tag with `efficiency` secondary because one bounded operation replaces hand-edited manifests and discarded runs; park-triage would take it: the transition closes a witnessed High-severity deadlock class, it does not only tidy process)

## Terms

- **done-pending**: task status recorded when a worker reports completion but the done boundary has not closed (commit or none receipt, checkbox, clean state, log evidence). It refuses claims, launches, reclaims, and aborts; before this plan it has no recovery exit.
- **Policy token (allowed_paths)**: the immutable per-claim path set seeded from the plan task section at claim time. Commit authorization stays scoped to it; this plan never widens or rewrites a live token.
- **Terminal evidence**: operator-supplied bounded evidence strings proving the worker process ended; each list names the claim's session or launch identity and the observed termination. The driver records it immutably in the recovery receipt and runs no process-liveness probe (claim records carry no process identity; the reclaim precondition docstring is the standing precedent).
- **Recovery receipt**: the append-only history event `done-pending-recovery` recording the task id, claim token and generation, disposition, terminal evidence, and linked backlog evidence. Its identity (task id plus token plus generation) fences duplicate receipts.
- **Disposition**: the operator's durable choice for the recovered task: `requeue` (back to pending under a newly authorized generation after plan/manifest scope is reconciled), `defer` (terminal `deferred` status with linked backlog evidence), or `abort` (the run ends).
- **Deferred**: new terminal-ish task status excluded from the incomplete selection set, never relaunched, carried in the manifest with its linked backlog evidence, named in the recovery receipt.
- **Skill-gate marker**: per-(project, session) marker under `~/.ai-playbook/runtime/skill-invoked/` refreshed before every gated plan-file write per `agents/hooks/skill-gate/README.md`.
- **Session key**: the session id derived by the shared `session_channel.py` subprocess; empty after strip becomes the literal `no-session`, otherwise `sha1(value)[:16]`.

## Assumptions

- assume the recovery transition is an explicit operator-invoked driver operation, not an automatic readiness side effect; basis: the backlog prescribes a "driver-owned, lock-protected recovery transition" and the existing vocabulary keeps mutations explicit (readiness is read-only by construction; reclaim and abort are explicit operations).
- assume terminal evidence is operator-supplied, validated, and recorded immutably, and the transition performs no process-liveness probe and no lease wait; basis: the reclaim docstring ("claim records carry token, generation, owner, and timestamp but no process identity, so process liveness cannot be proven") plus the backlog's "remove waits or process-liveness checks when authoritative terminal evidence already proves the worker ended".
- assume disposition `requeue` closes the wedged claim, bumps the manifest generation, and lets the next claim mint a fresh token from the reconciled plan section through the existing seeding boundary; the plan/manifest scope reconciliation itself happens through the skill-gated plan edit BEFORE recovery is invoked; basis: the backlog's "return the task to pending under a newly authorized generation after plan/manifest scope is reconciled" plus per-claim allowed_paths immutability.
- assume `defer` is machine-valid only when the deferred task is the next provable incomplete task (readiness's `incomplete[0]`); basis: the backlog's "validate task dependency ordering and remaining plan acceptance before allowing continuation" plus ordinal execution order being the only machine-provable dependency signal in the manifest.
- assume recovery refuses a task whose claim is owned by any live claim group, parallel or batch, leaving siblings untouched, with evidence naming the group; basis: the backlog's "sibling workers" test obligation plus minimal preservation (group member recovery has dedicated lock-owned paths this plan must not disturb; a batch member can rest at done-pending with a live claim while its group stays active, so the refusal is group-kind-agnostic via the existing `_claim_owned_by_live_group` predicate).

Decision points requiring a grill: terminal-evidence carrier shape (operator-supplied bounded strings recorded in the receipt, no liveness probe): resolved by standing pre-authorization (scheduling ask, 2026-09-24; basis: reclaim liveness-impossibility docstring); affected section: Task 1. Deferred dependency rule (defer only the next provable incomplete task): resolved by standing pre-authorization (scheduling ask, 2026-09-24); affected section: Task 2. Requeue scope-reconciliation mechanism (skill-gated plan edit first, then a fresh claim under a bumped generation via the seeding boundary): resolved by standing pre-authorization (scheduling ask, 2026-09-24); affected section: Task 1. CLI operation name `recover-done-pending` and readiness action naming: resolved by standing pre-authorization (scheduling ask, 2026-09-24); affected section: Task 3.

## Gist & Examples

TLDR: the execute-plan runtime driver gains a lock-protected recovery transition that converts a terminal worker's stuck `done-pending` claim into an operator-chosen durable disposition, so the witnessed task-6 deadlock class stops forcing manual manifest edits or discarded runs (new-capability, reliability-led).

The observed wedge (run evidence under `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/`, gitignored, cited read-only): task 6's worker terminated; its own implement log reports incomplete acceptance and no commit; the task's immutable allowed_paths token omits the runtime files its plan criteria required; the claim stays live with the task at `done-pending` and `resume_allowed: false`; readiness answers decision `recovery`, recovery action `preserve-and-reconcile`. Every existing exit is closed: `abort` refuses to regress a claim past its receipt boundary (the only wedge exception is commit-pending with a provably missing commit), `reclaim` admits only claims on tasks outside the progressed statuses and only after the four-hour lease, `record_done` refuses the incomplete done evidence, and readiness refuses every continuation. The contract forbids hand-editing the machine manifest, so the run was stuck.

What changes: a new driver method `recover_done_pending` behind a new CLI operation `recover-done-pending`. It admits exactly one shape: a task in `done-pending` on a fenced claim (owner, token, and generation must match exactly), whose claim no live claim group owns (parallel or batch; checked with the existing group-kind-agnostic `_claim_owned_by_live_group` predicate), with non-empty bounded terminal evidence naming the claim's session or launch identity. It records an immutable `done-pending-recovery` receipt and applies one operator-chosen disposition: `requeue` returns the task to pending (the shared `_reset_task_to_pending` rotation, stale session fields stripped) under a bumped generation so the next claim mints a fresh policy token from the reconciled plan section; `defer` marks the task `deferred` with an existing repo-relative backlog path recorded as evidence, allowed only when the task is the next provable incomplete task; `abort` ends the run (task aborted, claim aborted, workflow aborted), the same durable writes the wedged-abort path makes. Every arm preserves the working tree byte-for-byte and never relaunches the same claim. Readiness keeps refusing on its own and only gains discoverability: the done-pending failed condition's recovery action becomes `recover-done-pending` (commit-pending keeps `preserve-and-reconcile`).

Example flow: the operator reconciles the plan's task scope through the skill-gated plan edit, then invokes `recover-done-pending` with the claim token, disposition `requeue`, and terminal evidence naming the dead session. The driver verifies identity and terminality evidence, records the receipt, resets the task to pending, and bumps the generation. Readiness now answers `direct-continuation` naming the requeued task as the next provable task, and the normal claim path launches it under the corrected token. With disposition `defer` and a linked backlog path, the run skips the task and continues; the deferred task is never relaunched and is named in the terminal report through its recorded receipt. With disposition `abort`, the run ends cleanly with the refusal-free terminal state.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every disposition plus stale identity, duplicate receipt, wrong-status refusal, live-group refusal, and terminal-evidence refusal is test-proven in the new `DonePendingRecoveryTest`; the focused class and the full runtime suite pass.
- safety: zero working-tree mutation during recovery, zero relaunch of the same claim, commit authorization stays path-scoped (no allowed_paths edit anywhere in the transition).
- contract coherence: `runtime-contract.md` and `SKILL.md` name the operation, its refusal arms, the `deferred` status, and the readiness action exactly as implemented.
- compatibility: existing refusal arms are unchanged (abort progressed-past-receipt, reclaim lease gate, record_done fences); `test_readiness_recovery_on_commit_pending` remains the green `preserve-and-reconcile` fence.

**Done when:**
- `python3 -m unittest test_execute_plan_runtime.DonePendingRecoveryTest -v` passes from `scripts/`.
- `python3 -m unittest test_execute_plan_runtime -v` passes from `scripts/`.
- Readiness on a recovered manifest answers `direct-continuation` after requeue (naming the next provable task; pinned by `test_readiness_after_requeue_answers_direct_continuation`) and after defer (skipping the deferred task; pinned by `test_readiness_after_defer_skips_deferred_task`), and the abort disposition leaves `workflow_state: aborted` (pinned by `test_recover_abort_disposition_ends_run`).
- The Validation Commands block below exits 0, including the doc coherence greps.

**Ship when:**
- none; adoption is in-repo operational use by live execute-plan runs (no deploy, no external gate). Recovering the still-stuck 2026-09-22 run is the operator's follow-up use of the landed transition, not part of this plan.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py`; scope: new module constants (`RECOVERY_DISPOSITIONS`, receipt event literal), new `recover_done_pending` method, `_task_complete` gaining `deferred`, `validate_manifest`'s closed `task_states` set gaining `deferred` (nothing else in that method changes), readiness condition (b) action naming for the done-pending arm, `_operation_recover_done_pending`, argparse and `main()` dispatch. All other methods and branches in this file are frozen; reject any review finding that touches them.

**Tests:**
- `scripts/test_execute_plan_runtime.py`; scope: the new `DonePendingRecoveryTest` class only. All existing classes and fixtures are frozen; reject findings that modify them.

**Documentation:**
- `agents/skills/execute-plan/runtime-contract.md`; scope: durable task state machine (deferred status), transition table (recovery arms and refusals), driver entrypoint operations table (new row), new subsection `Terminal-worker done-pending recovery`, readiness decision section (done-pending action naming).
- `agents/skills/execute-plan/SKILL.md`; scope: the readiness decision table's unresolved-blocker row, the orchestration state table's `recovering` row reference, and the Orchestrator Responsibilities recovery line naming the operation and forbidding manual manifest edits.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime_codex.py` and `agents/hooks/codex-execute-plan/`; reason: adapter and hook layer, the transition is adapter-neutral.
- `scripts/execute_plan_resume_watcher.py`; reason: watcher family untouched by this plan.
- `docs/tmp/execute-plan/2026-09-22-codex-execute-plan-runtime-reconciliation/`; reason: gitignored run evidence, cited read-only.
- The live stuck run's persisted manifest itself; reason: recovering it is the operator's post-landing follow-up, never an authoring-time state edit.

## Design Invariants (CR Guard)

- Preserve the receipt-boundary refusal: `abort` must never regress a done-pending task through its existing path; the r5-F2 wedge exception stays commit-pending-only. The new transition is the single sanctioned exit from done-pending.
- Preserve per-claim policy-token immutability: no code path in this plan edits `allowed_paths`; a requeued task's fresh token derives at next claim from the reconciled plan section (seeding boundary).
- Preserve readiness read-only-ness: readiness names the operation in its recovery action; it never mutates state.
- Preserve lock ownership: the transition runs under `@_locked_mutation` like every other writer; no lock-free mutation path is added.

## Validation Commands

```bash
(
  cd scripts || exit 1
  python3 -m unittest test_execute_plan_runtime.DonePendingRecoveryTest -v || { echo "FAIL: focused recovery suite"; exit 1; }
  python3 -m unittest test_execute_plan_runtime -v || { echo "FAIL: full runtime suite"; exit 1; }
) || exit 1
test -f agents/skills/execute-plan/runtime-contract.md || { echo "FAIL: contract doc missing"; exit 1; }
test -f agents/skills/execute-plan/SKILL.md || { echo "FAIL: skill doc missing"; exit 1; }
grep -qF "recover-done-pending" agents/skills/execute-plan/runtime-contract.md || { echo "FAIL: contract operations-table row missing"; exit 1; }
grep -qF "Terminal-worker done-pending recovery" agents/skills/execute-plan/runtime-contract.md || { echo "FAIL: contract recovery subsection missing"; exit 1; }
grep -qF "recover-done-pending" agents/skills/execute-plan/SKILL.md || { echo "FAIL: SKILL.md recovery reference missing"; exit 1; }
if grep -qiE "offers no bounded recovery" agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/SKILL.md; then echo "FAIL: stale gap prose survived the doc update"; exit 1; fi
```

### Task 1: Recovery transition core with terminal-evidence gate, receipt fence, and requeue disposition

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] Tests first, in a new `DonePendingRecoveryTest` class building the hermetic git fixture per the `DoneBoundaryNoCommitTest` in-file precedent (temp repo, neutralized global git config, tracked minimal plan, `create_manifest` seeding), then driving `RuntimeDriver` directly: `test_recover_requeue_returns_done_pending_task_to_pending_under_new_generation`; given a manifest with one task in done-pending on a fenced claim (matching owner, token, generation) and non-empty terminal evidence naming the claim's session id, calling `recover_done_pending` with disposition `requeue` expects success, the task back to pending with `session_id`, `resume_allowed`, and `blocked_receipt` stripped, the claim closed, the manifest generation incremented exactly once, an appended `done-pending-recovery` history event recording task id, claim token, generation, disposition, and the bounded terminal evidence, and no claim or launch action in the outcome actions [class: REPOSITORY_TEST]
- [x] `test_recover_requires_exact_claim_identity`; given the same fixture but a wrong token in one variant and a wrong generation in another, expects blocked `stale-claim` with evidence naming the identity mismatch and a byte-identical manifest after the call [class: REPOSITORY_TEST]
- [x] `test_recover_requires_terminal_evidence`; given an empty evidence list in one variant and a list omitting the claim's session or launch identity in another, expects blocked with evidence naming the terminal-evidence requirement and no mutation [class: REPOSITORY_TEST]
- [x] `test_recover_refused_outside_done_pending`; given the claim's task in `claimed` status instead of done-pending, expects blocked with evidence naming the done-pending precondition and no mutation [class: REPOSITORY_TEST]
- [x] `test_recover_duplicate_receipt_refused`; given a manifest whose history already carries a `done-pending-recovery` event with the same task id, token, and generation, expects blocked with evidence naming the duplicate-receipt fence and no new history event [class: REPOSITORY_TEST]
- [x] `test_recover_preserves_working_tree_changes`; given dirty working-tree entries inside and outside the task's allowed paths, expects a successful requeue with no cleanup action in the outcome and every dirty entry byte-identical after the call [class: REPOSITORY_TEST]
- [x] `test_recover_skips_lease_wait`; given a claim whose timestamp is younger than `CLAIM_LEASE_SECONDS` and otherwise valid terminal evidence, expects the recovery to proceed (no lease refusal), pinning the backlog's remove-waits requirement [class: REPOSITORY_TEST]
- [x] `test_recover_refused_while_task_in_live_parallel_group`; given the done-pending fixture whose claim carries a `group_id` pointing at an active parallel `claim_groups` entry with a sibling member, expects blocked with evidence naming the group, a byte-identical manifest, and the sibling member's task and claim untouched [class: REPOSITORY_TEST]
- [x] `test_recover_refused_while_task_in_live_batch_group`; given the done-pending fixture whose claim is the active member of an active batch `claim_groups` entry (the contract's checkpoint-success shape: a member can rest at done-pending with its claim live while the group stays active), expects blocked with evidence naming the group and no mutation, pinning that the refusal is group-kind-agnostic [class: REPOSITORY_TEST]
- [x] `test_readiness_after_requeue_answers_direct_continuation`; given the manifest after a successful requeue recovery, calling `readiness` against the fixture plan expects decision `direct-continuation` with the requeued task as the next provable task [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 -m unittest test_execute_plan_runtime.DonePendingRecoveryTest -v` from `scripts/` errors on all ten new tests (`recover_done_pending` does not exist yet, so each raises AttributeError); the pre-existing `test_execute_plan_runtime` suite still passes [class: REPOSITORY_TEST]
- [x] Add the module-level `RECOVERY_DISPOSITIONS = ("requeue", "defer", "abort")` constant and the `done-pending-recovery` receipt event literal beside the existing status constants [class: IMPLEMENTATION_REQUIRED]
- [x] Implement `recover_done_pending(self, task_id, token, disposition, terminal_evidence, backlog_evidence=None)` under `@_locked_mutation`: exact-identity fence (owner, token, generation via `_stale_claim_outcome`), done-pending status precondition, live-claim-group refusal checked with the group-kind-agnostic `_claim_owned_by_live_group` predicate (evidence names the group), terminal-evidence validation through `bounded_evidence` (non-empty strings, one naming the claim's session or launch identity), duplicate-receipt fence scanning recorded history for the same task id, token, and generation, and disposition handling that dispatches only the requeue arm in this task while refusing `defer` and `abort` as not-yet-implemented dispositions with evidence naming the arm; the requeue arm reuses `_reset_task_to_pending`, closes the claim, bumps the manifest generation exactly once, appends the receipt, and post-validates that the next provable incomplete task is pending or None (the post-acceptance check); no launch or claim action is returned [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused class passes (10/10) and the full `python3 -m unittest test_execute_plan_runtime -v` suite passes from `scripts/` [class: REPOSITORY_TEST]
- [x] Commit: `feat: driver recovery transition core for stuck done-pending claims (requeue)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Defer and abort dispositions with dependency-ordering validation

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `test_recover_defer_marks_task_deferred_with_backlog_evidence`; given disposition `defer` with an existing repo-relative path under `docs/history/backlog/`, expects the task status `deferred`, the path recorded in the `done-pending-recovery` receipt, the claim closed, and the task excluded from the incomplete selection so the next provable task is the following pending task [class: REPOSITORY_TEST]
- [x] `test_recover_defer_requires_existing_backlog_path`; given a backlog path outside `docs/history/backlog/` in one variant and a nonexistent path in another, expects blocked with evidence naming the backlog-evidence requirement and no mutation [class: REPOSITORY_TEST]
- [x] `test_recover_defer_refused_when_earlier_task_incomplete`; given an earlier-ordinal task still pending, expects blocked with evidence naming the dependency-ordering rule (defer is valid only for the next provable incomplete task) [class: REPOSITORY_TEST]
- [x] `test_recover_abort_disposition_ends_run`; given disposition `abort` on the valid done-pending fixture, expects the task aborted, the claim aborted, `workflow_state` aborted, the receipt appended, and no claim or launch action returned [class: REPOSITORY_TEST]
- [x] `test_deferred_status_passes_manifest_validation`; given a seeded manifest whose task carries status `deferred`, calling `validate_manifest` expects success with no `unknown task status` refusal, pinning that the closed `task_states` set admits the new status (the F1 witness: without this set extension, readiness, diagnose, and every `refresh_manifest` caller would raise on any post-defer manifest and re-wedge the run) [class: REPOSITORY_TEST]
- [x] `test_readiness_after_defer_skips_deferred_task`; given the manifest after a successful defer recovery, calling `readiness` against the fixture plan expects decision `direct-continuation` with the following pending task as next provable and the deferred task absent from the selection (this test drives `readiness`, so it also fails red while `validate_manifest` still refuses `deferred`) [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 -m unittest test_execute_plan_runtime.DonePendingRecoveryTest -v` fails on the six new tests (the Task 1 implementation refuses `defer` and `abort` as not-yet-implemented dispositions with evidence naming the arm, so the four disposition tests see blocked outcomes and their asserted post-states never appear; the `validate_manifest` and readiness-after-defer tests fail because no deferred status can be written yet); the ten Task 1 tests and the pre-existing suite still pass [class: REPOSITORY_TEST]
- [x] Extend `validate_manifest`'s closed `task_states` set with `deferred` (that set membership is the only change inside the method) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `recover_done_pending` with the defer arm: backlog-evidence validation through `_safe_relative_path` (repo-relative, no path escape) plus existence under `docs/history/backlog/`, the next-provable-incomplete-task ordering check, the claim closed (its test pins the closed claim; a live claim on a non-progressed `deferred` task would flip readiness to `observe-worker` and fail the Done-when witness), task status `deferred`, receipt append; extend `_task_complete` to treat `deferred` as complete-for-selection so the incomplete set and the readiness terminal-path decision exclude deferred tasks; document in the method docstring that `deferred` deliberately stays out of `PROGRESSED_TASK_STATUSES` so readiness condition (c) plan-manifest agreement never demands unchecked-checkbox closure for a task the operator chose not to complete [class: IMPLEMENTATION_REQUIRED]
- [x] Add the abort arm: task aborted, claim aborted, `workflow_state` aborted (the same durable writes as the wedged-abort path), receipt append, the shared post-acceptance validation skipped (the run is terminal), and the shared `_abort_outcome` envelope shape (status `aborted`, reason `explicit-abort`, recovery action `preserve-and-stop`, carrying the recovery receipt identity and the abort evidence) so the Task 3 CLI pin stays honest for all three arms [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused class passes (16/16) and the full `python3 -m unittest test_execute_plan_runtime -v` suite passes from `scripts/` [class: REPOSITORY_TEST]
- [x] Commit: `feat: defer and abort dispositions for the done-pending recovery transition` [class: IMPLEMENTATION_REQUIRED]

### Task 3: CLI operation, readiness action naming, and contract and skill coherence

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] `test_readiness_names_recovery_operation_for_done_pending`; given the class's done-pending readiness fixture, expects the done-pending failed condition's recovery action to be `recover-done-pending` while `test_readiness_recovery_on_commit_pending` (frozen, pre-existing) keeps pinning `preserve-and-reconcile` for commit-pending [class: REPOSITORY_TEST]
- [x] `test_cli_recover_done_pending_operation_end_to_end`; given temp-repo manifests with a done-pending fenced claim, invoking the module CLI with `--operation recover-done-pending` and the task payload (task id, token, terminal evidence) once per disposition expects the disposition's family envelope on stdout with exit 0 for each (`requeue` and `defer` success envelopes; the abort envelope carries status `aborted`): `requeue` persists the task pending with the receipt appended, `defer` (with the backlog path) persists the task deferred, and `abort` persists the aborted workflow, pinning the CLI payload mapping for all three arms [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 -m unittest test_execute_plan_runtime.DonePendingRecoveryTest -v` fails on the two new tests (readiness still reports `preserve-and-reconcile` for the done-pending arm, and the CLI operation does not exist yet so the invocation errors); all sixteen Task 1 and Task 2 tests and the pre-existing suite still pass [class: REPOSITORY_TEST]
- [x] Add `_operation_recover_done_pending` (payload: task id, token, disposition, terminal evidence, optional backlog evidence; `persist_construction=False` construction like the sibling read/repair operations) plus the argparse wiring and the `main()` dispatch arm [class: IMPLEMENTATION_REQUIRED]
- [x] Change readiness condition (b) so the done-pending arm's recovery action is `recover-done-pending` (operator action) while commit-pending keeps `preserve-and-reconcile` [class: IMPLEMENTATION_REQUIRED]
- [x] Update `agents/skills/execute-plan/runtime-contract.md`: the durable task state machine gains the `deferred` status and the recovery receipt; the transition table gains the recovery arms and their refusal shapes; the driver entrypoint operations table gains the `recover-done-pending` row; a new subsection `Terminal-worker done-pending recovery` under the durable driver boundary states the identity fence, terminal-evidence requirement, duplicate-receipt fence, live-group refusal, working-tree preservation, no-relaunch guarantee, and the three dispositions; the readiness decision section names the new action for the done-pending arm [class: IMPLEMENTATION_REQUIRED]
- [x] Update `agents/skills/execute-plan/SKILL.md`: the readiness decision table's unresolved-blocker row references `recover-done-pending` as the bounded exit for a terminal worker's done-pending claim; the `recovering` orchestration state row and the Orchestrator Responsibilities recovery guidance name the operation and repeat the manual-manifest-edit prohibition [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused class passes (18/18), the full runtime suite passes from `scripts/`, and the plan's Validation Commands block exits 0 end to end [class: REPOSITORY_TEST]
- [x] Commit: `feat: recover-done-pending CLI operation with contract and skill coherence` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-24-done-pending-recovery-r1-low-findings.md: disposition folded into 2026-09-24-execute-plan-recover-stuck-done-pending-claims.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-24-execute-plan-recover-stuck-done-pending-claims.md: disposition folded into 2026-09-24-execute-plan-recover-stuck-done-pending-claims.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-20-execute-plan-done-boundary-forces-commits-on-verification-only-tasks.md: disposition folded into 2026-09-24-execute-plan-recover-stuck-done-pending-claims.md (2026-09-25); per-item file deleted.
