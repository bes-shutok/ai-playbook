# Plan: Em-dash fallback enumeration canary and review-worker git discipline

Backlog origin: docs/history/backlog/2026-09-28-emdash-plan-authoring-residuals.md
Driving force: code-quality + efficiency
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-emdash-residuals-canary-and-review-discipline-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Close the three residuals captured at the em-dash gate plan's r4 exit: a canary that witnesses the done-gate fallback's complete-stdout enumeration guarantee, a Validation-preamble record obligation covering all three authoring-time gate outcomes, and a standing git-mutation prohibition for review workers.

- A fifth canary proves the done-gate fallback enumerates every hitting file, so an implementation reading the failure message's ten-row tail instead of the probe's complete stdout can never pass the suite.
- The plans skill requires the plan's Validation preamble to record the pre-round structural gate outcome, the RED-today executions, and the authoring-time mechanical audit, so a structural-clean pre-round pass is evidenced rather than asserted.
- Review workers are forbidden from mutating the reviewed repository's git state, closing the witnessed incident class (a review worker briefly landed a commit on an authoring branch during a pins-suite simulation).

## Assumptions

- assume the fifth canary lands as a characterization test gated on the em-dash plan's fallback existing, not as a RED driver in this plan; basis: the fallback is implemented by the earlier-landed plan docs/history/plans/2026-09-28-em-dash-whole-file-gate-added-lines-selection.md Task 2, and a RED canary landing before its implementation would leave the lib suite failing between the two executions; the alphabetical and landing order both sequence the em-dash plan first, and the task carries an explicit ordering-violation stop for the residual case.
- assume the git-discipline sentence lands in two homes (the review-plan skill's worker-constraint paragraph and the plans skill's review-round launch template) because the two surfaces bind different readers: workers load review-plan instructions, while dispatching sessions assemble prompts from the plans template; basis: the witnessed incident came from a worker following the template prompt with no prohibition available in either surface.
Decision points requiring a grill: canary placement = characterization test inside this plan over a RED driver inside the em-dash plan; source: r4 finding F1 consequence analysis plus suite-green-between-executions invariant, 2026-09-28, Assumptions and Task 1; git-discipline homes = review-plan worker paragraph plus plans launch template; source: r4 incident disclosure plus the two-reader split, 2026-09-28, Task 3

## Gist & Examples

TLDR: a fifth canary pins the done-gate fallback's full enumeration, the plans skill requires all three authoring-time gate records in the Validation preamble, and review workers gain an explicit git-mutation prohibition, because r4 witnessed a worker landing a commit and an implementation that could silently pass on a ten-row tail.

**Before (today).** The em-dash plan's Task 2 prescribes the fallback partition input as the touched probe's complete stdout precisely because the current failure message carries only the last ten rows; no canary exercises more than ten hitting files, so a tail-reading implementation passes all four prescribed canaries. Rule 29 requires recording only the pre-round gate outcome in the Validation preamble, leaving the rule 19 RED-today executions and the rule 22 mechanical audit as unrecorded conventions. And a review worker's prompt says the plan file is read-only but nothing forbids git mutations: the r4 worker ran init, add, and commit inside a temp copy whose .git was a worktree pointer file and briefly landed a commit on the authoring branch.

**After (this plan).** `test_em_dash_fallback_many_hits_full_enumeration` builds a fixture with eleven tracked prose files each carrying one committed dash on an unchanged line plus clean working-tree additions, and expects rc 0 with eleven baseline rows in the gate message; an implementation reading a ten-row tail fails it. Rule 29's record sentence names all three authoring-time outcomes. The review-plan worker paragraph and the plans launch template both carry the prohibition sentence: no commits, branches, refs, stashes, or worktree operations in the reviewed repository; simulation fixtures live outside any worktree-linked .git directory.

**Edge cases.** This plan executing before the em-dash plan's implementation is the ordering violation: Task 1's first gate then fails, the task stops, and the report names the ordering reason; no partial canary lands. The shared-body forbidden-term gate over plans/SKILL.md constrains the prescribed sentences: all insertions are runtime-neutral and the prechecks below execute the gate before certification.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the fifth canary fails any partition input narrower than the probe's complete stdout (eleven rows witnessed in the message, ten-row tail under-enumerates).
- consistency: the two git-discipline sentences and the rule 29 record sentence are pinned by dedicated fail-closed greps.
- compatibility: the shared-body forbidden-term gate and the em-dash plan's G5 canary-name loop stay green after the edits.

**Done when:**
- The fifth canary exists, is green via the test venv, and the full lib suite passes.
- Rule 29's record sentence names the rule 19 and rule 22 records.
- Both git-discipline sentences are present at their anchors.
- All Validation Commands below exit 0.

**Ship when:**
- None as a release gate; all criteria are repository-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` *(one new canary plus the fixture helper it needs; existing tests and the four sibling canaries are frozen)*

**Production code:**
- `agents/skills/plans/SKILL.md` (only rule 29's record sentence and the sub-agent template's git-discipline sentence; all other rules and lines are frozen)
- `agents/skills/review-plan/SKILL.md` (only the worker-constraint paragraph's git-discipline sentence; all other lines are frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py`; reason: the fallback implementation belongs to the em-dash plan; this plan only witnesses it.
- `agents/skills/review-agents/` files; reason: the worker-constraint anchor lives in review-plan/SKILL.md and the launch template in plans/SKILL.md; the panel-selection catalogs are untouched.

## Validation Commands

Stage note: the authoring-time records this plan's own rule 29 amendment requires are recorded here: the pre-round structural gate ran clean before round 1 (pre-round exit 0), the RED-today executions ran against current bytes with measured outcomes (G1 RED-today: the five canary names are absent from the test file today; G2, G2b, and the Task 2 tail pin RED-today: the pinned spans are absent from their targets today; the Task 1 ordering gate RED-today: the four sibling canary names are absent from the test file today; G3 and G3b RED-today: both adjacency spans are absent from their targets today; G4 green: 1 passed, 426 deselected; G5 exit 0), and the mechanical audit (pinned spans once each, bash -n over this block) ran before round 1. The venv python resolves the test venv the lib suite uses.

```bash
# G1: the fifth canary exists and the full lib suite is green (the em-dash
# plan's fallback must already be implemented for this to pass).
for canary in test_em_dash_fallback_preexisting_tracked_passes test_em_dash_fallback_untracked_still_fails test_em_dash_fallback_dirty_added_lines_still_fails test_em_dash_fallback_mixed_hits_fail_untracked test_em_dash_fallback_many_hits_full_enumeration; do grep -qF "$canary" scripts/test_done_sweep_gates_lib.py || { echo "G1 fail: $canary missing"; exit 1; }; done
"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_done_sweep_gates_lib.py -q

# G2: rule 29 records all three authoring-time outcomes.
grep -qF "rule 19 RED-today execution evidence" agents/skills/plans/SKILL.md || { echo "G2 fail: rule 19 record missing"; exit 1; }
grep -qF "rule 22 authoring-time mechanical audit" agents/skills/plans/SKILL.md || { echo "G2b fail: rule 22 record missing"; exit 1; }

# G3: both git-discipline sentences present AT THEIR ANCHORS (adjacency pins;
# presence anywhere is not enough: the plans-template sentence must sit inside
# the fenced sub-agent template for dispatching sessions to assemble it).
grep -qF "Workers must not launch children. Workers must not mutate the reviewed repository's git state: no commits, branches, refs, stashes, or worktree operations; simulation fixtures live outside any worktree-linked .git directory. The \`risk\` worker applies" agents/skills/review-plan/SKILL.md || { echo "G3 fail: worker prohibition not at its anchor"; exit 1; }
grep -qF "before treating the round as failed. Git discipline (required in every review-round launch): no commits, branches, refs, stashes, or worktree operations in the reviewed repository" agents/skills/plans/SKILL.md || { echo "G3b fail: template prohibition not adjacent to the anti-idle paragraph"; exit 1; }

# G4: the shared-body forbidden-term gate stays green over the amended plans skill.
"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_execute_plan_runtime.py -q -k shared_skill_bodies_remain_runtime_neutral

# G5: the run introduced no em dashes anywhere.
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"
```

### Task 1: Fifth enumeration canary for the done-gate fallback

Files:
- `scripts/test_done_sweep_gates_lib.py`

- [ ] Run the ordering gate: `for c in test_em_dash_fallback_preexisting_tracked_passes test_em_dash_fallback_untracked_still_fails test_em_dash_fallback_dirty_added_lines_still_fails test_em_dash_fallback_mixed_hits_fail_untracked; do grep -qF "$c" scripts/test_done_sweep_gates_lib.py || exit 1; done` → expect all four found; the em-dash plan prescribes these canary names byte-exact in this same test file, so their presence witnesses its Task 2 executed; any missing name means the em-dash plan has not executed: stop this task, report the ordering violation, and mark nothing (never anchor this gate on lib-source literals: the lib invokes scanners through argv lists, so no prescribed lib byte carries a CLI-shaped literal) [class: REPOSITORY_TEST]
- [ ] Canary `test_em_dash_fallback_many_hits_full_enumeration`; given a fixture repo with eleven tracked prose files each carrying one committed em dash on an unchanged line while the working tree adds only clean lines, expects the em-dash-scan gate returns rc 0 with eleven `pre-existing (known-violation baseline): <path>:<line>` rows in the message, one per hitting file; construct fixture dash bytes via the Python source escape `"\u2014"`, never a literal U+2014 byte in test source [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: `"$HOME/.agents/venvs/ai-playbook-test/bin/python3" -m pytest scripts/test_done_sweep_gates_lib.py -q` (full suite including the four sibling canaries; a failure here means the fallback under-enumerates: fix nothing in this plan, report the failing canary against the em-dash plan's implementation) [class: REPOSITORY_TEST]
- [ ] Mutation probe: record `shasum -a 256 scripts/done_sweep_gates_lib.py` first, temporarily narrow the fallback's partition input to the first ten reported rows, run the canary, confirm it fails with an under-enumeration assertion, restore the saved bytes, and re-run the digest, expecting the recorded value byte-identical, before the commit step [class: REPOSITORY_TEST]
- [ ] Commit: `test: witness done-gate fallback full enumeration with an eleven-file canary` [class: IMPLEMENTATION_REQUIRED]

### Task 2: rule 29 records all three authoring-time outcomes

Files:
- `agents/skills/plans/SKILL.md`

- [ ] In rule 29's final sentence, extend `Record the pre-round gate outcome, and any failure class, in the plan's Validation preamble` to `Record the pre-round gate outcome, any failure class, the rule 19 RED-today execution evidence, and the rule 22 authoring-time mechanical audit in the plan's Validation preamble`, keeping the tail sentence byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G2's two greps → expect both found [class: REPOSITORY_TEST]
- [ ] Run the tail pin: `grep -qF "the rule 22 authoring-time mechanical audit in the plan's Validation preamble; a structural-clean pre-round pass converts the done-time exit gate into a pure review-record binding check (sidecar schema, source_kind, digest, verdict, zero blocking)." agents/skills/plans/SKILL.md` → expect RED-today (the pinned post-edit contiguous span is absent before the edit because its head names the inserted record) and GREEN after Task 2, proving the replacement kept the normative tail byte-identical; the replacement span ends at `Validation preamble` and the tail text after it must survive verbatim [class: REPOSITORY_TEST]
- [ ] Commit: `plans: record all three authoring-time gate outcomes in the Validation preamble` [class: IMPLEMENTATION_REQUIRED]

### Task 3: review workers must not mutate the reviewed repository's git state

Files:
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`

- [ ] In review-plan/SKILL.md's worker-constraint paragraph, immediately after the sentence `Workers must not launch children.`, append exactly: `Workers must not mutate the reviewed repository's git state: no commits, branches, refs, stashes, or worktree operations; simulation fixtures live outside any worktree-linked .git directory.` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the plans skill's sub-agent review template, immediately after the anti-idle discipline paragraph, append exactly: `Git discipline (required in every review-round launch): no commits, branches, refs, stashes, or worktree operations in the reviewed repository; the plan file is read-only and so is its git state; build simulation fixtures outside any worktree-linked .git directory.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G3's two greps → expect both found [class: REPOSITORY_TEST]
- [ ] Commit: `review-plan: forbid git-state mutations by review workers in the reviewed repository` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

Closed at the round 5 cap through the cap-closure terminal shape; every staged finding of the cap round with its disposition:

- F1 (High, quality#quoted-backtick-substitution): the G3 adjacency pin carried bare backticks inside a double-quoted grep pattern, which bash command-substitutes at execution; folded by escaping the backticks in the pin (folded).
- F2 (Medium, consistency#incomplete-authoring-record): the stage note's RED-today enumeration omitted G3 and G3b; folded by adding them (folded).
- Carried context from earlier rounds: the sibling-orchestrator prohibition gap (doing-code-review, rfc-design, review-confluence-doc dispatch the same worker class) was dropped at r3 as out of this plan's two-home scope and remains tracked on the origin backlog item's disposition.

### Task 4: final validation

- [ ] Run the full Validation Commands block from the repo root → expect every gate green; record the output in the task log [class: REPOSITORY_TEST]
