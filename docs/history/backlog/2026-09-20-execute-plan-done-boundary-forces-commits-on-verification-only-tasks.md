# Backlog: done boundary requires a provable commit identity even for verification-only tasks

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-20
Class: execute-plan runtime driver / contract gap (observed 2026-09-20 batch-2 phase-2 tasks 1 and 6)

## Problem

The driver's done boundary fails closed with `commit-pending` ("commit not
found") unless `commit_identity` matches a HEAD-reachable commit message
(`git log -F --grep`). Plans whose tasks are read-only verification gates
(no `Commit:` line, nothing to commit - e.g. batch-2 phase-2 Task 1 drift
gate and Task 6 final sweep) still have to satisfy it. The only way through
observed in practice was manufacturing checkbox-flip commits
("docs: ... task N checkboxes" / "chore: ... final sweep"), which conflates
"verification passed" with "content changed" and pollutes history.

## Suggested direction

Accept a documented no-commit justification shape for tasks with no
`Commit:` line and a clean worktree (e.g. `commit_identity: "none"` plus
clean-state and log evidence) instead of requiring a findable commit;
alternatively pin the convention that checkbox-flip commits ARE the
per-task commit for verification-only tasks (and say so in the Done prompt
template), so it is a rule rather than an improvisation.

Evidence: batch-2 phase-2 run, 2026-09-20, task-1 and task-6 done receipts.
