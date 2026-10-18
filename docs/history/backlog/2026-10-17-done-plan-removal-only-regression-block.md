# Backlog: done rejects reviewed removal-only edits to the active plan

- **Filed:** 2026-10-17, framework-callback-readability-and-review-scope Task 1 closeout
- **Status:** covered (docs/history/plans/2026-10-17-dirt-gate-removal-only-cleanup-passing.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed closeout blocker
- **Class:** fix-class
- **Driving force:** reliability (reviewed task commits can complete) + simplicity (remove content without replacement prose)
- **Skill/step:** `scripts/dirt_regression_gate.py`; `agents/skills/done/SKILL.md` Step 3
- **Environment:** local execute-plan worktree, Task 1 done boundary
- **Related origin:** `docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md`

## Problem

The Task 1 changes to the active plan were reviewed and intentionally removed obsolete task-log paths, their primary-class anchors, and a redundant audit criterion. The done commit gate refused the plan with `dirt REGRESSION: ... (restores base-era text over lines HEAD gained since 2fa5d5eadd57)`. The classifier treats a removal-only hunk as regressing because it removes a line gained since the merge base and the “all added lines are base text” condition is true for an empty added-line set.

The gate's comparison is useful for catching a restoration of base-era text over branch additions, but these plan edits restore no base-era text. The task's guide edits passed their validations and focused review; the plan is the sole refusal surface. A previous open item records the same removal-only false positive for within-file documentation edits, and a prior probe found that adding a concise, useful replacement statement in the same rewritten section passes, at the cost of replacement prose.

## Expected

The done boundary should allow reviewed, intentional removal-only edits to branch-added documentation while preserving detection of actual base-era restorations over branch-added content. Authors should not need to retain or invent prose solely to make a removal pass.

## Suggested direction

Plan a narrow correction to the classifier or its input contract that distinguishes pure removal from restoration of base-era text. Preserve the witnessed accidental-reversion protection and test both shapes. Evaluate an explicitly declared removal signal only if classifier narrowing cannot preserve that protection; any new approval mechanism must meet the machinery admission protocol and must not create a more frequent closeout refusal.

## Evidence

- The current Task 1 refusal names the plan file and reports `restores base-era text over lines HEAD gained since 2fa5d5eadd57`.
- `scripts/dirt_regression_gate.py`, `_hunk_is_regression`, returns regression when a removed line is HEAD-gained and every added line occurs in the base; for an empty `added` list, `all(...)` is true.
- `docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md` records a prior within-file documentation removal refusal and the replacement-prose workaround.
- `docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md` only excludes declared paths absent from the worktree; it leaves the classifier unchanged for present files, so it does not cover this case.

Cluster: docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md
