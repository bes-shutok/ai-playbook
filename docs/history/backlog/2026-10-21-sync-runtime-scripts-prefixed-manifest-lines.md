# Backlog: sync_runtime_scripts.sh does not basename-map scripts/-prefixed manifest lines

- **Filed:** 2026-10-21
- **Status:** open
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** code-quality (off-plan finding from the Task 1 intermediate review of docs/history/plans/2026-10-18-review-runtime-sibling-module-deployment.md)
- **Cluster:** docs/history/backlog/2026-10-21-runtime-deployer-test-pin-gaps.md; docs/history/backlog/2026-10-21-runtime-verifier-design-simplification.md; docs/history/backlog/2026-10-21-runtime-verifier-naming-and-remedy-gaps.md (shared runtime deployment scripts and verifier)

## Problem

`scripts/sync_runtime_scripts.sh` joins each manifest name directly onto the canonical `scripts/` directory (`canon_entry="$CANON/$name"`), while `scripts/deploy_runtime_helpers.sh` basename-maps `scripts/`-prefixed lines. The two prefixed entries in `scripts/runtime-scripts.list` (`scripts/land_squash.sh`, `scripts/test_land_squash.py`) therefore resolve to a nonexistent `scripts/scripts/` path under sync and escalate as "absent both deployed and canonical" (exit 1) on any sync run.

## Evidence

- `scripts/sync_runtime_scripts.sh` lines 97-178 (direct join, no basename mapping).
- `scripts/deploy_runtime_helpers.sh` line 145 (basename mapping of prefixed lines).
- `scripts/runtime-scripts.list` (the two prefixed entries).

## Suggested fix

Either basename-map in sync exactly as the deployer does, or drop the `scripts/` prefix from the two manifest lines. The census section 6 disposition pins the deployer as the enforcement owner with sync deferring to it, so the first option keeps the two scripts' behavior aligned without a manifest change.
