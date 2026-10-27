# Backlog: Safely untrack ignored files through the done runner

- **Filed:** 2026-10-27, consumer workflow failure
- **Status:** covered (docs/history/plans/2026-10-27-done-run-untrack-ignored-path.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-feedback (private consumer)
- **Consumer urgency:** Projects using the shared done workflow need a supported way to remove local-only files from version control without staging their ignored contents; do not defer this as skills-repository-only hardening.
- **Class:** fix-class
- **Driving force:** reliability + efficiency
- **Skill/step:** `agents/skills/done/SKILL.md` commit workflow; `scripts/done_run.sh` commit staging step
- **Dedup probe:** searched the open backlog for `done_run.sh`, tracked ignored paths, and untracking. The closest item, `docs/history/backlog/completed/2026-10-20-ignored-audit-home-paths-force-tracked.md`, addresses preventing ignored audit files from entering the index; this item is distinct because it covers intentional removal of an already-tracked ignored path while preserving its local working copy.

## Problem

The done runner refuses every declared path that matches `.gitignore` before it can distinguish ignored file contents from an index-only deletion. When a consumer needs to stop tracking a local-only file but retain it on disk, `git rm --cached` produces the desired deletion in the index, but `done_run.sh commit --stage <path>` reports the path as ignored and does not land the deletion. The consumer had to move the local files temporarily, alter ignore state during staging, and retry the closeout several times.

## Evidence

- The runner's commit staging loop checks `git check-ignore` before its already-staged-deletion branch (`scripts/done_run.sh`, commit staging section).
- The user-level workflow requires local-only agent files to be untracked and ignored, while also forbidding ignored file contents from being committed.
- In a consumer closeout, the intended final tree omitted the local mirror files and retained their working copies under an ignore rule; a direct index-only deletion path was unavailable.

## Suggested fix

Add a narrow, explicit untrack/deletion path. Accept it only when the path is tracked by `HEAD`, the resulting index entry is absent, and no ignored file contents are staged. Land only the index deletion while preserving the working-tree copy and the existing ignore rule. Add runner tests for the normal tracked-file removal, retained local copy, ignored status, exact resulting tree, and refusal when any ignored blob is staged. Do not broaden the general `--stage` arm or use force-add.

## Why not fixed now

This requires changing and testing the shared done-runner staging contract. The consumer session recovered the local files and completed its closeout; changing the runner during that report-recovery task would have widened the scope.
