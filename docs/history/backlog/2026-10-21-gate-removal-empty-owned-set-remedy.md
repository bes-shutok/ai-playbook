# Backlog: gate-removal empty-owned-set refusal keeps the unattainable migrate remedy

- **Filed:** 2026-10-21, Task 1 intermediate review of `gate-removal-closeout-accounting`
- **Status:** covered (docs/history/plans/2026-10-27-gate-removal-empty-owned-set-remedy.md)
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-10-26-plan-authoring-stand-down-before-charter.md (same gate-removal surface; this row covers an existing plan with no owned review claims)
- **Origin class:** unremediable refusal remedy
- **Class:** fix-class
- **Driving force:** correctness; secondary: code-quality
- **Skill/step:** `scripts/worktree_closeout_migrate.py` gate-removal empty owned set (around line 1204)
- **Cluster:** docs/history/backlog/completed/2026-10-07-gate-removal-unremediable-refuse-deadlock.md; docs/history/backlog/completed/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md
- **Dedup probe:** third arm of the same never-attainable-remedy shape the plan's Task 1 item 3 removed for citation refusals; deliberate scope-out recorded in the task-1 implement log.

## Problem

With no header citations and no --claims, gate-removal refuses with an empty owned set and prints the capture-and-migrate remedy, yet no migrate run can add a header citation; the attainable repair is adding the citation or passing --claims.

## Expected

Give the empty-owned-set refusal its own attainable remedy line, mirroring the citation/claims remedy split landed by the gate-removal-closeout-accounting plan.

## Witness 2026-10-27: the ad-hoc-run shape has no first-class input form

An ad-hoc maintenance run (no plan file exists) closing out its worktree hit the same input-shape presumption from the other side: the gate-removal owned-set extraction reads its citations from the `--plan` file, so the run had to pass a label-less review record as `--plan` (contributing no citations) beside a `--claims` file listing the run's review-record paths, and the `--branch`/`--worktree` mutual exclusion forced two invocations (worktree mode for the removal command, branch-only mode with `--migration-manifest` for the branch record). The workaround is deterministic but improvised per run; a documented ad-hoc invocation shape in the command's help, or `--claims`-only admission when no plan exists, would remove the improvisation. Priority: low re-affirmed (the workaround is safe and bounded; the cost is per-run improvisation, not a wrong result).
