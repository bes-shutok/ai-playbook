# Residual-exit ordering execution: impl-review r1 residuals

Cluster: docs/history/backlog/2026-09-29-p93-impl-review-nonblocking-residuals.md
Cluster: docs/history/backlog/2026-09-29-execute-plan-review-residuals.md
Cluster: docs/history/backlog/2026-09-30-emdash-residuals-exec-review-residuals.md
Cluster: docs/history/backlog/2026-09-30-prelaunch-recovery-impl-review-residuals.md


Origin class: consumer-company
Priority: low
Status: done (2026-10-01; family closeout executed+landed docs/history/plans/completed/2026-09-30-impl-review-residuals-family.md, squash main db5786c2, exec review r1 ready=yes zero blocking)(docs/history/plans/2026-09-30-impl-review-residuals-family.md)

Two non-blocking residuals from the residual-exit same-day ordering execution's r1 review (landing 10dd0ec9). F1 (tzset skip arm) was fixed in-run (085bcb0b).

1. `testing#coverage-asymmetry-at-boundary-arm` (scripts/test_execute_plan_runtime.py ~12258): the retargeted `test_refuses_policy_recorded_after_verification_round`'s at-or-after strictness arm refuses without the refusal-preservation (manifest byte-identity) assertion its strictly-past sibling carries; the boundary-equality witness is the one refusal left unpinned.
2. `bookkeeping#whitespace-noise-in-progress-commit` (plan doc): the progress bookkeeping commit deleted blank lines beyond the checkbox flips; precert-flagged, non-semantic.
