# Backlog: sidecar-boundary sentence duplicated within runtime-contract.md

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-18
Class: execute-plan runtime contract, duplicated boundary sentence

## Problem

The sidecar-boundary rule appears twice in
`agents/skills/execute-plan/runtime-contract.md`: once as the closing
"Sidecar boundary:" sentence of the "Staged terminal operation (archive
gate)" section, and again inside the readiness-section sentence "the
readiness operation never reads review sidecars; the terminal gate's
clean-round sidecar read is the only documented extension" (which SKILL.md's
readiness table also quotes verbatim). Two restatements of one rule drift
independently.

## Location

- `agents/skills/execute-plan/runtime-contract.md`: "Staged terminal
  operation (archive gate)" closing sentence; readiness section sentence.
- `agents/skills/execute-plan/SKILL.md`: readiness decision table quoting the
  same sentence.

## Suggested direction

Keep one canonical home (the readiness section's exact wording, which the
validation probes grep for) and reduce the staged-terminal closing sentence
to a pointer ("the sidecar boundary is owned by the readiness section's
sentence above"). Note the probe span dependency: the probes require the
exact sentence in both SKILL.md and runtime-contract.md, so the probe spans
must move with the dedup.

## Severity and source

Low; staging doc
`docs/reviews/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety-code-review-r1.md`,
round 1, finding D-5.

## Why not fixed now

The duplication was introduced by this round's own plan tasks and the probe
spans pin both copies; deferring avoids a same-pass probe-span migration.
Deferred by the round 1 address-pass disposition.
