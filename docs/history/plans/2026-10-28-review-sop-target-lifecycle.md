# Plan: review SOP target lifecycle applicability
Backlog origin: docs/history/backlog/2026-10-28-review-sop-applicability.md
Driving force: docs
Plan review record: .ai-playbook/reviews/2026-10-28-plan-review-review-sop-target-lifecycle-r*.md
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/review-sop-target-lifecycle.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms
- **Procedure applicability**: whether the stated preconditions of a cited SOP or runbook match the task's requested lifecycle and the target's actual state.
- **Existing-resource adoption**: bringing an already-created live resource under management.
- **New-target creation**: creating a target that does not yet exist in the relevant environment.

## Why
Step 4.2 checks whether assumptions are true in context, but it does not tell reviewers to compare a cited procedure's preconditions with the target lifecycle. A witnessed review applied an existing-schema onboarding procedure to a change creating new production targets and recommended an unnecessary blocker.

## Gist & Examples
TLDR: Check cited procedure preconditions against task intent and target lifecycle before relying on them in a review finding, to reduce false-positive blockers.

Before: A reviewer treats a topic-matched onboarding procedure as applicable even though it assumes an existing live resource and the task creates a new target.
After: A reviewer verifies the procedure's preconditions against the requested lifecycle and target state, then drops or reframes the finding if they do not match.

## Outcome
Reviewers check procedure applicability before using an SOP or runbook to support a blocking or severity-bearing finding.
- Existing-resource adoption is distinguished from new-target creation when assessing a procedure.
- A procedure that does not apply to the task's lifecycle does not support a blocker without independent evidence.
- Existing Step 4.2 assumption checks remain available and no production action becomes a review prerequisite.

Gate delta: none; this wording adds no refusal class, hard gate, fence, protocol layer, schema field, dispatch pause, or execution prerequisite; it removes none. No blocking review-layer duty is added; the read-only reviewer applicability check is non-blocking and derives from the origin's false-positive witness.

## Assumptions
- assume Step 4.2 is the sole operative home; basis: the origin names it and the review workflow places contextual assumption checks there.
- assume a read-only reviewer check is sufficient; basis: the witnessed failure was a mismatch between procedure preconditions and target lifecycle, and the origin rejects automatic gating and production execution prerequisites.
- simpler design: retain existing checks and add one concise generic procedure-applicability check; removing checks loses unrelated protections, a database-specific exception is too narrow, and a new automatic gate adds machinery without evidence of need (`docs/history/backlog/2026-10-28-review-sop-applicability.md`).
Decision points requiring a grill: none remain.

## Evaluation Criteria
- The guidance makes reviewers compare a referenced procedure's preconditions with task intent and target lifecycle/state before using it to support a blocking or severity-bearing finding.
- The examples or review checklist distinguish adopting an existing resource from creating a new target and use available issue, PR, author-thread, and repository-configuration evidence; unavailable sources do not become inferred facts.
- Non-applicable procedures are dropped or reframed, while independently supported concerns and applicable procedures remain reviewable.
- The change remains read-only and does not require production execution or create an automated gate.

**Quality dimensions:**
- Correctness: the applicability check matches the origin's stated expected behavior.
- Simplicity: the existing Step 4.2 checklist carries the rule without a new workflow step or machinery.
- Maintainability: guidance is general across procedures and target types, without a database-specific exception.

**Done when:** Step 4.2 contains a concise procedure-applicability check, the existing-resource and new-target cases produce the expected review decision, and the text-growth rule is satisfied without removing existing protections.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/doing-code-review/SKILL.md` (Task 1)

**Tests:**
- none

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Validators, automated review gates, and production execution prerequisites; the origin explicitly chooses a read-only reviewer check.
- Other review phases and unrelated Step 4.2 assumption checks; preserve their current protections.

## Validation Commands

```bash
git diff --check
```

### Task 1: Add the procedure-applicability check to Step 4.2

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/doing-code-review/SKILL.md`

Primary class anchors:
- `Step 4.2 Check Assumptions` in `agents/skills/doing-code-review/SKILL.md`

- [ ] Given a review concerns adopting an existing live resource, expects the reviewer to compare the cited procedure's preconditions with task intent and target state using available issue, PR, author-thread, and repository-configuration evidence; unavailable sources are recorded as unavailable, not inferred. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a review concerns creating a new target and the cited procedure only applies to adopting an existing resource, expects the reviewer to reject that procedure as support for a blocker based on topic similarity alone; given a procedure whose preconditions match new-target creation, expects the reviewer to assess it normally. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a cited procedure's preconditions do not match the requested lifecycle or target state, expects the reviewer to drop or reframe the procedure-based finding and retain any independently supported concern. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a procedure's preconditions do match the requested lifecycle and target state, expects the existing finding assessment to continue unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewrite Step 4.2 with the smallest generic wording change; do not add an automated gate, production execution prerequisite, or database-only exception. [class: IMPLEMENTATION_REQUIRED]
- [ ] Pay for any operative text growth in `agents/skills/doing-code-review/SKILL.md` by deleting equivalent operative bytes in the same change while preserving the existing assumption protections; record the comparison in the review. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the existing review-plan panel for the skill diff and resolve blocking findings. [class: REPOSITORY_TEST]
- [ ] Run the updated review skill with anonymized sample contexts for existing-resource adoption and new-target creation, including matching and mismatched procedure preconditions; verify the applicable procedure remains usable, the inapplicable procedure is dropped or reframed, and missing target-state evidence is not inferred. [class: REPOSITORY_TEST]
- [ ] Run `git diff --check`. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: check review procedure applicability` [class: IMPLEMENTATION_REQUIRED]
