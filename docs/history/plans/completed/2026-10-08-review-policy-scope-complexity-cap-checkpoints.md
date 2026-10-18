# Plan: review policy by scope, complexity, and cap reflection

Backlog origin: none
Driving force: simplicity + code-quality
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-review-policy-scope-complexity-cap-checkpoints-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/review-policy-cap-checkpoint.md (session no-session)

## Terms

- review effort: the breadth and depth of review work chosen for a change based on its scope and complexity.
- scope: the breadth of the change, including its tasks, affected surfaces, and boundaries.
- complexity: the change's novelty, coupling, interactions, and consequences of failure.
- review iteration cap: the configured number of rounds between trajectory reflections; a cap of five triggers at rounds 5, 10, 15, and each later multiple.
- convergence: at a checkpoint, review results are converging when no existing mechanical-churn or recurrence trigger is active and the open blocking-finding count has decreased since the prior round or is zero; an active churn or recurrence trigger classifies the trajectory as non-converging even if the blocking count fell.
- mechanical-churn trigger: an existing review rule that routes through reconciliation when fold-defect and wording findings dominate, staged findings fail to decrease, or open blocking findings fail to decrease across consecutive rounds.
- cap reflection: a checkpoint that records the review trajectory and chooses the next review action from convergence, scope, and complexity.
- bounded self-heal attempt: after non-convergence, reconciliation may propose one concrete simplification or refactor for an automatic attempt; the allowance does not renew during the same review run.
- cap-closure terminal shape: the existing operator-authorized sidecar and plan-record contract for closing a non-clean review at a configured checkpoint with residual dispositions.

## Why

Review policy currently resolves a project's `personal_projects_root` to choose tighter round limits and to prohibit a cap-closure outcome. That couples review effort to repository ownership, while review scope and complexity describe the work being reviewed.

The round caps also stop reviews unless a loop-specific instruction grants continuation. That can end a useful review when findings are converging, or let patch rounds continue when they are not converging.

## Outcome

Review effort follows scope and complexity across project types, and configured round caps trigger a reflection at each additional cap interval rather than automatically ending the review.

- A small, focused change can use focused review coverage, while a broad or cross-cutting change can use broader review coverage, regardless of project ownership.
- When review results converge at the cap, the loop continues without stopping solely because it reached that count.
- A cap of five starts reflections at rounds 5, 10, 15, and later multiples; simultaneous total-round and full-panel thresholds share one reflection.
- When results do not converge, the loop reconciles the findings and seeks a simpler or refactored approach before another review. At a checkpoint, existing mechanical-churn or recurrence triggers take precedence over a falling blocking count; reaching the cap alone never requires reconciliation.
- After non-convergence, reconcile and try at most one concrete simplification or refactor automatically. If reconciliation offers no concrete alternative, pause immediately. If the reviewed alternative leaves the same unresolved blocking findings, pause before another review and present any newly proposed approaches for operator direction; do not automatically start a second self-heal attempt. Cap closure is available only if this pause coincides with an existing reflection checkpoint.

Gate delta: removes the project-type resolution and personal-only review package from the shared policy, removes the total-round and full-panel cap stop conditions while keeping those counts as reflection triggers, and removes the personal-only cap-closure prohibition; adds a review-layer duty to reflect at a cap and route non-convergence through reconciliation and simplification or refactoring, witnessed by the user's 2026-10-08 review-policy decision; adds one bounded automatic self-heal attempt for non-convergence, then a blocking review-layer pause if no concrete alternative exists or the same blockers persist, witnessed by the user's 2026-10-08 approval ('sure') in this session, in response to the proposal to add this guard to the shared review policy; adds one nested run-wide self-heal attempt state to existing convergence telemetry, with a record-date compatibility fence at 2026-10-09 and validation so an attempt cannot renew after resume; normal state carries the r1 review-run-id as stable run_id; if prior identity evidence is unavailable, initialize `unknown` with that recovery round's minted review-run-id and carry it unchanged; no separate run-start marker is added; adds no separate manifest or project facts.

## Assumptions

- assume the policy covers every review workflow that currently uses project type to set review effort or continuation, including plan review, plan execution, staging guidance, and standalone code-review loops; basis: user confirmed the broad scope at the Step 1.4 requirements confirmation, 2026-10-08.
- assume the existing five-round default remains the shared starting point where a scope/complexity adjustment is not recorded; basis: it is the existing standard default and no replacement value was requested.
- assume scope and complexity guide panel breadth and any explicit review-budget adjustment; plan size is one signal, not a project-type substitute or a mandatory numeric formula; basis: user selected scope and complexity as the effort basis.
- assume each configured threshold triggers reflection again at every additional cap interval; if the total-round and full-panel thresholds coincide, one reflection covers both; basis: user decision, 2026-10-08.
- assume existing convergence telemetry is sufficient unless the implementation audit shows a specific signal gap; for this demonstrated resume-state gap, add only the nested `self_heal_attempt` member and its validator, with no separate manifest or project facts. A new run starts only at a new artifact chain's r1, with run_id equal to that first round's minted review-run-id; all later normal state carries it unchanged. If prior state or identity evidence is missing or malformed, the recovery round records `unknown` with its own minted review-run-id, an explicit recovery exception to the normal r1-bound run_id; this does not start a new artifact chain, and later rounds carry that unknown state unchanged. Unknown never authorizes an attempt. A later round cannot reset the allowance by claiming a new invocation. Self-heal code cannot create a run boundary. A legacy run resumed without reliable prior state records `unknown` and pauses before another automatic attempt.
- assume cap closure remains an explicit operator-authorized exit available at a reflection checkpoint; the cap itself does not prompt for or enact closure.
- assume unresolved blocking findings remain in review scope and existing worker-recovery, reconciliation, and fix-risk decision gates stay in force except where a round-count stop conflicts with this policy.

Decision points requiring a grill: scope/complexity policy and recurring cap reflection; user decisions from the conversation, 2026-10-08, affect Why, Outcome, Review Scope, and Tasks 1-4.

## Standing constraints

- Do not classify projects by ownership or read project facts to choose review strictness.
- Keep the review sidecar schema and existing finding, severity, blocking, and residual-policy contracts unchanged unless a demonstrated signal gap makes a narrowly scoped change necessary; this plan authorizes one nested `self_heal_attempt` member inside `extensions.convergence` and its validator, with no other sidecar schema changes. Records dated before 2026-10-09 remain valid historical records without the member; missing, malformed, or unavailable prior state or identity on resume requires `unknown` bound to the recovery round's minted review-run-id as an explicit exception to normal r1 identity binding; this does not start a new artifact chain, is carried unchanged afterward, and pauses before an automatic attempt. At or after the fence, the state is required. The user authorized override of the machinery-pricing block in the execution manifest.
- Keep completed history artifacts immutable; update living skills and their enforcement pins only.

## Gist & Examples

TLDR: Review effort follows scope and complexity, and round caps trigger reflection, for simplicity and code quality.

Before: a personal project gets a two-round default and a three-round hard stop, while a standard project gets a five-round limit and access to cap closure. The same change can therefore receive different review effort based on where its repository lives. A converging review can stop at the limit, and a non-converging review can spend rounds patching symptoms.

After: projects use one review policy. A small or contained change may receive a focused panel; a large or cross-cutting change may receive broader coverage. At each configured interval, the orchestrator records the existing round trajectory. Converging findings permit continuation. Non-convergence runs through reconciliation and a simplification or refactor path before another review. The cap does not ask the operator to close the loop; the cap-closure record remains available if the operator separately chooses a terminal exit at a reflection checkpoint.

## Design Invariants

- Project ownership and project facts never determine review strictness.
- Each configured total-round or full-panel threshold triggers reflection at every interval; simultaneous thresholds share one reflection.
- A cap reflection does not stop a review or ask for direction by itself. Results converge only when no existing mechanical-churn or recurrence trigger is active and the open blocking-finding count has decreased since the prior round or is zero; an active trigger takes precedence and routes to reconciliation.
- If both the total-round and full-panel counters reach their configured interval on the same review, one reflection covers both; reflection recurs at each later interval.
- Non-convergence triggers the existing reconciliation workflow and a search for simplification or refactoring before another review. Reaching a cap by itself does not trigger reconciliation.
- After non-convergence, allow at most one automatic simplification or refactor attempt. If none is available, or that reviewed change leaves the same unresolved blocking set, pause for operator direction before another review; present any new proposal without executing it automatically.
- Existing finding, blocking, severity, residual-policy, and sidecar-shape contracts stay unchanged unless a demonstrated signal gap requires a narrowly scoped change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: no living review workflow makes review budgets or cap-closure availability depend on project ownership/type.
- convergence: every configured round-count cap starts a reflection at each cap interval; coinciding total-round and full-panel checkpoints share one reflection. Convergence allows continuation, and non-convergence triggers reconciliation plus a simplification or refactor path before the next review.
- maintainability: `review-plan` owns the shared policy, callers point to it, and cap behavior agrees across skills, staging, and readiness validation.

**Done when:**
- The project-type package and personal-only restrictions are removed from all living review-policy surfaces.
- Total-round and full-panel thresholds trigger reflection without an automatic stop, and every affected loop has an explicit continuation path for convergence, a reconciliation plus simplify/refactor path for non-convergence, and an operator pause when no alternative is available or one attempted alternative fails to reduce the unresolved blockers.
- The generic cap-closure sidecar contract remains valid without a project-class check.
- The review policy pins, shared-body checks, readiness tests, em-dash scan, and public-hygiene scan pass.

**Ship when:** none; this is a repository-internal policy change.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code and policy:**
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `docs/maintenance/glossary.md`
- `docs/maintenance/project-decisions.md`

**Tests and enforcement:**
- `scripts/review_policy_sample_contexts.md` *(new)*
- `scripts/check_maintenance_pins.sh`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_plan_readiness.py`
- `scripts/test_review_record_selection.py`

**Plan-related extension:** implementation and review may change files not listed above when a change is causally required to keep the new policy consistent. This extension includes `scripts/validate_review_staging.py` and its embedded self-tests solely to validate the nested run-wide attempt state after the reviewed start-time fence, plus `scripts/review_record_selection.py` and `scripts/test_review_record_selection.py` to make legacy unnumbered singleton round-one records visible to the same selection and continuation guard. Record the extension and reason in the round staging record.

**Out of scope; reject unless plan-related:**
- `docs/history/plans/completed/`; reason: completed plans remain immutable history.
- `docs/history/plans/deferred/2026-10-07-review-plan-project-strictness.md`; reason: the deferred resolver plan stays parked and is not the implementation vehicle for this policy.
- user or project facts files; reason: no project-type replacement field is needed.
- `scripts/plan_readiness.py`; reason: source inspection found the cap-closure validator checks the generic sidecar shape without resolving project class.

## Validation Commands

```bash
set -euo pipefail
python3 -m pytest scripts/test_execute_plan_runtime.py -k test_shared_skill_bodies_remain_runtime_neutral -q
python3 scripts/validate_review_staging.py --selftest
PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness
PYTHONPATH=scripts python3 -m unittest scripts.test_review_record_selection
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh touched
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-08-review-policy-scope-complexity-cap-checkpoints.md
```

**Sample-context workflow validation:** Use `scripts/review_policy_sample_contexts.md` to run the changed review workflows. Hold the change's scope and complexity constant while varying only synthetic contexts for the former personal-project-root membership; assert identical panel choice and cap behavior. Separately compare a small focused change with a broad cross-cutting change and assert the broader change receives the broader panel in both contexts. Set `max_review_rounds` to 5 and `max_full_panel_rounds` to 3: assert the full recurring schedule through round 15: total-round reflections at 5, 10, and 15; full-panel reflections at 3, 6, 9, 12, and 15; round 15 produces one combined reflection. Confirm the independent first hits at full-panel round 3 while total rounds remain below 5 and total round 5 while the full-panel counter remains below 6. Also cover a converging trajectory continuing without a cap-only prompt, a falling blocking count with an active churn trigger routing through reconciliation and a simplification/refactor search before another review, and reconciliation that leaves one automatic alternative failing to resolve the blockers pausing for operator direction before another review, while any second proposal is presented but not automatically attempted; paired no-progress cases at and between reflection checkpoints proving cap closure is offered only at a checkpoint. Record observed panel choices, counters, and next actions in the `Observed outcomes` table in `scripts/review_policy_sample_contexts.md`.

### Task 1: Define the shared scope-and-complexity policy

Context surface: this plan's Terms, Assumptions, and Standing constraints.

Files:
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/plans/SKILL.md`
- `docs/maintenance/glossary.md`
- `docs/maintenance/project-decisions.md`

Evidence:
- The absence pins and maintenance-pin check show no active project-class review policy remains.
- The review-plan and shared panel-selection contracts identify scope and complexity as the effort basis, while the configured round cap is a recurring trajectory-reflection checkpoint. A five-round cap reflects at rounds 5, 10, and 15; if total-round and full-panel intervals coincide, one reflection covers both. At reflection, an active mechanical-churn or recurrence trigger makes the trajectory non-converging even when blocking findings fell; otherwise a falling blocking count or zero open blockers permits continuation. The reflection records the trajectory but does not ask for direction when results converge.

- [x] Replace the project-class resolver and personal/standard package in `review-plan` with one shared policy that describes scope and complexity signals, treats plan size as one signal, and keeps one shared default where no adjustment is justified [class: IMPLEMENTATION_REQUIRED]
- [x] Update `review-panel-selection.md` as the single source of truth for choosing focused or broader panels from scope and complexity, preserving the existing risk-signal floor [class: IMPLEMENTATION_REQUIRED]
- [x] Update plan-review reflection and reconciliation rules: every configured interval reflects; cap alone does not trigger reconciliation; no active mechanical-churn or recurrence trigger plus a falling blocking count or zero open blockers means convergence and continuation; any active churn or recurrence trigger means non-convergence, reconciliation, and a simplify/refactor search before another review [class: IMPLEMENTATION_REQUIRED]
- [x] Align the glossary and project decision record with the implemented contract, retaining the two-class backlog default from ADR-0002 [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the shared policy and plan-review contract [class: IMPLEMENTATION_REQUIRED]

### Task 2: Apply checkpoint behavior to execution and standalone review loops

Context surface: this plan's Terms, Assumptions, Standing constraints, and Task 1 policy.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

Evidence:
- The loop instructions explicitly distinguish a cap-triggered reflection from a stop condition.
- A scope/complexity-based panel choice and deterministic convergence path are available after the checkpoint without requiring a standing instruction solely to exceed the cap. Every interval reflects again, coinciding total-round and full-panel intervals share one reflection, and existing churn or recurrence triggers route to reconciliation even when the blocking count fell.
- At most one simplify/refactor alternative is attempted automatically; no available alternative or unchanged blockers after that attempt pause for operator direction before another review.

- [x] Change `max_review_rounds` and `max_full_panel_rounds` from automatic stop limits to recurring reflection triggers; combine coinciding thresholds, record each interval, continue without a cap-only prompt when results converge, and reconcile non-convergence before the next review [class: IMPLEMENTATION_REQUIRED]
- [x] After non-convergence, try at most one concrete simplification or refactor automatically; if none is available or the reviewed alternative leaves the same blockers, pause for operator direction before another review and present any next proposal without executing it automatically [class: IMPLEMENTATION_REQUIRED]
- [x] Remove cap-only reconciliation from the standalone review loop; preserve independent churn/recurrence reconciliation triggers and apply the same convergence precedence as plan review [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the personal-project default and hard cap; preserve the existing escalation, timeout, re-entry, material-user-decision, and no-progress reconciliation stops that are unrelated to project type or round count [class: IMPLEMENTATION_REQUIRED]
- [x] Record the reflection using existing loop records and convergence data; add only the nested run-wide `self_heal_attempt` member inside `extensions.convergence` when needed to enforce the one-attempt limit across resume, without creating a separate manifest [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the execution and standalone-loop policy changes [class: IMPLEMENTATION_REQUIRED]

### Task 3: Remove class-based closure restrictions and synchronize consumers

Context surface: this plan's Terms, Assumptions, Standing constraints, and Task 1 policy.

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `scripts/test_plan_readiness.py`

Evidence:
- The generic cap-closure test set passes without needing project facts.
- A valid explicit operator choice can close the cap-closure shape; reaching the cap alone does not prompt or enact closure.
- The staging sidecar gains only the nested attempt-state member needed to preserve the one-attempt rule across resume; existing finding, severity, blocking, and residual-policy contracts remain unchanged.

- [x] Remove class-resolution references and personal-only cap-closure prohibitions from staging and consumer guidance; preserve the generic operator-authorized cap-closure shape and unresolved-blocking checks [class: IMPLEMENTATION_REQUIRED]
- [x] Run the cap-closure readiness tests and confirm the sidecar contract remains generic and independent of project type [class: REPOSITORY_TEST]
- [x] Commit consumer and cap-closure alignment [class: IMPLEMENTATION_REQUIRED]

### Task 4: Pin the policy and run the validation suite

Context surface: this plan's Terms, Assumptions, Standing constraints, and Tasks 1-3.

Files:
- `scripts/review_policy_sample_contexts.md` *(new)*
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `docs/maintenance/glossary.md`
- `docs/maintenance/project-decisions.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_plan_readiness.py`
- `scripts/validate_review_staging.py`
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`

Primary class anchors:
- `validate_self_heal_attempt_state` in `scripts/validate_review_staging.py`
- `select_record` and `_enumerate` in `scripts/review_record_selection.py`

Evidence:
- `bash scripts/check_maintenance_pins.sh` pins the shared policy, cap reflection behavior, class-policy removal, and class-agnostic closure rules.
- The listed test and scan commands pass on the final tree, and the policy pins distinguish recurring intervals, coincident thresholds, convergence continuation, churn-triggered reconciliation, and fail-closed run-wide attempt state, including the `unknown` resume disposition.
- The sample fixture carries its procedure and an `Observed outcomes` table; the completed table records identical behavior for identical scope and complexity regardless of former project-root membership, distinct behavior for small and broad changes, independent total-round and full-panel checkpoints, every scheduled 5/3 reflection through round 15 (total: 5, 10, 15; full-panel: 3, 6, 9, 12, 15), one combined reflection at round 15, and the correct convergence/churn next actions.

- [x] Add presence pins for scope/complexity-based panel selection, reflection at recurring intervals (including later intervals such as 10 and 15 for a five-round cap), one reflection when thresholds coincide, the convergence predicate and continuation path, and churn/recurrence precedence with reconciliation plus simplify/refactor routing [class: IMPLEMENTATION_REQUIRED]
- [x] Add absence pins for cap-only stops and cap-only reconciliation, the project-class resolver, and personal-only limits on each affected surface [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the one-attempt self-heal limit and add sample trajectories proving that no available alternative pauses immediately and an unsuccessful first alternative pauses before another review [class: IMPLEMENTATION_REQUIRED]
- [x] Add paired no-progress cases at and between reflection checkpoints, asserting cap closure is available only when the operator pause coincides with a checkpoint [class: IMPLEMENTATION_REQUIRED]
- [x] Define the post-fence convergence-state contract and legacy resume disposition in `review-staging`, with a typed status union and exact field names [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `validate_review_staging.py` to require post-fence state and validate status, normal r1-bound run identity, the explicit unknown-recovery identity exception without a new chain boundary, sidecar round agreement with `-rN` filenames, treating unnumbered canonical records as singleton r1 only, predecessor discovery by stable artifact stem across dates, consumed round/digest binding, and carry-forward across the full linked chain using iterative traversal; current post-fence filename and sidecar dates must be calendar-valid or reject both `unused` and `unknown`; predecessor filenames and sidecar dates must be calendar-valid before they count as trusted post-fence evidence, requiring `unknown` recovery when either predecessor date is calendar-invalid, and require `unknown` when the predecessor sidecar `source_digest` is missing or malformed; validate exactly one complete minted identity pair on every linked post-fence predecessor. Separately, require `unknown` when a predecessor's complete minted pair is missing, duplicated, malformed, or its fallback marker conflicts with either mint field. Reject a current record combining the fallback marker with a mint field and reject a current usage fallback without a minted review-run-id [class: IMPLEMENTATION_REQUIRED]
- [x] Extend review record selection to recognize unnumbered singleton r1 records, allocate r2 on explicit continuation while preserving the matched filename family stem, and refuse duplicate r1 representations [class: IMPLEMENTATION_REQUIRED]
- [x] Add validator self-test cases for valid unused/consumed states, missing post-fence state, malformed status/identity/round/digest and calendar-invalid predecessor filename/sidecar dates, with paired cases for each invalid predecessor date that accept `unknown` and reject `unused`, plus current-record cases proving invalid filename and sidecar dates reject both `unused` and `unknown`; include filename/sidecar round mismatch, unnumbered singleton and non-r1 rejection, cross-date predecessor lookup including duplicates, legacy-to-post-fence unknown recovery, unknown carry-forward/reset attempts, broken earlier links, a linked history longer than Python's recursion limit, bare-mint-fallback rejection, for missing/malformed `review-run-id`, missing/malformed/duplicate `review-started-at-ms`, duplicate `review-run-id`, fallback-marker-plus-pair predecessor cases including each individual mint field, and separately test missing and malformed predecessor `source_digest`, accepting `unknown` and rejecting `unused` for each; for current fallback-marker-plus-pair, reject the record with either individual mint field, unhashable status values, duplicate predecessor rejection, and consumed state that cannot reset on resume [class: REPOSITORY_TEST]
- [x] Pin the state shape and fail-closed resume contract; test selection reuse/allocation for unnumbered singleton r1, alias-family stem preservation, duplicate-r1 refusal, and run the validator self-test and plan validation commands [class: REPOSITORY_TEST]
- [x] Commit the validator extension [class: IMPLEMENTATION_REQUIRED]
- [x] Run all commands in `## Validation Commands` on the final tree and fix any failure caused by this plan [class: REPOSITORY_TEST]
- [x] Add `scripts/review_policy_sample_contexts.md` with realistic sample plans and round records for paired former-project-root contexts, small and broad changes, independent total-round and full-panel thresholds, every recurring checkpoint through their later coincidence, convergence, active-churn, and bounded self-heal trajectories; include an `Observed outcomes` table for the validation run [class: IMPLEMENTATION_REQUIRED]
- [x] Run the changed review workflows with those sample contexts and record panel choices, checkpoint counts, and next actions in the fixture's `Observed outcomes` table [class: REPOSITORY_TEST]
- [x] Commit the policy pins and final validation [class: IMPLEMENTATION_REQUIRED]
