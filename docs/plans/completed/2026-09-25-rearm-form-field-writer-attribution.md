# Plan: parent_automation_form writer attribution and stale-form fallback precision (rearm r6 F1/F2/F3)

Backlog origin: docs/history/backlog/2026-09-25-rearm-form-field-writer-attribution.md
Driving force: correctness

## Terms

- `parent_automation_form`: the armed carrier's form field in the scheduler state file (`one-shot` or `recurring` when armed, `null` at rest), additive under schema 4; the support text lives in the maintenance skill's State file semantics section.
- form writers: the Turn-start carrier re-arm duty and a rearm-on-touch session's arming edit, the only writers that record the form beside the id; the Step 1 reader's id-adoption edit clears the field to null.
- non-form-writing id writers: re-arm writers that change `parent_automation_id` without writing the form (for example the watchdog recovery re-arm, the child re-arm duty's targeted edit; the class is exemplary, not exhaustive); each leaves any prior form stale beside the new id.
- stale form: a recognized, non-null form recorded beside a different id than the arming edit recorded; textually indistinguishable from a correctly paired form.
- form-unknown: the read-side classification for anything that is not a valid paired form (a null field, an unrecognized value, an id adopted without a form, or a stale form).
- carry-forward list: the Step 6 state-file rewrite's enumeration of externally written fields the rewrite must preserve.

## Assumptions

- assume the fix is text-only in the two skill files named by the origin's Exact location (`agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/zcode.md`); no runtime script changes and no state-schema change; basis: the origin's Non-goals and the field's additive schema-4 status.
- assume the completed rearm-emission plan stays byte-frozen and the amendment targets only the live skill text; basis: `plans` Plan Lifecycle freezes completed plans, and the origin's fix line ("amend plan-verbatim text at the next natural edit") points at the live copy of that text.
- assume the stale-form case is both added to the form-unknown enumeration and covered by an explicit provenance reading; the two texts divide deliberately: the enumeration item names the stale-form shape for writer attribution, the appended sentence states the general read rule; basis: origin F2 offers either form, and the enumeration alone leaves a reader unable to distinguish a stale form from a paired one, which is exactly the gap F2 names.
- assume the two zero-listings exception lists' asymmetry is recorded as safe rather than aligned; basis: the origin offers either remedy, alignment would edit operative delete-first bound text that the Non-goals freeze, and recording is inert prose.
- assume the divergence between the amended prose and `scripts/rearm_on_touch.py` (the script mirrors the state-first classification and does not implement the provenance reading, so a stale form beside the current id reads as paired to the script but form-unknown per the amended text) is an accepted residual; basis: the origin's Non-goals exclude runtime scripts and bound the damage, and recording it prevents a future editor from reading it as an unplanned gap.
- assume verification is mechanical prose gating: pinned `rg` needles (presence, absence, and occurrence counts), the maintenance pins suite (which gates these two files among others; no pin touches any span this plan amends), and the em-dash gate in insertion-scoped mode; basis: the touched files are markdown skill texts, whole-`file` em-dash mode is known-red on them today (seven pre-existing em-dash occurrences on five lines, all outside every amended span, which this plan must not touch), and the repo convention for prose edits to such files is `added-lines --base "$BASE_SHA"`.

Decision points requiring a grill: none remain (both origin either/or choices resolve mechanically: provenance reading added beside the enumeration; rationale recorded instead of list alignment).

## Gist & Examples

TLDR: the `parent_automation_form` support text is tightened so its writer attribution and form-unknown fallback cannot be misread into adding a form writer or misclassifying a stale form, for correctness.

**Before (today).** The Step 6 carry-forward clause says the form is "written by the same edits" directly after a `next_turn_at` clause that names two writers (the Turn-start carrier re-arm duty AND the child re-arm duty), while the field paragraph names only the turn-start duty and a rearm-on-touch arming edit as form writers and the accepted rearm-r6 residual records that the child re-arm writes no form. A future editor could read the carry-forward clause as instructing the child payload to start writing the form. The form-unknown fallback enumerates "a null field, an unrecognized value, or an id adopted without a form" but not the stale-form case the non-form-writing id writers actually produce: a watchdog recovery re-arm records a new parent id without the form, the old `one-shot` stays beside the new id, and a reader keying on "the form recorded beside the currently recorded `parent_automation_id`" misreads the stale value as a correctly paired form. The ladder precheck parenthetical's unqualified "a cap-refused create" invites conflation with the re-arm create.

**After (this plan).** The carry-forward clause names the form writers explicitly and states that the child re-arm duty's targeted edit writes no form. The field paragraph's enumeration gains the stale-form shape and the provenance reading (a form read is valid only beside the id the arming edit recorded; anything else reads as form-unknown and takes the existing form-unknown path). The ladder precheck parenthetical says "a cap-refused child create", naming the create it actually gates. A one-sentence rationale records why the two zero-listings exception lists may stay asymmetric.

**Worked example (stale form).** A recurring parent is deleted by a watchdog recovery re-arm, which records the replacement id without writing the form; the field still says `recurring` beside the NEW id. Before this plan the read classification for that shape is undefined text; after it the shape is named in the enumeration and the provenance reading classifies it stale, so the read falls to the form-unknown path whose behavior (the bounded reactive path) is already landed and unchanged.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each of the three origin findings (F1 writer attribution, F2 stale-form fallback, F3 precheck qualification and asymmetry rationale) resolves as exactly one pinned amendment site per Task bullet, each gate-pinned; no sentence outside the pinned amendments changes; the child re-arm duty still writes no form in the amended text; the re-arm create is never called a child create.
- maintainability: each amendment is self-contained prose a future editor can read without the rearm-r6 review record; the provenance reading is stated where the field is defined, not only where it is read.
- observability: the Validation Commands block pins each amendment with a fail-closed gate (old text absent, new text present, operative sentinels present, occurrence counts pinned), so a revert, partial apply, find-replace clobber, or adjacent-text damage is caught mechanically.

**Done when:**
- all tasks checked; every Validation Commands line exits green on the amended tree; the insertion-scoped em-dash gate and the public hygiene scan pass; the origin item is routed done with its disposition folded into this plan's completion record.

**Ship when:**
- the next runtime skill-install sync carries the amended maintenance skill text to agent runtime installs (external, per-install sync; this repo's `agents/skills/` copy is the canonical source and lands with this plan).

## Review Scope

**Goal:** verify the amendments resolve origin F1/F2/F3 exactly, touch no other sentence, and leave every operative bound (delete-first ordering, zero-listings bounds, dispatch ladder path, schema-4 additive status) byte-unchanged.

**Files:**
- `agents/skills/maintenance/SKILL.md` (Task 1, Task 3)
- `agents/skills/maintenance/zcode.md` (Task 1 drift check, Task 2, Task 3)
- `docs/history/backlog/2026-09-25-rearm-form-field-writer-attribution.md` (Task 3)

**Documentation:**
- the backlog origin (reference during amendment; routed done in Task 3)
- the accepted residual that the child re-arm writes no form: the completed rearm-emission plan's Assumptions (`docs/plans/completed/2026-09-25-maintenance-rearm-emission-loop-prevention.md`)
- the r6 findings that staged this origin: `docs/reviews/2026-09-25-plan-review-maintenance-rearm-emission-loop-prevention-r6.md`

## Design Invariants

- CR: no operative bound text changes; the delete-first ordering, the zero-listings bounds, the dispatch ladder's operative path, and the field's additive schema-4 status are byte-preserved outside the pinned amendments (origin Non-goals); enforced mechanically by the sentinel presence gates, the sibling `cap-refused create` count and presence gates, and the pins suite.
- CR: the child re-arm duty must not become a form writer; F1's fix names the writers explicitly to prevent the misread, never to add a writer (the accepted rearm-r6 residual records the child re-arm writes no form); enforced mechanically by the pinned post-edit occurrence count of `child re-arm duty` plus the presence gate on the carry-forward replacement's writer attribution.

## Tasks

### Task 1: Attribute the form writers and pin the stale-form fallback in SKILL.md

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`

- [ ] Execution-start drift check, before any edit: assert every pinned pre-edit needle's exact count and abort for re-authoring on any mismatch. SKILL.md: `plus \`parent_automation_form\` (written by the same edits, so the rewrite must carry it)` = 1 (`rg -F -c`), `a null field, an unrecognized value, or an id adopted without a form` = 1, `rg -c 'child re-arm duty'` = 5, `a recorded recurring form or form-unknown keeps the delete at the cap-refused create` = 1. zcode.md: `its own lingered record must be deleted before a cap-refused create` = 1, `stays governed by the dispatch-discipline bounds` = 1, `form-unknown or a recorded recurring form keeps the delete at the cap-refused create` = 1, `A tripped precheck stands its lane down with zero listings performed` = 1, `a recorded recurring form or form-unknown keeps the delete at the cap-refused create` = 1. Record `BASE_SHA=$(git rev-parse HEAD)` for the Task 3 em-dash gate (if the variable is lost later, BASE_SHA is the parent of the first amendment commit) [class: REPOSITORY_TEST]
- [ ] In the Step 6 carry-forward list, replace the clause `plus \`parent_automation_form\` (written by the same edits, so the rewrite must carry it)` with `plus \`parent_automation_form\` (written outside Step 6 by the Turn-start carrier re-arm duty and by a rearm-on-touch session's arming edit, which record it beside the id; the child re-arm duty's targeted edit writes no form, so the rewrite must carry it)`; no other word of the carry-forward list changes [class: IMPLEMENTATION_REQUIRED]
- [ ] In the `parent_automation_form` field paragraph, extend the form-unknown enumeration `a null field, an unrecognized value, or an id adopted without a form` to `a null field, an unrecognized value, an id adopted without a form, or a recognized non-null form recorded beside a different id than the arming edit recorded, the stale-form case`, and append one sentence after the form-unknown sentence: `A form read is valid only beside the id the arming edit recorded; a stale form left by a non-form-writing id write such as the watchdog recovery re-arm or the child re-arm duty's targeted edit reads as form-unknown.`; keep the additive schema-4 note byte-unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: attribute parent_automation_form writers and pin the stale-form fallback` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Qualify the precheck create and record the asymmetry rationale in zcode.md

Files:
- `agents/skills/maintenance/zcode.md`

- [ ] In the Ladder precheck bullet's parenthetical, replace `its own lingered record must be deleted before a cap-refused create` with `its own lingered record must be deleted before a cap-refused child create`; the re-arm hygiene bullet's and the turn-start duty bullet's creates are the parent carrier re-arm create and stay byte-unchanged (they must not be called a child create); no other word of the bullet changes [class: IMPLEMENTATION_REQUIRED]
- [ ] Immediately after the clause `a listing after the mutations have executed stays governed by the dispatch-discipline bounds`, insert the parenthetical `(the two zero-listings exception lists are deliberately asymmetric subsets; the asymmetry is safe because the turn-start duty runs before any dispatch, so a listing it mandates as its decision input always precedes the turn's first mutation, and any later listing stays governed by the dispatch-discipline bounds whose exception list carries the dispatch-side entries)`; no operative bound wording changes [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: qualify the ladder precheck create and record the zero-listings asymmetry rationale` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Verify the amendments and route the origin done

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `docs/history/backlog/2026-09-25-rearm-form-field-writer-attribution.md`

- [ ] Run the amendment gates: `! rg -q 'written by the same edits' agents/skills/maintenance/SKILL.md` (old clause absent), `! rg -q 'deleted before a cap-refused create' agents/skills/maintenance/zcode.md` (unqualified precheck form absent), `rg -q 'written outside Step 6 by the Turn-start carrier re-arm duty and by a rearm-on-touch' agents/skills/maintenance/SKILL.md` (apostrophe-free gate prefix; the full pinned wording carries the possessive), `rg -q 'cap-refused child create' agents/skills/maintenance/zcode.md`, `rg -q 'a recognized non-null form recorded beside a different id' agents/skills/maintenance/SKILL.md`, `rg -q 'valid only beside the id the arming edit recorded' agents/skills/maintenance/SKILL.md`, `rg -q 'a stale form left by a non-form-writing id write' agents/skills/maintenance/SKILL.md`, `rg -q 'deliberately asymmetric subsets' agents/skills/maintenance/zcode.md`; all eight pass on the amended tree [class: REPOSITORY_TEST]
- [ ] Run the invariant gates: `[ "$(rg -o 'child re-arm duty' agents/skills/maintenance/SKILL.md | wc -l | tr -d ' ')" = 7 ]` (occurrence count: pre-edit 5 plus the two amended mentions, and no sentence attributes a form write to the child re-arm duty), `[ "$(rg -c 'cap-refused create' agents/skills/maintenance/zcode.md)" = 2 ]` (the sibling re-arm-create phrases survive the precheck edit), plus the sentinel presence gates `rg -F -q '(an additive field; schema version unchanged)' agents/skills/maintenance/SKILL.md`, `rg -F -q 'form-unknown or a recorded recurring form keeps the delete at the cap-refused create' agents/skills/maintenance/zcode.md`, `rg -F -q 'a recorded recurring form or form-unknown keeps the delete at the cap-refused create' agents/skills/maintenance/SKILL.md`, `rg -F -q 'A tripped precheck stands its lane down with zero listings performed' agents/skills/maintenance/zcode.md`, plus `bash scripts/check_maintenance_pins.sh` exit 0 [class: REPOSITORY_TEST]
- [ ] Route the origin done per fold-then-delete: fold the disposition into this plan's completion record, verify the deletion is ungated with `printf 'docs/history/backlog/2026-09-25-rearm-form-field-writer-attribution.md\n' | python3 scripts/doc_registry_validator.py --root . check-writes --stdin` exiting 0 (top-level backlog items are unregistered and not completed-history), then delete `docs/history/backlog/2026-09-25-rearm-form-field-writer-attribution.md`; Commit: `backlog: close rearm-form-field-writer-attribution origin (r6 F1/F2/F3 amended)` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the complete `## Validation Commands` block; verify `git diff --check` passes. Commit: `test: certify rearm form-field writer attribution` [class: REPOSITORY_TEST]

## Validation Commands

Fail-closed: every line must exit 0 (the two negated greps pin absence as the pass condition); a non-zero exit anywhere fails the block. Whole-`file` em-dash mode is known-red on these two files (seven pre-existing em-dash occurrences on five lines, all outside every amended span), so the em-dash gate runs insertion-scoped against `BASE_SHA`, recorded by Task 1's drift check before the first amendment commit (recovery: the parent of the first amendment commit); the hygiene line resolves the `{public_hygiene_scan_script}` facts key.

```
bash scripts/check_maintenance_pins.sh
[ "$(rg -o 'child re-arm duty' agents/skills/maintenance/SKILL.md | wc -l | tr -d ' ')" = 7 ]
[ "$(rg -c 'cap-refused create' agents/skills/maintenance/zcode.md)" = 2 ]
! rg -q 'written by the same edits' agents/skills/maintenance/SKILL.md
! rg -q 'deleted before a cap-refused create' agents/skills/maintenance/zcode.md
rg -q 'written outside Step 6 by the Turn-start carrier re-arm duty and by a rearm-on-touch' agents/skills/maintenance/SKILL.md
rg -q 'cap-refused child create' agents/skills/maintenance/zcode.md
rg -q 'a recognized non-null form recorded beside a different id' agents/skills/maintenance/SKILL.md
rg -q 'valid only beside the id the arming edit recorded' agents/skills/maintenance/SKILL.md
rg -q 'a stale form left by a non-form-writing id write' agents/skills/maintenance/SKILL.md
rg -q 'deliberately asymmetric subsets' agents/skills/maintenance/zcode.md
rg -F -q '(an additive field; schema version unchanged)' agents/skills/maintenance/SKILL.md
rg -F -q 'form-unknown or a recorded recurring form keeps the delete at the cap-refused create' agents/skills/maintenance/zcode.md
rg -F -q 'a recorded recurring form or form-unknown keeps the delete at the cap-refused create' agents/skills/maintenance/SKILL.md
rg -F -q 'A tripped precheck stands its lane down with zero listings performed' agents/skills/maintenance/zcode.md
bash scripts/check-no-em-dash.sh added-lines --base "$BASE_SHA"
python3 scripts/doc_registry_validator.py --root . validate
git diff --check
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
```

## Execution record

Executed 2026-09-25 (in-session, worktree branch 2026-09-25-rearm-form-attribution, commits 306a8564 + 7aea5198): Task 1 carry-forward writer attribution and stale-form enumeration + provenance reading landed in `agents/skills/maintenance/SKILL.md`; Task 2 `cap-refused child create` qualification and the zero-listings asymmetry rationale landed in `agents/skills/maintenance/zcode.md`. All eight amendment gates and all invariant/sentinel gates green; maintenance pins hold; insertion-scoped em-dash gate vs BASE_SHA 85388c62 green. Origin `docs/history/backlog/2026-09-25-rearm-form-field-writer-attribution.md` (rearm r6 F1/F2/F3) discharged by these amendments; disposition folded here per fold-then-delete, origin file deleted (deletion verified ungated via doc_registry_validator check-writes).
