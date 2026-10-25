# Backlog: retire the obsolete docs-branch Step 2 selector test

- **Filed:** 2026-10-09, docs-branch-scope-and-tmp-retention plan execution
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** execution deferral
- **Class:** fix-class
- **Driving force:** maintainability (primary); reliability (secondary)
- **Skill/step:** `agents/skills/docs-branch/SKILL.md`, sync entry-point selection; `scripts/test_docs_branch_step2_selector.py`
- **Severity:** low; the selector test still expects the retired backend selection and fails when run against the new single-runner skill
Cluster: docs/history/backlog/2026-10-09-docs-branch-witness-contract-and-recovery-test.md (same surface: the docs-branch skill and its runner tests; both rows are deferrals from the same execution)
Cluster: docs/history/backlog/2026-10-22-done-docs-restore-untracked-record-loss.md (same surface: the docs-branch sync runner; that row investigates an unattributed mid-run record deletion near the sync pass)

## Problem

`scripts/test_docs_branch_step2_selector.py` exercises selection of the old Step 2 synchronization path. The docs-branch change removes that selector in favor of one canonical runner, so the test's old expectations no longer match the skill. It is outside Task 1's `Files:` list, while the plan's broader Review Scope had listed it for removal. During execution, the user chose to defer this test cleanup to a separate backlog item so the current implementation task can stay within its seeded claim scope.

## Suggested fix

Remove the obsolete selector test and any registration that invokes it. Keep its useful coverage only if it tests a behavior still required by the canonical runner; the focused runner suite already checks that `worktree_policy` does not select a backend. Update the current plan or its closeout record to identify this item as deferred.

## Evidence

- The focused canonical sync suite passes against the single-runner contract.
- Running `python3 -m unittest discover -s scripts -p 'test_docs_branch_step2_selector.py' -v` fails because the test still expects the removed selector.
- The live execute-plan task's `Files:` declaration does not include this path; the pre-launch warning half landed via [the execute-plan live-claim scope-widening plan](../plans/completed/2026-10-23-execute-plan-live-claim-scope-widening.md).

## Acceptance

- The obsolete selector test is removed or rewritten to assert only current canonical-runner behavior.
- The relevant focused suite passes, and repository test discovery no longer exercises removed selector behavior.
- The docs-branch plan's deferred-work record points to this backlog item until it is completed.
