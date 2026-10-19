# Stale carrier armed flags on terminal clocked-order ledger records

- **Status:** open
- **Priority:** low
- **Class:** fix-class
- **Origin class:** session witness (2026-10-19 authoring closeout turn)

## Observed

Every terminal order in `.ai-playbook/maintenance/clocked-orders.json` (20 of 20: discharged or cancelled) still carries `carrier.armed: true` in its carrier record, written at arm time and never revisited at the state transition.

## Expected

A terminal order's carrier record reads as torn down (disarmed), or carries an explicit teardown note, so a ledger reader can distinguish an armed carrier from a consumed one without leaving the ledger.

## Witness

The 2026-10-19 closeout had to probe launchd directly because the discharged order's `armed: true` contradicted its `state: discharged`; six launchd jobs for discharged orders were still loaded and were booted out by hand. The ledger's flags said nothing about which jobs were live.

## Suspected root area

The discharge and cancel handlers in the clocked-order operation update the order's `state` but never the carrier record's `armed` field (the flag is written once at order-arm time).

## Fix shape

One ad-hoc pass: set `carrier.armed: false` on every terminal order and append a bootout/teardown event to each record's history. Rejected arm (with basis): flipping the flag inside the discharge/cancel handlers now - no second witnessed cost, and the landed consult reads state fields, not carrier flags, so the smallest arm that removes the witnessed cost is the data sweep.
