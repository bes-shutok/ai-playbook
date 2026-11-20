# Backlog: execute-plan has no sanctioned lane for a read-only verification plan

Status: covered (docs/history/plans/completed/2026-11-19-execute-plan-read-only-verification-lane.md)
Workflow: backlog
Priority: high
Origin class: self-serving
Class: skill-text
Driving force: simplicity
Skill/step: `agents/skills/execute-plan/run-setup.md` (Phase 0) and `agents/skills/execute-plan/implementation-loop.md` (Phases 1 to 3)
Severity: low
Source reference: execute-plan run, 2026-11-17, Claude Code runtime.

## Problem

A plan whose tasks are all read-only checks (no `Files:` edits, no tracked change until the completion pass) still faces the full run contract: a worktree under the `worktrees` policy, an execution claim, one worker per task, an intermediate review per task, a light boundary commit per task, and a Phase 3 review panel. The run took a reduced path by judgment (primary checkout, no claim, no workers, no panel) and disclosed it. The skill gives no rule that says which of these duties apply when no task changes a tracked file, so the choice was unreviewed and a later archive guard refused the first commit for a missing exec-review pointer record that the full flow would have written.

## Expected

The skill names a read-only verification lane: which Phase 0 and Phase 3 duties stay, which are vacuous, and which record the completion pass must still write before the archive commit (the exec-review pointer with the archived plan digest).

## Suggested fix

Add a short paragraph to execute-plan that defines the lane by its observable condition (every task's `Files:` list is "none" and no task edits a tracked path) and lists the retained duties: readiness gate, session manifest, the plan-file marker, the plans-egress pointer record, the archive-egress check. State that no review panel runs because no code diff exists, and that the exec record says so.

## Evidence and orientation

- Witness: a three-task plan with every `Files:` entry "none" ran its tasks inline, then hit `reverse_squash_guard.py check-archive` refusing the archive commit ("missing evidence leg: exec-review record"). The record was written afterwards and the commit redone.
- `agents/skills/execute-plan/archive-and-cleanup.md`, Phase 4: documents the plans-egress pointer record but only as part of the full flow.

## Rejected alternatives

- Treat the plan as a manual or read-only run: rejected because the operator invoked execute-plan and the archive still needs the execute-plan completion evidence.

## Why not fixed now

Changing the execute-plan contract is outside the executed plan's scope, which forbade edits to shared skills.
