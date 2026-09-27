# Backlog: P52 Task 1 - region pins do not cover the greenfield skip-discovery and no-invented-keys clauses

- Date: 2026-09-24
- Status: rejected (2026-09-27; pin addition for a hypothetical partial landing)
- Origin: execute-plan Phase 3 r2 testing worker, finding 1
- Driving force: code-quality (secondary: correctness)

## Concern

The Task 1 region pin loop pins the ask, seed literals, directory creation, gitignore spans, and compose-in-either-order, but not the operative clauses `skip discovery for the doc keys` and `persist no invented doc keys`; a partial landing dropping either stays green (measured sweep on HEAD).

## Suggested remedy

When a successor plan next touches the bootstrap greenfield rule, add region pins for both spans to the Task 1 span loop.
