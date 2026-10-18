# Plan: Execute-plan lifecycle recovery gaps (reviewed-scope resumption, out-of-scope plan-edit disposition, status-question guard, Codex corrected submission)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-04-execute-plan-done-pending-scope-refresh.md
- docs/history/backlog/2026-10-04-codex-worker-malformed-result-recovery-gap.md
- docs/history/backlog/2026-10-04-execute-plan-status-question-interrupts-run.md

Driving force: reliability (justification: reliability is not one of the five driving principles; this plan is implemented anyway because all three origins are witnessed reliability failures in the core execute-plan lifecycle, two reproduced during the 2026-10-05 service-repo execution run, and each strands completed, verified work behind a claim shape no sanctioned operation accepts; park-triage would not take it because the blockers are live on the primary execution lane)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-execute-plan-lifecycle-recovery-gaps-r*.md (the highest rN is the authoritative record, including any deferred-residual list; the staging records are gitignored and migrate to the primary checkout's reviews home at closeout)

## Terms

- Reviewed scope: the `Files:` declaration of a task in the currently reviewed plan bytes; the review-digest-bound set a claim's `allowed_paths` must match before launch.
- Done-pending requeue: the `recover-done-pending` disposition that closes the terminal worker claim and returns the task to `pending` so a fresh claim can continue it.
- Claimed prelaunch shape: a claim in `claimed` state with a prepared intent and an unconsumed binding, the only shape today's `recover-task-scope` accepts.
- Done boundary: the driver's terminal checkpoint that verifies the task commit's first-parent paths against the claim's allowed set and the committed source digest against the captured verification receipts.
- Evidence envelope: the closed-schema machine-verifiable result a worker must return (command identities, output references, test identities, changed paths, criterion coverage); verification of it is driver-side.
- Claim fencing: the invariant that a claim's identity, generation, and scope tokens gate every mutation, so stale or foreign state never writes.
- Prelaunch binding: the prepared handoff intent a launch consumes; the worker-start receipt consumption is what lets a checkpoint claim its owner.
- Worker-start receipt: the launch-side evidence consumed against the prelaunch binding; a checkpoint without its consumed receipt refuses owner-mismatch.
- Recovery-transition machinery: the shared locked single-write, validate-before-persist, receipt-appending discipline the existing recover operations run under.
- Out-of-scope plan edit: a valid plan-file change (checkbox marks, review fixes) inside a task-scoped commit whose claim's allowed paths exclude the plan path; the done boundary returns `commit-pending` with `out-of-scope committed change` and `resume_allowed: false`.
- Corrected submission: a driver-owned re-request of the closed-schema evidence envelope from an already-terminal worker session under the live claim token and generation, verified with unchanged fail-closed semantics.
- Status question: an operator or agent turn asking for run state; never a stop, pause, or abort request.

## Why

Three witnessed lifecycle failures strand completed work: a requeued done-pending task cannot acquire its reviewed scope because the only scope-recovery route requires the pre-launch claim shape the requeue destroyed; a task commit carrying a valid plan edit is refused at the done boundary with no supported recovery, while the done pre-commit sweep rejects the same edit left unstaged; and a status question was misread as a stop request, persisting a false `user_interrupt` that suppresses scheduled continuation. A fourth related shape leaves a terminal-but-malformed Codex worker's successful implementation behind a live claim with no concrete corrected-submission route and no path past the worker-start binding fence.

## Outcome

Each witnessed shape has one sanctioned, fenced exit that preserves claim fencing and completed work.

- A requeued done-pending task's fresh claim receives exactly the reviewed `Files:` paths before launch, so reviewed widenings continue instead of wedging on scope drift, and the following preflight passes and the next claim launches with that scope.
- A terminal commit rejected for an out-of-scope plan edit is recoverable through a receipt-keyed done-boundary exception that preserves the implementation commit and the reviewed plan bytes, and the done pre-commit sweep admits the required plan-checkbox edit through the same disposition without widening the task's allowed paths.
- A status question produces a concise state report and continuation; only an explicit stop, pause, or abort request authorizes the `interrupt` mutation, pinned by a skill-contract guard in the established doc-probe pattern.
- A terminal worker whose final response is malformed has a driver-owned corrected-submission route for the Codex host shape whose acceptance also consumes the pending worker-start binding, so the resulting checkpoint no longer refuses owner-mismatch; the refusal text names the route.

Gate delta: adds two recovery operations and one corrected-submission operation inside the existing recovery-transition machinery, plus one done-sweep staging admission arm inside the existing post-landing-staging gate, plus one skill doc-probe pin; each new refusal-checked transition is priced by its paying sibling arm (the intent-backed `recover-task-scope` transition, whose locked single-write shape, derive-from-repository-state rule, and receipt discipline the two recovery operations reuse, with a different identity anchor stated per operation; the existing driver-side evidence verifier, whose fail-closed semantics the corrected submission reuses unchanged; the sweep gate's existing record-only allowlist precedent, whose owned-paths admission shape the staging arm extends); no manifest schema shape change (each operation's write inventory is enumerated in its task step and stays within existing fields), no new fence family, and the skill edit replaces an under-specified sentence rather than adding a gate.

## Assumptions

- A1: The recovery transitions derive plan bytes, review readiness, declaration paths, commit paths, and claim identity from repository state and the manifest only, never from caller-supplied scope (the existing `recover-task-scope` rule, preserved and extended).
- A2: Every refusal leaves the manifest byte-identical and appends no receipt; every accepted transition lands its whole mutation set in one locked manifest write validated before persistence (the existing `_persist_recovery_transition` discipline). Task 3's bounded-attempts exhaustion arm is an accepted transition with its own receipt, not a refusal, so A2 holds for every path.
- A3: The status-question guard is a skill-contract clarification pinned by a doc-content probe in the suite's established pattern, plus a first-class regression pin that the `interrupt` operation persists `user_interrupt` when invoked; the runtime operation keeps its machine contract because authorization lives at the agent-workflow layer that decides to invoke it.
- A4: The Codex corrected submission is driver-owned: the driver constructs and runs the adapter's append-prompt resume command through the adapter resume seam with a bounded deadline, argv-list no-shell construction, and a driver-constant prompt; the fresh envelope is verified by the existing driver-side verifier with unchanged fail-closed semantics; the manifest lock releases across the adapter I/O window and the manifest is re-read under the claim drift fence before the nested write (the existing resume path's pattern); the parent never hand-crafts worker prompts.
- A5: The out-of-scope plan-edit recovery uses a receipt-keyed done-boundary exception, never allowed-path widening: the disposition receipt records the plan path, the commit identity, and the accepted edit class; the done boundary accepts a committed plan path covered by a receipt whose commit identity matches and no superseding disposition receipt exists for the same plan path with the reviewed digest unchanged, and refuses when the commit changed since; the committed-source-digest gate keeps its original allowed-set basis with the excepted plan path excluded; the existing commit is never rewritten; narrowing keeps today's ordinary-preflight semantics and the new operation refuses the narrowing shape as a fence-shape mismatch.
- A6: The accepted plan-edit classes are exactly: a checkbox-marker-only delta against the reviewed digest (the existing marker-only classifier), or plan bytes covered by a fresh ready review round; substantive drift still refuses.
- A7: The three transitions are new operations rather than extensions of existing hosts, on this basis: the reviewed-scope acquisition operates on a claim-less requeued shape keyed to the requeue receipt's recorded prior claim identity, while `recover-task-scope` requires the live intent-backed claimed prelaunch shape and keys its replay fence on prior token and generation; the out-of-scope recovery keys on a commit identity and disposition receipt, while `recover-done-pending`'s disposition set operates on the terminal worker claim's task state; and no existing operation owns an adapter-mediated terminal-session resume under a live launched claim.
- A8: Launch-time worker-start receipt capture stays out of scope; the in-scope repair is the after-launch consumption arm Task 3 adds (the origin's own "or document an equivalent receipt path" branch). Two origin quality observations (the missing implement-log detection before checkpoint acceptance, and review-only checks not comparing an example against the wire schema) are parent-workflow quality gaps, not recovery exits, and stay out of scope.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the execute-plan runtime gains the three missing recovery exits the witnessed service-repo run had to improvise around (reviewed-scope resumption after done-pending requeue, out-of-scope plan-edit disposition at the done boundary and the done sweep, Codex corrected submission whose acceptance consumes the worker-start binding) and the skill gains the status-question rule, per the reliability force.

- Witnessed widening: Task 1's reviewed `Files:` gained `scripts/generate-schema-contracts.sh`; `recover-done-pending requeue` returned the task to `pending` with the seeded allowed paths unchanged, the next preflight blocked on scope drift, and `recover-task-scope` refusing because the fresh claim shape is not the intent-backed prelaunch shape.
- Witnessed plan edit: Task 1's commit included the plan document; the done boundary returned `commit-pending`, `resume_allowed: false`, `out-of-scope committed change`; later the same run's Task 3 could neither leave the plan checkbox edit unstaged (the done pre-commit sweep rejects) nor stage it (the claim fence rejects the plan path).
- Witnessed malformed response: the Codex worker completed implementation and verification, returned prose instead of the evidence envelope (including a false claim that child-side `git add` failed); the driver named criteria missing, the claim stayed launched, and no documented operation accepted the terminal-worker-with-live-claim shape; a later verified checkpoint was refused owner-mismatch because the launch binding had no consumed worker-start receipt.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: each new transition accepts exactly the witnessed shape and refuses stale identities (keyed per operation: the requeue receipt's recorded prior identity for the acquisition; the launch-window eligibility conjuncts including launch-record evidence, worker rows, and reservations), unreviewed or changed plan bytes outside the accepted edit classes, malformed or empty scope, unsupported recovery shapes, and replays after superseding state, with byte-identical refusals and one locked write on acceptance.
- Completeness: every recovery exit demanded by the origins' Expected paragraphs is either implemented or named in the exclusions with its reason; the pins cover widening before launch, terminal worker recovery, fresh preflight passing after the recovery, the next claim launching with the stamped scope, terminal out-of-scope-plan-commit recovery, the done-sweep staging admission, stale identity, review drift, malformed scope, replay, the narrowing shape, and group-member boundaries.
- Reliability: no manual manifest edits anywhere in the flows; verified work is never rotated away; unverified checkpoints stay refused; the corrected submission cannot hang the lane (deadline) or interpolate into a shell (argv list).
- Simplicity: the new transitions reuse the existing recovery-transition machinery, receipt discipline, and driver-side evidence verifier; no parallel mechanism is introduced.

**Done when:**

- The full Validation Commands block exits 0, including the new pins.
- Each recovery transition is witnessed red against the current runtime (the witnessed shapes refuse or strand today) and green after its task; the Task 2 doc probe is red against the current User Interruption bytes and its record_interrupt regression pin is declared green-on-arrival regression coverage.
- The status-question guard pins the new User Interruption decision text (status question reports state and continues; only an explicit stop, pause, or abort authorizes the `interrupt` mutation) and the existing interrupt behavior, consistent with the authorization-layer assumption.

**Ship when:**

- The next execute-plan run that hits one of the witnessed shapes resolves it through the named exit without improvisation; no cross-team condition applies.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py`
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/runtime-adapters/codex.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/done/SKILL.md`

**Tests:**
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_done_sweep_gates_lib.py`

**Machinery:**
- `scripts/check_maintenance_pins.sh` (re-keying any span the touched literals move; no pin exists over the touched runtime or User Interruption literals today)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Adapter implementations other than the Codex host shape; reason: the witnessed corrected-submission gap is Codex-specific and the adapter contract stays host-pluggable.
- Launch-time worker-start receipt capture redesign; reason: this plan delivers the origin's documented equivalent-receipt path (Task 3's consumption arm); the capture redesign is separately scoped work.
- The missing implement-log detection before checkpoint acceptance and review-only wire-schema comparison; reason: parent-workflow quality gaps, not recovery exits.
- New backlog rows captured during execution under `docs/history/backlog/`; reason: sanctioned Step 1.2b captures ride the done commit and are excluded from the scope check by name pattern.

## Validation Commands

Authoring-time gate runs recorded: the em-dash touched-mode gate, the public-hygiene scan, and `plan_readiness.py --pre-round` each exited 0 against the drafted bytes before the first review round; the rule-22 mechanical audit over the Validation block (`bash -n` on the extracted block) passed; the block derives its merge base from the facts document's `base_branch` (falling back to `main`), so no branch name is hardcoded.

```bash
cd "$(git rev-parse --show-toplevel)"
base_branch="$(sed -n 's/^base_branch = "\([^"]*\)"/\1/p' .ai-playbook/facts.md)"
base_branch="${base_branch:-main}"
base="$(git merge-base "$base_branch" HEAD)" || { echo "FAIL: merge-base"; exit 1; }
python3 scripts/test_execute_plan_runtime.py || { echo "FAIL: full driver suite"; exit 1; }
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo "FAIL: done sweep gates suite"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base "$base" -- scripts/execute_plan_runtime.py scripts/done_sweep_gates_lib.py scripts/test_execute_plan_runtime.py scripts/test_done_sweep_gates_lib.py agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/runtime-adapters/codex.md agents/skills/execute-plan/subagent-prompts.md agents/skills/done/SKILL.md scripts/check_maintenance_pins.sh || { echo "FAIL: em-dash added-lines"; exit 1; }
( cd "$(git rev-parse --show-toplevel)" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" --files scripts/execute_plan_runtime.py scripts/done_sweep_gates_lib.py scripts/test_execute_plan_runtime.py scripts/test_done_sweep_gates_lib.py agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/runtime-adapters/codex.md agents/skills/execute-plan/subagent-prompts.md agents/skills/done/SKILL.md scripts/check_maintenance_pins.sh ) || { echo "FAIL: hygiene scan"; exit 1; }
changed="$(git diff --name-only "$base" -- .)" || { echo "FAIL: git diff"; exit 1; }
allowed="$(printf '%s\n' "$changed" | grep -v -x -e 'scripts/execute_plan_runtime.py' -e 'scripts/done_sweep_gates_lib.py' -e 'scripts/test_execute_plan_runtime.py' -e 'scripts/test_done_sweep_gates_lib.py' -e 'agents/skills/execute-plan/SKILL.md' -e 'agents/skills/execute-plan/runtime-contract.md' -e 'agents/skills/execute-plan/runtime-adapters/codex.md' -e 'agents/skills/execute-plan/subagent-prompts.md' -e 'agents/skills/done/SKILL.md' -e 'scripts/check_maintenance_pins.sh' -e 'docs/history/plans/2026-10-05-execute-plan-lifecycle-recovery-gaps.md')" || true
scope_violations="$(printf '%s\n' "$allowed" | grep -v -E '^docs/history/backlog/[0-9]{4}-.*\.md$')"
grep_rc=$?
if [ "$grep_rc" -ge 2 ]; then echo "FAIL: scope check tool error rc=$grep_rc"; exit 1; fi
if [ -n "$scope_violations" ]; then echo "FAIL: unexpected tracked change:"; echo "$scope_violations"; exit 1; fi
```

### Task 1: Reviewed-scope resumption after done-pending requeue, and the out-of-scope plan-edit recovery

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/done/SKILL.md`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `python3 scripts/test_execute_plan_runtime.py ReviewScopeResumptionRecoveryTest`; covers the requeued-claim reviewed-scope acquisition (exact reviewed paths stamped, evidence contract digest recomputed, receipt keyed to the requeue receipt's recorded prior claim identity), the post-recovery fresh preflight passing and the next claim launching with the stamped scope, the terminal out-of-scope-plan-commit recovery through the receipt-keyed done-boundary exception, and the stale-identity, launch-window eligibility, review-drift, malformed-scope, plan-path-in-declaration, narrowing-shape, and replay refusals.
- `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` (the established venv-first runner, falling back to `python3`); covers the done pre-commit sweep's admission of the disposition-covered plan-checkbox edit beside the existing record-only allowlist behavior.

- [x] `ReviewScopeResumptionRecoveryTest#test_requeued_task_acquires_reviewed_scope_before_launch`; given a done-pending task requeued via `recover-done-pending` after a reviewed `Files:` widening, expects the new acquisition operation to stamp exactly the reviewed declaration paths, recompute the evidence contract digest, append one receipt keyed to the requeue receipt's recorded prior claim identity, and the following preflight to pass and the next claim to launch with that scope; given a stale identity, a launch-window occupant, drifted plan bytes, a declaration containing the plan path, a narrowing shape, or a replay after superseding state, expects byte-identical refusals. Full recipe: [class: REPOSITORY_TEST]
- [x] `ReviewScopeResumptionRecoveryTest#test_out_of_scope_plan_edit_recovery`; given a launched task whose commit contains a checkbox-marker-only plan edit absent from the allowed paths, expects the disposition operation to accept one receipt (plan path, commit identity, edit class) and the done boundary to accept the commit with the plan path excepted and the source-digest gate keeping its original basis; given a commit changed since the receipt or substantive plan drift, expects refusal. Full recipe: [class: REPOSITORY_TEST]
- [x] **Step 1 (RED):** Add `ReviewScopeResumptionRecoveryTest` to `scripts/test_execute_plan_runtime.py` covering, with the suite's fixture machinery: (a) the requeued-claim reviewed-scope acquisition with its full refusal ladder (the requeue persist call at `recover-done-pending requeue` is the witness that allowed paths stay stale today), the post-recovery fresh preflight pass, and the next-claim launch carrying the stamped scope in its policy token; (b) the terminal out-of-scope-plan-commit recovery through the receipt-keyed exception with its commit-identity fence and evidence-basis rule; (c) group-member boundaries mirroring the single-claim arms. RED contract: today every scenario in (a) and (b) strands or refuses with no sanctioned exit (the origin rows' executed witnesses). [class: REPOSITORY_TEST]
- [x] **Step 1b (RED):** Add the sweep-admission case to `scripts/test_done_sweep_gates_lib.py`: a done pre-commit sweep whose only unstaged residue is a plan-path edit whose worktree-vs-HEAD diff classifies checkbox-marker-only passes (the sweep classifies the residue in place against the A6 class; the disposition receipt is required only at the done boundary for committed paths), beside the existing record-only allowlist behavior. RED contract: today the gate rejects that residue (the witnessed `post-landing-staging` rejection). [class: REPOSITORY_TEST]
- [x] **Step 2 (GREEN):** Implement in `scripts/execute_plan_runtime.py` inside the existing recovery-transition machinery: (a) the acquisition operation (write inventory: task allowed_paths stamp from the reviewed declaration, evidence contract digest recompute, one receipt; identity anchored on the requeue receipt's recorded prior claim identity; the launch-window eligibility conjuncts restated for the claim-less shape (the task's own historical launch record and released terminal worker rows are accepted witnessed-shape residue; the conjuncts refuse only live window evidence: a live claim's launch record, a live worker row, a held reservation, or live claim-group ownership); the plan-path-in-declaration and narrowing-shape refusals); (b) the disposition operation (write inventory: one receipt recording plan path, commit identity, and edit class; the done boundary's exception read in the same file) with the accepted edit classes of A6; per-operation CLI payload validation, dispatch registration, contract-table rows, and the deployment-gap invalid-choice sentence. Extend the done boundary with the receipt-keyed exception (refuse when the commit changed since the receipt) keeping the source-digest basis per A5. Extend `gate_post_landing_staging` in `scripts/done_sweep_gates_lib.py` to admit an unstaged plan-path residue classified checkbox-marker-only in place (the A6 class-1 read; no receipt read needed at the sweep), beside the record-only allowlist, updating its pins. Update `agents/skills/execute-plan/runtime-contract.md` (the Terminal-worker done-pending recovery section, the Reviewed scope recovery paragraph, and the machine-verifiable evidence obligation) and the SKILL.md recovery-route enumerations (`recover-task-scope` row, the done-pending recovery guidance) to name the new exits; update `agents/skills/done/SKILL.md`'s staging-gate prose for the disposition arm. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 2b (commit):** Commit the GREEN state: `runtime: reviewed-scope resumption after done-pending requeue and receipt-keyed out-of-scope plan-edit recovery`. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 3 (verify):** Run the full Validation Commands block; all gates exit 0; the new pins are red against the pre-task runtime and green after. [class: REPOSITORY_TEST]

### Task 2: Status questions never record an interruption

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `python3 scripts/test_execute_plan_runtime.py ContractContentParityTest`; covers the doc probe: the User Interruption section carries the status-question decision text (a status question requires a concise state report followed by continued work; only an explicit user request to stop, pause, or abort authorizes the `interrupt` mutation; an ambiguous turn asks), the replaced blanket sentence is absent, and the workflow-level status-versus-stop example is present.
- `python3 scripts/test_execute_plan_runtime.py`; covers the record_interrupt regression pin (an explicit stop invocation persists `user_interrupt`; declared green-on-arrival regression coverage, not RED).

- [x] `ContractContentParityTest#test_user_interruption_status_question_rule`; given the User Interruption section bytes, expects the status-question decision text, the ambiguous-turn ask rule, the absence of the replaced blanket record-before-stopping sentence, and the status-versus-stop example. Full recipe: [class: REPOSITORY_TEST]
- [x] `RecordInterruptContractTest#test_explicit_stop_persists_user_interrupt`; given an explicit stop invocation of the interrupt operation, expects `user_interrupt` persisted with the recorded timestamp. Full recipe: [class: REPOSITORY_TEST]
- [x] **Step 1 (RED):** Add the User Interruption doc probe to the established skill-bytes pin pattern in `scripts/test_execute_plan_runtime.py` (fragment probes over the section) and add the record_interrupt regression pin as its own test class. RED contract: the doc probe fails against today's User Interruption bytes (the section orders recording an interruption in every interruption state and never states the status-question rule); the record_interrupt pin is green-on-arrival regression coverage, declared as such. [class: REPOSITORY_TEST]
- [x] **Step 2 (GREEN):** In `agents/skills/execute-plan/SKILL.md`'s User Interruption section, state the status-question rule (concise state report followed by continued work), the authorization rule (only an explicit user request to stop, pause, or abort authorizes the `interrupt` mutation), the ambiguous-turn ask rule, and the status-versus-stop example; replace the blanket record-before-stopping sentence the probe pins absent. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 2b (commit):** Commit: `skills: status questions report state and continue, only explicit stop authorizes interrupt`. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 3 (verify):** Full Validation Commands block exits 0; the doc probe is red before the skill edit and green after; the record_interrupt pin stays green throughout. [class: REPOSITORY_TEST]

### Task 3: Codex corrected submission for a terminal malformed final response

Files:
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-adapters/codex.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `python3 scripts/test_execute_plan_runtime.py CodexCorrectedSubmissionTest`; covers the corrected-submission success arm (fresh envelope verified by the driver-side verifier with unchanged fail-closed semantics; the pending worker-start binding consumed with the fresh session's recorded host-invocation evidence; terminal-worker and capacity state reconciled with identity-matched fresh terminal observation on the release arm), the bounded-attempts exhaustion arm (one accepted terminal-disposition receipt, task stays launched, claim fenced, refusal text routes the operator), and the refusal text naming the concrete route.

- [x] `CodexCorrectedSubmissionTest#test_corrected_submission_success_and_exhaustion`; given a terminal worker session whose final response was refused malformed by the driver-side criteria check with the task launched, expects the corrected-submission operation to resume through the adapter resume seam, verify the fresh envelope with unchanged fail-closed semantics, consume the pending worker-start binding, reconcile terminal-worker and capacity state, and admit the resulting checkpoint past the owner-mismatch fence; given two exhausted attempts, expects one terminal-disposition receipt and the claim still fenced. Full recipe: [class: REPOSITORY_TEST]
- [x] **Step 1 (RED):** Add `CodexCorrectedSubmissionTest` to `scripts/test_execute_plan_runtime.py` with the established adapter-fake patterns (a composite fake providing both `resume` and `observe_terminal_evidence`): a terminal worker session whose final response was refused malformed by the driver-side `validate_adapter_result` criteria check, the task launched, the terminal row active. RED: the corrected-submission operation is absent; `resume` selects only blocked tasks, `diagnose` is read-only, and the launch binding's consumption fence refuses the verified checkpoint. [class: REPOSITORY_TEST]
- [x] **Step 2 (GREEN):** Implement the driver-owned corrected-submission operation: it resumes the registered terminal session through the adapter resume seam (the Codex host shape: `codex exec resume <session-id> --json` built as an argv list, no shell, driver-constant re-submit prompt demanding the closed-schema envelope under the live claim token and generation, bounded deadline, bounded output capture); the manifest lock releases across the adapter I/O window and the manifest is re-read under the claim drift fence before the nested write (the existing resume path's pattern); the fresh envelope is verified by the existing driver-side verifier with unchanged fail-closed semantics; acceptance consumes the pending worker-start binding (the origin's documented equivalent receipt path: the fresh session's recorded host-invocation evidence supplies the binding's omitted identity fields) and reconciles terminal-worker and capacity state (release requires the identity-matched fresh terminal observation); the bounded attempts (two) exhaust into one accepted terminal-disposition receipt through the shared persist helper, leaving the task launched and the claim fenced with the refusal text routing the operator; the `required verification criteria missing` refusal text names this concrete route; the single-task-worker role-contract construction states that the terminal message must carry the evidence envelope per the closed schema, that committing and the done step are parent-owned, and that a host denial such as git index access is reported inside the envelope or blocked shape, never converted into narrative; the deployment-gap invalid-choice sentence covers the new operation. Update `agents/skills/execute-plan/runtime-adapters/codex.md` (the resume seam's contract), `agents/skills/execute-plan/subagent-prompts.md` (the return-format clarity mirrored parent-side), and `agents/skills/execute-plan/runtime-contract.md` (the machine-verifiable evidence obligation: the corrected-submission route and the binding consumption). [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 2b (commit):** Commit: `runtime: driver-owned corrected submission for terminal malformed codex responses`. [class: IMPLEMENTATION_REQUIRED]
- [x] **Step 3 (verify):** Full Validation Commands block exits 0; the pins are red before and green after; any re-keyed pinned span updates its owning pin in the same edit. [class: REPOSITORY_TEST]

## Disposition

- Outcome: executed and landed on main (squash commit recorded at landing).
- Tasks 1-3 all complete; every checkbox ticked; the full Validation Commands block exited 0 (driver suite 737 OK, sweep suite 158 passed + 3 subtests, pins pass, em-dash added-lines pass, hygiene scan pass, scope check clean).
- Exec review: r1 two-worker fresh-adversarial (4 findings: 1 Critical + 1 High blocking, 2 Low; all four folded in 9ab76ff7: locked recovery writes, generation fence, corrected-submission owner stamp, in-lock receipt-uniqueness re-checks) then r2 verification-only ready=yes with zero findings over the final bytes; records + sidecars at docs/reviews/2026-10-05-plan-review-execute-plan-lifecycle-recovery-gaps-exec-r{1,2}.md.
- Implementation commits: 1fd010f0 (Task 1), ef73aa2e (Task 2), 0f8d3ce3 (Task 3), 9ab76ff7 (r1 fold).
- Deferred residuals: none.
