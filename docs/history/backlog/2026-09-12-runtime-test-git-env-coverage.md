# Backlog: apply the hermetic git env to every git subprocess call site in the runtime test harness

Status: open
Origin: review r5 T-R5-1 (execute-plan runtime guardrails; round-cap deferral, zero blocking)
Discovered: 2026-09-12

The r4 fix (commit 2e74e33) introduced `self._git_env` (GIT_CONFIG_GLOBAL/SYSTEM=/dev/null) in `scripts/test_execute_plan_runtime.py` but applied it at only ~10 of ~56 git subprocess call sites. The rest (commit/link/rebase/cherry-pick helpers at roughly lines 663, 1019, 1049, 1285, 2473-2519) still inherit host config: `commit.gpgsign`, `core.hooksPath`, `sequence.editor` can fail or skew fixture repos on configured hosts. Fix: route every call through one `self._git(*args)` helper that always injects `self._git_env`, so new call sites cannot skip it.

Witness: a host with `commit.gpgsign=true` makes fixture commits raise CalledProcessError outside the assertions (environment-dependent suite).
