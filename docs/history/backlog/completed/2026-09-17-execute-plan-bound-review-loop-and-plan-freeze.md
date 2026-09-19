# Backlog: bound review loops and freeze executable plans

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-17
Class: execute-plan review liveness and plan freeze

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Problem

A readiness review can become an unbounded loop when every review correction
changes the plan digest and automatically requires another whole-plan review.
The workflow loses implementation liveness and spends review budget on changes
that do not affect the next task.

## Required behavior

After a conditional readiness review passes for a digest, freeze the executable
plan for ordinary task progression. Do not run another whole-plan readiness
review between sequential tasks when the digest, runtime manifest, ownership
ledger, and review scope remain valid.

During the frozen period, allow only bounded corrections that do not add
behavior or scope, such as a verified path, selector, ownership, or wording
repair. If a correction changes behavior, task order, ownership, evidence
class, or release scope, enter a named plan-change recovery path.

The skill must maintain separate budgets for readiness reviews, implementation
workers, code-review and fix rounds, and plan edits caused by review findings.
When a budget is exhausted, the workflow must report the exact state and create
or update a backlog item instead of silently continuing the loop.

## Acceptance criteria

1. One clean readiness review permits direct Task N to Task N+1 progression.
2. A digest change invalidates the prior review exactly once and starts a
   bounded recovery review.
3. Non-semantic corrections do not restart a whole-plan review after the
   current readiness result is accepted.
4. Semantic scope changes require explicit re-readiness and show the changed
   sections.
5. Review rounds and plan-edit rounds have independent, testable caps.
6. The controller reports why it continued, resumed, paused, or entered
   recovery.
7. Regression tests cover clean continuation, interrupted implementation,
   semantic plan change, repeated non-semantic edits, and exhausted budgets.

## Prevention

The readiness decision must be based on the exact current digest and runtime
state, but the policy must not treat every status update or implementation
interruption as a new planning event. A review should prove executability, not
serve as an ongoing design forum.
