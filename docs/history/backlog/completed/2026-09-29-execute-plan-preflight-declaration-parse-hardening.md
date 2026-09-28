# Backlog: Preflight task-declaration parse hardening (duplicate and remaining ambiguous `Files:` shapes)

Driving force: code-quality
Status: done (2026-09-30; executed by plan completed/2026-09-29-execute-plan-seed-readiness-prelaunch-recovery.md, landed main 2f108210, impl review r1 zero blocking)
Priority: medium
Origin: Step 1.2b intermediate review, task 1 of docs/history/plans/2026-09-29-execute-plan-worker-lifecycle-and-scope-recovery.md (round 3 focused re-review; convergence stop after two focused fixes landed)

## Concern

The Task 1 structured-declaration parser (`_plan_declared_files` in `scripts/execute_plan_runtime.py`) now refuses malformed entries and present-but-empty or missing declarations with non-empty seeded scope, but a task section carrying TWO exact `Files:` lines still compares only the first list: an out-of-scope path in a second declaration escapes the preflight drift comparison (Step 1.2b finding, Medium, blocking, plan-related).

## Acceptance

- Preflight refuses (named problem) when a task section carries more than one `Files:` heading, or otherwise cannot produce one unambiguous structured declaration.
- Any further ambiguous-shape edges found while implementing (entry-line lookalikes before the heading, indented pseudo-headings) are refused or handled with an explicit named decision, never silently truncated.
- Regression tests cover the duplicate-heading refusal and each newly handled shape; the full runtime suite passes; preflight stays read-only on refusal.
