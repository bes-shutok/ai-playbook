# Plan: Deferred residual dispositions

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-20-phase3-r1-polish-residuals.md`
- `docs/history/backlog/2026-09-21-r3-review-overflow-residuals.md`
- `docs/history/backlog/2026-09-21-lessons-gate-recovery-distinguish-duplicate-ids.md`

Driving force: code-quality + simplicity
Plan review record: the staging series docs/reviews/2026-09-27-plan-review-deferred-residual-dispositions-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Disposition every witnessed residual finding from the three promoted origin batches as an individual, verified fix in this repository (13 findings: 8 + 4 + 1; none is a recorded wontfix: each was re-verified live on 2026-09-27 against current code or prose).

- The added-lines gate stops reading a typo'd pathspec as CLEAN: an argument that matches no tracked file aborts non-zero with a named error, and the implemented `--base=REF` long form and `--` pathlist separator are documented and pinned.
- The learn/done blocked-learn recovery contract names the right remedy per validator category, so a duplicate lesson id no longer sends the operator through a no-op tagging command.
- The two runtime code paths that persist a blocked/parked claim and the two sites that inline the at-least-one-task-heading rule share one implementation each, so the mirrors cannot drift.
- The runtime contract and the maintenance skill prose state each claim once: the recovery-action literal the driver emits appears in the contract, the payload-copy consume duty covers every clearer and the Step 1 dispatched-copy consumer, and the attempt-bound and loop-mode rules are named once and referenced elsewhere.

## Origin dispositions

Every origin finding, dispositioned individually (per-finding probes recorded 2026-09-27 in this plan's exploration; "fix" tasks are in Tasks 1-9):

| # | Origin finding | Disposition | Where |
|---|---|---|---|
| F1 | added-lines typo'd pathspec reads CLEAN (probe: exit 0, no output) | fix: fail-closed abort on a paths argument matching no tracked file | Task 1 |
| F2 | "No negative arm rejects an unknown claim state" is partially stale: the guard exists (`unknown claim state` ValueError, claim-state membership check in `RuntimeDriver.validate_manifest`); no test pins it | fix (narrowed): add the junk-state rejection witness test | Task 3 |
| F3 | `_park_waiting_capacity_locked` active-park branch re-implements `_apply_blocked`'s task-persist block + worker-blocked history append verbatim | fix: parameterize the shared blocked-persist tail with the claim state | Task 4 |
| F4 | at-least-one-task-heading predicate inlined at two mirror sites (terminal gate, readiness plan-shape guard) | fix: extract one shared predicate; keep both evidence strings | Task 5 |
| F5 | envelope-level paragraph flush-left terminates the `recovery` decision bullet list (verified at the "One envelope-level outcome sits outside..." paragraph; region drifted from the finding's :792 anchor) | fix: re-indent the paragraph into the list | Task 6 |
| F6 | `--base=REF` long form and `--` separator implemented, absent from usage text and tests; "the plan" in the finding names completed history | fix: usage text + pins; the completed plan is immutable history, no edit (disposition reason recorded here) | Task 1 |
| F7 | driver-emitted `resume-same-claim` literal absent from the contract (grep: 0 hits; capacity paragraph paraphrases only) | fix: name the literal in the capacity paragraph | Task 6 |
| F8 | bounded-read missing-file refusal fragment gained a `: {exc}` suffix; helper docstring numbering note is half-true. Fold target `docs/history/backlog/rejected/2026-09-20-bounded-read-pin-hardening.md` is REJECTED (2026-09-26 direction triage), so the disposition is absorbed here | fix: align the docstring sentence; sanction the suffix explicitly | Task 7 |
| T1 | keyed-copy consume duty bound to the Step 1 reader only; other clearers carry no copy-deletion duty; dispatched copies have no consumer | fix: copy-deletion duty on every clearer; consume step in the Step 1 dispatch path. Excluded with reason: the child blueprints' park-first consume paths (prompt-templates.md successor/discharge duties) stay unwired: the origin's candidate fix prescribes the Step 1 dispatch path as the consumer, and the child-side paths are beyond it | Task 8 |
| T2 | zcode recipe content span ("names the lane the mode excludes") disagrees with the pinned literal (names the lane the mode keeps); literal does not pin `<directive>` normalization | fix: reword the span to defer to the literal; state trim + single-line normalization | Task 9 |
| T3 | attempt-bound predicate restated at four operative sites | fix: one named predicate (the live-bound condition), other sites reference it | Task 9 |
| T4 | loop-mode exclusion stated three times in the Pending dispatch bullet plus Step 3 plus the successor condition | fix: name the exclusion once (the Step 3 loop-mode exclusion), reference it; the successor-condition restatement lives in `agents/skills/maintenance/prompt-templates.md` (the successor-dispatch duty paragraph's chain-nothing condition), not in SKILL.md | Task 9 |
| R1 | recovery remedy presents `--tag-unclassified` as the fix for duplicate ids, where it is a no-op (witnessed: `0 lessons rewritten`) | fix: branch the recovery contract on validator category; operator-driven, never auto-renumber | Task 2 |

## Terms

- **added-lines mode**: `scripts/check-no-em-dash.sh added-lines [--base REF] [paths...]` scans git-diff added lines (default base HEAD) for em dashes; git exit >= 2 aborts non-zero, never reading as clean.
- **Keyed copy / pairing rule**: a `pending_rearm` (or parked-dispatch) intent record paired with its assembled payload copy under `docs/tmp/future-plan-prompts-<date>[-rearm|-dispatch-<basename>].md`; **consume-after-survival** = the consumer deletes the intent's own keyed copy only after the intent-clearing state edit has survived.
- **Live-bound condition**: the Step 0 consultation's attempt-bound predicate: a `rearm_note` whose structured first line names the same defect token and parent automation id, recorded within the last cadence period; it suppresses only the mutating repair for that touch.
- **Loop-mode exclusion**: the standing `loop_mode` field excludes target kinds from dispatch; an excluded retained target is parked with reason `loop-mode-held` and re-dispatched when the mode lifts.
- **Validator categories**: `scripts/lessons_index.py` classifies each lesson failure as exactly one of `duplicate`, `untagged`, `multiple-tags`, `invalid-family` (precedence in that order).
- **Pins suite**: `scripts/check_maintenance_pins.sh`, exit 0 = all maintenance-skill pins hold; it pins exact prose spans this plan rewords, so moved spans update their pins in the same task.

## Assumptions

- assume the three origin files are the scope of record and their findings are all in scope; basis: the authoring dispatch names them as origins.
- assume F1's remedy is fail-closed abort (not warn): a typo'd pathspec is the same false-clean class the script's own abort rule names ("git failures abort non-zero instead of reading as clean"), so a silent warn would keep the CLEAN misread the finding witnessed; basis: the script's usage text abort philosophy plus the origin's candidate fix, accepted per the dispatch's standing pre-authorization.
- assume F2's deliverable is the missing test witness only; basis: 2026-09-27 probe of `RuntimeDriver.validate_manifest` (claim-state membership rejection present in the source).
- assume F8 is dispositioned in this plan, not folded into the named backlog item; basis: that item sits under `docs/history/backlog/rejected/` (rejected 2026-09-26), and completed-history/rejected placement is immutable context.
- assume F6's "the plan" reference needs no edit; basis: the referenced document is a completed history artifact (immutable; doc-hierarchy document states).
- assume maintenance-prose tasks may move pin spans and therefore update `scripts/check_maintenance_pins.sh` in the same task; basis: the pins suite pins the exact spans being reworded, and its header declares span pins as its mechanism.
- assume wording consolidation (T3, T4) never edits the maintenance revision-ledger entries: the ledger is history, not operative sites; basis: the ledger lines describe past rounds and are excluded from the origin finding's operative-site count.
- assume `scripts/rearm_on_touch.py` needs no change: T1-T4 alter prose ownership and consume duties, not the classification semantics the script mirrors; basis: the script mirrors the state-first classification and bookkeeping edits, none of which change.
- assume the pins suite's single baseline failure is pre-existing and exempt: `bash scripts/check_maintenance_pins.sh` exits 1 at committed HEAD (012dd94e, tree clean) with exactly `PIN FAIL: live-vs-archive basename twin: docs/history/plans/2026-09-26-release-skill.md also archived at docs/history/plans/completed/2026-09-26-release-skill.md`, measured 2026-09-27; basis: the failing pin is a basename-twin check over docs/history/plans/ artifacts, not a span pin over a reworded span, and docs/history/** is immutable context in this plan's scope model. The repair is out of scope here and tracked as `docs/history/backlog/2026-09-27-release-skill-plan-live-twin.md`; every pins arm in this plan fails on any NEW pin break while tolerating exactly that named line.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: thirteen witnessed residuals become thirteen individual verified fixes: the added-lines gate stops reading a typo'd pathspec as CLEAN and the recovery contract branches on validator category (behavior first), then the duplicated persist/heading code paths, the contract drift, and the four maintenance-wording themes collapse to single owned sources, because claim-versus-behavior divergence is cheapest to close while it is still witnessed (code-quality + simplicity).

Concretely today: `bash scripts/check-no-em-dash.sh added-lines --base HEAD does-not-exist.md` exits 0 (CLEAN): the false pass the gate exists to prevent. A duplicate `UL#N` sends the operator to `lessons.py adopt --tag-unclassified`, which rewrites nothing. Two code sites spell the same blocked-persist mutation; four prose sites spell the same attempt-bound rule. After execution each claim has exactly one owned source, and the gate refuses the typo instead of blessing it.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every dispositioned behavior fix has a discriminating witness that fails on current code or pins the new contract (per-task test items below); no disposition rests on the origin text's assertion alone.
- consistency: after Tasks 6-9, each consolidated rule (resume-same-claim documentation, copy-deletion duty, live-bound condition, loop-mode exclusion, appendix literal) has exactly one operative source; per-file greps prove it.
- maintainability: F3/F4 refactors leave the existing runtime suite green with no behavior change; the shared implementations are the only remaining copies.
- regression safety: the full existing suites named in Validation Commands exit 0 after every task that touches their subject.

**Done when:**
- All Tasks 1-9 checklist items are checked with their commands run to the stated expectation.
- `bash scripts/check_maintenance_pins.sh` exits 0, or fails only on the single named pre-existing baseline twin recorded in Assumptions (any other pin failure blocks).
- Both new test files and every extended test pass from the scripts directory invocation form.
- The three origin files' witnessed subjects each show the fixed behavior under the Validation Commands probes: `docs/history/backlog/2026-09-20-phase3-r1-polish-residuals.md` via the F1 probe pair, the usage greps, the F7 contract grep, and the runtime suite; `docs/history/backlog/2026-09-21-r3-review-overflow-residuals.md` via the T2 greps, the T3/T4 single-source greps, the Task 8 consume-duty greps, and the runtime suite; `docs/history/backlog/2026-09-21-lessons-gate-recovery-distinguish-duplicate-ids.md` via the recovery-contract suite.

**Ship when:**
- Nothing; the work is entirely in-repository (no deploy, external team, or human-owned gate).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check-no-em-dash.sh` *(usage text + added-lines pathspec guard only; all other commands in this file are frozen)*
- `scripts/execute_plan_runtime.py` *(only `RuntimeDriver.validate_manifest` claim-state span is read, `_apply_blocked`, `_park_waiting_capacity_locked`, the two at-least-one-task-heading sites, and `_read_plan_bounded`'s docstring numbering sentence; all other methods are frozen)*
- `agents/skills/execute-plan/runtime-contract.md` *(only the recovery-decision bullet-list region and the capacity paragraph; all other sections are frozen)*
- `agents/skills/learn/SKILL.md` *(only the blocked-index recovery recipe span)*
- `agents/skills/done/SKILL.md` *(only the Step 1 learn-blocked recovery span)*
- `agents/skills/maintenance/SKILL.md` *(only the `pending_rearm` field paragraph's Clearers sentence, the Step 1 Pending re-arm bullet, the Pending dispatch bullet's three clauses, the Step 3 loop-mode enforcement sentence, the Step 0 consultation's attempt-bound clause (the live-bound condition's definition home), the self-heal arm's attempt-bound restatement, the structured-first-line sentence, and the `rearm_note` field paragraph's bound restatement; the revision-ledger entries and everything else are frozen)*
- `agents/skills/maintenance/prompt-templates.md` *(only the successor-dispatch duty paragraph's chain-nothing loop-mode condition)*
- `agents/skills/maintenance/zcode.md` *(only the Mode appendix bullet)*
- `scripts/check_maintenance_pins.sh` *(only pins over spans the tasks reword)*

**Tests:**
- `scripts/test_check_no_em_dash.py` *(new)*
- `scripts/test_lessons_recovery_contract.py` *(new)*
- `scripts/test_execute_plan_runtime.py` *(only additions: the junk-state witness test; everything else frozen)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/rearm_on_touch.py`; reason: mirrors classification semantics this plan does not change (see Assumptions).
- `docs/history/**` completed plans and `docs/history/backlog/rejected/**`; reason: immutable history context; dispositions that would edit them are recorded in Origin dispositions instead.
- The live-vs-archive plan-twin repair (`docs/history/plans/2026-09-26-release-skill.md` also archived under `completed/`); reason: pre-existing baseline defect outside this plan's scope model, tracked by `docs/history/backlog/2026-09-27-release-skill-plan-live-twin.md`.
- `docs/reviews/**` staging artifacts; reason: review records, not deliverables.

## Validation Commands

```bash
# Rule 10 fail-closed block: every required check aborts non-zero on miss.
set -u
fail=0

# Task 1: added-lines hermetic arms (new suite).
( cd scripts && python3 -m unittest test_check_no_em_dash -v ) || { echo "FAIL: added-lines suite"; fail=1; }

# Tasks 2-5, 7: runtime + recovery-contract suites.
( cd scripts && python3 -m unittest test_lessons_recovery_contract -v ) || { echo "FAIL: recovery-contract suite"; fail=1; }
( cd scripts && python3 -m unittest test_execute_plan_runtime.ExecutePlanRuntimeTest.test_validate_manifest_rejects_unknown_claim_state -v ) || { echo "FAIL: junk-state witness"; fail=1; }
( cd scripts && python3 -m unittest test_execute_plan_runtime ) || { echo "FAIL: runtime suite regression"; fail=1; }

# F1 probe: a typo'd pathspec must abort non-zero (inside a scratch git repo is fine; here the repo itself).
if bash scripts/check-no-em-dash.sh added-lines --base HEAD docs/no-such-typo-path.md; then echo "FAIL: unmatched pathspec still reads CLEAN"; fail=1; fi
# F1 companion: a real tracked path with no diff still exits 0.
if ! bash scripts/check-no-em-dash.sh added-lines --base HEAD README.md; then echo "FAIL: matched path false-aborts"; fail=1; fi

# F6: usage text documents both implemented forms (per-file dedicated greps).
grep -q -- "--base=REF" scripts/check-no-em-dash.sh || { echo "FAIL: usage lacks --base=REF"; fail=1; }
grep -qE '(^\s+--\s|\[--\])' scripts/check-no-em-dash.sh || { echo "FAIL: usage lacks the -- separator documentation"; fail=1; }

# F7: the driver literal is documented in the contract, exactly once.
if [ "$(grep -cF 'resume-same-claim' agents/skills/execute-plan/runtime-contract.md)" -ne 1 ]; then echo "FAIL: resume-same-claim literal not documented exactly once"; fail=1; fi

# T2: the disagreeing span is gone from the recipe; the normalization is stated.
if grep -qF 'naming the lane the mode excludes' agents/skills/maintenance/zcode.md; then echo "FAIL: stale excludes-span still present"; fail=1; fi
grep -qF 'single line' agents/skills/maintenance/zcode.md || { echo "FAIL: <directive> normalization not stated"; fail=1; }

# T3/T4 single-source proof: the restated spans are gone and each rule is owned by exactly one site.
if [ "$(grep -cF 'carrying a live bound' agents/skills/maintenance/SKILL.md)" -ne 1 ]; then echo "FAIL: live-bound predicate restated beyond its definition site"; fail=1; fi
if grep -qF 'mirroring the Step 0 precedence wording' agents/skills/maintenance/SKILL.md; then echo "FAIL: Step 1 reader mirror still restates the live-bound clause"; fail=1; fi
if grep -qF 'a `rearm_note` for the same repair shape' agents/skills/maintenance/SKILL.md; then echo "FAIL: self-heal arm tail still restates the bound predicate"; fail=1; fi
if [ "$(grep -cF 'retained in `pending_dispatch` with reason `loop-mode-held`' agents/skills/maintenance/SKILL.md)" -ne 1 ]; then echo "FAIL: loop-mode retention clause not owned by exactly one site"; fail=1; fi
if [ "$(grep -cF 'the Step 3 loop-mode exclusion' agents/skills/maintenance/SKILL.md)" -lt 2 ]; then echo "FAIL: named loop-mode exclusion not defined plus referenced in SKILL.md"; fail=1; fi
grep -qF 'the Step 3 loop-mode exclusion' agents/skills/maintenance/prompt-templates.md || { echo "FAIL: successor condition not reduced to the named exclusion"; fail=1; }

# T1: the new consume duties landed (presence) and the old Clearers tail is gone (negated).
grep -qF "deletes the intent's own keyed copy per consume-after-survival" agents/skills/maintenance/SKILL.md || { echo "FAIL: per-clearer copy-deletion duty missing"; fail=1; }
grep -qF "deletes the dispatched intent's keyed copy" agents/skills/maintenance/SKILL.md || { echo "FAIL: Step 1 dispatched-copy consume step missing"; fail=1; }
if grep -qF 'never leaves a stale intent behind.' agents/skills/maintenance/SKILL.md; then echo "FAIL: old Clearers tail still present"; fail=1; fi

# R1: the duplicate remedy no longer presents the tagging command as the fix.
python3 - <<'PY' || { echo "FAIL: recovery-contract grep arms"; fail=1; }
import pathlib, sys
learn = pathlib.Path("agents/skills/learn/SKILL.md").read_text(encoding="utf-8")
done_ = pathlib.Path("agents/skills/done/SKILL.md").read_text(encoding="utf-8")
for name, text in (("learn", learn), ("done", done_)):
    if "duplicate" not in text or "multiple-tags" not in text:
        print(f"{name}: recovery contract lacks per-category branches"); sys.exit(1)
PY

# Maintenance pins: fail on any NEW pin break; tolerate exactly the recorded baseline twin (see Assumptions).
PINS_OUT="$(bash scripts/check_maintenance_pins.sh 2>&1)"; PINS_RC=$?
if [ "$PINS_RC" -ne 0 ]; then
  printf '%s\n' "$PINS_OUT" | grep -F 'PIN FAIL: live-vs-archive basename twin: docs/history/plans/2026-09-26-release-skill.md' >/dev/null || { echo "FAIL: pins failed without the exempt baseline line"; printf '%s\n' "$PINS_OUT"; fail=1; }
  if printf '%s\n' "$PINS_OUT" | grep '^PIN FAIL:' | grep -vF 'PIN FAIL: live-vs-archive basename twin: docs/history/plans/2026-09-26-release-skill.md' | grep -q '.'; then echo "FAIL: pin breaks beyond the recorded baseline exemption"; printf '%s\n' "$PINS_OUT"; fail=1; fi
fi

exit "$fail"
```

### Task 1: added-lines fails closed on an unmatched pathspec; usage text documents both implemented forms (F1, F6)

Files:
- `scripts/check-no-em-dash.sh`
- `scripts/test_check_no_em_dash.py` *(new)*

- [x] `AddedLinesModeTest#test_unmatched_pathspec_aborts_non_zero`; given a temp git repo with one tracked file and `added-lines --base HEAD does-not-exist.md`, expects a non-zero exit and a stderr message naming the unmatched pathspec, never exit 0. [class: REPOSITORY_TEST]
- [x] `AddedLinesModeTest#test_matched_path_with_no_diff_exits_zero`; given a tracked, unchanged file, expects exit 0 (the new guard must not false-abort a legitimate pathspec). [class: REPOSITORY_TEST]
- [x] `AddedLinesModeTest#test_untracked_pathspec_aborts_non_zero`; given a real but never-tracked file in the temp repo, expects exit 2 with the unmatched-pathspec message (pins that aborting on untracked paths is intended: the mode cannot scan them, and this must not later be "fixed" back to a warn-and-continue fail-open). [class: REPOSITORY_TEST]
- [x] `AddedLinesModeTest#test_added_em_dash_line_reported`; given a tracked file gaining one em dash line versus the base commit, expects exit 1 and a `file:new-line:` report line (regression pin of the mode's core behavior). [class: REPOSITORY_TEST]
- [x] `AddedLinesModeTest#test_long_form_base_and_separator_accepted`; given `--base=HEAD <path>` and `--base HEAD -- <path>` invocations over the same fixture, expects both to match the short-form result. [class: REPOSITORY_TEST]
- [x] `UsageTextTest#test_usage_documents_long_form_and_separator`; given the script's usage text, expects it to contain `--base=REF` and a documented `--` pathlist separator row. [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd scripts && python3 -m unittest test_check_no_em_dash.AddedLinesModeTest.test_unmatched_pathspec_aborts_non_zero -v )` (current code exits 0 on the unmatched pathspec) [class: REPOSITORY_TEST]
- [x] Implement: in the added-lines argument handling, after parsing, for each entry in `paths` verify at least one tracked file matches (`git ls-files -- <entry>` non-empty); on no match print `check-no-em-dash: pathspec matches no tracked file: <entry>` to stderr and exit 2 (mirrors the git-abort exit class). Preserve every existing exit path. [class: IMPLEMENTATION_REQUIRED]
- [x] Update `usage()` so the added-lines row reads `added-lines [--base REF] [--base=REF] [--] [paths...]` with one sentence for the separator and one sentence stating that a paths argument matching no tracked file, including untracked files, aborts non-zero because the mode cannot scan it. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_check_no_em_dash -v )` [class: REPOSITORY_TEST]
- [x] Run the Validation Commands F1 probe block → expect the abort/companion pair to hold. [class: REPOSITORY_TEST]
- [x] Commit: `em-dash: added-lines fails closed on unmatched pathspec, usage documents both base forms` [class: IMPLEMENTATION_REQUIRED]

### Task 2: recovery contract branches on validator category (R1)

Files:
- `agents/skills/learn/SKILL.md`
- `agents/skills/done/SKILL.md`
- `scripts/test_lessons_recovery_contract.py` *(new)*

- [x] `ValidatorCategoryTest#test_category_taxonomy_matches_validator`; given `scripts/lessons_index.py`, expects the four category literals `duplicate`, `untagged`, `multiple-tags`, `invalid-family` and their documented precedence order to be present (pins the taxonomy the contract branches on). [class: REPOSITORY_TEST]
- [x] `RecoveryContractTest#test_learn_recovery_branches_on_category`; given the learn skill's blocked-index recovery recipe text, expects per-category remedies: `untagged`/`invalid-family` → the tagging/adoption workflow; `duplicate` → inspect the colliding headings, choose a unique identifier, update same-corpus references, rerun the validator; `multiple-tags` → remove the competing family tags after classifying the lesson. [class: REPOSITORY_TEST]
- [x] `RecoveryContractTest#test_done_recovery_branches_on_category`; given the done skill's Step 1 learn-blocked recovery text, expects the same three-way branch. [class: REPOSITORY_TEST]
- [x] `RecoveryContractTest#test_duplicate_remedy_omits_tagging_command`; given both recovery texts' duplicate-branch spans, expects the span to not contain `--tag-unclassified` (zero-match assertion, negated in the test). [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd scripts && python3 -m unittest test_lessons_recovery_contract -v )` (today neither text branches) [class: REPOSITORY_TEST]
- [x] Rewrite the learn recovery recipe span and the done Step 1 recovery span to the branched wording; keep recovery operator-driven: the contract never renumbers lessons or rewrites cross-references itself, and the tagging command is never presented as a duplicate remedy. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_lessons_recovery_contract -v )` [class: REPOSITORY_TEST]
- [x] Commit: `learn: recovery contract branches on validator category (duplicate is not a tagging case)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: junk-state rejection witness through validate_manifest (F2, narrowed)

Files:
- `scripts/test_execute_plan_runtime.py`

- [x] `ExecutePlanRuntimeTest#test_validate_manifest_rejects_unknown_claim_state`; given a seeded valid manifest whose claim `state` is `junk-state`, expects `ValueError` naming `unknown claim state` from `RuntimeDriver.validate_manifest`, and given a task `status` of `junk-state`, expects `ValueError` naming `unknown task status` (both closed-set rejections pinned; the guard itself pre-exists and is not modified). [class: REPOSITORY_TEST]
- [x] Run → expect GREEN at add (pin, not behavior change): `( cd scripts && python3 -m unittest test_execute_plan_runtime.ExecutePlanRuntimeTest.test_validate_manifest_rejects_unknown_claim_state -v )` [class: REPOSITORY_TEST]
- [x] Commit: `runtime: pin junk claim/task state rejection through validate_manifest` [class: IMPLEMENTATION_REQUIRED]

### Task 4: one shared blocked-persist tail for blocked and parked claims (F3)

Files:
- `scripts/execute_plan_runtime.py`

- [x] Parameterize `_apply_blocked` with a claim-state keyword constrained to exactly `blocked` (the default, preserving today's shape) or `waiting-capacity`, pinned by a module-level constant pair or an assertion inside `_apply_blocked` so the shared tail cannot become a generic claim-state writer for states its lease semantics do not cover; have `_park_waiting_capacity_locked`'s active-park branch call it instead of re-implementing the task-persist block and worker-blocked history append. The park's `retry_policy` write stays at the call site, the `recovery_action` assignment precedes the shared-tail call (the persisted blocked_receipt keeps the literal), and `_save` still happens once per path. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN, no behavior change: `( cd scripts && python3 -m unittest test_execute_plan_runtime -k capacity )` then the full `( cd scripts && python3 -m unittest test_execute_plan_runtime )` (the existing waiting-capacity durable-state tests are the behavioral witnesses; add none). [class: REPOSITORY_TEST]
- [x] Commit: `runtime: parameterize the shared blocked-persist tail with the claim state` [class: IMPLEMENTATION_REQUIRED]

### Task 5: one at-least-one-task-heading predicate for both gates (F4)

Files:
- `scripts/execute_plan_runtime.py`

- [x] Extract the inlined at-least-one-task-heading rule (the readiness plan-shape guard and the terminal gate's vacuous-scan requirement) into one shared predicate over `_TASK_SECTION_HEADING` matches; both sites call it and keep their own distinct evidence strings; no message text changes. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime )` (both gates' zero-heading rejection is covered by existing tests; add none). [class: REPOSITORY_TEST]
- [x] Commit: `runtime: share the at-least-one-task-heading predicate across both gates` [class: IMPLEMENTATION_REQUIRED]

### Task 6: contract matches the code (F5, F7)

Files:
- `agents/skills/execute-plan/runtime-contract.md`

- [x] Re-indent the "One envelope-level outcome sits outside that failed-condition enumeration:" paragraph and its continuation lines to the two-space list level so the `recovery` decision bullet list is no longer terminated mid-section (the `- direct-continuation` bullet follows it in the same list). [class: IMPLEMENTATION_REQUIRED]
- [x] In the capacity paragraph, name the literal the driver emits: the parked-claim recovery action is `resume-same-claim` (the exact value carried in the receipt's `recovery_action` field), keeping the existing in-place-resume prose as the explanation. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Validation Commands F7 grep (exactly one `resume-same-claim` hit) and a two-space indent check over the re-indented paragraph (`grep -n '^One envelope-level outcome' agents/skills/execute-plan/runtime-contract.md` must report no flush-left hit). [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: contract re-indents recovery list, documents resume-same-claim` [class: IMPLEMENTATION_REQUIRED]

### Task 7: bounded-read docstring says the true numbering story; suffix sanctioned (F8)

Files:
- `scripts/execute_plan_runtime.py`

- [x] Replace `_read_plan_bounded`'s docstring sentence claiming leading or trailing blank lines shift no interior number with the accurate statement: the text is stripped once here, every consumer numbers lines from the stripped form, so a leading blank region shifts every subsequent line's reported number down while relative order and spacing are preserved. [class: IMPLEMENTATION_REQUIRED]
- [x] Sanction the refusal fragment's `: {exc}` suffix explicitly in the plan of record (this task's check item is the sanction): the fragment is `is missing or unreadable: {plan_path}: {exc}` and stays as-is; existing tests pin the stable substring. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd scripts && python3 -m unittest test_execute_plan_runtime )`. [class: REPOSITORY_TEST]
- [x] Commit: `runtime: correct the bounded-read docstring numbering note` [class: IMPLEMENTATION_REQUIRED]

### Task 8: payload-copy consume duty for every clearer and a consumer for dispatched copies (T1)

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh` *(only if a pin over the edited span moves)*

- [x] Extend the `pending_rearm` field paragraph's Clearers sentence so every clearer (the writing duty's same-session success, the Step 0 recipe re-arm, the Step 1 memory-note re-arm path, the watchdog recovery re-arm) carries the same copy-deletion duty as the Step 1 reader: the sentence states each clearer "deletes the intent's own keyed copy per consume-after-survival" once the clearing edit has survived, and a missing copy never blocks the clear; the old tail "never leaves a stale intent behind." is removed. [class: IMPLEMENTATION_REQUIRED]
- [x] Give dispatched `pending_dispatch` copies a consume step in the Step 1 dispatch path: when the retained target's dispatch succeeds, the dispatching turn "deletes the dispatched intent's keyed copy" per consume-after-survival, mirroring the reader's re-arm consume. [class: IMPLEMENTATION_REQUIRED]
- [x] Check → expect GREEN: the Validation Commands T1 grep pair (two presence greps on the new duty spans, one negated grep on the old tail). [class: REPOSITORY_TEST]
- [x] Sweep `scripts/check_maintenance_pins.sh` for pins over the edited spans; update any moved span in this task (the watchdog pairing pin's span is expected to survive unchanged). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN or only the recorded baseline-twin failure: `bash scripts/check_maintenance_pins.sh`. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: payload-copy consume duty on every clearer and dispatched copies` [class: IMPLEMENTATION_REQUIRED]

### Task 9: maintenance prose states each rule once (T2, T3, T4)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md` *(only the successor-dispatch duty paragraph's chain-nothing condition)*
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh` *(only pins over reworded spans)*

- [x] T2: reword the zcode Mode appendix bullet's content span to defer to the pinned literal (the paragraph names the lane the mode keeps, per the literal `Mode directive: <directive> (<mode> lane only.)`), and state the substitution normalization in the literal's sentence: `<directive>` is trimmed and collapsed to a single line. [class: IMPLEMENTATION_REQUIRED]
- [x] T3: name the attempt-bound predicate once at the Step 0 consultation (the live-bound condition, Terms above); reduce the other four operative restatements to references that keep only what each site additionally reads: the Step 1 reader's precedence mirror drops the restated clause "mirroring the Step 0 precedence wording", the self-heal arm tail drops the restated parenthetical "a `rearm_note` for the same repair shape", and the structured-first-line sentence and the `rearm_note` field paragraph's bound sentence each reduce to the named reference; the suppression scope (only the mutating repair, never the mandated listing) is stated at the named definition. [class: IMPLEMENTATION_REQUIRED]
- [x] T4: name the loop-mode exclusion once (the Step 3 loop-mode enforcement sentence owns it); reduce the Pending dispatch bullet's gate, dispatch, and tail clauses to references carrying the `loop-mode-held` retention semantics by name, and reduce the successor condition's restatement in `agents/skills/maintenance/prompt-templates.md` (the successor-dispatch duty paragraph's chain-nothing condition) to the same named exclusion. [class: IMPLEMENTATION_REQUIRED]
- [x] Update any pin whose pinned span a reword moves: the `loop-mode-held` retention span is expected to move (keep it pinned at the clause that still carries the retention wording verbatim); the zcode appendix wording-span pin is expected to move with T2; the successor chain-nothing pin (`is a non-dual mode excluding the execution lane`, region-scoped to the successor paragraph) is expected to move, re-anchoring on the named-exclusion reference in the successor paragraph; the Step 0 attempt-bound span pin (`suppresses the repair for that touch`) may move with the arm-tail reduction. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN or only the recorded baseline-twin failure: `bash scripts/check_maintenance_pins.sh` and the Validation Commands T2/T3/T4 greps. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: name the attempt-bound and loop-mode rules once, defer the appendix wording to its literal` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/completed/2026-09-20-phase3-r1-polish-residuals.md`: executed by this plan (declared origin); folded by the 2026-10-02 done-corpus backfill sweep (docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md); former backlog file deleted, body recoverable via git history.
- `docs/history/backlog/completed/2026-09-21-lessons-gate-recovery-distinguish-duplicate-ids.md`: executed by this plan (declared origin); folded by the 2026-10-02 done-corpus backfill sweep (docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md); former backlog file deleted, body recoverable via git history.
- `docs/history/backlog/completed/2026-09-21-r3-review-overflow-residuals.md`: executed by this plan (declared origin); folded by the 2026-10-02 done-corpus backfill sweep (docs/history/plans/2026-10-01-done-origin-fold-delete-enforcement.md); former backlog file deleted, body recoverable via git history.
