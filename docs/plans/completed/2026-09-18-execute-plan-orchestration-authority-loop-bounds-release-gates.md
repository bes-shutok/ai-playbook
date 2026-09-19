# Plan: execute-plan orchestration: authority, loop bounds, release gates

Backlog origins: docs/history/backlog/2026-09-17-execute-plan-single-authority-and-ownership-validation.md; docs/history/backlog/2026-09-17-execute-plan-bound-review-loop-and-plan-freeze.md; docs/history/backlog/2026-09-17-execute-plan-scope-and-release-gate-separation.md; docs/history/backlog/2026-09-18-execute-plan-residual-acceptance-exit-for-review-loops.md
Group: P11 (docs/tmp/future-plan-prompts-2026-09-16.md); composes with the P9 plan docs/plans/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety.md (execution sequenced after P9 lands)
Language guidelines: projects/.ai-playbook/python_guidelines.md (validator work is Python)

## Terms

- **Ownership check (plan validator)**: the function Tasks 1 adds to `scripts/plan_readiness.py` (`plan_ownership_problem`): static checks over the plan text that enforce one creating task per new file (the plans template's `*(new)*` annotation is the creation record), consumer-before-owner ordering for file paths (method-token ordering stays an authoring and review duty), `Files:` paths existing on disk (checklist-only references to nonexistent paths are an authoring and review duty, recorded in the origin dispositions) or carrying that annotation, and at most one transition-table section.
- **Classification tag**: the inline suffix `[class: IMPLEMENTATION_REQUIRED]` or `[class: REPOSITORY_TEST]` that Tasks 2 requires on every task checklist item via the `scope_classification_problem` check it adds to `scripts/plan_readiness.py`; `EXTERNAL_RELEASE_GATE` and `OPERATIONS_FOLLOW_UP` are invalid inside task sections (they belong in Ship when).
- **Bounded non-semantic correction**: a plan edit recorded as a `plan_correction:` manifest line before the edit's skill-gated write, limited by `budget_plan_edits`, verified by a focused re-cert round over the corrected sections instead of a whole-plan review.
- **Plan-change recovery path**: the named path for a semantic plan change: a `plan_change:` manifest line naming the changed sections, then a fresh whole-plan review round.
- **Residual policy**: the `residual_policy:` manifest line recorded before a verification round runs, granting the sanctioned residual-acceptance exit for a named fix set; its machine-checkable carrier is the structured `residual_policy` input field of the pre-archive stage (Tasks 4 adds it).

## Assumptions

- assume P9's execution is in flight at authoring time (its driver predicate `_pre_archive_gate` has already landed in scripts/execute_plan_runtime.py, verified 2026-09-18); this plan's execution is sequenced after P9 completes and its Phase 0 drift check re-baselines the shared execute-plan SKILL.md sections (Step 3.5, Review end condition table, Hard Gates) and the landed driver predicate against whatever P9 state has landed; basis: grep of the working tree plus the group ledger's sequencing.
- assume the new validator checks are date-gated on the latest review round's date via a new `PLAN_STRUCTURE_MIN_DATE` constant (pattern parity with DECISION_MARKER_MIN_DATE and REVIEW_SCOPE_MIN_DATE), value `2026-09-19`, so legacy open plans are grandfathered until their next re-cert and this plan's own rounds (dated 2026-09-18) do not self-trip; basis: the gating helpers verified in scripts/plan_readiness.py.
- assume in-file selftests are the validator's test convention (the `_selftest_*` suite behind `--selftest`, exit 0 today); no separate test file is created; basis: scripts/plan_readiness.py structure verified on disk.
- assume `plan_correction:`, `plan_change:`, `budget_readiness_reviews:`, and `budget_plan_edits:` are session `manifest.md` lines (siblings of `review_round` and `recurrence_groups`), written by the orchestrator, not machine-manifest fields; the `residual_policy:` audit line lives in the session manifest.md AND its machine-checkable carrier is a structured `residual_policy` input field of the pre-archive stage (finding ids, grant source, recorded-at), which the landed predicate can verify against the focused sidecar - the driver never parses manifest.md; basis: the landed predicate's input-attestation design (phase5_checklist, review_sidecar) verified on disk.
- assume the classification tag vocabulary extends, and does not replace, the plans skill Checklist inclusion gate taxonomy (repository implementation / release condition / external prerequisite); the Task 2 rule text carries the explicit mapping and conflict rule; basis: the gate's text.
- assume this plan self-complies with the new gates at its own re-certs: its checklist items are pre-tagged (Task 2's vocabulary), its Files lists claim no duplicate `*(new)*` creation, and its own review rounds dated before 2026-09-19 are grandfathered; a re-cert dated on or after the minimum finds the tags present; basis: Task 5's verification item.
- assume scripts/plan_readiness.py carries 37 pre-existing em dashes on 35 lines in comments and docstrings; they are outside the repo's prose-only em-dash policy (.py files are scanned only under the opt-in flag), this plan leaves them untouched, and the Task 5 hygiene sweep covers the three prose skill surfaces only; basis: measured 2026-09-18.

Origin criteria dispositions (per the origins' promotion-audit rule):
- Origin A criterion 3 (cross-validation of manifest rows, task projections, and runtime allowed paths): covered by construction - the driver's create seeds allowed paths from the same Files lists Tasks 1 inventories, and the create operation's existing fail-closed path policy owns the runtime half; no separate check.
- Origin A criterion 1's contradictory-outcome half (conflicting normative outcomes for the same state and input): the transition-table uniqueness check (clause d) is the mechanical subset; semantic contradiction detection remains a review-agent duty per origin A's own Prevention paragraph (review agents classify findings as contradiction or executable gap).
- Origin A's task-ordering criterion for test-method tokens: the static check orders file paths only (creation is marked by the `*(new)*` annotation); method-level ownership ordering is an authoring-time duty of the plans skill's ownership-ledger rule (Task 2 adds it) and a review-agent classification duty (recorded).
- Origin B criterion 7 (regression tests for continuation, interruption, semantic change, repeated corrections, exhausted budgets): these are manifest-plus-prose flows, not code paths; their witnesses are the budget-exhaustion stop, the Step 0.5 focused re-cert round, and the obligation probes in this plan's Validation Commands; full workflow-simulation fixtures would be execute-plan driver work and are out of scope (candidate for a future runtime plan).
- Origin A's referenced-path existence criterion, checklist-only half: clause (c) checks `Files:` paths; a checklist-only reference to a nonexistent path is an authoring-time and review-agent duty (the ownership ledger and the review-plan correctness lens), recorded here rather than checked statically
- Origin C criterion 4 (rejecting a repository task depending on an unavailable external witness without a declared dependency): the classification check removes external classes from task checklists entirely; witness availability stays a review-time and inclusion-gate judgment, not a static check (recorded).

Decision points requiring a grill: validator home for the new checks: extend scripts/plan_readiness.py in file with new problem functions and in-file selftests, decision: standing pre-authorization accepting the existing in-file pattern over a new checker script, source: authoring prompt 2026-09-18, affects Tasks 1 and 2; date gate: gate the new checks on the latest review round's date via PLAN_STRUCTURE_MIN_DATE = 2026-09-19, decision: standing pre-authorization accepting pattern parity with the existing min-date constants, source: authoring prompt 2026-09-18, affects Tasks 1 and 2; origin B current state: the freeze and direct Task N to Task N+1 progression already exist in the Readiness decision table, so only the correction path, the recovery path, and the budgets are new work, decision: standing pre-authorization accepting the current-state reading, source: authoring prompt 2026-09-18, affects Task 3; classification enforcement point: inline tags on task checklist items with Ship-when prose exempt, decision: standing pre-authorization accepting the mechanically checkable form, source: authoring prompt 2026-09-18, affects Task 2; residual-exit authorization: the orchestrator proposes and a standing instruction or explicit user grant records the policy before the verification round, decision: standing pre-authorization accepting the auditable-recording shape from the origin, source: authoring prompt 2026-09-18, affects Task 4.

## Gist & Examples

Four orchestration gaps close together because they share one root shape: the execution workflow's guarantees live in prose that orchestrators can skip, and the plan validator cannot see ownership, classification, or convergence policy.

1. **Authority and ownership (origin A).** Complex plans describe the same file, test witness, or state transition under several task owners, and reviewers find the contradictions late. Example: Tasks 1 and 2 both list `scripts/plan_readiness.py` in Files without `*(new)*` (sequential edits of one file, which passes); a checklist item in Task 1 references `scripts/new_checker.py` that Task 5 marks `*(new)*` (consumer-before-owner, which fails). Today nothing fails until a reviewer reads all tasks. After this plan the readiness validator reports the duplicate owner and the consumer-before-owner ordering by name, before implementation.

2. **Loop bounds and plan freeze (origin B).** One clean readiness review already permits direct Task N to Task N+1 progression (the Readiness decision table's direct-continuation row); the origin's acceptance 1 is current state, and this plan codifies it rather than rebuilding it. What is missing is what happens when the plan must change mid-run: today every digest change routes to a whole-plan review. The plan adds a bounded non-semantic correction path (a `plan_correction:` manifest line recorded before the edit, capped by `budget_plan_edits`, verified by a focused re-cert of the corrected sections) and a named plan-change recovery path (a `plan_change:` line naming the changed sections, then a fresh whole-plan round), plus separate, independently capped budgets whose exhaustion records the exact state and a backlog item instead of looping silently.

3. **Scope and release-gate separation (origin C).** Plans absorb deployment and operations requirements into task checklists, making local implementation depend on evidence the repository cannot produce. After this plan every task checklist item carries a classification tag, and the validator rejects `EXTERNAL_RELEASE_GATE` or `OPERATIONS_FOLLOW_UP` used as a task checkpoint; those requirements live in Ship when with owner, evidence source, and closure condition (the release-gate ledger's home). A review finding that only improves external evidence routes to a backlog item or the release-gate ledger, never a new implementation task.

4. **Residual-acceptance exit (origin D).** Fresh-adversarial panels over large diffs asymptote toward zero blocking without reaching it, and today the only sanctioned exits are a clean round or the cap stop with an ask. The efficiency run needed an ad-hoc chat agreement for what this plan makes process: when a reconciliation pass or fix-risk triage produces a named fix set, the orchestrator proposes the exit, a standing instruction or user grant records `residual_policy:` in the manifest before the verification round, one address pass fixes the named set, one focused targeted round verifies it, and any new blocking finding outside the set becomes a durable backlog item with an owner and a trigger.

Code and prose change together under the ledger's G3 rule: the validator owns the mechanical checks (Tasks 1 and 2), and the skill prose commands it and cites it rather than restating its rules.

## Design Invariants (CR Guard)

- **Cite owners, never restate:** the ownership and classification rules are owned by the validator functions and their selftests; the plans and execute-plan skill prose references them. The freeze is owned by the Readiness decision table; Task 3 cites it and adds only the correction, recovery, and budget clauses.
- **Date-gated adoption:** both new checks gate on `PLAN_STRUCTURE_MIN_DATE` via the existing `_gate_fires` helper over the latest review round's date; legacy plans fail only at their next post-min-date re-cert, and the check reason strings say so.
- **Fail-closed first-failure:** each new problem function returns the first violation with the exact task, path, method, or item named, mirroring `review_scope_problem`'s contract.
- **Composition with P9:** execution of this plan lands after P9; no task rewrites P9's landed edits; shared-section edits are additive rows and clauses, not rewrites of P9's text.
- **Sanctioned exits stay auditable:** the residual exit and the correction path are only valid when their manifest lines were recorded before the verification or edit ran; a resumed session cannot widen a recorded policy.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each new validator check fires on exactly its named violation class and names the offending task, path, method, or item; each is covered by an in-file selftest arm that fails when the check is removed
- consistency: every new skill obligation has a dedicated fail-closed validation probe; prose cites the owning validator function or table instead of restating rules
- minimality: no new checker script, no new test file; the diff touches only the listed surfaces
- hygiene: `scripts/check-no-em-dash.sh` and `scripts/scan-public-hygiene.sh` exit 0; `python3 scripts/plan_readiness.py --selftest` exits 0

**Done when:**
- `python3 scripts/plan_readiness.py --selftest` passes including the new `_selftest_plan_ownership` and `_selftest_scope_classification` arms
- the full Validation Commands block passes

**Ship when:**
- execution of this plan is sequenced after the P9 plan lands, with the Phase 0 drift re-baseline of the shared sections
- deployed `$HOME/.ai-playbook/scripts` validator copies refresh in the separate standing maintenance pass (not this plan's gate)

## Residual review findings (recorded at the 5-round cap)

The authorized review budget is 5 rounds. Round 5 (the cap) reported ready=no with one blocking finding
(F1: no prescribed command executed the runtime driver suite Task 4 amends) and two Lows (F2: no probe
for the plans-skill ownership-ledger rule; F3: the Terms overclaimed clause (c)'s coverage of
checklist-only references). All three are folded into this final draft: the driver suite now runs in
Validation Commands section 1 with a Task 4 RED/GREEN bullet, the ownership-ledger rule has its probe,
and the Terms claim is corrected with the disposition recorded above. The digest after this fold has not
been re-reviewed because the cap was reached; the executing session's mandatory PRE-STEP readiness gate
re-certifies the final bytes (focused re-cert round over any stale digest) before Phase 1, which is the
designed cover for exactly this gap. Review history: r1 (six blocking, fold-inducing), r2 (three),
r3 (two), r4 (one), r5 (one, folded here).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `docs/plans/2026-09-18-execute-plan-orchestration-authority-loop-bounds-release-gates.md` *(this plan; triage folds and the Task 5 validation sweep)*

**Tests:**
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-reconciliation/SKILL.md`; owns the normalization and design-reflection machinery this plan cites, never edits it
- `scripts/execute_plan_resume_watcher.py`; watcher machinery untouched (the runtime driver IS touched by Task 4's OR-branch and is listed under explicit must-fix)
- `docs/history/backlog/2026-09-17-execute-plan-worker-deadline-contract.md`; the worker-deadline origin stays in its own backlog item, not this group

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1

expect_match() {
  p="$1"; shift
  for f in "$@"; do
    if [ ! -f "$f" ]; then echo "FAIL: missing swept path $f"; exit 1; fi
    if ! grep -qF -- "$p" "$f"; then echo "FAIL: obligation missing in $f: $p"; exit 1; fi
  done
}

expect_no_match() {
  p="$1"; shift
  for f in "$@"; do
    if [ ! -f "$f" ]; then echo "FAIL: missing swept path $f"; exit 1; fi
  done
  rc=0
  grep -nE "$p" "$@" || rc=$?
  if [ "$rc" -ge 2 ]; then echo "FAIL: sweep tool error rc=$rc for $p"; exit 1; fi
  if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden pattern present: $p"; exit 1; fi
}

PR="scripts/plan_readiness.py"
EP="agents/skills/execute-plan/SKILL.md"
PL="agents/skills/plans/SKILL.md"
RL="agents/skills/review-loop/SKILL.md"
RC="agents/skills/execute-plan/runtime-contract.md"

# 1. Validator selftests (the two new arms) and the runtime driver suite (Task 4's OR-branch fixtures)
python3 scripts/plan_readiness.py --selftest || { echo "FAIL: validator selftest"; exit 1; }
python3 scripts/test_execute_plan_runtime.py || { echo "FAIL: runtime driver suite"; exit 1; }

# 2. Ownership-check obligations (origin A); spans quoted from Task 1
expect_match "PLAN_STRUCTURE_MIN_DATE" "$PR"
expect_match "def plan_ownership_problem(" "$PR"
expect_match "_selftest_plan_ownership" "$PR"
expect_match "consumer-before-owner" "$PR"
expect_match "duplicate creating task" "$PR"
expect_match "the plans template's new-file record, the planned-new marker" "$PR"

# 3. Classification-check obligations (origin C); spans quoted from Task 2
expect_match "def scope_classification_problem(" "$PR"
expect_match "_selftest_scope_classification" "$PR"
expect_match "[class: IMPLEMENTATION_REQUIRED]" "$PR"
expect_match "classification tag" "$PL"
expect_match "taxonomy mapping and conflict rule" "$PL"
expect_match "ownership ledger of files, witnesses" "$PL"
expect_match "[class: REPOSITORY_TEST]" "$PL"

# 4. Loop-bounds obligations (origin B); spans quoted from Task 3
expect_match "plan_correction:" "$EP"
expect_match "budget_plan_edits" "$EP"
expect_match "plan-change recovery path" "$EP"
expect_match "budget_readiness_reviews" "$EP"
expect_match "focused re-cert" "$EP"
expect_match "prompt must include the recorded class" "$EP"

# 5. Residual-exit obligations (origin D); spans quoted from Task 4
expect_match "residual_policy:" "$EP"
expect_match 'optional `residual_policy` field' "$EP"
expect_match "Residual-acceptance exit" "$EP"
expect_match "residual policy is satisfied" "$EP"
expect_match "backlogged-residual tally" "$EP"
expect_match "satisfied recorded residual policy" "$EP"
expect_match "test_accepts_residual_policy_exit" "scripts/test_execute_plan_runtime.py"
expect_match "lists the backlogged residuals" "$EP"
expect_match "routes any out-of-set change back" "$EP"
expect_match "count only blocking findings outside the recorded residual set" "$RL"
expect_match "residual-acceptance exit" "$RL"
expect_match "residual_policy" "$RC"
expect_no_match 'plan_correction:' "$PL"

# 6. Authoring hygiene over the touched prose surfaces and this plan
#    (scripts/plan_readiness.py is excluded: it carries 37 pre-existing em dashes
#    in comments, outside the prose-only em-dash policy; recorded in Assumptions)
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file "$EP" "$PL" "$RL" || { echo "FAIL: em dash present"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "FAIL: public hygiene scan"; exit 1; }
```

### Task 1: Plan-ownership static checks in the readiness validator (origin A)

Files:
- `scripts/plan_readiness.py`

- [x] Add the module constant `PLAN_STRUCTURE_MIN_DATE = "2026-09-19"` beside the existing min-date constants, and a `_selftest_plan_ownership` arm registered with the existing selftest suite [class: REPOSITORY_TEST]
- [x] Add `def plan_ownership_problem(` with signature `(plan_text: str, repo_root: Path) -> str | None`, returning the first violation only, each reason naming the exact task ordinal, path, or method: (a) `duplicate creating task` for a `Files:` path annotated `*(new)*` (the plans template's new-file record, the planned-new marker) in more than one task's `Files:` section - shared listings without the annotation are sequential edits of one file and never trip; (b) `consumer-before-owner` when a checklist item references a file path whose creating task (the task carrying the `*(new)*` annotation for it) is a later task - referencing an already-created witness in a later task passes, per origin A criterion 4; test-method tokens are not ordered by this static check (they carry no creation marker): their ownership ordering is an authoring-time duty of the ownership ledger and a review-agent classification duty, recorded in the origin dispositions; (c) a `Files:` path that does not exist under `repo_root` and carries no `*(new)*` annotation; (d) more than one section heading denoting a transition table (`state transition` or `transition table` in the heading). Do not reflow or fix the file's 37 pre-existing em dashes; they are outside the prose-only em-dash policy and out of scope [class: IMPLEMENTATION_REQUIRED]
- [x] Wire it into `evaluate_readiness` after the existing `review_scope_problem` call, gated by `_gate_fires(round_date, PLAN_STRUCTURE_MIN_DATE)` with a reason string in the `_gated_probe_reason` shape naming the min date [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the in-file selftest suite with `_selftest_plan_ownership`: fixture plans that trip (a) through (d) individually, one clean fixture (including the legitimate shared-edit shape and a reference-after-owner shape that must pass), one mutation probe asserting each check stops firing when its own clause is removed, and two gated-wiring cases in the existing temp-tree convention: a plan whose latest sidecar is dated before 2026-09-19 stays exempt, and one dated on or after it fails with the gated reason naming the minimum date [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/plan_readiness.py --selftest` fails because `plan_ownership_problem` and its selftest arm do not exist yet [class: IMPLEMENTATION_REQUIRED]
- [x] Implement; run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` passes [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `validator: plan ownership checks in the readiness gate (P11 origin A)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Classification tags and the scope ledger (origin C)

Files:
- `scripts/plan_readiness.py`
- `agents/skills/plans/SKILL.md`

- [x] Add `def scope_classification_problem(` with signature `(plan_text: str) -> str | None`, returning the first violation only: (a) a task checklist `- [ ]` item with no `[class: ...]` tag; (b) a task checklist item tagged `[class: EXTERNAL_RELEASE_GATE]` or `[class: OPERATIONS_FOLLOW_UP]`; (c) a tag value outside the four-name vocabulary. Ship when prose is exempt [class: IMPLEMENTATION_REQUIRED]
- [x] Wire it into `evaluate_readiness` beside Task 1's check under the same `PLAN_STRUCTURE_MIN_DATE` gate, and extend the selftest suite with `_selftest_scope_classification`: fixtures tripping (a) through (c) and one clean fixture with both valid tags, plus the same two gated-wiring cases in the temp-tree convention (sidecar dated before 2026-09-19 stays exempt; dated on or after fails with the gated reason) [class: REPOSITORY_TEST]
- [x] Run → expect RED: the selftest fails because the function and arm do not exist yet [class: IMPLEMENTATION_REQUIRED]
- [x] Implement; run → expect GREEN [class: IMPLEMENTATION_REQUIRED]
- [x] In the plans skill's Checklist inclusion gate section, add the `classification tag` rule: every task checklist item carries `[class: IMPLEMENTATION_REQUIRED]` or `[class: REPOSITORY_TEST]`, external-gate and operations requirements are written in Ship when with their class, evidence owner, and closure condition named in prose, and add the scope-ledger prevention sentence the origin's Prevention section asks for (classification recorded at plan creation and re-checked at the first readiness review), plus origin A's Prevention authoring rule (the ownership ledger of files, witnesses, and their owning tasks is written before prose expansion, so method-level ownership ordering is settled at authoring time) [class: IMPLEMENTATION_REQUIRED]
- [x] In the same rule text, add the taxonomy mapping and conflict rule: `IMPLEMENTATION_REQUIRED` and `REPOSITORY_TEST` refine the inclusion gate's repository-implementation class, `EXTERNAL_RELEASE_GATE` and `OPERATIONS_FOLLOW_UP` refine its release-condition and external-prerequisite classes respectively, and on conflict the stricter inclusion-gate classification wins [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `validator: scope classification tags with validator rejection (P11 origin C)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Loop bounds - corrections, recovery, budgets (origin B)

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] In Step 0.5's digest rule, after the existing resume-exemption paragraph, add the `bounded non-semantic correction` branch: the `plan_correction:` manifest line is OPENED before the skill-gated edit with its timestamp, before-digest, quoted span, and class non-semantic, and the after-digest is appended to the same line immediately after the write; corrections are capped by `budget_plan_edits` (default 3 per run, applying from run start, not per phase) and verified by a `focused re-cert` review round over the corrected sections only (review-panel-selection Targeted follow-ups), never a whole-plan round; the re-cert round's prompt must include the recorded class and span so the reviewer validates the class as part of the round [class: IMPLEMENTATION_REQUIRED]
- [x] Add the `plan-change recovery path` paragraph: a semantic change (behavior, task order, ownership, evidence class, or release scope) records a `plan_change:` manifest line naming the changed sections and requires a fresh whole-plan review round before continuation [class: IMPLEMENTATION_REQUIRED]
- [x] In the Phase 3 "Track in manifest.md" list, add the two budget lines `budget_readiness_reviews:` (fresh whole-plan review rounds per run, default 3) and `budget_plan_edits:` (non-semantic corrections per run, default 3, from run start - the list entry is the tracking home for the line the Step 0.5 branch defines), with the exhaustion rule: when a budget is exhausted the orchestrator records the exact state (which budget, what was attempted, the current digest and review position), writes or updates a durable backlog item, and stops for direction instead of continuing silently [class: IMPLEMENTATION_REQUIRED]
- [x] Add one sentence in the Readiness decision table section codifying the freeze as current state: the table's direct-continuation row already permits Task N to Task N+1 progression without a whole-plan re-certification while the digest and manifest stay valid (a citation, not new machinery) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the section 4 obligation probes → expect GREEN; sections 2, 3, and 5 stay in their prior state at this task point [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skills: bounded plan corrections, change recovery, and separate loop budgets (P11 origin B)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: The sanctioned residual-acceptance exit and its gate reconciliation (origin D)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/review-loop/SKILL.md`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] In the Review end condition table, add the row `Residual-acceptance exit`: when a reconciliation pass or the fix-risk triage produces a named fix set, the orchestrator may propose the bounded exit; a standing instruction or explicit user grant records `residual_policy:` in the manifest BEFORE the verification round runs (the named finding set, the grant's source, and the date), the exit is one address pass for the named set plus ONE focused targeted round composed per review-panel-selection Targeted follow-ups, findings in the named set must reach fixed or dropped, any NEW blocking finding outside the set becomes a `durable backlog item` with an owner and a trigger instead of another round, and the `exit report lists the backlogged residuals` with their item paths [class: IMPLEMENTATION_REQUIRED]
- [x] Add the Step 3.5 routing row: when a recorded `residual_policy` is satisfied (the address pass and the one focused targeted round completed, the named set reached fixed or dropped, and every out-of-set new blocking finding carries its durable backlog item), Step 3.5 routes to Phase 4 - the clear row's blocking-clean requirement does not apply under the recorded policy; the cap row keeps a pointer to the same exit as the second, user-mediated entry point [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile the governing gates (each gets the explicit exception): the Review end condition Blocking row gains the clause that the gate `accepts the exit report's backlogged-residual tally` in place of zero blocking findings when the recorded residual policy is satisfied; Phase 5's success checklist item 3 gains the alternative exit evidence (a `satisfied recorded residual policy` with its exit report, alongside the existing blocking-clean option); review-loop's Exit criterion 1 is amended to `count only blocking findings outside the recorded residual set` [class: IMPLEMENTATION_REQUIRED]
- [x] Give the exit its sidecar contract for P9's landed terminal gate: in `scripts/execute_plan_runtime.py`, extend the pre-archive stage's input with an optional structured `residual_policy` field (finding ids, grant source, recorded-at epoch) and an OR-branch in the clean-round sidecar predicate - it additionally accepts the focused verification-round sidecar when the input carries `residual_policy` whose recorded-at predates that round's date and no sidecar findings row is both `blocking: true` and a member of the policy's finding ids (blocking rows outside the set are the backlogged residuals and are permitted; a blocking row inside the set still refuses); under this branch the landed `verdict` sub-check does not apply - the sidecar's verdict may be `no` precisely because the out-of-set residuals are staged - the membership rule replaces the zero-blocking rule; `residual_policy.finding_ids` are integers matching the version-1 sidecar's integer finding ids; add four fixture cases to `ArchiveGatePreArchiveTest` in `scripts/test_execute_plan_runtime.py`: `test_accepts_residual_policy_exit` (a focused-round sidecar with verdict `no` and one out-of-set blocking row, plus the policy input, archives), the same sidecar without the policy input still refuses, a sidecar whose blocking row id is inside the policy's finding ids refuses, and a policy whose recorded-at postdates the sidecar's round refuses; document the input field and OR-branch in `agents/skills/execute-plan/runtime-contract.md`'s staged-terminal section [class: REPOSITORY_TEST]
- [x] In execute-plan SKILL.md Phase 4 step 1, extend the pre-archive payload enumeration with the optional `residual_policy` field (finding ids, grant source, recorded-at), so an orchestrator following the skill verbatim supplies the policy the predicate's OR-branch consumes [class: IMPLEMENTATION_REQUIRED]
- [x] Composition note in place of a P9 plan-document edit: P9's execution is in flight (its driver predicate `_pre_archive_gate` has landed), so this plan amends the landed driver code and the runtime contract and never the live P9 plan document (a digest edit would wedge the running execution's Step 0.5 gate); this plan's execution Phase 0 drift check verifies the OR-branch against P9's fully landed state [class: IMPLEMENTATION_REQUIRED]
- [x] In review-loop's Exit criteria, add the mirror line: standalone loops share the same `residual-acceptance exit` shape (named fix set, one focused targeted round, out-of-set new blocking findings to durable backlog items, policy recorded before the verification round) [class: IMPLEMENTATION_REQUIRED]
- [x] In the exit-report duty, add the named-set diff: the orchestrator diffs the address pass's changed files against the named set and routes any out-of-set change back to a normal fresh round instead of the exit [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED then GREEN: `python3 scripts/test_execute_plan_runtime.py` - the new `test_accepts_residual_policy_exit` and sibling refusal cases fail before implementation and pass after; the existing suite stays green [class: IMPLEMENTATION_REQUIRED]
- [x] Run the section 5 obligation probes → expect GREEN; the full block runs at Task 5 [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skills: sanctioned residual-acceptance exit with gate reconciliation and P9 composition (P11 origin D)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Full validation and composition sweep

Files:
- `docs/plans/2026-09-18-execute-plan-orchestration-authority-loop-bounds-release-gates.md` *(this plan)*

- [x] Extract the Validation Commands bash block from this plan file, run `bash -n` on it, and execute it → expect the full block GREEN (selftest, all obligation probes, hygiene sweeps) [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the composition ordering note survives in the plan header and Assumptions (execution sequenced after P9; Phase 0 drift re-baseline of the shared sections) [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `plans: P11 orchestration plan validation sweep` [class: IMPLEMENTATION_REQUIRED]
