# plans: readiness scope-classification misses a classification tag placed on a multi-line checklist item's continuation line

- Status: open
- Priority: high
- Skill and step: `agents/skills/plans/SKILL.md` Plan Format classification-tag rule; `scripts/plan_readiness.py` scope classification probe
- Driver: authoring review loop of the 2026-09-23 P48 post-execution residuals plan (round r1 stage, caught by the r2 review's direct probe)

## Problem

A plan checklist item whose text wraps over multiple lines carried its `[class: ...]` tag at the end of the LAST continuation line instead of the first (checkbox-marker) line. The readiness parser reads only checkbox-marker lines, so the tag was invisible: the item classified as untagged, the scope-classification probe reported the plan defective, and the plan's own Gate 0 (`plan_readiness.py`) could never exit 0. The defect survived a review round because the tag was visually present and the reviewing panel only caught it by exercising the probe directly.

Observed versus expected: the plans skill's tag rule says the tag sits "at the end of the item line", which is ambiguous for a wrapped item; the validator silently treats continuation lines as invisible rather than flagging a tag token placed there.

## Suggested fix

Make the parseable placement explicit on one side (or both): (a) the plans SKILL.md tag rule states the tag must sit on the item's first (checkbox-marker) line; (b) `plan_readiness.py` warns when a `[class: ...]` token appears on a non-checkbox line inside a task block, so a wrapped-item tag fails loud instead of silently classifying the item untagged.

## Reproduction

Author a plan with one wrapped checklist item tagged on its continuation line; run `python3 scripts/plan_readiness.py <plan>`: the scope-classification probe reports the item untagged. Move the tag to the first line: the probe clears. Verified both directions during the r2 fold of the witnessing plan (probe returned the violation before, None after).

## Environment

Ad-hoc worktree authoring off main (206a7f7b), 2026-09-23, repo copy current. Witnessed in the P48 residuals plan review loop (r1 fold introduced the wrapped item; r2's blind probe caught the classification failure).
