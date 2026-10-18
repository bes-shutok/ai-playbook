# Backlog: treat an explicit investigation request as direction to research a blocked lane

- **Filed:** 2026-10-17, follow-up to a done commit blocked by the dirt-regression gate
- **Status:** covered (docs/history/plans/2026-10-17-investigate-user-directed-gate-workaround.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** operator workflow correction
- **Class:** fix-class
- **Driving force:** reliability (a blocked lane gets the requested diagnosis) + operator time
- **Skill/step:** `agents/skills/investigate/SKILL.md`, invocation boundary; `AGENTS.md`, Machinery admission protocol
- **Environment:** local skills-repository execution, 2026-10-17
- **Related origin:** `docs/history/backlog/2026-10-17-done-plan-removal-only-regression-block.md`
- **Cluster:** docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md (same defect class: a blocked lane's recovery path needs an explicit continuation contract); docs/history/plans/2026-10-18-plan-declared-missing-input-fallback.md (covered: the landed plan-declared missing-input fallback plan)

## Problem

The prior investigation record for an intentional removal-only dirt-gate refusal said that the sanctioned gate change was an operator decision under the machinery admission protocol. The user then explicitly requested a backlog and an investigation to find a workaround. `AGENTS.md` names retry, skip-with-report, and park-for-operator as the bounded responses, while the investigate skill defines what happens after invocation; neither connects an explicit user-directed investigation with those blocker dispositions. This ambiguity can make an agent read an earlier operator-decision note as a reason to wait even after the user has directed investigation.

## Expected

When the user directs investigation and recovery of a blocked lane, inspect the refusal, search for a safe workaround, and apply any workaround within existing authority. Rerun the refused gate and resume the interrupted work through its existing completion boundary; do not stop after finding or logging a viable option. Keep any gate or validator change behind its plan and existing approval contract; do not use investigation as a bypass. For an unresolved block, choose the existing bounded disposition without expanding what may be committed during the lane.

## Suggested direction

Clarify the gate-block recovery guidance and the investigate invocation boundary so a user-directed investigation is a supported response alongside bounded retry, skip-with-report, and park-for-operator. Preserve the current restrictions on editing a gate mid-lane, adding machinery, or treating a diagnostic workaround as permission to bypass a refusal. Reuse the existing continuity lens and machinery admission protocol rather than adding another gate, ledger, or required ceremony.

## Evidence

- `AGENTS.md`, Machinery admission protocol, lists bounded retry, skip-with-report, or park-for-operator when a gate blocks a lane and forbids editing a gate or validator mid-lane without a plan.
- `agents/skills/investigate/SKILL.md`, Boundary and Stage 3 continuity lens, defines autonomous investigation with no user interview and requires blocker alternatives and a viable narrower recovery path to be priced.
- `docs/history/plans/completed/2026-10-14-investigate-blocker-continuity-signal.md` added the continuity lens to investigation after a blocker interrupted authorized work; it does not define the caller's response when a new user message explicitly requests investigation.
- `docs/history/backlog/2026-10-17-done-plan-removal-only-regression-block.md` records the current gate refusal and the evidence-backed replacement-text workaround.

## Alternatives

- Require another operator decision before any investigation: rejected because the user already explicitly directed investigation and workaround research in this incident.
- Let the investigator change the gate or validator during the blocked lane: rejected because `AGENTS.md` explicitly forbids that without a plan.
- Add a new workflow gate or mandatory incident ledger for blocker investigations: rejected because this request can be handled by existing backlog and investigate artifacts without new blocking machinery; no witnessed incident supports an additional blocking gate or ledger (`agents/skills/investigate/SKILL.md`, Boundary and Stage 4; `AGENTS.md`, Machinery admission protocol).
