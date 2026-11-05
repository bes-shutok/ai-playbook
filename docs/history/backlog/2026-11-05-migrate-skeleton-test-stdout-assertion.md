# Backlog: worktree-closeout-migrate skeleton-producer test still asserts stdout after the eval-safe stderr split

Status: open
Priority: high
Class: fence-class
Driving force: reliability
Added: 2026-11-05, memory-index-load-budget-consolidation execution run (learn Step 1.9; full-suite witness)
Capture hygiene: `scan-public-hygiene.sh` pass.
Cluster: docs/history/backlog/2026-11-02-closeout-migrate-manifest-flag-kind-ambiguity.md (same worktree-closeout-migrate test/machinery family)
Origin class: self-serving

## Problem

`scripts/test_worktree_closeout_migrate.py::ZeroPlanMigrateSkeletonProducerTest::test_zero_plan_run_emits_skeleton_beside_skip_record` asserts `"migrate-shape manifest skeleton present"` in the producer's **stdout**, but the eval-safe emission contract landed by the done-run-setup-stdout-export-emission-split execution (acquisition stdout carries only `export `-prefixed lines; every status, advisory, and diagnostic line routes to stderr) moved this class of emission to stderr. The producer now runs clean and writes the skeleton, the assertion reads empty stdout, and the test fails - so every full-suite run at current HEAD is red (1 failed / 3431 passed on 2026-11-05).

The failure is verified pre-existing at main (fails identically at the base-tip descendant f0f895ce2 and at the landing tip), not introduced by the witnessing run (docs-only diff).

## Exact location

- `scripts/test_worktree_closeout_migrate.py` (ZeroPlanMigrateSkeletonProducerTest::test_zero_plan_run_emits_skeleton_beside_skip_record, the `assertIn("migrate-shape manifest skeleton present", proc.stdout)` line)

## Suggested direction

One test edit: assert the message on `proc.stderr` (matching the eval-safe contract the split landing pinned) or on the combined output, whichever the suite's other emission assertions use; re-run the single test and the full suite to green.

## Evidence

- Witnessed 2026-11-05, full scripts suite (3431 passed, 1 failed, 271 subtests passed, 1h04m): the failure reproduced in three trees (primary main, landing tip, fresh single-test runs)
- The emission contract: the done-run-setup-stdout-export-emission-split landing (`9c5b34551`, 2026-11-05) - its wrapper suite (224 tests) does not collect this test file, which is how the stale assertion survived that landing's gates
