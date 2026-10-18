# Backlog: execute-plan-normative-example-review certification residuals

- **Filed:** 2026-10-13, plans authoring certification (r3 terminal)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** certification residual (non-blocking review findings)
- **Class:** fix-class
- **Skill/step:** `docs/history/plans/2026-10-13-execute-plan-normative-example-review.md` (plan bytes); `agents/skills/review-agents/documentation.md` and `scripts/test_review_agent_normative_example_selection.py` (the planned surfaces)
- **Cluster:** the executed plan docs/history/plans/completed/2026-10-13-execute-plan-normative-example-review.md (both origin rows pruned at the execution landing)

## Residuals

- r3 F1: the plan's Terms define `Boundary exception` but no operative text uses the term after the r1 fold moved the exception wording to the every-tier sentence; the landed plan bytes carry an unused glossary entry.
- r3 F2: the plan's Gate delta claims "Nothing is removed" and the witness suite freezes review-panel-selection.md's rows and Boundary paragraph, but no witness pins the preserved lines of documentation.md (the Normative example replay section's existing bullets), so an executor edit could silently drop preserved text on the second target file without a test failing. When the plan executes, extend the witness suite with a frozen-span pin over documentation.md's preserved replay-section lines.
- Carried context (r2 overflow, pre-existing, not fold-introduced): overlap between documentation.md's general inventory boundary (full execution impractical) and the new runnable-example fallback; both readings are safe and the boundary bullet stays unchanged by this plan.

## Why not fixed now

Non-blocking findings at the certification round never force a fold; the certification residual contract files consequence-bearing residue durably instead. Neither residual changes an executable task's behavior contract: the unused term is plan-bytes hygiene, and the missing documentation.md pin is an execution-time test addition inside the planned suite.

## Source

- Review series docs/history/reviews/2026-10-13-plan-review-execute-plan-normative-example-review-r1.md through -r3.md (untracked reviews corpus); certification seal docs/history/review-certs/execute-plan-normative-example-review.md.
