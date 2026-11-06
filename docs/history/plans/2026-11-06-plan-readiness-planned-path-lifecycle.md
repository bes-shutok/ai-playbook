# Plan: plan-readiness planned-path lifecycle

Backlog origins (scope of record):
- docs/history/backlog/2026-11-06-plan-readiness-earlier-created-path-reference.md
- docs/history/backlog/2026-10-30-plan-readiness-deleted-files-path-vocabulary.md

Authoring claim: 2026-11-06-plan-readiness-earlier-created-path-reference.md (session sess_33d663bb-85b0-4537-bd18-a1af4c0a6c0b)

Driving force: simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-plan-readiness-planned-path-lifecycle-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically).
Execution budget: 2.25h total, largest task 1.0h
Executed: no

## Terms

- planned-new marker: the `*(new)*` annotation (optionally with elaboration) on a task `Files:` item; the single creation record marking the task that creates the file.
- planned-deletion marker: the `*(deleted)*` annotation on a task `Files:` item; declares the task deletes the path at execution; never a creation record.
- creation record: the `owners` mapping `plan_ownership_problem` collects from planned-new annotations; section index plus label for each created path.
- Files-existence check: clause (c) of `plan_ownership_problem`; refuses a `Files:` path absent under the repo root when it carries no recognized annotation.
- pre-round gate: `python3 scripts/plan_readiness.py --pre-round <plan>`, the structural-only authoring gate; "preflight" in this plan's prose is a synonym for it, not a second gate.
- duplicate-creator refusal: two planned-new annotations for one path in different task sections (validator reason: "duplicate creating task").
- consumer-before-owner refusal: a checklist item referencing a path whose creation record is a later task section (validator reason: "consumer-before-owner"); distinct from the Files-listing strictly-later-owner shape, which refuses through the Files-existence check.

## Why

The plan-readiness validator refuses two legitimate plan shapes. A task that edits a file an earlier task creates refuses, because the existence loop ignores the creation record the duplicate-creator check already collected; the witnessed authoring run had to split one report into two artifacts to pass preflight. A task that deletes a file has no grammar to declare the deleted path, forcing the witnessed mid-run prose workaround. Both false positives push authors away from declared Files lists.

## Gist & Examples

TLDR: the Files-existence check recognizes an earlier creation owner and a new `*(deleted)*` annotation, so sequential-edit and planned-deletion plans pass preflight without extra artifacts, in the name of simplicity.

Before: Task 1 lists `src/report.md` with the planned-new marker and Task 3 lists the same path unannotated; preflight refuses Task 3 with "does not exist ... carries no *(new)* annotation", although the duplicate-creator check already knows Task 1 creates it. A deletion task cannot name its deleted path at all; the witnessed run moved the rows into prose.

After: the same Task 3 listing passes because a creation record at an earlier or the same section index exempts it; a Files listing carrying `*(deleted)*` passes whether the path exists today or not. An absent path with no creation record, two creating tasks, and a consumer before its creator still refuse exactly as today.

Edge cases: a Files listing whose creation record sits in a LATER task still refuses (the strictly-later owner does not exempt; the Files-listing form of consumer-before-creator keeps its refusal). A `*(deleted)*` marker never claims creation, so duplicate-creator and consumer-before-owner are untouched by it. Marker kind is decided per annotation by its leading keyword: an elaboration is in-grammar when it follows the leading keyword (`*(deleted; see Task 2)*` is a deletion marker, `*(new; also-deleted)*` is a creation record, not a deletion marker), and an item carrying both annotations is both a creation record and deletion-exempt (independent flags; no kind crossing). The planned-deletion marker imposes no creation linkage and no ordering constraint against creation records: a deletion of a never-created or never-existing path, and a delete-listing ahead of the creating task, pass preflight by design (an accepted narrowing; detection defers to execution and review, and the stance is pinned by a Task 2 witness cell). Directory-shaped plans assemble task sections through `charter_plus_tasks_text` in filename order, so the earlier-creator comparison keys on heading ordinals when every section carries one, falling back to document position; a Task 1 witness cell pins the directory form with unpadded task filenames. The Review Scope inventory derivation wraps the same Files collector, so deleted-marked paths stay declared tokens for coverage without code change there.

## Outcome

Authoring plans describe a file's full lifecycle, creation through later edit through deletion, in their declared Files lists and pass the pre-round gate without workaround artifacts.

- An unannotated later Files listing of a path an earlier task creates passes preflight without materializing the file.
- A deletion task declares its deleted path with `*(deleted)*` and passes preflight.
- The three protections (absent path with no creation record, two creating tasks, consumer before its creator) keep their exact refusals.

Gate delta: no new gate, validator, fence, protocol layer, or schema field. Two existing refusal surfaces narrow: the Files-existence refusal no longer fires for a `Files:` path whose creation record an earlier or the same task owns, and it exempts paths carrying the planned-deletion marker (including a deletion of a never-created path and a delete-listing ahead of its creating task: accepted narrowings, no creation linkage and no ordering constraint). Removed refusals: none beyond those two narrowings. The absent-no-creator, duplicate-creating-task, and consumer-before-owner refusals are unchanged; the marker is accepted input grammar, not a checked surface.

## Assumptions

- assume the narrower existence predicate consults the already-collected creation records rather than recomputing them; basis: the owners map in `plan_ownership_problem` (scripts/plan_readiness.py:1451-1467) holds exactly the needed evidence, probe-confirmed 2026-11-06.
- assume the deletion representation is an annotation in the existing Files grammar, not a side table or prose convention; basis: origin 2's suggested remedy, and the simpler-design comparison recorded in the requirements buffer.
- assume no runtime behavior changes beyond the validator and the plans skill documentation; basis: both origins scope the change to the validator and the Files grammar.
- The stale comment at scripts/plan_readiness.py:1070 naming an execute_plan_runtime.py `_plan_declared_files` producer is pre-existing drift; grep shows the problem strings now live only in plan_readiness.py and its test. Out of scope; recorded as an observation.

Decision points requiring a grill: none remain.

## Standing constraints

- This repository never runs its whole test suite during plan execution; validation uses the focused plan-readiness suite plus the validator's selftest.
- The validator's Files grammar docstrings declare the one declaration contract; the pairing comment at scripts/plan_readiness.py:1069-1081 is a historical note whose named runtime peer (execute_plan_runtime.py `_plan_declared_files`) no longer exists (grep-verified; the problem strings live only in plan_readiness.py and its test). Edits there keep the existing docstring style and never reflow unrelated lines.

## Evaluation Criteria

Quality dimensions:
- correctness: the two false-positive shapes pass preflight; the three protected shapes keep their exact refusal reasons (probe-verified against the current validator before implementation).
- regression safety: the focused plan-readiness suite and the validator selftest pass after each task.
- maintainability: the collector returns marker kinds through one annotation-grammar home; no second parser appears.

**Done when:**
- The focused plan-readiness suite and `python3 scripts/plan_readiness.py --selftest` pass with the new regression cells.
- A probe plan exercising the earlier-creator shape and the planned-deletion shape passes `--pre-round`; the three protected shapes refuse.

**Ship when:**
- Not applicable; repository-local tooling with no external release surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (Task 1)

**Tests:**
- `scripts/test_plan_readiness.py` (Task 1) *(new cells in existing file; Task 2 shares both paths)*

**Documentation:**
- `agents/skills/plans/SKILL.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_shape.py`; reason: the directory-shape resolver reads section structure only and owns no Files-annotation grammar.
- `scripts/done_run.sh`; reason: the closeout runner consumes review staging, not the Files grammar.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
# 1. Focused suite: the plan-readiness suite (canonical executable artifact)
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py -q || { echo "focused suite failed"; exit 1; }
# 2. Validator selftest over the ownership family
python3 scripts/plan_readiness.py --selftest || { echo "selftest failed"; exit 1; }
```

The Done-when probe plan lives temporarily under `docs/history/plans/` (the pre-round gate refuses plans outside that directory): author a minimal structural plan exercising the earlier-creator shape and the planned-deletion shape plus the three protected shapes, run `python3 scripts/plan_readiness.py --pre-round <probe-path>` expecting the pass and the three refusals, and delete the probe file in the same task before commit (no stranded residue).

### Task 1: Recognize an earlier creation owner in the Files-existence check

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

Primary class anchors:
- `plan_ownership_problem` in `scripts/plan_readiness.py`
- `_plan_files_items` in `scripts/plan_readiness.py`

- [ ] `plan_ownership_problem` delivers `earlier-creator exemption`: given a plan whose Task 1 lists an absent path with the planned-new marker and a later task lists the same path unannotated in its Files declaration, expects the existence check to report no refusal for the later listing while the duplicate-creator check stays silent [class: REPOSITORY_TEST]
- [ ] `plan_ownership_problem` delivers `same-section exemption`: given one task whose Files list marks an absent path planned-new and lists the same absent path again unannotated in the same section, expects no duplicate-creator refusal and no existence refusal (the absent path makes the cell RED today through the Files-existence refusal, so only an at-or-before owner comparison turns it GREEN) [class: REPOSITORY_TEST]
- [ ] `plan_ownership_problem` delivers `directory-form ordering`: given a directory-shaped plan with ten or more unpadded task filenames run through the plan-shape assembler, where Task 2 creates an absent path and Task 10 lists it unannotated, expects no refusal (heading-ordinal order governs the comparison when every section carries an ordinal; unpadded filename assembly order would otherwise invert the exemption) [class: REPOSITORY_TEST]
- [ ] Safety witness (strictly-later owner): given a Files-listing-only plan (no checklist reference to the path in any earlier task, so the consumer-before-owner clause cannot mask this clause) whose absent path has its planned-new record in a LATER task section, expects the existing Files-existence refusal naming the LISTING task and path, byte-identical, so the Files-listing consumer-before-creator shape keeps its refusal [class: REPOSITORY_TEST]
- [ ] Safety witness (protections unchanged): given an absent path with no creation record anywhere, given two tasks both carrying the planned-new marker for one path, and given a checklist item referencing a path whose creation record is a later task, expects each to keep its current refusal reason (pinned by stable substring, the repository's existing selftest pattern); these cells are expected GREEN today [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the new exemption cells (earlier-creator, same-section, directory-form) fail against the current validator; the safety-witness cells pass today (tests selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation: in the existence loop, pass a token when its creation record's section index is at or before the current section's index, ordering sections by heading ordinal when every section carries one and by document position otherwise (directory plans assemble task bodies in filename order) [class: IMPLEMENTATION_REQUIRED]
- [ ] Write minimal implementation, cont.: update the clause (c) docstring to name the earlier-owner and same-owner exemptions; keep the reason string and every other refusal byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the focused plan-readiness suite passes including the Task 1 cells [class: REPOSITORY_TEST]
- [ ] Commit: `fix: readiness accepts a later edit of an earlier task-created file` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Add the planned-deletion marker to the Files grammar

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

Primary class anchors:
- `_plan_files_items` in `scripts/plan_readiness.py`
- `plan_ownership_problem` in `scripts/plan_readiness.py`

- [ ] `_plan_files_items` delivers `deletion-marker recognition`: given a Files item carrying the `*(deleted)*` annotation, expects the collector to record the marker kind so the existence check can exempt the path; the token itself is still collected and declared [class: REPOSITORY_TEST]
- [ ] `_plan_files_items` delivers `marker-kind grammar`: marker kind is decided per annotation by its leading keyword; given `*(deleted; see Task 2)*` expects deletion-kind with no creation record, given `*(new; also-deleted)*` expects a creation record with no deletion marker, and given one item carrying both `*(new)*` and `*(deleted)*` annotations expects both flags set (independent annotations, no kind crossing) [class: REPOSITORY_TEST]
- [ ] `plan_ownership_problem` delivers `deleted-path exemption`: given a Files listing carrying the `*(deleted)*` marker for a path absent under the fixture repo root, and given the same marker on a path that exists under that root, expects the existence check to refuse neither [class: REPOSITORY_TEST]
- [ ] Safety witness (delete-before-create accepted): given a task listing an absent path `*(deleted)*` ahead of a later task's planned-new record for the same path, expects no refusal (the accepted no-ordering narrowing, pinned deliberately) [class: REPOSITORY_TEST]
- [ ] Safety witness (marker is not a creation record): given two tasks both carrying the `*(deleted)*` marker for one path that exists under the fixture root (or carries a creation record, so the Files-existence clause stays out of the assertion), and given a `*(deleted)*` listing beside an unannotated listing of the same existing path, expects `plan_ownership_problem` to return no refusal at all (assert refusal-freeness, not the absence of one reason substring) [class: REPOSITORY_TEST]
- [ ] Safety witness (marker is not a creation record, consumer half): given a checklist reference in an EARLIER task section than the deleted-marked Files listing, expects consumer-before-owner behavior unchanged after the fix (the marker claims no creation, so a mutant recording the marker as a creation record trips the refusal) [class: REPOSITORY_TEST]
- [ ] Safety witness (grammar isolation): given a Files item with an unrecognized annotation, expects the collector to keep treating it as unannotated so no unknown marker silently gains existence exemption [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the new exemption and grammar cells (deletion-marker recognition, marker-kind grammar, deleted-path exemption absent half, delete-before-create) fail against the current validator; the safety-witness cells' existing-refusal halves pass today (tests selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation: extend the collector's annotation recognition to the planned-deletion marker (leading-keyword regex in the same family as the planned-new expression) and exempt deleted-marked paths in the existence check; the collector's return shape is consumed at four sites (Review Scope wrapper, FILES-COVERAGE per-task set, duplicate-creator loop, existence loop): keep every site's unpacking and predicate updated [class: IMPLEMENTATION_REQUIRED]
- [ ] Write minimal implementation, cont.: update the collector's and the clause (c) docstrings to the marker-kind contract, keeping the existing docstring style [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the focused plan-readiness suite passes including the Task 2 cells [class: REPOSITORY_TEST]
- [ ] Commit: `feat: readiness accepts planned-deletion Files declarations` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Document the planned-deletion marker in the plans skill

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `Plan Format template Files list` in `agents/skills/plans/SKILL.md`

- [ ] The template Files example gains one line showing the planned-deletion annotation beside the planned-new example, and the format rules gain one bullet defining the marker: it declares the task deletes the path, it is not a creation record, and the existence check exempts it [class: IMPLEMENTATION_REQUIRED]
- [ ] The same rule bullet's neighborhood carries a one-clause mention that an unannotated later listing of an earlier task's planned-new path is accepted (the Task 1 acceptance needs no author action or grammar token) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the pre-round gate over this plan stays clean and the documentation renders in the template block without breaking the template's structure [class: REPOSITORY_TEST]
- [ ] Commit: `docs: plans Files grammar documents the planned-deletion marker` [class: IMPLEMENTATION_REQUIRED]
