# Plan: Execute-plan runtime hardening pair

Backlog origins (scope of record): `docs/history/backlog/2026-09-29-execute-plan-launch-boundary-hardening.md`, `docs/history/backlog/2026-09-29-execute-plan-recovery-receipt-identity-hardening.md`
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-execute-plan-runtime-hardening-pair-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Two launch-boundary edges and the evidence-recovery receipt's identity binding close at the runtime layer, each with its regression pin, so the witnessed bypass shapes refuse at the boundary instead of mutating state first.

- A task whose worker contract lacks mandatory scope or evidence fields refuses at launch with a named blocked outcome before any reservation, in both evidence-enforcement modes; the adapter is never the first line to catch an incomplete contract.
- Every checklist action line classifies regardless of its checked state; a checked-but-unclassified action refuses seeding exactly like an unchecked one.
- Startup retirement by evidence recovery requires the receipt's successor owner and launch id bound against the resolved intent's successor block (the receipt's successor describes the retired claim; a post-recovery re-claim always mints fresh identity, so a current-claim equality could never hold), rejects receipts whose intent does not resolve or whose predecessor identity disagrees, and a non-mapping `successor` value returns False instead of raising inside startup reconciliation.

Gate delta: two checked conditions added to the existing launch refusal surface (contract completeness before reservation, both modes; checklist classification across checked states) and the existing recovery-receipt validation surface extended by three checked conditions (intent resolution and predecessor binding, successor owner/launch-id equality against the resolved intent's successor block, non-mapping successor guard returning False instead of raising). The fix-class pricing per origins: both launch edges are boundary-order repairs (the check exists elsewhere and fires too late or not at all - the sanctioned exit is refusing earlier without mutation), the crash guard removes a false-positive crash on malformed history (the class-default fix), and the identity binding closes the witnessed admission gap with no refusal surface removed. No gate, field, or refusal class is removed.

## Terms

- Launch reservation: the launch path's first state mutation (claim and task state moving to launched/reserved); everything before it must be refusal-only.
- Worker contract: the `single-task-worker` dict `_worker_role_contract` builds from the task and claim.
- Evidence-recovery receipt: a history event of kind `evidence-contract-recovery` or `prelaunch-contract-recovery` carrying `handoff_recovery`.
- Intent record: the runtime's recovery intent (writer at the prepare site: `intent_id`, `prior` identity block, `successor` block with owner and launch id, `prelaunch_binding`, `launch_receipt`).

## Assumptions

- The two origins are cluster-linked siblings from the same worker-lifecycle plan's Step 1.2b round-2 reviews, same runtime file and suite, so one plan carries both without scope extension. (Basis: both origin headers and their Cluster lines.)
- The intent record's `prior` block carries `task_id`, `checkpoint_identity`, `claim_owner_id`, `claim_token`, `generation`, and the `successor` block carries `task_id`, `claim_owner_id`, `claim_token`, `generation`, `launch_id` (writer verified this cycle); the provider terminal receipt and session identity fields the recovery origin names are verified from the intent's terminal/launch-receipt shape at implementation start before their validation is wired, with the found names recorded in the task log. (Basis: the intent writer block, read today.)
- `evaluate_pause`-adjacent surfaces are untouched; this plan's surface is `scripts/execute_plan_runtime.py` and its suite only. (Basis: both origin bodies.)

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The launch boundary validates the worker contract and classifies every checklist action before mutating state, and the evidence-recovery receipt binds its full identity before startup retirement; force: code-quality.

Today a legacy-mode task with empty criteria or commands gets past the driver's contract check, reserves, and only then meets the adapter's refusal, leaving launch state mutated behind a blocked launch; and a task body whose `- [x]` actions are unclassified seeds cleanly because the collector never looks at checked boxes. On the recovery side, a handoff receipt is admitted on successor task/token/generation alone: its owner and launch id are never compared to the intent or the current claim, a receipt naming an unknown intent is not distinguished from one naming the right intent, and a malformed `successor` value crashes startup reconciliation with an AttributeError instead of leaving the claim examined. After this plan each shape refuses or returns False at the boundary with a regression pin in the suite.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each refusal fires before the first state mutation (launch) or without raising (recovery), in both evidence-enforcement modes where modes apply.
- Coverage: every new refusal shape has a named suite pin that fails when the guard is violated; the full runtime suite passes.
- Compatibility: legacy-evidence mode keeps its documented fallbacks (body, log path, evidence owner defaults); only the empty scope/evidence contract refusal is new.

**Done when:**
- The full runtime suite passes under `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime`, and every Validation Commands line exits 0.

**Ship when:**
- The next mixed-mode execute-plan run exercises the new launch refusal or recovery binding in vivo (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md` (wording touch-up only)

**Tests:**
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-29-execute-plan-legacy-evidence-contract-compat.md` and `docs/history/backlog/2026-09-30-baseline-aware-stale-session-cleanup.md`; reason: cluster siblings owned elsewhere, untouched here.
- the adapter's own contract checks; reason: the boundary check supplements them, never replaces them.

## Validation Commands

```bash
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime 2>&1 | tail -1 | grep -q "^OK" || { echo FAIL: runtime suite; exit 1; }
grep -c "test_launch_refuses_incomplete_contract_before_reservation_legacy_mode" scripts/test_execute_plan_runtime.py | grep -q -v "^0$" || { echo FAIL: legacy contract pin; exit 1; }
grep -c "test_launch_refusal_leaves_no_reservation_state" scripts/test_execute_plan_runtime.py | grep -q -v "^0$" || { echo FAIL: no-mutation pin; exit 1; }
grep -c "test_checked_checklist_action_requires_classification" scripts/test_execute_plan_runtime.py | grep -q -v "^0$" || { echo FAIL: checked-action pin; exit 1; }
grep -c "test_recovery_receipt_non_mapping_successor_returns_false" scripts/test_execute_plan_runtime.py | grep -q -v "^0$" || { echo FAIL: crash-guard pin; exit 1; }
grep -c "test_recovery_receipt_binds_intent_successor_owner_and_launch" scripts/test_execute_plan_runtime.py | grep -q -v "^0$" || { echo FAIL: identity pin; exit 1; }
grep -c "test_recovery_receipt_rejects_intent_mismatch" scripts/test_execute_plan_runtime.py | grep -q -v "^0$" || { echo FAIL: mismatch pin; exit 1; }
grep -q "worker contract is incomplete" scripts/execute_plan_runtime.py || { echo FAIL: launch refusal token; exit 1; }
grep -qF '[[ xX]]' scripts/execute_plan_runtime.py || { echo FAIL: checked-box collector; exit 1; }
grep -q "successor identity is not a mapping" scripts/execute_plan_runtime.py || { echo FAIL: successor guard token; exit 1; }
grep -q "recovery receipt does not bind the recorded intent" scripts/execute_plan_runtime.py || { echo FAIL: identity token; exit 1; }
bash scripts/check-no-em-dash.sh file scripts/execute_plan_runtime.py scripts/test_execute_plan_runtime.py docs/history/plans/2026-10-01-execute-plan-runtime-hardening-pair.md || { echo FAIL: em-dash; exit 1; }
```

### Task 1: launch refuses an incomplete worker contract before reservation, both modes

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md` (wording touch-up only)

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k incomplete_contract -k leaves_no_reservation -q`; covers the legacy-mode refusal and the no-mutation pin (unittest has no boolean -k grammar; multiple -k flags OR together)

- [ ] Run → expect RED: `grep -c "test_launch_refuses_incomplete_contract_before_reservation_legacy_mode" scripts/test_execute_plan_runtime.py` returns 0 [class: REPOSITORY_TEST]
- [ ] In `_launch_claimed_task` (the function containing the `worker_contract is None` blocked return; `launch_next_task` delegates to it), immediately after that blocked return: refuse with a named blocked outcome (message containing `worker contract is incomplete`, naming the task) when the contract's `allowed_paths`, `required_criteria`, or `validation_commands` is empty, before any reservation write (the `_outcome` blocked return mutates nothing; enforcement mode already refuses incomplete contracts via the existing contract-None path, so the new message arms the legacy leg) [class: IMPLEMENTATION_REQUIRED]
- [ ] Migrate the fixtures the new refusal reaches (measured at 64 newly broken tests in the r1 simulation, so this item is load-bearing, not cosmetics): enrich the legacy launch fixtures with non-empty `required_criteria`/`verification_commands` via the existing `verification_fields` helper and the `_worker_prompt_fixture` pattern; update `disjoint_tasks` centrally so every batch/parallel group fixture launches; re-point `test_retry_after_contract_violation_success_lands_done_pending` and `test_contract_violation_gets_one_driver_owned_retry` at a non-empty contract, keeping one of them as the boundary-order regression witness (with the boundary check in place the adapter is no longer reachable with an empty contract) [class: IMPLEMENTATION_REQUIRED]
- [ ] Touch up the contract doc's `required_criteria` wording (`agents/skills/execute-plan/runtime-contract.md` line 286, "Tasks may declare immutable `required_criteria` and `verification_commands`") so the documented legacy shape matches the new refusal [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_launch_refuses_incomplete_contract_before_reservation_legacy_mode` (legacy manifest, task with empty criteria and commands; blocked with the named message) and `test_launch_refusal_leaves_no_reservation_state` (after the refused launch, the claim stays `claimed`, the task stays unlaunched, no worker entry or launch id recorded) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command and, after the fixture migration item, the full suite green (the baseline is 652 tests OK) [class: REPOSITORY_TEST]
- [ ] Commit: `runtime: launch refuses an incomplete worker contract before reservation` [class: IMPLEMENTATION_REQUIRED]

### Task 2: checked checklist actions classify like unchecked ones

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k checked_checklist -q`; covers the new refusal

- [ ] Run → expect RED: `grep -c "test_checked_checklist_action_requires_classification" scripts/test_execute_plan_runtime.py` returns 0 [class: REPOSITORY_TEST]
- [ ] In the seeding-time collector, widen the checklist regex from `\[ \]` to `[[ xX]]` boxes (the capture group stays the action text), so checked action lines feed the same classification requirement: an unclassified checked action raises the same named seeding error, and a classified set must now cover checked and unchecked lines together [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_checked_checklist_action_requires_classification` (task body with a `- [x]` action and no `checklist_actions` refuses seeding with the named error; adding the classification record seeds cleanly) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command; full suite green [class: REPOSITORY_TEST]
- [ ] Commit: `runtime: checked checklist actions classify at seeding` [class: IMPLEMENTATION_REQUIRED]

### Task 3: recovery receipt survives a non-mapping successor

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k non_mapping_successor -q`; covers the crash guard

- [ ] Run → expect RED: `grep -c "test_recovery_receipt_non_mapping_successor_returns_false" scripts/test_execute_plan_runtime.py` returns 0 [class: REPOSITORY_TEST]
- [ ] In `_claim_retired_by_evidence_recovery`'s handoff branch, read `successor = handoff.get("successor")` once and return False (claim stays examined) when it is not a Mapping, before any field access; the refusal carries the token `successor identity is not a mapping` in the branch comment [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_recovery_receipt_non_mapping_successor_returns_false` (history event whose `handoff_recovery.successor` is a string; `_reconcile_startup_locked` completes and the claim stays examined, no exception) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command; full suite green [class: REPOSITORY_TEST]
- [ ] Commit: `runtime: recovery receipt tolerates a non-mapping successor` [class: IMPLEMENTATION_REQUIRED]

### Task 4: recovery receipt binds its full identity

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -k recovery_receipt_binds -k rejects_intent_mismatch -q`; covers the binding and its mismatch shapes

- [ ] Run → expect RED: `grep -c "test_recovery_receipt_binds_intent_successor_owner_and_launch" scripts/test_execute_plan_runtime.py` returns 0 [class: REPOSITORY_TEST]
- [ ] First, verify the provider terminal receipt and session identity fields the recovery origin names by reading the intent record's terminal/launch-receipt shape at its persist site; record the found field names in the task log before wiring their validation [class: REPOSITORY_TEST]
- [ ] In `_claim_retired_by_evidence_recovery`'s handoff branch, after the existing checks: resolve the intent record by `handoff.intent_id` (scan `manifest["handoff_intents"]` values, the uniqueness-scan precedent) and refuse (return False, claim stays examined, comment token `recovery receipt does not bind the recorded intent`) when the intent is missing, or when the receipt-level `token`/`generation` disagree with the intent's `prior` block (plus a `handoff_recovery.prior` block, when the production writer recorded one, must match the intent's `prior` too), or when the successor's `claim_owner_id` or `launch_id` is absent or disagrees with the resolved intent's `successor` block - the successor describes the retired claim, so the intent is the only sound binding target (a post-recovery re-claim mints fresh owner/launch id, and no current-claim equality is prescribed); bind `receipt.worker_session_id == intent.launch_receipt.provider_session_id` when the intent carries a launch receipt, and presence-check the receipt-side `provider_terminal_receipt_id` [class: IMPLEMENTATION_REQUIRED]
- [ ] Update `test_retired_evidence_claim_admits_by_latest_matching_receipt` on BOTH sides: the admitted receipts' `handoff_recovery.successor` blocks gain `claim_owner_id`/`launch_id` (the production writer always emits all five successor keys), and their manifests gain the matching resolvable `handoff_intents` entry (intent_id `intent-1`, `prior` matching the receipt's token/generation, `successor` mirroring those values); one new refusal arm pins the identity-incomplete shape (receipt naming an unknown intent id), cross-referencing the mismatch pin below [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_recovery_receipt_binds_intent_successor_owner_and_launch` (a receipt whose successor owner/launch id match the resolved intent's successor block admits retirement) and `test_recovery_receipt_rejects_intent_mismatch` (each shape refuses: unknown intent id, successor owner flipped, successor launch id flipped) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command; full suite green [class: REPOSITORY_TEST]
- [ ] Commit: `runtime: recovery receipt binds successor owner and launch to the intent` [class: IMPLEMENTATION_REQUIRED]

### Task 5: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers all five pins, the three refusal tokens, the collector regex, and the em-dash gate

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
