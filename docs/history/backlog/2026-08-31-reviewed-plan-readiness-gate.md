# Backlog: enforce reviewed-plan readiness before execution and finalization

Status: open
Workflow: backlog
Source: 2026-08-31 session, CRM-688 plan workflow failure and follow-up analysis
Severity: Medium (workflow safety, implementation-blocking)
Scope: plans, review-plan, execute-plan, done, and host-level gate integration

## Problem

The plans workflow can produce and present an implementation plan after
requirements discovery without completing the required review lifecycle. In
the triggering session, the plans skill was used for repository exploration,
Jira/RFC analysis, scope clarification, and plan drafting, but no
`review-plan` round was run and no `ready=yes` review artifact was produced.
The result was honestly described as an unreviewed draft only after the user
asked for verification, rather than being blocked before finalization.

The immediate workflow ambiguity is that conversational Plan Mode requires a
response containing a proposed plan and forbids repository mutations, while
the full plans skill lifecycle assumes that the plan is saved, reviewed,
possibly amended, and finalized. The agent resolved that tension by emitting
the plan instead of explicitly stopping at the draft boundary. The existing
skill-gate does not detect this because it gates writes to plan files, and no
plan file was written in conversational Plan Mode.

The current Codex installation also has no blocking pre-tool hook for final
responses. A write hook therefore cannot make premature response finalization
impossible. Enforcement must exist at the plan artifact, execution, and
finalization boundaries, with host response enforcement added if the platform
event becomes available.

## Impact

An implementer can receive a plan that appears complete even though it has
not passed the required correctness, testing, design, documentation, and risk
review panel. This weakens the intended guarantee that execution starts only
from a plan whose current bytes have a clean review result. It also makes the
distinction between a conversational draft and an execution-ready plan
dependent on agent honesty and memory.

## Suggested fix

### 1. Make plan modes explicit

Update `agents/skills/plans/SKILL.md` so conversational Plan Mode is a
drafting mode, not a completed plan lifecycle. The skill must require the
agent to say that review and artifact finalization are pending when the
conversation cannot write and review the plan. The artifact workflow must
remain responsible for saving the plan, invoking `review-plan`, folding
accepted findings, and running `done`.

Add a pre-finalization self-check with these exact questions:

- Was `review-plan` invoked for this plan?
- Does the latest Markdown review and `.stats.json` sidecar exist?
- Does the sidecar digest match the final plan bytes?
- Does the latest review report `ready=yes`?
- Are there zero unresolved blocking findings?

The agent must not describe the plan as ready for execution when any answer
is negative.

### 2. Add one readiness validator

Create a shared, fail-closed validator for a plan path that checks:

- the plan file exists under the resolved `{plans_dir}`;
- the latest review artifact and required sidecar exist under `{reviews_dir}`;
- the sidecar schema is valid;
- `source_digest` matches the plan bytes;
- the latest review has `ready=yes`; and
- no unresolved blocking findings remain.

Reuse the existing review-staging validator for sidecar schema and digest
validation instead of duplicating digest rules. The readiness result should
identify the first failed condition without exposing unrelated implementation
details.

### 3. Enforce readiness at workflow boundaries

Call the validator before `execute-plan` starts implementation and before
`done` finalizes a plan-creation session. A plan edit must invalidate the
previous readiness result because the digest changes. Missing reviews, stale
reviews, malformed sidecars, and blocking findings must all fail closed.

Keep external release gates and human approval separate from repository
readiness. A clean plan review establishes implementation readiness; it does
not authorize deployment, merge, or other external effects.

### 4. Add host integration where possible

Investigate a blocking final-response or completion event for each supported
agent. If Codex gains such an event, wire the readiness validator without
removing the existing post-tool hooks. Until then, document that Codex cannot
block the final response and rely on the execution/finalization gates.

Do not treat the existing skill marker as proof of review. It proves only that
the owning skill was invoked before a gated write.

## Acceptance criteria

- A conversational Plan Mode response clearly identifies an unreviewed plan
  as a draft and cannot claim `ready for execution` without review evidence.
- `execute-plan` refuses a plan with no review artifact, a missing sidecar, a
  malformed sidecar, a stale `source_digest`, `ready=no`, or unresolved
  blocking findings.
- `done` refuses to finalize the plan-creation workflow until the same
  readiness conditions pass, except when the user explicitly chooses to stop
  without finalization and that choice is recorded.
- A clean review becomes invalid immediately after any plan-byte change.
- The validator uses the resolved facts paths and does not hardcode
  `docs/plans/`, `docs/reviews/`, or machine-specific paths.
- Existing skill-gate behavior for plan and lessons writes remains intact.
- The implementation is covered by tests for every accepted and rejected
  readiness state, including a review edited after validation and a reviewer
  sidecar with a valid schema but an incorrect plan digest.
- Public-hygiene, hook-probe, and realistic skill-flow checks pass.

## Test scenarios

- Given a plan with no review files, readiness rejects it with a missing-review
  reason.
- Given a valid review whose sidecar digest matches the plan and whose verdict
  is `ready=yes`, readiness accepts it.
- Given a plan edited after a clean review, readiness rejects the stale digest.
- Given a review with one unresolved blocking finding, readiness rejects it.
- Given a malformed or missing `.stats.json`, readiness rejects it rather than
  trusting the Markdown review alone.
- Given a review with `ready=no` and no blocking finding, readiness rejects it.
- Given a plan outside the resolved plans directory, readiness rejects it.
- Given a supported host hook payload for a plan finalization or execution
  action, the hook blocks failed readiness and allows a matching clean review.
- Given the current Codex host with no blocking final-response event, the
  diagnostic probe records the limitation and verifies that execution and
  finalization gates still enforce readiness.

## Files and likely ownership

Primary implementation is expected in:

- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- shared validator and hook scripts under `scripts/` or the established hook
  directory, after checking the existing runtime layout
- corresponding self-tests and realistic workflow fixtures

The exact validator location should follow the existing shared-script and
runtime-layout conventions. Do not add a second implementation of digest or
review-sidecar validation.

## Out of scope

- Changing the CRM-688 implementation plan or its product requirements.
- Making plan review a deployment, merge, or release approval.
- Adding a new external service or plugin solely to review plans.
- Treating a forgeable local skill marker as a security boundary.
- Blocking ordinary conversational answers that are not plan finalization or
  execution actions.

## Delivery notes

This backlog item should become a focused implementation plan in the
`ai-playbook` project. The remediation plan itself must pass the complete
plans workflow, including at least one `review-plan` round and a fresh review
after every accepted plan fold. The final implementation should be tested in
the local ai-playbook repository before considering the workflow remediation
complete.
