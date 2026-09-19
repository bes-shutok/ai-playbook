# High priority: Align execute-plan worker deadlines with the worker contract

## Problem

The execute-plan runtime adapter can apply a launch or wait deadline that is
shorter than the worker contract. A repository worker is authorized to
implement a task, run validation, append its execution log, and return a
structured result. A valid worker or review panel can therefore be terminated
during ordinary work, including a review that legitimately needs more than
five minutes, and be recorded as a runtime timeout. The parent then stops at a
false infrastructure blocker instead of resuming the claimed task.

## Prevention

Keep launch, worker wait, panel, address-pass, and done deadlines explicit,
bounded, and owned by the runtime package. The normal defaults must cover the
actual contract, not an arbitrary short host default such as 30 seconds or
five minutes, while remaining finite. Adapter tests must exercise legitimate
work longer than each former short default and must verify that timeout
evidence is preserved. The driver must distinguish a genuine deadline expiry
from a malformed host result, and recovery must require verified process
termination before a claim is reopened. A timed-out claim must never be
treated as successful merely because the repository happens to contain a
prior implementation log.

## Required follow-up

1. Choose and document a cross-runtime baseline for launch and wait deadlines.
2. Add a hermetic adapter test for the baseline and a bounded timeout case.
3. Add a recovery witness showing that a terminated timeout can be reconciled
   without a duplicate worker launch.
4. Ensure the host adapter returns a structured result before the deadline or
   fails closed with actionable evidence.
5. Add a review-panel witness whose runtime exceeds five minutes but remains
   within the configured panel deadline, proving that ordinary review work is
   not classified as a timeout.

## Scope

This is project-agnostic execute-plan runtime hardening. It does not authorize
changes to any product repository, deployment, external system, or worker
implementation.

## Boundary with the interruption inventory

This item owns deadline sizing and timeout classification. The related
`2026-09-17-execute-plan-interruption-root-cause-inventory.md` owns the broader
state machine, capacity waiting, user-input interruption, readiness routing,
inclusion classification, and terminal evidence. Fixing the deadline alone is
not completion of the interruption problem.
