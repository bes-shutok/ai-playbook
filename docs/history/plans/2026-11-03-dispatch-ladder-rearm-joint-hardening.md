# Plan: Activate the Launchd Clock-Order Chain as the Bound-Session Re-Arm and Dispatch Default

Authoring claim: 2026-11-03-dispatch-ladder-rearm-first-action-joint.md (session sess_e1107706-f404-4674-8091-83f98b98d0bd)

Backlog origin: docs/history/backlog/2026-11-03-dispatch-ladder-rearm-first-action-joint.md
Driving force: simplicity (primary; activation retires the conditional promotion gate and its default-in-waiting framing, leaving one named default and one documented fallback instead of a two-stage demotion), efficiency (secondary; each emission-suppression incident costs a stand-down cycle plus an out-of-band re-derivation that the chained default avoids, witnessed four times on 2026-11-03)
Plan review record: the staging series .ai-playbook/reviews/2026-11-03-plan-review-dispatch-ladder-rearm-joint-hardening-p1d965793-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h

## Terms

- emission suppression: the loop's decided-call-unsent form; a session records a mutating automation primitive decision, narrates it, and emits repeated read-only listings instead (lesson 59's class; the stand-down guard that catches it stays).
- automation-born create cap: the platform refusal binding a session that spawned or created an automation record; the binding survives the record's completion until the record is deleted, so a lingered completed spawner keeps its session's `CronCreate` refused.
- delete-own-spawner leg: the sanctioned cap lift; a session deletes its own lingered spawner record by id before creating. Its mechanics are unchanged by this plan; its entry condition gains the chained-path skip (Task 2).
- launchd clocked-order chain: `scripts/execute_plan_runtime.py --operation clocked-order-schedule`; the unbound launchd one-shot carrier family with keyed per-order identity, arming proof (the armed fire epoch read back and required to equal the requested epoch), env-complete headless job script, ledger discharge events, the missed-order due detector, and payload copies under `.ai-playbook/maintenance/clocked-order-payloads/`; the clocked-orders ledger is the chain carrier's registry of record.
- silent strand (the discharge-verification gap): a launchd carrier fires and its payload session never records itself (dies before its first write or never launches), the ledger reads healthy `discharged`, and the turn is lost with zero residue; first witness docs/history/plans/completed/2026-10-17-rearm-dispatch-ladder-incident-guards.md Task 3's gate row, second witness docs/history/backlog/completed/2026-10-18-clocked-order-discharged-order-silent-strand.md.
- clocked-order discharge-verification gap row: the disposed backlog row (living path removed with the covered stub, no completed twin) that gated this activation; its durable home is the covering plan's completed twin docs/history/plans/completed/2026-10-17-rearm-dispatch-ladder-incident-guards.md, and its durable trail is the two silent-strand witnesses above and this plan's disposition sentence.
- verify-successor arm: the warning-only read-only consult leg (`clocked-order-verify-successor` in `scripts/execute_plan_resume_watcher.py`, the survey consult bullet in `agents/skills/maintenance/survey-arms.md`, the overlay stall sentence) that flags a discharged order past a grace window with no attributable successor; machinery registry rows `duty:clocked-order-verify-successor` (admission + pre-registered removals). Its consumers are live maintenance survey turns, so it verifies wiring and records flags only when a survey turn runs; this plan treats it as a wiring control, not a proof of detection capability.
- promotion review: the review named by the completed 2026-10-17 guard plan Task 3 that gates the chain's takeover as the operative default; the same review is where the verify-successor arm's pre-registered promotion decision rides.
- operative default vs documented fallback: the default a bound session runs unless a named guard refuses, versus a path kept behind both guard rule sets (the ownership allowlist and the post-delete probe with the distinct-failure rollback) and taken first when the default's mechanism refuses.
- `pending_rearm`: the scheduler-state park holding an unexecuted re-arm intent paired with its payload copy; the backstop this plan leaves unchanged.
- Step 0 discharge precedence: the standing rule that a primitive-capable turn discharges parked re-arm records at its opening boundary; the named discharger for the park path.
- reduced-toolset terminal: the dispatch ladder's park rung for a session whose automation toolset lacks the mutation primitives; unchanged.
- D-3, D-4, D-11: the operator's fixed carrier cadences (daily 11:00 scheduler carrier; 05:49 and 01:53 authoring carriers) recorded in docs/maintenance/operator-directives.md; this plan changes the carrier mechanism a bound session uses between fires, never their slot semantics.

## Why

The dispatch ladder's re-arm and child-dispatch recipes require an automation-born session to emit a mutating automation primitive as its first action, and that joint failed four times on 2026-11-03 alone: the 00:57 stand-down (4 listings, 0 mutations, operator touch recovered it), the ~10:03 suppressed spawner delete (the scheduler parent stayed dark), the ~10:05 suppressed parent re-arm create (the 02:00 analysis parent stayed dark; the park carried the intent), and the 18:16-18:19Z suppressed D-3 create in this plan's own authoring carrier session (4 listings, 0 mutations, stand-down recorded 18:19Z; the re-arm was satisfied out-of-band through the launchd chain with its arming proof passed, order co-2a144efa2a1a4ab6ac8aa39b04358c0e, armed 18:19Z). Lesson 59's witness commit 981c62cc3 recorded that in-context rule text does not immunize against the loop. The same failure shape sits on the child side too: the payloads' canonical re-arm FIRST ACTION lives in `agents/skills/maintenance/duties-core.md` step 3, which embeds a recycle-then-delete-plus-create tree naming the chain only as the post-failure switch. The chain already carries every property the promotion review asks for: deletion tolerance witnessed twice (landing 7b0f48390 and the 2026-11-03 18:19Z re-arm), an arming proof on every arm, the env-complete job form, the ledger event trail, the missed-order detector, and the silent-strand consult leg landed warning-only on 2026-10-18 with its promotion pre-registered to this review. The gate the 2026-10-17 plan installed now only delays a default the evidence already supports.

## Gist & Examples

TLDR: the promotion review records activation, so a bound session's re-arm and child dispatch default to the launchd clocked-order chain across the overlay and the child duty texts while delete-plus-create becomes the documented fallback behind its existing guards, and the discharge-verification gap row is dispositioned closed by the same change.

Before: a bound session's first action is a same-session mutating automation emission; when emission suppression strikes (four times on 2026-11-03, child sessions included), the re-arm dies with the session.

After: the same bound session arms the chain through its reliable Bash surface as the default, on the overlay and in duties-core's first action and the successor dispatch duty alike; the chain's fired uncapped payload session restores the recurring automation at its own first action (that restore remains a fresh-session mutating emission; its residual risk is named in Edge cases, not assumed away); the delete-plus-create path plus the emission-suppression stand-down and park path stay unchanged as the documented fallback and backstop; the verify-successor arm stays warning-only at review time (zero recorded catches, its consumers and masking limits named), per its pre-registered promotion criteria.

Edge cases: a chain arm refusal or an unreachable launchd runtime routes to the documented fallback (delete-plus-create behind its guards) unchanged; a fresh or unbound session never enters the bound-session default and keeps `CronCreate`; a degraded toolset with no mutation primitives keeps the reduced-toolset terminal park; the watchdog's darkness predicate reads an armed, undischarged clocked order as the carrier being present, so the chain-pending window is not darkness; a silent strand after activation surfaces only through the warning-only detector family at a survey turn (a dark loop runs no consults), which is why the disposition sentence carries a re-open trigger rather than a claim of detection.

## Outcome

The promotion review is held and recorded, and the ladder and duty texts name the chain as the operative default for bound sessions.

- The activation decision rule fires on the named evidence inventory (Task 1); on any failed conjunct, or when Task 1's covering-run check finds this origin already covered by another plan, the review records "activation deferred" or "activation moot-by-coverage" in one state-file note with the failing witness, and no text flips.
- The delete-own-spawner leg's mechanics, the ownership allowlist, the post-delete probe, the distinct-failure rollback, the emission-suppression stand-down, the `pending_rearm` park path, and the reduced-toolset terminal are all unchanged (the origin's arm 3 honored verbatim); the leg's entry gains only the chained-path skip.
- The gap row's disposition lands as the activated lead sentence's citation of this plan as the review of record, carrying the re-open trigger (a witnessed chain misfire re-opens the default via a new plan), the revert recipe pointer (the plan's own quoted prior bytes plus re-pinning), and the verify-successor arm's standing 2027-01-18 decision date.
- The verify-successor arm's review decision is recorded beside its registry posture: stays warning-only on zero recorded catches (the expected branch); a true recorded catch promotes it per the pre-registered removals-row criteria as a recorded deviation.
- Gate delta: no machinery gate added or removed; the removed promotion-deferral sentences are operative text, not machinery gates. The change is a promotion of an existing unbound mechanism behind its pre-registered review plus a documentation flip; the repository guidelines' anti-growth rules are honored by the net byte balance the Task 4 single commit reports over the final committed bytes (Tasks 2 and 3 combined).
- Companion pin rows for the changed operative text are the standing duty for skill-text changes (the 2026-10-17 guard plan Task 4 precedent), not new gates; they land in the same commit as the text they assert.
- Origin disposition: the origin row flips covered at landing via the standard mark-covered step of the authoring lifecycle, recorded here per the Done-when mapping.
- Visibility note: activation shifts the loop's primary mutation carrier from the listing-visible automation surface to launchd orders that listing-based guards cannot see; the clocked-orders ledger plus payload copies are the chain carrier's registry of record, and the frequency shift from exceptional switch to default is the accepted exposure change this review prices.
- Origin arm 2 (a fresh-chat re-arm route built on a durable file write) is rejected by simpler-design comparison recorded here: the durable-write route already exists (the `pending_rearm` park plus the Step 0 discharge precedence plus the memory-index line, the origin's own backstop), and activation removes the bound session's first-action emission dependency, the specific joint the origin witnesses failing; a second durable-write ceremony would duplicate the park path without a guaranteed discharger beyond the ones the park path already names.

## Assumptions

- The chain's operation signature is stable: this plan changes no line of `scripts/execute_plan_runtime.py` or `scripts/execute_plan_resume_watcher.py`; the activation is skill and duty text plus companion pin rows only.
- Fixed operator cadences (D-3 daily 11:00, D-4 05:49, D-11 01:53) keep their slot semantics; activation changes the carrier mechanism a bound session uses between fires, never the slot selection rules.
- Fresh chats and never-bound sessions keep `CronCreate` as their path; the standing loop carrier itself stays a `CronCreate` create per the existing recipe text.
- The Operator-ordered schedule surface paragraph keeps its delete-own-spawner-first ordering for direct operator schedule asks (unchanged surface; only its stale default-in-waiting boundary clause is updated).
- A live duplicate-origin collision is underway at authoring time: a sibling authoring run (claim sess_automation-7c014815-1813-auth, its own worktree, a frozen PLAN-PROMPTS entry) is racing this plan on the same origin row. The claim and landing machinery own the deconfliction (first canonical claim, first-landed-wins); Task 1's covering-run check converts a lost race into the moot-by-coverage abort rather than a second execution of the same activation.
- The review's decision rule is evidence-thresholded, not open-ended; conjunct 4 is stated in its checkable form (swept surfaces record zero recurrence) and the plan does not claim the sweep proves absence for the zero-residue subclass the Terms define.
- The verify-successor sweep at review time covers the scheduler-state notes and turn_error fields, the friction-audit state, and the clocked-orders ledger; a flag recorded anywhere there counts as a true catch for its promotion criteria.
- The skill-text budget gate is warning-only; the plan still reports the zcode.md byte balance because operative text growth without deletion is a review finding class under the repository guidelines.
Decision points requiring a grill: none remain.

## Standing constraints

- No new gate, validator, lock, ledger, or required ceremony; companion pin rows for changed operative text are the standing duty, not new gates; no removal of any existing refusal, check, or state-schema field; the only removals are the obsolete promotion-deferral sentences of the activated text.
- The emission-suppression stand-down and park path stay unchanged as the backstop; nothing protective is retired without a witnessed-incident basis (the origin's own constraint).
- The delete-own-spawner leg's mechanics stay byte-unchanged in every paragraph that names them; the only change is the entry condition's chained-path skip (no delete is entered when the creation form is the chain, because the Bash arm needs no cap lift).
- Runtime overlay and duty text name ZCode primitives as their charter; the runtime-agnostic `agents/skills/maintenance/SKILL.md` remains out of scope for this plan, while `duties-core.md` (the shared child duty set the templates load) and `template-execution.md`'s successor duty are in scope because they carry the child-side first action this plan activates.
- Every changed refusal or pin needle keeps its accepted form named beside it; companion pin rows land in the same commit as the text they assert.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the activated text names exactly one operative default for bound sessions and one documented fallback across all three edited files; every surviving pin needle stays green or its pin row moves in the same change.
- compatibility: fresh-chat and unbound paths, the fixed operator cadences, the park and stand-down paths, and the schedule-ask surface behave byte-identically after the change, except the one boundary clause Task 3 updates.
- maintainability: the byte balance of `agents/skills/maintenance/zcode.md` is net-negative or within 500 bytes net-positive, recorded via wc -c before and after in the completion claims; no second mechanism description is introduced (the chain-default sentence is single-homed in the re-arm hygiene bullet).

**Done when:**
- Task 1's evidence inventory is on disk with each conjunct's witness path, the covering-run check has run, and the activation verdict is recorded in one state-file note.
- The zcode.md ladder step 2, the turn-start carrier re-arm duty's creation-form default clause, the Re-arm hygiene bullet's chain-default sentence, duties-core's step 3, template-execution's successor duty, and the schedule-surface boundary clause all name the activated posture, and every grep in the Validation Commands block over the changed text passes.
- The companion pin rows in `scripts/check_maintenance_pins.sh` assert the activated text and the pins suite exits 0.
- The full validation block passes over the final bytes; the byte balance of `agents/skills/maintenance/zcode.md` is recorded in the completion claims.

**Ship when:**
- No external prerequisites and no release gate; the change is repository-internal.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md` (Task 2)
- `agents/skills/maintenance/zcode.md` (Task 3)
- `agents/skills/maintenance/duties-core.md` (Task 3)
- `agents/skills/maintenance/template-execution.md` (Task 3)
- `scripts/check_maintenance_pins.sh` (Task 4)

**Tests:**
- none; the pins suite is the test surface for this change and no script behavior changes.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py` and `scripts/execute_plan_resume_watcher.py`; reason: the chain is activated as-is, zero script bytes change.
- `agents/skills/maintenance/SKILL.md` and the other maintenance modules not named above; reason: runtime-agnostic surfaces keep their generic wording, the overlay and the two child-duty files own the activated posture.
- `README.md`, `docs/history/` archive rows, and the machinery registry rows; reason: no catalog surface changes and the registry notes stay true under the expected branch (arm stays warning-only).

## Validation Commands

Authoring-time evidence (recorded before round 1 per authoring rule 29): the touched no-em-dash scan, the public-hygiene scan, and the readiness pre-round gate were executed over this plan's bytes and passed; the pins suite over the unchanged authoring tree passed. Polarity, stated per grep: the activated-text needles (asserting text Task 2 inserts) are RED-today and flip GREEN exactly when Task 2 and Task 3 land; the needles that already occur in today's text (`documented fallback firing only behind both guard rule sets`, `clocked-order discharge-verification gap row`) are GREEN-today and witness retention until Task 2 rewords their spans, which is when their count-exact forms take over witnessing the landed replacement; the superseded-wording negation greps are RED-today (each superseded span exists in today's text) and flip GREEN when their removing tasks land, the lead-family four with Task 2 and the stale-declaration four with Task 3. On the abort path (Task 1 defers), the plan-local span greps for the activated text stay RED as the sanctioned-deferral state recorded in the state-file note, never a task failure. On the promote branch (Task 1 records a caught chain misfire), the warning-only posture needle line and its pin row are not asserted and their RED is the sanctioned promoted posture recorded as the deviation. `bash -n` over this block passed at authoring time.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
export PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH"
python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q || { echo "FAIL: watcher suite"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins"; exit 1; }
python3 scripts/skill_text_budget.py --check >/dev/null 2>&1 || true
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em-dash scan"; exit 1; }
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || { echo "FAIL: hygiene scan"; exit 1; }
( cd "$REPO" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md ) || { echo "FAIL: pre-round gate"; exit 1; }
test "$(grep -oF 'the launchd clocked-order chain is the operative default child dispatch for sessions already bound to an armed automation record' agents/skills/maintenance/zcode.md | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: operative-default needle missing or duplicated"; exit 1; }
test "$(grep -oF 'defaults to arming the chain through the launchd clocked-order chain at the next slot' agents/skills/maintenance/duties-core.md | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: duties-core chained default missing"; exit 1; }
grep -qF 'chain-first leg' agents/skills/maintenance/duties-core.md || { echo "FAIL: duties-core chain-first leg missing"; exit 1; }
grep -qF 'successor chain route' agents/skills/maintenance/template-execution.md || { echo "FAIL: successor chain route missing"; exit 1; }
test "$(grep -oF 'documented fallback firing only behind both guard rule sets' agents/skills/maintenance/zcode.md | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: fallback needle missing"; exit 1; }
test "$(grep -oF 'clocked-order discharge-verification gap row' agents/skills/maintenance/zcode.md | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: gap-row disposition missing"; exit 1; }
test "$(grep -oF 'the verify-successor arm stays warning-only with zero recorded catches at review time' agents/skills/maintenance/zcode.md | wc -l | tr -d ' ')" -eq 1 || { echo "FAIL: verify-successor posture line missing"; exit 1; }
grep -qF 'armed 2026-11-03 by the promotion review' agents/skills/maintenance/zcode.md || { echo "FAIL: activation date marker missing"; exit 1; }
grep -qF 'a witnessed chain misfire re-opens this default via a new plan' agents/skills/maintenance/zcode.md || { echo "FAIL: re-open trigger missing"; exit 1; }
grep -qF 'counts as the carrier being present' agents/skills/maintenance/zcode.md || { echo "FAIL: watchdog chain-aware clause missing"; exit 1; }
grep -qF 'no delete is entered when the creation form is the chain' agents/skills/maintenance/zcode.md || { echo "FAIL: delete-leg chained-path skip missing"; exit 1; }
grep -qF 'docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md' agents/skills/maintenance/zcode.md || { echo "FAIL: review-of-record citation missing"; exit 1; }
grep -qF 'activated 2026-11-03' agents/skills/maintenance/zcode.md || { echo "FAIL: schedule-surface activation marker missing"; exit 1; }
if grep -qF 'delete-plus-create is the operative path; the recycling update call is demoted' agents/skills/maintenance/zcode.md; then echo "FAIL: demoted heading still present"; exit 1; fi
if grep -qF 'takes over as the operative default for bound sessions only when the promotion review records' agents/skills/maintenance/zcode.md; then echo "FAIL: promotion-gate sentence still present"; exit 1; fi
if grep -qF 'Demoted fallback (arm 3)' agents/skills/maintenance/zcode.md; then echo "FAIL: demoted lead still present"; exit 1; fi
if grep -qF "The promotion review and the guard rules' cost review are separate decisions" agents/skills/maintenance/zcode.md; then echo "FAIL: obsolete cost-review sentence still present"; exit 1; fi
if grep -qF 'keeps delete-plus-create operative' agents/skills/maintenance/zcode.md; then echo "FAIL: stale operative declaration still present"; exit 1; fi
if grep -qF 'step 2 is delete-plus-create operative' agents/skills/maintenance/zcode.md; then echo "FAIL: stale step-2 operative declaration still present"; exit 1; fi
if grep -qF 'stays UNVERIFIED with delete-plus-create operative' agents/skills/maintenance/zcode.md; then echo "FAIL: stale UNVERIFIED operative declaration still present"; exit 1; fi
if grep -qF 'the only operative path' agents/skills/maintenance/zcode.md; then echo "FAIL: stale only-operative-path declaration still present"; exit 1; fi
grep -qF 'ladder operative chain default needle' scripts/check_maintenance_pins.sh || { echo "FAIL: renamed pin row missing"; exit 1; }
grep -qF 'ladder re-arm chained default needle' scripts/check_maintenance_pins.sh || { echo "FAIL: re-arm pin row missing"; exit 1; }
if grep -qF 'ladder operative delete-plus-create needle' scripts/check_maintenance_pins.sh; then echo "FAIL: old pin row name still present"; exit 1; fi
```

### Task 1: Promotion review evidence pass, covering-run check, and disposition decision

Context surface: the plan's Terms, Why, and Assumptions.

Files: none (read-only evidence pass; the verdict and inventory digest land in one state-file note whose write this task orders, and the checkboxes ride the plan document's own review commits; no separate Task 1 commit exists because the evidence pass writes no tracked file).

- [ ] Covering-run check first: the origin row docs/history/backlog/2026-11-03-dispatch-ladder-rearm-first-action-joint.md still reads Status open at the primary checkout and no other plan file at docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md exists on the default branch; when either fails, record "activation moot-by-coverage" in the state-file note with the covering plan's path and skip Tasks 2 through 4 entirely (the race resolution the Assumption models) [class: REPOSITORY_TEST]
- [ ] Suppression-witness rows compiled: the four 2026-11-03 emission-suppression stand-downs located on disk (scheduler-state `turn_error`/`rearm_note` entries at 00:57, ~10:03, ~10:05, and 18:16-18:19Z) plus lesson 59's witness commit 981c62cc3, each row naming its path [class: REPOSITORY_TEST]
- [ ] Deletion-tolerance rows compiled: landing 7b0f48390 and the 2026-11-03 18:19Z re-arm order co-2a144efa2a1a4ab6ac8aa39b04358c0e with arming proof fire_epoch equal to requested_epoch, each row naming its ledger or state path [class: REPOSITORY_TEST]
- [ ] Verification-family rows compiled: the arming proof in scripts/execute_plan_runtime.py, the env-complete headless job form, ledger discharge events with late flags, the `clocked-order-due` missed marking, and the warning-only verify-successor consult leg with its two machinery registry rows, each named [class: REPOSITORY_TEST]
- [ ] Silent-strand catch sweep compiled: the count since the 2026-10-18 landing over the scheduler-state notes and turn_error fields, the friction-audit state, and the clocked-orders ledger, with zero-catch or per-catch rows named; the zero-residue limitation of this sweep is recorded beside the count, never silently dropped [class: REPOSITORY_TEST]
- [ ] Activation conjuncts evaluated against the inventory: (1) deletion tolerance has at least one witnessed live pass; (2) the arming proof fired on every witnessed arm including the most recent; (3) the env-complete job form is the shipped payload builder shape; (4) the silent-strand detector family is live with its consult wired and the swept surfaces record zero recurrence since the 2026-10-18 landing [class: IMPLEMENTATION_REQUIRED]
- [ ] Abort path holds fail-closed and durable: on any failed conjunct, "activation deferred" is recorded with the failing witness in the same state-file note and Tasks 2 through 4's flips are skipped, the documented fallback staying operative; the state-file note (one targeted scheduler-state notes[] append) is the durable home for both the proceed and defer verdicts beside the inventory digest [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify-successor decision recorded at this review: zero recorded catches records "stays warning-only, promotion criteria unmet at review time, next decision point 2027-01-18" (the expected branch, named in Task 2's disposition sentence); a recorded catch promotes the arm per the pre-registered removals-row criteria and is recorded as a deviation in the completion claims with the registry edits it orders [class: IMPLEMENTATION_REQUIRED]

### Task 2: Activate the overlay ladder and re-arm texts

Context surface: the plan's Terms, Outcome, Standing constraints, and Task 1's recorded verdict.

Files:
- `agents/skills/maintenance/zcode.md`

Keep every surviving needle byte-identical (`## Child dispatch ladder`, `Rollback: if the child create then fails`, `runs the peak-window and runtime-fit check first`).

- [ ] Ladder step 2 heading parenthetical: replace `delete-plus-create is the operative path; the recycling update call is demoted to the optimization leg closing this step` with the activated order naming the chain as the operative default child dispatch for sessions already bound to an armed automation record and delete-plus-create as the documented fallback [class: IMPLEMENTATION_REQUIRED]
- [ ] Demoted lead removed: the `Demoted fallback (arm 3):` lead sentence, the promotion-gate sentence, and the obsolete cost-review sentence `The promotion review and the guard rules' cost review are separate decisions` asserted absent by the validation block's negation greps are deleted [class: IMPLEMENTATION_REQUIRED]
- [ ] Activated lead landed: the replacement lead opens with Operative default (armed 2026-11-03 by the promotion review) citing this plan's path as the review of record [class: IMPLEMENTATION_REQUIRED]
- [ ] Gap-row disposition landed: the activated lead carries the gap-row disposition with the exact bytes `clocked-order discharge-verification gap row`, the re-open trigger needle `a witnessed chain misfire re-opens this default via a new plan`, and the revert recipe pointer (the plan's own quoted prior bytes plus re-pinning) [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify-successor posture landed: the disposition wording carries the exact bytes `the verify-successor arm stays warning-only with zero recorded catches at review time` with the standing 2027-01-18 decision date [class: IMPLEMENTATION_REQUIRED]
- [ ] Chain-default sentence: lands with the full bytes `the launchd clocked-order chain is the operative default child dispatch for sessions already bound to an armed automation record`, the companion pin needle `the launchd clocked-order chain is the operative default child dispatch` being its contiguous prefix, and retains the deletion-tolerance witness clause [class: IMPLEMENTATION_REQUIRED]
- [ ] Fallback sentence: the documented-fallback sentence (exact needle `documented fallback firing only behind both guard rule sets`) gains the first-route clause `and taken first when the chain arm refuses or the launchd runtime cannot be reached` [class: IMPLEMENTATION_REQUIRED]
- [ ] CronCreate and recycling sentences: the retained CronCreate sentence is extended by `and for sessions whose delete-own-spawner leg lifted the cap`; the recycling-leg status sentence stays unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Creation-form sentence amended in place: the turn-start duty's `The creation form follows the cadence rule:` sentence itself gains the bound-session default, reading that a session bound to an automation record defaults to arming the chain through the launchd clocked-order chain at the next slot with the scheduler-template payload copy carrying the FIRST-ACTION recurring restore [class: IMPLEMENTATION_REQUIRED]
- [ ] Unchanged-paths clause in the same sentence: fresh or unbound sessions and sessions whose delete-own-spawner leg lifted the cap keep the automation-primitive create; the chain-default sentence is single-homed in the Re-arm hygiene bullet and the turn-start duty references it rather than restating it, the turn-start sentence's added clause being that brief default clause only [class: IMPLEMENTATION_REQUIRED]
- [ ] Delete-leg chained-path skip: the re-arm hygiene and turn-start duty paragraphs gain `no delete is entered when the creation form is the chain` beside the existing delete-first ordering, the leg's mechanics untouched [class: IMPLEMENTATION_REQUIRED]
### Task 3: Activate the remaining overlay arms and the child duty texts

Context surface: the plan's Terms, Outcome, Standing constraints, and Task 1's recorded verdict.

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/duties-core.md`
- `agents/skills/maintenance/template-execution.md`

- [ ] Stale-span reconciliation, re-arm and ladder spans: each named span is scoped to the fallback path or reworded to the activated posture: the re-arm hygiene parenthetical `(operative delete-plus-create: ...)`, the turn-start duty's `the dispatch ladder's operative delete-plus-create consumes the just-armed carrier record`, step 2 body phrases (`operative delete`, `converges to the operative delete-plus-create`) [class: IMPLEMENTATION_REQUIRED]
- [ ] Stale-span reconciliation, discipline and switch spans: the dispatch-discipline sentence `a parent re-arm's shape is per the recipe's operative shape (delete-plus-create today; ...)` is reworded to the activated shape, and the distinct-failure switch sentence gains the clause that when the failing mechanism was the chain the switch lands on the park [class: IMPLEMENTATION_REQUIRED]
- [ ] Stale-span reconciliation, operative declarations (four): each present-tense declaration is scoped to the documented fallback or reworded to the activated posture, byte-exact: `the dispatch ladder keeps delete-plus-create operative`, `the dispatch ladder's step 2 is delete-plus-create operative`, `stays UNVERIFIED with delete-plus-create operative`, `the ladder keeps delete-plus-create operative`; neighboring witness and pin-asserted bytes stay untouched [class: IMPLEMENTATION_REQUIRED]
- [ ] Stale-span reconciliation, only-operative-path declarations (two): each is reworded to the fallback-scoped posture, byte-exact: `keeps delete-plus-create as the only operative path` and `delete-plus-create stays the only operative path`; no rewording reintroduces a negated stale form; the conditional declaration `keeps delete-plus-create as its operative path` is deliberately retained, scope-conditional on the recycling legs and true post-activation [class: IMPLEMENTATION_REQUIRED]
- [ ] Watchdog chain-aware clause: the watchdog backstop bullet gains that an armed, undischarged clocked order for the repository counts as the carrier being present, so the chain-pending window is not darkness [class: IMPLEMENTATION_REQUIRED]
- [ ] Precheck and park-discharge scoping: the ladder precheck bullet and the park-discharge precheck routing gain that the chain leg needs no automation mutating primitives and routes before the fallback legs for bound sessions [class: IMPLEMENTATION_REQUIRED]
- [ ] duties-core step 3: the child-side re-arm tree gains the chain-first leg, reading that a bound session defaults to arming the chain through the launchd clocked-order chain at the next slot via `chain-first leg` wording with the delete-plus-create leg demoted to the fallback behind the existing precheck, and the same no-delete-when-chained skip [class: IMPLEMENTATION_REQUIRED]
- [ ] template-execution successor duty: the ZCODE SUCCESSOR DISPATCH paragraph gains the `successor chain route` (the chain arms the successor one-shot as the first leg for this bound session, reshape and delete-plus-create demoted behind it), the both-legs-fail park path unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Schedule-surface boundary clause: `the loop child dispatch launchd default-in-waiting` is replaced by the exact bytes `the loop child dispatch launchd default activated 2026-11-03` [class: IMPLEMENTATION_REQUIRED]
### Task 4: Companion pin rows and the single validation commit

Context surface: the plan's Validation Commands and Tasks 2 and 3's landed text.

Files:
- `scripts/check_maintenance_pins.sh`

- [ ] Pin row renamed and re-needled in this task's commit: the row named `ladder operative delete-plus-create needle` is renamed to `ladder operative chain default needle` and re-needled to `the launchd clocked-order chain is the operative default child dispatch`, its comment naming this plan [class: IMPLEMENTATION_REQUIRED]
- [ ] Arm-3 rows converted in this task's commit: the rows `arm 3 demoted-fallback paragraph heading` and `arm 3 promotion-review activation span` convert to absence (negation) rows on their removed spans; the row `arm 3 retired default-dispatch span` re-pins the fallback sentence's retained span; the bound unit-clause parenthetical row re-pins the activated-shape replacement of `(delete-plus-create today; ...)`, each comment naming this plan [class: IMPLEMENTATION_REQUIRED]
- [ ] Byte balance recorded: wc -c of agents/skills/maintenance/zcode.md before (base) and after this task's single commit land in the completion claims; the file's net balance is measured once over the final committed bytes covering Tasks 2 and 3, net-negative or within 500 bytes net-positive [class: IMPLEMENTATION_REQUIRED]
- [ ] GREEN: every plan-local span grep in the Validation Commands block over the three edited files passes, and all eight negation greps confirm the removed spans absent [class: REPOSITORY_TEST]
- [ ] New positive rows added with the comment naming this plan: `ladder re-arm chained default needle` asserting `defaults to arming the chain through the launchd clocked-order chain at the next slot` in duties-core; `ladder gap-row disposition needle` asserting `clocked-order discharge-verification gap row` in zcode.md; `ladder verify-successor posture needle` asserting `the verify-successor arm stays warning-only with zero recorded catches at review time` in zcode.md [class: IMPLEMENTATION_REQUIRED]
- [ ] New absence rows added with the comment naming this plan: absence (negation) rows on the remaining six of the eight removed spans named by the validation block's negation greps, the converted rows of the arm-3 item covering the other two [class: IMPLEMENTATION_REQUIRED]
- [ ] RED-GREEN: before Tasks 2 and 3 the new rows fail on the untouched text and after they land the pins suite exits 0 with the rows green; polarity of the already-green needles follows the block's stated polarity table [class: REPOSITORY_TEST]
- [ ] Single commit: Tasks 2 through 4 land as one commit so no intermediate commit leaves the pins suite red, the text and its moved and added pin rows together; commit message: `maintenance: activate the launchd chain as the bound-session re-arm and dispatch default` [class: IMPLEMENTATION_REQUIRED]
- [ ] Full validation sweep: the complete Validation Commands block runs over the final bytes and every line passes; any RED line is a task failure, never a waiver (abort path: the sweep is not run and the sanctioned-deferral note stands; promote branch: the warning-only posture needle lines' RED is the sanctioned promoted posture per the polarity paragraph) [class: REPOSITORY_TEST]

