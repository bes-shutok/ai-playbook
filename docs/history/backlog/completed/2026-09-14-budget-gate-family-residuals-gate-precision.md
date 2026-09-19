# Backlog: budget-gate family residuals plan, validation-gate precision residuals

Status: done (closed moot 2026-09-16: host plan budget-gate-family-residuals EXECUTED+ARCHIVED (705a6bed); archived plan bodies are immutable, so the validation-gate precision residuals have no actionable surface)
Origin: review round r3 (docs/reviews/2026-09-14-plan-review-budget-gate-family-residuals-r3.md, ready=yes zero blocking) of docs/plans/2026-09-14-budget-gate-family-residuals.md; captured per the backlog capture rule instead of a fourth fold round, because the gate-precision family regenerated one Low per round across r1-r3 (the known non-converging fold family) and the plan is safe to execute without them
Date: 2026-09-14

Three non-blocking residuals on the plan's Validation Commands block, all one family (a gate witnesses less than an Evaluation Criteria claim):

1. Gate 5 witnesses the predicate's name presence (`grep -qF 'rollout_carries_rate_limits'`), not the maintainability claim that it is a pure module-level function; an anchored form (`grep -q '^def rollout_carries_rate_limits'`) would witness the definition site.
2. Gate 8's dead-pointer needle is CRLF-sensitive in its flattened form (`tr '\n' ' '` leaves a CR inside the wrapped phrase), so a wrapped `See the task log` pointer reintroduced with CRLF line endings could evade the sweep (measured in r3's overflow).
3. Gate 4's multiline guard only covers the arg-list-on-next-line shape; the escape-hatch bullet (a site keeping `subprocess.run` with `env=self._git_env`) has no multiline-aware check that the env is actually present on a wrapped call.

## Suggested fix

When the plan executes (or in a later gate-hardening pass), tighten the three needles per the list above and re-run the plan's Validation block plus the r3 negative controls. None blocks execution: the gates are fail-closed today and every defect class they miss is caught by review or the task-level verification bars.

## Why not fixed now

Folding any of them mutates the certified digest (ba3cce5c...) and forces a fourth round; the family has regenerated one new Low per fold for three consecutive rounds, so the expected convergence is zero. Dispositioned backlog-by-default per the ADR-0002 regenerating-class rule.
