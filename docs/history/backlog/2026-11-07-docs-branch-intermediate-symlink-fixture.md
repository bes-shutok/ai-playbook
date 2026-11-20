# Backlog: docs-branch intermediate symlink fixture skips before exercising containment

- **Filed:** 2026-11-07, learn Step 1.9 during test-suite runtime reduction Task 1
- **Status:** open
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fence-class
- **Driving force:** reliability

## Problem

The intermediate-symlink traversal test does not currently exercise its intended path. The baseline run recorded it as skipped after symlink creation raised `ENOENT`. In `scripts/test_docs_branch_sync.py`, the fixture creates `.ai-playbook/reviews/` but not the `docs/` parent before creating `docs/escape`. That link is also outside the selected `.ai-playbook/reviews` archive root. The `traversal.md` target begins with `../../escape`, so `symlink_target_is_under` encounters a parent step that leaves the allowed root before the path can reach any `escape` component; the target also never names `docs/escape`. Adding `docs/` alone would stop the local ENOENT but still would not exercise the named intermediate-symlink path.

## Evidence

- `scripts/test_docs_branch_sync.py`, `DocsBranchSyncTests.test_intermediate_symlink_then_parent_traversal_refuses_without_ref_change` (fixture lines 1061-1073).
- `docs/history/feature-notes/2026-11-06-test-suite-runtime-reduction-baseline.md`, baseline outcome: this was the sole skipped test; symlink creation raised `ENOENT`.
- `scripts/docs_branch_sync.sh`, `symlink_target_is_under`: the traversal check returns false as soon as a `..` step leaves its supplied archive root. The fixture target reaches that step before its `escape` component.

## Suggested fix

Place the intermediate symlink under the allowed archive root and construct the traversal link so it encounters that symlink before applying a parent step. Keep the test asserting containment refusal, unchanged `docs` ref, and absence of snapshot, prune, and ref-update trace events. Confirm the repaired test runs rather than skips and that it reaches the intended symlink-aware check.

## Why not fixed now

The active plan task owns runtime reduction in the wrapper and landing-squash suites. This fixture is an unrelated docs-branch security-coverage gap, so changing it would expand Task 1 scope.

## Capture review

Keyword search of the open backlog found no item for this fixture or its path-resolution failure. The nearest match, `docs/history/backlog/2026-10-21-runtime-deployer-test-pin-gaps.md`, concerns runtime deployment test pins and does not cover docs-branch fixture setup or symlink traversal. This is a repository-test coverage issue, not a skill-corpus defect.

Capture hygiene: `scan-public-hygiene.sh --files` and `check-no-em-dash.sh file` passed before commit.
