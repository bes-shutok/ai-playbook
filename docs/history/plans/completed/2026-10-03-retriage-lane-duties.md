# Plan: Deferred-Corpus Re-Triage Lane Duties

Backlog origins (scope of record):
- docs/history/backlog/2026-10-01-deferred-revival-trigger-census.md
- docs/history/backlog/2026-10-01-retriage-proposal-consumption.md

Driving force: automation
Plan review record: the staging series docs/reviews/2026-10-03-plan-review-retriage-lane-duties-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The deferred-corpus re-triage machinery owns both halves of the deferral contract: a per-turn census arm detects fired revival triggers every survey turn, and its discharge duties revive or close rows inside the consult's existing serialization.

- Fired revival triggers stop aging silently between the 30-day sweeps: every survey turn evaluates each open deferred row's recorded trigger and reports fired/total.
- Rows whose work is already landed stop festering: the discharge duty closes them in place with a completion receipt, and fires rows revive through the deferred README protocol with a restoration receipt, serialized through the sweep's existing move-list and merge-lock machinery.
- A pending proposal report stops disappearing into a gitignored directory: the record carries a pending_proposal field, every survey turn carries a pointer until resolution, and no second adjudication of a proposed row happens without reading the proposal first.

Gate delta: additions, each priced: (1) one per-turn census survey duty (non-blocking output except its once-only turn_error escalation, which feeds the existing G2 turn tripwire, and its six-turn census-aging counter in the record's census-aging field, both priced by the same witnessed silent-fire census) (seven of sixteen revival triggers fired with zero action before the operator-prompted triage, main 51bb9758); (2) one same-turn discharge executing arm that deliberately reuses the consult's existing serialization (the sweep's move-list, the merge landing lock, the lane occupancy rules, the claim gate, and the sweep's pre-commit gate chain (doc_registry_validator, the check-writes gate, the origins gate, the added-lines em-dash scan); no new child kind, no new schedule, no new automation primitive, no new lock) priced by the same witness plus the witnessed amnesia incident (one deferred row carried two conflicting recorded adjudications, owner shown neither); (3) one additive record key (pending_proposal) priced by the same amnesia witness; (4) precedence sentences in the arm and the deferred README, behavior-binding prose with no enforcement arm, priced by the same amnesia witness, and mirrored in two homes deliberately because manual deferred triages read the README while lane actors read the consult; (5) exactly one new presence pin on the precedence span, priced by the amnesia witness as its guard, with the census and pointer spans and the r2 fix clauses (the citing-resolution clear, the drift-retry binding, the aging and escalation bounds, the memory-index note) adjudicated unpinned (self-reporting or record-observed duties whose failure is visible in the survey output or in the record the duty writes). Removals: none; the rubric sweep, its reject classes, its authorization contract, and all existing pins are untouched.

## Terms

- **Re-triage consult:** the maintenance survey's Deferred-corpus re-triage consult bullet in agents/skills/maintenance/SKILL.md (the consult) and its sub-bullets; the procedure of record for the deferred-corpus lane, per the retriage pointer stub in agents/skills/maintenance/prompt-templates.md.
- **Per-turn arm:** the new top-level survey bullet this plan adds beside the consult (the Deferred-revival census and discharge arm); it runs every survey turn regardless of the consult's next_due.
- **Deferred corpus:** the top-level .md entries of docs/history/backlog/deferred/ and docs/history/plans/deferred/, README files excluded (the corpus the consult's digest enumeration already defines).
- **Revival trigger:** the revival condition a deferred row records anywhere in the row (its Status or Priority line, a recorded Trigger line or section, or a receipt section); the deferred README's revival protocol discharges it.
- **Restoration receipt / completion receipt:** the per-row record formats the 2026-10-01 triage landing established (historical provenance main 51bb9758): a Restoration receipt section names the fired trigger with fresh disk evidence; a Completion receipt names the fixing work that let a row close in place.
- **Pending proposal:** a re-triage sweep's proposal report awaiting an owner decision; today it is written only to the gitignored runtime directory with no consumption surface.

## Assumptions

- assume the consult block plus the new per-turn arm are the duty homes, and a dispatched re-triage child inherits these duties by assembly (the pointer stub names the consult block the procedure of record, agents/skills/maintenance/prompt-templates.md); basis: on-disk stub text and the origin rows' coordination clause; the sibling registry-migration entry absorbs the consult paragraph verbatim, and whichever of the two plans lands second re-reads the landed region and reconciles the absorbed copy before its own completion record.
- assume the census evaluates every open deferred row whose recorded trigger text is parseable from its Status or Priority line, a recorded Trigger line or section, or a receipt section; rows without parseable trigger text are census-skipped-with-reason, never guessed; basis: the deferred README rubric and the real recording conventions of the live corpus (the porcelain row's Status-line self-gate, the restored rows' body Trigger lines).
- assume the pins decision is adjudicated by this plan as: exactly one new presence pin (the precedence span), everything else unpinned; basis: the origin row's authoring constraint deferring the decision to this pass under the 2026-09-28 cost-benefit adjudication, with the amnesia witness pricing the one pin.
- assume the porcelain-unquote-octal-escapes row's pending reject proposal stays operator-gated; basis: the consult's authorization paragraph and origin row arm 6.
- assume the plan re-declares the driving force as automation where the origin rows declare reliability; basis: the closed taxonomy's automation tag covers machinery that runs a routine loop itself, and the per-turn census is exactly that; the origins' reliability witness is the pricing evidence the Gate delta cites.
- assume review records land at docs/reviews/2026-10-03-plan-review-retriage-lane-duties-r*.md; basis: the repository's record-naming convention.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The re-triage machinery gains the revival half of the deferral contract and a pending-proposal surface, so the loop itself runs the census, revival, and proposal consumption instead of waiting for operator-prompted triages.

Today the consult's contract covers only rejection: a 30-day rubric sweep that moves rows to rejected/ under owner authorization. The deferred README's revival protocol has no owner between sweeps, so seven of sixteen recorded revival triggers fired with zero action (main 51bb9758), three completed rows sat open, and the lane's one proposal report (2026-09-27) left its lone reject candidate invisible: a later manual triage adjudicated the same row on a different basis without knowing the proposal existed. After this plan, a survey turn runs a bounded census through a closed probe vocabulary, the discharge duties revive a fired row or close a verified-fixed one through the sweep's own serialization, and a pending proposal is visible in the survey output every turn until an owner resolves it.

Example: the census reads the row docs/history/backlog/deferred/2026-09-25-porcelain-unquote-octal-escapes.md, whose Status line records a corruption-witness self-gate; the census's fixed-string probe for the witness anchor over the row-named surfaces finds none, so the census reports it unfired and writes nothing. A row whose named surface gained commits since deferral reports fired, and the discharge duty executes the deferred README's protocol that same turn, with the move entering the sweep's move-list and the merge landing lock held.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the census classifies fired/unfired per each row's recorded trigger through the closed probe vocabulary; the discharge duties follow the deferred README protocol's mechanics (protocol steps owned there, never copied into the skill text) with the receipt and serialization extensions this plan prescribes; receipts match the 2026-10-01 triage landing's worked-example formats.
- non-regression: every span of the consult not prescribed by this plan stays byte-identical; the pins suite exits 0 including the one new pin; the rubric sweep, its reject classes, and its authorization contract are unchanged.
- maintainability: the per-turn duties live in one arm beside the consult, and the consult's only new text is the record-field sub-bullet, so the sibling registry migration carries both verbatim.

**Done when:**
- The consult block carries the pending-proposal field sub-bullet; the per-turn arm bullet carries the census, the discharge duties, and the pending-proposal pointer duties; the deferred README carries the mirror precedence sentence and cites the current deferred-plan paths; the legacy-verdict row's Priority line cites the current deferred-plan paths; the pins suite carries the one new precedence pin.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- The dedicated validation greps below pass on the landed tree, and were executed RED-today at authoring with the per-line outcomes recorded in the Validation preamble.

**Ship when:**
- The porcelain-unquote-octal-escapes pending owner decision is put to the operator and resolved by the operator (operations follow-up, class OPERATIONS_FOLLOW_UP: the plan and its executor never resolve it; closure condition: a recorded owner disposition on that row).
- The sibling pluggable-task-registry plan (docs/history/backlog/2026-10-03-pluggable-per-project-maintenance-tasks.md) carries this lane's duty text into the registry when it lands (operations follow-up, class OPERATIONS_FOLLOW_UP: coordination, not this plan's deliverable; the second-lander reconciliation duty above owns the ordering hazard).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- agents/skills/maintenance/SKILL.md (only the consult bullet and its sub-bullets plus the new per-turn arm bullet; pre-edit that region is lines 78-84, and it grows by this plan's own insertions; the rest of the file is frozen; reject any finding that touches other regions)
- docs/history/backlog/deferred/README.md (only the standing-rubric pointer on line 3 and the revival protocol paragraph on line 7)
- docs/history/backlog/deferred/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md (only the two stale path citations in the Priority line, line 4)
- scripts/check_maintenance_pins.sh (only the one new pin registration, its presence pin and its exactly-once companion, and their provenance comment)

**Tests:**
- none; prose-only plan (validation is the pins suite plus the dedicated greps below)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- docs/history/plans/deferred/2026-09-15-plan-readiness-legacy-verdict-grammar-deletion.md; reason: byte-identity frozen by its own park record (review digest db071188 must stay valid); its stale Backlog origin line is recorded as accepted, never repaired
- docs/history/backlog/2026-10-03-pluggable-per-project-maintenance-tasks.md; reason: a peer-authored open row this plan coordinates with, never edits
- scripts/done_sweep_gates_lib.py and every scripts/ file other than the pins suite; reason: the plan adds no code and no gate script

## Validation Commands

Validation preamble (authoring-time execution record): the block below was executed against the pre-task tree with every line observed individually after the r2 and r3 fold batches with identical observed outcomes; lines 1 through 8 exited 1 through the fail-closed wrapper on their missing spans; line 9's probe matched the still-present stale citation in the legacy-verdict row (rc 0, so its fail branch fired); lines 10 and 11 exited 1 on the missing repaired citations; line 12's probe matched the still-present stale rubric pointer in the deferred README (its fail branch fired); line 13's order precheck failed fail-closed on the missing arm bullet (the empty-anchor arm of the conjunction fires, unlike the pre-r2 form); line 14's pin-companion grep exited 1 on the missing pin lines. Every failing line flips GREEN only as its owning task lands (line 5 with Task 1; lines 1 through 4, 6, 7, and 13 with Task 2; lines 8 through 12 with Task 3; line 14 with Task 4). The pins suite (line 15) exited 0 pre-task (existing pins unaffected), and `bash -n` over this block passed.

```bash
SOT=agents/skills/maintenance/SKILL.md
RDM=docs/history/backlog/deferred/README.md
LVR=docs/history/backlog/deferred/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
grep -qF 'Deferred-revival census and discharge arm (per turn, non-blocking)' "$SOT" || fail "per-turn arm bullet missing"
grep -qF 'never an executable string' "$SOT" || fail "probe allowlist span missing"
grep -qF 'enters the move-list before execution' "$SOT" || fail "revival serialization span missing"
grep -qF 'a claimed verdict is skip-and-annotate and aborts the remaining moves of that discharge' "$SOT" || fail "claim-gate semantics missing"
grep -qF 'pending_proposal field into the re-triage record' "$SOT" || fail "pending-proposal field sub-bullet missing"
grep -qF 'records agreement or the distinguishing evidence for the divergence (read-before-adjudicate precedence)' "$SOT" || fail "precedence sentence missing"
grep -qF 'turn_error: pending-proposal-unresolved' "$SOT" || fail "escalation bound missing"
grep -qF 'Before any revival, close, or second adjudication' "$RDM" || fail "README mirror sentence missing"
if grep -qF 'docs/plans/deferred/2026-09-15' "$LVR"; then fail "stale citation survives in legacy-verdict row"; fi
grep -qF 'docs/history/plans/deferred/2026-09-15-plan-readiness-legacy-verdict-grammar-deletion.md' "$LVR" || fail "repaired citation missing"
grep -qF 'docs/history/plans/deferred/README.md' "$LVR" || fail "repaired rubric citation missing"
if grep -qF 'docs/plans/deferred/README.md' "$RDM"; then fail "stale rubric pointer survives in deferred README"; fi
arm_line="$(grep -n '^- Deferred-revival census and discharge arm (per turn, non-blocking)' "$SOT" | head -1 | cut -d: -f1)"; child_line="$(grep -nF 'Child-outcome check' "$SOT" | head -1 | cut -d: -f1)"; { [ -z "$arm_line" ] || [ -z "$child_line" ] || [ "$arm_line" -ge "$child_line" ]; } && fail "arm missing, indented as a sub-bullet, or not placed before the Child-outcome check bullet"
grep -qF 'retriage adjudication precedence exactly-once' scripts/check_maintenance_pins.sh || fail "precedence pin or its exactly-once companion missing"
bash scripts/check_maintenance_pins.sh || fail "pins suite regressed"
```

### Task 1: Pending-proposal field sub-bullet in the consult block

Files:
- agents/skills/maintenance/SKILL.md (consult block, one new sub-bullet after the Output sub-bullet)

Evidence:
- `grep -qF 'pending_proposal field into the re-triage record' agents/skills/maintenance/SKILL.md`; covers the field sub-bullet's presence
- `bash scripts/check_maintenance_pins.sh`; covers non-regression of every existing pin

- [ ] Insert as one new sub-bullet directly after the consult's Output sub-bullet, before the Child-outcome check bullet's indent level, exactly this text, one new line starting with two spaces and `- `: `Pending-proposal field: the proposal path writes a pending_proposal field into the re-triage record (report path, date, pending-decision count, an additive key beside the record's existing fields) the field's clear semantics (citing-resolution requirement, any-actor clear, drift-retry writes), per-turn pointer, precedence, memory-index note, and escalation duties live in the Deferred-revival census and discharge arm, not here.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the record contract reads additive (no schema-version bump claimed, no existing field reworded) and the consult's original bytes are otherwise unchanged: `git diff` over the file shows exactly one added line in that region [class: REPOSITORY_TEST]
- [ ] Run → expect the task's presence grep GREEN and the pins suite GREEN; the remaining block lines stay RED until Tasks 2-4 land [class: REPOSITORY_TEST]

### Task 2: The per-turn census and discharge arm

Files:
- agents/skills/maintenance/SKILL.md (one new top-level bullet directly after the consult block's last sub-bullet, before the Child-outcome check bullet)

Evidence:
- `grep -qF 'Deferred-revival census and discharge arm (per turn, non-blocking)' agents/skills/maintenance/SKILL.md`; covers the arm bullet's presence
- `grep -qF 'never an executable string' agents/skills/maintenance/SKILL.md`; covers the closed probe vocabulary's presence
- `grep -qF 'enters the move-list before execution' agents/skills/maintenance/SKILL.md`; covers the revival serialization's presence
- `grep -qF 'turn_error: pending-proposal-unresolved' agents/skills/maintenance/SKILL.md`; covers the escalation bound's presence
- `bash scripts/check_maintenance_pins.sh`; covers non-regression of every existing pin

- [ ] Insert as one new top-level bullet (single dash, column 0, aligned with the consult bullet) directly after the consult block's last sub-bullet and before the Child-outcome check bullet, exactly this text: `Deferred-revival census and discharge arm (per turn, non-blocking): at every survey turn, regardless of the consult's next_due, run the census, discharge fired rows, and carry the pending-proposal pointer duties, as the four named sub-bullets this task inserts under it` [class: IMPLEMENTATION_REQUIRED]
- [ ] Directly under the parent bullet, insert as a two-space-indented sub-bullet exactly this text: `Census: for each open deferred row in the digest enumeration's corpus (README files excluded), read the row's recorded revival trigger text wherever the row records it (its Status or Priority line, a recorded Trigger line or section, or a receipt section); a row without parseable trigger text is census-skipped-with-reason, never guessed. Evaluate each parsed trigger through the closed probe vocabulary (a since-deferral git log over the row-named surface paths, a fixed-string grep for the row's anchor span over the row-named surfaces, or the one fixed corpus-convergence invocation python3 scripts/plan_readiness.py --sweep for convergence rows); every row-supplied value is passed after an explicit end-of-options separator, and a value whose first character is a dash is a census-skip-with-reason, never an argument; parameters are only paths, anchor spans, and dates extracted from the row, never an executable string; row text naming any other command is a census-skip-with-reason, never an execution. Report fired/total in decision_reason; an ambiguous probe result (tool error, unparseable outcome) is census-report-only, never a revival sanction. Fired-and-skipped means a turn in which the census reports the row's trigger fired and the same-turn discharge did not execute (a claimed-abort, a lane-occupancy deferral, a lock timeout, or any recorded skip reason); a row fired-and-skipped across six consecutive survey turns ages into a census warn entry beside the fired/total report, counted through the record's census-aging field (a per-row counter in the re-triage record, mutated under the same targeted-edit drift-retry rules, never a write into the deferred row files).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Directly under the Census sub-bullet, insert as a two-space-indented sub-bullet exactly this text: `Discharge: a fired trigger discharges in the same turn through the consult's execution machinery: the revival move is a sweep move (it enters the move-list before execution and acquires the merge landing lock per the sweep mechanics bullet, inside the lane's occupancy rules), passes the sweep's gate chain per the consult's Gates bullet (check_backlog_claimed.py, doc_registry_validator.py validate, the check-writes gate, the origins gate, and the added-lines em-dash scan; a claimed verdict is skip-and-annotate and aborts the remaining moves of that discharge per the sweep's claimed-abort rule), discharging the deferred README's revival protocol with its steps owned there (never copied into this text) and a Restoration receipt section per the receipt formats the restored rows of this corpus record; a row whose finding is verified fixed by other work closes in place with a Completion receipt naming the fixing evidence; a revival racing a rejected/ move is recovered by the next sweep's move-list reconciliation.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Directly under the Discharge sub-bullet, insert as a two-space-indented sub-bullet exactly this text: `Pending-proposal pointer: while the consult's pending_proposal record field is set, every survey turn carries a one-line decision_reason pointer to the report; the field clears only when the resolution record cites the proposal (agreement recorded, or the divergence evidence named), so a sweep's reject of a proposed row that cannot cite the proposal leaves the field set and keeps the pointer; the actor recording a citing resolution (a sweep, a manual triage, an owner disposition read back from the row) clears the field in the same targeted record edit, and every retriage-record mutation under this arm follows the targeted-edit drift-retry rules (re-read, re-apply, loser yields), never bare atomic replace; a field set across six consecutive survey turns records turn_error: pending-proposal-unresolved once, with repeats suppressed while the field's value is unchanged; when the runtime provides a persistent memory index, a one-line note records the pending decision.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Directly under the Pending-proposal pointer sub-bullet, insert as a two-space-indented sub-bullet exactly this text: `Precedence: before any sweep or manual deferred triage adjudicates a row named in a pending proposal, it reads the proposal first and records agreement or the distinguishing evidence for the divergence (read-before-adjudicate precedence).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the arm block sits at the right indent (the parent bullet single-dashed at column 0, its four sub-bullets two-space indented) and before the Child-outcome check bullet, and the consult's bytes are otherwise unchanged: a diff against the post-Task-1 tree shows exactly five added lines, the parent bullet plus its four sub-bullets [class: REPOSITORY_TEST]
- [ ] Run → expect the task's four presence greps GREEN and the pins suite GREEN [class: REPOSITORY_TEST]
### Task 3: README mirror sentence, README pointer repair, and row citation repair

Files:
- docs/history/backlog/deferred/README.md (standing-rubric pointer line 3; revival protocol paragraph line 7)
- docs/history/backlog/deferred/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md (Priority line citations, line 4)

Evidence:
- `grep -qF 'Before any revival, close, or second adjudication' docs/history/backlog/deferred/README.md`; covers the mirror sentence's presence
- `! grep -qF 'docs/plans/deferred/2026-09-15' docs/history/backlog/deferred/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md && ! grep -qF 'docs/plans/deferred/README.md' docs/history/backlog/deferred/README.md`; covers both stale-citation removals

- [ ] Append to the revival protocol paragraph (line 7) exactly this sentence: `Before any revival, close, or second adjudication of a row named in a pending re-triage proposal, read the pending proposal first and record agreement or the distinguishing evidence for the divergence.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Repair the deferred README's standing-rubric pointer (line 3) by replacing the substring `docs/plans/deferred/README.md` with `docs/history/plans/deferred/README.md`; no other byte of the line changes [class: IMPLEMENTATION_REQUIRED]
- [ ] In the legacy-verdict row's Priority line (line 4), repair the two stale citations by replacing the substring `docs/plans/deferred/` with `docs/history/plans/deferred/` in both its occurrences (the parked plan path and the rubric README path); no other byte of the line changes [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the block's full Validation Commands; expect every line except line 14 GREEN at this task boundary (line 14, the pin registration, flips with Task 4) [class: REPOSITORY_TEST]

### Task 4: The one new precedence pin

Files:
- scripts/check_maintenance_pins.sh (one pin line and its provenance comment, beside the existing re-triage pin group)

Evidence:
- `grep -qF 'pin "retriage adjudication precedence"' scripts/check_maintenance_pins.sh`; covers the presence pin's registration (the companion is covered by its own evidence line)
- `grep -qF 'retriage adjudication precedence exactly-once' scripts/check_maintenance_pins.sh`; covers the exactly-once companion's presence
- `bash scripts/check_maintenance_pins.sh`; covers the pin passing against the landed SKILL.md text

- [ ] Add beside the existing re-triage pin group, with a provenance comment naming the witness (the 2026-10-03 amnesia incident record, the plan docs/history/plans/2026-10-03-retriage-lane-duties.md), exactly these two pin lines matching the group's presence-plus-exactly-once idiom: `pin "retriage adjudication precedence" grep -qF 'records agreement or the distinguishing evidence for the divergence (read-before-adjudicate precedence)' "$S"` and `pin "retriage adjudication precedence exactly-once" test "$(grep -oF 'records agreement or the distinguishing evidence for the divergence (read-before-adjudicate precedence)' "$S" | wc -l | tr -d ' ')" -eq 1` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the pins suite; expect exit 0 with the new pin passing against the landed Task 2 text [class: REPOSITORY_TEST]

### Task 5: Authoring-time mechanical audit and gate execution (recorded in this plan's Validation preamble)

Files:
- none (this task's evidence is the preamble record above; the block was executed at authoring and re-executed line by line after the r2 fold batch, and the preamble reflects the latest observed outcomes)

Evidence:
- `bash -n` over the Validation Commands block; covers shell syntax
- the rule 22 mechanical audit (pinned spans occur exactly once in the prescribed task text; no external pin literal touched beyond the one new pin); covers the pin/text contract

- [ ] Rule 29 gates executed at authoring (and re-run after every fold batch): `bash scripts/check-no-em-dash.sh touched` over the plan bytes, the public-hygiene scan, and `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-03-retriage-lane-duties.md` from the repo root, all exit 0 [class: REPOSITORY_TEST]
- [ ] Rule 19 RED-today execution recorded: the block ran pre-task with every line observed individually; lines 1 through 14 each failed on their missing span or still-present stale text (fail-closed exits recorded in the preamble), and the pins suite (line 15) passed pre-task [class: REPOSITORY_TEST]
- [ ] Rule 22 audit recorded: each pinned span above occurs exactly once in its task's prescribed text; the only external pins artifact this plan touches is the one new pin line of Task 4 [class: REPOSITORY_TEST]
