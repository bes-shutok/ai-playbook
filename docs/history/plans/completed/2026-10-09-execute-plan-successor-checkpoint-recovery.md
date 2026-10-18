# Plan: execute-plan successor checkpoint recovery

Backlog origins (scope of record):
- docs/history/backlog/2026-10-08-execute-plan-successor-checkpoint-unconsumed-handoff.md (primary)
- docs/history/backlog/2026-10-08-execute-plan-checkbox-progress-stales-review-certificate.md (cluster sibling, second refusal)
Driving force: reliability (primary); reliability justification: the witnessed harms strand verified execution work at the task-continuation boundary (a completed successor worker's checkpoint refused on an unconsumed launch binding; a committed checkbox-only progress update staling the review digest so the next task cannot start), so the work is implemented for continuity of already-authorized execution; park triage: not applicable, the origin rows are witnessed runtime refusals, not parked rows
Plan review record: the staging series docs/history/reviews/2026-10-09-plan-review-execute-plan-successor-checkpoint-recovery-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Authoring claim: docs/tmp/authoring-claims/2026-10-09-execute-plan-successor-checkpoint-recovery.md (session d4-authoring-carrier-automation-15f03d78)
Execution budget: 2.5h total, largest task 1.5h
Dispatch entry: PLAN-PROMPTS entry `execute-plan-successor-checkpoint-recovery` (frozen 2026-10-09)

## Terms

- Handoff intent: the manifest's per-successor-launch record (`handoff_intents`), carrying the `prelaunch_binding` the parent runtime wrote before the worker launch and transitioning through launching, launched, receipt-persisted.
- Prelaunch binding: the intent's binding object (`run_writer_id`, `parent_session_id`, `turn_id`, `tool_use_id`, `claim_owner_id`, `claim_token`, `generation`, `launch_id`, `expected_model`), consumed by the matching worker-start receipt.
- Worker-start receipt: the full identity receipt the driver consumes in `record_worker_start` (the required sixteen-field set including `worker_id` and `provider_session_id`), setting `worker_identity`, `worker_start_receipt`, and `consumed: true` on the binding.
- Terminality proof: the driver-side observable that the successor's provider session is no longer live, via the adapter's optional `observe_terminal_evidence` port (the two in-runtime precedents are the done-sweep release consultation and the ambiguous-handoff recovery); the reconciliation refuses while the session is live or its state is not terminal, and refuses with a distinct port-unavailable evidence line when the adapter implements no such port, never collapsing that case into live-session.
- Unconsumed-binding refusal: the successor checkpoint refusal at the handoff-intent guard ("successor checkpoint has no consumed matching launch binding"), fired when the intent state is not launched or the binding is unconsumed.
- Marker-only classifier: the existing plan-delta classification that recognizes `checkbox-marker-only` (and `review-ready-round`) deltas with paired-line identity, as used by the out-of-scope plan-edit recovery.
- Plan-disposition receipt: the done-boundary record naming the actual commit that carried a plan edit and its classification, as recorded by the existing recover-out-of-scope-plan-edit transition.
- Done commit (and the done boundary): the per-task commit the done flow verifies and records; the boundary where a task's completion, plan edits, and evidence receipts land.
- Claim: the manifest's per-task execution claim (owner, token, generation, launch id, state) whose live identity every receipt must match.
- Reviewed-plan digest: the plan-bytes digest the latest ready review round's sidecar covers and the startup reconciliation checks the current bytes against.
- Two-attempt/replay budget: the runtime's bounded retry and replay fences on receipts; unchanged by this plan.
- Startup reconciliation: the runtime's task-startup checks (`reconcile_startup`/`_reconcile_startup_locked`), including the reviewed-plan digest arm that refuses with "the latest ready review round must cover the current plan digest".
- Manifest lock: the runtime's existing manifest write lock every manifest mutation already takes; both recoveries persist through locked driver transitions, never direct manifest edits.
- Task scope: the manifest's per-task seeded scope (allowed paths, required criteria, verification commands) plus its recomputed derivative digests, refreshed by the runtime's existing route.

## Why

Two witnessed refusals strand verified execution work at the same task-continuation flow, with distinct state predicates. First, a successor worker completes and returns a successful structured result while the runtime still refuses its checkpoint because the handoff intent's `prelaunch_binding` was never consumed: the worker-start event never reached `record_worker_start`, so the guard at the successor checkpoint ("successor checkpoint has no consumed matching launch binding") blocks the done boundary with no executable recovery (origin row one, witnessed 2026-10-08 in the review-policy run's Task 2). Second, a task's authorized checkbox-only progress update rides its done commit, the plan bytes change, and the next task's startup reconciliation refuses because the latest ready review round's digest no longer covers the plan ("the latest ready review round must cover the current plan digest"), demanding a full re-review for an authorized progress marker (origin row two, witnessed twice in the same run). Both witnesses come from one execution run; the recovery contracts stay separate because their evidence and predicates differ (provider-session terminality and launch identity for the first; an authorized done commit and a marker-only delta for the second).

## Gist & Examples

TLDR: gives the execute-plan driver two narrowly scoped recovery transitions so a completed successor worker stranded by an unconsumed launch binding and a committed checkbox-only progress update that staled the review digest both resume through the ordinary gates (reliability: no verified work strands at the task-continuation boundary).

Example 1: a successor task's worker thread returns `implemented` with all criteria verified, but the checkpoint is refused because the binding is unconsumed; the parent runs the new reconciliation with the worker-start receipt identity and the terminality proof, the driver verifies the provider session is terminal and every identity field matches the claim, intent, and binding, consumes the binding through the existing worker-start logic, and re-enters the ordinary checkpoint and done gates with the held receipt.

Example 2: Task 2's done commit carried its checkbox progress, so Task 3's startup reconciliation reads a digest mismatch; the new arm classifies the committed delta with the marker-only classifier, proves the delta is the receipted authorized done commit, refreshes the plan digest and task scope under the manifest lock with the receipt recorded, and Task 3 launches; a semantic plan edit or a replayed receipt refuses exactly as before.

## Outcome

The execute-plan driver recovers both witnessed strandings through two separate bounded transitions: a completed successor worker's unconsumed binding is reconciled after provider-terminality and full-identity verification (worker-start evidence persisted before the terminal evidence, then the ordinary checkpoint and done gates), and a committed checkbox-only progress update refreshes the reviewed-plan digest and task scope at startup under the manifest lock with the authorized-commit receipt recorded; both remain idempotent, refuse mismatched or live sessions and semantic plan edits, and never require direct manifest edits.

Gate delta: one new driver-owned reconciliation transition on the successor path and one new arm in the startup reconciliation's reviewed-plan digest route; every existing refusal (owner mismatch, live session, malformed receipt, semantic edit, replay) keeps its predicate; no launch-policy change and no review-process change.

## Assumptions

- assume the terminality proof reuses the runtime's existing provider-session observation machinery rather than a new liveness probe; basis: the manifest readiness operation already reports the launch state and directs the parent to observe the live worker, so the observable exists (worker verifies the exact probe entry point at execution).
- assume the consume logic of `record_worker_start` is reused for the reconciliation rather than duplicated, so the binding write, the idempotent-duplicate arm, and the consumed-by-other refusal stay single-sourced; the manifest lock is deliberately non-reentrant, so the reconciliation composes with it the way the done flow composes its locked region with its dependent transition (never a same-thread nested acquisition); basis: the function already implements the full identity match and consume sequence the origin demands, and `record_done` demonstrates the composition.
- assume the committed-delta arm classifies `HEAD` plan bytes against the reviewed bytes with the existing marker-only classifier and sources the authorized-commit proof from the recorded plan-disposition receipt chain, not a new ledger; basis: the witnessed Task 3 recovery recorded exactly that receipt against the actual Task 3 commit.
- assume both recoveries sit behind the driver's CLI/transition surface and take the manifest lock like every other manifest mutation; basis: the runtime's transition family and the standing direct-manifest-edit prohibition.

Decision points requiring a grill: keeping the two recoveries as separate transitions rather than one generic recovery bypass: the dispatch entry's own instruction that their state predicates and evidence differ, PLAN-PROMPTS entry execute-plan-successor-checkpoint-recovery, 2026-10-08, affected: Tasks 1 and 2; reuse of record_worker_start's consume sequence instead of a parallel writer: the single-source anti-duplication rule and the entry's bind-to-exact-identity wording, authoring session, 2026-10-09, affected: Task 1; the digest refresh records the authorized-progress receipt without re-scoring the old review as covering the new bytes: the origin row's without-misrepresenting requirement, docs/history/backlog/2026-10-08-execute-plan-checkbox-progress-stales-review-certificate.md, 2026-10-08, affected: Task 2.

## Standing constraints

- Direct manifest edits stay forbidden: both recoveries persist through the driver's locked transition surface only.
- The handoff identity fences stay intact: task, owner, token, generation, and launch identity must match exactly; a live or mismatched provider session refuses; the idempotent-duplicate and consumed-by-other arms keep their semantics.
- The marker-only classifier and the review readiness semantics are reused, never redefined: a semantic plan edit refuses exactly as today, and no refreshed state may claim the prior review covered changed bytes.
- Worker launch policy, the review process, and the two-attempt/replay budgets are out of scope; no existing refusal predicate is relaxed.
- The two recoveries stay separate transitions with their own state predicates; no generic recovery bypass.
- Changes stay limited to execute-plan runtime and its direct tests.

## Evaluation Criteria

**Done when:**

- Tasks 1 and 2 are checked.
- The runtime suite passes (`python3 scripts/test_execute_plan_runtime.py` exit 0).
- `bash scripts/check-no-em-dash.sh added-lines --base main` is clean over the landing range.
- The public hygiene scan passes (exit 0).
- `python3 scripts/plan_readiness.py docs/history/plans/completed/2026-10-09-execute-plan-successor-checkpoint-recovery.md` passes, binding the final review round.

**Ship when:** the next completed successor worker with an unconsumed binding reconciles through the new transition and reaches the ordinary done gates, and the next post-checkbox startup reconciliation refreshes and continues without a full re-review, both without any live-session, mismatch, semantic-edit, or replay refusal weakening.

## Review Scope

**Production code:**

- scripts/execute_plan_runtime.py

**Tests:**

- scripts/test_execute_plan_runtime.py

## Validation Commands

- `python3 scripts/test_execute_plan_runtime.py`
- `bash scripts/check-no-em-dash.sh added-lines --base main`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `python3 scripts/plan_readiness.py docs/history/plans/completed/2026-10-09-execute-plan-successor-checkpoint-recovery.md`

Validation preamble: authoring-time mechanical gates, 2026-10-09: fixer total 0 substitutions; em-dash `touched` OUTCOME: pass; public hygiene OUTCOME: pass; `plan_readiness.py --pre-round` OUTCOME: pass (structural checks clean, review record not consulted). Rule 19 RED-today execution evidence: none observed; the runtime suite on the authoring base exits 0 (770 tests). Round-start state for r1: worktree branch 2026-10-09-execute-plan-successor-checkpoint-recovery at commit db54a9670, plan digest 15282f3d7526c2215f466bd9ca542b3c6cb4d91e14c0e7c17b78bfd16c5d3a42.

## Tasks

### Task 1: Successor worker-start reconciliation for an unconsumed binding

Files: scripts/execute_plan_runtime.py; scripts/test_execute_plan_runtime.py.

- [x] Add a driver-owned reconciliation transition for the completed-successor case: inputs are the worker-start receipt's full identity set plus the provider-session terminality proof; the transition binds to the exact task, owner, token, generation, and launch identity (the same match predicates `record_worker_start` enforces against the live claim, the handoff intent, and the prelaunch binding), proves the provider session is terminal through the adapter's `observe_terminal_evidence` port (a port-unavailable adapter refuses with a distinct evidence line, never read as live-session), refuses a live or mismatched session and a mismatched identity with the existing owner-mismatch vocabulary, consumes the binding through the existing `record_worker_start` consume sequence composed outside the transition's own locked region (the manifest lock is non-reentrant; worker-start evidence persisted first), and then re-enters the ordinary checkpoint path so the held successful receipt passes the handoff guard and reaches the done gates; idempotent on a second call (the duplicate arm answers, no second consume); never writes the manifest outside the locked transition [class: IMPLEMENTATION_REQUIRED]
- [x] Add the focused runtime witnesses: the missing-consumption refusal followed by a successful reconciliation and checkpoint; stale identity refusal (wrong token, generation, or launch id); live-session refusal; consumed-by-different-receipt refusal; retry-after-reconciliation idempotence; and the reconciliation's own refusal for a task with no handoff intent [class: REPOSITORY_TEST]

### Task 2: Committed checkbox-only progress reconciliation at startup

Files: scripts/execute_plan_runtime.py; scripts/test_execute_plan_runtime.py.

- [x] Add a bounded arm to the startup reconciliation's reviewed-plan digest route: when the plan digest mismatch's delta classifies `checkbox-marker-only` with the existing marker-only classifier and the delta is receipted to the authorized done commit through the recorded plan-disposition chain, refresh the plan digest and task scope under the manifest lock, recording the receipt naming the commit and the classification, so the next task launches; the delta is reconstructed from git (the disposition receipt's commit against its baseline revision, the `recover_out_of_scope_plan_edit` classification precedent), because the receipt's recorded digest hashes the post-edit bytes; the arm demands the terminal byte-equality, the current plan digest equal to the receipt chain's last post-edit digest, so a plan moved past the receipted commit by an out-of-runtime edit refuses instead of refreshing over it; the refreshed state names the authorized-progress receipt and never asserts the prior review round covered the changed bytes; a semantic plan delta refuses exactly as today, a replayed or already-consumed receipt stays idempotent, and direct manifest edits remain refused [class: IMPLEMENTATION_REQUIRED]
- [x] Add the focused runtime witnesses: successful refresh and next-task launch after a committed checkbox-only done commit; semantic-edit refusal; replay refusal (the same receipt twice); digest-and-scope state after the refresh (the manifest carries the new digest plus the receipt, not a re-dated review); and the refusals when the delta is checkbox-only but no authorized-commit receipt exists, and when a receipt exists but the current bytes moved past the receipted commit (the terminal byte-equality refusing rather than refreshing over an out-of-runtime edit) [class: REPOSITORY_TEST]
