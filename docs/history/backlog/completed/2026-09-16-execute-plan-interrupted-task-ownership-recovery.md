# Backlog: preserve execute-plan task ownership across interruptions

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-16
Class: execute-plan interruption recovery and task ownership

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Problem

When an implementation task is interrupted, the orchestration layer can lose
the distinction between a cancelled wait, a still-running worker, a worker that
returned without completing the task, and a genuinely abandoned claim. If those
states are handled alike, recovery may launch duplicate work, discard valid
ownership, rerun a whole-plan readiness review unnecessarily, or mark progress
from an incomplete worker receipt.

The task claim, the human plan checkbox, the runtime manifest, and the worker
evidence must remain correlated until the task reaches a committed checkpoint.
An interruption is a state transition, not proof of failure or completion.

## Sanitized witness

During a resumed plan execution, the wait for an implementation worker was
interrupted by new user input. The worker itself remained live, but the
orchestrator had to determine whether the wait had been cancelled or the worker
had stopped. Earlier recovery also exposed a plan/manifest disagreement and a
runtime path that could not advance a task without the configured adapter.

The safe next action was to inspect the same worker and preserve its claim. A
new worker or a new whole-plan readiness review would have created duplicate
work and more noise without changing the plan digest or the valid parts of the
runtime state.

## Root-cause classification

**Principle:** Family E (temporal / ordering invariants), with Family D (single
source of truth) and Family H (verify the real thing, not the abstraction) as
secondary families.

**Shape trigger:** an asynchronous worker owns a stateful unit of work while the
controller can be interrupted, resumed, or receive new input before the worker
returns.

**General form:** model interruption separately from cancellation, failure, and
completion. Preserve the ownership token and task identity while the worker is
observable; reclaim only after durable evidence proves that the prior owner is
gone or its lease is expired. Reconcile the task receipt with the plan and
runtime state before advancing or retrying.

## Required behavior

### Live worker

- Interrupting a wait must not cancel or duplicate the worker unless cancellation
  was explicitly requested and the worker API confirms cancellation.
- The controller must wait on the same worker handle, using a bounded wait that
  can be repeated after user input.
- The task claim, generation, owner, and next action remain unchanged while the
  worker is live.

### Returned worker

- A worker receipt records only what the worker actually returned. It does not
  mark the plan checkbox, commit a task, or advance the next-task pointer by
  itself.
- The controller must inspect the task log, diff, tests, and claim before
  deciding whether to checkpoint, retry, enter recovery, or hand off to `done`.
- A failed, partial, timed-out, or adapter-blocked return remains resumable and
  names one concrete next action.

### Reclaim and retry

- Reclaim an active task only after the runtime can prove that its previous
  owner is no longer live or that its lease has expired under the declared
  protocol.
- A stale or malformed manifest must enter recovery and cannot be repaired by
  guessing from a summary.
- A retry must preserve the plan digest and task identity, and must not silently
  restart completed tasks.
- If the plan digest, manifest validity, review scope, and unresolved-finding
  state are unchanged, interruption recovery must use direct continuation. The
  conditional readiness item is the authority for when a new readiness review is
  required.

## Skill and harness ownership

- `execute-plan` owns the interruption state table and the decision to observe,
  checkpoint, retry, reclaim, or enter readiness recovery.
- The runtime manifest/claim helper owns generation, owner, lease, and atomic
  state transitions.
- The worker adapter owns cancellation and liveness semantics and must expose
  enough state for the controller to distinguish a cancelled wait from a dead
  worker.
- `done` owns commit finalization only after the task has a reconciled
  checkpoint; it must not infer completion from a worker receipt.
- Any hook may reject an unsafe transition, but all components must use the same
  task-state predicate rather than maintaining a second recovery policy.

## Acceptance criteria

1. A cancelled wait followed by user input observes the original worker and does
   not launch a duplicate worker for the same claim.
2. A live worker keeps its claim and task identity until it returns or an
   explicit cancellation is confirmed.
3. Worker outcomes distinguish completed, partial, failed, timed-out, cancelled,
   and adapter-unavailable states, each with a resumable next action where
   applicable.
4. A worker receipt cannot advance a plan checkbox or task pointer without
   matching diff, verification, and runtime-claim evidence.
5. Reclaim requires proven owner loss or lease expiry and is covered by a
   deterministic regression test.
6. Interruption recovery does not repeat a whole-plan readiness review when the
   plan digest and runtime/review state remain valid.
7. Digest drift, manifest disagreement, unresolved findings, and unknown next
   task enter the conditional readiness or recovery path instead of direct
   continuation.
8. The implementation, fixtures, logs, and documentation contain no
   repository-specific identifiers, personal data, internal URLs, secrets, or
   environment names.

## Why this is high priority

Duplicate workers and guessed recovery state can corrupt task ownership and
produce misleading progress. Treating every interrupted wait as a new planning
event also adds repeated review work, reduces liveness, and encourages unsafe
manual bypasses.

## Related backlog items

- `2026-09-16-execute-plan-conditional-readiness-gate.md` defines when direct
  continuation is valid and when readiness review is required.
- `2026-09-16-execute-plan-review-evidence-and-manifest-gate.md` covers exact
  plan bytes, manifest projections, and verification evidence lineage.
- `2026-09-16-execute-plan-terminal-completion-integrity.md` covers the shared
  terminal predicate and prevents non-terminal states from being reported as
  complete.
