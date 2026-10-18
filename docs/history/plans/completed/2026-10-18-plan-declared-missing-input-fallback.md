# Plan: plan-declared missing-input fallback

Authoring claim: docs/tmp/authoring-claims/plan-declared-missing-input-fallback.md (session sess_ba9e0356-44b4-4f13-a29d-a18cdfbc7c15)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-17-parked-run-input-fallback-option.md

Driving force: automation, efficiency
(ranked compound; the arm removes the recurring park-and-wait operator direction on a foreseeable absent input, and the operator-time cost of an all-or-nothing gate; the origin row's reliability motive, authorized execution continuing without evidence loss, is carried by this compound and by the indeterminate-recording floor)

Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-plan-declared-missing-input-fallback-p29c99fd4-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 1.5h total, largest task 0.5h

## Terms

- Missing-input fallback (plan-declared): a bounded alternative arm a plan declares at authoring time for one foreseeable missing-input condition: the plan names the condition, the degraded outputs, the indeterminate-recording duty, and the disclosure duty; the run applies it in-run instead of parking when the declared condition fires.
- Declared condition: the exact, checkable absence shape that fires the fallback, stated in the plan (for example: the named operator-provided artifact is absent from its named delivery location at task start); a condition that does not state an exact checkable shape is not applicable and the run parks.
- Degraded outputs: the outputs the run still produces under the fallback, and the outputs it skips; the plan names both.
- Indeterminate recording: the fallback's duty to record affected classifications as indeterminate in the session manifest instead of inferring them; the no-fabrication core (never infer what the evidence cannot support) survives in every arm.
- Disclosure duty: the fallback's requirement that the session manifest and the closeout report name the fired condition and the degradation.
- Session manifest: execute-plan's named per-run record surface (manifest.md), the home of the fired-fallback record, the indeterminate-classification records, the recorded baseline, and the fallback sample-context outcomes.
- Inclusion Hard Gate: the standing execute-plan gate whose Move to Ship when and Stop outcomes are today's only response to an unavailable evidence source; undeclared absences keep its outcomes byte-unchanged.
- Pins suite: the repository's skill-text regression suite at scripts/check_maintenance_pins.sh; its failing-set comparison is the boundary witness of Task 1.
- Recorded baseline: the pins-suite output tail (the OUTCOME line plus every PIN FAIL and suppressed-recorded-reds line) recorded in the session manifest at the pre-change HEAD before Task 1 edits; Task 3's comparison names it.
- Readiness pre-round: the structural plan gate `python3 scripts/plan_readiness.py <plan> --pre-round`, run before every review round.
- Vendored twin: the runtime-side copy under ~/.agents/skills/ of each touched agents/skills/ file, synced byte-equal in the same change per the repository guidelines' Vendored Asset Sync Rules.

## Why

A plan whose evidence contract depends on an external input has no in-run alternative to a complete stop when that input is absent: the witnessed run paid a full Phase 0 and parked indefinitely on a foreseeable absence. A plan-authored, review-covered fallback lets the run degrade bounded outputs instead, while undeclared absences keep parking exactly as today.

## Gist & Examples

TLDR: execute-plan gains a plan-declared missing-input fallback arm and the plans skill's external-dependency guidance references it, so a foreseen absent input degrades bounded outputs in-run instead of parking; automation and efficiency, because the run handles the routine case itself instead of waiting for an operator.

Before: an execute-plan run whose plan names an operator-provided artifact as a task precondition finds it absent, writes its input-gate record, and parks with workflow_state active; every plan with an external-input contract repeats the all-or-nothing shape.

After: when the plan declares a fallback whose condition covers the absence, the run produces only the declared degraded outputs, records affected classifications as indeterminate in the session manifest, names the fired condition and degradation in the session manifest and the closeout report, marks the affected items complete on their degraded outputs, and continues; when no fallback is declared, or the absence falls outside the declared condition, today's stop response stands byte-unchanged.

Edge cases: an absence outside the declared condition parks (the arm is condition-scoped, never a general bypass); a declaration missing any of the four fields, or stating a condition without an exact checkable shape, is not applicable and the run parks; doubt whether an observed absence is inside the declared condition resolves to the standing outcome, never to firing; a resumed or Recovery pass reads the recorded firing disposition from the session manifest instead of re-deciding; the arm never authorizes editing the plan, a gate, or a validator mid-run and never admits an external prerequisite as executable; sibling span surfaces stay untouched (the delivery contract and park-time state mirror belong to the summary-handoff entry, the record-filing vehicle to the durable-record entry, and the caller policy to the user-directed-gate-workaround entry).

## Outcome

A run facing a declared absent input continues with degraded outputs instead of parking, and the degradation is visible in the session manifest and the closeout report.

- The witnessed all-or-nothing park class shrinks to undeclared, out-of-condition, or uncheckable-declaration absences only.
- The no-inference protections survive: indeterminate recording and the disclosure duty are part of every declaration, and the fired disposition is recorded once and read back on resume.
- No gate, validator, ledger, or new plan section type is added; the declaration is optional plan text.

Gate delta: none counted; the arm adds one prose eligibility check (a declaration must name the four fields and state an exact checkable condition; an incomplete or uncheckable declaration is not applicable and the run parks exactly as it would today, so nothing new refuses, pauses, or checks more than the standing absent-input stop), and the disclosure duty names existing record surfaces (the session manifest and the closeout report); no gate, fence, refusal surface, protocol layer, schema field, or pausing condition is added or removed, and the undeclared-absence response stays byte-identical (admission: the origin row records the rejected gate, bypass, and validator arms with the missing-incident absence named).

## Assumptions

- assume the declaration grammar is exactly the four fields (condition, degraded outputs, indeterminate recording, disclosure), single-homed in the execute-plan arm and referenced by name from the plans skill; basis: the origin row's Expected and Suggested direction.
- assume the declaration lives as optional prose in the plan, an authoring choice with no new section type and no validator; basis: the origin's rejected validator arm and the repository anti-growth rules.
- assume this plan owns only the missing-input response contract; the delivery contract and park-time state mirror belong to post-implementation-review-summary-handoff, the record-filing vehicle to the row docs/history/backlog/2026-10-17-parked-run-durable-record-residue.md, and the caller policy to investigate-user-directed-gate-workaround; basis: the dispatch entry's Orientation span split.
- assume coexistence, not amendment, for the standing inclusion absolutes: the Checklist inclusion gate's admission semantics and its exception-admissibility rules are unchanged, because the arm disposes only the absence of a declared input after the gate's classification and never admits an external prerequisite as executable; the absolutes keep their text and the arm text states the boundary; basis: the plans skill's inclusion-gate and Integration Points sentences and the origin's rejected bypass arm.
- assume the byte growth is priced: the delta is exactly the dispatch entry's anti-growth allowance (one allowance arm in execute-plan plus one authoring bullet in plans), and no equivalent cut exists in either file without reopening the sibling spans the dispatch entry assigns elsewhere; basis: the dispatch entry's Anti-growth line and the repository's skill text anti-growth rules.
- assume vendored twins sync byte-equal in the same change for both touched skills; basis: the repository guidelines' Vendored Asset Sync Rules.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the arm fires only on a plan-declared condition, decided before the Inclusion Hard Gate's pause outcomes; every undeclared or out-of-condition absence keeps today's response, verified by the byte-identity boundary witness and the sample-context exercise
- anti-growth: the landed delta is two prose insertions and one extended sentence, with no gate, validator, ledger, or new section type, verified by the hunk-count check; the byte growth is priced in Assumptions
- maintainability: the four-field grammar has one home (the execute-plan arm) and the plans guidance references it by name, so the emitter/reader drift surface is removed rather than watched

**Done when:**
- both skills carry their insertion with byte-equal vendored twins and the pins suite failing set matches the recorded baseline
- the validation battery is green, the sample-context exercise records the two fresh-run outcomes and the resume read-back outcome, and the landing diff carries exactly the hunks the task lists prescribe

**Ship when:**
- the landed tree's validation battery passes and the closeout report records the boundary, span, and sample-context witnesses

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- agents/skills/execute-plan/SKILL.md
- agents/skills/plans/SKILL.md
- scripts/check_maintenance_pins.sh *(conditional: only Task 1's boundary-pin re-key arm; byte-unchanged when the suite reports no new delta)*
- docs/history/backlog/2026-10-17-parked-run-input-fallback-option.md *(landing rider: deletion)*
- docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md *(landing rider: Cluster-pointer tidy only)*
- docs/history/backlog/2026-10-17-parked-run-durable-record-residue.md *(landing rider: Cluster-pointer tidy only)*
- docs/history/backlog/2026-10-17-investigate-user-directed-gate-workaround.md *(landing rider: Cluster-pointer tidy only)*
- docs/history/backlog/PLAN-PROMPTS.md *(landing rider: own-entry prune with receipt)*

**Tests:**
- none new; the validation battery below is the verification surface

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. A pins-suite delta caused by an insertion boundary is in scope only as the pin re-key named in Task 1. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the three sibling entries' span surfaces (the summary-handoff delivery contract and park-time mirror, the durable-record vehicle, the user-directed-gate-workaround caller policy); reason: the dispatch entry's span split assigns them to their own entries
- agents/skills/execute-plan/subagent-prompts.md; reason: the arm changes parent-side task-handling text only
- review-loop machinery, review-panel-selection rosters, and any validator or gate script; reason: no gate or panel change is in scope

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/plan_readiness.py docs/history/plans/2026-10-18-plan-declared-missing-input-fallback.md --pre-round
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md
diff agents/skills/execute-plan/SKILL.md "$HOME/.agents/skills/execute-plan/SKILL.md"
diff agents/skills/plans/SKILL.md "$HOME/.agents/skills/plans/SKILL.md"
```

### Task 1: the execute-plan plan-declared missing-input fallback arm

Context surface: the plan's Terms and this task.

Files:
- agents/skills/execute-plan/SKILL.md
- scripts/check_maintenance_pins.sh *(conditional: only the boundary-pin re-key arm below; byte-unchanged when the suite reports no new delta)*

- [x] Run the pins suite at the pre-change HEAD and record its full tail (the OUTCOME line plus every PIN FAIL and suppressed-recorded-reds line) in the session manifest as the recorded baseline. [class: REPOSITORY_TEST]
- [x] Insert a `Plan-declared missing-input fallback` subsection between the Inclusion Hard Gate section and the Step 1.2 heading. [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the applicability condition: the arm applies only when the plan declares the fallback naming all four fields (condition, degraded outputs, indeterminate-recording duty, disclosure duty). [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the precedence: a fired declared condition is decided before the Inclusion Hard Gate's pause outcomes are selected for the covered item and is applied instead of them, and the same rule holds when the Recovery path re-applies the gate to the task's items. [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the fired-condition behavior: the run applies the fallback in-run, produces only the degraded outputs, records affected classifications as indeterminate in the session manifest, and names the fired condition and the degradation in the session manifest and the closeout report, then continues. [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the fired item's completion: the affected checklist items are marked complete on their produced degraded outputs with the session manifest carrying that record; the marking is recorded and disclosed, never a silent skip. [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the validation accounting: the recorded fired-fallback disposition in the session manifest is the verification record for validation commands whose inputs the fallback skipped (recorded as fallback-skipped, never failed), the passing subset still runs and passes, and the standing verification gate and the Phase 2 accounting read that record instead of re-running or fix-looping the skipped commands. [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the evaluation window and the fixed disposition: the arm is evaluated only at Inclusion Hard Gate invocation, including the Recovery path's re-invocation, on absences determinable at that point; a task's disposition is fixed at its first evaluation and recorded in the session manifest, and a resumed or Recovery pass reads the recorded firing, or its absence, from the session manifest instead of re-deciding. [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the absence boundary: an undeclared absence or an absence outside the declared condition leaves the Inclusion Hard Gate's standing outcomes unchanged; a declaration whose condition lacks an exact checkable shape is not applicable, and any doubt resolves to the standing outcome, never to firing. [class: IMPLEMENTATION_REQUIRED]
- [x] The subsection states the authority boundary: the arm authorizes no plan, gate, or validator edit mid-run, and the Checklist inclusion gate's admission semantics are unchanged because the arm disposes only the absence, never admitting an external prerequisite as executable. [class: IMPLEMENTATION_REQUIRED]
- [x] Sync the vendored twin byte-equal in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the arm's heading phrase is absent from the skill and its twin before the edit. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the heading phrase, the precedence sentence, and the undeclared-absence boundary sentence (the contiguous span `undeclared absence`) verify in the skill and its twin after the edit, and diff against the twin exits 0. [class: REPOSITORY_TEST]
- [x] Boundary witness: given the pins suite run after the change, its failing set equals the recorded baseline; a new failure caused by an insertion boundary is re-keyed inside this change as the only sanctioned pins-suite edit, with the re-key recorded in the session manifest. [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan plan-declared missing-input fallback arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the plans skill external-input authoring bullet

Context surface: the plan's Terms and this task.

Files:
- agents/skills/plans/SKILL.md

- [x] Extend the Step 1.2 External dependencies confirmation element with one sentence encouraging a bounded missing-input fallback declaration, referencing execute-plan's plan-declared missing-input fallback arm and the four fields that arm requires, for an operator-provided input artifact the run consumes. [class: IMPLEMENTATION_REQUIRED]
- [x] The sentence states the declaration scopes only the absence response and never admits an external prerequisite as executable, so the Checklist inclusion gate's admission semantics are unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Sync the vendored twin byte-equal in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the literal `plan-declared missing-input fallback arm` is absent from the skill and its twin before the edit. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the literal verifies in the skill and its twin after the edit, and diff against the twin exits 0. [class: REPOSITORY_TEST]
- [x] Commit: `feat: plans skill missing-input fallback declaration guidance` [class: IMPLEMENTATION_REQUIRED]

### Task 3: boundary, span, and validation battery

Context surface: the plan's Terms and this task.

Files:
- agents/skills/execute-plan/SKILL.md (read-only verification)
- agents/skills/plans/SKILL.md (read-only verification)

- [x] Verify the landing diff carries exactly the hunks the task lists prescribe, nothing else in either skill. [class: REPOSITORY_TEST]
- [x] Verify the sibling span surfaces are untouched: the delivery-contract, record-filing, and caller-policy text carries no changes from this plan; the only sanctioned sibling-row delta is the landing closeout's Cluster-pointer tidy at the removed row. [class: REPOSITORY_TEST]
- [x] Exercise the landed subsection against two fresh-run sample contexts and record both outcomes in the session manifest: one where a declared condition covers the absence (expect degrade-only-declared-outputs, indeterminate recording, session-manifest and closeout disclosure, and continuation) and one where the absence falls outside the condition or a field is missing (expect the standing park). [class: REPOSITORY_TEST]
- [x] Exercise the resume read-back with a third sample context and record the outcome in the session manifest: a resumed or Recovery pass facing a task whose fired disposition the session manifest already records expects the recorded disposition read back and honored (continuation without re-deciding), and a pass facing no recorded disposition expects fresh evaluation. [class: REPOSITORY_TEST]
- [x] Run the full validation battery: the pins suite failing set equals the recorded baseline (after Task 1's sanctioned re-key if it fired), the hygiene scan exits 0, the em-dash file-mode scan on the two touched skills is clean, and the readiness pre-round reports no blocking problem. [class: REPOSITORY_TEST]
- [x] Record the task's verification-only closure in the session manifest (this task stages nothing; the recorded baseline and all three sample-context outcomes are its evidence). [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-17-parked-run-input-fallback-option.md: the landing closeout (the authoring session's landing commit, outside task scope) deletes this row per the repository guidelines' backlog-completion rule, naming this landed plan as the witness, and tidies the removed row's Cluster back-references in the three sibling rows in the same change, and prunes this plan's own dispatch entry from PLAN-PROMPTS.md with the `PLAN-PROMPTS-PRUNE: plan-declared-missing-input-fallback -> docs/history/plans/2026-10-18-plan-declared-missing-input-fallback.md` receipt line and a prune-audit pass; the row's problem, expected, and suggested-direction substance is folded into this plan's Why, Gist, and Tasks.
