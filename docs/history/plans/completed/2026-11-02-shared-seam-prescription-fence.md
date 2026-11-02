# Plan: Shared-seam prescription fence for sibling open plans

Backlog origin: docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-shared-seam-prescription-fence-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.5h total, largest task 1.0h
Authoring claim: 2026-10-06-staging-preflight-done-readiness-shared-payload-span.md (session sess_6e8a47a5-54c0-42a4-8974-cf1f5b55883c)

## Terms

- Shared-file seam: two open plans whose `Files:` lists name the same file section and both prescribe edits there.
- Sibling open plan: another plan at the plans root (not this plan, not archived, not completed).
- Quoted task span: the exact existing text a plan task quotes to locate its edit target.
- Seam disposition: the recorded choice for a seam: re-anchor on the sibling's landed form, declare an execution dependency, or drop the duplicated span as already covered.
- Execution-order note: the one-line note beside a correction record naming the sibling plan whose execution moved the anchor.
- Corrections chain: the plans skill's classified plan-edit route (delta classifier, correction rows, digest re-bind).
- Seam rule: the plans skill's split rule governing shared-file sets and header execution dependencies under the parked-dependency machinery.
- Companion pin: a pin entry the pins suite checks beside a provenance comment naming the plan and task that introduced the pinned span.
- Operative span: the exact new text a task adds to a pinned skill file, which the companion pin protects against drift.
- Provenance comment: the comment line beside a companion pin naming its plan and task.
- Preflight paragraph: the execute-plan Phase 0 step that runs `scripts/plan_readiness.py --pre-round` and routes a stale or malformed plan to repair before implementation.

## Why

Two certified plans once prescribed replacing the same sentence in the same skill file, and the second executor met a stale anchor: the edit failed, and the run burned a mid-execution correction round (witnessed 2026-10-06, backlog row 2026-10-06-staging-preflight-done-readiness-shared-payload-span.md, including its Update note). Nothing at authoring time or at execution start makes such an overlap visible before the second run starts, so every new overlap re-creates the same wasted round.

## Gist & Examples

TLDR: plans prescribing edits over the same file section as a sibling open plan now carry an explicit seam disposition, and a missed seam leaves a filed execution-order note, so the second executor never meets a stale anchor unprepared; driving force: efficiency (a witnessed correction round is the cost being removed).

Before (today): plan A and plan B are both certified; each task quotes the same sentence in one skill file for replacement. A executes and lands its replacement. B's executor starts, the quoted sentence is gone, the edit fails, and B consumes a correction round to re-anchor on A's landed form.

After (this plan): while B was authored, the seam with A was already adjudicated: B either declared an execution dependency on A under the Seam rule (so B executes after A lands, with its spans re-authored against A's form), or dropped the duplicated span as already covered. If an overlap still slips through, B's executor files the execution-order note naming A and the landing commit, so the ordering is explicit for the next consumer of that seam.

Edge cases: the sibling lands between this plan's certification and its execution start (the residual window; the execution-order note convention covers it); three plans share one seam (the adjudication repeats per pair and the dependency chain orders them); the sibling is archived before this plan starts (the re-anchor disposition applies against the archived plan's landed form).

## Outcome

Shared-seam overlaps between sibling open plans surface at authoring time with a recorded disposition, and overlaps that still reach execution leave an auditable execution-order note.

- The next overlap is adjudicated before certification instead of at the second executor's failure.
- A missed overlap still produces an explicit ordering record naming the sibling plan and its landing commit.
- No new gate, validator, or scheduler state is added; the fence is advisory skill text.

Gate delta: none. Both duties are advisory skill text: one authoring-time adjudication step and one execution-time note convention. No gate, fence, refusal class, protocol layer, schema field, or dispatch-pausing condition is added, and no existing refusal, check, or field is removed. The advisory posture is deliberate: the witnessed incident is one, so the machinery admission protocol prices a blocking gate as unaffordable here.

## Assumptions

- assume the adjudication lives in the plans skill's pre-finalization structural failure modes list; basis: that list is the authoring boundary already checked before finalizing, so the step runs without new machinery or a new phase.
- assume the execution-order note rides the corrections chain, the repair route the execute-plan preflight paragraph names for a stale or malformed plan; basis: the witnessed stale anchor surfaced mid-execution when a worker's span edit no longer matched, and the corrections chain is the route that re-binds the amended plan.
- assume both edited files stay pinned and each new operative span gains a companion pin in the same edit; basis: both files are pinned by `scripts/check_maintenance_pins.sh` and the suite's companion-pin convention pins new operative spans beside a provenance comment.
- Decision receipts: seam-fence arm adjudication resolved to the no-new-machinery default (authoring adjudication step plus execution-order note, the backlog row's arms (a) and (c)), the landing-closeout shared-span scan (arm (b)) declined as unpriced machinery for one witnessed incident; basis: the row's own adjudication guidance and the repository machinery admission protocol; date 2026-11-02; affected sections Why, Tasks.

Decision points requiring a grill: seam-fence arm adjudication: authoring adjudication step plus execution-order note adopted, landing-closeout shared-span scan declined as unpriced machinery, source backlog row adjudication guidance plus machinery admission protocol, 2026-11-02, affected sections Why and Tasks.

## Standing constraints

- Both edited files are pinned by `scripts/check_maintenance_pins.sh`: an edit that moves or breaks a pinned span updates that span's mirror inside `scripts/check_maintenance_pins.sh` in the same commit, and each new operative span this plan adds gains its companion pin in the same edit.
- Skill text stays tool-agnostic and imperative, matching the surrounding file's density and idiom.

## Evaluation Criteria

- Correctness: both edited locations are real, verified by grep before certification (the structural failure modes list in the plans skill; the preflight paragraph in execute-plan).
- Consistency: the new terms each have one definition home; greping the two files shows no contradicting seam wording against the Seam rule or the corrections chain.
- Gates: `bash scripts/check_maintenance_pins.sh` exits 0, `bash scripts/scan-public-hygiene.sh` exits 0, and the added lines carry no em dash.

Done when: both edits are committed on the run branch, the three gates above are green, and the branch diff contains exactly the Review Scope paths plus this plan document.

Ship when: none (repository-internal process text; no external release surface).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `scripts/check_maintenance_pins.sh` (Task 1, Task 2: companion-pin additions only)

**Tests:**
- none (the duties are verified by the pins suite and the greps in Validation Commands, not by a new test file)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. Inside `scripts/check_maintenance_pins.sh`, only the companion-pin additions Tasks 1 and 2 prescribe and a pin-mirror update demanded by a moved pinned span are in scope; any other change there is out of scope.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/prompt-templates.md`; reason: the historical seam; its original spans no longer exist after the template split, and no task edits it.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
```

### Task 1: Shared-seam adjudication step in the plans skill

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pin for the new span)

Edit target: the structural failure modes list introduced by "Then verify these structural failure modes and fix them in the plan", verified at authoring time by grep.

- [ ] Add one "Shared-seam overlap" bullet to that list: given a plan whose `Files:` paths overlap a sibling open plan's `Files:` paths on the same file section, expects the authoring session to adjudicate the seam before finalizing and to record the disposition in `## Assumptions` naming the sibling plan [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet states the three dispositions: re-anchor on the sibling's landed form when the sibling already executed; declare the header execution dependency under the Seam rule when both plans are open; drop the duplicated span as already covered when the sibling's landed form already delivers the edit [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet states the advisory posture: the adjudication adds no gate, validator, or refusal; an unadjudicated seam is a review finding, never a mechanical stop [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a companion pin in `scripts/check_maintenance_pins.sh` for the new operative span (the shared-seam overlap bullet), aiming the needle beside a provenance comment, and run `bash scripts/check_maintenance_pins.sh` expecting exit 0 [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `bash scripts/check_maintenance_pins.sh` after the edit, expect exit 0, and update the pin mirror in the same commit if a pinned span moved [class: REPOSITORY_TEST]
- [ ] Commit: `plans: add shared-seam adjudication step to plan authoring` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Execution-order note on sibling-moved stale spans

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pin for the new span)

Edit target: the preflight paragraph carrying "A stale or malformed plan stops before implementation", verified at authoring time by grep.

- [ ] Extend that paragraph's routing with the digest-fresh stale-span case: given a plan whose bytes still match its certified digest but whose task's quoted span no longer exists at execution time because a sibling plan's execution landed first, expects the executor to take the corrections chain and to record the execution-order note beside the correction record [class: IMPLEMENTATION_REQUIRED]
- [ ] The note's filed form is stated in the paragraph: `Execution-order note: anchor moved by <sibling-plan-slug> landing <commit>`, one line in the run's correction record [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a companion pin in `scripts/check_maintenance_pins.sh` for the new operative span (the execution-order note sentence), aiming the needle beside a provenance comment, and run `bash scripts/check_maintenance_pins.sh` expecting exit 0 [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `bash scripts/check_maintenance_pins.sh` after the edit, expect exit 0, and update the pin mirror in the same commit if a pinned span moved [class: REPOSITORY_TEST]
- [ ] Commit: `execute-plan: file execution-order note when a sibling landing moves the anchor` [class: IMPLEMENTATION_REQUIRED]
