# Backlog: runtime-reduction validation misses committed Python insertions

Status: open
Workflow: backlog
Priority: low
Origin class: plan-review residual
Class: fix-class
Driving force: code-quality

## Problem and evidence

The Validation Commands in `docs/history/plans/2026-11-06-test-suite-runtime-reduction.md` run `scripts/check-no-em-dash.sh added-lines` over the two Python test modules without an explicit base. Task 3 executes after Task 2 commits those edits, so the default HEAD-to-worktree comparison no longer covers Task 2 insertions. The command may pass while a committed insertion violates the text rule.

The testing worker in the 2026-11-06 test-suite-runtime-reduction plan review reproduced the distinction in a temporary repository: after committing an em dash, the default-base scan exited 0 and the scan against the preceding revision exited 1. This is Low, non-blocking certification overflow; the plan's regression and benchmark obligations are not invalidated.

## Correction

At the next natural plan update, bind the insertion scan to the execution baseline captured before Task 2 rather than the current HEAD; keep the changed-file scope and avoid scanning unrelated historical lines. Verify both a committed violating insertion and a clean insertion, and retain a clean legacy line outside the changed range. Use the normal plan edit/review lifecycle; do not silently mutate certified bytes.

Dedup probe: searched open backlog for added-lines, scan base, committed insertions and plan-validation grep needles. The existing plan-validation-grep-needles item concerns nondiscriminating text needles, not a changed-line scan whose baseline omits an earlier task commit.
