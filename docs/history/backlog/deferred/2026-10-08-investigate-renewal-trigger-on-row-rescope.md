# Backlog: no investigate renewal trigger when an origin row's scope changes after its entry exists

- **Filed:** 2026-10-08, operator compliance ask in the friction-sweep session ("did you run investigate for the renewed backlog item?")
- **Status:** deferred (2026-10-11; fresh plan review found the candidate can still dispatch before refresh, and the date-only `Added:` line cannot identify the original authoring commit; preventing stale dispatch would add a blocking pause with no same-change blocker retirement)
- **Workflow:** backlog
- **Priority:** deferred
- **Origin class:** self-serving (the repository's own workflow skills are the affected surface)
- **Class:** skill-contract gap
- **Skill/step:** agents/skills/investigate/SKILL.md (the stage contract and standing write rules); agents/skills/maintenance/SKILL.md (the monitor's rolling prompt log duties, read side)

## Observed vs expected

Observed: the investigate contract covers new items (the Stage 0 survey skips origins already represented in either rolling log's Origins lines or a plans-root plan file) and authoring-start freezes, but no clause says what happens when an origin row's recorded scope materially changes after an entry exists for it. The witnessed sequence: the memory-index row was rescoped by operator decision (the row's Rescope section, commit 2a5962888) and the existing entry was amended by targeted edit only; a fresh anchored pass ran later the same day (commit 5251042ca) and materially reshaped the prompt after archaeology found the recurring-task registry consult - an outcome the amendment could not have produced. The gap surfaced only because the operator asked whether the pass had been re-run; no mechanism would have noticed.

Expected: a renewal duty - when an origin row's scope changes materially after an entry exists (a Rescope-class section, a recorded operator decision, or an equivalent in-row witness newer than the entry's Added line), the change's own session re-runs the anchored investigate pass for that row and refreshes the entry, or records the renewal-skip reason in the entry. The monitor's log-read side treats a noticed row-scope/entry divergence as a renewal candidate with the same duty. The duty composes with the freeze rule: a frozen entry still takes no prompt rewrite, so a renewal under freeze records the pending renewal and executes at unfreeze.

## Suggested direction

Define the trigger where the amendment precedent already lives (the investigate skill's targeted-edit rules) and mirror the read-side duty in the maintenance monitor's rolling prompt log duties. The trigger reads the origin row itself (a self-declaring Rescope-class section or material status change), never a new digest store or ledger; the pins suite updates in the same change because both homes are pinned surfaces.

## Evidence

- The witnessed same-day sequence: amendment 2a5962888 (13:35) without a pass; renewal pass 5251042ca (15:04) reshaped Arm 1 onto the recurring-task registry consult.
- The operator compliance ask that caught the gap, 2026-10-08: no surface answered the question "did you run investigate for the renewed row?".
- agents/skills/investigate/SKILL.md: the Stage 0 skip rule and the freeze rule have no renewal counterpart.

## Deferred disposition

The latest plan is parked byte-for-byte at `docs/history/plans/deferred/2026-10-10-investigate-renewal-trigger.md`; review r6 is at `docs/history/reviews/2026-10-11-plan-review-investigate-renewal-trigger-r6.md` and records the unresolved precedence and provenance defects. Do not execute or mark this origin covered. Revive only after the operator chooses a non-blocking solution or names an existing blocker to retire in the same change; any revived design must define original-entry commit derivation and ensure the stale payload cannot dispatch before refresh without adding unpaid blocker machinery. The already-pruned `PLAN-PROMPTS.md` entry stays pruned; its receipt remains historical.
