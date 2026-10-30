# Backlog: machinery_registry.json no longer round-trips under its canonical serializer

- **Filed:** 2026-10-30, agent-type-affinity-before-plan-work Task 2 boundary learn
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (no gate is red and consumer runs proceed; the cost is a standing byte-smear hazard and a textual-insertion constraint inherited by every future registry editor)
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** reliability
- **Cluster:** docs/history/backlog/2026-10-30-machinery-inventory-post-repair-regrowth-two-release-scripts.md (same surface; that row registers two unregistered scripts, this row restores the file's byte round-trip; one registry session can carry both)
- **Cluster:** docs/history/backlog/2026-10-30-doctrine-text-precision-residuals.md (shared surface; that row fixes a registry note citation, this row fixes key-order drift; one registry session can carry both)
- **Skill/step:** `save_registry()` in `scripts/machinery_inventory.py` (the registry's single writer); `scripts/machinery_registry.json`
- **Dedup probe:** searched `docs/history/backlog/` contents for `round-trip`, `sort_keys`, `key-sort`, `canonical serializer`, `re-serializ`: nearest hits are the regrowth row's "stash round-trip" (a verification technique, not this defect) and the recursion row's writer-side `re-serialization` guard (JSON parse safety, not byte shape); no open row owns the registry byte-shape drift
- **Source reference:** docs/tmp/execute-plan/agent-type-affinity-before-plan-work/task-2-implement.log.md (the Registry byte-shape check note); capture hygiene: scan-public-hygiene pass, em-dash scan pass

## Problem

The registry's canonical form is whatever `save_registry()` writes: `json.dumps(registry, indent=2, sort_keys=True)` plus a trailing newline. The on-disk file does not round-trip under it: canonicalizing the current bytes reorders keys in at least three `removals` rows (`guard:maintenance-pins-recorded-red-consult`, `script:check-prompt-log-origins-receipt-without-removal-warning`, `release-recovery-push-rails`), whose keys sit in insertion order rather than sorted order. Consequences, witnessed while registering `protocol:agent-type-affinity-check` at the agent-type-affinity Task 2 boundary:

- Any code path that re-serializes (the `save_registry` call in the scaffold path) rewrites those rows' bytes, smearing unrelated pre-existing content into an unrelated diff.
- Editors must work by byte-preserving textual insertion, as Task 2 did; the workaround is now the standing practice and every future editor inherits the constraint and its schema-drift risk.
- The drift is invisible to `machinery_inventory.py --check`: the check validates row shape and witnesses, not key order, so a green check proves nothing about the round-trip.

## Expected

The file byte-identically round-trips under its own writer's canonical form (canonical dump of the parsed file equals the file bytes), so edits can re-serialize safely and diffs carry only intended changes.

## Suggested direction

A dedicated normalize-only change: re-serialize the current content through the canonical form (equivalently, key-sort the drifted `removals` rows in place), then verify (a) `git diff` touches only key ordering on the drifted rows, (b) `machinery_inventory.py --check` reports no new failure beyond the known regrowth reds, and (c) a canonical dump of the parsed file equals the file bytes. Note the machinery registry is plan-route-only on the eligibility denylist, so the normalize change routes through a plan; any registry-touching session (see the two cluster rows) can carry it as a rider within that plan's own scope rules.

## Why not fixed now

The witnessing task registered its blocker by textual insertion precisely to avoid rewriting unrelated pre-existing bytes inside a plan-scoped diff, and the registry is plan-route-only; the learn boundary captures outside-scope witnessed defects and does not repair them.
