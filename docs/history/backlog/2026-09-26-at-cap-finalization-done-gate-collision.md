# Backlog: at-cap plan finalization cannot pass the done plan-readiness gate

Status: open
Priority: high
Workflow: backlog
Class: plans/done lifecycle
Driving force: correctness

## Problem

The standing authoring directive template caps plan-review rounds (five) and prescribes, at the cap, finalizing with the best available draft and recording the residual findings in the plan. The done skill's plan-readiness gate independently requires the latest review round's sidecar to carry verdict ready=yes with zero unresolved blocking findings, and its only bypass is the recorded-stop exception, which requires the user to explicitly choose to stop without finalization. When the cap round is not clean, the two contracts collide: the directive orders a finalization the gate mechanically refuses, no further round is permitted, and the recorded-stop exception does not match what was authorized (the user chose finalize-with-residuals, not abandon). An orchestrator following the template either exceeds the cap on its own authority or strands the finalized plan unlanded with the worktree and branch preserved.

## Observed versus expected

- Observed: at the cap round the panel reported ready=no with blocking findings (later folded); the directive forbade another round; the gate refused finalization; the run ended with the plan finalized and recorded but unlandable without an operator decision.
- Expected: a defined at-cap closure path. Candidates: (a) the gate learns a recorded residual-finalization state (for example a plan section, referenced by the sidecar, that marks the loop closed at cap with residuals recorded, satisfying the gate as an explicit operator-authorized terminal shape); or (b) the directive template changes to require clean-at-cap and prescribes the recorded-stop path when the cap round is not clean; or (c) review-plan gains a cap-closure staging shape whose verdict the readiness gate accepts.

## Suggested fix

Pick and implement one of the candidates above so the at-cap terminal shape is mechanically expressible end to end; document the chosen shape in plans SKILL.md (round-cap paragraph), the done gate's plan-readiness bullet, and the review-plan Iteration Discipline section in the same change.

## Environment

Scheduled authoring session, 2026-09-26, doc-corpus plan, six rounds run (five in-cap plus one disclosed verification round), final round ready=no with all findings folded and a residual-findings section recorded in the plan.
