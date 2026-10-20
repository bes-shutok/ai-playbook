# Backlog: runtime deployment verifier design simplifications

- **Filed:** 2026-10-21
- **Status:** open
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** code-quality (r2 design lens findings of docs/history/plans/2026-10-18-review-runtime-sibling-module-deployment.md)
- **Cluster:** docs/history/backlog/2026-10-21-runtime-deployer-test-pin-gaps.md; docs/history/backlog/2026-10-21-runtime-verifier-naming-and-remedy-gaps.md; docs/history/backlog/2026-10-21-sync-runtime-scripts-prefixed-manifest-lines.md (shared runtime deployment scripts and verifier)

## Problem

The verifier and its carrier carry accepted non-blocking design debt; each item is a simplification, not a behavior bug, so none of it blocks this plan:

- The verifier carries a needless `--mode` axis duplicating the deployer's own check contract: delete `--manifest` and `--mode`, exit 1 on any violation, and the deployer maps rc 1 to advisories in check mode.
- `resolve_interpreter` spends 30 lines and a 30s subprocess probe on a fact `sys.executable` already carries: replace with `sys.executable` plus its version string, and add OSError to `probe_one`'s except set.
- Inert named/remember dedup in `run_probe` (each entry is visited once per loop).
- Dual `UsageError`/`ToolError` classes with identical handling: `Parser.error` can raise `ToolError` directly.
- Dead defensive guards: the `hasattr(sys, "stdlib_module_names")` check and `imported_tops`' falsy-top filter.
- The deployer header restates the verifier docstring; keep the integration facts and point at the docstring for the rest.
- Test helpers `assert_pass`/`assert_refused` overlap `assert_outcome` and never pin exactly-one-OUTCOME-line.

## Evidence

- `scripts/verify_runtime_deployment.py` lines 108-169, 236-256, 313-344, 363-399, 403-413.
- `scripts/deploy_runtime_helpers.sh` lines 33-58.
- `scripts/test_deploy_runtime_helpers.py` lines 44-79.

## Suggested fix

One simplification pass landing the deletions with the suite green, after this plan lands.
