# Backlog: runtime deployment test pin gaps (site flags, deployed-symlink invocation, verifier twin)

- **Filed:** 2026-10-21
- **Status:** open
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** code-quality (intermediate review findings of Task 2, docs/history/plans/2026-10-18-review-runtime-sibling-module-deployment.md)
- **Cluster:** docs/history/backlog/2026-10-21-runtime-verifier-design-simplification.md; docs/history/backlog/2026-10-21-runtime-verifier-naming-and-remedy-gaps.md; docs/history/backlog/2026-10-21-sync-runtime-scripts-prefixed-manifest-lines.md (shared runtime deployment scripts and verifier)

## Problem

The Task 2 suite (22 tests, all green) leaves three pin gaps, all verified non-blocking by mutation testing:

1. The probe child's `-S` (and `-B`, and the redundant PYTHONPATH strip) flag is pinned only through `-I`'s observable effect; removing `-S` passes the whole suite. A discriminating test needs a fixture entry importing a name shadowed from a polluted system site-packages, unobservable in clean fixtures.
2. No test invokes the deployer through the deployed home symlink (the production arm the realpath resolution rule exists for); the lone-copy test pins only the refusal text. Candidate fix: one arm running `bash "$runtime/deploy_runtime_helpers.sh" --check` after a deploy and expecting the resolved-verification path, not the skipped advisory.
3. The re-pinned ghost-entry arm asserts `verify-canonical-missing: ghost.py` with the restore-or-drop remedy where the plan's RED bullet 4 says "refuses naming its import-probe failure". The test is right (a probe-fail classification cannot fire for a home-absent entry). Recorded: the wording amendment is now the plan's Residual findings line testing#ghost-arm-pin-wording (F7, disposition folded), so this item's trigger has fired and carries no remaining work.

## Evidence

- `scripts/test_deploy_runtime_helpers.py` lines 389-404, 582-614; `scripts/verify_runtime_deployment.py` line 239 (probe invocation).

## Suggested fix

Add the two witness arms (polluted-site probe fixture; deployed-symlink invocation). Item 3 is closed by the plan's Residual findings line testing#ghost-arm-pin-wording (recorded 2026-10-21).

## Round 3 addition (2026-10-21, review r3)

4. REMEDY_BYTES is never asserted verbatim for the admitted unreadable/unparseable arms (only class+name); one assertIn of "restore the canonical file or drop its manifest line" in test_unreadable_entrypoint_is_named pins it. (Observation, no action: the containment-not-name-matching property of canonical_link_realpath is by contract; the deployer walk converges mis-aims.)
