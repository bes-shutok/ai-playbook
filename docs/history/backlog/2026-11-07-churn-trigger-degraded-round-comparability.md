# Review-plan churn-trigger trajectory comparison counts a coverage-degraded round as a comparable trajectory point

- **Filed:** 2026-11-07, learn Step 1.8 capture from the budget-resume-carrier-gc authoring session (r2-r4 review loop)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (a degraded round's totals can spuriously fire the non-convergence machinery, whose terminal state is an operator pause)
- **Origin class:** session-witnessed flow gap (review-plan loop rule, the churn-trigger definition)
- **Class:** fix-class
- **Skill/step:** `agents/skills/review-plan/SKILL.md` (the loop rule's churn-trigger sentence: "total staged findings not decreasing across the two most recent rounds, or a positive open-blocking count not decreasing across two consecutive rounds")
- **Source reference:** worktree `.ai-playbook/reviews/2026-11-07-plan-review-budget-resume-carrier-gc-pc377ff97-r2.stats.json` (coverage outcome degraded, one of five workers completed) and `-r3.md` (the orchestrator's ad hoc degraded-round exclusion argument in Triage outcomes); capture hygiene: `scan-public-hygiene.sh` pass, `check-no-em-dash.sh added-lines` pass
- **Why not fixed now:** the session's loop is paused at an operator gate; the trigger definition is pinned loop text whose amendment belongs to its own authoring lane
- **Dedup probe:** searched open backlog rows for `churn`, `degraded`, `trajectory`; no open row on the trigger's round comparability; no merge

## Problem

The churn triggers compare the two most recent rounds' staged-findings and open-blocking totals. A round whose coverage outcome is `degraded` (workers timed out, hit usage walls, or were skipped) contributes totals from a fraction of the panel; comparing those totals literally against the adjacent full-panel rounds both under- and over-fires the trigger. In the witnessed run, the degraded r2 (1 of 5 workers, 4 staged) against the full r3 (13 staged) reads as "not decreasing" on the literal text, and the orchestrator had to improvise an exclusion argument (degraded rounds are not comparable trajectory points; the comparable full-panel trajectory strictly decreases) inside the round record to proceed without operator direction.

## Expected

The trigger definition states which rounds are comparable trajectory points: a coverage-degraded round (coverage outcome `degraded` or `failed`, or any panel row skipped) is excluded from the comparison window, and the comparison runs over the most recent comparable rounds instead; when fewer than two comparable rounds exist, the loop continues one round to establish the baseline rather than firing. The exclusion records one line in the round's convergence telemetry so the reconciliation pass can audit it.

## Suggested fix

Amend the churn-trigger sentence with the comparability clause and mirror it in review-reconciliation's trigger section, using the witnessed r2-r3 pair as the incident witness. The r4 checkpoint's literal firing (staged 13 to 14, blocking 3 to 5 across two full-panel rounds) was a true positive and is not affected by the fix.
