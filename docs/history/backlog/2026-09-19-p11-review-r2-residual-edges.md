# Backlog: P11 review r2 residual edges

Status: open
Origin: P11 execution review r2 (docs/reviews/2026-09-19-execute-plan-orchestration-authority-loop-bounds-release-gates-code-review-r2.md, NF1/NF2)
Date: 2026-09-19

Two non-blocking Lows from the post-fix round:
1. NF1: a huge-int `recorded_at` in the terminal pre-archive `residual_policy` input overflows the `float()` coercion; `OverflowError` escapes `main()`'s except tuple and prints a traceback instead of a blocked envelope (fail-closed, no writes; refusal point precedes all filesystem work).
2. NF2: position-based ownership identity in `plan_ownership_problem` can false-trip `consumer-before-owner` when a creation record lives in a later `#### Step N.x` subsection's Files block; zero corpus exposure (no `#### Task/Step` headings in any live or completed plan); fail-closed direction; the reason string is self-contradictory in that shape.

Fix shapes: (1) add `ArithmeticError` (or an overflow-aware coercion) to the CLI's except tuple with a blocked-envelope reason; (2) exclude subsection headings from the ownership section splitter or reorder the reason string to name both sections. Pin both shapes with a selftest arm each.

Trigger: next edit to `_normalize_residual_policy`/the CLI except tuple (1) or the ownership section splitter (2).
