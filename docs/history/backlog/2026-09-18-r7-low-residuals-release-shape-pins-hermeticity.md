# Backlog: r7 low residuals - release-shape reuse, structural-pin strength, test hygiene

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-18
Class: r7 focused-round residuals (Low), batch/watcher machinery
Origin: r7 focused verification (docs/reviews/2026-09-18-...-code-review-r7.md; fix commit c4cbba5f).

## Items
1. (Low) Reclaim-time release keeps a third inline copy of the group-release shape (scripts/execute_plan_runtime.py:3857, already drifted: its history event lacks the reason key). Reuse _fail_group_release_locked.
2. (Low) Silent loss of the r6 F5 carrier rectification when the rectification CAS is stale (scripts/execute_plan_resume_watcher.py:1346): surface a cas-stale marker, retry once, or weaken the contract sentence to best-effort. Corner: a left-armed intent stamp naming a FOREIGN job path (label-conflict arm) could later route a receipt-only teardown at another run's job.
3. (Low) Choke-point AST pin covers only subscript assignments; .update()/setdefault() and claim-named aliases bypass it (scripts/test_execute_plan_runtime.py:6383). Extend the walker or narrow the docstring.
4. (Low) Stale 'unfenced done evidence' comment in the exhaustiveness test (scripts/test_execute_plan_runtime.py:6238) contradicts the pinned stale-claim assertion. Reword.
5. (Low) F5 rectification test arms 1/2/4 run with the real launchctl_bootstrap bound (scripts/test_execute_plan_resume_watcher.py:1290); a refusal-ordering regression would mutate the real gui domain before the test turns red. Install a recording success fake for the whole test.
6. (Low) Structural pin asserts module witness only; a renamed/typo'd derivation symbol silently drops out (scripts/test_execute_plan_resume_watcher.py:2711). Add a per-symbol witnessed assertion.

## Owner + trigger
Owner: batch/watcher runtime + test suites. Trigger: any edit touching the reclaim release path, the rectification CAS, the structural pins, or the F5 test; or the next review round touching these files.
