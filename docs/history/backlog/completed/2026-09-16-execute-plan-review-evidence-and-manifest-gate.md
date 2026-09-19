# Backlog: make execute-plan review evidence and manifests fail closed

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-16
Class: plan readiness, review freshness, executable verification, and evidence lineage

Privacy boundary: this item is project-agnostic and sanitized. It contains no
repository, product, ticket, branch, commit, person, customer, market, internal
URL, account, provider, environment, credential, or configuration value from the
originating run.

## Problem

The implementation workflow can have several artifacts that look authoritative
while disagreeing about what was reviewed or verified:

- the plan can change after a review digest is created;
- a canonical test manifest can drift from phase projections;
- a projection can name a stale or nonexistent test method;
- a helper can find a matching test case but accept a failing or errored result;
- a required verification harness can be absent while a smaller self-test passes;
- a complete witness list can contain more rows than the manifest or phase
  projections account for; and
- a command can run a broader selector than the evidence manifest covers.

These are evidence-lineage failures. They can produce a green-looking readiness
summary without proving the current plan, the intended test, or a successful test
outcome. They are especially dangerous in execute-plan because a stale review can
be treated as fresh after plan mutations, and a partial test matrix can be treated
as release verification.

## Sanitized witness

A resumed execution run exposed all of the following:

1. The current plan digest did not have a fresh review sidecar, and the readiness
   validator correctly rejected the stale artifact only after execution had
   already reached the review gate.
2. The canonical manifest and phase projections disagreed. Some rows used method
   names that were no longer present, while current tests had been renamed or
   projected differently.
3. The complete witness set was materially larger than the canonical manifest,
   leaving unaccounted verification rows.
4. The helper self-test did not include XML cases containing `<failure>` or
   `<error>`, so a matching testcase could be mistaken for a passing testcase.
5. The negative harness did not prove selector failure, stale timestamps, or the
   required-versus-optional behavior of a no-container environment.

The result was useful diagnostic evidence, but not a release-ready verification
record. The workflow needed to stop with explicit evidence gaps and a next action.

## Root-cause classification

**Principle:** Family D (single source of truth), with Family G (data-loss
observability) and Family H (verify the real thing, not the abstraction) as
secondary families.

**Shape trigger:** multiple manifests, projections, reports, or summaries claim to
describe one verification set, but no fail-closed validator proves that they have
the same identity, scope, outcome, and freshness.

## Skill and hook ownership

This should be implemented as a shared workflow change with explicit ownership:

- `execute-plan` owns the terminal gate and must refuse completion when review
  freshness or verification evidence is invalid.
- `review-loop` and `doing-code-review` own coverage state, source-digest
  lineage, and the distinction between full, replacement-covered, partial,
  capacity-blocked, and stale review results.
- `plans` owns canonical manifest structure and plan-to-evidence traceability.
- `learn` owns capture of this kind of skill or validator defect as a high-priority
  project-agnostic backlog item, after deduplication and privacy scrubbing.
- A lightweight pre-final-response hook may provide an early guard, but it must
  call the same terminal predicate as the skills. A hook is a safety net, not a
  second source of truth.

The language-continuity issue belongs in the shared human-facing writing contract
and its session or response hook. It must be tracked separately from evidence
freshness so a language mismatch cannot be dismissed as a review-manifest issue.

## Fix candidates

### 1. One canonical manifest compiler

Choose one manifest as the source of truth. Generate phase projections from it, or
validate every projection as an exact declared subset with stable row identity.
Reject unknown methods, stale selectors, duplicate witnesses, missing rows, and
rows that cannot be mapped to a real build report. The checker must expose the
uncovered remainder instead of silently ignoring it.

### 2. Bind review freshness to the current plan

Every plan mutation must invalidate the prior review receipt. Readiness must fail
closed when the current digest has no fresh review sidecar, when the sidecar uses
an older plan revision, or when the review scope no longer covers the current
changed surfaces. A fallback or partial review must carry an explicit coverage
state and must not satisfy a full-review gate by implication.

### 3. Make report verification prove success

The report verifier must reject a witness when the matching testcase is skipped,
contains `<failure>`, contains `<error>`, has zero executions, has the wrong run
identity, or is outside the allowed freshness window. Add fixtures for each
negative case and one positive accept-at-boundary case.

### 4. Test the harness failure modes

The self-test must cover:

- a missing or invalid Maven test selector;
- stale report timestamps and mismatched run identity;
- failing and errored XML testcases;
- an optional no-container environment that records a skip; and
- a required no-container environment that fails readiness.

The harness must distinguish “not run”, “skipped by policy”, “failed”, and
“passed”. A self-test that only exercises the happy path is insufficient.

### 5. Reconcile command scope with evidence scope

For every verification command, record the exact selector, module scope, required
profile or feature flag, runtime prerequisites, and expected witness rows. Readiness
must fail when a command executes tests that are not represented in the manifest,
or when the manifest claims rows that the command cannot produce.

### 6. Preserve degraded review truth

Review staging must report full, replacement-covered, partial, capacity-blocked,
and stale outcomes separately. A bounded fallback reviewer is useful evidence, but
it is not equivalent to a fresh full panel unless the declared material lenses are
all independently covered and the current digest is verified.

## Acceptance criteria

1. A single canonical manifest and a machine-checkable projection rule exist.
2. Current-plan digest freshness is mandatory for readiness and final review
   completion.
3. Unknown, stale, duplicate, missing, renamed, or unaccounted witness rows fail
   validation with an actionable next step.
4. XML reports containing skipped, failed, or errored matching testcases cannot
   satisfy a passing witness.
5. The self-test covers selector failure, stale identity, timestamp boundaries,
   failure and error XML, and required-versus-optional no-container behavior.
6. Review coverage state is explicit and a partial or capacity-blocked review
   cannot satisfy a full clean-review gate.
7. Every validation command has evidence scope that matches its manifest rows.
8. The regression fixtures and documentation contain no repository-specific
   identifiers, personal data, internal URLs, secrets, or environment names.

## Why this is high priority

This gap can convert incomplete or stale evidence into a false release signal. It
also makes recovery slower because the next agent must reconstruct truth from
disagreeing artifacts instead of following one authoritative record.

## Why not fixed now

The current request is to capture reusable playbook backlog, not to modify the
shared execution, review, or validation machinery. Implementing these controls
requires its own plan, tests, review, and compatibility decision for existing
sidecars and manifests.
