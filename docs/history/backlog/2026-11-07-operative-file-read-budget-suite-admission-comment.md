# Backlog: update the pins suite budget segment's admission comment when Task 1's promotion and suite-mode rewire land

- **Filed:** 2026-11-07, review round r4 certification-residual capture for docs/history/plans/2026-11-07-operative-file-read-budget-gate.md (the unfolded second sentence of r3 F5's fold comment)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** plan-review certification residual (this plan's r4; flagged by r3 F5's comment, whose exit-3 leg folded and whose admission-comment leg did not enter the plan text)
- **Class:** fix-class
- **Skill/step:** plan Task 1, pins-suite rewire bullet; scripts/check_maintenance_pins.sh budget segment
- **Dedup probe:** searched this plan's review series (r3 F5's comment requested exactly this edit beside the exit-3 pin) and the open backlog. No row covers the budget segment's admission comment.

## Problem

The plan owns rewiring the pins suite's gate-invocation arm to the suite mode (Task 1's rewire bullet) but pins no edit to the admission comment directly above the capture arm (scripts/check_maintenance_pins.sh lines 3881-3891). After Task 1 lands, that comment states two falsehoods about the wiring it describes: "the gate runs --check on every pins-suite invocation" (the rewired arm calls the suite mode), and "Promotion path: blocking exit 1 only after the gate's first true catch, promoted by a later change" (the promotion is this very plan, and the blocking exit keys on the ceiling class). A future editor or machinery audit of that segment reads a stale admission record describing the pre-promotion posture.

## Expected

The rewire edit updates the segment's comment to the promoted posture (suite-mode invocation, breach lines visible without moving the suite exit, ceiling-class blocking at the standalone surface, promotion landed by this plan), or the same edit range otherwise retires the two stale clauses. The machinery registry row's note (which the plan already updates same-change) remains the canonical admission record; this row covers only the local segment comment.
