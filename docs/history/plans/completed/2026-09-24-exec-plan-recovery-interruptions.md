> SUPERSEDED 2026-09-25 by docs/plans/2026-09-25-execute-plan-recovery-contract-preflight.md: its premise that the parked workstream `2026-09-22-codex-execute-plan-runtime-reconciliation` is reference-only contradicts that plan's land-after-workstream drift gate (its Task 1); never execute this plan.

# Plan: Execute-plan recovery interruptions end-to-end contract

Plan review: docs/reviews/2026-09-24-plan-review-exec-plan-recovery-interruptions-r1.md (r1, ready=no; folds applied for r2)

Backlog origins (scope of record): this plan covers docs/history/backlog/2026-09-24-execute-plan-recovery-interruptions.md and absorbs three uncovered siblings whose remedies are this plan's own tasks: docs/history/backlog/2026-09-23-execute-plan-preflight-before-claim-launch.md (Task 3 launch preflight and canonical continuation invocation), docs/history/backlog/2026-09-23-execute-plan-immutable-scope-plan-drift.md (Task 4 plan-to-claim scope parity preflight), and docs/history/backlog/2026-09-24-done-pending-recovery-r1-low-findings.md (F1 and F2 folded into Task 2's receipt and anchor rework; F3 is record-only and folds into the same docs touch).
Driving force: code-quality + efficiency (reliability-led; justification: the motivating force is reliability, the witnessed class of multi-hour execute-plan interruptions at recovery and launch boundaries, and `reliability` is not in the closed taxonomy; the deliverable hardens existing driver and validator surfaces, so `code-quality` is the primary tag as the robustness home, with `efficiency` secondary because every avoided interruption saves hours of unattended runtime and re-work)

## Terms

- done-pending: the terminal-but-uncommitted claim state a task enters when its worker finished but the commit handoff did not complete; the sanctioned exit family is the P53a `recover-done-pending` driver transition (requeue, defer, abort) plus the Task 4 `supersede-handoff` operation for scope-drifted uncommittable handoffs.
- retained launch record: the preserved `launch_record` a requeued or recovered claim keeps for audit; on startup reconciliation it is historical evidence, not proof of ownership.
- claim generation: the monotonically increasing version of a task's claim; recovery requeue increments it.
- terminal receipt: the immutable `done-pending-recovery` evidence record a recovery transition persists; it is the correlate that pairs a retained launch record with its own claim generation.
- launch preflight: a read-only driver check that resolves and validates runtime activation and approval evidence through the same routines the launch path uses, before any claim state changes.

## Design Invariants (CR Guard)

- Claim fencing is never weakened: a live claim's token and generation still fence every mutation; the Task 3 preflight refuses without changing any prepared claim (no `resume_allowed` flip, no generation bump, no manifest write), and the preflight shares the launch path's own `activation_check` and re-runs the same approval loader the launch entry chain uses (`capabilities.load_approval_receipt`, which re-reads the host config and recomputes the fingerprint rather than consuming a cached verdict) so the two can never disagree.
- Immutable task scopes are never widened: Task 4's parity check refuses drifted launches; once a claim exists its `allowed_paths` are never rewritten, and a completed-but-uncommittable handoff exits only through the Task 4 `supersede-handoff` transition, whose routing exclusivity the Task 7 diagnosis table owns (the requeue disposition is pinned to committable-recoverable handoffs), and which moves the original worker's preserved changes to a driver-recorded, operator-recoverable location named in the audit receipt and leaves the worktree clean of refused entries.
- Approval verification is never bypassed: the preflight validates activation and receipt evidence, it never skips or caches an approval decision.
- P53a's recovery receipt stays immutable validated evidence: Task 2 may only tighten what enters a receipt (F1) and how anchors resolve (F2), never loosen validation of existing receipt fields; the existing per-arm post-acceptance checks are retained, not replaced.
- The historical-record exception stays exact: the startup reconciler may bypass the `owner-mismatch` refusal for a retained launch record ONLY on the closed-claim + pending-or-deferred-task + matching recovery receipt tuple (Task 1), disposition-aware and receipt-paired per cycle; no generalization to ambiguous handoffs, live claims, or mismatched receipts.
- The model-guard posture stays fail-closed: an unlisted tool identity never skips model verification (Task 5 pins the default).
- Provider-specific process probing stays in the Codex adapter; durable policy lives in the runtime driver (origin item non-goals).

## Assumptions

- assume the implementation base is current `main` (post 26936b9f) including P53a's landed recovery transition at 7f708429 and the P50 watcher receipt work at ce968c19; basis: `git log main` shows both squashes landed 2026-09-24.
- assume the parked branch 2026-09-22-codex-execute-plan-runtime-reconciliation (667875c3) is reference material only; no task pulls or rebases onto it; basis: branch listing plus the origin item's "separately authorized" framing.
- assume `require-luna.py` means `agents/hooks/codex-model-guard/require-luna.py` (repo copy; the deployed host copy is refreshed by the done skill's stale-deploy remedy, an operations path listed under Ship when); basis: `scripts/test_codex_model_guard.py` imports exactly that path.
- assume tests run with `python3 -m unittest` from `scripts/`; the full `test_execute_plan_runtime` suite is the baseline gate (362 tests at P53a close, green); basis: the P53a plan's Validation Commands.
- assume `supersede-handoff` lands as a new driver operation sibling of `recover-done-pending` (not a new recovery disposition inside it), because the origin item scopes a separately authorized close-or-supersede path for scope-drifted handoffs; basis: the immutable-scope sibling item's suggested fix.
- assume "no manual machine-state edits" holds: no task asks the operator to hand-edit `runtime_state.json`; every remedy is driver-owned; basis: origin item desired outcome.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the execute-plan runtime gains launch preflight, plan-to-claim parity, and recovery-transition validation so recovery succeeds AND the next launch works, ending the class of recover-then-immediately-block interruptions (code-quality + efficiency, reliability-led).

Four witnessed failure shapes close:

1. Recovery leaves the run wedged for the next launch: `recover-done-pending` requeues Task 6 and rotates the claim, but startup reconciliation then reads the retained launch record on the closed claim as proof the task is still owned and refuses continuation as `owner-mismatch`, even though the exact recovery receipt proves the claim closed and the task pending. Task 1 narrows the historical recognition to the exact receipt tuple, disposition-aware across requeue and defer; Task 2 validates the post-transition manifest (manifest-internal checks only) before persistence so a recovery that would fail the next launch fails loudly instead, leaving the manifest byte-identical.
2. A caller omission becomes a dead claim: the first continuation omits the approval receipt, the adapter returns `runtime-policy-unavailable`, and the driver flips a prepared claim to `blocked` with `resume_allowed: false`; the four-hour lease becomes the only exit. Task 3's read-only preflight refuses BEFORE the claim changes, and the canonical continuation invocation removes the reliance on the caller remembering optional flags.
3. Plan prose drifts from machine scope: a rebased plan's Task `Files:` name paths the seeded immutable `allowed_paths` never authorized; on main the mismatch surfaces only after `done-pending`, fenced. Task 4 re-checks parity at every claim mint (and when the run's plan digest changes), refuses drifted launches with a both-set diagnostic before a claim exists, re-checks an already-minted live claim at the launch boundary, and routes post-claim drift to the `supersede-handoff` transition instead of a mid-execution fence.
4. Adjacent gate defects amplify interruptions: the Codex model guard's deny-unless-verified fallthrough denies model-less lifecycle calls (wait, inspect, send, close) and its substring marker classification over-broadens launch gating (Task 5), and a plan-review record emitted without the `plan-review-` infix is invisible to the readiness validator, so a fresh review does not advance readiness (Task 6, which also binds the combined review preflight before panel launch).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every witnessed failure shape above has a regression test that fails on current `main` behavior and passes after its task (RED stated per task, GREEN at task end).
- reliability: an end-to-end recovery cycle (claim, launch, terminal receipt, done handoff, `recover-done-pending`, next-task launch) passes with a retained launch record across TWO generation-bump cycles, and a supersede-then-next-launch leg passes with a clean worktree.
- safety: no task weakens claim fencing, immutable scopes, approval verification, receipt immutability, or the fail-closed model-guard posture (CR Guard); each guard has a negative test proving the old refusal still fires.
- maintainability: interruption outcomes are diagnosable from one operator-readable table with one supported action per condition; no remedy requires hand-editing `runtime_state.json`.

**Done when:**
- `python3 -m unittest test_execute_plan_runtime -v` passes from `scripts/` (full suite, new tests included).
- `python3 -m unittest test_codex_model_guard -v`, `python3 -m unittest test_plan_readiness -v`, and `python3 -m unittest test_review_record_selection -v` pass from `scripts/`.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-24-exec-plan-recovery-interruptions.md` exits 0 on the final bytes.
- `agents/skills/execute-plan/SKILL.md` and `runtime-contract.md` carry the recovery contract, the exit family, and the canonical continuation invocation, and the operator diagnosis table names one action per condition across the readiness, preflight, and parity surfaces.

**Ship when:**
- the deployed host copies the done skill owns (driver script, model-guard hook) are refreshed on the host by the done skill's stale-deploy remedy; evidence owner: the executing session's done handoff; closure: the remedy reports the deployed copies in sync. [class: OPERATIONS_FOLLOW_UP]
- the next real recovery incident on this repository resolves without a manual manifest edit; evidence owner: the maintenance loop's incident record; closure: the incident record shows a driver-owned resolution. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py`
- `scripts/review_record_selection.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/hooks/codex-model-guard/require-luna.py`
- `scripts/plan_readiness.py`

**Tests:**
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_review_record_selection.py`
- `scripts/test_codex_model_guard.py`
- `scripts/test_plan_readiness.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. `scripts/review_retention.py` mirrors the review-record infix tuple; a Task 6 change that alters the tuple must sweep it under plan-related extension.

**Out of scope; reject unless plan-related:**
- the Codex adapter's provider-specific session probing internals; reason: origin item keeps provider probing in the adapter, this plan touches only the driver contract boundary.
- branch 2026-09-22-codex-execute-plan-runtime-reconciliation contents; reason: parked reference only (Assumptions).
- docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md scope (worker evidence proof strength); reason: separate evidence-contract item, not a recovery-interruption cause named by the origin.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO/scripts" && python3 -m unittest test_execute_plan_runtime -v ) \
  || { echo "FAIL: full runtime suite"; exit 1; }
( cd "$REPO/scripts" && python3 -m unittest test_codex_model_guard -v ) \
  || { echo "FAIL: model guard suite"; exit 1; }
( cd "$REPO/scripts" && python3 -m unittest test_plan_readiness -v ) \
  || { echo "FAIL: plan readiness suite"; exit 1; }
( cd "$REPO/scripts" && python3 -m unittest test_review_record_selection -v ) \
  || { echo "FAIL: review record selection suite"; exit 1; }
( cd "$REPO" && python3 scripts/plan_readiness.py docs/plans/2026-09-24-exec-plan-recovery-interruptions.md ) \
  || { echo "FAIL: readiness gate"; exit 1; }
sed -n '/^def select_record/,/^def /p' "$REPO/scripts/review_record_selection.py" | grep -q "plan-review-" \
  || { echo "FAIL: emit path lost the plan-review infix"; exit 1; }
rc=0; grep -nE "marker in tool_name" "$REPO/agents/hooks/codex-model-guard/require-luna.py" || rc=$?
case "$rc" in
  0) echo "FAIL: marker membership idiom still present"; exit 1 ;;
  1) : ;;
  *) echo "FAIL: forbidden-match probe error rc=$rc"; exit 1 ;;
esac
for probe in "derive one next action" "without a full plan review" "superseded-handoff"; do
  grep -qF "$probe" "$REPO/agents/skills/execute-plan/SKILL.md" \
    || { echo "FAIL: SKILL.md missing obligation: $probe"; exit 1; }
done
grep -qF "supersede-handoff" "$REPO/agents/skills/execute-plan/runtime-contract.md" \
  || { echo "FAIL: runtime contract missing supersede-handoff operation"; exit 1; }
grep -qF "review-preflight" "$REPO/agents/skills/doing-code-review/SKILL.md" \
  || { echo "FAIL: doing-code-review missing review-preflight binding"; exit 1; }
```

The forbidden-match probe uses explicit rc capture: rc 0 fails as a forbidden match, rc 1 passes as a clean no-match, rc >= 2 aborts as a tool error, so an unreadable or missing target can never pass silently. The infix pin is scoped to the select_record function's span (region-extracted from its top-level def), which contains the nested emit construction while excluding the module-level discovery-tuple literal, so the pre-existing literal cannot satisfy the pin; the swept surface is the executing tree's selector, not the plan.

### Task 1: Startup reconciliation pairs retained launch records with their exact receipts

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] `StartupReconciliationTest#test_retained_launch_record_with_matching_receipt_continues`; given a done-pending task requeued by an exact recovery receipt whose closed claim retains its launch record, expects startup reconciliation to classify the record as historical and continuation of the pending task to proceed [class: REPOSITORY_TEST]
- [ ] `StartupReconciliationTest#test_retained_launch_record_without_matching_receipt_refused`; given a retained launch record whose receipt token, claim generation, or pending-task pairing does not exactly match the tuple, expects today's `owner-mismatch` refusal with no mutation (CR Guard negative witness) [class: REPOSITORY_TEST]
- [ ] `StartupReconciliationTest#test_live_claim_identity_mismatch_still_refused`; given a LIVE claim whose owner, token, or generation cannot be proven safe, expects the existing refusal outcomes (`stale-claim` / `owner-mismatch`) unchanged [class: REPOSITORY_TEST]
- [ ] `StartupReconciliationTest#test_two_generation_bump_cycles_pair_own_receipts`; given a task driven through TWO successive recover-then-reselect cycles with two accumulated receipts, expects each retained record to pair only with its own receipt and both cycles to continue without manual manifest edits [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `cd scripts && python3 -m unittest test_execute_plan_runtime.StartupReconciliationTest -v` from `$REPO` errors or fails on the new acceptance and pairing tests (the receipt-tuple bypass does not exist on current `main`); the negative-witness tests pass before and after; the pre-existing full suite still passes [class: REPOSITORY_TEST]
- [ ] `StartupReconciliationTest#test_receipt_paired_defer_reconciliation_continues`; given a task deferred by an exact recovery receipt whose closed claim retains its launch record, expects startup reconciliation to classify the record as historical and later continuations of the run to proceed; given a mismatched defer receipt, expects the `owner-mismatch` refusal (defer leg of the tuple) [class: REPOSITORY_TEST]
- [ ] Implement in `_reconcile_startup_locked` (and the launch-evidence collection it reads): recognize the exact historical tuple (closed claim + pending-or-deferred task + a `done-pending-recovery` receipt pairing that claim token and generation with this task, disposition-aware) and bypass the `owner-mismatch` refusal only for it; every live claim, ambiguous handoff, and mismatched record keeps today's refusal behavior [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the focused class passes (5/5) and the full suite from `scripts/` passes [class: REPOSITORY_TEST]
- [ ] Commit: `feat: pair retained launch records with exact recovery receipts in startup reconciliation` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Recovery transitions validate the post-transition manifest before persistence

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [ ] `PostTransitionValidationTest#test_requeue_manifest_validated_before_persist`; given a `recover-done-pending` requeue whose resulting in-memory manifest would fail schema validation or the receipt-pairing reconciliation predicates, expects the transition to refuse and the persisted manifest bytes to stay identical (no partial write) [class: REPOSITORY_TEST]
- [ ] `PostTransitionValidationTest#test_valid_requeue_persists_and_launch_passes`; given a valid requeue, expects the transition to persist and the immediately following watcher snapshot and startup reconciliation to pass on the persisted bytes [class: REPOSITORY_TEST]
- [ ] `PostTransitionValidationTest#test_requeue_backlog_evidence_validated`; given a requeue carrying a `backlog_evidence` value outside `docs/history/backlog/` (F1), expects the transition to refuse validation; given no value or a valid backlog-relative path, expects the receipt to record it normalized through the same relative-path gate the defer arm uses [class: REPOSITORY_TEST]
- [ ] `PostTransitionValidationTest#test_terminal_evidence_resolves_group_launch_records`; given a session-less group-member done-pending claim whose true launch identity lives on the group (F2), expects terminal-evidence anchor extraction to route through the group launch-record resolution and accept the exact group identity [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `cd scripts && python3 -m unittest test_execute_plan_runtime.PostTransitionValidationTest -v` fails on the new tests (the requeue arm records `backlog_evidence` unvalidated and the anchors never resolve group records today); Task 1's suite stays green [class: REPOSITORY_TEST]
- [ ] Implement one shared post-transition validation helper, LOCK-COMPATIBLE AND MANIFEST-INTERNAL: it validates the already-loaded in-memory manifest through `validate_manifest` plus pure reconciliation predicates (receipt pairing, status invariants) and never calls `reconcile_startup` or any git/worktree/commit witness inside the locked transition; it COMPOSES with the existing per-arm post-acceptance checks (they are retained); scope its predicates per disposition: schema and receipt-pairing validation on ALL arms, next-task status invariants only on requeue and defer, terminal-shape invariants on abort (matching that arm's documented design); wire it into every recovery transition before persistence [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the focused class passes and the full suite passes [class: REPOSITORY_TEST]
- [ ] Commit: `feat: validate post-transition manifests and harden recovery receipts` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Read-only launch preflight and the canonical continuation invocation

Files:
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [ ] `LaunchPreflightTest#test_missing_activation_refuses_before_claim_change`; given a continuation whose runtime activation evidence is absent, expects the preflight to return a refused outcome naming the missing evidence, the persisted manifest bytes to be BYTE-IDENTICAL after the refusal (no launch record, activation receipt, or history event), and the claim state (token, generation, `resume_allowed`) unchanged [class: REPOSITORY_TEST]
- [ ] `LaunchPreflightTest#test_stale_or_invalid_receipt_refuses_without_side_effects`; given a stale or invalid approval receipt, expects refusal before any claim mutation and a retryable prepared claim (a retry with a valid receipt then proceeds on the SAME claim token and generation) [class: REPOSITORY_TEST]
- [ ] `LaunchPreflightTest#test_valid_preflight_proceeds_to_launch`; given complete activation and receipt evidence, expects the preflight to pass and the continuation to proceed to worker launch on the authorized claim [class: REPOSITORY_TEST]
- [ ] `LaunchPreflightTest#test_preflight_shares_launch_path_resolvers`; given the preflight implementation, expects it to invoke the same adapter activation-check `_launch_claimed_task` uses AND to re-run the same approval loader the launch entry chain uses (`capabilities.load_approval_receipt`, re-reading host config and recomputing the fingerprint, never consuming a cached verdict; no second resolver; wiring assertion in the test) [class: REPOSITORY_TEST]
- [ ] `CanonicalInvocationTest#skill_document_carries_one_continuation_command`; given `agents/skills/execute-plan/SKILL.md`, expects exactly one canonical continuation invocation block binding selected runtime, approval receipt path, repo root, manifest path, plan path, and current claim, matching the runtime-contract's CLI boundary (grep-verified, one block) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `cd scripts && python3 -m unittest test_execute_plan_runtime.LaunchPreflightTest test_execute_plan_runtime.CanonicalInvocationTest -v` fails on the new tests (no preflight operation and no canonical invocation block exist today); Tasks 1-2 suites stay green [class: REPOSITORY_TEST]
- [ ] Implement the driver-owned read-only preflight operation as a thin shared-resolver check run before dispatch (refuses without state change; reports parity verdict read-only), and publish the canonical invocation in SKILL.md bound in a new runtime-contract.md approval-boundary subsection beside the adapter contract's approval-policy terms [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the focused classes pass and the full suite passes [class: REPOSITORY_TEST]
- [ ] Commit: `feat: read-only launch preflight and canonical continuation invocation` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Plan-to-claim scope parity at every claim mint, with supersede-handoff recovery

Files:
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [ ] `ScopeParityTest#test_plan_paths_versus_seeded_allowlist_diff_refuses_launch`; given a plan whose Task N `Files:` set contains paths absent from the `allowed_paths` the driver would seed for that task, expects a parity refusal naming BOTH set differences (plan-only paths and scope-only paths) before any claim exists [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_parity_pass_seeds_identical_scopes`; given matching plan and seeded sets, expects the run to proceed to normal claiming with no extra output obligation [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_parity_reruns_at_every_claim_mint_after_plan_edit`; given a run whose plan file changes between two claim mints, expects the parity check to re-run at the next mint (re-reading the persisted plan through the bounded reader) and refuse the drifted task's launch before its claim is issued [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_post_claim_drift_refusal_fires_at_launch_boundary`; given an already-minted LIVE claim whose token predates a plan edit, expects the parity re-check at the launch/resume boundary (pre-dispatch) to refuse with the `supersede-handoff` routing [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_group_advance_parity_refusal_takes_group_release_shape`; given a batch group claimed parity-clean whose plan file is edited before the first member's done, expects the group-advance parity refusal to take the fail-group-release shape (the completed member's done lands, staged members re-enter the individual queue, the drifted member refuses at its own individual claim mint), never a refused done [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_parity_skips_when_plan_input_absent`; given a run with no plan text available or a task section without a `Files:` list, expects parity to skip with a logged line (the absent-input contract, witnessed so the skip is deliberate) [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_preflight_reports_parity_verdict_readonly`; given the Task 3 preflight invoked after this task lands, expects its read-only outputs to include the parity verdict [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_post_claim_drift_routes_to_supersede_not_midexec_fence`; given a live claim whose token predates a plan edit that adds paths, expects the launch refusal to name `supersede-handoff` as the only exit (no mid-execution fence, no token rewrite) [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_supersede_moves_changes_to_recoverable_location_and_continues`; given a completed-but-uncommittable handoff, expects `supersede-handoff` to close it, move the preserved worker changes OUT of the worktree into a driver-recorded, operator-recoverable location (path named in the audit receipt), leave the worktree clean of refused entries, and allow the next launch to proceed [class: REPOSITORY_TEST]
- [ ] `ScopeParityTest#test_supersede_refuses_unattributable_dirty_entries`; given a worktree carrying dirty entries the claim's baseline diff does NOT attribute to the worker (operator WIP), expects `supersede-handoff` to refuse with a named operator action and leave those entries untouched (negative witness: unrelated dirt is never relocated) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `cd scripts && python3 -m unittest test_execute_plan_runtime.ScopeParityTest -v` fails on the new tests (no parity check and no supersede operation exist today); Tasks 1-3 suites stay green [class: REPOSITORY_TEST]
- [ ] Implement the parity contract with an OWNED input path: add a create payload key carrying the plan path, gate it through `_safe_relative_path` at the seeding boundary (the same repo-relative gate the defer arm applies to backlog evidence), and persist `plan_path` plus `plan_digest` at `create_manifest` (digest computed at the seeding boundary through the bounded reader; existing test fixtures and legacy manifests ride the absent-input skip); invoke the parity check at EVERY claim-mint site (single, batch, parallel, and group-advance activation) re-reading the persisted plan through the bounded reader, comparing each remaining task's plan `Files:` set against the `allowed_paths` that mint would seed, with both-set diagnostics; at the group-advance site a parity refusal takes the FAIL-GROUP-RELEASE shape (the completed member's done lands, staged members re-enter the individual queue, the drifted member refuses at its own individual claim mint), never a refused done; ALSO invoke the parity check at the launch/resume boundary for an already-minted live claim (pre-dispatch inside `_launch_claimed_task`), routing that refusal to `supersede-handoff` with no token rewrite; skip parity with a logged line when the plan text is unavailable or the task section carries no `Files:` list; extend the Task 3 preflight's read-only outputs with the parity verdict; implement `supersede-handoff` as a new driver operation sibling of `recover-done-pending` (operator evidence in; relocate ONLY entries the claim's baseline diff attributes to the worker; refuse with a named operator action when unattributable dirty entries exist; preserved changes moved to the recoverable path; audit receipt appended; pin the persisted post-supersede task and claim states as a named new status integrated at EVERY site the deferred precedent spans, not a reuse of deferred or aborted semantics: (1) `validate_manifest`'s task_states set and the claim-state set; (2) `_task_complete`'s complete-for-selection set so the terminal gate and the defer/recovery ordering gates treat superseded as out of selection; (3) the startup reconciler's examined filter (or Task 1's receipt tuple extended with the supersede audit receipt) so a closed superseded claim never re-triggers `owner-mismatch`; (4) readiness); bind the parity contract in runtime-contract.md's manifest seeding section [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the focused class passes and the full suite passes [class: REPOSITORY_TEST]
- [ ] Commit: `feat: per-claim scope parity preflight and supersede-handoff recovery` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Model guard: exact creation identities, fail-closed default, lifecycle allow-path

Files:
- `agents/hooks/codex-model-guard/require-luna.py`
- `scripts/test_codex_model_guard.py`

- [ ] `ModelGuardTest#test_worker_creation_requires_selected_model`; given a worker-creation tool identity from the exact set WITHOUT a nonempty model or selected policy correlation, expects the hook to deny with the launch-policy reason (specify the harness: no Luna transcript active, no model field present) [class: REPOSITORY_TEST]
- [ ] `ModelGuardTest#test_lifecycle_operations_pass_without_model`; given wait, inspect, send, and close tool identities under the same no-transcript harness, expects the hook to allow them without any model field (the lifecycle allow-path must run BEFORE any model consultation; the witnessed false denials) [class: REPOSITORY_TEST]
- [ ] `ModelGuardTest#test_unlisted_spawnlike_identity_gated_under_luna_transcript`; given a spawn-like tool identity OUTSIDE the exact set with a Luna-active transcript and NO model field, expects the hook to allow it today (the deny-unless-verified fallthrough passes under Luna) and to DENY it after this task with the launch-policy reason (the deliberate tightening: the spawn-like fallback routes such identities to the launch gate; fail-closed CR Guard witness) [class: REPOSITORY_TEST]
- [ ] `ModelGuardTest#test_exact_spawn_spelling_still_gated`; given a tool identity carrying a spawn-like marker WITH an explicit non-Luna model in `tool_input`, expects the launch-gate deny before and after (preservation witness for the migration from substring markers to the explicit set plus spawn-like fallback pattern; explicit-model harness pinned so the witness cannot flip polarity) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `cd scripts && python3 -m unittest test_codex_model_guard -v` fails on the lifecycle-allow test (denied today by the deny-unless-verified fallthrough) and on the Luna-transcript spawn-like test (allowed today, launch-gate-denied after); the exact-set creation test and the exact-spelling preservation test pass before and after [class: REPOSITORY_TEST]
- [ ] `ModelGuardTest#test_spawnlike_identity_with_lifecycle_substring_still_gated`; given a spawn-like creation identity whose name merely CONTAINS a lifecycle substring (for example a wait or close fragment), expects the launch gate to apply (the lifecycle allow-path matches EXACT identities, never substrings) [class: REPOSITORY_TEST]
- [ ] Implement: replace the `WORKER_TOOL_MARKERS` membership classification with an explicit worker-creation identity set plus a spawn-like fallback pattern; route lifecycle identities to allow BEFORE any model consultation using the same EXACT-IDENTITY discipline (never substring matching); every other identity keeps today's deny-unless-verified fallthrough [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `cd scripts && python3 -m unittest test_codex_model_guard -v` passes [class: REPOSITORY_TEST]
- [ ] Commit: `fix: model guard gates exact creation identities with a fail-closed default` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Kind-aware plan-review record infix and the bound review preflight

Files:
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`
- `agents/skills/doing-code-review/SKILL.md`

- [ ] `ReviewRecordSelectorTest#test_plan_kind_selection_emits_readiness_discoverable_name`; given a plan-kind record selection, expects the emitted filename to carry the `plan-review-` infix so the readiness validator's glob discovers it (RED today: the emitter builds `<date>-<slug>-r<N>` with no infix) [class: REPOSITORY_TEST]
- [ ] `ReviewRecordSelectorTest#test_non_plan_kinds_keep_their_shapes`; given branch-review, code-review, and bare-kind selections, expects their emitted names to keep today's shapes (the infix is kind-aware, never unconditional) [class: REPOSITORY_TEST]
- [ ] `ReviewRecordSelectorTest#test_round_discovery_pairs_infixed_and_bare_families`; given a reviews directory holding both legacy bare and new infixed plan-review records, expects round discovery to pair families correctly in both directions (PRESERVATION witness: passes before and after; update the suite's bare-shape pins for the new family) [class: REPOSITORY_TEST]
- [ ] `ReviewPreflightTest#test_combined_preflight_reports_scope_and_annotation_problems` (lives in `scripts/test_plan_readiness.py`); given a plan whose new Task paths lack global Review Scope entries or `*(new)*` annotations, expects the combined `review-preflight` invocation in `plan_readiness.py` to report both problems in one refusal (single-sourcing the existing parsers; only the combined invocation is new) [class: REPOSITORY_TEST]
- [ ] `ReviewPreflightTest#doing_code_review_binds_preflight_before_panel` (also in `scripts/test_plan_readiness.py`); given `agents/skills/doing-code-review/SKILL.md`, expects its pre-panel step to invoke the `review-preflight` operation before launching a panel for PLAN-REVIEW source passes, passing the plan document's path as the preflight input (grep-verified obligation over the scoped wording; PR and branch review modes are out of the binding's scope) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `cd scripts && python3 -m unittest test_review_record_selection -v` fails on the plan-kind emission test (bare names emitted today) while the non-plan-shapes and pairing-preservation tests pass before and after, and `cd scripts && python3 -m unittest test_plan_readiness -v` fails on BOTH ReviewPreflightTest tests (neither the combined-preflight operation nor the doing-code-review binding exists today); all other tests in both suites pass [class: REPOSITORY_TEST]
- [ ] Implement: kind-aware infix in the selector's emit path (plan-kind only), update the suite's pinned naming expectations, add the combined `review-preflight` mode to `plan_readiness.py` composing the existing scope and annotation parsers, and bind it in the doing-code-review pre-panel step scoped to plan-review source passes with the plan path as the named input; sweep `scripts/review_retention.py`'s mirrored infix tuple under plan-related extension if the tuple changes [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both focused suites pass and the full suite passes [class: REPOSITORY_TEST]
- [ ] Commit: `feat: kind-aware plan-review record infix and bound review preflight` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Decision-driven resume contract, exit family, and the operator diagnosis table

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] Amend the SKILL.md recovery contract prescribing verbatim: "derive one next action" from the driver and recorded artifacts after each checkpoint; a line forbidding a full plan review repeat for an unchanged digest worded so it contains "without a full plan review"; a line forbidding relaunching or re-seeding a claim to repair plan prose; and a line recording unrelated validation or hygiene failures as separate follow-ups that do not invalidate the active task [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend the SKILL.md and runtime-contract.md exit wording to name the sanctioned EXIT FAMILY (recover-done-pending dispositions plus the supersede-handoff operation), replacing today's single-exit sentences; the SKILL.md resume contract names the superseded-handoff condition as a supported state the diagnosis table covers [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the operator diagnosis table to runtime-contract.md: one supported action per interruption condition across the three surfaces (readiness operation, launch preflight, claim-path parity), distinguishing retryable pre-launch refusals from ambiguous post-launch states, covering the superseded-handoff condition AND the deferred-task reconciliation condition, pinning the recover-done-pending requeue disposition to committable-recoverable handoffs (the scope-drifted-handoff condition names `supersede-handoff` as its single action), and never instructing a manual `runtime_state.json` edit [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify with fail-closed greps (in the task gate AND mirrored in the Validation Commands block): `grep -qF "derive one next action"`, `grep -qF "without a full plan review"`, `grep -qF "superseded-handoff"` over SKILL.md; `grep -qF "supersede-handoff"` over runtime-contract.md; each wrapped with an explicit `|| { echo FAIL; exit 1; }` [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the doc-probe greps fail against current SKILL.md and runtime-contract.md (no obligation lines exist yet); suites from Tasks 1-6 stay green [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: all four doc-probe greps pass; `cd scripts && python3 -m unittest test_execute_plan_runtime -v` still passes (doc-only task; the suite is the regression net) [class: REPOSITORY_TEST]
- [ ] Commit: `docs: resume contract, exit family, and operator diagnosis table` [class: IMPLEMENTATION_REQUIRED]

### Task 8: End-to-end recovery cycle integration test

Files:
- `scripts/test_execute_plan_runtime.py`

- [ ] `EndToEndRecoveryTest#test_recover_then_next_launch_full_chain`; given a seeded run driven through claim, launch, terminal receipt, done handoff, `recover-done-pending`, and the next task's launch, expects every boundary to pass with a retained launch record and a generation bump, ending in a live next-task claim (run the chain TWICE to exercise receipt pairing across cycles) [class: REPOSITORY_TEST]
- [ ] `EndToEndRecoveryTest#test_rebased_plan_scope_drift_routes_to_parity_refusal`; given a rebased plan whose task files differ from machine-seeded scope, expects the chain to surface the Task 4 parity refusal BEFORE any drifted claim is issued (first-claim runs never fence mid-execution) [class: REPOSITORY_TEST]
- [ ] `EndToEndRecoveryTest#test_supersede_then_next_launch_continues`; given a run reaching a completed-but-uncommittable handoff, expects `supersede-handoff` to close it with a clean worktree and the next launch to proceed, and drives the chain THROUGH THE TERMINAL GATE afterward (the run reaches its terminal state with the superseded task out of selection) [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `cd scripts && python3 -m unittest test_execute_plan_runtime.EndToEndRecoveryTest -v` fails against any tree where a prerequisite task is missing; the tests pass only over the complete chain [class: REPOSITORY_TEST]
- [ ] Write the integration tests using the existing test fixtures and driver entry points; no production changes expected (if one is needed, it is plan-related and gets its own commit) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the full Validation Commands block, all commands in order [class: REPOSITORY_TEST]
- [ ] Commit: `test: end-to-end recovery, parity routing, and supersede continuation` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-24-execute-plan-recovery-interruptions.md: disposition folded into 2026-09-24-exec-plan-recovery-interruptions.md (2026-09-25); per-item file deleted.
