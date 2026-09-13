# plan-readiness: Review Scope category-label grammar misses label-with-prose lines

Status: done
Origin: tooling-polish plan code review r4 F1 (docs/reviews/2026-09-09-plan-authoring-tooling-polish-code-review-r4.md), diff digest 4aa0a410

## Finding (Medium, verified)

`_REVIEW_SCOPE_CATEGORY_RE` in `scripts/plan_readiness.py` requires a category label line to END at `:**`, but the plans skill's own Review Scope template (agents/skills/plans/SKILL.md, Review Scope authoring area) shows the Documentation label with guidance prose on the same line (`**Documentation:** production code and tests use the explicit list...`). A plan copying that template-literal line opens no category block: implementation/test paths listed under it escape check (a) and are misattributed to the preceding block (check (b) duplicate attribution can also distort). Probe at HEAD: template-prose label with `src/service.py` under it returns None; bare label yields the named reason.

## Candidate fixes

- Widen the grammar to accept a bold-label prefix followed by same-line prose (`^\*\*(.+?):\*\*[ \t]*(.*)$`, label still ending in `:` inside the bold); items then belong to that block.
- Or pin the authoring rule that category labels sit alone on their line and add a selftest arm locking the chosen shape.

Add whichever arm pins the decision (`selftest#review_scope/template_prose_label_*`).
