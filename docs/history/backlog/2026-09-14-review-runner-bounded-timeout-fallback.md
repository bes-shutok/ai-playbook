# Backlog: bounded review-worker timeout fallback and coverage accounting

Status: open
Priority: medium
Workflow: backlog
Origin: repeated bounded plan-review worker timeouts during a service-plan certification run; the final broader correctness and implementation auditor timed out twice after bounded intervals while independent focused reviewers supplied replacement coverage
Severity: Medium overall; individual controls range from Low to High depending on whether missing coverage can hide a blocking defect
Class: review-runner reliability and coverage accounting

## Problem

The review runner can produce a useful review even when one worker times out,
but the current workflow does not make the difference between complete,
replacement-covered, and materially incomplete review coverage explicit enough.
This leaves several questions to manual judgment:

- Was the timed-out worker retried, and how many bounded attempts remain?
- Which replacement lens covered the missing material area?
- Does the final `ready=yes` mean every material lens completed, or only that
  another worker appeared to cover related topics?
- How should automation distinguish a clean review from a review that stopped
  with degraded coverage?

The desired behavior is bounded and selective. A timeout should not trigger an
unbounded wait or an automatic full-panel relaunch. A worker that timed out
because of a transient provider or capacity problem may receive a bounded
retry. If the worker remains unavailable, the runner should select an explicit
independent replacement for the missing material lens. Deterministic review
failure, malformed output, and data or parsing errors should be classified and
logged distinctly rather than being treated as transient capacity failures.

## Evidence from the triggering run

The 2026-09-14 review staging artifact for a service plan recorded a four-worker
focused panel:

| Worker | Lenses | Result | Findings |
|---|---|---|---:|
| design-simplicity | architecture, simplification | complete | 2 |
| testing | testing, quality | complete | 3 |
| contract-docs | documentation, consistency | complete | 1 |
| correctness-completeness | quality, implementation | timed out | 0 |

The initial broader worker launches timed out, including a bounded retry of a
single worker. Independent focused reviewers were then used to cover the
material areas that still needed evidence. They produced six distinct findings,
all of which were folded and locally verified:

1. `architecture#vendor-specific-failure-policy` (High, blocking): the
   application-level test contract could have reintroduced JDBC and
   PostgreSQL-specific retry policy after that responsibility had been moved to
   infrastructure. The correction separated neutral application failure
   reasons from infrastructure-specific SQLSTATE and JDBC inspection.

2. `testing#dependency-provenance` (High, blocking): a fresh checkout could
   have used a different broker image or dependency version, making end-to-end
   evidence untrustworthy. The correction pinned dependency coordinates,
   repository provenance, and an immutable broker image digest.

3. `testing#real-listener-failure-routing` (High, blocking): unit mapping tests
   did not prove that an unclassified runtime, data-access, or post-commit
   failure at the real listener boundary reached the native dead-letter path
   without retry. The correction added a real-listener broker witness with
   source and retry-delivery assertions and sanitized error logging.

4. `testing#broker-runtime-contract` (High, blocking): the host JVM could have
   connected to an advertised container port or used a broker delay table that
   differed from the mapping tested by the consumer. The correction made the
   host route, nameserver advertisement, effective delay table, and preflight
   parsing observable.

5. `implementation#timeout-budget-wiring` (Medium, blocking): the effective
   consumer callback timeout was not tied to the pinned client API and could
   have outlasted the transaction budget, causing overlapping redelivery or
   commit uncertainty. The correction named the property, client setter, unit,
   numeric margin, and effective-value assertion.

6. `documentation#release-and-sync-closure` (Medium, non-blocking): a release
   could have passed with broker tests skipped, or stale documentation claims
   could have survived beside a newer source-revision manifest. The correction
   added an explicit release-time integration-test gate and an executable
   documentation revision check.

The final broader auditor timed out again after two bounded intervals and was
stopped. The review was still marked `ready=yes` because the focused reviewers,
the replacement coverage, the review artifacts, and local closure checks
provided evidence for the material areas. That outcome was reasonable for the
run, but it is not represented by a sufficiently precise machine-readable
coverage state. A future runner should make this reasoning explicit instead of
requiring a human to reconstruct it from prose and sidecars.

## Additional recurrence and response direction

In a subsequent review attempt, every worker exceeded two bounded wait
intervals. This indicates that the current combination of worker prompt scope
and timeout budget is too ambitious for reliable execution; it is not evidence
that the reviewed plan itself needs less review coverage.

The likely correction is both narrower prompts and a larger, still-bounded
timeout budget:

1. Narrow each worker prompt to the artifact, assigned lens, changed-risk
   signals, and the exact evidence fields it must return. Avoid asking every
   worker to rediscover the whole plan or perform a broad cross-lens audit.
   Run any broader audit as a separately scoped replacement or escalation.
2. Increase the per-worker timeout only after making the prompt scope
   explicit, using observed completion times to choose a configurable upper
   bound. Keep the retry count and total panel wall-clock budget fixed, so a
   larger timeout does not become an unbounded wait.
3. Preserve the replacement and degraded-coverage rules. A worker that still
   exceeds the new bounded budget must produce an explicit timeout record and
   either receive an independent replacement lens or prevent `ready=yes`.

The implementation should measure these two changes separately where possible:
prompt-scope reduction, timeout-budget change, and the resulting completion or
replacement coverage. This makes it possible to tell whether failures are due
to excessive prompt work, provider latency, or an overly small timeout rather
than simply increasing the limit without evidence.

## Scope and non-goals

This backlog item covers the shared review runner, panel accounting, retry
selection, review staging metadata, and readiness validation.

It does not change product behavior in the reviewed service. In particular, it
does not decide which service failures are retried. Product plans must continue
to classify deterministic malformed-property and data errors separately from
transient database-congestion failures, and must define the appropriate log
level and sanitized fields for each class. This item only ensures that review
workers and their outputs receive an equally explicit failure classification.

It also does not require waiting forever, retrying every worker, or relaunching
the whole panel after one lens times out.

## Proposed changes

### 1. Per-worker timeout and retry telemetry

Record a machine-readable event for every worker attempt, including:

- stable panel, worker, lens, and attempt identifiers;
- start time, bounded wait deadline, completion time if available, and elapsed
  duration;
- outcome: `complete`, `failed`, `timeout`, `cancelled`, or `malformed-output`;
- failure class when known: provider timeout, usage or rate limit, worker crash,
  orchestrator wait timeout, parse failure, or other data error;
- retry decision, retry number, retry budget, and reason;
- replacement worker or lens selected after an exhausted or non-retryable
  outcome;
- whether the result contributed material coverage to the final verdict.

Telemetry must not include prompts, authentication material, provider payloads, or review
content that is not already part of the staged artifact. It should be possible
to reconstruct the panel timeline and coverage without reading raw worker logs.

### 2. Fixed retry budget

Define a fixed, configuration-visible retry budget at the panel or worker
level. A bounded wait must consume a known unit of that budget, and the runner
must stop retrying when the budget is exhausted. The implementation should:

- avoid indefinite retry loops and repeated full-panel relaunches;
- distinguish a retryable provider or capacity timeout from a deterministic
  malformed-output or data/parsing failure;
- preserve late or partial artifacts from an attempt for diagnosis without
  treating them as a completed verdict;
- report the budget and exhaustion reason in the panel sidecar.

The first implementation can use a small fixed budget suitable for the
existing runner. The exact default should be chosen from observed recurrence
data and documented with the timeout values.

The timeout budget must be independent from prompt breadth. A worker attempt
may receive a larger bounded deadline after the prompt is narrowed, but the
panel must still enforce a fixed attempt count and total wall-clock ceiling.

### 3. Explicit replacement-lens selection

When a material worker is unavailable after its permitted attempts, select a
replacement through a declared rule rather than an informal decision in the
review narrative. The selection record should identify:

- the missing lens or lens group;
- why the original worker was not used again;
- the independent worker, prompt family, or focused review mode selected;
- how the replacement is independent enough to provide useful coverage;
- whether the replacement covers the full material lens or only a subset;
- the evidence artifact and sidecar that establish replacement completion.

Replacement coverage must not silently change the review scope. If no suitable
replacement exists, the runner must report the lens as incomplete.

The replacement prompt must be no broader than the missing lens requires. It
must name the original lens, the reduced evidence scope, and the exact
artifact/sidecar that will establish coverage; it must not recreate the timed
out broad audit under a different worker name.

### 4. Machine-readable degraded-coverage outcome

Extend the panel status model so it can distinguish at least:

- clean completion with all material lenses covered;
- completed with documented replacement coverage;
- degraded or incomplete because one or more material lenses remain
  unreviewed;
- failed because the runner could not establish a trustworthy review result.

The status must include the set of material lenses, completed coverage,
replacement coverage, missing coverage, timed-out attempts, and retry-budget
exhaustion. Human-readable Markdown may summarize the result, but it must not
be the only source used by readiness checks or downstream automation.

### 5. Ready verdict must require material coverage

Make `ready=yes` impossible when material lens coverage is missing. The
readiness validator should fail closed if:

- a material worker is timed out, failed, cancelled, or malformed and has no
  accepted replacement coverage;
- a replacement is recorded without an artifact and sidecar proving completion;
- the sidecar and Markdown disagree about the material-lens set or final
  outcome;
- a late original result is mistaken for a successful attempt after the panel
  already moved to degraded or replacement coverage;
- the runner cannot determine whether a lens is material.

The validator may accept a clean `ready=yes` after an explicitly recorded
replacement review when every material lens is covered and all existing
integrity checks pass. It must not infer coverage from a nearby lens name,
worker launch, or a summary sentence.

### 6. Preserve existing artifact and sidecar safeguards

The change must retain and reuse the existing protections that make review
results auditable:

- a completed review round requires both the Markdown artifact and its
  machine-readable sidecar;
- a killed worker or late flush is audited on disk before relaunch;
- a rate-limited or otherwise unavailable lens remains in panel accounting
  until a replacement or explicit incomplete outcome is recorded;
- readiness is checked against the current source digest and current staged
  findings;
- worker output is not hand-transcribed into sidecars;
- stale artifacts cannot be promoted by filename or summary alone.

These rules should be expressed once in the review-runner or staging validator
and covered by focused self-tests.

## Acceptance criteria

1. Panel metadata records every worker attempt with status, failure class,
   bounded deadline, retry lineage, and final coverage contribution.
2. One fixed retry budget applies per worker or round, is visible in the
   sidecar, and prevents unbounded waits or accidental full-panel retry loops.
3. Timeout fallback records an explicit missing lens and an explicit
   replacement worker or focused review mode, or records that no replacement
   exists.
4. A replacement result is linked to its own Markdown artifact and sidecar and
   distinguishes the original timeout from replacement completion.
5. The final machine-readable outcome distinguishes clean, replacement-covered,
   degraded, and failed review states.
6. The readiness validator rejects `ready=yes` whenever a material lens remains
   incomplete, ambiguous, or unsupported by a valid artifact and sidecar.
7. The validator accepts `ready=yes` only when all material lenses are covered,
   including accepted replacement coverage, and source-digest and integrity
   checks pass.
8. Self-tests cover complete workers, retryable timeout followed by completion,
   exhausted timeout followed by replacement, timeout with no replacement,
   malformed output, deterministic data or parsing failure, late original
   output, and disagreement between Markdown and sidecar.
9. Telemetry and artifacts contain no prompts, authentication material, provider secrets,
   or unredacted review payloads.
10. Existing artifact recovery, rate-limit accounting, source-digest binding,
    and sidecar completeness safeguards remain green.
11. A regression fixture demonstrates that a narrowed lens-scoped prompt can
    complete within the configured bounded timeout, while a broad prompt is
    accounted for as its own bounded attempt rather than silently extending the
    deadline or relaunching the whole panel.

## Why not fixed now

The triggering service plan was already certified after independent focused
reviewers supplied replacement coverage for the timed-out material area. The
six concrete findings from that run were folded, and local integrity and
closure checks passed. Changing the shared runner and readiness model is a
cross-cutting playbook change that deserves its own design and review cycle.

This item is therefore captured as workflow backlog rather than retroactively
changing the certified service plan or weakening its review result. No Jira
ticket is created by this backlog entry.

## Promotion notes

When scheduled, create an implementation plan under `docs/plans/` and update
the relevant review-runner, `review-plan`, `review-loop`, `review-staging`, and
readiness-validator contracts together. Preserve the existing lessons covering
post-verdict fold audits, killed-worker artifact recovery, rate-limited lens
relaunch, and the requirement for both Markdown and sidecar artifacts.

Start by collecting recurrence data for provider timeout, usage or rate-limit,
worker crash, orchestrator wait timeout, malformed output, and data or parsing
failure. Use that data to choose the initial retry budget and replacement rules;
do not silently turn all error classes into retries.
