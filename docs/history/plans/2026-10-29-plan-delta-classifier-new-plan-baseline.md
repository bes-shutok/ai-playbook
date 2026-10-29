# Plan: Classify new plans from their first checkpoint

Backlog origin: docs/history/backlog/2026-10-28-plan-delta-classifier-new-plan-baseline.md
Driving force: simplicity; secondary: correctness
Plan review record: the staging series .ai-playbook/reviews/2026-10-29-plan-review-plan-delta-classifier-new-plan-baseline-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-28-plan-delta-classifier-new-plan-baseline.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- **First-draft checkpoint**: the earliest commit after the classifier's `--since` commit that adds the plan path and contains its initial authored bytes.
- **Absent baseline**: a plan path missing from `--since` after a successful history lookup found no first-draft checkpoint through `HEAD`.
- **Correction row**: the classifier-produced record for an exempt plan edit, stored in a review sidecar.
- **Directory plan**: a plan stored as a directory with a charter and task files.
- **Fresh review**: the existing full plan-review round required when a change is unclassified.
- **Unclassified outcome**: the classifier's existing result for changes it cannot prove mechanical, which triggers a fresh review.

## Why

A new plan may not exist at the review loop's start commit, so the delta classifier currently reports an opaque tool error even though each authored plan write is checkpointed in Git. This plan uses the first checkpoint's exact bytes when available and preserves the existing fresh-review path when no baseline can be derived.

## Gist & Examples

TLDR: Reuse the first checkpoint for new-plan classification, improving clarity through simplicity.

Before, a plan absent from `--since` stops classification with a tool error even when its first draft is available in a later checkpoint commit.

After, the classifier uses that checkpoint as the exact before side; when no checkpoint is available, it names the absent baseline and follows the existing fresh-review route.

Tracked plans keep their current comparison. No acknowledgement, extra commit, or new gate is added.

## Outcome

A new plan's later folds receive a clear classification result from its first authored checkpoint, with fresh review covering the case where a successful history lookup finds no checkpoint.

- The first checkpoint supplies exact baseline bytes without adding a commit step.
- When history is readable but no checkpoint exists, the named unclassified result follows the existing fresh-review route; a Git read failure keeps its existing error result.
- Tracked-plan results, directory-plan structural handling, and the semantic review gate keep their current behavior.

Gate delta: no new refusal class, hard gate, fence, protocol layer, schema field, ceremony, or dispatch pause is added or removed; the missing-baseline condition reuses the first authored checkpoint and otherwise enters the existing unclassified fresh-review path.

## Assumptions

- The first authored checkpoint is the correct exact baseline because it records the plan bytes reviewed before subsequent folds. Basis: `agents/skills/plans/SKILL.md`, Authoring checkpoint duty, and the witnessed untracked-plan failure in the backlog origin.
- When a successful history lookup finds no checkpoint, fresh review is safer and already supported. Basis: `agents/skills/plans/SKILL.md`, review-loop rule 2.
- The directory-plan structural classification path is outside this single-file plan scope. Basis: `scripts/plan_delta_classifier.py` handles directory plans in a separate mode that already reports added files as unclassified.

Decision points requiring a grill: baseline recovery uses the earliest authored checkpoint and falls back to fresh review when absent; maintenance-selected authorization via `docs/history/backlog/PLAN-PROMPTS.md`, entry `plan-delta-classifier-new-plan-baseline`; affects Task 1 and Outcome; source: origin prompt; 2026-10-29.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: first-checkpoint bytes are used only when the classifier can resolve them from Git history.
- Compatibility: tracked-plan behavior and directory-plan structural handling remain unchanged.
- Review integrity: an absent checkpoint is named as unclassified and continues through fresh review without acknowledgement.

**Done when:**
- Focused fixtures prove first-checkpoint reuse, no checkpoint after a successful history lookup, a history-read failure, and unchanged tracked-plan classification.
- The plan-delta classifier suite passes.

**Ship when:**
- None; this changes repository-owned classifier behavior only.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/plan_delta_classifier.py` (Task 1)

**Tests:**
- `scripts/test_plan_delta_classifier.py` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above when they directly implement the checkpoint lookup or its classifier fixtures, or fix a regression introduced by this plan.

**Out of scope; reject unless plan-related:**
- `agents/skills/plans/SKILL.md`; reason: its existing checkpoint and fresh-review duties already provide both inputs to the classifier behavior.
- Directory-plan structural classification; reason: its separate path already treats manifest additions as unclassified.
- The two Stage 1 design-context backlog rows; reason: they describe distinct classifier and authorization defects.

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_plan_delta_classifier.py'
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/plan_delta_classifier.py scripts/test_plan_delta_classifier.py
bash scripts/scan-public-hygiene.sh --files scripts/plan_delta_classifier.py scripts/test_plan_delta_classifier.py
```

### Task 1: Reuse the first checkpoint as the new-plan baseline

Context surface: the plan's Terms and this task.

Files:
- `scripts/plan_delta_classifier.py`
- `scripts/test_plan_delta_classifier.py`

Primary class anchors:
- `main` in `scripts/plan_delta_classifier.py`

Evidence:
- The classifier currently reports a tool error when a plan path is absent from the valid `--since` commit (`scripts/plan_delta_classifier.py`).
- The plans skill commits every plan-file write, so a first-draft checkpoint may contain the exact bytes without a new checkpoint ceremony (`agents/skills/plans/SKILL.md`, Authoring checkpoint duty).
- The review sidecar stores a digest, not source bytes; it cannot reconstruct an unavailable checkpoint (`agents/skills/review-staging/SKILL.md`).

- [ ] Given a readable first commit after `--since` that adds the single-file plan path, use that commit's exact blob as the before side and report the selected baseline commit and digest. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the plan path is absent from `--since` and a successful history lookup finds no checkpoint adding that path through `HEAD`, report a named absent-baseline unclassified outcome so review-loop rule 2 starts a fresh full review; emit no correction row and require no operator acknowledgement. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the plan path exists at `--since`, preserve current classifier results; given the checkpoint history lookup fails, preserve the existing indeterminate or tool-error distinction instead of treating the failure as an absent checkpoint. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given first-checkpoint, no-checkpoint, history-read-failure, and tracked-plan fixtures, assert each result and keep directory-plan structural classification unchanged. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: classify new plans from first checkpoint` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

No workflow prose change is needed: the plans skill already checkpoints every plan-file write and routes unclassified folds to fresh review. The classifier's result and its regression fixtures carry the behavior.
