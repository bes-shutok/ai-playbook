# Backlog: a mid-run 5h usage-limit refusal has no resume-carrier arm; the lane sleeps until the operator wakes it

- **Filed:** 2026-11-13, interactive arc over the session-identity authoring run (operator indefinite-operation mandate 2026-11-12/13)
- **Status:** covered (docs/history/plans/2026-11-13-indefinite-operation-loop-continuation-duties.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fence-class
- **Origin class:** witnessed lane-darkness gap
- **Skill/step:** `agents/skills/maintenance/quota-policy.md` (Step 4 quota leg, beside the stop-before-exhaustion arm) + `agents/skills/plans/budget-gate.md` (the Budget-gate pause boundary, for the authoring run's own wall class pointer)

## Observed versus expected

**Observed:** at ~01:00 WET 2026-11-13 the r1 review agent died on the harness refusal "[1308] Usage limit reached for 5 hour. Your limit will reset at 2026-11-13 09:49:24" (displayed string; GMT+8 per the standing operator note = 01:49:24 WET local). The session's turn ended with no armed carrier, and the lane slept roughly 6.5 hours until the operator resumed it at 07:40 WET, though the usage window reset at 01:49 and the work queue held 25 PLAN-PROMPTS plus 12 EXEC-PROMPTS entries. The quota leg's stop-before-exhaustion arm carries its arm-or-re-point carrier duty only for the >= 95 percent pre-exhaustion park; a mid-run usage-limit refusal at any percent has no arming duty, and the resume rule ("the first boundary after the reset whose probe is fresh") presumes a later session arrives, which an ended interactive turn never supplies on its own.

**Expected:** at a mid-run usage-limit refusal the boundary converts the displayed reset into the local window-start minute, arms a one-shot resume carrier at that minute through the overlay's named dispatch primitive (the clocked one-shot, the idle-time primitive, or the launchd resume carrier per the park-with-carrier leg's pairing shape), records the wall in the boundary's own pause surface (budget_pause where the boundary owns a sink; the turn output otherwise), and ends the turn; the fired continuation re-enters the interrupted work from its recorded boundary. The second wall this arc (10:45 WET) armed such a carrier ad hoc (the 12:45 WET one-shot, automation-8f1664a2, deleted on operator resume), which is the proof the primitive exists and only the duty is missing.

## Reproduction evidence (trimmed)

- Wall 1 (~01:00 WET): refusal text captured in the run's requirements buffer; no carrier armed; lane dark 01:00-07:40 WET with a 01:49 reset.
- Wall 2 (~10:45 WET): refusal text captured; carrier armed ad hoc after the operator's standing directive; reset 12:39 WET; the carrier's skip-if-done deconfliction and GMT+8 conversion were hand-built in the payload.

## Environment context

- zcode runtime; the operators's standing GMT+8 note lives in user-level instructions, not repo text (see the timezone-conversion row filed the same day). Witnessed 2026-11-12/13.

## Suspected root area

The quota leg prices the pre-exhaustion park (>= 95 percent) but never the mid-run refusal class; the budget gates record pauses but arm nothing; every wall's continuation currently depends on either the automation fleet's own carriers or the operator typing resume.
