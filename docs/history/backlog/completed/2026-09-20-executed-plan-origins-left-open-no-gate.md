# Backlog: execution closeout leaves plan origins open (no mechanical gate)

Status: done (delivered by docs/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-gates.md, executed 2026-09-22)
Priority: high
Workflow: backlog
Date: 2026-09-20

## Problem

The execution archive step prescribes moving backlog origins to `completed/` with
`Status: done`, but nothing verifies it, and recent executions archived their plans
while leaving origins open at the top level. A manual sweep on 2026-09-20 closed six
such items on main (commit `eff584c9` plus status-line fixes): all four origins of the
executed docs-branch-sync-and-worktree-lifecycle plan, the park-guard plan's origin,
and one already-dispositioned item that stayed in the open survey. An open origin whose
covering plan has archived reads as plan-uncovered to the maintenance survey (the
coverage grep only scans top-level plans), so the authoring lane will author a
duplicate plan for work already delivered - the exact waste the coverage rule exists
to prevent.

## Observed vs expected

Observed: three executions (park-guard, docs-branch-sync-and-worktree-lifecycle,
batch-2-phase-2) archived their plans; the first two left 5 origins + 1 dispositioned
item open at the top level, discoverable only by a manual grep of archived plans for
open-item basenames. Expected: the archive step verifies every name in the plan's
"Backlog origins (scope of record)" block has left the top level before the archive
commit lands, and the maintenance survey (Step 1) or a done gate flags any open item
whose basename appears in an archived plan's origins block.

## Expected behavior (mechanical shape)

A small check in the execute-plan archive step (and mirrored as a warn in the
maintenance survey): parse each archived plan's origins block, verify each named item
sits under `completed/` (or carries a closed/done status), and fail or warn listing
the stragglers. Same warn-and-continue posture as the sibling optional gates.

## Suspected root area

`agents/skills/execute-plan/SKILL.md` (archive step has no verification arm);
`agents/skills/maintenance/SKILL.md` Step 1 (survey counts plan-uncovered without
consulting archived plans' origin blocks); execution payload blueprints in
`agents/skills/maintenance/prompt-templates.md` (archive instruction is prose-only).
Environment: repo-local skills checkout, 2026-09-20; witness commits `eff584c9`,
`7cde8871`, `225186a0` on main.
