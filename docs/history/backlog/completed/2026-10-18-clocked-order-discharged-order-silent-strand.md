# Clocked order discharges with no payload session record and no successor order

- **Filed:** 2026-10-18, learn Step 1.8 capture from the 2026-10-18 authoring session's closeout
- **Status:** covered (docs/history/plans/2026-10-18-clocked-order-successor-verification.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed recovery gap (recurrence of the covered 2026-10-10 discharge class)
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/zcode.md` (Recurring automation recipe, Re-arm hygiene, turn-start carrier re-arm duty); `scripts/execute_plan_resume_watcher.py` (clocked-order ledger, discharge-on-fire operation)
- **Driving force:** reliability
- **Cluster:** docs/history/backlog/2026-10-10-clocked-order-discharge-no-payload-session.md (same instant-death class, first witness; its verification arm was routed to the launchd promotion review, not landed)
- **Cluster:** docs/history/plans/completed/2026-10-17-rearm-dispatch-ladder-incident-guards.md (the landed guard plan whose arm 3 names the launchd default-in-waiting posture this row's evidence feeds)
- **Cluster:** docs/history/backlog/2026-10-17-rearm-ladder-guards-certification-residuals.md (the same ladder surface's residual row)

## Observed versus expected

Observed: clocked order co-b3f5bb778d3448369e6ec145322d4577 (requested 2026-10-18 12:04, armed 11:09 by the 11:00 session's re-arm duty) discharged at 12:04:03; the job log holds only the discharge JSON and the err log is empty. No payload session record ever appeared (no scheduler-state children[] entry, no authoring or execution claim, no worktree, no commits in the 12:04 window), and no successor order was armed. The ledger reads healthy (`discharged`), so the missed-order detector never fires; the stranded turn surfaced only because the still-live 11:00 session's closeout ran the loop-liveness duty and armed the 20:08 repair order (co-cf3cc4af5b8f4a2abe1f6027d704c74b).

Expected: a discharge whose payload session does not verifiably record itself (no state-file entry) and produce a successor re-arm within a grace window is detected by a host-side arm (the chain or its consult), which records the miss and arms the recovery turn; the loop's continuation must not depend on an unrelated session happening to run a liveness check.

## Evidence

- Ledger history for the order: recorded 11:09, armed through launchd, discharged 12:04:03 late by 3 seconds.
- Job log: only the discharge JSON; empty err log (the 2026-10-10 row's instant-death signature).
- Scheduler state at recovery: the parent pointer named the discharged order with next_turn_at 12:04 until the closeout re-pointed it; no children[] entry exists for the 12:04 window.
- Second witness of the class in eight days (the 2026-10-10 row); this instance left zero residue, so the loss is the turn itself.

## Suspected root area

The discharge path closes the order without any continuation verification, and the re-arm duty is session-side only: a payload that never launches (or dies before its first write) leaves no process holding the duty to re-arm. The covered sibling row routed its verification arm to the launchd promotion review; this recurrence is evidence the arm should not wait for that promotion, because a warning-shaped discharged-without-successor check (the state file's next_turn_at still naming a discharged order past a grace window) can ride the existing missed-order consult or the chain's discharge path without new blocking machinery.

## Why not fixed now

The capture turn is a learn and investigate turn: the recovery already happened (repair order armed, loop live), and the fix needs the machinery admission wording plus the promotion-review deconfliction; the investigate pass routing this row lands in the same turn as its design input.
