# Backlog: bind plan acceptance to executable evidence and archive closure

Status: open
Workflow: backlog
Source: anonymized follow-up from an implementation-plan completion review
Severity: Medium
Class: execute-plan completion evidence
Related: `docs/history/backlog/2026-09-08-document-ownership-and-archive-lifecycle.md`

## Problem

An execute-plan run can produce a blocking-clean source review while a plan's
acceptance checklist still contains unchecked items, or while an acceptance
statement names a test without proving that the test exists, runs, and
discriminates the required behavior. If completion is inferred from the code
diff or a commit summary, the implementation may be largely complete while
the plan remains open and its lifecycle state is ambiguous.

The existing document-lifecycle work defines how an eligible plan is archived.
This item covers the preceding eligibility proof: the executor must not enter
that transition until acceptance evidence is complete. Without that boundary,
the correct archive mechanics can still close a plan whose implementation
proof is incomplete.

This is distinct from the general immutable-document lifecycle: that policy
defines what archival means, while this item makes the executor prove that
the plan is eligible for the archival transition.

## Location

- `agents/skills/execute-plan/SKILL.md`, Phase 2 completion and Phase 4 archive
  gates
- `agents/skills/plans/SKILL.md`, acceptance/evidence requirements and plan
  lifecycle contract
- `agents/skills/review-plan/SKILL.md`, plan-quality checks for acceptance
  criteria and validation commands
- `agents/skills/doing-code-review/SKILL.md` and
  `agents/skills/review-agents/testing.md`, review evidence for changed tests
- Runtime or validator self-tests owned by the affected workflow

## Suggested fix

Add an explicit completion-evidence contract shared by plan authoring,
execution, review, and archival:

1. Require each acceptance criterion to identify an observable artifact: a
   discriminating test assertion, a validation command, or a bounded
   repository-local structural check. A test class or method name alone is not
   evidence.
2. During Phase 2, enumerate every acceptance criterion and verify its named
   artifact against the current tree with fresh output. Missing, unchecked, or
   non-discriminating evidence blocks Phase 3 and archival; it must not be
   silently marked complete.
3. Make the review panel's testing and correctness lenses inspect the
   acceptance-to-evidence mapping, including negative paths and boundary
   states, rather than treating a green build as proof of complete acceptance
   coverage.
4. Feed the completion-evidence result into the existing Phase 4 lifecycle
   gate. An incomplete or unbound acceptance item must prevent archival; the
   existing archive and registry checks remain the source of truth for the
   transition itself.
5. Add hermetic fixtures that prove both failure and success: an incomplete
   or unbound acceptance item prevents the lifecycle transition, while a fully
   evidenced plan reaches the existing archive checks.

## Acceptance

- A generic plan fixture with one unchecked or evidence-free acceptance item
  fails the completion gate and remains under the active plan path.
- A generic plan fixture with complete task and acceptance evidence passes only
  when each named test or structural check is present and its assertion is
  discriminating for the stated invariant.
- The review staging or completion receipt records the acceptance-to-evidence
  mapping, not only a test count, method name, HTTP status, or green build.
- The completion gate invokes the existing archive checks only after the
  acceptance-evidence contract passes.
- The success path records final validation output and the acceptance mapping
  before it enters the existing archive and session-cleanup gates.
- The workflow remains tool-agnostic and contains no private service names,
  customer data, credentials, ticket identifiers, internal URLs, or machine
  paths.

## Why not fixed now

The immediate product implementation was completed through a manual lifecycle
repair. Strengthening the shared acceptance and archival contract changes
multiple skills and their executable fixtures, so it should land as a
dedicated ai-playbook change with a fresh review of the workflow itself.
