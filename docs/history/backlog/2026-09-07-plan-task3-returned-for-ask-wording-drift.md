# Backlog: archived plan Task 3 prescription text predates the r1/r2 returned-for-ask review fixes

- **Origin:** returned-for-ask semantics execute-plan Phase 3 review r2, finding F5 (risk + contract-docs, documentation#prose-prescription-drift), 2026-09-07; widened per review r4, finding F1 (correctness-completeness + risk + contract-docs), 2026-09-07; widened per review r6, finding F5 (contract-docs, consistency#sibling-plan-forward-conflict), 2026-09-07
- **File:** docs/plans/2026-09-04-returned-for-ask-semantics.md (Terms "outstanding presentation" definition, Gist item 3, Task 3 first checkbox prescription)
- **Status:** open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)


Superseded spans in the unarchived plan (all pre-r1/r2 wording; the shipped skill text governs):

1. **Terms definition (Terms section, "outstanding presentation" bullet):** defines an outstanding presentation as one "whose question has not yet been relayed to the user (or returned to the orchestrator / turned into a stop for direction in a non-interactive run)". The r2 semantics split this: a non-blocking ask is discharged by recording (not by relaying), and "outstanding" now means undischarged; relaying/surfacing is a separate exit-report obligation.
2. **Gist item 3:** prescribes that an outstanding returned-for-ask presentation must be "performed (interactive) or escalated ... before returning to Step 3.1", mirrored as a stop in review-loop rule 4. The r2 fix replaced this with the discharge split (gate item 6): recording IS the discharge for a non-blocking ask, after which the loop may continue; only a must-stay-blocking ask stops for direction.
3. **Task 3's checked first checkbox:** prescribes the pre-r1 wording for the Step 3.3 gate item ("the Step 3.5 counter update waits for the answer").
4. **Task 3's second checkbox:** prescribes review-loop rule 4's original blanket stop sentence. The r1 and r2 review fix rounds superseded the Task 3 prescriptions: gate item 6 now states the recording-is-the-discharge split for non-blocking asks (wait applies before the next Step 3.1 launch; no Step 3.5 counter role), and rule 4 now splits must-stay-blocking (stop for direction) from non-blocking (record + surface at exit). The shipped skill wording governs.

The validation pins are substrings of both the old and new variants, so the fail-closed checks cannot see this drift. The plan file is not edited in-run because any plan edit invalidates the reviewed digest; at archive time, record this divergence in the archive note (or accept the plan as a frozen historical record of what was prescribed at authoring time) rather than editing the plan body.

## Sibling plan forward conflict (widened per review r6, finding F5, 2026-09-07)

The unexecuted sibling plan `docs/plans/2026-09-04-review-pointer-wiring-polish.md` prescribes edits (its ~L105-112 and ~L159-162) that target spans this branch rewrote: its probes and prescriptions predate the returned-for-ask single-source wiring and would delete/replace the exact text now carrying the review-staging pointer at `execute-plan` subagent-prompts step 7 and the Step 3.3 gate item 4 canonical scope phrase. Executing that plan as written regresses the review-staging pointer wiring. Before executing it, either run a fresh `review-plan` round on it so the prescriptions are re-derived against the current tree, or amend its Task text; do not execute it as authored.
