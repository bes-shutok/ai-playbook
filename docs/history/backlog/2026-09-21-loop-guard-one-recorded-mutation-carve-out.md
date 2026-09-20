# Backlog: loop-guard remedy forbids the terminating mutation - one recorded mutation carve-out (dark-loop prevention)

Captured: 2026-09-21 evening (operator analysis with the authoring resume session automation-2fd9c94e after it tripped the guard live)
Status: open
Priority: high
Workflow: backlog

## What was witnessed

The 2026-09-21 authoring-resume one-shot (automation-2fd9c94e, fired 16:40 local) carried the
parent re-arm create as its payload-mandated FIRST ACTION, with the decision recorded
state-first in the scheduler state file BEFORE any primitive call. The session still emitted
four CronList calls instead of the decided CronCreate, tripping the selection-loop guard
mechanically, then honored the guard's stand-down (rearm_note + repo-matching
loop-parent-missing memory note) without ever mutating. With the parent absent, no scheduled
actor exists to read the escalation note, so the loop stayed dark and recovery waited on an
interactive touch - the second dark night in two days (2026-09-20 overnight produced zero
plans for the same structural reason; 2026-09-21 ended dark again by design).

## Why the guard is not really helpful now (design analysis)

The guard's aim is correct and load-bearing: it bounds a real, repeatedly witnessed pathology
(the action-selection regress where a session emits listing after listing and the decided
mutation never goes out; see the sibling item 2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md
for five prior witnesses). The flaw is in the remedy's scope, not the aim:

1. The remedy forbids ALL automation-primitive calls after the guard fires - including the
   one mutating call that terminates the loop and restores liveness. A circuit breaker that
   also welds shut the reset switch. In the common case (a scheduler turn retried in two
   hours by a fresh session, or any parent present) the cost is one wasted turn. In the
   re-arm case - the actor IS the only restorer - "safe stop" and "loop goes dark" are the
   same event, and no scheduled carrier exists to read the escalation note.
2. The guard's premise ("the emission channel cannot emit the mutation even when it wants
   to") is only partially true. Today's session demonstrated the other reading: the channel
   can emit; the session was honoring the recorded rule. A rule that says "after the guard
   fires, exactly ONE decided mutation is permitted, then stop" preserves the bound against
   the regress while removing the darkness consequence - and it cannot reopen the regress,
   because one recorded mutation is not a repeated listing.
3. The escalation path (rearm_note + loop-parent-missing note) is prose-only recovery. It
   reliably carries the intent (today's note instructed the recovery correctly and completely)
   but nothing mechanical executes it, and its only readers are sessions that touch the repo
   later - of which there are none scheduled once the parent is dark. The dark loop therefore
   self-heals only through luck (an unrelated touch) or a human.

## Suggested fix

1. One-recorded-mutation carve-out in the overlay's dispatch-discipline section
   (agents/skills/maintenance/zcode.md) and the re-arm duty loop-guard clauses in both child
   blueprints (agents/skills/maintenance/prompt-templates.md): when the guard's signature
   appears (two listings, no mutating step between) AND the decided mutation was already
   recorded durably via a state-file write that preceded the first listing, the session may
   emit exactly ONE mutating call implementing that recorded decision, then must stop touching
   automation primitives regardless of outcome; any refusal after that single call takes the
   existing escalation paths (rearm_note, memory note, park) with no further primitive calls.
   A decision recorded only in chat narration does not qualify - the state-first write is the
   carve-out's gate, which keeps the discipline paragraph's decision-first rule load-bearing.
2. Operator override as a documented escape: the overlay states explicitly that the guard
   binds unattended sessions protecting themselves from their own pathology; an explicit user
   instruction to proceed outranks it. Today the operator had to intuit this; it should be
   written down so a future session offers the override instead of only reporting blocked.
3. Mechanical recovery carrier for the dark case: when the escalation note is written by a
   session that was the sole restorer (no ENABLED parent, no pending child), the note (or the
   state file's pending_rearm field proposed by the sibling durable-carrier item) must name a
   non-primitive carrier - the parked payload plus exact recipe - so a rearm-on-touch session
   executes the recovery mechanically instead of re-deriving it. Coordinate with
   2026-09-21-successor-duty-primitive-absence-park-fallback.md (its re-arm park path is the
   durable-intent half; that item is taken by the in-flight scheduler-leftovers authoring,
   plan A) and with 2026-09-21-loop-mode-durable-carrier.md (the loop_mode field that must
   survive every re-arm; same plan A).
4. Pins: the carve-out sentence, the operator-override sentence, and the single-call bound get
   occurrence pins in scripts/check_maintenance_pins.sh; the pinned re-arm duty paragraphs in
   prompt-templates.md change under the freeze-literal protocol the pins header documents.

## Sequencing constraint

The carve-out edits the same zcode.md dispatch-discipline region as the in-flight
scheduler-leftovers authoring's plan C (the suppression item's fix: discipline extension plus
the env-complete launchd recipe). Sequence after `2026-09-21-scheduler-maintenance-loop-quality-hygiene`
leaves the top-level survey: the fixing plan carries `External gate: scheduler-maintenance-loop-quality-hygiene`
so the scheduler skips it while that plan is open. Union-merge precedent exists if they ever
overlap.

## Acceptance

- The overlay's dispatch-discipline section carries the carve-out (countable fixed-string
  span naming the one-recorded-mutation bound) and the operator-override escape sentence.
- Both blueprints' re-arm duty loop-guard clauses state the carve-out (or reference it), with
  the pins suite green under the freeze-literal protocol.
- The dark-case escalation note format names the mechanical recovery (parked payload +
  recipe) so a touch session executes it without re-derivation.
- A dark-loop drill (simulated guard trip with a state-first recorded decision) shows exactly
  one mutation emitted and the session stopped after it.

## Evidence pointers

- 2026-09-21 session automation-2fd9c94e: four CronList calls, zero mutations, rearm_note +
  loop-parent-missing note written, loop left dark (scheduler-state decision_reason history).
- Sibling witness item: 2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md
  (six witnesses including today's; the launchd carrier recipe lives there).
- Dark-loop outcomes: 2026-09-20 overnight (zero plans) and 2026-09-21 16:41 local.
- Related (taken elsewhere, coordination only): 2026-09-21-loop-mode-durable-carrier.md and
  2026-09-21-successor-duty-primitive-absence-park-fallback.md (scheduler-leftovers plan A),
  2026-09-18-budget-gate-scheduling-on-automation-bound-sessions.md and
  2026-09-19-scheduler-toolset-precheck-before-dispatch.md (the same fix family, untaken).
