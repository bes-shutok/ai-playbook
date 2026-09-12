# Backlog: ambient-noise pattern trim (YAGNI) vs plan Task 3 allowlist definition

Status: open
Workflow: backlog
Source: 2026-09-10-execute-plan-runtime-residuals code review r2, finding F-r2-12 (design-simplicity, Low), deferred by the review round's triage
Severity: Low (blocked by the plan's Task 3 allowlist definition)
Scope: scripts/execute_plan_runtime.py

## Problem

`AMBIENT_NOISE_PATTERNS` (scripts/execute_plan_runtime.py) carries editor
swap/lock patterns (`.#*`, `#*#`, `*.swp`, `*.swo`, `*.swpx`, `*~`) that have
not yet been observed in this workflow. Only the `.DS_Store` family has
observed evidence. Trimming the unobserved patterns would be a YAGNI
simplification of the allowlist, but the plan's Task 3 explicitly defines the
allowlist as ".DS_Store and editor-swap patterns", so trimming contradicts
the plan as written.

## Suggested fix

Only with a plan amendment: trim `AMBIENT_NOISE_PATTERNS` to the observed
`.DS_Store` family (`.DS_Store`, `.DS_Store?`, `._.DS_Store`) and update the
plan Task 3 allowlist definition plus the runtime-contract ambient-noise
paragraph and the `cleanup-required` transition-table row in the same pass.
Revisit only if editor-swap noise is actually observed (keep) or the plan is
amended (trim).

## Why not fixed now

The trim contradicts the plan's Task 3 allowlist definition, which the
review round's scope did not authorize amending. Deferred by the r2 triage
(review doc
`docs/reviews/2026-09-10-execute-plan-runtime-residuals-code-review-r2.md`,
Triage outcomes section).
