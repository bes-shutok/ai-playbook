# Backlog: fix coverage-contract attempt-loop variable shadowing in the review staging validator

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-16
Class: review staging validator defect (captured during plan review r3 of the execute-plan integrity quad authoring run)

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Problem

The review staging validator's coverage-contract check loops over coverage
attempts and assigns the loop-local attempt outcome to the same variable name
that later holds the coverage-level outcome. After any attempt is evaluated,
the coverage-level check reads the last attempt's outcome instead of the
coverage outcome, so a verdict-yes sidecar that legitimately carries an
attempts list spuriously fails with a verdict/outcome mismatch naming the
attempt outcome value.

Producers currently work around it by omitting the attempts array from
sidecars, which also drops the attempt telemetry the schema exists to carry.

## Root-cause classification

**Principle:** Family C (naming and shadowing) with Family D (single source of
truth) as secondary: one variable name is reused for two scopes, so the
coverage-level truth is overwritten by loop-local data.

## Required behavior

- Rename the loop-local outcome variable inside the attempts loop so the
  coverage-level outcome survives the loop.
- Add regression fixtures: a verdict-yes sidecar with a non-empty attempts
  list whose attempts carry their own outcomes passes the coverage contract;
  a verdict-yes sidecar with a coverage outcome that genuinely mismatches the
  verdict still fails.
- Confirm no other loop in the validator reuses an enclosing scope's variable
  name for its own assignment (same-family sweep).

## Acceptance criteria

1. The shadowing is fixed and the validator's coverage-contract check reads
   the coverage-level outcome after the attempts loop.
2. A sidecar with attempts telemetry passes the hard validation when the
   coverage contract genuinely holds.
3. Negative fixtures still fail (genuine verdict/outcome mismatch, missing
   coverage fields).
4. The fix contains no repository-specific identifiers, personal data,
   internal URLs, secrets, or environment names.

## Why this is high priority

The workaround (omitting attempts) silently removes attempt telemetry from
review records, weakening the coverage evidence the schema was built to
carry; and any future producer that includes attempts fails validation
incorrectly, blocking unrelated review work.

## Related backlog items

- Captured from the execute-plan integrity quad authoring run's review panel
  (r3 tooling defect note; r4 and r5 re-verified the workaround shape).
