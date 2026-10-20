# Backlog: runtime deployment verifier naming and remedy gaps

- **Filed:** 2026-10-21
- **Status:** open
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** code-quality (intermediate review findings F1/F2/F3/F5 of Task 2, docs/history/plans/2026-10-18-review-runtime-sibling-module-deployment.md)
- **Cluster:** docs/history/backlog/2026-10-21-runtime-deployer-test-pin-gaps.md; docs/history/backlog/2026-10-21-runtime-verifier-design-simplification.md; docs/history/backlog/2026-10-21-sync-runtime-scripts-prefixed-manifest-lines.md (shared runtime deployment scripts and verifier)

## Problem

Three Low findings in `scripts/verify_runtime_deployment.py` and one in `scripts/deploy_runtime_helpers.sh` survive review as valid but non-blocking:

1. An admitted entry whose canonical file is deleted while the runtime home still holds stale regular-file bytes escapes all verifier naming: `closure_scan` silently continues on missing canonical bytes and `run_probe` classifies canonical-missing only when the home also lacks the entry, so the stale bytes are copied and may probe clean (Edge-cases refusal property does not hold in this variant; the walk still prints its skip line, so it is not silent). Fix: classify canonical-missing by canonical existence first, regardless of home state. Folded by commit 37e687647: canonical-first classification landed (canonical-missing decided from canonical existence; a new not-canonical class names home bytes that are not symlinks into the canonical scripts directory and they are never copied or probed).
2. An unadmitted sibling whose bytes are unparseable gets class `unparseable` with the restore-or-drop remedy, whose "drop the manifest line" clause does not apply because no manifest line exists. Narrow remedy-wording mismatch only (still a named violation). Folded by commit 37e687647: unadmitted siblings get the restore-only remedy; a pinning test asserts the exact restore-only line (testing fold 2026-10-21).
3. The probe provenance assertion skips modules without `__file__`, so an out-of-root import resolving to a namespace package escapes it; the closure scan cannot see it either. Observation grade: the plan's pinned out-of-root cases use real .py files and are caught.
4. Check mode with a nonzero verifier exit (reachable only by a misbehaving verifier) says "the verifier could not run" although rc=1 means it ran; the advisory already names the re-run command.

## Evidence

- `scripts/verify_runtime_deployment.py` lines 70-72, 167, 179-183, 270-287.
- `scripts/deploy_runtime_helpers.sh` lines 224-228.

## Suggested fix

One pass over the verifier: extend the provenance assertion to namespace packages (or name the limitation in the header contract); reword the check-mode nonzero-exit advisory to "the verifier exited N" with the re-run command. (Items 1 and 2 are folded by commit 37e687647 and no longer carry work.)

## Round 3 additions (2026-10-21, review r3, all Low non-blocking)

5. The Exit-codes paragraph dropped the version-probe tool-error cause ("an interpreter that cannot answer the version query" is still coded exit 3 at scripts/verify_runtime_deployment.py run()); re-enumerate it.
6. The plan's Edge-cases sentence ("the probe then fails for that entry and deploy mode refuses") is superseded by the canonical-missing-first classification but only the RED-bullet wording is folded in the plan's Residual findings; extend that fold to the Edge-cases sentence at the next legitimate plan-text touch.
7. REMEDY_HOME_ABSENT and the deployer's missing-entry advisory lack the "from the primary checkout" qualifier that REMEDY_NOT_CANONICAL carries; a worktree-invoked healing run poisons symlinks in the home-absent case the same way.
