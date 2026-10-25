# Backlog: authoring stopped after explicit operator reauthorization instead of resuming

- **Filed:** 2026-10-25, observed while resuming the done-finalize plan authoring lane
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** session-witnessed execution friction
- **Class:** design-class (whether an existing continuation contract needs one clearer caller instruction spans multiple skill owners)
- **Driving force:** reliability + continuity
- **Skill/step:** `agents/skills/maintenance/decisions.md` Blocker recovery; `agents/skills/review-reconciliation/SKILL.md` section 4; `agents/skills/review-plan/SKILL.md` Step 5

## Problem

The plan changed after its latest review, making the recorded r13 source digest stale and requiring one fresh review under the existing plan-review workflow. The operator then explicitly directed the session to proceed. The assistant stopped anyway, treating reconciliation's rule to require fresh user direction after a recurring root as a terminal refusal, and failed to apply the existing Blocker recovery duty to record the defect, use the safe fresh-review route, and continue the authorized work. It also made review launch attempts before the required usage mint; those attempts were interrupted and did not produce review artifacts.

## Evidence

- `agents/skills/review-reconciliation/SKILL.md`, section 4, says the original caller owns a fresh review after a change and requires fresh user direction only before another review if the same root reopens.
- `agents/skills/review-plan/SKILL.md`, Step 5, requires review of the current source digest; the plan's latest r13 digest does not match the edited plan.
- `agents/skills/maintenance/decisions.md`, Blocker recovery, already directs the assistant to record a defect, apply a safe compliant workaround, and continue authorized work without asking for routine recovery.
- Current-session witness: explicit operator authorization followed the stop; a valid fresh review had not yet been staged or launched.

## Suggested direction

Resume with the existing contract: mint review usage before launch, stage one fresh digest-bound focused review of the revised docs-only plan, and continue only if the existing readiness and review gates pass. Do not reuse r13's stale digest, reset the round or self-heal budget, add a new gate, or automatically repeat a review if the same blocker returns. Determine during authoring whether one concise caller-resumption clarification is needed across the existing skill owners; if not, close this row as an execution lapse and preserve the existing contract.

## Dedup probe

Searched open backlog titles and text for reauthorization, post-stop resumption, review non-convergence, and blocker continuity. `docs/history/backlog/2026-10-25-review-plan-nonconvergence-recovery.md` covers recurring plan-specific findings and exhausted review budgets, not failure to resume after fresh operator authorization; the causal mechanisms differ, so no Cluster line was added.
