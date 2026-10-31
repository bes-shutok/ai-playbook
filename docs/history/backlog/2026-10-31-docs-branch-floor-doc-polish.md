# docs-branch floor: doc polish residuals (code-review r1 F3/F4)

- Class: IMPLEMENTATION_REQUIRED
- Driving force: simplicity
- Origin: execute-plan Phase 3 code-review r1 (non-blocking Low), plan docs/history/plans/2026-10-28-docs-branch-supported-python-runtime.md
- Record: .ai-playbook/reviews/2026-10-31-docs-branch-supported-python-runtime-code-review-r1.md

## Findings
- F3: the plan's Edge-cases prose still says a missing python3 fails with the shell's existing error; the landed wrapper emits an explicit actionable diagnostic (strictly stronger). Drop the stale clause when the plan is next touched.
- F4: agents/skills/docs-branch/SKILL.md leaves `python3` and PATH unbackticked (byte-budget forced) and "This backend" now resolves via the Core Concepts bullet. Restore backticks / antecedent on the next substantive edit of the file (net byte growth is acceptable then).
