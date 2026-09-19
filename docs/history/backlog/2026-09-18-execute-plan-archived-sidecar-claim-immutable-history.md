# Backlog: unqualified "driver never reads review sidecars" claim in archived completed plan

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-18
Class: archived history artifact, superseded contract claim

## Problem

The archived completed plan
`docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md` (its
historical context, folded from review round 1's dropped-items list) carries
an unqualified claim that "the driver never reads review sidecars". The
Phase 3 staged-terminal work made that claim false as a current statement:
the terminal gate reads the clean-round sidecar as the only documented
extension. Living surfaces (SKILL.md, runtime-contract.md) are already
amended; the archived copy is not.

## Location

`docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md`, terminal /
sidecar passage.

## Suggested direction

Recommend accept-as-immutable-history: completed plans are frozen context
(per doc-hierarchy document states); do not edit the archived body. The
superseded-by note is this item: the current contract owner is
`agents/skills/execute-plan/runtime-contract.md` ("Staged terminal operation
(archive gate)" plus the readiness section's scoped sentence). Close this
item on acceptance without touching the archived file.

## Severity and source

Low; staging doc
`docs/reviews/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety-code-review-r1.md`,
round 1, finding CD-5.

## Why not fixed now

Editing archived completed plans is excluded by the document lifecycle; the
finding is recorded as the superseded-by note instead. Deferred by the round
1 address-pass disposition.
