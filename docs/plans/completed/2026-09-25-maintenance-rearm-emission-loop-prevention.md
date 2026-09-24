# Plan: Maintenance re-arm emission-loop prevention (delete-first ordering)

Backlog origin: `docs/history/backlog/2026-09-25-automation-born-rearm-emission-loop-prevention.md`
Driving force: efficiency

## Terms

- re-arm duty: the state-first duty that re-arms the loop carrier (zcode.md "Recurring automation recipe" re-arm hygiene bullet, the turn-start carrier re-arm duty, and the child payloads' FIRST ACTION paragraph).
- lingered spawner: the completed one-shot automation a session was born from, still listed after firing (enabled false, lifecycle completed) and still binding its spawner session.
- automation-born cap: the platform refusal blocking automation creates in a session whose automation binding lingers; deleting the bound record lifts it in the same session.
- emission loop: repeated read-only listing calls with a decided mutating call still unsent; byte-identical listing output reinforces the pattern because repetition earns no error signal.
- carrier form: whether the armed carrier record is a one-shot or a recurring automation, recorded by the turn-start duty beside the carrier id so the next session can key the delete-first decision without a listing.

## Assumptions

- The fixes are protocol-text edits to the maintenance skill surfaces plus their validation gates; no runtime scripts change; basis: the origin item's "mechanical, ordering-level" fix statement and its Exact location list.
- The stale platform-swallow attribution has no live quote in skill text; basis: repo grep 2026-09-25 found the phrase only inside the origin item itself; the fix therefore adds the corrected diagnosis and a corpus no-hit gate instead of an in-place rewrite.
- Fix 1 keys on the carrier form the turn-start duty records beside the id; form-unknown or a recorded recurring form keeps the existing delete-at-cap-refused ordering, so a delete-first rule cannot open a dark window in front of a live carrier; basis: the item's "lingered spawner" wording and the current one-shot-chain architecture where every carrier turn is born from a completed one-shot; the child payloads' re-arm records no form and does not update the field, and the field paragraph keys the read to the currently recorded carrier id, so the turn after a child dispatch reads form-unknown and takes the reactive ordering, and payload-side form recording rides the accepted residual's follow-up condition; the payload-layer writers that update the id without arming (the child re-arm duty, the watchdog) are guarded by the field's id-keyed read defaulting to form-unknown and by the drift clause, an accepted residual.
- The child payloads' re-arm paragraphs keep their present text: their opening already carries "without listing first", their delete leg says "before a cap-refused create", and neither licenses a listing before the delete, so no contradiction with the tightened bounds is introduced; the payload-explicit alignment of the delete-first and zero-listings bounds is an accepted residual and a follow-up only if an incident shows payload-side drift; basis: prompt-templates.md FIRST ACTION paragraphs read 2026-09-25.
- The dispatch ladder's delete-at-cap-refused ordering for its own lingered completed spawner (zcode.md dispatch ladder) is deliberately retained and out of scope: a dispatch create's payload depends on runtime state the re-arm path does not touch, and the span is suite-pinned; basis: the ladder's operative path text and the origin item's Exact location list, which names only the re-arm duties.
- The failure-cap (G2) machinery, the state schema, and the dispatch ladder's operative delete-plus-create path are unchanged; basis: the item's Suggested fix list, which prescribes ordering and remedy wording only.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Pins delete-first emission ordering, one-message delete+create emission, and zero-listings-after-decision into the maintenance re-arm duties, and scopes the loop guard stand-down to the automation-primitive surface; an efficiency repair, because two carrier turns on the night of 2026-09-25 died to the emission loop, repeated listings with the decided mutations unsent, that the current wording still admits, and each incident idled the loop for hours.

Example of the defect being closed: the 04:01 carrier session recorded its delete-plus-create re-arm decision in the state file, then emitted five listing calls in a row with the decided mutations unsent, and parked the whole turn, taking the authoring lane down with the re-arm failure even though the authoring lane needed no automation primitives and the quota window was fresh. The operator-attended discharge validated the inverse: emitting the delete of the lingered spawner as the FIRST primitive, id taken from the state file, succeeded on the first emission. Example of the remedy scoping being closed: after this plan, that same failure stands down only the automation-primitive surface, and the in-session authoring lane continues in the same turn.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every inserted rule is verifiable by a dedicated occurrence-counted grep whose span occurs exactly once at its named surface, and every replaced stale phrase has a zero-count gate that fires RED on today's tree.
- consistency: no inserted wording contradicts the remaining guard text; duty-mandated verification listings keep an explicit exception; the suite-pinned spans in the edited bullets keep their pinned counts.
- maintainability: each rule lives in the bullet that owns the duty it governs (re-arm hygiene for emission ordering, dispatch discipline for loop-guard remedy and diagnosis); where the same obligation is stated on two surfaces the two wordings are distinct spans, each occurrence-counted, so neither copy can drift silently.

**Done when:**
- All six origin fixes are present at their named surfaces and the full Validation Commands block exits 0.
- The pins suite and the public-hygiene scan exit 0 over the edited tree.
- The plan passes the readiness gate over the final bytes with zero blocking findings.

**Ship when:**
- The next two carrier turns complete their re-arm without a listing-first emission, and any future guard stand-down leaves primitive-free lanes running; operational observation over subsequent loop turns, not a repo check. Evidence owner: the maintenance loop's own turn records; closure condition: two consecutive incident-free carrier turns recorded in the state file. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`

**Tests:**
- none new; the validation gates live in this plan's Validation Commands block and the existing pins suite.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/prompt-templates.md`; the payload layer's re-arm paragraphs keep their present text under the accepted residual recorded in Assumptions; Gate 6 witnesses the parity read-only.
- `scripts/check_maintenance_pins.sh`; no pinned literal changes; the suite is run, not edited; task 1's replacements preserve the suite-pinned form-enumeration span and the ENABLED-verification tail verbatim.
- `.ai-playbook/scheduler-state.json`; runtime state, not skill text; the form record is the additive `parent_automation_form` field, registered in SKILL.md's schema block without a schema-version bump (the additive children-entry worktree field precedent).
- `docs/history/backlog/*`; the origin item stays in place under the backlog top level per the plans skill lifecycle; routing happens at completion, not in this plan's tasks.

## Validation Commands

Authoring-time RED evidence, recorded 2026-09-25 over the pre-edit tree and re-executed after the round 1 fold: the stale-phrase gates fire RED (stale hygiene clause 1, stale listing bound 1, stale turn-start paraphrase 1, unscoped remedy 1), every new-span gate reads 0, the attribution sweep exits rc 1 (clean; the phrase lives only in the origin item and this plan, both outside the swept surfaces), the three preserved pin spans read 1, 1, and 1, the payload parity span reads 3, and the pins suite exits 0. The block's first failing gate on the pre-edit tree is Gate 1's stale-clause check.

```bash
REPO="$(git rev-parse --show-toplevel)"
Z="$REPO/agents/skills/maintenance/zcode.md"
S="$REPO/agents/skills/maintenance/SKILL.md"
P="$REPO/agents/skills/maintenance/prompt-templates.md"
occ() { grep -oF "$1" "$2" | wc -l | tr -d ' '; }

# Gate 0: pins suite over the edited surfaces
bash "$REPO/scripts/check_maintenance_pins.sh" || { echo "GATE0 pins-suite FAILED"; exit 1; }

# Gate 1 (task 1): delete-first + one-message emission rule keyed on the recorded carrier form
test "$(occ 'delete the own lingered record before a create the automation-born cap refused' "$Z")" -eq 0 || { echo "GATE1 stale rearm-hygiene clause still present"; exit 1; }
test "$(occ 'the FIRST automation primitive of the decided re-arm is the delete of that record' "$Z")" -eq 1 || { echo "GATE1 delete-first span missing"; exit 1; }
test "$(occ 'the delete is the earlier call of the one assistant message that also emits the create' "$Z")" -eq 1 || { echo "GATE1 one-message span missing"; exit 1; }
test "$(occ 'form-unknown or a recorded recurring form keeps the delete at the cap-refused create' "$Z")" -eq 1 || { echo "GATE1 hygiene form-fallback span missing"; exit 1; }
test "$(occ 'its own report standing in for the listing' "$Z")" -eq 1 || { echo "GATE1 already-gone generalization span missing"; exit 1; }
test "$(occ 'beside the currently recorded carrier id, the armed carrier form as one-shot' "$Z")" -eq 1 || { echo "GATE1 turn-start delete-first span missing"; exit 1; }
test "$(occ 'the armed carrier form in the additive state field' "$Z")" -eq 1 || { echo "GATE1 carrier-form record span missing"; exit 1; }
test "$(occ 'first primitive emission is the recorded delete of that record' "$S")" -eq 1 || { echo "GATE1 SKILL.md agnostic delete-first span missing"; exit 1; }
test "$(occ 'a recorded recurring form or form-unknown keeps the delete at the cap-refused create' "$S")" -eq 1 || { echo "GATE1 SKILL.md form-fallback span missing"; exit 1; }
test "$(occ 'while a recorded recurring form or form-unknown keeps the delete at the cap-refused create' "$Z")" -eq 1 || { echo "GATE1 turn-start form-fallback span missing"; exit 1; }
test "$(occ 'parent_automation_form' "$Z")" -eq 1 || { echo "GATE1 zcode form-field span missing"; exit 1; }
test "$(occ 'parent_automation_form' "$S")" -eq 6 || { echo "GATE1 SKILL.md form-field registration count wrong"; exit 1; }
test "$(occ 'clears it to null' "$S")" -eq 1 || { echo "GATE1 reader-adoption clearing span missing"; exit 1; }

# Gate 2 (task 2): zero-listings-after-decision with the duty-mandated exception; stale bounds replaced
test "$(occ 'at most one listing is permitted, after the mutation decision and never before it' "$Z")" -eq 0 || { echo "GATE2 stale listing bound still present"; exit 1; }
test "$(occ 'so it lists at most once, after the mutation decision and never before it' "$Z")" -eq 0 || { echo "GATE2 stale turn-start paraphrase still present"; exit 1; }
test "$(occ 'the recorded mutations are the only permitted next primitive calls' "$Z")" -eq 1 || { echo "GATE2 hygiene zero-listings span missing"; exit 1; }
test "$(occ 'the only permitted next primitive calls are the recorded mutations' "$Z")" -eq 1 || { echo "GATE2 dispatch zero-listings span missing"; exit 1; }
test "$(occ 'other than a listing a duty mandates as its decision input' "$Z")" -eq 1 || { echo "GATE2 duty-mandated exception span missing"; exit 1; }
test "$(occ 'never between a recorded mutation and its emission' "$Z")" -eq 1 || { echo "GATE2 turn-start retimed bound span missing"; exit 1; }
test "$(occ 'any listing emitted before them is the loop signature by construction' "$Z")" -eq 1 || { echo "GATE2 signature-by-construction span missing"; exit 1; }
test "$(occ 'a refusal is a DIFFERENT result that breaks the loop' "$Z")" -eq 1 || { echo "GATE2 discriminator span missing"; exit 1; }
test "$(occ 'consecutive calls in a single assistant message' "$Z")" -eq 1 || { echo "GATE2 dispatch one-message span missing"; exit 1; }

# Gate 3 (task 3): remedy scoped to the automation-primitive surface
test "$(occ 'leave the parent armed, and end the turn' "$Z")" -eq 0 || { echo "GATE3 unscoped remedy still present"; exit 1; }
test "$(occ 'stand down the automation-primitive surface for the session' "$Z")" -eq 1 || { echo "GATE3 scoped remedy span missing"; exit 1; }
test "$(occ 'lanes executable without primitives continue per the scoped remedy' "$Z")" -eq 1 || { echo "GATE3 suppression-scoping span missing"; exit 1; }
test "$(occ 'the just-succeeded state write is the able-surface witness' "$Z")" -eq 1 || { echo "GATE3 continuation-witness span missing"; exit 1; }
test "$(occ 'stop sentence yields to this scoping' "$Z")" -eq 1 || { echo "GATE3 prompt-precedence span missing"; exit 1; }

# Gate 4 (task 4): corrected diagnosis present; stale attribution absent from the live skill corpus (agents/ and scripts/; this scope is skill text, docs quotes are history)
test "$(occ 'emission selection, not primitive health' "$Z")" -eq 1 || { echo "GATE4 diagnosis span missing"; exit 1; }
test "$(occ 'no looping session in that window shows a failing mutation' "$Z")" -eq 1 || { echo "GATE4 diagnosis witness span missing"; exit 1; }
test "$(occ 're-opens the primitive-health hypothesis' "$Z")" -eq 1 || { echo "GATE4 reopen span missing"; exit 1; }
grc=0; grep -rnF 'swallowed as listings' "$REPO/agents" "$REPO/scripts" 2>/dev/null; grc=$?
test "$grc" -eq 1 || { echo "GATE4 stale attribution rc=$grc (0=found, >=2=tool error)"; exit 1; }

# Gate 5: suite-pinned spans survive the edits (counts the pins suite also enforces)
test "$(occ 'or the live recurring fallback record this session spawned from' "$Z")" -eq 1 || { echo "GATE5 pinned form-enumeration span drifted"; exit 1; }
test "$(occ "the loop's signature appeared (two listings, no mutating step between them)" "$Z")" -eq 1 || { echo "GATE5 guard-signature count drifted"; exit 1; }
test "$(occ 'a state-first write that preceded the first listing' "$Z")" -eq 1 || { echo "GATE5 state-first gate count drifted"; exit 1; }

# Gate 6: payload parity holds read-only (payloads keep the listing-first-free opening)
test "$(occ 'without listing first' "$P")" -ge 1 || { echo "GATE6 payload parity lost"; exit 1; }

# Gate 7: hygiene over the whole repo, anchored to the repo root
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || { echo "GATE7 hygiene FAILED"; exit 1; }

echo "ALL VALIDATION GATES GREEN"
```

### Task 1: Delete-first emission ordering and one-message shape (origin fixes 1 and 2)

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/SKILL.md`

- [x] zcode.md turn-start carrier re-arm duty bullet: replace the sentence beginning `It deletes its own spawner record whatever its form` so that the suite-pinned parenthetical `(a lingered completed one-shot, or the live recurring fallback record this session spawned from)` is preserved verbatim and the sentence reads, verbatim: `It deletes its own spawner record whatever its form (a lingered completed one-shot, or the live recurring fallback record this session spawned from): when the state file records, beside the currently recorded carrier id, the armed carrier form as one-shot, that delete is the duty's first primitive emission, before any listing that is not itself duty-mandated and before the create (already-gone is success), while a recorded recurring form or form-unknown keeps the delete at the cap-refused create; the duty still treats an already-exists refusal as success only after the ENABLED verification (title plus prompt opening, the prompt containing the resolved repository root).` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md same bullet: extend the sentence `The duty's final targeted edit records the fresh carrier id into` by inserting, after the words `the armed fire time into `next_turn_at` (null when nothing could be armed)`, the words `, together with the armed carrier form in the additive state field `parent_automation_form` (one-shot or recurring; null at rest), so the next session's delete-first decision reads form from state` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md re-arm hygiene bullet: replace the clause `delete the own lingered record before a create the automation-born cap refused` with, verbatim: `in an automation-born session whose state file records the armed carrier as a one-shot, the FIRST automation primitive of the decided re-arm is the delete of that record by the state-recorded id, emitted before any listing that is not itself duty-mandated and before the create (already-gone is success; the delete lifts the automation-born cap, so the refusal path no longer gates the ordering); the delete is the earlier call of the one assistant message that also emits the create, whose arguments never depend on the delete result, and a create cap-refusal after an in-message delete takes the existing escalation paths with no further emission; form-unknown or a recorded recurring form keeps the delete at the cap-refused create; a delete-first target whose delete reports a live rather than lingered-completed record proceeds with the same-message create regardless, the targeted edit records the form the delete observed so the next read self-corrects, and the drift is named in the turn output` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md re-arm hygiene bullet: extend the sentence beginning `The already-gone outcome is success too` so that after `recorded as success with no escalation and no retry` it continues, verbatim: `; a delete-first emission reporting the record already gone is success-shaped the same way, its own report standing in for the listing` [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Step 0 turn-start bullet: immediately after the sentence the pins suite anchors (`turn-start carrier re-arm: run the runtime overlay's Turn-start carrier re-arm duty before the survey`), insert this runtime-agnostic sentence, verbatim: `In a session whose own spawner record lingers completed, the duty's first primitive emission is the recorded delete of that record, before any listing that is not itself duty-mandated; already-gone is success; a recorded recurring form or form-unknown keeps the delete at the cap-refused create.` No runtime primitive name may appear in the inserted sentence (the pins suite asserts SKILL.md names no runtime primitive) [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md state-schema registration: in the State file schema block, insert the line `"parent_automation_form": null,` immediately after the `"parent_automation_id": "<id or null>",` line; in the sanctioned-writer enumeration's parenthetical naming the duty's final one-edit recording, extend the recorded fields with `and the armed carrier form into `parent_automation_form``; in the Step 6 carry-forward sentence listing the fields written outside Step 6 (`pending_dispatch`, `pending_rearm`, `next_turn_at`), append one more clause before the sentence's final period: `; `parent_automation_form` (written by the same edits, so the rewrite must carry it)`; extend the sanctioned-writer enumeration's rearm-on-touch class entry with `parent_automation_form` among its targeted-edit fields, and prescribe in the Step 1 reader's id-adoption arm that the adopting edit clears `parent_automation_form` to null; after the `next_turn_at` field paragraph, insert this field paragraph, verbatim: `parent_automation_form` is the armed carrier's form: `one-shot` or `recurring` when armed; `null` at rest. Writers: the Turn-start carrier re-arm duty and a rearm-on-touch session's arming edit record it beside the id, and the Step 1 reader's id-adoption edit clears it to null; the read keys on the form recorded beside the currently recorded `parent_automation_id`, and any other case (a null field, an unrecognized value, or an id adopted without a form) is form-unknown (an additive field; schema version unchanged). [class: IMPLEMENTATION_REQUIRED]
- [x] `TaskGate1` run: Gates 0 and 1 (plus Gate 5); expect every Gate 1 count as named, Gate 0 GREEN, and the Gate 5 pinned-form span still 1; Gates 2 to 4 still RED until their tasks land, Gate 6 and Gate 7 GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance delete-first re-arm emission rule at both duty sites` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Zero-listings-after-decision and the refusal discriminator (origin fixes 3 and 5)

Files:
- `agents/skills/maintenance/zcode.md`

- [x] zcode.md re-arm hygiene bullet: replace the clause `at most one listing is permitted, after the mutation decision and never before it` with, verbatim: `after a recorded-but-unexecuted mutation, the recorded mutations are the only permitted next primitive calls, other than a listing a duty mandates as its decision input (the state-file-cannot-decide listing, the pending-rearm armed verification); a listing after the mutations have executed stays governed by the dispatch-discipline bounds` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md turn-start carrier re-arm duty bullet: replace the clause `so it lists at most once, after the mutation decision and never before it, and only when the state cannot decide` with, verbatim: `so it lists only when the state file cannot decide, and never between a recorded mutation and its emission` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md dispatch-discipline bullet, appended immediately after its preventive-emission-rule sentence, two sentences, verbatim: `Recorded-mutation precedence: once a re-arm or dispatch decision is recorded state-first, the only permitted next primitive calls are the recorded mutations, emitted as consecutive calls in a single assistant message, and any listing emitted before them is the loop signature by construction, not a bookkeeping step; the exception is a listing a duty mandates as its decision input (the ladder confirm listing, the state-file-cannot-decide listing, the pending-rearm armed verification), which precedes the mutations without being the loop signature.` and `Discriminator: when a session catches itself re-listing with a decided mutation pending, the next call to emit is the recorded delete even at the risk of a refusal, because a refusal is a DIFFERENT result that breaks the loop; listings are free and therefore self-reinforcing, while mutations always return new information.` [class: IMPLEMENTATION_REQUIRED]
- [x] `TaskGate2` run: Gates 0 and 2 (plus Gates 1 and 5); expect the two stale bounds at 0, the seven new Gate 2 spans at 1 each, and every Gate 1 and Gate 5 count unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance zero-listings-after-decision rule and refusal discriminator` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Stand-down remedy scoped to the automation-primitive surface (origin fix 6)

Files:
- `agents/skills/maintenance/zcode.md`

- [x] zcode.md dispatch-discipline bullet: replace the sentence `record a \`turn_error\` naming the deferred target, leave the parent armed, and end the turn.` with, verbatim: `record a \`turn_error\` naming the deferred target, leave the parent armed, and stand down the automation-primitive surface for the session; lanes whose delivery requires automation primitives (clocked dispatches, further re-arm attempts) end, while lanes executable without primitives (in-session authoring under a fresh-window quota signal, the claim, worktree, review, and landing surfaces) continue, because under a standing authoring-only directive the authoring lane is the loop delivery and must not inherit a re-arm mechanical failure; the just-succeeded state write is the able-surface witness for the continuation, and a continuation lane re-runs its own entry guards (the fresh-window quota signal, the claim and occupancy checks) before proceeding; the scheduler prompt's stop sentence yields to this scoping, the state-file record being the stop it requires for the stood-down surface.` [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md emission-suppression rule, same bullet: extend the clause `do not attempt a third listing or a narrated create, and stand down via a Bash state write immediately` with the trailing words, verbatim: `, and the stand-down covers the automation-primitive surface and the lanes that require it, while lanes executable without primitives continue per the scoped remedy above` [class: IMPLEMENTATION_REQUIRED]
- [x] `TaskGate3` run: Gates 0 and 3 (plus Gates 1, 2, and 5); expect the unscoped remedy at 0, the four new Gate 3 spans at 1 each, and all earlier gate counts unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance loop-guard stand-down scoped to the primitive surface` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Corrected diagnosis; stale platform-swallow attribution retired (origin fix 4)

Files:
- `agents/skills/maintenance/zcode.md`

- [x] zcode.md dispatch-discipline bullet, appended after the discriminator sentence of task 2, verbatim: `Store-evidenced diagnosis (2026-09-25, tool_usage table, that day's store window): the failure is emission selection, not primitive health; every looping session in that window executed mutations successfully in hours before and after the loop, only sessions whose first automation primitive after the decision was a listing looped; the documented 04:01 store witness shows clean mutations in hours before and after its loop, and no looping session in that window shows a failing mutation. The earlier platform-swallow attribution of the 2026-09-24 01:0x turn_error is retracted: no store evidence supports a harness-side swallow, and triage treats that wording as superseded wherever it is quoted; a future loop whose store trace shows failing or lying mutations re-opens the primitive-health hypothesis (the echoed-success-but-never-fired update defect of 2026-09-19 is the standing counterexample class).` [class: IMPLEMENTATION_REQUIRED]
- [x] `TaskGate4` run: Gates 0 and 4 plus the full block; expect both diagnosis spans and the reopen span at 1, the negated corpus sweep rc 1 (clean), and Gate 7 GREEN; at this point the entire Validation Commands block exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: maintenance store-evidenced emission-loop diagnosis, platform-swallow attribution retired` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Suite green and final certification inputs

Files:
- none new; verification over the tree tasks 1 to 4 produced

- [x] Run the full Validation Commands block; expect `ALL VALIDATION GATES GREEN` and exit 0, with the pins suite (Gate 0) and hygiene (Gate 7) green over the edited tree [class: REPOSITORY_TEST]
- [x] Commit: `test: maintenance re-arm emission-loop prevention validation green` [class: IMPLEMENTATION_REQUIRED]

## Execution notes

Executed 2026-09-25 in worktree `ai-playbook-exec-rearm` (branch `2026-09-25-execute-plan-maintenance-rearm-emission-loop-prevention` off main `7a15764a`), one commit per task:

- Task 1: delete-first + one-message rule at both duty sites (zcode.md turn-start bullet and re-arm hygiene bullet; SKILL.md Step 0 sentence + `parent_automation_form` schema registration with 6 occurrences, reader-adoption clearing). TaskGate1 + Gate 5 counts all as named, Gate 0 green.
- Task 2: zero-listings-after-decision bound (hygiene + turn-start retiming) and the dispatch-discipline recorded-mutation precedence + discriminator sentences. TaskGate2 all green.
- Task 3: stand-down scoped to the automation-primitive surface with the continuation-witness and prompt-precedence clauses; emission-suppression extension. TaskGate3 all green.
- Task 4: store-evidenced diagnosis + platform-swallow retraction; corpus sweep rc 1 (clean). TaskGate4 green.
- Task 5: full Validation Commands block exit 0, `ALL VALIDATION GATES GREEN` (pins suite + public hygiene green over the edited tree). The task-5 commit is folded into the plan-checkbox tick commit (no tree delta remained after task 4).

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-25-automation-born-rearm-emission-loop-prevention.md: disposition folded into 2026-09-25-maintenance-rearm-emission-loop-prevention.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md: disposition folded into 2026-09-25-maintenance-rearm-emission-loop-prevention.md (2026-09-25); per-item file deleted.
