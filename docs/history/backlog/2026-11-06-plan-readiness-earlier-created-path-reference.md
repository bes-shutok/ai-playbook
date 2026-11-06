# Backlog: readiness rejects a later edit of an earlier task-created file

Status: covered-pending-execution (docs/history/plans/2026-11-06-plan-readiness-planned-path-lifecycle.md)
Workflow: backlog
Priority: high
Origin class: self-serving
Environment: Codex, 2026-11-06, repository-local readiness validator
Class: fix-class
Driving force: simplicity
Cluster: docs/history/backlog/2026-10-30-plan-readiness-deleted-files-path-vocabulary.md (related existence vocabulary; this row is the distinct earlier-owner case, not planned deletion)

## Problem and evidence

During test-suite-runtime-reduction authoring, Task 1 created a new benchmark report and Task 3 updated it. The unannotated Task 3 Files entry failed `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-06-test-suite-runtime-reduction.md` with `Files: path docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction.md in Task 3 does not exist` and `carries no *(new)* annotation`. Annotating Task 3 then failed with `duplicate creating task` and `annotated *(new)* in both Task 1 and Task 3`.

The first shape is preserved in authoring checkpoint 83a4f9da4c76712901a2a201221a9e872c79efe6, and the duplicate-marker probe in checkpoint 7074fceca2a0d5e09b43b14dff3a3ee2e48960ee. `plan_ownership_problem` in `scripts/plan_readiness.py` collects the creating task before its per-entry existence loop, but that loop ignores the earlier owner when an unannotated later Files entry refers to the same future-created path. Its documentation says shared listings without annotation are sequential edits, yet the nonexistent-path check refuses this ordinary new-file sequence.

## Recovery and proposed correction

This authoring run kept the validator unchanged and separated the baseline/options report from the final comparison report. The workaround preserves measurement evidence but adds an otherwise unnecessary artifact. Prefer recognizing a preceding creation owner in the existing existence predicate; preserve duplicate-creator and consumer-before-owner rejection. No added blocker or validator is requested.

## Acceptance

A Task 1 new file followed by a Task 3 unannotated edit is accepted without materializing the file during authoring. An absent path with no creator, a consumer before its creator, and two creating tasks retain their current refusals. Include both single-file and directory-plan consumers when their shared grammar reaches this predicate.

Dedup probe: searched open backlog and PLAN-PROMPTS for planned-new, future paths, creating task and ownership. The older deleted-files-path-vocabulary row covers paths absent after deletion; it does not cover a file legitimately created by an earlier task.
