# High priority: eliminate recurring execute-plan interruption loops

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-17
Class: execute-plan liveness, evidence integrity, and recovery orchestration

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or machine path.

## Problem

Long-running plan executions can appear to stop repeatedly even when the
underlying implementation is recoverable. The observed pattern is not one bug;
it is a chain of independent liveness and evidence failures:

1. Worker or reviewer deadlines are shorter than the work contract, so ordinary
   implementation or review is recorded as a timeout.
2. Worker capacity or credits are temporarily unavailable, but the workflow has
   no durable waiting state that resumes the same claim automatically.
3. A partial, local, or fallback review is allowed to stand in for the required
   parent-orchestrated review without preserving the same exit obligations.
4. The human plan, runtime manifest, task claim, commits, and review digest can
   disagree, causing repeated readiness work or unsafe guesses about progress.
5. The plan contains external prerequisites or optional evidence tooling in the
   executable task list, so implementation repeatedly reaches an ownership or
   inclusion blocker.
6. Per-task worker logs and done handoffs are absent, overwritten, or cleaned up
   before the next recovery step can consume them.
7. A worker checkpoint, review artifact, or plan archive is mistaken for the
   terminal state even though the required review, fix, validation, or terminal
   receipt is incomplete.
8. User status questions or new input interrupt the controller, and the next
   turn does not reliably observe the same worker and continue the same state.
9. A user clarification about an unresolved design choice is treated as a
   reason to stop implementation, even after the user has already selected a
   simple MVP direction. The controller then reopens plan review or asks for
   permission at ordinary task boundaries instead of recording the decision,
   applying the bounded plan correction, and continuing.
10. The readiness gate is treated as a recurring workflow phase rather than a
    conditional recovery check. This makes a stable digest and consistent
    manifest pay the cost of repeated whole-plan reviews, and can displace the
    implementation and review work the gate was meant to protect.
11. External deployment, UAT, supervisor, or optional evidence work is mixed
    into repository implementation tasks. The executor then stops on work it
    cannot perform, although the product change could be verified locally and
    the external item could be handed off under Ship when.

These causes interact. Increasing one timeout alone does not fix stale evidence,
capacity waiting, premature completion, or repeated planning gates.

## Sanitized evidence pattern

The execution history contained timed-out review workers, a worker-capacity
failure, a fallback review, later successful worker recovery, repeated plan
readiness checks after plan and manifest drift, and a final archive before the
strict per-task and implementation-review contract had been fully demonstrated.
The implementation itself had landed in repository commits, but the execution
receipt did not prove that every required orchestration phase had run.

This is a process failure, not evidence that the product implementation was
necessarily incorrect. The important distinction is between product completion
and workflow completion.

## Root-cause classification

**Principle:** Family E (temporal / ordering invariants), with Family D (single
source of truth), Family G (data-loss observability), and Family H (verify the
real thing, not the abstraction) as secondary families.

**Shape trigger:** an asynchronous implementation workflow has multiple clocks,
owners, progress records, and evidence artifacts, and a transient runtime event
can be confused with failure or completion.

**General form:** make every non-terminal state durable, bounded, resumable, and
owned by one state machine. Preserve the original claim and evidence lineage
through timeout, capacity loss, user input, and review recovery. Permit terminal
completion only when the same machine-checkable predicate proves implementation,
validation, review, archive, and terminal receipt closure.

## Cause-to-owner matrix

| Cause | Required prevention | Owning component |
|---|---|---|
| Deadline shorter than worker contract | Set separate finite launch, wait, panel, and done deadlines from the actual contract; test normal long-running work and timeout recovery | Runtime adapter and `execute-plan` |
| Temporary capacity loss | Record `waiting-for-capacity` with claim, generation, next action, and retry policy; resume the same claim without duplicate launches | Runtime driver and scheduler |
| Partial or fallback review | Preserve `partial`, `capacity-blocked`, and `timed-out` as non-clean results; use fallback only with explicit coverage and the same exit predicate | `doing-code-review`, `review-loop`, `execute-plan` |
| Plan, manifest, claim, or digest drift | Reconcile against exact bytes and durable evidence; direct-continue only when the digest, scope, manifest, and claim are unchanged | `execute-plan`, runtime validator, `plans` |
| External or optional work in task checklists | Apply the inclusion gate before launch; move external prerequisites and optional hardening to Ship when or a durable backlog item | `plans` and `execute-plan` |
| Missing or overwritten preceding logs | Enforce append-only per-task and per-round logs; refuse `done` when the immediately preceding evidence is missing | `execute-plan`, `agent-logs`, `done` |
| Premature terminal response or archive | Require one terminal predicate and driver receipt; archive and remove session state only after the receipt is written and re-read | `execute-plan` and runtime driver |
| User input interrupts a wait | Distinguish input interruption from worker cancellation; observe the same worker and preserve ownership unless explicit cancellation is confirmed | Runtime adapter and `execute-plan` |
| Clarification is mistaken for an abort | Treat questions as non-terminal input; record confirmed decisions, keep the current task claim, and continue unless the user explicitly pauses or aborts | `execute-plan`, `plans` |
| Readiness gate repeats on stable state | Make readiness conditional on changed digest, inconsistent manifest, unresolved blocker, or crossed review scope; do not repeat it during ordinary task progression | `execute-plan`, `plans` |
| External work is executable by implication | Classify each checklist item before launch; keep external prerequisites and UAT/manual release work under Ship when, and keep optional hardening as backlog | `plans`, `execute-plan` |

## Required implementation

1. Build one state-transition table for active, running, waiting-for-capacity,
   timed-out, interrupted, needs-review, needs-fix, paused, recovering, and
   terminal states. Each state must declare its owner, durable evidence, next
   action, retry limit, and allowed transitions.
2. Add deterministic runtime tests for every cause in the matrix, including a
   worker that legitimately exceeds the old short deadline, a review that needs
   more than five minutes, capacity recovery, user-input interruption, stale
   digest, manifest disagreement, missing log, and premature terminal attempt.
3. Make adapter deadlines configurable only through the runtime contract. Do
   not scatter timeout constants across prompts, skills, and host wrappers.
4. Make fallback review and local recovery preserve the same machine-readable
   coverage and terminal requirements as the preferred path.
5. Make the terminal operation fail closed unless it can prove the current plan
   digest, all task checkpoints, required review closure, final validation,
   archive path, last commit, and cleanup order.
6. Add a compact diagnostic report that identifies the first failed transition,
   not only the last visible timeout. The report must distinguish timeout,
   capacity-unavailable, user interruption, cancellation, worker failure, stale
   evidence, inclusion failure, and terminal-gate failure.
7. Keep the normal path simple: one conditional readiness decision, one task
   owner, one canonical manifest, one review exit predicate, and one terminal
   receipt. Optional defenses should be backlog items, not additional recurring
   gates.

## Acceptance criteria

1. A normal worker or reviewer allowed by the contract is not timed out by a
   shorter host default, and a bounded timeout remains testable.
2. Capacity loss produces a resumable waiting state and never causes duplicate
   task claims or silent completion.
3. A fallback or partial review cannot satisfy a clean-review gate without the
   declared coverage and exact current digest.
4. Unchanged valid state resumes directly; plan, manifest, claim, scope, or
   digest changes enter the corresponding recovery or readiness path once.
5. External prerequisites and optional evidence work cannot block repository
   implementation tasks after the inclusion gate classifies them.
6. Missing, overwritten, or stale preceding logs prevent `done` from committing.
7. Archive, cleanup, and final response are impossible before the terminal driver
   receipt is durably written and re-read.
8. User input during a worker wait preserves the original worker and claim unless
   explicit cancellation is confirmed.
9. A clarification or answer does not restart the workflow or trigger a new
   readiness review when the digest, manifest, and review scope are unchanged.
10. External prerequisites, manual UAT, supervisor release checks, and optional
    evidence tooling are not executable checklist items without the required
    inclusion classification and evidence.
11. Regression tests cover every row in the cause-to-owner matrix.
12. The implementation and documentation remain project-agnostic and contain no
    personal data, private infrastructure identifiers, credentials, or internal
    URLs.

## Why this is high priority

Repeated interruptions consume review capacity, encourage manual bypasses, and
make a correct product change indistinguishable from an incomplete workflow.
Without one cross-cutting state model, individual fixes will continue to move the
failure from timeout to capacity wait, from capacity wait to stale evidence, or
from stale evidence to premature completion.

## Related backlog items

- `2026-09-17-execute-plan-worker-deadline-contract.md` covers worker launch
  deadline sizing and timeout recovery.
- `2026-09-16-execute-plan-interrupted-task-ownership-recovery.md` covers claim
  preservation and interruption recovery.
- `2026-09-16-execute-plan-conditional-readiness-gate.md` covers direct
  continuation versus a fresh readiness review.
- `2026-09-16-execute-plan-review-evidence-and-manifest-gate.md` covers digest,
  manifest, review, and verification evidence lineage.
- `2026-09-16-execute-plan-terminal-completion-integrity.md` covers terminal
  state, review closure, and final-response safety.
- `2026-09-17-execute-plan-worker-deadline-contract.md` also records the
  concrete long-review timeout witness; this inventory owns the cross-cutting
  state and recovery contract rather than duplicating deadline sizing.
