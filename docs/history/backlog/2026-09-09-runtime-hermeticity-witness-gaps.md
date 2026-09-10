# Runtime hermeticity witness gaps: env sanitization, live-installation read, ambient manifest read, clock/tz/locale assertions

Status: open
Workflow: backlog
Source: docs/reviews/2026-09-09-plan-review-agent-agnostic-execute-plan-r8.md (re-cert round r8), findings F2 + F4 (Medium/Low, non-blocking; deferred from execution of docs/plans/2026-09-09-agent-agnostic-execute-plan.md)

## Problem

1. **F2 (`implementation#missing-acceptance-witness`, Medium)**: the hermeticity checklist item reworded during execution (commit 41a6505) dropped two observables that no test owns:
   - Subprocess environment sanitization: `_subprocess_runner` in `scripts/execute_plan_runtime_codex.py` filters the environment to `SAFE_ENV_KEYS = {PATH, HOME, LANG, LC_ALL, TZ, TMPDIR}` and injects the policy token, but no test references `SAFE_ENV_KEYS`, `environ`, or `EXECUTE_PLAN_POLICY_TOKEN`. A regression leaking the full parent environment (credentials, host session data) into worker subprocesses would pass the whole suite. `test_real_owned_process_group_is_cleaned_on_timeout` runs the real runner but asserts only process-tree cleanup.
   - Live-installation read denial: the old item asserted "no live installation is read"; no test asserts that anywhere (grep over all three test files returns nothing). Only implicitly true because runners are injected.
   - Adjacent: `CodexAdapter.__init__` reads `EXECUTE_PLAN_PACKAGE_MANIFEST` from the ambient environment with no test covering that read path.
2. **F4 (`testing#set-but-unasserted-boundary`, Low)**: `test_runtime_replay_is_hermetic_to_fixture_root` sets `LANG=C`, `LC_ALL=C`, `TZ=UTC` in the fixture environment but the subprocess round-trip asserts only `cwd` and `HOME`; there is no clock-freeze/advance seam anywhere in the suite. The clock/timezone/locale boundary listed in the plan item is set-but-never-verified.

## Location

- `scripts/test_execute_plan_runtime_codex.py` (add env-sanitization + ambient-manifest-read witnesses)
- `scripts/test_execute_plan_runtime.py` (`test_runtime_replay_is_hermetic_to_fixture_root`, ~lines 807-840: extend round-trip assertions to TZ/LANG/LC_ALL)
- `scripts/execute_plan_runtime_codex.py` (`SAFE_ENV_KEYS` ~line 22, `_subprocess_runner` ~lines 42-48, `CodexAdapter.__init__` ~lines 157-164)

## Suggested fix

Add one discriminating test per dropped witness: (1) launch through the real `_subprocess_runner` with a poisoned parent environment and assert the child sees only `SAFE_ENV_KEYS` plus the policy token; (2) assert the driver/adapter never opens a path under a seeded live-installation root (point `HOME`/package manifest at a fixture and assert no read outside it); (3) cover the `EXECUTE_PLAN_PACKAGE_MANIFEST` ambient read (missing var → fail-closed, valid var → loaded); (4) extend the hermeticity round-trip to assert TZ/LANG/LC_ALL take effect in the child.

## Severity

Medium (F2), Low (F4). Regression-detection gaps, not current behavioral defects: the suite is green (42+18 tests) and the implemented behavior is correct as of 22259a2.

## Why not fixed now

Execution of the plan was complete (all tasks landed, Phase 3 code review rounds r1-r3 done) when the re-cert surfaced these; adding test witnesses mid-resume would mutate the digest the pending Phase 3 round-4 fresh review was about to cover and extend the run's review budget for non-blocking residuals. Deferred per the backlog-capture rule.
