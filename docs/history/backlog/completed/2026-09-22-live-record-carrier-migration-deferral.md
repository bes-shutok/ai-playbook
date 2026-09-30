# Backlog: live-record carrier migration deferred by the cadence plan execution

Status: done (2026-09-30; legacy origin fold completed post-execution: covered by docs/history/plans/completed/2026-09-23-p50-scheduler-state-durability-leftovers.md)
Priority: medium
Workflow: backlog
Date: 2026-09-22
Class: operations follow-up from plan 2026-09-21-maintenance-turn-self-scheduling-cadence Task 1
Disposition: 2026-09-23 (annotated via docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md, Task 3 and Ship when): the duplicate-parent tripwire migration arm is the durable carrier; the live listing verification (no-op close or post-migration observation) rides that plan's Ship when. Stays open until the verification.

## Problem

Task 1 of the cadence plan prescribes an execution-time live-record migration step: when an ENABLED automation matching the old scheduler prompt opening plus the resolved repository root exists but does not carry the new recognition title (`Maintenance scheduler turn`), the executor retimes and retitles it per the cadence rule with one update-primitive call under the HOST CAVEAT.

The executing session was barred from automation mutations (scheduled-session constraint: never create, retime, or retitle automations), so the step was deferred and the checkbox was marked with the plan's sanctioned backstop: the duplicate-parent tripwire. The deferral is recorded in the execution log (implement-t1-pass1.log.md) and commit c9a378f2's body.

Exposure: until the migration runs, the already-armed fixed-cadence parent (if one exists at execution time) keeps the old title. The duplicate-parent tripwire is the backstop: when a turn-start duty later creates the new-form carrier, the old record's ENABLED recognition match trips the tripwire and the turn takes the prescribed escalation instead of silently running two carriers. The loop does not go dark, but one escalation cycle is spent.

Driving force: the migration is a one-time operational action on live scheduler state, not a repo edit; it needs a session that owns scheduling primitives and can verify the echoed record (HOST CAVEAT), which the executing session could not.

## Fix item

At the next maintenance turn that owns scheduling primitives: list automations, find any ENABLED record matching the old scheduler prompt opening plus this repository root but not the new title, and retime/retitle it per the overlay's cadence rule with one update call under the HOST CAVEAT (unverifiable echo routes to delete-plus-create). Record the migration in decision_reason. If none exists, record no-op and close.
