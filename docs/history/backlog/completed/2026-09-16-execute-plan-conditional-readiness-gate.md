# Backlog: make execute-plan readiness review conditional

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-16
Class: execute-plan readiness liveness and recovery

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration identifier.

## Problem

`execute-plan` can require a full plan-readiness review even when an interrupted
run has an unchanged plan digest and a consistent runtime manifest. This adds
avoidable latency and can make normal task continuation look like a new planning
phase.

The opposite failure is also possible: a changed plan or inconsistent manifest
can be resumed without revalidation if the runtime relies only on a previous
review receipt or an optimistic progress summary. The workflow needs a conditional
gate that distinguishes safe continuation from recovery.

## Sanitized witness

An interrupted implementation run had already completed earlier tasks, but its
human plan and machine manifest disagreed about later task completion. The plan
was then amended to reconcile ownership, contracts, and verification evidence.
Reviewers launched before the final amendment reported against an older digest.
The runtime correctly rejected that stale review, but the execution path had no
compact rule for deciding when a fresh whole-plan review was actually necessary.

The result was repeated review work before the next unfinished task could be
claimed, followed by uncertainty about whether the run had stopped because of a
real blocker, stale evidence, or an orchestration limitation.

## Root-cause classification

**Principle:** Family E (temporal / ordering invariants), with Family D (single
source of truth) and Family H (verify the real thing, not the abstraction) as
secondary families.

**Shape trigger:** a workflow resumes from durable progress records and must
decide whether prior validation still applies to the exact work state.

**General form:** validate only the state that changed, but never skip validation
when an identity, dependency, or completion record changed. A valid unchanged
state may continue directly; a changed plan, inconsistent state, or unresolved
finding must enter a named recovery or readiness path.

## Required behavior

### Direct continuation

Allow the next task to resume without a new whole-plan readiness panel when all of
the following are true:

1. The plan digest matches the digest recorded by the latest eligible readiness
   review.
2. The runtime manifest passes schema and ownership validation.
3. No task has an unresolved claim, commit-pending handoff, or plan/manifest
   disagreement.
4. The previous review has no unresolved blocking finding and its declared scope
   still covers the next task.

### Conditional readiness review

Require a fresh readiness review only when at least one of these conditions holds:

- the plan bytes or digest changed;
- the runtime manifest is missing, malformed, stale, or inconsistent with the
  plan, commits, or task evidence;
- the previous review reported an unresolved planning blocker;
- the next task crosses a boundary not covered by the previous review scope; or
- recovery cannot prove which task is next.

After the conditional review passes, do not repeat the whole-plan review during
ordinary sequential task progression unless one of those conditions becomes true.

## Ownership and implementation scope

- `execute-plan` owns the decision table and the direct-continuation versus
  readiness-review transition.
- The runtime validator owns manifest schema, claim, and digest witnesses.
- `review-staging` owns review eligibility, scope, and freshness fields.
- `review-loop` owns the unresolved-finding state and fresh-review requirement
  after fixes.
- A pre-final-response hook may reject a false success response, but it must call
  the same terminal predicate and must not invent a second readiness policy.

This is a shared workflow change. It must not be implemented by changing a
consumer project's plan, suppressing a stale-review error, or manually editing a
machine manifest.

## Acceptance criteria

1. The skill documents the conditional decision table with direct-continuation,
   readiness-review, and recovery outcomes.
2. An unchanged valid plan and consistent manifest resume the next task without a
   new whole-plan review.
3. A changed plan digest always invalidates the prior readiness receipt.
4. A plan/manifest disagreement, unresolved claim, or unresolved blocker cannot
   enter direct continuation.
5. A readiness review is not repeated between ordinary task transitions when the
   digest, scope, and manifest remain valid.
6. Regression tests cover unchanged resume, digest mutation, manifest mismatch,
   unresolved findings, changed review scope, and unknown next-task recovery.
7. The final-response gate remains separate: direct continuation does not permit
   a completion response without the terminal predicate and receipt.
8. The skill, validator, tests, and documentation contain no repository-specific
   identifiers, personal data, internal URLs, credentials, or environment names.

## Why this is high priority

An unconditional gate harms liveness and encourages agents to bypass or weaken
the review process. A missing gate risks executing a plan that reviewers did not
assess. The decision must be both fail-closed for changed or inconsistent state
and lightweight for a valid unchanged continuation.

## Related backlog items

- `2026-09-16-execute-plan-interrupted-task-ownership-recovery.md` covers
  preserving the current worker claim and task identity when a wait or session
  is interrupted.
- `2026-09-16-execute-plan-review-evidence-and-manifest-gate.md` covers stale
  evidence, canonical manifests, projection validation, and report integrity.
- `2026-09-16-execute-plan-terminal-completion-integrity.md` covers terminal
  response safety and broader state reconciliation.
