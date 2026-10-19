# Backlog: direct gate runs on a completed-archive plan path derive the wrong source identity

- **Filed:** 2026-10-19, fifth max-4 exec-run learn capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Skill/step:** `scripts/worktree_closeout_migrate.py` `gate-removal` / `verify-records` identity derivation (`_plan_identity_for`); the `--plan-identity` override
- **Driving force:** correctness (warning noise trains operators to ignore the diagnostic tier)

Cluster: docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md (same defect class: a record citing a path that moved to the completed archive)

## Problem

When `gate-removal` or `verify-records` runs directly with `--plan docs/history/plans/completed/<file>.md`, `_plan_identity_for` derives the completed-archive path as the source identity, while the plan's review records carry tokens and identities derived from the original plans-root path - so every series member reports a spurious foreign-identity warning. The sanctioned flow is unaffected (the completed-twin runner passes the original plans-root path through `--plan-identity`, pinned by test), and the warnings are read-only, but a direct run on an archived plan warns on every record.

## Expected

The smallest fix: when the resolved plan path sits under the completed archive, derive the identity from the original plans-root path (`docs/history/plans/<basename>`) unless `--plan-identity` overrides it - mirroring exactly what `_run_gate_on_twin` already passes. Bounded by the machinery admission protocol: a derivation correction on an existing read-only surface, no new gate, no behavior change for plans-root paths.

## Evidence

Witnessed 2026-10-19 (playbook repo, fifth max-4 exec run): the execution review of the series-token plan observed that a direct `gate-removal`/`verify-records` run on `docs/history/plans/completed/2026-10-18-closeout-gate-series-token-infix.md` warns for every record; recorded as the reviewer's accepted non-blocking observation (finding 6), with the twin wiring correct and pinned.

## Notes

Low priority: noise only on the direct-run shape; the operative closeout paths are clean.
