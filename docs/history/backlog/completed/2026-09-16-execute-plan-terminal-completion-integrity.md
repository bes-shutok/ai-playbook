# Backlog: enforce execute-plan terminal completion and state reconciliation

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-16
Class: execute-plan terminal safety, review-loop liveness, and state reconciliation

Privacy boundary: this item is intentionally project-agnostic. It omits repository,
product, ticket, branch, commit, person, customer, market, internal URL, account,
provider, and environment identifiers. The original session evidence remains in the
private task history; this file records only the reusable failure pattern.

## Problem

An `execute-plan` run can reach a non-terminal state and still be reported to the
partner as finished. The current workflow describes the required review and recovery
steps, but the final-response boundary is not enforced strongly enough by a single
machine-checkable terminal contract.

The failure is especially dangerous when several kinds of progress are visible at
once:

- implementation workers have returned and some task commits exist;
- a review artifact has been staged, but it contains unresolved blocking findings;
- the runtime has temporarily lost worker capacity and later regains it;
- a budget safety gate pauses further work;
- a session manifest claims task progress that the plan checkboxes do not yet show.

Those signals are not equivalent to completion. A worker receipt means only that one
step returned. A review report is not a clean review. A budget pause is not successful
delivery. A manifest summary is not authoritative when it disagrees with the plan,
git history, or review artifacts.

## Sanitized incident witness

The observed run had this shape:

1. Several implementation tasks ran through worker processes and produced partial
   progress.
2. The first review-panel attempt could not use the preferred worker configuration,
   so a local fallback review was staged.
3. When worker capacity became available again, a broader review ran and identified
   multiple blocking correctness, boundary, configuration, observability, and test
   coverage issues.
4. Instead of entering the required receiving-review address pass, followed by a
   fresh review, the orchestration turn ended after reporting the review result.
5. The runtime state still indicated an active run, while the final response implied
   that implementation and review had been handled.
6. A later recovery audit also found that the machine progress record had advanced
   farther than the plan checkboxes justified. Recovery had to reconstruct the next
   unfinished task from commits, the plan, and the review evidence.
7. A later budget safety pause correctly prevented further work near exhaustion, but
   the pause was another non-terminal state that required durable resume information,
   not a completion message.

The user had to detect the mismatch and ask why execution had stopped. The realistic
consequence is an apparently complete change with unresolved review findings,
unfinished plan tasks, incomplete release proof, and no reliable next action.

## Root-cause classification

**Principle:** Family E (temporal / ordering invariants), with Family D (single source
of truth) and Family H (verify the real thing, not the abstraction) as secondary
families.

**Shape trigger (when to suspect this family):** an orchestrator has multiple partial
progress signals and can emit a completion response before the required next state,
or two progress records can disagree about what is complete.

**General form:** treat orchestration as a state machine. A step receipt advances only
the step that returned. Every non-terminal state must name its next action and remain
resumable. Completion is permitted only after an independent terminal predicate is
true: all required plan work is accounted for, all mandatory review/fix loops are
clean, required verification has passed, and the durable runtime state says the run
has exited. Never infer terminal state from a worker summary, a review document, a
stale manifest, or a clean subset of the work.

## What should be prevented

### 1. Premature final responses

The orchestrator must not produce a final completion response while any of these are
true:

- the runtime manifest is `active`, `paused`, `waiting`, `needs-review`, or
  `needs-fix`;
- a required plan checkbox is unchecked or its evidence is missing;
- a review contains unresolved blocking findings;
- a valid finding was neither fixed nor durably backlogged;
- a required fresh review has not run after a fix;
- the final `done`/terminal receipt is absent;
- the budget pause record has no explicit next action and resume condition.

The only allowed user-facing result in those states is a progress or pause update
that names the current state, the next action, and the condition for resumption.

### 2. Review reports must drive the next transition

The review loop must make the following transition mandatory rather than advisory:

`review completed with blocking findings -> receiving-review address pass -> done for
that pass -> fresh targeted or full review -> repeat until clean`.

If the preferred worker configuration fails, the fallback path may change how the
review is produced, but it must not change the exit condition. Temporary worker
capacity loss is recoverable runtime state, not permission to exit.

### 3. Progress records must reconcile before they are trusted

Before advancing a task or declaring a phase complete, compare the independent
records:

- the plan checkbox and task acceptance criteria;
- the task commit and its verification output;
- the review and triage artifacts;
- the runtime manifest and its next-action field;
- the current git state and any required documentation deliverables.

If they disagree, enter a recovery state and reconstruct progress from the most
authoritative evidence. Do not silently repair the manifest by assuming that a worker
receipt means the plan task is complete.

### 4. Budget pauses must preserve liveness without crossing the safety floor

The budget protocol must stop starting new work before the configured safety floor,
while preserving a durable pause record containing the binding window, reason, phase,
round, next action, and resume condition. A pause is successful only when the run can
resume safely or a human can see exactly what remains. The budget rule must never
convert a non-terminal pause into a success response.

## Proposed skill and harness changes

This is a workflow/harness change, not a product-code change.

### `execute-plan`

1. Define an explicit state table covering `active`, `needs-review`, `needs-fix`,
   `paused`, `waiting-for-capacity`, `recovering`, and `terminal`.
2. Add a mandatory transition loop after every worker return, review result, quota
   decision, and user status question. The loop must select the next action before
   control can return to the user.
3. Make the terminal driver receipt a hard precondition for the final response. The
   response gate must fail closed when the manifest is non-terminal or when any
   required evidence is missing.
4. State that a user question such as “why did you stop?” is a non-terminal resume
   signal unless the user explicitly cancels the run.
5. Make the recovery path reconstruct one task at a time from plan checkboxes,
   commits, tests, and review artifacts. Require the checkbox update and evidence
   reconciliation before moving to the next task.
6. Make the budget pause protocol persist the next action and arrange the documented
   resume mechanism, while respecting the configured stop-before-exhaustion rule.

### `receiving-review` and `review-loop`

1. Make unresolved blocking findings an explicit non-terminal state owned by the
   orchestrator.
2. Require the address pass, per-finding verification, triage update, and fresh
   review before the loop can claim completion.
3. Treat a fallback review, timed-out worker, or partial panel as a change in
   evidence quality or execution method, never as a clean verdict.
4. Require every valid unfixed finding to have a durable backlog path before a loop
   can exit for a non-blocking reason.

### `doing-code-review` and review runtime contracts

1. Return structured status distinguishing `clean`, `blocking-findings`,
   `non-blocking-findings`, `partial`, `capacity-failure`, and `timed-out`.
2. Include the review scope, source digest, worker coverage, and whether the result is
   eligible to satisfy the execute-plan exit gate.
3. Ensure a fallback or resumed panel cannot overwrite a stronger prior result without
   recording which evidence was superseded.

### `plans` and `done`

1. Keep the plan checkbox as the task-level source of truth, with commits and tests
   as evidence rather than substitutes for the checkbox.
2. Add a pre-commit/pre-finalization consistency check for unchecked tasks,
   unaccounted review findings, active manifests, and missing terminal receipts.
3. Ensure `done` reports an incomplete or paused run as incomplete or paused and never
   upgrades it to success because the working tree is clean.

### Regression harness

Add deterministic fixtures or tests for at least these paths:

- implementation worker returns, but the next plan task is still unchecked;
- review returns blocking findings;
- the address pass fixes findings but the fresh review has not run;
- the preferred worker launch fails, then capacity returns;
- a user asks for status while the run is active;
- manifest and plan checkbox disagree;
- budget pause happens between two worker waves;
- all work is complete and the terminal receipt is present.

Each fixture must assert both the next state and whether a final response is allowed.
At least one negative test must prove that every non-terminal state rejects a success
response.

## Acceptance criteria

1. A single, documented terminal predicate exists and is used by `execute-plan`,
   `review-loop`, and `done`.
2. The predicate fails closed for an active or paused manifest, an unchecked required
   task, unresolved blocking findings, missing fresh-review evidence, or a missing
   terminal receipt.
3. A review with blocking findings automatically leaves the run in a resumable
   address state and cannot be reported as complete.
4. A capacity failure or fallback review preserves the same state machine and exit
   conditions; regaining capacity resumes the pending action rather than starting a
   second ambiguous run.
5. A plan/manifest disagreement is detected and surfaced as recovery work before any
   later task is marked complete.
6. A budget pause records enough state to resume the exact next action and does not
   cause a completion response.
7. The regression fixtures cover every state transition listed above and demonstrate
   that the final-response gate rejects each non-terminal case.
8. The implementation and tests contain no repository-specific identifiers, personal
   data, internal URLs, credentials, or environment names from the originating
   incident.

## Why this is high priority

This defect can invalidate the safety guarantees of every other execute-plan rule.
Even correct implementation, review, budget, and recovery instructions are not
effective if the orchestrator can stop at an intermediate state and declare success.
The failure also hides the true state from the partner, increasing the chance that
unfinished work is mistaken for reviewed and delivered work.

## Why not fixed now

The current user request is to create a durable, sanitized backlog item. Applying the
changes above would modify shared skills and their regression harness across the
ai-playbook repository, which requires its own implementation plan, review, and
verification cycle. The originating product change remains a separate unfinished
run; this item deliberately records the playbook remediation without attempting to
resume or broaden that implementation.

## Related backlog items

This item is intentionally the umbrella terminal-safety item. It complements, rather
than duplicates, existing narrower items for mid-round budget watchers, parallel
review-address workers, bounded review-worker fallback, paused-execution resumption,
and automatic capture of skill-usage issues. Those items address individual mechanisms;
this item makes their states converge on one fail-closed completion contract.

## Additional witness: interruption during an active execution run

A later run reproduced the same failure family with a more precise sequence:

1. The implementation plan changed after its review digest had been recorded.
2. The readiness check detected that the review sidecar no longer matched the
   current plan, but the orchestration path did not turn that result into a
   durable recovery state with a single next action.
3. A broader review-panel launch was denied because the worker pool had reached
   its concurrent-task limit. The account still had substantial usage
   allowance, so this was a capacity state, not a quota state.
4. A bounded fallback reviewer produced useful blocking findings, but the full
   review panel could not be re-established before the user-facing status
   exchange.
5. The response was emitted while later reviewer completion notifications were
   still able to arrive. The run was therefore neither terminal nor fully
   reviewed when the response was shown.

This witness adds two required safeguards to the state-machine contract:

- a status question from the user must keep an active execution run resumable
  unless the user explicitly cancels it; and
- asynchronous reviewer notifications must be joined or durably recorded before
  the orchestrator emits a terminal response. A response boundary must not
  outrun the worker lifecycle.

The run also showed why the terminal predicate must include review completeness,
not only implementation and test progress. Several required integration witnesses
were still disabled, and the available fallback review had identified unresolved
correctness and release-readiness risks. The correct outcome was an explicit
incomplete state with the next address action, not a completion-shaped response.
