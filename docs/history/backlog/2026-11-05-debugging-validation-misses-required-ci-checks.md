Status: open
Priority: high
Consumer urgency: This affects consumer projects that use the shared debugging skill; do not park or defer it as formal-hardening for the skills repository alone.
Class: fix-class
Origin class: consumer-feedback (company)

# Debugging verification can report green tests while required CI checks remain skipped
Cluster: docs/history/backlog/2026-11-05-debugging-lesson-recall-not-wired.md (same shared skill surface; distinct Phase 1 and Phase 4 duties)

## Problem

`agents/skills/systematic-debugging/SKILL.md`, Phase 4, Step 3 says to verify that the test passes and no other tests broke, but does not direct the worker to resolve and run the target project's required validation checks. In a recent review-fix session, the local full verification command explicitly skipped the formatter check to avoid broad formatting changes. Tests passed locally, but CI failed at the formatter check before tests ran. The result was a locally reported success that did not match the required CI contract.

Expected: verification follows the target project's required checks, including non-test checks that CI requires. A formatting concern should narrow the formatting scope or be reported as a blocker; it should not silently turn a required check off. Keep test-only tooling separate from full validation and avoid adding a second generic gate when an existing project command already defines the checks.

## Exact location

- `agents/skills/systematic-debugging/SKILL.md`, Phase 4, Step 3 and the phase success criteria.
- Related existing policy: `agents/skills/execute-plan/SKILL.md` and `agents/skills/receiving-review/SKILL.md` validation guidance.

## Suggested fix

Add a concise pointer from Phase 4 verification to the target project's declared validation commands or CI-required checks. State that the worker must report skipped checks and cannot call verification complete when a required check was skipped. Prefer a pointer to a single existing source of truth; do not add another validator or repeat a full suite policy here.

## Severity and source

Severity: High; local verification can miss a required CI failure and return an incomplete fix.
Source: user correction in an anonymized consumer-project review-fix session, 2026-11-05; capture hygiene: `scan-public-hygiene --files` pass.

## Why not fixed now

This request is for incident analysis and backlog capture. The cross-skill wording should be reconciled against the existing validation policies before editing the shared skill.

## Driving force

reliability + maintainability

## Dedup probe

Searched open backlog names and Problem bodies for `formatter`, `CI check`, `validation command`, `test scope`, and `full suite`. `docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md` covers project-wide suite selection and focused-test policy, not disabling a required non-test CI check during a review fix. `docs/history/backlog/2026-11-05-lessons-orphan-disposition-sweep.md` covers lesson discoverability, not CI-equivalent verification. Keep this as a distinct skill-step issue.
