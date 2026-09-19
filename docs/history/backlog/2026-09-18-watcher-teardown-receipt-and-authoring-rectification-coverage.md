# Backlog: watcher teardown receipt on the pause arm and authoring rectification coverage

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-18
Class: r7 focused-round residuals (observability + coverage), execute-plan/plans watcher machinery
Origin: r7 focused verification of the r6 fixes (docs/reviews/2026-09-18-...-code-review-r7.md; fix commit c4cbba5f).

## Items
1. (Medium) The r6 F3 supersede carrier teardown computes its receipt (scripts/execute_plan_resume_watcher.py:1373) but the schedule arm's outcome_factory drops it (line 1517 forwards only carrier_rectified) - a pause superseding an armed watcher tears down with no machine-readable evidence, and no test covers teardown on that arm (the existing test drives the rarer watcher-supersede kind). Fix: forward carrier_teardown beside carrier_rectified (one line), extend the runtime-contract sentence, add a pause-shaped assertion.
2. (Medium) PlansAuthoringWatcherAdapter.compare_and_swap_carrier (the authoring rectification mirror, scripts/execute_plan_resume_watcher.py:1873-1910) has zero test coverage; a drift in its CAS predicate/validation/projection re-creates the false armed-carrier receipt class (r6 F5) on the plans path undetected. Fix: add the authoring-arm test mirroring the runtime rectification arms.

## Owner + trigger
Owner: execute-plan/plans watcher machinery. Trigger: any edit to supersede_carrier_teardown, the schedule-arm outcome build, or compare_and_swap_carrier; or the first real budget pause exercising the teardown on the pause arm.

## Closure (2026-09-19, P13 Task 4)

Pause-arm receipt forwarding landed at the outcome factory (`carrier_teardown=boundary.get("carrier_teardown")` beside the `carrier_rectified` forwarding); the runtime contract's `watcher-schedule` envelope sentence now names the pause-arm teardown receipt. New pause-shaped test `test_pause_boundary_outcome_carries_carrier_teardown` asserts a non-null receipt with the expected shape over an armed launchd carrier (bootstrap faked for hermeticity; bootout membership asserted, the pause chain reaches the carrier through more than one idempotent path). Discrimination witnessed 2026-09-19: with the forwarding line reverted the new test fails ("pause outcome dropped the computed carrier_teardown"); full suite 68 passed with the line in place.
