# Plan: consumer-corpus review and authoring doors (typed catalogs, producer inventories, helper retargeting, ops framing)

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-23-phase3-review-vs-external-pr-bot-gaps.md`
- `docs/history/backlog/2026-09-25-execute-plan-door-change-owning-it-green.md`
- `docs/history/backlog/2026-09-25-plans-domain-door-producer-inventory.md`
- `docs/history/backlog/2026-09-25-plans-ops-framing-and-meta-javadoc.md`
- `docs/history/backlog/2026-09-25-review-typed-catalog-enumeration-door.md`

Driving force: efficiency (secondary: code-quality)
Force note: the five origins declare reliability / lost-work prevention, which is outside the closed force taxonomy; efficiency is the taxonomic carrier (prevented rework across consumer PR cycles), and the shared-skill consumer-urgency rule keeps this family eligible regardless of the personal profile's formal-hardening deferral.

## Terms

- **Domain door**: a fail-closed validation added on a mutator path that rejects an illegal caller or state (addressable position guard, typed enqueue, catalog key-set restriction, status or capacity gate).
- **Producer**: any production caller or shared test helper that reaches the same mutator a domain door guards (bootstrap enqueue, scheduler, capacity, recovery, shared IT helper).
- **Owning integration class**: the project-local integration suite that exercises the guarded module end to end (Failsafe or `*IT` naming per the consumer repo's convention), as opposed to the unit suite alone.
- **Delivery-slice meta**: class-level javadoc or comment prose that only records plan-slice identities (P0.n style), ticket keys, or "this PR adds" narrative instead of behavior.
- **Pattern id**: a `<lens>#<kebab-name>` registration declared inside a review-agents lens file, cited by findings, residual grants, and panel signals.

## Assumptions

- assume skill-text amendments plus one new test file only; no runtime script behavior changes in this repository; basis: all five origins scope `agents/skills/` files and a review-agent selftest.
- assume the golden-eval takes the review-agent selftest form (pattern registry with required-action pins over canned fixture snippets), not an LLM-driven eval; basis: origin 1 remaining work 1 sanctions "golden-eval (or review-agent selftest)" and the repo has no LLM eval harness.
- assume the optional java-spring overlay examples (origin 1 remaining work 3) are deferred, not implemented; basis: the origin marks them optional; carried under **Ship when**.
- assume `agents/skills/receiving-review/SKILL.md` needs no edit in this plan (its Fix-risk invariant closure is recorded as already updated by origin 1); basis: origin 1 "What landed this session" and the cross-link task below only references it from execute-plan.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the shared skill corpus gains four consumer-facing doors (typed-catalog enumeration, helper retargeting after a door change, producer inventories at plan-authoring time, ops-ownership framing plus a delivery-slice-meta ban), so consumer repos stop losing work to external bot finds that internal reviews never stage.

**Before (today):** a consumer repo plan adds a fail-closed catalog door. The plan lists the production call site and one happy-path test. Shared Failsafe helpers still call the wider all-keys enumeration helper; the implement worker changes production only, Surefire stays green, the task is marked done, and the owning Failsafe class fails in a later session or an external bot opens bypass threads after Phase 3 exits. Separately, a scheduler class javadoc describes an app-owned retention job as DBA work because the schema is DBA-owned, and class comments restate P0.n slice ids; no lens stages either defect.

**After (this plan):** the authoring rule (plans Validation rule 38) forces a producer inventory with per-family RED canaries and the owning integration class in Validation Commands for every door task. The execute-plan Step 1.2 exit criteria require the helper grep, the same-change-set retarget, and the owning-class green run for door-change tasks, and treat a missing owning-class run as incomplete evidence, not success. Three new lens patterns (`quality#typed-catalog-enumeration-door`, `testing#helper-path-retarget-after-door`, `documentation#prose-delivery-slice-meta`) plus a panel signal make Phase 3 and Step 1.2b stage these misses before archive, and the Residual-acceptance exit refuses blanket deferral grants for the widened lost-work family.

Edge cases motivating the design: a plan may explicitly document a wider key set (the catalog pattern permits it when the plan says so); a helper whose retarget is genuinely out of scope must leave through an explicit OUT deferral with a backlog path, never silently; an app-owned cleanup job differs from DBA DDL ownership even when both touch the same table.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each new pattern id is declared exactly once in its lens file and carries the origin's required worker actions (name both APIs and cite one illegal key for the catalog door; helper grep, same-change-set retarget, owning-class green for the testing door; behavior-facing-only class comments for the documentation door), verified by `scripts/test_review_agent_doors.py`.
- maintainability: the new selftest is the single registry that gates all three pattern ids, and the workspace review-agents rule (AGENTS.md) names it as a standing gate beside the portability checker, so future lens edits that drop a required action fail mechanically on the next review-agents change.
- compatibility: the pins suite, the review-agent portability checker, and the shared-body runtime-neutrality test all pass, so no pinned span, stack-neutral catalog, or shared-body forbidden term regressed.

**Done when:**
- `scripts/test_review_agent_doors.py` passes (registry, required-action, fixture-annotation, and exactly-once declarations).
- `python3 scripts/check_review_agent_portability.py` exits 0.
- The shared-body runtime-neutrality test passes over the touched shared files.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- The workspace review-agents rule in `AGENTS.md` names both the portability checker and the door selftest as required gates.
- The Residual-acceptance exit row names the widened lost-work family; the Step 1.2 door-change exit criteria and the plans rule 38 text exist where the tasks prescribe them.

**Ship when:**
- Consumer repos pick the corpus up on their next vendored sync of `agents/skills/`; no in-repo evidence beyond the gates above is possible.
- The optional java-spring overlay examples (origin 1 remaining work 3) and any LLM-driven golden-eval upgrade remain deferred work; they need fixture repositories this plan does not create.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `AGENTS.md` (repo root; the Testing Guidelines review-agents rule)
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

**Tests:**
- `scripts/test_review_agent_doors.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/receiving-review/SKILL.md`; origin 1 records its Fix-risk invariant closure as already landed, so no edit belongs to this plan.
- `docs/history/backlog/deferred/2026-09-18-review-agents-miss-dual-surface-parity-conversion-floors-comment-inventories.md`; the deferred dual-surface bundle stays deferred; only its catalog slice is promoted here through the typed-catalog origin.
- Any java-spring overlay example files; deferred per Assumptions.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1

# New door-pattern registry selftest (Task 1 expects RED; Tasks 2-4 flip it GREEN)
python3 scripts/test_review_agent_doors.py || { echo "FAIL: door selftest"; exit 1; }

# Shared review-agents catalogs stay stack-neutral (repo rule for any review-agents touch)
python3 scripts/check_review_agent_portability.py || { echo "FAIL: portability"; exit 1; }

# Shared skill bodies stay runtime-neutral (plans SKILL.md, execute-plan SKILL.md, subagent-prompts.md are edited here)
python3 scripts/test_execute_plan_runtime.py -k "*shared_skill_bodies*" || { echo "FAIL: shared-body neutrality"; exit 1; }

# No pinned span in the touched skill files broke
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }
```

### Task 1: door-pattern registry selftest (RED first)

Files:
- `scripts/test_review_agent_doors.py` *(new)*

- [x] `ReviewAgentDoorsTest#test_typed_catalog_enumeration_door_declared`; given `agents/skills/review-agents/quality.md`, expects exactly one `Pattern: `quality#typed-catalog-enumeration-door`` declaration whose surrounding pattern text requires (a) the key source of a materialize / floor / enqueue-from-catalog loop to be the typed or published definition set rather than a wider all-keys helper unless the plan explicitly documents the wider set, (b) the finding body to name both enumeration APIs, and (c) the finding body to cite one illegal key the wide API admits and the typed API excludes [class: REPOSITORY_TEST]
- [x] `ReviewAgentDoorsTest#test_helper_path_retarget_after_door_declared`; given `agents/skills/review-agents/testing.md`, expects exactly one `testing#helper-path-retarget-after-door` pattern declaration whose text requires (a) a grep of test helpers for the newly banned path, (b) same-change-set helper retarget or update, and (c) a green run of the owning integration class, not only the unit suite [class: REPOSITORY_TEST]
- [x] `ReviewAgentDoorsTest#test_delivery_slice_meta_declared`; given `agents/skills/review-agents/documentation.md`, expects exactly one `documentation#prose-delivery-slice-meta` pattern declaration whose text classifies a class-level comment carrying only plan-slice ids, ticket keys, or add-narrative as a finding requiring behavior-facing prose [class: REPOSITORY_TEST]
- [x] `ReviewAgentDoorsTest#test_panel_signal_names_both_doors`; given `agents/skills/review-agents/review-panel-selection.md`, expects the catalog / helper change signal to name both `quality#typed-catalog-enumeration-door` and `testing#helper-path-retarget-after-door` [class: REPOSITORY_TEST]
- [x] `ReviewAgentDoorsTest#test_fixture_annotations_cover_witnessed_shapes`; given three canned fixture snippets embedded in the test (a materialize loop enumerating an all-keys helper where the typed definitions set is required, a class javadoc whose only content is a P0.n slice id plus ticket key, and a shared test helper calling a path a new production door rejects), expects each fixture's distinctive tokens (for example `all-keys`, `typed or published definition set`, `P0.n`, `helper`) to appear in the corresponding pattern text, so each witnessed miss shape is covered by the instruction that must stage it [class: REPOSITORY_TEST]
- [x] `ReviewAgentDoorsTest#test_concurrency_lost_work_fixtures_characterized`; given two canned fixture snippets embedded in the test (an ungated multi-row cleanup CTE that deletes without an update-generation fence, and a worker permit acquired without a finally release), expects `agents/skills/review-agents/concurrency.md` to declare `concurrency#cleanup-gated-on-update` and `concurrency#permit-finally` and to name each fixture's distinctive mechanism (the cleanup update fence; the finally release), characterizing origin 1's fixture ask against the already-landed concurrency patterns [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_review_agent_doors.py` (the three declaration tests, the panel-signal test, and `test_fixture_annotations_cover_witnessed_shapes` fail because the pattern ids do not exist yet; `test_concurrency_lost_work_fixtures_characterized` passes at this task point because its patterns pre-exist on the base branch; the failure output names each missing id) [class: REPOSITORY_TEST]
- [x] Commit: `test: add review-agent door-pattern registry selftest (RED)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: catalog enumeration door and panel signal (flips the catalog tests GREEN)

Files:
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/review-panel-selection.md`

- [x] Append to the quality lens checklist (same numbered-item shape as the existing `quality#addressable-domain-door` entry): when a loop materializes, floors, or enqueues from a catalog, require the key source to be the typed or published definition set, never a wider all-keys helper, unless the plan explicitly documents the wider set; the finding body names both enumeration APIs and cites one illegal key the wide API admits and the typed API excludes. End the item with `Pattern: `quality#typed-catalog-enumeration-door`.` [class: IMPLEMENTATION_REQUIRED]
- [x] Add one signal row or bullet to the review-panel-selection Risk-signal floor section: when the diff changes a materialize / floor / catalog loop or pairs a production guard change with shared test helper edits, the testing and quality workers must run the catalog-enumeration and helper-retarget checks, naming both pattern ids [class: IMPLEMENTATION_REQUIRED]
- [x] Fix the pre-existing portability violation in the quality lens MyBatis section intro (the stack-naming word in "a mapped Java `void` return", `quality.md` near line 122): reword to the stack-neutral "a mapped `void` return" so `python3 scripts/check_review_agent_portability.py` exits 0; the violation is committed state on the base branch and this plan's Done-when gate owns it [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN (partial): `python3 scripts/test_review_agent_doors.py` (`test_typed_catalog_enumeration_door_declared` and `test_panel_signal_names_both_doors` pass; the helper-retarget and delivery-slice declaration tests, and `test_fixture_annotations_cover_witnessed_shapes` (its testing and documentation tokens), still fail; `test_concurrency_lost_work_fixtures_characterized` passes, its patterns pre-exist on the base branch) and `python3 scripts/check_review_agent_portability.py` exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: quality typed-catalog-enumeration-door pattern and panel signal` [class: IMPLEMENTATION_REQUIRED]

### Task 3: helper-retarget door in the testing lens (flips the retarget test GREEN)

Files:
- `agents/skills/review-agents/testing.md`

- [x] Add to the testing lens closing numbered verification list (the numbered items before the Changed-code family inventory section): when the task diff adds or tightens a fail-closed door on a mutator, require (a) a grep of test helpers for the newly banned path, (b) same-change-set retarget or update of every helper still calling it, and (c) a green run of the owning integration class for the guarded module, not only the unit suite; stage the pattern when helpers keep the rejected path while the unit suite is green. End the item with `Pattern: `testing#helper-path-retarget-after-door`.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN (partial): `python3 scripts/test_review_agent_doors.py` (the retarget declaration test passes; the documentation declaration test and `test_fixture_annotations_cover_witnessed_shapes` (its documentation token) still fail; the catalog, panel-signal, and concurrency tests pass) [class: REPOSITORY_TEST]
- [x] Commit: `feat: testing helper-path-retarget-after-door pattern` [class: IMPLEMENTATION_REQUIRED]

### Task 4: delivery-slice-meta ban in the documentation lens (flips the suite GREEN)

Files:
- `agents/skills/review-agents/documentation.md`

- [x] Add to the documentation lens prose-defect paragraph (the paragraph near documentation.md line 95 that declares the existing prose- family ids, missing-example-replay and prose-example-conflict among them): a class-level comment whose only content is plan-slice identity (P0.n style), a ticket key, or "this PR adds" narrative is a finding (Medium when it is the only class comment); require behavior-facing prose or deletion. Do not conflate with the deferred relocatable identifier-inventory class. End the item with the `documentation#prose-delivery-slice-meta` pattern id [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_review_agent_doors.py` (the full suite passes at this task point, including `test_delivery_slice_meta_declared` and `test_fixture_annotations_cover_witnessed_shapes`) [class: REPOSITORY_TEST]
- [x] Commit: `feat: documentation prose-delivery-slice-meta pattern` [class: IMPLEMENTATION_REQUIRED]

### Task 5: plans authoring rule 38 and ops-ownership grill case

Files:
- `agents/skills/plans/SKILL.md`

- [x] Append rule 38 to the Validation Commands (authoring rules) list: when a task introduces or tightens a fail-closed domain door on a mutator, the plan must carry a producer inventory listing every production caller and shared test helper that reaches the guarded mutator, each with a Files entry and a given/expects RED canary proving the door rejects that path, or an explicit out-of-scope deferral naming the backlog item that carries it; the task's Validation Commands or interim gate must run the owning integration class for the guarded module, not only the unit suite, whenever the door can reject helper paths; a door task without a producer inventory is a blocking plan defect [class: IMPLEMENTATION_REQUIRED]
- [x] Append case 8 to the Phase 1 confidence-gate regression cases: a feature whose scope mentions retention, cleanup, or purge of rows or history keeps the ops-ownership question (app-owned scheduled job vs DBA one-shot vs out-of-process job) low-confidence unless the ticket names the owner; schema ownership alone never defaults the answer to DBA [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep the two prescribed insertions' exact text against the shared-body forbidden-term gate before certification (the plans SKILL.md is a gated shared file) and reword rather than amend the gate; expect no hit for this plan's wording [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (no pinned plans span moved) and `python3 scripts/test_execute_plan_runtime.py -k "*shared_skill_bodies*"` [class: REPOSITORY_TEST]
- [x] Commit: `feat: plans rule 38 producer inventory and ops-ownership grill case` [class: IMPLEMENTATION_REQUIRED]

### Task 6: execute-plan door-change exit criteria, residual widening, Hard Gate 23 cross-link

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

- [x] Extend the Step 1.2 exit criteria (the per-task verification gate before checkbox flip): when the task diff adds or tightens a fail-closed door on a mutator, the exit criteria additionally require the helper grep for the banned path, the same-change-set helper retarget in the task's Files set, and a green run of the owning integration class; when the plan's Validation Commands omit the owning class for a door-change task, the orchestrator records incomplete evidence (the done launch is blocked as a malformed receipt), never success [class: IMPLEMENTATION_REQUIRED]
- [x] Widen the Residual-acceptance exit row's blanket-deferral prohibition to the full lost-work family: `concurrency#*` (which subsumes the currently enumerated cleanup-gated-on-update, permit-finally, and terminal-not-partial entries), `quality#addressable-domain-door`, `quality#port-api-truth`, `quality#typed-catalog-enumeration-door`, and `implementation#typed-enqueue-door`; the family stays fix-or-block unless the user names each finding id in the residual set [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Hard Gate 23 entry with the cross-link sentence: fix-regeneration thrash after external review-bot comments routes through the closed pattern doors in the lens files and `receiving-review` **Fix-risk triage when fixes regenerate findings** (its "Invariant closure before more microfixes" paragraph) before further microfix rounds [class: IMPLEMENTATION_REQUIRED]
- [x] Add the door-change checklist line to the Implement Task template in `subagent-prompts.md`: door on a mutator in the diff implies helper grep, same-change-set helper retarget, and owning integration class green in the task's evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py -k "*shared_skill_bodies*"` and `bash scripts/check_maintenance_pins.sh` (both edited execute-plan files are shared-body gated; no pinned span moved) [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan door-change exit criteria and residual family widening` [class: IMPLEMENTATION_REQUIRED]

### Task 7: standing selftest caller beside the portability rule

Files:
- `AGENTS.md`

- [x] Extend the Testing Guidelines rule that names `python3 scripts/check_review_agent_portability.py` for `agents/skills/review-agents/` changes so the same sentence also requires `python3 scripts/test_review_agent_doors.py` (exit 0 required), keeping the door-pattern registry a standing post-landing gate instead of a one-shot certification check [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `grep -c "test_review_agent_doors" AGENTS.md` reports 1 or more, and both named commands exit 0 against the current tree [class: REPOSITORY_TEST]
- [x] Commit: `docs: wire door-pattern selftest into the review-agents testing rule` [class: IMPLEMENTATION_REQUIRED]

### Task 8: full gate run over the final tree

Files: none (verification only)

- [x] Run the complete Validation Commands block in order and expect every command green on the final tree [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_review_agent_doors.py` reports all registry, required-action, fixture-annotation, and exactly-once tests passing [class: REPOSITORY_TEST]

## Execution record

Executed 2026-09-25 in worktree `ai-playbook-exec-consumer-corpus` off local main e054ac72. Deviation: Task 1's fixture-token assertions normalize whitespace in the pattern window (the lens files line-wrap pattern prose), so the catalog fixture token "typed or published definition set" matches across the wrap; selftest committed RED first per plan. Task 2's portability fix reworded "a mapped Java `void` return" to "a mapped `void` return" as prescribed. Full Validation Commands block exit 0 on the final tree (door selftest 6/6, portability, shared-body neutrality, pins, plus hygiene exit 0).
