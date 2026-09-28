Status: done (2026-09-30; all three residuals executed by plan completed/2026-09-28-emdash-residuals-canary-and-review-discipline.md, landed main abe72523; r1 impl review zero blocking)
Priority: medium
Origin class: self-serving

# Em-dash plan authoring residuals: >10-hit partition canary, stage-note record, review-agent git discipline

**Captured from:** plan docs/history/plans/2026-09-28-em-dash-whole-file-gate-added-lines-selection.md review rounds r4 (non-blocking residuals, re-executed green in r4) and the r4 reviewer's incident disclosure; deferral default chosen at the r4 ready=yes exit per the authoring flow's backlog-deferral default.

**1. Partition-input canary for the >10-hitting-files case (r4 F1, Medium, testing#partition-input-unwitnessed):** the done-gate fallback pins its partition input to the touched probe's COMPLETE stdout precisely because the lib's failure message carries only `tail_rows[-10:]`; no canary exercises a fixture with more than ten hitting files, so an implementation reading the failure message instead of the probe stdout would pass every prescribed canary. Add a fifth canary whose fixture carries eleven hitting files and expects the baseline report to enumerate all tracked rows.

**2. Stage-note authoring-record backfill (r4 F2, Low, documentation#missing-authoring-record):** the plan's Validation stage note omits the rule-29 pre-round, rule-19 RED-today, and rule-22 mechanical-audit authoring records; the r4 round re-executed all of them green. A future plan template or checklist item should pin that the Validation preamble records these three authoring-time gate outcomes.

**3. Review-subagent git-mutation discipline (r4 incident):** an r4 review worker ran `git init/add/commit` inside a temp copy whose `.git` was a worktree pointer file, briefly landing commit 02a8c4c2 on the authoring branch before repairing with `git reset HEAD~1`. The review-plan sub-agent prompt states the plan file is READ-ONLY but does not forbid git mutations on the repository under review; amend the review-plan dispatch guidance so review workers never create commits, branches, or refs in the reviewed repository (simulation fixtures must live outside any worktree-linked `.git`), and consider a lessons-corpus entry for the worktree-pointer `.git` collision.
