# Backlog: execute-plan efficiency plan r11 review residuals (post-certification polish)

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-15
Class: plan-review residuals (post-certification capture per receiving-review Backlog capture)

Origin: docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md certified ready=yes with zero blocking findings at review round r11 (docs/reviews/2026-09-15-plan-review-execute-plan-review-fix-pipeline-efficiency-r11.md, sidecar digest 46951f1d773a028e929ccf49678a236ffd83db311e225ffd8ceee3872ed66f46, matching the certified plan bytes). Folding these four non-blocking findings would have changed the digest and voided that certification, so they are captured here instead. Fold them into the plan's first execution drift pass (each is small and precisely located) or a follow-up polish plan before or during execution.

## Findings

1. Medium (testing#missing-named-case, r11 F1): the `--operation interrupt` writer (Task 5) has no named test or validation pin anywhere in the plan, so a persistence regression in the interrupt stand-down's only input ships green. Suggested fix: add a named case (for example `test_interrupt_operation_persists_user_interrupt`) to `scripts/test_execute_plan_runtime.py` in Task 5's named-case list and a matching presence pin to the Validation block.
2. Medium (consistency#pin-prescription-mismatch, r11 F2): three Validation pins pin tokens no task prescribes as literal text, so a faithful implementation fails the Task 9 gate with an unplanned edit: the WATCH pins `report-only` and `progress_revision`, and the DRV pin `default-off \`batch\` opt-in on claim` (backtick inside the pinned span cannot match plain prescribed prose). Suggested fix: re-pin each to a span that occurs verbatim in the prescribing task text (for example `remains report-only`, `semantic progress revision`, `default-off batch opt-in on claim` without the inner backticks), or adjust the prescribed sentences to carry the pinned literals.
3. Low (testing#verification-coverage-gap, r11 F3): em-dash scan coverage is partial: Task 5's staged-diff scan omits `scripts/test_budget_guard_hooks.py` (which its Files list and bullets edit), Task 1's scan omits the driver and runtime-test files it stages, and the authoring-time RED record still says the em-dash scans live in "Tasks 4 and 8" while the Done-when bullet says Tasks 1, 4, 5, 6, and 8. Suggested fix: align each Python-editing task's staged-diff scan with that task's full Python Files list and make the RED record match the Done-when enumeration.
4. Low (consistency#invariant-task-contradiction, r11 F4): the Budget gate section the plan edits will contain two guard-flag cleanup disciplines side by side: the frozen pause-protocol step 5 (unlocked re-read-before-unlink with single-block retry) and the new locked compare-and-delete mandate (shared `fcntl.flock` lock). Suggested fix: when Task 5 lands, reword the pause-protocol step 5 cleanup clause to delegate to the locked compare-and-delete operation (one discipline, one owner), keeping the mirror deltas in sync.

## Why not fixed now

Round r11 certified the current bytes ready=yes with zero unresolved blocking findings, which is the loop exit condition; any post-certification fold changes the digest and voids the certification (plans Plan Quality Gate rule 2). The findings are non-blocking by the panel's severity calibration and are recorded here per the Backlog capture rule for valid unfixed findings.

## When to act

At the executing session's Step 0.4b-style plan-maintenance pass or the first review round of the execution (drift re-verification), before the affected task's commit gates run.

Related: docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md (the certified plan); docs/history/backlog/2026-09-15-budget-gate-pause-protocol-timing.md (the pause-protocol timing incident captured during the same authoring run).
