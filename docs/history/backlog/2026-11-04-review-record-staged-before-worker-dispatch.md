Status: open
Priority: high
Class: fix-class
Origin class: witnessed defect (interactive maintenance auth authoring session, plan-review delta round r5, 2026-11-04)
Cluster: docs/history/backlog/2026-11-02-done-finalize-resume-marking-honesty-r4-residuals.md (record-marking honesty family)

# Review records can be staged naming worker completion before the workers return

Skill/step: `agents/skills/review-plan/SKILL.md` (Record statistics step 7 and the round-close step); `agents/skills/review-staging/SKILL.md` (record grammar, Panel section)

## Observed vs expected

Observed: during a focused plan-review delta round, the round record and its sidecar were staged with the Panel row already marked `complete` and zero findings while the named worker had not yet been dispatched; the dispatch then failed on a provider usage wall, leaving a staged canonical record claiming panel work no worker performed. The honest remedy consumed extra turns after the window reset: dispatch the worker for real, fold its actual verdict, amend the record's Triage outcomes with the dispatch evidence (completion time and the pause note), correct a stale count the anticipation had frozen, and re-run the hard staging validator.

Expected: the record-staging step text states the fence explicitly: a staged record's Panel rows, counts, and verdict may describe only workers that actually returned; a staging interrupted before a worker returns is completed by dispatching and amending the record with the real dispatch evidence, or by relabeling the panel row to the honest blocked state, never by leaving the anticipatory claim standing for a later turn to ratify.

## Evidence (trimmed)

- A delta-round record staged with Panel status `complete`, verdict ready, and a Triage-scope count frozen before dispatch; the dispatch refused on the usage wall; post-reset the worker ran, returned the same zero-finding verdict, and the record was amended with the dispatch timestamp and pause note; the count correction (the cited series had grown by the round's own record) and the hard validator PASS closed the gap.
- Neither review-plan's record-statistics step, nor review-staging's record grammar, nor the staging validator distinguishes an anticipatory panel row from a returned one; only the session's own re-check caught it.

## Suspected root area

The review-plan record-staging step text (the fence sentence is missing; the step order implies it but nothing states it). A validator arm, if ever promoted, would compare a record's panel-completion claims against per-worker return evidence and is out of scope until the machinery admission protocol's true-catch bar is met.

## Ship when

The record-staging step and the staging skill's record grammar carry the explicit fence sentence plus the usage-wall interruption remedy (dispatch-then-amend, or relabel), and the witnessed remedy pattern is citable from the skill text instead of re-derived per incident.
