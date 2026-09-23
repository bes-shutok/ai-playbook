# execute-plan: codex adapter "Evidence verifier" section understates the new coverage-completeness obligation

- Status: open
- Priority: Low
- Area: execute-plan
- Driver: Phase 3 review r1 finding 2 of the 2026-09-22-execution-integrity-worker-evidence execution (2026-09-23)
- Driving force: runtime-contract.md "Worker execution contract" principle 3 now carries the completeness obligation (coverage must be complete across the implement-owned acceptance criteria; an omitted criterion is a malformed receipt), but `agents/skills/execute-plan/runtime-adapters/codex.md` "Evidence verifier" (~lines 154-166) restates the acceptance conditions as the seven envelope items without that clause, so the adapter's restatement now understates the contract SOT and can drift further.

## Findings

- Not a contradiction today: the adapter states necessary conditions ("accepts ... only when"), and the contract adds one at the SOT layer; adapter verifier semantics are owned by the separate runtime implementation plan (runtime scripts out of the executing plan's scope).
- The surface was absent from the executing plan's Review Scope, so it was deferred rather than fixed in-task.

## Suggested fix

Either extend the adapter's Evidence verifier list with the completeness clause (mirror wording from the contract), or replace the list with a pointer to contract principle 3 so the mirror cannot drift. Touch runtime-contract parity tests only if the adapter text is asserted there; run the pins suite after.
