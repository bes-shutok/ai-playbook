# Plan: Reconcile a completed task handoff against reviewed plan bytes
Backlog origin: docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-29-plan-review-execute-plan-plan-digest-handoff-drift-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.75h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-execute-plan-plan-digest-handoff-drift.md (session 01a1875f-5fcf-74f2-8a58-18f079231711)

## Terms

- **Done-pending handoff:** the accepted worker completion is recorded as terminal, but the run has not yet committed and advanced the task boundary.
- **Reconciliation receipt:** a durable record on one `runtime_state.json` `tasks[task_id]` entry, binding the current reviewed plan digest, launched task-scope digest, task identity, accepted terminal completion evidence, and observed task checkbox projection before runtime state advances.
- **Task checkbox projection:** the runtime's per-task completion state derived from the checklist for that task in the plan.
- **Task-scope digest:** a hash of the complete task section delivered to the worker, with only the `[ ]`/`[x]` marker normalized away so completion marking does not change the worker's assigned scope.

## Why

The witnessed Task 1 handoff reached `done-pending` while later plan corrections changed the plan digest and the task checkbox projection. Preflight then refused the combination of terminal handoff, stale digest, and mismatched task state, without offering a continuation. The existing `recover-task-scope` path repairs a reviewed digest mismatch before launch, but it does not reconcile a completed worker's terminal receipt with checkbox changes at the done boundary. Manual runtime-manifest edits are prohibited, so this recovery must be owned by the execution runtime, bind the worker's launched task scope, and leave the existing done commit gate in place.

## Gist & Examples

Title: Reconcile a completed task handoff against reviewed plan bytes

TLDR: Add an execution-runtime recovery transition that uses a receipt to reconcile an accepted `done-pending` task with the exact reviewed plan digest, launched task scope, and checkbox projection, improving code quality.

Before: A task may have accepted terminal completion evidence while reviewed plan corrections change its digest or checkboxes; preflight sees inconsistent runtime state and offers no canonical continuation.

After: The runtime validates a reconciliation receipt against current plan-review evidence, the worker's launched task scope, terminal completion evidence, and the task's checklist projection, then atomically updates the manifest before rerunning ordinary preflight and the done commit gate.

Edge cases: Stale review evidence, changed task scope, a changed checkbox projection not covered by the reviewed bytes, a missing terminal receipt, or a changed manifest generation refuses without mutating state; after a successful atomic update, an identical retry reports already reconciled without another write.

## Outcome

An execution-runtime-owned, receipt-backed transition reconciles only a valid `done-pending` task whose reviewed plan bytes, launched task scope, task identity, completion evidence, and checkbox projection agree. The transition preserves the worker's terminal receipt and runs through the ordinary preflight and done commit gate before another task can start.

- A valid completed task can resume through the canonical continuation without hand-editing the runtime manifest.
- Stale review evidence, changed scope, unreviewed checkbox changes, and interrupted writes leave the accepted worker receipt intact and runtime state recoverable.

Gate delta: Add one receipt-backed `done-pending` recovery protocol and the per-task `task_scope_digest` and `handoff_reconciliation` fields under `runtime_state.json`'s `tasks[task_id]`; the existing execution claim and parent-only sequential writer serialize it, with no new lock, ordinary dispatch gate, or fence. The backlog records one witnessed incident; catch frequency is one, a false refusal costs another recovery attempt while preserving terminal evidence, the current guard-liveness ledger ratio is 29:48, and use is reviewed by 2026-11-29 for removal if existing paths cover the case. Preflight and the done commit gate remain unchanged, and no existing refusal, check, or field is removed.

## Assumptions

- The host-native execute-plan orchestrator remains the sole caller and owner of `runtime_state.json`; a new helper owns only validation and atomic reconciliation for this `done-pending` recovery. The existing run claim excludes a second live plan run, and the parent-only sequential writer contract excludes overlapping same-run mutations. `scripts/execute_plan_runtime.py` remains manifest-free and does not regain recovery or worker-launch ownership. Evidence: that module's docstring and execute-plan's Task state section.
- The existing `recover-task-scope` path remains the remedy for reviewed scope or digest mismatches before task launch. This plan handles only accepted `done-pending` completion handoffs. Evidence: the backlog's workaround assessment and the execute-plan runtime contract.
- The historical runtime state at generation 9 and the preflight output may be unavailable in a fresh checkout because they are under `docs/tmp/`; the tracked backlog witness remains the incident record. No implementation may depend on reconstructing that ignored state.
- The current plans review record is the authority for plan bytes; a reconciliation receipt cannot make stale review evidence current or authorize changed task scope.

Decision points requiring a grill: none remain. Maintenance-selected authorization resolves the implementation as a bounded recovery transition in the current execute-plan runtime, with no additional dispatch gate; the existing completion gate remains authoritative.

## Evaluation Criteria

- **Correctness:** The transition binds an exact plan digest, task identity, accepted terminal worker receipt, review evidence, and task checkbox projection, and applies the manifest update atomically.
- **Recovery safety:** Every mismatch refuses without partial mutation; an accepted terminal receipt is preserved; retry is possible after review or state is repaired.
- **Scope control:** Prelaunch `recover-task-scope`, ordinary preflight, the done commit gate, worker execution, and unrelated resume-watcher behavior keep their existing contracts.
- **Done when:** Focused runtime regressions cover successful reconciliation and each refusal class; execute-plan documentation specifies the writer, receipt, ordering, and recovery outcomes; relevant pin and hygiene checks pass.
- **Ship when:** No external release or human-owned prerequisite applies.

## Review Scope

**Production:**
- `scripts/reconcile_execute_plan_handoff.py` *(new)* (bounded `done-pending` receipt validation and serialized state transition)
- `agents/skills/execute-plan/SKILL.md` (add the receipt-backed recovery transition to the Phase 1 task-state and preflight flow)
- `agents/skills/execute-plan/runtime-contract.md` (document the runtime state transition and its failure outcomes)

**Tests and checks:**
- `scripts/test_reconcile_execute_plan_handoff.py` *(new)* (successful atomic transition, exact evidence binding, preserved terminal receipt, refusal without mutation, concurrent/stale generation)
- `scripts/test_execute_plan_resume_watcher.py` (confirm the new recovery leaves watcher identity and digest fences intact)
- `scripts/check_maintenance_pins.sh` (pin the new done-pending recovery arm in the Phase 1 flow and its separation from prelaunch scope recovery)

**Records:**
- `docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md` (Task 3; fold into the archived plan's disposition section and remove the living row at completion)

## Validation Commands

```bash
set -eo pipefail
python3 -m pytest scripts/test_reconcile_execute_plan_handoff.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_execute_plan_resume_watcher.py'
bash scripts/check_maintenance_pins.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-29-execute-plan-plan-digest-handoff-drift.md
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/runtime-contract.md
bash scripts/check-no-em-dash.sh file scripts/reconcile_execute_plan_handoff.py
bash scripts/check-no-em-dash.sh file scripts/test_reconcile_execute_plan_handoff.py
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Add an atomic receipt-backed done-pending reconciliation operation

Context surface: The accepted task terminal receipt and `tasks[task_id]` record in `runtime_state.json`, plan task identity and checklist, and the latest valid plan-review evidence for the active plan digest.

Files:
- `scripts/reconcile_execute_plan_handoff.py` *(new)*
- `scripts/test_reconcile_execute_plan_handoff.py` *(new)*
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `HandoffReconciler` in `scripts/reconcile_execute_plan_handoff.py`, which validates the recovery receipt and owns the atomic per-task manifest transition.
- `main` in `scripts/reconcile_execute_plan_handoff.py`, which exposes the bounded recovery operation to the host-native orchestrator.

- [x] Define and validate a reconciliation receipt on the corresponding `tasks[task_id]` entry, binding run and plan identity, task identity, expected manifest generation, exact current plan digest, launched task-scope digest, accepted worker terminal receipt, review evidence, and observed task checkbox projection. [class: IMPLEMENTATION_REQUIRED]
- [x] Store that task's receipt and reconciled projection in the same atomic `runtime_state.json` replacement; preserve every other task record and receipt so later task completion cannot overwrite earlier evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a bounded helper that accepts only a `done-pending` task, re-derives receipt inputs from disk, and owns only validation and reconciliation; the host-native orchestrator remains the helper's sole caller and owns every other runtime-state update. [class: IMPLEMENTATION_REQUIRED]
- [x] Require the active execution claim and the host-native parent's foreground, sequential invocation; re-read run identity, task identity, task-scope digest, and expected manifest generation immediately before atomic replacement, refusing on drift. No worker or other helper invocation writes this runtime state. [class: IMPLEMENTATION_REQUIRED]
- [x] Add an admission matrix proving each recovery precondition independently: a missing or foreign active claim and any task state other than `done-pending` each produce a named refusal with unchanged manifest and terminal-receipt bytes, while the same claimed task in `done-pending` reaches reconciliation. If the claim is enforced only by the parent, prove the helper cannot be reached before claim acquisition. [class: REPOSITORY_TEST]
- [x] If a retry finds that `handoff_reconciliation` exactly matches the requested receipt and the reconciled task projection, return `already-reconciled` success without another write or generation increment; otherwise refuse stale generation or mismatched evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a changed-scope regression that keeps run, plan, and task identifiers constant, changes task text beyond checkbox markers after launch, and asserts a named refusal with unchanged manifest and terminal-receipt bytes. [class: REPOSITORY_TEST]
- [x] Add a legacy `done-pending` regression with no `task_scope_digest` field: recover the launch scope only from exact plan bytes whose digest equals the run's saved launch `plan_digest`; refuse as `launch-scope-unverified` without mutation when no such bytes or exact launch record exist. [class: REPOSITORY_TEST]
- [x] Add focused regressions for a readable per-task receipt, each refusal class, same-receipt retry after an interrupted response, atomic-write failure, and stale-generation refusal; prove refusals preserve manifest and terminal-receipt bytes and interrupted writes leave either the old manifest or the complete new task receipt and projection. [class: REPOSITORY_TEST]
- [x] Reconcile two distinct tasks in sequence and verify the second transition preserves the first task's scope digest and receipt. [class: REPOSITORY_TEST]
- [x] Add an end-to-end fixture proving that a corrected and freshly reviewed `done-pending` task reconciles, passes preflight, receives the canonical next continuation, and still requires the ordinary done commit gate. [class: REPOSITORY_TEST]
- [x] Verify the recovery does not weaken resume-watcher identity and digest fences or permit manual manifest edits; preserve the accepted worker terminal receipt across the complete flow. [class: REPOSITORY_TEST]
- [x] Commit: `fix: reconcile reviewed done-pending handoffs` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Connect the recovery operation to the execute-plan done-pending flow

Context surface: The Phase 1 task-state and preflight steps in `agents/skills/execute-plan/SKILL.md` and the Sequential native execution contract in `agents/skills/execute-plan/runtime-contract.md`; this task introduces the done-pending recovery arm and connects it to the existing done commit gate.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/check_maintenance_pins.sh`

- [x] Before a new worker receives its prompt, record the normalized task-scope digest in that task's `runtime_state.json` record. For legacy `done-pending` tasks lacking the field, derive the digest only from an exact task-launch record or historical plan bytes matching the saved launch `plan_digest`; refuse as `launch-scope-unverified` when neither source proves the worker's scope. [class: IMPLEMENTATION_REQUIRED]
- [x] Document when the orchestrator creates and invokes the receipt-backed recovery, the per-task `task_scope_digest` and `handoff_reconciliation` fields, the same-replacement write, the preservation of other task entries, and the exact `already-reconciled` retry response. [class: IMPLEMENTATION_REQUIRED]
- [x] Require ordinary preflight and the existing done commit gate to pass after reconciliation and before advancing to the next task; keep prelaunch `recover-task-scope` as the separate remedy for prelaunch scope/digest mismatches. [class: IMPLEMENTATION_REQUIRED]
- [x] Specify the fail-closed recovery result for stale reviews, changed scope, unreviewed checkbox changes, missing legacy scope proof, and interrupted writes, preserving the terminal receipt and requiring fresh review or state recovery as appropriate; require ordinary preflight and the done commit gate after both a new reconciliation and an `already-reconciled` retry. [class: IMPLEMENTATION_REQUIRED]
- [x] Add section-scoped pins ensuring the done-pending reconciliation flow is present and remains distinct from prelaunch recovery; run the pins check. [class: REPOSITORY_TEST]
- [x] Commit: `docs: specify done-pending reconciliation recovery` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Verify the handoff lifecycle and record the disposition

Context surface: The origin backlog row and this plan's completed runtime and integration evidence.

Files:
- `docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md`

- [x] Flip the origin to `Status: covered (<plan path>)` only after all acceptance evidence passes; leave independent prelaunch workaround behavior unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: cover completed task handoff origin` [class: IMPLEMENTATION_REQUIRED]

**Origin disposition:** At completion, fold the covered backlog row into the archived plan's `## Disposition of migrated backlog items` section and remove the living origin in the same completion pass.

## Delivered deviations (r1 2026-11-02, durable record)

- Task 1 checkbox 7 / Task 2 checkbox 1: the delivered launch-scope proof implements only the historical-plan-bytes source; the "or exact launch record" alternative was narrowed away (fail-closed; no current writer produces the exact launch record the alternative required).
- Task 2 checkbox 3: prelaunch recover-task-scope is retired rather than kept as a separate remedy; delivered docs route prelaunch scope/digest mismatches to the Reviewed task-scope change referral and the Step 0.5 fresh-review path (grep confirms recover-task-scope had no remaining main-tree home; the substitution is coherent and fail-closed).

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md: covered by this plan; deleted from the living backlog at this plan's archive per the covered-row rule (this section is the durable home of the row's disposition). Delivered deviations over the row's original criteria are recorded in this plan's "Delivered deviations" section.
