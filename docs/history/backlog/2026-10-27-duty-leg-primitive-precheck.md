# Backlog: the turn-start carrier re-arm duty orders its delete-own-spawner leg without a toolset precheck, so a listing-only fired session plans the leg and loops on its last successful read

- **Filed:** 2026-10-27, learn Step 1.8 over the 2026-10-27 11:03 resume exec session (project lesson 263)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** session-witnessed skill-instruction defect (a duty's primitive leg assumes the executing session's toolset exposes that primitive)
- **Class:** fix-class
- **Driving force:** efficiency (the session burns repeated listing calls at the emission point and stalls its plan; the loop guard's repeated-listing signature is the visible symptom, and the reduced-toolset terminal rung's park path never fires because no re-arm or dispatch decision is suppressed)
- **Skill/step:** `agents/skills/maintenance/zcode.md` (Turn-start carrier re-arm duty; the delete-own-spawner ordering and its delete-first primitive emission)
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `toolset`, `rearm`, `primitive`, `listing-only`; nearest are 2026-10-23-scheduling-asks-rearm-wording-candidates.md (scheduling-ask confirmation wording, different surface and defect) and 2026-10-17-rearm-ladder-guards-certification-residuals.md (ladder guard certification residuals, different defect class); lesson #196 and the reduced-toolset terminal rung cover recorded absences and decided-action parks, not delete-leg planning. No open row owns the precheck arm.
- **Cluster:** the registry consult's state-record read-root defect is covered (landed read-root sentence, EXEC-PROMPTS entry registry-due-read-primary-root); this row owns a duty leg planned against an absent toolset primitive

## Problem

The Turn-start carrier re-arm duty in agents/skills/maintenance/zcode.md orders the session to delete its own spawner record "whatever its form" as the duty's first primitive emission, and the re-arm hygiene bullet's delete-first ordering presumes the delete primitive exists. A fired session on this host often carries a listing-only automation toolset (the listing primitive without create/delete/update). Planning the leg from the duty text alone, such a session discovers the absence only at emission time; the witnessed session then re-emitted its verification listing three times (harness-flagged as repeated identical calls) before naming the leg proven-absent. The operator-ordered schedule surface paragraph owns a "proven-absent deletion primitive" vocabulary for the cap-refused create path, but the turn-start duty's text never routes a listing-only session to it when no create is owed.

## Expected

The duty text names the precheck: a session whose toolset lacks the delete primitive records the proven-absent leg beside its re-arm decision (the lingered spawner ages out; the automation-born cap never fires without a create) and proceeds with the leg-free work, emitting no further listings for the leg.

## Suggested fix

One clause in the Turn-start carrier re-arm duty bullet: after the delete-first ordering, "a session whose prechecked toolset lacks the delete primitive records the proven-absent leg beside the re-arm decision instead of planning the delete emission (the lingered record ages out; the cap never fires without a create)". Prose only, no machinery; project lesson #263 carries the witness.
