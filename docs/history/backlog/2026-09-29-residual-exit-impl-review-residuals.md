# Residual-exit ordering execution: impl-review r1 residuals

Origin class: consumer-company
Priority: low
Status: open

Two non-blocking residuals from the residual-exit same-day ordering execution's r1 review (landing 10dd0ec9). F1 (tzset skip arm) was fixed in-run (085bcb0b).

1. `testing#coverage-asymmetry-at-boundary-arm` (scripts/test_execute_plan_runtime.py ~12258): the retargeted `test_refuses_policy_recorded_after_verification_round`'s at-or-after strictness arm refuses without the refusal-preservation (manifest byte-identity) assertion its strictly-past sibling carries; the boundary-equality witness is the one refusal left unpinned.
2. `bookkeeping#whitespace-noise-in-progress-commit` (plan doc): the progress bookkeeping commit deleted blank lines beyond the checkbox flips; precert-flagged, non-semantic.
