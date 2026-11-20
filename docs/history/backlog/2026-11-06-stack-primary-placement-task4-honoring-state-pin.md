Status: open
Priority: low
Class: fix-class
Origin class: review-intermediate
Driving force: maintainability

## Problem
The primary-placement-stack-execution plan (Task 1) enumerates pins for Task 4's fresh-config consult and explicit-direction precedence insertions but not for Task 4's third checkbox: the honoring-state-path clause (the execution claim's branch and the manifest identity fields `run_branch`, `run_worktree` refreshing to the operator-directed placement, with the continuity probe re-running in the new placement's mode). When Task 4 lands, that clause is unguarded by `scripts/test_stack_primary_placement.py`.

## Suggested fix
Add a pin group in `scripts/test_stack_primary_placement.py`'s policy-paragraph section for the honoring-state-path tokens once Task 4's insertion lands; while there, also pin the step 2 stability-list rewording (the placement-identity sentence in execute-plan-stack/SKILL.md), which is delivered but unpinned (Phase 3 review finding).
