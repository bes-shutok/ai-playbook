# Host-dependent home-surface sweep makes the reintroduction guard vacuous off-host

Status: open
Workflow: backlog

## Problem statement

`test_removed_controls_absent_from_active_entrypoints` hardcodes this operator's five home entrypoint files and five hook-config paths with an exists-then-skip design: on any other machine every path is absent, the test skips, and the removed-controls reintroduction guard silently covers only repo surfaces. A green run on a fresh checkout asserts nothing about host wiring (the docstring discloses this). The operator-specific path list also lives in a public repo script rather than externalized configuration.

Evidence: `scripts/test_harness_policy_contract.py`, `HOME_ENTRYPOINT_FILES` / `HOME_HOOK_CONFIG_FILES` constants consumed by the named test; ambient-input note: the sweep only asserts substring absence in-process, so running the suite creates no privacy side effect.

## Location

- `scripts/test_harness_policy_contract.py` — `HOME_ENTRYPOINT_FILES`, `HOME_HOOK_CONFIG_FILES`, `test_removed_controls_absent_from_active_entrypoints`

## Suggested fix

If portability matters, derive the surface list from an optional facts/config key (for example a `home_entrypoint_files` / `home_hook_config_files` pair) with the current list as the fallback default, per the repository's configuration-externalization convention.

## Severity and source reference

Low. Source: code review round r1 finding F4 (testing worker), `docs/reviews/2026-09-23-code-review-ai-harness-friction-audit-r1.md`. Capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

Non-blocking Low finding triaged to backlog capture by the r1 address-phase instruction. Acceptable as shipped for the single-operator host: the skip is recorded and the repo-side twin of the sweep carries the real coverage.

Driving force: testability, secondary: maintainability
