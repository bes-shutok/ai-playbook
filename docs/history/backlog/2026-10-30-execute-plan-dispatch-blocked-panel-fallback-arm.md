# execute-plan Phase 3 lacks a dispatch-blocked fallback arm for the review panel

- **Filed:** 2026-10-30
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (a provider-side dispatch block can strand a mid-run round with no documented in-skill path; the session that hit it improvised)
- **Origin class:** session witness (execute-plan Phase 3 round, 2026-10-29/30 execution run; every worker dispatch attempt provider-refused, so the two-lens round ran inline in the parent session and the honest focused review record was shaped by hand)
- **Class:** fix-class (one skill-text arm documenting an existing admissible fallback; no new gate or validator)
- **Driving force:** reliability

## Observed versus expected

Observed: the execute-plan skill's Phase 3 procedure assumes worker dispatch succeeds. When the dispatch channel is blocked outright (provider refuses every launch, distinct from a worker timeout or a quota wall), the skill text gives no fallback: no permission to run the round inline in the parent session, and no record-shaping contract for that case. The witnessing session improvised the full path (inline two-lens review with mutation evidence; review record reshaped to focused panel mode with the block named in the selection reason, workers launched equal to the lenses executed, material lens set scoped so the verdict's coverage claim stays true) and validated it against the staging validator by trial and error.

Expected: the skill names the dispatch-blocked fallback explicitly: run the round inline with the planned lenses, keep mutation evidence per guarded mechanism, and record the round as a focused panel whose record fields describe what actually ran (never the producer template's full-panel default). Cross-reference the review-record honesty grammar it depends on.

## Reproduction evidence

A run where every dispatch attempt returned a provider activity block, including a minimal probe; the round nonetheless completed inline and its record passed hard validation only after the sidecar was reshaped from the template's full-panel claim to a scoped focused claim. Details witnessed in the run's review log under the session's records home.

## Suspected root area

`agents/skills/execute-plan/SKILL.md`, Phase 3 (fresh review round) procedure: missing fallback arm for a blocked dispatch channel, and missing pointer to the record honesty grammar for the inline case.
