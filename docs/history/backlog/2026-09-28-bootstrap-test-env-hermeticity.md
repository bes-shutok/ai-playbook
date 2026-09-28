Status: open
Priority: low
Workflow: backlog
Class: test hermeticity (the fixture's subprocess calls inherit the ambient environment instead of a sanitized one)
Driving force: testability (hermeticity primary; flaky-run hygiene secondary)

# Bootstrap smoke test inherits the ambient environment in its two subprocess calls

**Exact location:** `scripts/test_execute_plan_worktree_bootstrap.py` - `run_readiness_validator` (builds `env = dict(os.environ)` and passes it to the validator subprocess) and the `test_recipe_block_executes_verbatim_and_gate_exits_zero` recipe invocation (`subprocess.run(["bash", "-c", recipe], cwd=str(worktree), capture_output=True, text=True)`, which inherits the parent environment wholesale); the `_git` helper inherits likewise.

## Problem

The smoke test drives the canonical Transfer-in recipe and the readiness validator with the inherited ambient environment. A session that carries `GIT_DIR`, `GIT_WORK_TREE`, or `GIT_INDEX_FILE` exports (for example a run launched from inside a manual worktree session), or a global git config with a `core.hooksPath`, mandatory hooks, or an `init.templateDir`, can redirect the fixture's git calls or the recipe's `git rev-parse`/`git worktree` plumbing away from the synthetic fixture and fail the run for reasons unrelated to the recipe. The failure direction is safe: this can only produce spurious red (a false failure of a load-bearing recipe), never a false green, because the fixture assertions still check real files in the real fixture worktree. No witnessed flake yet; the exposure is structural.

## Observed versus expected

- Observed: both subprocess calls run under the invoking session's ambient environment (validator explicitly via `dict(os.environ)`; recipe and `_git` by inheritance), so environmental leakage is a standing flake source.
- Expected: the two subprocess calls (and the `_git` helper) run under a sanitized environment - a minimal env carrying `PATH` and a scratch `HOME` (git config isolation), with `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`/`GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` explicitly unset or pinned to the fixture - so the test's verdict depends only on the fixture and the recipe bytes.

## Suggested fix

Build one module-level `sanitized_env()` helper and use it in the two subprocess calls (plus `_git` for consistency); keep the validator's `PLAN_READINESS_VALIDATOR` override on top of the sanitized base.

## Source reference

docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r3.md (round 3 address pass; staged finding set item "bootstrap test env hermeticity"). Capture hygiene: scan-public-hygiene --files pass (rc 0, recorded in the execution log review-r3-receiving-review.log.md). Why not fixed now: the r3 address pass is narrowly scoped and the suite is green in the run environment; touching the test harness's env plumbing late in the loop risks regenerating findings on a just-fixed surface (fix-risk triage), so it is captured as durable backlog. Severity: Low.

Dedup probe: searched the open backlog corpus (filenames plus Problem bodies) for "hermetic", "environment", "GIT_DIR", "smoke test": no open item owns this suite's env plumbing; the nearest items are r2's bootstrap-test anchor work (landed in the same file) and the testability family items under other suites; no overlap, no merge.

Origin class: self-serving
