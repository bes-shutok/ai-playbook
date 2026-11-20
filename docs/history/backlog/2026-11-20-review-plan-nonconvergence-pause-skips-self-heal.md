Status: covered-pending-execution (docs/history/plans/2026-11-20-review-plan-nonconvergence-self-heal-at-round-close.md)
Workflow: backlog
Priority: medium
Class: fix-class (the review loop paused on a churn trigger without the mandated self-heal assessment; the simplification only happened after a user reply)
Origin class: session-witnessed stop (Claude Code, session 883322f3, 2026-11-20)
Driving force: automation (primary), simplicity (secondary)
Added: 2026-11-20
Cluster: docs/history/backlog/2026-11-20-direct-maintenance-invocation-asks-instead-of-deciding.md

# The plan-review loop parked on non-convergence and asked the user instead of reconciling and invoking self-heal

## Problem

Plan `2026-11-20-plan-review-gate-hook-round-tie` took five review rounds with blocking counts 4, 5, 1, 2 across rounds 1 to 4. `review-plan` (Scope and complexity policy) says an active churn trigger means reconcile, then invoke `self-heal` once (when the plan authorizes the attempt and the run-wide attempt state is unused), then pause. The session did neither: it paused after round 4, wrote a summary with a recommended simplification, and waited for the user. Only the user reply "sure" released the simplification, which then converged in one round (round 5, zero blocking).

## Observed vs expected

Observed: the trigger (blocking count rose from 1 to 2 between comparable rounds) was recognized by hand at the end, not at the round-close where the sidecars were written; `extensions.convergence` counters and `self_heal_attempt` state were not consulted for the decision; no `self-heal` invocation occurred.
Expected: at round close the loop reads the convergence counters, and on a trigger runs reconciliation and the one self-heal assessment itself; an unattended or standing-authorized run continues with the simplification the assessment names, and pauses only when no authorized option exists.

## Evidence (trimmed)

- Round records r1 to r5 in `.ai-playbook/reviews/` (plan-review series for the slug `plan-review-gate-hook-round-tie`); the folds after r2 and r3 each introduced the next round's blocking defect (an anchored regex that hid dated slugs, witnesses without verdicts).
- The plan-format two-round alarm ("the mechanism is too novel: split the mechanism") also applied from round 2 and was not acted on.

## Suspected root area

- `agents/skills/review-plan/SKILL.md` round-close and Scope and complexity policy; `agents/skills/plans/plan-quality-gate.md` loop rules. Investigate whether the trigger evaluation is mechanical anywhere (a script that returns the required next action from the sidecars) before adding anything; prefer reading the existing sidecar counters over new machinery.

## Ship when

A non-converging review loop run under standing authorization invokes `self-heal` at the trigger, applies its authorized simplification, and reaches a review round without a user question.

Dedup probe: searched backlog and plans for `non-converg`, `churn`, `self_heal_attempt`, `two-round alarm`, `before any pause`; `2026-11-16-interactive-session-gate-asks-without-self-heal-consult.md` (closed: no skill-text change warranted) covers interactive gate asks and is distinct (this row is the unattended loop's churn path); no open row covers it.
