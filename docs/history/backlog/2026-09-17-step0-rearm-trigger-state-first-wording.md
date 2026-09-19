# Backlog: Step 0 rearm-on-touch trigger wording is listing-first

Status: open
Workflow: backlog
Origin: 2026-09-16-maintenance-scheduler-liveness r1 review (finding DS-4, deferred to backlog by the triage)
Severity: Low (design tension, not a liveness bug)
Scope: agents/skills/maintenance/SKILL.md (Step 0 bullet), scripts/check_maintenance_pins.sh (Task 4 pin), docs/plans/2026-09-16-maintenance-scheduler-liveness.md (Task 4 wording and Validation gate 2 needle), agents/skills/maintenance/zcode.md (re-arm hygiene bullet; extended 2026-09-18, r5 entry 17: the bullet asserts the state-first shape governs the re-arm decision of the turn's Step 0 and rearm-on-touch sessions, a claim the listing-first Step 0 wording contradicted until the rewrite landed)

## Problem

The Step 0 rearm-on-touch check opens with the trigger phrase "when the
automation listing shows no ENABLED parent", which is a listing-first
trigger: a touching session performs an automation listing before it has
consulted the scheduler state file. The design principle of record (the
record-oscillation rewrite) is state-first: consult the state file first,
list at most once after the mutation decision, never before. The Step 0
wording inverts that order for the touch surface and adds one listing per
touching session per cycle.

The wording is plan-prescribed in three coupled places, which is why the r1
pass deferred it: the discriminating pin substring in the pins suite, the
same substring in the plan's Validation gate 2, and the Step 0 sentence
itself. Changing only the sentence breaks the pin; changing the pin breaks
the plan's gate; the plan is a historical record, so the fix must land in one
pass and register the wording change against the plan.

## Consequence

Every session that runs the Step 0 check (and the done-skill line that
defers to it) lists the automation fleet before reading the state file,
contradicting the state-first invariant taught everywhere else in the skill,
and pays one listing per touch that the state file could often make
unnecessary. The r1 address pass added the repo-scope precondition and moved
darkness classification wholly to the State file semantics, but the trigger
order itself is still listing-first.

## Fix sketch

One atomic edit pass across all three coupled surfaces:

1. Rewrite the Step 0 trigger to state-first: open with the state-file
   consultation (state file exists for this repository, recorded
   `parent_automation_id`, live pending child, `parent_absent_since` age),
   and list only when the state file cannot decide or a darkness
   classification needs confirmation.
2. Update the pins-suite discriminating pin to the new sentence's needle
   (keep the old needle as a negative pin so the listing-first wording
   cannot silently return).
3. Record the wording change as a dated deviation against the plan's Task 4
   quote (the plan text itself stays historical), and flip the Validation
   gate 2 needle in the same commit so the plan's gate block and the pins
   suite never disagree.

Note (2026-09-18, P12 origin 4): DS-4 finding restated inline. Consequence:
the listing-first trigger paid one automation listing per touching session
before the state file is consulted, inverting the state-first invariant for
the touch surface. Origin: liveness r1 review, deferred by the triage
because the three coupled surfaces (the Step 0 sentence, the pins-suite
discriminating pin, and the archived plan's Validation gate 2 needle) had
to move in one pass. The rewrite landed in one pass across all three coupled
surfaces plus the zcode.md re-arm hygiene bullet added to Scope above, whose
state-first claim becomes accurate with the Step 0 rewrite.

Note (2026-09-19, code review r1 RISK-1): detection trade for the landed
state-first trigger, mirroring Task 1's containment-trade pattern. The touch
surface lists only when the state file cannot decide; an externally induced
parent loss (a human deletion, or the witnessed garbled recycling update
that lands enabled:false/completed per backlog
2026-09-19-recycling-update-flip-refuted-delete-plus-create.md) never writes
state trouble, so a fresh, healthy-looking state file would keep the touch
surface listing-free forever and make touch-surface darkness undetectable.
Remedy landed in SKILL.md Step 0 (review r1 address pass): the cannot-decide
list gained the state-file-evaluable staleness escape (a file whose own last
write is older than one cadence period attests no listing verification of
the recorded parent's presence within one cadence period, so only the
listing decides), and the three bookkeeping edits are reconciled as
listing-derived (none applies when the state file decided and no listing
ran). Accepted residual: a touch surface whose state file was written within
the last cadence period performs zero listings and cannot observe an absence
newer than that write; the escape bounds the blind window at one cadence
period past the last successful state write, and the turn surface's own
guard listings cover the live loop.
