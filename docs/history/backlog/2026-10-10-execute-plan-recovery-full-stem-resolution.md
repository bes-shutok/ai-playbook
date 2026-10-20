# Backlog: bind out-of-scope plan recovery to the manifest's full plan path

- **Filed:** 2026-10-10, Task 1 done-pending recovery
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed recovery blocker
- **Class:** fix-class
- **Cluster:** docs/history/backlog/2026-10-05-execute-plan-reviewed-scope-recovery.md; docs/history/backlog/2026-10-09-execute-plan-live-claim-scope-widening.md; docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md (shared surface: execute-plan scope and recovery transitions)
- **Driving force:** reliability + recoverability
- **Skill/step:** `agents/skills/execute-plan/runtime-contract.md`, “Out-of-scope plan-edit disposition”; `scripts/execute_plan_runtime.py`, `recover_out_of_scope_plan_edit`
- **Severity:** high; the sanctioned recovery operation can reject before considering its documented edit classes because it resolves a date-prefixed plan path as `<plans_dir>/<plan_slug>.md`.

## Problem

When a task's done handoff rejects a reviewed plan edit as out of scope, `recover-out-of-scope-plan-edit` derives the plan path from the facts-resolved plans directory plus `manifest.plan_slug`. Execute-plan manifests record the canonical artifact slug without the date prefix, while plan files use date-prefixed filenames. The recovery therefore looks for a nonexistent path and refuses with a full-stem identity mismatch, even when the task, claim, commit, and live plan are otherwise correctly bound. This strands the task in `done-pending`; the documented recovery receipt cannot be recorded.

## Evidence

- Plan: `docs/history/plans/2026-10-10-plan-scope-gist-surface.md`, Task 1.
- The task commit was rejected with `out-of-scope committed change: docs/history/plans/2026-10-10-plan-scope-gist-surface.md`.
- Invoking the documented `recover-out-of-scope-plan-edit` operation with the live task identity and commit returned `precondition-unverified`: it resolved `docs/history/plans/plan-scope-gist-surface.md`, which does not match the manifest's `plan_slug` `plan-scope-gist-surface` by full-stem identity.
- The plan file and ready r6 review record exist under their date-prefixed canonical paths. No runtime manifest fields were edited.
- Repeat observation 2026-10-10, generation 9: a temporary symlink at the resolved slug path (`docs/history/plans/plan-scope-gist-surface.md` -> the date-prefixed plan) passed the full-stem lookup, but recovery then refused because checkbox edits made after review r9 left its sidecar `source_digest` stale. Thus the alias is only a lookup workaround; recovery also requires a fresh ready review over the current plan bytes. The symlink is temporary and must not be committed.

## Expected

Persist or derive the full plan path as a distinct identity, then make the recovery operation consume that identity through the same facts-resolved path policy used by create, readiness, and preflight. Preserve the review-ready and checkbox-only edit-class fences, commit identity binding, and refusal immutability. Add coverage for date-prefixed single-file plan names and directory-form plan runs.

## Repeat observation (2026-10-11)

The same date-prefixed plan identity mismatch blocks `recover-requeued-task-scope` after Task 1 was requeued to refresh verifier evidence: the operation searches for `docs/history/plans/plan-origins-coverage-parse.md` although the reviewed plan is `docs/history/plans/2026-10-10-plan-origins-coverage-parse.md`. It refuses before a receipt or manifest write. The documented temporary symlink workaround from the prior observation is being applied in the execution worktree; it remains uncommitted and must be removed after the run's runtime needs end. A ready review for the exact plan digest already exists, so this attempt does not rely on stale review evidence.
