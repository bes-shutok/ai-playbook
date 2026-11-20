# Backlog: known-red baseline Task 2 review residuals

Driving force: code-quality (witnessed by the Task 2 intermediate review r1, 2026-11-19, worktree run known-red-gates-consumed-baseline, commit f9a9f9c698; log `docs/tmp/execute-plan/known-red-gates-consumed-baseline/review-task2-r1.log.md` in the run worktree, mirrored at the reviews home at Phase 3).

Low candidates (valid, in-diff, unfixed):

1. The plan-quality-gate classification clause drops the Terms' "from the check families" qualifier on the lower-case `pin fail:` exit-effect wording; cosmetic, no reachable divergence (classification fires only on baseline-listed lines).
2. The preamble's "subordinated to the render-time snapshot" phrase is directionally loose (naming is subordinate to live output over the snapshot); the colon expansion carries the operative direction; the phrase is a Task 3 witness-needle span, so any rewording must move the needle in the same change.
3. The unavailable-definition parenthetical is duplicated verbatim on the classification clause and the preamble (each plan-mandated); future definition changes need lockstep edits across Terms/clause/preamble.

Cluster: known-red-gates-consumed-baseline
