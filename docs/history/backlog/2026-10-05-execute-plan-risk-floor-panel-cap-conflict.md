# Backlog: execute-plan review cap conflicts with risk-signal floor

- **Filed:** 2026-10-05, operator-directed maximum urgency
- **Status:** resolved for STORY-KEY execution
- **Workflow:** backlog
- **Priority:** superurgent (operator-marked)
- **Origin class:** review policy dead end
- **Class:** fix-class
- **Driving force:** reliability

## Problem

Execute-plan Phase 3 can require another full five-worker review after fixes, while its independent hard cap forbids a sixth full-panel round. The targeted-follow-up selection rule's risk-signal floor can force the full five-worker set when the reviewed diff still carries two risk signals. In that combination, the ordinary fix-review path has no eligible next panel.

## Evidence

- STORY-KEY completed five full-panel rounds by 2026-10-05 Round 5.
- Commit `4d00a02f` fixes a client-visible untrusted validation message and updates contract artifacts.
- The targeted-follow-up risk-signal rule requires a full five-worker panel at two or more signals; the execute-plan hard cap says to stop before a sixth full-panel round.
- The current change remains within public API and security boundary scope. No documented exception or evidence-equivalent targeted selection was found in the current execute-plan and review-panel-selection skills.
- **Cluster:** docs/history/plans/completed/2026-10-07-review-round-cap-operator-gate.md

## Expected

The policy should define a valid bounded post-fix verification route for this intersection, or a single documented exception that preserves mandatory risk coverage while honoring the round cap.

## Resolution

The user explicitly authorized continuing with a few more reviews on 2026-10-05. That direction satisfies the execute-plan gate requiring user direction before a sixth full-panel round. Round 6 proceeded with all five workers required by the risk-signal floor. The general policy interaction remains a future maintenance concern; this execution is no longer blocked by it.

## Source

- Observed while resuming STORY-KEY execute-plan, 2026-10-05.
