# Certification residuals: dirt-gate-removal-only-cleanup-passing

- **Filed:** 2026-10-17, the r5 certifying round (ready=yes, zero blocking, focused panel)
- **Status:** open
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** certification-residual (review-plan cap-closure routing)
Cluster: docs/history/plans/2026-10-17-dirt-gate-removal-only-cleanup-passing.md (the certified plan; its landing serves the parent origin)

## Residuals (deferred at certification, none blocking)

1. The incident-arm fixture spec should carry an explicit partial-removal clause (the dirt leaves at least one gained line in the worktree), so a literal all-gained-deleted fixture cannot land on the accepted residual boundary and fail green-less at Task 2 (r5 F1, testing#incident-fixture-residual-collision).
2. The Validation Commands should pin the two later arm defs (`test_pure_append_whole_reversion_still_regression`, `test_set_equal_list_unequal_worktree_passes`) with expect1 lines, so dropping or renaming them cannot pass the battery (r5 F2, testing#missing-gate-needle).
3. The hermeticity strip list should extend to GIT_CONFIG_PARAMETERS, GIT_OBJECT_DIRECTORY, and GIT_ALTERNATE_OBJECT_DIRECTORIES (r5 F3, testing#hermeticity-gap; measured no verdict flip).
4. The validation battery may optionally run the neighboring gate-executing suite `scripts/test_parallel_work_regressions.py` (r5 F4, quality#validation-battery-omits-neighbor-gate-suite; measured 3 of 3 green against the planned classifier).

Executor note: include the strip-list extensions and the two expect1 pins in the execution's own validation pass even before adopting the residual row's items; all four are one-line-scale.
