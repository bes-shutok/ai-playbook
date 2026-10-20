# Plan-review Validation-block check and validation-authoring rules 4/13 need a pinned-mirror note

- **Filed:** 2026-10-21, execute-plan Step 1.2b intermediate review of Task 2 (plan-validation-command-undefined-repo); item shape completed at Phase 3 r1 (finding cc1)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fence-class (a wording fence, not a gate: the drift it prevents is an author-rule versus reviewer-check disagreement, the failure class the plan-validation-command-undefined-repo plan closed)
- **Driving force:** consistency (primary), code-quality (secondary)
- **Skill/step:** `agents/skills/review-plan/SKILL.md` Validation-block check; `agents/skills/plans/validation-authoring-rules.md` rules 4 and 13
- **Source reference:** Task 2 intermediate review (task-2-review.log.md, contract-docs context) and `.ai-playbook/reviews/2026-10-21-plan-validation-command-undefined-repo-code-review-r1.md` finding cc1 (Low, non-blocking); capture hygiene: `scan-public-hygiene.sh --files` pass
- **Why not fixed now:** the plan's readiness-boundary constraint admits no extra review machinery and both files' byte-neutral ceilings (41486 and 64158) leave no room for a cross-reference clause on either side; deferred by the execute-plan orchestrator at the Task 2 boundary
- **Dedup probe:** searched open backlog filenames and Problem text for `pinned mirror`, `validation-authoring`, `Validation-block`, `rule 13`, `undefined variable`; nearest: none open (the origin row 2026-10-10-plan-validation-command-undefined-repo was deleted at plan creation); no merge

## Problem

The 2026-10-21 plan-validation-command-undefined-repo landing added a reviewer-facing Validation-block check to `agents/skills/review-plan/SKILL.md` that restates the same predicate as `agents/skills/plans/validation-authoring-rules.md` rules 4 and 13 (documented working directory; variables assigned in the block or explicitly supplied; redundancy only when another invocation covers the same check, paths, and failure mode) near-verbatim, with no cross-reference naming the counterpart text as its pinned mirror. The two wordings can drift silently in future edits of either file, and a drift between an authoring rule and its reviewer-facing check recreates the author-vs-reviewer disagreement class this landing closes.

## Suggested fix

At the next natural edit of either file, add a one-clause pinned-mirror note on each side naming the counterpart location and the duty to change both together (the pattern the review-plan skill already uses for its other pinned mirrors), paying the bytes with an equivalent deletion in the same file. No validator or gate; wording coupling only.
