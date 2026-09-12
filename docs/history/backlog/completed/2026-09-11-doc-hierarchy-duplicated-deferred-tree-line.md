# Backlog: delete duplicated plans/deferred/ tree line in doc-hierarchy SKILL

Status: done (fixed 2026-09-12 by commit 4cdc79a: deleted the second duplicated tree line; hygiene scan exit 0)
Workflow: backlog
Source: 2026-09-10-execute-plan-runtime-residuals code review r1, finding contract-docs-3 (contract-docs, Low); owned by the deferred-plans-parking convention session (peer)
Severity: Low
Scope: agents/skills/doc-hierarchy/SKILL.md

## Problem

`agents/skills/doc-hierarchy/SKILL.md` (around lines 69-70) duplicates the
`plans/deferred/` tree line: the same directory appears twice in the
documented layout tree.

## Suggested fix

Delete one of the two duplicated `plans/deferred/` tree lines. No other
content depends on the duplication.

## Why not fixed now

The file is owned by the peer deferred-plans-parking convention session
working the same shared branch; editing it here would create cross-session
file contention. Left for that session; the fix is a one-line deletion.
Deferred by the r1 triage (review doc
`docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r1.md`,
triage summary section).
