# Backlog: Profiling harness residuals (probe correction input set, fixture git env, minor analysis arms)

Driving force: correctness
Cluster: hook-timeout-recurrence-diagnostic follow-ups
Status: open

## Items

1. Interpreter-probe correction input set: the session-channel (b) correction re-check feeds the interpreter-probe share into the runner-up ranking while `stage_shares` excludes the probe (`scripts/profile_skill_gate_consult.py:716-726` vs `:444-465`) — two input sets for one dominance rule. Strictly conservative today (can only suppress a (b) mapping); unify before the probe share grows.
2. Fixture git calls run under the ambient environment: `build_sandbox`'s `git init/add/commit` and `run_self_checks`' `git rev-parse` inherit global git config, so a global `core.hooksPath` executes user hook code against the fixture and `commit.gpgsign` can abort spuriously. Set `GIT_CONFIG_GLOBAL=/dev/null` (or equivalent) on those calls.
3. Minor: analyze takes the last emission-off repeat's p95 silently; per-worker `resolver_probe_timed_out` flag is copied statically into emission-off samples.

Witnesses: exec-r1 correctness lens F-C2 + suggestions, safety lens F1 (.ai-playbook/reviews/2026-11-09-plan-review-hook-timeout-recurrence-diagnostic-exec-r1-lens-{correctness,safety}.md, worktree branch 2026-11-09-hook-consult-profiling).
