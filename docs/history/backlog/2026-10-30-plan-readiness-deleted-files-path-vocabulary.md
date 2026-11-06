# plan readiness: no vocabulary for Files paths a task deletes

Driving force: a plans task whose closure action deletes a file cannot name that path in its `Files:` list. `scripts/plan_readiness.py` (pre-round, check (c) at the Files-existence loop) exempts only paths carrying the `*(new)*` planned-new marker; a deleted-at-execution path fails with "does not exist ... and carries no *(new)* annotation" (witnessed 2026-10-30 in the review-plan-nonconvergence-disposition run: both origin-row deletions refused pre-round readiness after the task body landed, forcing a mid-run skill-gated plan repair that moved the rows into prose and split the evidence list).

Suggested remedy: a planned-deletion marker or disposition token in the plans template `Files:` grammar (for example `*(deleted)*`), recognized by the existence check and by the coverage warning leg, so a deletion task keeps its touched paths declared without a prose workaround.

Scope: scripts/plan_readiness.py existence/coverage checks and the plans template Files grammar; no runtime behavior change beyond the validator.

Cluster: plan-readiness validator grammar family.
Cluster: docs/history/backlog/2026-11-06-plan-readiness-earlier-created-path-reference.md
