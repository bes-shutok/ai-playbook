# Backlog: execute-plan-document-probe-contracts certification residuals

- **Filed:** 2026-10-13, plans authoring certification (r2 terminal)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** certification residual (non-blocking review findings)
- **Class:** fix-class
- **Skill/step:** `docs/history/plans/2026-10-13-execute-plan-document-probe-contracts.md` (plan bytes); `scripts/execute_plan_runtime.py` `verify_preconditions` (the planned artifact-probe change)
- **Cluster:** docs/history/plans/completed/2026-10-13-execute-plan-document-probe-contracts.md

## Residuals

- r2 F1: the plan's backward-compat assumption says three completed plans carry `Predecessors:` blocks; a line-anchored grep finds the block in two (`docs/history/plans/completed/2026-09-13-budget-gate-quota-fixes.md`, `docs/history/plans/completed/2026-09-14-budget-gate-family-residuals.md`) while `2026-09-11-execute-plan-runtime-guardrails.md` mentions the block concept in prose and defines the term without carrying a block line. The no-stranding conclusion is unaffected; the landed plan bytes carry the overcount.
- r2 F2: the empty-string clause shape (malformed) landed in Terms and the Task 1/Task 2 items but not in the plan's Gist edge-cases sentence, and the Evaluation criteria line still says "both malformed shapes" where the enumerated set is three shapes.
- r2 F3: Task 2's malformed enumeration omits the empty `must_not_contain` list; today an empty list is falsy and reads malformed, but a natural `isinstance`-based rewrite could read it as "no forbidden clauses", and no test pins the shape. Both readings are safe; the shape should be pinned when the plan executes.

## Why not fixed now

Non-blocking findings at the certification round never force a fold; the certification residual contract files consequence-bearing residue durably instead. None of the three changes an executable task's behavior contract: the operative task items and validation gates already enumerate the three malformed `contains` shapes, and the unpinned `must_not_contain` shape is an execution-time test addition.

## Source

- Review series docs/history/reviews/2026-10-13-plan-review-execute-plan-document-probe-contracts-r1.md and -r2.md (gitignored reviews corpus); certification seal docs/history/review-certs/execute-plan-document-probe-contracts.md.
