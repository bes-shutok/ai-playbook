# Plan: Make validation commands executable as written

Backlog origin: docs/history/backlog/2026-10-10-plan-validation-command-undefined-repo.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-20-plan-review-plan-validation-command-undefined-repo-r*.md
Execution budget: 1.5h total, largest task 1.0h

## Terms

- Validation block: the fenced bash block in a plan's `## Validation Commands` section.
- Documented working directory: the repository location from which a plan tells the operator or executor to run its validation block.

## Why

A plan can prescribe a validation command that fails because it uses an undefined shell variable or assumes an unstated working directory. Such commands make the plan's verification unreliable and can duplicate checks that already run elsewhere in the block.

## Gist & Examples

TLDR: make plan validation commands runnable from their documented directory with declared inputs, and remove only redundant checks during authoring and review.

Before: a plan may run `cd "$REPO"` without assigning `REPO`, or repeat a check already covered by another command.

After: plan authoring guidance requires defined command inputs and a clear working directory; plan review has a concrete example of an undefined variable and treats redundant invocations as avoidable.

Edge cases: a command that intentionally consumes an environment variable names it and documents how it is supplied; a check that looks similar but covers a different path or failure mode remains separate.

## Outcome

Every plan validation command has a documented execution directory and all required shell inputs are defined or explicitly supplied. The plan-review guidance recognizes undefined-variable commands and duplicate invocations that cover the same check, paths, and failure mode. No new validator, gate, or workflow step is introduced.

Gate delta: no blocker, refusal class, fence, protocol layer, schema field, or dispatch condition added; existing validation-authoring and plan-review guidance is clarified, and no existing gate is removed.

## Assumptions

- The existing `Validation Commands (authoring rules)` module is the single home for authoring requirements about validation blocks. Basis: `agents/skills/plans/SKILL.md` delegates this topic to `agents/skills/plans/validation-authoring-rules.md`.
- The `review-plan` readiness-boundary examples are the right home for a reviewer-facing defect example; the skill already treats those examples as the executable reference for its readiness judgment. Basis: `agents/skills/review-plan/SKILL.md`, `Readiness boundary examples`.
- Duplicate checks belong under the existing validation-minimality rule, and defined variables plus working-directory assumptions extend the existing cwd-anchoring rule. These existing rules cover the same validation-command predicate, so no new top-level authoring rule is needed. Basis: `agents/skills/plans/validation-authoring-rules.md`, rules 4 and 13.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: every validation command's working directory and shell inputs are explicit enough to run as documented.
- Maintainability: redundant invocations are removed when another command proves the same check.
- Reviewability: plan reviewers can identify an undefined-variable validation defect from a concrete example.

**Done when:**
- The authoring rules cover command working directories, variable definition or explicit supply, and duplicate-check minimality.
- The review-plan skill includes a concrete undefined-variable example and the finding it warrants.
- Plan readiness, review, hygiene, and em-dash checks pass for the changed plan and documentation; `PYTHONPATH=scripts python3 -m unittest scripts.test_plan_review_boundary_examples` passes with the readiness fixture markers and judgments intact.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/plans/validation-authoring-rules.md`
- `agents/skills/review-plan/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: this backlog asks for authoring and review guidance, not a new mechanical validator.
- Unrelated validation examples or runtime scripts; reason: they do not determine whether plan validation commands are executable as documented.

## Validation Commands

Run these commands from the repository root.

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-20-plan-validation-command-undefined-repo.md
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-20-plan-validation-command-undefined-repo.md
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-20-plan-validation-command-undefined-repo.md agents/skills/plans/validation-authoring-rules.md agents/skills/review-plan/SKILL.md
PYTHONPATH=scripts python3 -m unittest scripts.test_plan_review_boundary_examples
bash scripts/scan-public-hygiene.sh --files agents/skills/plans/validation-authoring-rules.md agents/skills/review-plan/SKILL.md docs/history/plans/2026-10-20-plan-validation-command-undefined-repo.md
```

### Task 1: Make validation authoring rules self-contained

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/plans/validation-authoring-rules.md`

Primary class anchors:
- `Validation Commands (authoring rules)` in `agents/skills/plans/validation-authoring-rules.md`

- [x] Extend existing rule 4 to remove redundant commands only when another invocation covers the same check, paths, and failure mode; retain commands that prove distinct obligations. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend existing rule 13 to require the documented working directory and require every referenced shell variable to be assigned in the block or explicitly supplied by its documented invocation context before use. Name `cd "$REPO"` with no `REPO` assignment as invalid. [class: IMPLEMENTATION_REQUIRED]
- [x] Delete equivalent redundant operative prose from this same file so its byte count does not grow; preserve existing obligations and record the before/after byte counts in the task log. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: require executable plan validation commands` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Add a plan-review example for undefined validation inputs

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/review-plan/SKILL.md`

Primary class anchors:
- `Readiness boundary examples` in `agents/skills/review-plan/SKILL.md`

- [x] Add a reviewer check for undefined variables and undocumented working directories, plus redundant invocations only when one command covers the same check, paths, and failure mode; preserve distinct checks. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a concise example where `cd "$REPO"` lacks a definition and a check is invoked twice without adding coverage; show the finding and corrected form. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the example within the current readiness boundary: it checks existing validation promises and adds no requirement for guessed test identities, new validators, or extra review machinery. [class: IMPLEMENTATION_REQUIRED]
- [x] Delete equivalent redundant operative prose from this same file so its byte count does not grow; preserve existing obligations and record the before/after byte counts in the task log. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: show undefined validation variable finding` [class: IMPLEMENTATION_REQUIRED]
