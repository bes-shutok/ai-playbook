# Backlog: execute-plan placement compatibility test rejects the live profile-specific contract

- **Filed:** 2026-10-16, retrospective of the resource-cleanup execution and closeout session
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** pre-existing test failure surfaced during execution
- **Class:** test-contract drift
- **Driving force:** reliability
- **Skill/step:** `scripts/test_plan_readiness.py`, `ExecutePlanProfilePlacementCompatibilityTest`

## Problem

The readiness suite has one failing placement compatibility test. Its assertion requires the `Project worktree policy` paragraph to contain neither `personal` nor `company`, while the current execute-plan policy deliberately includes profile-specific primary-placement safeguards. The full run in this session reported 99/100 passing, with this test as the unrelated failure.

The test was introduced in `e0d7d6961` to pin profile-independent placement. The policy later gained profile-specific branch rules in `f042e22c9`; the test was not updated to reflect that contract. The adjacent open plan-authoring placement backlog concerns a different lane and does not cover this stale test expectation.

## Expected

The compatibility test passes while still checking the placement cases and profile-specific safeguards that the current policy defines. The test must detect accidental loss or misplacement of those safeguards without requiring the policy text to remain profile-neutral.

## Suggested direction

Inspect the exact assertions and the current `Profile and placement` and `Project worktree policy` paragraphs. Update the test's contract assertions to cover the current profile-specific cases while retaining the valid placement matrix checks. Do not change placement policy unless the test and current contract reveal an actual policy contradiction.

## Alternatives

- Restore a profile-neutral placement paragraph by moving the safeguards elsewhere: not justified by this test failure; it would broaden a test repair into a policy change (`agents/skills/execute-plan/SKILL.md`).
- Delete the compatibility test: rejected because the profile-placement contract remains worth pinning and the current mismatch is isolated to its outdated assertion (`scripts/test_plan_readiness.py`).
- Add a new validator or blocking gate for skill/test consistency: rejected because the observed failure is already visible in the existing test and no additional blocking mechanism is needed (`scripts/test_plan_readiness.py`).

## Evidence

- The failing test's `assertNotRegex(placement_policy, r"\b(personal|company)\b")` is in `scripts/test_plan_readiness.py`.
- The current policy includes personal/pet branch restrictions in `agents/skills/execute-plan/SKILL.md`.
- The test was added by `e0d7d6961`; the expanded policy paragraph was introduced by `f042e22c9`.
- The prior session's readiness run reported this one failure among 100 tests; no code fix was made for it.

## Execution-run fold (2026-10-16)

The placement-closing-doctrine-enforcement execution's Task 1 intermediate review independently witnessed this row's leg red at HEAD and on the post-consolidation working tree (identical failure point), and its plan-regression fix rewrote the profile-by-policy matrix's two `primary-execution` legs to the two spelled values (the primary legs now pin the consolidated primary-resolution span). The row's remaining subject, the profile-neutral `assertNotRegex` leg, was deliberately left untouched per the off-plan no-fix-in-task rule and stays this row's open fix; this fold line is the execution witness.
