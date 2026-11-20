# Backlog: the D-17 continue-loop re-run is invisible at the authoring closeout boundary; the session stood down at the landing while the execution queue was full

- **Filed:** 2026-11-13, interactive arc over the session-identity authoring run (operator indefinite-operation mandate 2026-11-12/13)
- **Status:** covered (docs/history/plans/2026-11-13-indefinite-operation-loop-continuation-duties.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fence-class
- **Origin class:** witnessed operative-duty skip at a boundary the duty never reaches
- **Skill/step:** `agents/skills/maintenance/template-authoring.md` (the AUTHORING CLAIM duty's placement-owned deletion boundaries) + `agents/skills/maintenance/zcode-scheduling-primitives.md` (the in-session authoring primitive, the duty's existing home)
- **Cluster:** docs/history/backlog/2026-11-13-empty-exec-candidate-cross-lane-stop-gap.md (the mirror direction: that row owns the exec-side empty candidate set; this row owns the authoring-side boundary skipping the continuation), decisions.md D-17

## Observed versus expected

**Observed:** at ~14:40 WET 2026-11-13 the session landed the certified session-identity plan, pruned the frozen entry, deleted its claim, and ended the lane with "next lane step (not this session's)", while 12 EXEC-PROMPTS entries were queued and the 5h window held hours of allowance. The in-session authoring primitive mandates the opposite: "after an in-session authoring run lands, the turn re-runs the execution-lane decision on the freshly landed plan under the continue-loop condition (directive D-17; D-6's quota clauses remain active), never ending at the authoring boundary while dispatchable work remains and the primary 5h limit is not low." The duty lives in the scheduling module; the AUTHORING CLAIM duty's closeout boundary and the plans skill's landing handoff never name it, so the closing session never loads the rule at the boundary where it fires (the same wiring class the session-identity plan itself fixes for guards.md G1a's claim matching).

**Expected:** the authoring closeout boundary carries a one-line pointer to the continue-loop re-run (the execution-lane decision on the freshly landed plan, its quota_signal token, and the in-session-or-dispatch continuation it mandates), so the closing session re-runs the decision before ending instead of inheriting the lane-territory reading of the authoring mandate cap.

## Reproduction evidence (trimmed)

- The closing report of the landed arc names no execution-lane re-run decision, no quota_signal token, and no probe read at the boundary; the 12-entry EXEC-PROMPTS queue and the fresh 5h window were both observable on disk at that minute.

## Environment context

- zcode runtime; witnessed 2026-11-13 on the session-identity authoring arc. The duty text itself is correct and correctly placed in the scheduling module; the gap is the missing pointer from the closeout boundary the closing session actually reads.

## Suspected root area

Load-on-dispatch gives the closing session the AUTHORING CLAIM duty and the plans skill's landing handoff, neither of which references the scheduling module's continue-loop leg; the duty fires only where its module is loaded, and the authoring boundary is not such a place.
