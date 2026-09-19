# Backlog: enforce one authoritative state machine and task ownership

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-17
Class: execute-plan plan consistency and ownership

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Problem

Complex plans can describe the same state transition, test witness, or file
under different task owners and in multiple competing matrices. Reviewers then
find contradictions late, and each correction changes the digest and triggers
another review cycle.

## Required behavior

The plans workflow must require one authoritative state-transition table per
workflow. Other sections may explain or reference it, but may not introduce a
different normative outcome for the same input.

The plan validator must also enforce:

- exactly one creating task per file and test method;
- later tasks may consume a witness but may not recreate or re-own it;
- every manifest row has one owner, one phase, and one canonical key;
- every task allowed path is present in the owning task file ledger;
- every referenced path and selector either exists or is explicitly marked as a
  planned new file or method;
- task order does not place a consumer before its owning task.

## Acceptance criteria

1. Contradictory outcomes for the same state and input are reported before
   implementation.
2. Duplicate file ownership and duplicate test-method ownership fail readiness.
3. Canonical manifest rows, task projections, and runtime allowed paths are
   cross-validated.
4. A later task can reference a completed witness without creating a second
   ownership record.
5. Regression fixtures cover duplicate owners, nonexistent paths, conflicting
   matrices, and consumer-before-owner ordering.
6. The validator reports the exact task, row, path, or selector that conflicts.

## Prevention

Plan authoring should create the ownership ledger before prose expansion.
Review agents should classify findings as contradiction, executable gap,
documentation gap, or future work. Only contradictions and executable gaps
that block the current task may change the implementation plan.
