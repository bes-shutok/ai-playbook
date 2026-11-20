# Plan: stop-boundary-rederivation

Backlog origins (scope of record):
- docs/history/backlog/2026-11-14-user-only-blocker-classification-self-certified.md
- docs/history/backlog/2026-11-14-per-run-directives-override-d18-arming.md

Driving force: automation + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-14-plan-review-stop-boundary-rederivation-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Executed: yes (cdd899ee23370058d5b06617fb82c5bc19dea0be)
Authoring claim: stop-boundary-rederivation.md (session sess_939f5b42-9671-4d9b-8535-93b6ae8366f1)

## Terms

- User-only blocker: a stop-path blocker the deciding surface classifies into decisions.md's self-heal bullet's exempt class (missing authority, ambiguous ownership, unsafe target, external-owner action, explicit operator stop); the classification exempts the stop from the self-heal consult.
- Classification verification duty: the new pre-stop duty this plan adds: before recording a user-only stop or ask, the deciding surface verifies the classification from disk with two reads (the refusing gate's source or owning rule text; one corpus recall) and records both.
- Corpus recall surfaces: the three standing search surfaces the duty names: the backlog directory `docs/history/backlog/`, the lesson corpus `docs/maintenance/development_lessons.md`, and the user-level session memory index the session reads, bound to its audit home `docs/maintenance/recurring-tasks/memory-index-audit.md`; keyed on the refusal's distinctive phrases.
- D-18: the operator directive in `docs/maintenance/operator-directives.md` (loop continuity): the loop runs until the eligible queue is empty or the primary 5h wall; every exit arms its successor or records its exemption; the closing report's `loop-liveness:` line names the exit token or standing carrier.
- Exit token: the `loop-exit:<class>` record D-18 orders on each exit; the five landed classes are queue-empty, quota-wall, blocked-retry, operator-park, operator-stop.
- Directive-cap exit: the new exit class this plan adds: a per-run payload or ask wording that caps the run's unit count (for example "author at most 1 plan then stop") ends the capped lane's loop with a recorded exemption, never silently.
- Precedence sentence: the new D-18 rule binding per-run directives to the standing exit arms: a per-run directive composes with them unless it explicitly orders a full stop without arming.
- Reset-anchored successor: the one-shot resume carrier armed at the quota probe's `reset_at_epoch` plus the standing arming margin (the landed arming shape this plan binds by reference, never restates).
- Self-finance: the byte-budget pay-for-growth duty shape where a file already past its advisory cap takes its own addition's bytes out of its existing text in the same change (compression, not duty removal); where the witness-safe reservoir is smaller than the addition, the residual is bounded by the byte-budget gate's single-read ceiling headroom.
- Pins suite: `bash scripts/check_maintenance_pins.sh`, which pins literals in guarded maintenance modules including `agents/skills/maintenance/decisions.md`.
- Byte-budget gate: `python3 scripts/skill_text_budget.py --check`; blocking on the single-read ceiling class, advisory on cap and ratchet breaches; the same-change payment duty is review-enforced per the repository's anti-growth rules, not enforced by this gate's exit code.

## Why

The landed continuation machinery (the self-heal consult duty, the D-18 no-dark-exit contract, the quota-wall arming arms) failed at its decision boundaries in one witnessed run: a diagnosable blocker reached the operator as a user-only classification without the refusing gate's source or any corpus surface being read, and two later exits carried no exit token and no loop-liveness line because their class (a directive-capped run) has no token shape and no precedence rule. The loop stopped dark twice in ways the landed text was written to prevent.

## Gist & Examples

TLDR: verify user-only blocker classifications from disk and give directive-capped runs their D-18 exit shape, so the loop never stops dark on a judgment call.

Before: a session that asserts "user-only" skips the self-heal consult on its own say-so; the witnessed run parked for the operator on a refusal whose fix was two seal-anchor edits documented in an open backlog row, a lesson, and the session's own memory index, and later exits recorded no token at all. After: the same session must produce two recorded reads before recording a user-only stop (a contradicting read re-routes the blocker to the consult and the blocked-retry arm), and a directive-capped run exits with `loop-exit:directive-cap` and a loop-liveness line naming the directive, while its quota wall still arms the reset-anchored successor.

## Outcome

Maintenance stop boundaries re-derive their classifications and exits from disk evidence instead of conversation-internal narrative.

- A user-only stop or ask carries two recorded verification reads, and a misclassification is caught at the boundary instead of by the operator.
- A directive-capped run's exit is recorded in the D-18 vocabulary, so the loop's continuity state is readable from the closing report.
- A unit-capped run's quota wall still arms the reset-anchored successor; the cap no longer reads as a stop-without-arming order.

Gate delta: +1 recording duty (the classification verification reads recorded at user-only stops; prose-only, no refusal surface, no checked-set growth) and +1 exit-token shape (`loop-exit:directive-cap`) and +1 precedence sentence at D-18; removed: none (no refusal, check, or field is removed); priced by the witnessed incident the origin rows record (an operator turn consumed at a self-certified user-only park; two tokenless exits on a live run); no new machinery.

## Assumptions

- assume the classification-verification duty's home is the decisions.md self-heal bullet; basis: the entry's priced options plus the verified read-surface fact (the maintenance router, the runtime overlay, and both gates resolve their module citations from the repo checkout, so the repo copy is the operative read surface; the runtime registry twin `~/.agents/skills/maintenance/decisions.md`, byte-identical to the repo copy today, converges through the operator-side registry sync, and a registry-authoritative reversion is outside this plan's mutation surface, reconciled at the twin's next natural edit)
- assume decisions.md takes no net growth beyond the bounded residual: the self-finance shape (compression of the same bullet's verbose spans) pays for the addition up to the witness-safe reservoir, the residual bounded by the single-read ceiling headroom; basis: the advisory breach measured 2026-11-14 (99904 bytes over cap 92132; re-priced at execution, see the receipt below)
- assume the directive-cap exit records as `loop-exit:directive-cap`; basis: the landed token vocabulary's naming shape (queue-empty, quota-wall, blocked-retry, operator-park, operator-stop)
- assume serving the operator's indefinite-operation direction needs no dispatch-ladder change: the precedence sentence plus the token shape close the witnessed darkness, and continuation past a cap rides the standing carrier per D-18; basis: the entry's rejected alternative with its recorded evidence basis
- assume the byte-neutrality target was re-priced at execution to a bounded 96-byte overage; basis: the execution intermediate review 2026-11-14 measured the witness-safe annotation reservoir (the witness-integrity restorations it required consumed the strict zero-growth reading's compression pool; the two constraints were jointly unsatisfiable at the strict bound; the re-price keeps both with the residual bounded by the byte-budget gate's single-read ceiling (100000, headroom 96 over the 99904 baseline), the byte-budget gate's own advisory breach report being the growth record the anti-growth rules name)
- assume origin row 1's landing disposition: this plan fixes the classification half; the row's recall-surface half (the cross-project self-heal skill's unnamed search surfaces) stays out of scope, and a successor row is filed at landing for it if the self-heal skill text does not carry the named surfaces by then; basis: the row's Compounding-half paragraph and the recorded home-selection receipt
Decision points requiring a grill: duty home selection resolved by decision receipt (home = the decisions.md self-heal bullet; source: the investigation entry stop-boundary-rederivation, 2026-11-14; affected: Task 1); token name resolved by decision receipt (`loop-exit:directive-cap`; source: the same entry, 2026-11-14; affected: Task 2)

## Standing constraints

- No new gate, validator, lock, ledger, or required ceremony: both tasks edit existing operative text only.
- The pins suite and the byte-budget gate must stay green (non-blocking) after both edits; the pins suite pins literals in decisions.md, so any pinned span the edits touch gets its pin row updated in the same change, and the Task 1 compression diff keeps every pinned span verbatim.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the pins suite exits 0 after both edits; the byte-budget check exits 0 (no blocking ceiling breach) with decisions.md net bytes within the single-read ceiling headroom over the pre-change count
- compliance: the new duty text names all three corpus recall surfaces and the two recorded reads; D-18 carries the directive-cap class and the precedence sentence
- completeness: every remedy both origin rows state is present in exactly one task

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0
- `python3 scripts/skill_text_budget.py --check` reports no new blocking breach (exit 0; decisions.md at or under the 100000 single-read ceiling) and decisions.md's byte count is at most 96 bytes over its pre-change count (99904), the single-read ceiling headroom
- grep over the two edited files finds the verification duty, the three surface paths, the `loop-exit:directive-cap` token, and the precedence sentence

**Ship when:**
- (OPERATIONS_FOLLOW_UP) the next witnessed maintenance stop records the two verification reads and carries an exit token on its loop-liveness line; evidence owner: the next maintenance authoring or execution session that hits a blocker or a directive cap; measurable closure condition: one witnessed stop whose closing report carries both recorded reads and a non-empty `loop-liveness:` line; evidence sources: that closing report and the turn's decision-reason record, each tracing to Task 1's and Task 2's landed text

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/decisions.md` (Task 1)
- `docs/maintenance/operator-directives.md` (Task 2)

**Tests:**
- none; both tasks are operative-text edits verified by the pins suite, the byte-budget gate, and grep checks

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/self-heal/SKILL.md` (and its deployed runtime copy); reason: the duty homes in decisions.md by recorded decision receipt, and a self-heal skill edit needs a dual-surface sync outside this plan's scope
- `docs/maintenance/development_lessons.md`; reason: lesson capture rides the closeout learn step, not this plan's tasks

## Validation Commands

Authoring-time recording (rule 29; amended 2026-11-14 at execution: the Task 1 byte-neutrality commitment re-priced to a bounded 96-byte overage (the single-read ceiling headroom at 100000) after the intermediate review's witness-integrity restorations consumed the measured annotation reservoir): the pins suite exits 0 (`OUTCOME: pass`, the decisions.md advisory breach line 99904 over 92132 confirmed); the byte-budget gate exits 0 (0 ceiling breaches blocking, 3 advisory ratchet lines); the pre-round gate exited 1 at r2 with three structural violations (missing standalone trailer, untagged checklist items, one over-cap item) - fixed by the r2 fold batch and re-run green at r3; the four greps are RED-today at count 0 (exit 1 each), the expected authoring-time state, their closure condition being the post-execution landed text; the mechanical audit recorded: em-dash fixer 0 substitutions at every plan write, public hygiene scan exit 0.

```bash
bash scripts/check_maintenance_pins.sh || { echo "MISS: pins suite"; exit 1; }
python3 scripts/skill_text_budget.py --check || { echo "MISS: byte-budget gate"; exit 1; }
grep -q "loop-exit:directive-cap" docs/maintenance/operator-directives.md || { echo "MISS: directive-cap token"; exit 1; }
grep -q "verifies the classification from disk" agents/skills/maintenance/decisions.md || { echo "MISS: verification duty"; exit 1; }
grep -q "memory-index-audit" agents/skills/maintenance/decisions.md || { echo "MISS: memory-index binding"; exit 1; }
grep -q "docs/history/backlog/" agents/skills/maintenance/decisions.md || { echo "MISS: backlog surface"; exit 1; }
grep -q "docs/maintenance/development_lessons.md" agents/skills/maintenance/decisions.md || { echo "MISS: lesson-corpus surface"; exit 1; }
grep -q "composes with the standing exit arms" docs/maintenance/operator-directives.md || { echo "MISS: precedence sentence"; exit 1; }
```

### Task 1: Classification-verification duty in the self-heal bullet

**Files:**
- `agents/skills/maintenance/decisions.md` (Task 1)

**Evidence:**
- the self-heal bullet's user-only enumeration (decisions.md, the self-heal bullet) is the classification site the duty verifies; the bullet landed 2026-11-02 (6f4b53260) with the enumeration unverified by design
- the witnessed classification failure (origin row 1): the park-3 classification named a machinery conflict without reading `scripts/corrections_record.py`, the open row `docs/history/backlog/2026-11-03-review-plan-cap-closure-seal-anchor-composition.md`, lesson #383, or the session memory index, all of which held the accepted composition
- the advisory breach (99904 bytes over cap 92132, measured 2026-11-14) binds the self-finance shape

- [x] In the self-heal bullet, after the user-only enumeration, add the verification duty: before recording a user-only stop or ask on a blocker, the deciding surface verifies the classification from disk with two recorded reads: (a) the refusing gate's source or the owning rule text at the refusal point; (b) one corpus recall keyed on the refusal's distinctive phrases; both reads recorded on the stop or ask [class: IMPLEMENTATION_REQUIRED]
- [x] In the same insertion, name the three corpus recall surfaces with their paths: the backlog directory `docs/history/backlog/`, the lesson corpus `docs/maintenance/development_lessons.md`, and the user-level session memory index, bound to its audit home `docs/maintenance/recurring-tasks/memory-index-audit.md` [class: IMPLEMENTATION_REQUIRED]
- [x] In the same insertion, add the re-route rule: evidence contradicting the classification re-routes the blocker to the non-user-only path (the self-heal consult, then the D-18 blocked-retry arm); the explicit-operator-stop class and a route pinned to another session by its own text verify in one read and pass immediately, the duty pricing one source read plus one search, never an investigation [class: IMPLEMENTATION_REQUIRED]
- [x] Self-finance the addition: compress verbose spans of the same file in the same change so the file's byte count does not exceed its pre-change count (99904) by more than 96 bytes, the byte-budget gate's single-read ceiling (100000) headroom, every witness-preserving annotation compression taken first, no duty, exemption, or witness citation deleted or damaged, and the compression diff keeping every pinned span verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` and update any pin row the edit touches in the same change; the suite exits 0 [class: REPOSITORY_TEST]
- [x] Append the Revisions-ledger row for this change to `agents/skills/maintenance/CHANGELOG.md`, naming this plan and Task 1 [class: IMPLEMENTATION_REQUIRED]

### Task 2: Directive-cap exit shape and precedence at D-18

**Files:**
- `docs/maintenance/operator-directives.md` (Task 2)

**Evidence:**
- D-18's exit-token population names five classes (docs/maintenance/operator-directives.md, the D-18 record); none covers a directive-capped run's completion or its quota-wall pause, so a compliant session had no token to record (origin row 2's witnessed tokenless exits)
- the maintenance SKILL.md no-dark-exit invariant (the generic loop-liveness binding) already records every token-class exit, so the invariant needs no edit
- the landed arming shape (the reset-anchored successor bullet, agents/skills/maintenance/zcode-scheduling-primitives.md) is bound by reference and stays byte-unchanged

- [x] At D-18, add the precedence sentence: a per-run directive composes with the standing exit arms unless it explicitly orders a full stop without arming (the preserved explicit-current-stop clause deciding that case exactly as D-17 records it); a directive that forbids arming without ordering a full stop routes its capped-create quota-wall exit to the ladder-terminal operator-park token the record already names [class: IMPLEMENTATION_REQUIRED]
- [x] At D-18, add the directive-cap exit class: a per-run payload or ask wording that caps the run's unit count records `loop-exit:directive-cap` on the closing report's loop-liveness line with the exemption naming the directive; a unit-capped run's quota wall still arms the reset-anchored successor for the capped work's remainder [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile D-18's Recorded-population sentence with the new class: the count reads six token classes, and the recorded-exemption population gains the capped completion (the lane stops instead of continuing and holds no standing carrier), the directive being the exemption it names [class: IMPLEMENTATION_REQUIRED]
- [x] Append the Revisions-ledger row for this change to `agents/skills/maintenance/CHANGELOG.md`, naming this plan and Task 2 [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` and `python3 scripts/skill_text_budget.py --check`; both stay non-blocking; update any pin row the edit touches in the same change [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-14-user-only-blocker-classification-self-certified.md: covered by this plan's Task 1 (the classification-verification duty landed in the decisions.md self-heal bullet); the row's recall-surface half is filed as its successor row docs/history/backlog/2026-11-14-self-heal-recall-surfaces-unnamed.md and stays open.
- docs/history/backlog/2026-11-14-per-run-directives-override-d18-arming.md: covered by this plan's Task 2 (the directive-cap exit class, the precedence sentence, and the Recorded-population reconcile landed in the D-18 record).
