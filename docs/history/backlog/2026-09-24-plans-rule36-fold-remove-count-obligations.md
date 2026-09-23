# Backlog: plans rule 36 joint duty omits folds that REMOVE count obligations

- Priority: low
- Status: open
- Workflow: backlog
- Scope: `agents/skills/plans/SKILL.md` (Validation Commands rule 36) and `agents/skills/review-plan/SKILL.md` (Step 5 amend item 5)
- Owner: playbook maintenance
- Source: code review r1 F6 for plan 2026-09-24-p55-audit-deployment-gaps-gate-blind-spots (Low, non-blocking)
- Driving force: code-quality + simplicity

Origin: docs/reviews/2026-09-24-2026-09-24-p55-audit-deployment-gaps-gate-blind-spots-code-review-r1.md, finding F6. Rule 36's joint-direction duty triggers on "a fold that adds or moves a count obligation on a file". A fold that REMOVES a count obligation (or removes text an older gate counts) leaves the same joint-satisfaction surface: the remaining gate set must still be jointly satisfiable over the post-fold file, and the removed gate's span may leave a sibling gate's needle count changed. The duty as worded skips that direction.

Suggested fix: widen the rule 36 trigger (and the mirrored review-plan Step 5 item 5 wording) from "adds or moves a count obligation" to include folds that remove one, re-simulating the file's complete remaining count-gate set in the same mechanical-audit pass.
