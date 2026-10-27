# Backlog: done self-heal handoff's coined "staging classification asks" label lacks a step antecedent

- **Filed:** 2026-10-27, execute-plan Task 1 intermediate review (self-heal-before-workflow-stop)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-finding
- **Class:** fix-class (prose precision in a user-only-stop carve-out)
- **Driving force:** clarity (prose precision in a carve-out that gates when recovery may be attempted)
- **Skill/step:** `agents/skills/done/SKILL.md` self-heal handoff (user-only stop list); referent is the Step 4/5 side-repo walk's staging ask

## Problem

The new done handoff names user-only stops as "(the learn corpus block, staging classification asks, lock `blocked` returns)"; all three compressions anchor unevenly (Phase 3 r1 widened this row from the single staging item): "staging classification asks" points at the side-repo walk's classify-and-ask step while the nearby "Baseline-dirt classification" is mechanical and never asks; "the learn corpus block" appears only as Step 1's "learn reports a blocked state (Step 6.6 user-corpus violation)" bullet, resolvable by word-form inference; "lock `blocked` returns" is ambiguous across three blocked-returning sites (Step 0 done-lock acquire, the commit run's runner-refusal posture whose bounded retry stays available, Step 6's review-thread gate), and mapping the runner-refusal case onto the carve-out contradicts the same paragraph's bounded-retry authorization. Worst case is a skipped (not bypassed) self-heal consideration or an unnecessary user round-trip.

## Suggested investigation

Anchor all three items in the owning steps' vocabulary (for example "learn's user-corpus block (Step 1)", "the side-repo staging asks", "the Step 0 done-lock `blocked` acquire") and disambiguate the lock item from the commit run's runner-refusal posture; or record the single-item scope as deliberate and accept the residual inference.

## Source

Execute-plan intermediate review finding, plan docs/history/plans/2026-10-27-self-heal-before-workflow-stop.md.
