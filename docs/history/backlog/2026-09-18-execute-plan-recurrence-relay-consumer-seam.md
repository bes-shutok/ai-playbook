# Backlog: recurrence relay is a seam without a consumer

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-18
Class: execute-plan Phase 3 recurrence mechanics, prescribed design residual

## Problem

The plan prescribed a relay seam: the done sub-agent must relay the
`recurrence_groups` trigger status verbatim
(`agents/skills/execute-plan/subagent-prompts.md` "Done (per review iteration)"
required output) and the parent records it against the
`recurrence_groups` line (`agents/skills/execute-plan/SKILL.md` Step 3.4).
The relayed value is recorded but no downstream step consumes the relayed
copy: Step 3.2 and Step 3.5 re-read `manifest.md` directly. The seam is a
prescribed-by-plan design residual, not a defect; it adds one required output
whose only effect is redundancy.

## Location

- `agents/skills/execute-plan/subagent-prompts.md`: "Done (per review
  iteration)" Context block and required-output rule.
- `agents/skills/execute-plan/SKILL.md`: Step 3.4 recording clause.

## Suggested direction

Either (a) drop the relay requirement and let the parent read the line from
`manifest.md` at Step 3.5 as before, or (b) make a consumer real: have Step
3.5's first action verify that the recorded relayed status matches the
`recurrence_groups` line and refuse on mismatch (a tamper check between
sub-agent observation and parent recording). Decide when Phase 3 recurrence
mechanics are next touched.

## Severity and source

Low; staging doc
`docs/reviews/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety-code-review-r1.md`,
round 1, finding D-3.

## Why not fixed now

The seam is prescribed by the executed plan's Task 3 (the design decision is
not this round's to reverse); deferred by the round 1 address-pass
disposition.
