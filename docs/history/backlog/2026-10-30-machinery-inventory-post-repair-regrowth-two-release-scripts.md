# Backlog: machinery_inventory --check red again on two unregistered release scripts

- **Filed:** 2026-10-30, agent-type-affinity-before-plan-work Task 1 boundary learn
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** reliability
- **Cluster:** docs/history/backlog/2026-10-25-machinery-inventory-check-preexisting-red.md (same defect class and surface; that row's 2026-10-29 repair landed the green baseline this row's witness post-dates)
- **Cluster:** docs/history/backlog/2026-10-23-machinery-inventory-baseline-red-obscures-regrowth.md (the masking consequence class: a red baseline hides new regrowth)
- **Cluster:** docs/history/backlog/2026-10-30-review-plan-attempt-state-pin-stale-at-baseline.md (same defect class: a repo-wide gate red at baseline; mechanisms differ per member)
- **Cluster:** docs/history/backlog/2026-10-30-doctrine-text-precision-residuals.md (shared surface: `scripts/machinery_registry.json`; that row fixes a registry note citation, this row registers two scripts)
- **Cluster:** docs/history/backlog/2026-10-30-machinery-registry-canonical-serializer-non-round-trip.md (same surface; that row restores the registry's canonical-serializer byte round-trip, this row registers two unregistered scripts; one registry session can carry both)
- **Skill/step:** `scripts/machinery_inventory.py --check`; `scripts/machinery_registry.json`
- **Dedup probe:** searched `docs/history/backlog/` for `machinery_inventory`, `release-diagnostic-replay`, `release-privacy-locators`, `unregistered`: nearest are the two covered cluster rows (their dispositions closed the 2026-10-29 failure set; neither owns post-repair regrowth) and the 2026-10-30 release-* rows (they name the same scripts for other defects: replay TOCTOU, locator exit codes, control escapes; none covers registration)
- **Source reference:** docs/tmp/execute-plan/agent-type-affinity-before-plan-work/task-1-implement.log.md (Task 1 validation commands); capture hygiene: scan-public-hygiene --files pass

## Problem

`python3 scripts/machinery_inventory.py --check` exits 1 with 2 regrowth failures at the current base: `regrowth: unregistered script file scripts/release-diagnostic-replay.sh` and `regrowth: unregistered script file scripts/release-privacy-locators.py`. Both scripts landed in 0a3c1ee34 (2026-10-30 19:28 UTC) after the green-baseline repair in 42e48cd61 (2026-10-30 14:58 UTC, disposition of the covered cluster rows), so the baseline is red again hours after it was asserted green. While red, a genuinely new unregistered script cannot be distinguished from this noise, and any plan whose Validation Commands include the bare `--check` cannot reach green. Witnessed at the agent-type-affinity Task 1 boundary: the task's validation ran the check, verified the red pre-existing via a stash round-trip, and reported it instead of repairing it.

## Expected

Every tracked script is registered (or explicitly exempted) in `scripts/machinery_registry.json` in the same landing that adds it, so the check stays green at baseline and regrowth detection keeps signal.

## Suggested direction

Register both scripts as keep rows with resolving witnesses (the registry-only shape the covered rows' 2026-10-29 repair used), run the fixture suite, and re-assert the green baseline with the check's ok line quoted. Also consider naming the registration step in the release landing lane's checklist so the next release script does not reopen this class.

## Why not fixed now

The witnessing task's allowed file list excluded `scripts/machinery_registry.json`; the learn boundary captures outside-scope witnessed defects and does not repair them.
