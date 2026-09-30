- **Filed:** 2026-09-30
- **Status: done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-user-directed-maintenance-payload-rearm-duties.md, squash main 89cde29a, exec review r1 ready=yes zero blocking)(docs/history/plans/2026-09-30-user-directed-maintenance-payload-rearm-duties.md)
- **Workflow:** done (learn Step 1.8)
- **Priority:** high
- **Origin class:** self-serving
- **Driving force:** reliability
- **Class:** fix-class

# User-directed maintenance payload carries no turn-start carrier re-arm duty

## Observed vs expected

Witness 2026-09-30 01:41 local: a one-shot user-directed maintenance payload ("execute plans one by one", manual CronCreate, not the scheduler prompt template) fired in an automation-born session. Unlike blueprint-dispatched children (whose payloads carry the re-arm-first paragraph as FIRST ACTION), this payload's prompt carries no re-arm duty; the session attempted the turn-start carrier re-arm duty voluntarily, hit the selection-loop stand-down on the primitive surface (repeated listings, decided delete-plus-create unsent), and parked `pending_rearm`. Result: the loop had no armed carrier and no blueprint child scheduled to re-arm it; recovery rides solely on the parked record being discharged by a later primitive-capable touch. The maintenance skill's Step 0 duties are written for scheduler turns and blueprint children; an interactive/user-directed maintenance payload session falls outside both audiences, so the arm-at-turn-start property silently does not hold for that class.

## Expected

A user-directed maintenance payload either (a) instructs the receiving session to perform the turn-start carrier re-arm duty per the runtime overlay's recipe before any payload work (with the same reduced-toolset park fallback), or (b) the done/report step of such a session verifies an ENABLED recognition match exists (or the parked record stands) and reports loop-liveness status in its closing summary so darkness is visible to the operator.

## Reproduction evidence (trimmed)

State file at turn start: parent one-shot recorded with a past `next_turn_at`; listing showed only lingered completed records (the spawner and a co-firing authoring twin); no ENABLED recognition match; session stood down per the selection-loop guard; `pending_rearm` + payload copy written; no primitive-capable carrier armed afterward.

## Environment

ZCode runtime, 2026-09-30, agents/skills/maintenance/SKILL.md + zcode.md overlay (repo copy); payload issued interactively via CronCreate from a fresh chat.

## Suspected root area

agents/skills/maintenance/prompt-templates.md (payload blueprint audience) and SKILL.md Step 0 duty scoping; possibly the interactive-dispatch template (zcode.md) which never mentions the re-arm duty.
