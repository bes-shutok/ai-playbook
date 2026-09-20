# Backlog: scheduler dispatch ignores live 5-hour quota state when choosing the authoring primitive

Captured: 2026-09-19 (source: Andrey correction in the maintenance scheduler session - "why don't you run it right now? The quota is full so it seems like an error in judgement that we should fix")
Status: done (executed via docs/plans/completed/2026-09-20-quota-aware-scheduling-semantics.md, 2026-09-21)
Priority: high

Workflow: backlog

## What was witnessed

At the 2026-09-19 "proberesume" turn the authoring pick
(docs/history/backlog/2026-09-19-gate-driven-silent-prose-edits.md) was
dispatched to the idle-time queue (offpeak-1f9389c4, queue position #4, no
guaranteed start time) even though the interactive scheduler session was alive,
capable, and the 5-hour model quota window was freshly full. Andrey observed
the full quota at correction time; the scheduler itself never consulted any
quota signal, because its decision procedure has no such input. In-session
authoring had already been proven as a working path four times in the same
session whenever the idle-task quota was refused.

The reasoning recorded at dispatch time, in full:

1. Design-default bias: the loop treats the idle child as the primary dispatch
   primitive and in-session authoring as a fallback reserved for idle-quota
   refusal. When the slot freed (a junk probe failed), the decision reverted
   to the standing default instead of being re-derived from current
   conditions.
2. Context preservation: the scheduler session had already absorbed four full
   authoring loops; dispatching keeps the scheduler session light for future
   turns.

What that reasoning ignored: the demand-side resource state. Idle-queue
dispatch trades a guaranteed slot of currently-abundant interactive quota for
an unguaranteed off-peak slot later. When the 5-hour quota is full and the
session is alive, running in-session is strictly better: zero wait, the same
quota, and no queue ticket held hostage (a queued idle task has no cancel and
no amend primitive). The failure family is "defaults overriding narrower
intent" - the same family captured in
2026-09-19-gate-driven-silent-prose-edits, witnessed here in the scheduler
itself.

Secondary observation from the same incident: because a queued idle task
cannot be cancelled or amended, superseding the dispatch in-session leaves a
duplicate-authoring risk that can only be defused through conversation
history. The dispatched payload carried no pre-execution re-verification gate
(is the pick still plan-uncovered? has the work already been done?) and no
stand-down-if-covered instruction.

## Suggested fix

1. Quota-state-aware primitive selection in the maintenance skill (the D2
   authoring decision, and the runtime overlay where primitives are named):
   before choosing between idle-queue dispatch and in-session authoring,
   consult the current 5-hour quota state (user-reportable or host-surfaced;
   no independent probe primitive exists). Interactive quota available plus
   session alive means author in-session (or a foreground child); quota scarce
   or peak window, or a session unable to carry the work, means idle queue.
   Related: 2026-09-16-quota-aware-fire-time and
   2026-09-18-maintenance-quota-aware-lane-decisions cover when to fire and
   which lane runs; this item covers which primitive carries the work.
2. Idle dispatch payloads gain a pre-execution re-verification gate in the
   authoring blueprint: on start, re-check the pick is still plan-uncovered
   and that no plan for the same backlog origin exists; stand down writing
   nothing if covered, and say so in one output line.

## Acceptance

- The maintenance skill carries the primitive-selection rule and names the
  live quota signal as a required decision input.
- The scheduler state decision record for an authoring dispatch names the
  quota signal observed at decision time (grep-able field).
- Idle authoring payload templates carry the still-uncovered re-verification
  stand-down gate (countable in maintenance/prompt-templates.md).
- A later dispatch decision made under a full quota window runs in-session
  instead of queueing (witnessed in the scheduler state history).
