# Plan: Certification Gates Report All Violations in One Exit

Executed: yes (385bebf19)

Authoring claim: 2026-11-03-certification-gates-sequential-reporting-churn.md (session sess_da6fb9e7-3b0e-4bce-a6c6-d6984827a07a)

Backlog origin: docs/history/backlog/2026-11-03-certification-gates-sequential-reporting-churn.md
Driving force: efficiency (primary; one sequential violation report costs a full fix-then-rerun review round per defect), token-usage (secondary; multi-worker rounds re-run once per hidden violation)
Plan review record: the staging series .ai-playbook/reviews/2026-11-03-plan-review-certification-gates-full-violation-reporting-peca47cdd-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3h total, largest task 1.5h

## Terms

- first-failure exit: a gate that stops at its first violation and reports only that violation before exiting non-zero.
- full-violation reporting: one gate pass enumerates every violation with per-violation evidence before the single non-zero exit; exit codes and pass/fail verdicts unchanged, except the one deliberate flip: a mixed indeterminate-plus-failure input moves from exit 1 to exit 2 per the done sweep's indeterminate-dominates rule.
- readiness gate: `scripts/plan_readiness.py`, the plan certification validator (`evaluate_readiness`, `run_pre_round`, `_main` reporting).
- staging validator: `scripts/validate_review_staging.py`; its `ValidationResult.errors` accumulation and its hard mode.
- cascade suppression: the staging validator's single-reporter rule; when a record's prerequisite data is malformed, the gate owning the prerequisite reports its error and the dependent gates' diagnostics stay suppressed as a cascade; this plan removes the silence, not the suppression, by rendering an explicit skip note naming each suppressed dependent diagnostic.
- run-id chain rule: the staging validator refusal "run_id cannot change after r1 in the same artifact chain"; the accepted form carries the run_id minted at r1 forward unchanged in later rounds.
- contract naming: a refusal or warning message that states the accepted forms when a caller-supplied value is rejected or out of set (run-id chain, discard-code set, identity-qualified filename pattern).
- identity-qualified filename: the `-p` plus eight hex plus `-r<N>` record filename token enforced in `validate_staging_file`.
- evidence item byte cap: `MAX_EVIDENCE_ITEM_BYTES = 512` in `scripts/runtime_capabilities.py`, enforced by `evidence_criterion_ids` and named by the `execute_plan_runtime` evidence-limit wrapper.
- authoring-time preflight: running every pinned validation command in the plan's own Validation Commands block once over the plan bytes before the first review round; the plans skill's rule 29 duty, generalized from its mechanical-gate subset.
- harvest window: the 2026-11-02 07:00 to 2026-11-03 07:15 UTC session-pattern harvest window the origin row's evidence section covers.
- certification churn: the per-violation fix-then-rerun round cost a certification run pays when its gates report one violation at a time.
- many-violation fixture: a test fixture planting several violations of different gate families in one artifact, asserting one exit enumerates all of them.

## Why

Certification gates stop at their first violation, so a run with several defects pays one full fix-then-rerun round per defect. In the harvest window the origin row covers, landing subjects certified at r2 through r8, later-round workers re-derived the accepted run-id form by trial in four of seven reviewed sessions, and a byte-cap fold missed a second over-cap item and re-failed the gate at r3.

## Gist & Examples

TLDR: the readiness and staging validators report every violation of one pass in one enumerated report before their single non-zero exit, shape refusals name their accepted forms, and cascade-suppressed staging diagnostics are named in skip notes, so one defect no longer hides the rest.

Before: the readiness gate reports the first failed condition only, so a plan with four structural defects is refused, folded, and re-refused across four review rounds. A staging record whose prerequisite data is malformed gets the owning gate's error but no line naming which dependent checks did not run. The run-id chain rejection states the rejection but not the accepted form, so every later-round worker re-derives it by trial.

After: the same failing input prints every failed condition with its evidence in one report and exits non-zero once; `run_pre_round` prints the full problem set; the shared sidecar gate's full error list reaches the readiness report with each error routed through the existing family classifier; cascade-suppressed diagnostics carry explicit skip notes. Refusals that reject a caller-supplied shape name the accepted form beside the rejection, and the byte-cap refusal lists every over-cap criterion with its size on the wrapped path authors actually see. Fail-closed semantics do not change: the same inputs fail, the same inputs pass, only the report width grows.

## Outcome

One pass over the certification gates enumerates every violation with evidence, and a caller can read the accepted record form from the refusal or warning itself.

- A plan failing several readiness checks is refused once, with every failed check and its evidence in one report; the passing set still passes.
- The staging validator renders a skip note naming each cascade-suppressed dependent diagnostic beside the owning gate's error, so a malformed prerequisite no longer silently hides which later checks did not run.
- Refusals for the run-id chain rule and the identity-qualified filename name their accepted forms, the unknown-discard-code warning names the accepted code set, and the byte-cap refusal lists every over-cap criterion with its size on the wrapped path.
- The plans skill's authoring flow runs every pinned validation command in the plan's own Validation Commands block once before the first review round, so mechanical defects surface before any review round pays for them.
- Gate delta: reporting-shape widening inside the readiness gate, skip-note rendering beside two existing staging suppression points, contract naming on two existing refusal texts and one existing warning text, and one enumeration widening inside the existing byte-cap check and its wrapper; no new gate, fence, refusal class, schema field, or protocol layer, and no refusal-class or checked-set growth (the same conditions fail; only the report widens); one prose-only authoring preflight duty widened in the plans skill from its mechanical-gate subset to every pinned command, priced by the origin row's completed witnesses (the r2-r8 churn, the run-id rejection in four of seven sessions, the re-tripped byte cap) and by the rule 29 precedent family (the byte-balance preflight, six witnesses in the harvest window); removals: the silent cascade suppression's report gap (the suppression itself stays; only its silence is removed); blocking review-layer duties: none.

## Assumptions

- Filing class re-derivation: the origin declares Class: fix-class and its body records a reporting defect that converts N defects into N rounds; these arms widen existing reports, refusal texts, and warning text without adding a refusal class or checked condition, so the fix-class refusal-path addition justification does not apply.
- Origin arm 2's round-kind enum member is excluded from the naming slice: the enum refusal already names its accepted member list, so no naming arm is needed there; the identity-qualified filename naming arm replaces it in scope.
- The staging validator already accumulates every independently evaluable gate's errors in one hard-mode pass (landed by the completed 2026-10-22 review-staging fail-fast iteration plan); the staging-side residual this plan removes is the cascade suppression's silence, not missing enumeration.
- `evaluate_readiness` callers consume an `(ok, reason)` pair; the accumulation renders all violations through the existing reason channel as an enumerated multi-line reason, so caller signatures stay stable while the report widens; prerequisite gates stay stop-further-descending checks with explicit skip notes, and an indeterminate problem is never aggregated; the sidecar schema and kind pre-checks stay stop-further with the shared gate as their single reporter under the widening, and discovery failures stay prerequisite-class.
- The byte-cap refusal text is a pinned dispatch key; every extension keeps the existing needle bytes as a contiguous prefix and keeps the message a deterministic function of its inputs, so exact-equality attribution in consumer modules keeps matching.
- The plan delta classifier's unclassified-hunk default stays unchanged: its refusal already enumerates every non-exempt hunk (the bad-hunk list in `exempt_verdict`), and the fresh five-worker round is the sanctioned re-verification instrument for plan-integrity deltas; re-pricing the default needs a witnessed basis this origin does not carry.
Decision points requiring a grill: none remain.

## Standing constraints

- Fail-closed semantics are unchanged by every task: the same inputs fail and the same inputs pass after each task; only report width and refusal text grow (reporting order only).
- No new gate, validator, lock, ledger, or required ceremony; the origin's machinery-admission note prices reporting changes inside existing gates as needing no admission test.
- Pinned refusal needles stay byte-identical: every message this plan extends keeps its existing text as a contiguous prefix of the extended form and stays a deterministic function of its inputs, so substring dispatch and exact-equality attribution in consumer modules keep matching.
- Skill-text edits stay runtime-neutral and tool-agnostic; behavior is described by intent, never by tool or agent-type name.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every planted violation in a many-violation fixture appears in the one non-zero exit's report, per changed gate family; existing single-violation and pass behaviors stay green across the three pinned suites and both embedded selftests.
- compatibility: `(ok, reason)` callers and `validate_staging_file` callers keep their contracts; the soft mode, single-violation records, and the frozen hard-mode emission order behave as before.
- maintainability: the enumeration reuses each script's existing accumulation machinery (`run_sweep`'s list pattern in the readiness gate; `ValidationResult.errors` in the staging validator); no parallel reporting channel is added.

**Done when:**
- The three pinned suites pass with the new many-violation fixtures, and both embedded selftests pass.
- A fixture-driven refusal output shows every planted violation's evidence in one exit for each changed gate family.
- The plans skill's authoring flow names the pinned-command preflight execution before round 1, and rule 29's language covers every pinned command in the plan's own Validation Commands block.
- The repository hygiene scan and the no-em-dash scan pass over the touched set; the readiness pre-round gate passes on this plan's own bytes.

**Ship when:**
- No external prerequisites and no release gate; the change is repository-internal.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (Task 1)
- `scripts/plan_readiness.py` (Task 3)
- `scripts/validate_review_staging.py` (Task 2)
- `scripts/validate_review_staging.py` (Task 3)
- `scripts/runtime_capabilities.py` (Task 3)
- `scripts/execute_plan_runtime.py` (Task 3)
- `agents/skills/plans/SKILL.md` (Task 4)
- `agents/skills/plans/validation-authoring-rules.md` (Task 4)

**Tests:**
- `scripts/test_plan_readiness.py` (Task 1)
- `scripts/test_step31_record_validation_gate.py` (Task 2)
- `scripts/test_step31_record_validation_gate.py` (Task 3)
- `scripts/test_runtime_capabilities.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_delta_classifier.py`; reason: the recorded decision keeps the classifier default unchanged, so no byte of it changes in this plan.
- `README.md` and `docs/history/` archive rows; reason: no catalog or archive surface belongs to this reporting fix.

## Validation Commands

Authoring-time evidence (recorded before round 1 per authoring rule 29): the touched no-em-dash scan, the public-hygiene scan, and the readiness pre-round gate were executed over this plan's bytes and passed; the rule 22 mechanical audit over pinned spans and the `bash -n` syntax check over this block passed at authoring time; the Task 4 target-state pins were executed against the current files and confirmed RED (absent), and the superseded-wording negation pin was executed and confirmed its fail polarity (the phrase still present, so the pin fires until Task 4 lands).

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
export PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH"
python3 -m pytest scripts/test_plan_readiness.py -q || { echo "FAIL: readiness suite"; exit 1; }
python3 -m pytest scripts/test_step31_record_validation_gate.py -q || { echo "FAIL: staging gate suite"; exit 1; }
python3 -m pytest scripts/test_runtime_capabilities.py -q || { echo "FAIL: runtime capabilities suite"; exit 1; }
python3 scripts/plan_readiness.py --selftest >/dev/null || { echo "FAIL: readiness selftest"; exit 1; }
python3 scripts/validate_review_staging.py --selftest >/dev/null || { echo "FAIL: staging selftest"; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins"; exit 1; }
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em-dash scan"; exit 1; }
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || { echo "FAIL: hygiene scan"; exit 1; }
( cd "$REPO" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-03-certification-gates-full-violation-reporting.md ) || { echo "FAIL: pre-round gate"; exit 1; }
grep -qF "run every pinned validation command in the plan's own Validation Commands block once over the plan bytes before the first review round" agents/skills/plans/SKILL.md || { echo "FAIL: preflight duty pointer missing"; exit 1; }
grep -qF "Run every pinned validation command in the plan's own Validation Commands block over the plan bytes before the first review round" agents/skills/plans/validation-authoring-rules.md || { echo "FAIL: rule 29 widened duty missing"; exit 1; }
if grep -qF "Run the repo's cheap mechanical format gates over the plan bytes before the first review round" agents/skills/plans/validation-authoring-rules.md; then echo "FAIL: superseded narrow scope still present"; exit 1; fi
grep -qF "naming every failed condition" agents/skills/plans/SKILL.md || { echo "FAIL: verdict sentence not widened"; exit 1; }
grep -qF "the enumerated violation report on stderr" agents/skills/plans/validation-authoring-rules.md || { echo "FAIL: rule 29 exit-1 wording not widened"; exit 1; }
```

### Task 1: Readiness gate enumerates every failed condition

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

Primary class anchors:
- `evaluate_readiness` in `scripts/plan_readiness.py`
- `run_pre_round` in `scripts/plan_readiness.py`

- [x] Full enumeration witness: given a plan fixture violating at least three independent readiness checks, expects one `evaluate_readiness` call returning every violation with each check's evidence in the reason channel, not only the first [class: REPOSITORY_TEST]
- [x] Shared-gate widening witness: given a record whose sidecar validation produces multiple errors, expects every error line present in the readiness report with each error routed through the existing family classifier, instead of only the first element [class: REPOSITORY_TEST]
- [x] Pre-round full-problem witness: given a plan violating several pre-round probes, expects one `run_pre_round` invocation printing every probe failure and exiting 1 once [class: REPOSITORY_TEST]
- [x] CLI full-report witness: given the multi-violation fixture driven through the main entry, expects each planted violation's evidence substring in the captured stderr with the `OUTCOME: fail` tail intact [class: REPOSITORY_TEST]
- [x] Fence-suppression safety witness: given a plan with an unbalanced fence plus plantable later-probe violations, expects only the fence reason plus explicit skip notes naming the suppressed probes at one exit 1, never probe output derived from truncated text and never an exception escape [class: REPOSITORY_TEST]
- [x] Indeterminate-exclusivity witness: given an indeterminate graded condition plus an independent deterministic violation, expects exit 2 with the indeterminate prefix at position 0 of the reason, mirroring the done sweep's indeterminate-dominates rule [class: REPOSITORY_TEST]
- [x] Exit-vocabulary stability witness: given a violation-free plan, expects the existing pass path unchanged; given an indeterminate condition alone, expects exit 2 unchanged [class: REPOSITORY_TEST]
- [x] RED: run `scripts/test_plan_readiness.py` and observe the new enumeration, suppression, and exclusivity witnesses fail against the first-failure implementation [class: REPOSITORY_TEST]
- [x] Implement the accumulation: collect each independently computable check's problem in gate order into the reason channel, render the full set in the `readiness FAILED:` output and the pre-round report, and route every sidecar error through the family classifier; prerequisite gates (operand resolution, fence balance, sidecar readability, plan-byte decode) stay stop-further-descending checks that contribute their reason with explicit skip notes for suppressed dependents [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the accumulation invariants: an indeterminate problem never aggregates and renders as the sole reason with the prefix at position 0; refresh the reason-semantic docstrings (the module docstring's exit-contract sentence, `evaluate_readiness`'s, and `run_pre_round`'s) to the enumerated semantics, leaving `check_review_name`'s first-failure sentence unchanged; every check's condition and every verdict stays identical [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite the first-error legacy pin: update the coexistence test that asserts exactly the `errors[0]` family so it asserts every routed family appears in the accumulated reason while the per-family classifier keeps its mapping coverage [class: REPOSITORY_TEST]
- [x] GREEN: `scripts/test_plan_readiness.py` and the readiness embedded selftest pass, including the new witnesses; legacy expectations stay unchanged except the named first-error pin, which the rewrite item updates [class: REPOSITORY_TEST]
- [x] Commit: `scripts: readiness gate reports every failed condition in one pass` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Staging validator names each cascade-suppressed dependent diagnostic

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/validate_review_staging.py`
- `scripts/test_step31_record_validation_gate.py`

Primary class anchors:
- `validate_staging_file` in `scripts/validate_review_staging.py`
- `_validate_stats_sidecar_gates` in `scripts/validate_review_staging.py`

- [x] Skip-note witness: given a record whose sidecar prerequisite data is malformed, expects the owning gate's error accompanied by explicit skip notes naming each cascade-suppressed dependent diagnostic, never silent suppression and never an exception escape [class: REPOSITORY_TEST]
- [x] Emission-order stability witness: given a fully valid record and a record whose errors are all independently evaluable, expects outputs shaped as today with the frozen emission order preserved, the skip notes adding lines only where a suppression actually occurred [class: REPOSITORY_TEST]
- [x] Soft-mode compatibility witness: given the soft-mode invocation and a single-violation record, expects the current output shape and exit codes unchanged [class: REPOSITORY_TEST]
- [x] RED: run `scripts/test_step31_record_validation_gate.py` and observe the skip-note witness fail against the silent suppression [class: REPOSITORY_TEST]
- [x] Implement the skip notes: at the sidecar-gate chain's dependency sequencing point and the self-heal chain walk's first-refusal stop, render one explicit skip note naming each suppressed dependent diagnostic beside the owning gate's ERROR line as a WARN-line warning on the warnings channel, never an errors-list entry, so every embedded selftest pin stays green; the suppression itself, the gate set, the frozen emission order, and every verdict stay identical [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: the staging gate suite, the readiness suite, and both embedded selftests pass with the frozen emission-order pin and legacy expectations unchanged [class: REPOSITORY_TEST]
- [x] Commit: `scripts: staging validator names cascade-suppressed diagnostics in skip notes` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Refusal contract naming and byte-cap enumeration

Context surface: the plan's Terms, this task, and `## Standing constraints` (the pinned-needle constraint binds this task).

Files:
- `scripts/validate_review_staging.py`
- `scripts/runtime_capabilities.py`
- `scripts/execute_plan_runtime.py`
- `scripts/plan_readiness.py`
- `scripts/test_step31_record_validation_gate.py`
- `scripts/test_runtime_capabilities.py`
- `scripts/test_plan_readiness.py`

Primary class anchors:
- `_validate_self_heal_record` in `scripts/validate_review_staging.py`
- `validate_discarded_findings` in `scripts/validate_review_staging.py`
- `evidence_criterion_ids` in `scripts/runtime_capabilities.py`

- [x] Run-id accepted-form witness: given a later round whose run_id differs from r1's, expects the refusal to state that r1's run_id carries forward unchanged beside the existing rejection, the original sentence kept byte-identical as its prefix [class: REPOSITORY_TEST]
- [x] Discard-code accepted-set witness: given a discard reason outside the accepted set, expects the unknown-discard-code warning to list the accepted codes, the warning class and the passing verdict unchanged [class: REPOSITORY_TEST]
- [x] Filename-pattern witness: given a record whose sidecar declares extensions.plan_identity while its filename lacks the identity token, validated with --source-plan set, expects the refusal to name the required identity-qualified filename shape [class: REPOSITORY_TEST]
- [x] Byte-cap wrapped-refusal witness: given a plan with two criteria over the 512-byte cap driven through the pre-round path, expects one wrapped refusal naming both over-cap items with their sizes, the bare needle kept byte-identical as its prefix [class: REPOSITORY_TEST]
- [x] RED: run the three pinned suites and observe the accepted-form, warning-set, and enumeration witnesses fail against the current refusal texts and first-offender wrapper [class: REPOSITORY_TEST]
- [x] Implement the naming: prefix-extend the run-id and filename refusal messages with their accepted forms and extend the discard warning with the accepted code set, keeping each existing needle byte-identical as the prefix and each message a deterministic function of its inputs [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the byte-cap enumeration: enumerate every over-cap item with its size in the byte-cap check and widen the evidence-limit wrapper to name every over-cap item instead of the first offender; refusal classes, warning classes, verdicts, and exit codes unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: the three pinned suites, both embedded selftests, and the maintenance pins battery pass with legacy expectations unchanged [class: REPOSITORY_TEST]
- [x] Commit: `scripts: record-shape refusals name their accepted forms` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Authoring preflight duty covers every pinned validation command

Context surface: the plan's Terms, this task, and `## Standing constraints`. This task owns no production behavior; it widens the plans skill's authoring-time duty text, so it declares no primary class anchors.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/plans/validation-authoring-rules.md`

Prescribed landing snippets (the Validation Commands pins audit these spans; the superseded-wording negation pin proves the deletion):

- `agents/skills/plans/SKILL.md` gains exactly one pointer sentence beside the rule 29 reference: "The authoring-time preflight is owned by rule 29 in `agents/skills/plans/validation-authoring-rules.md`: run every pinned validation command in the plan's own Validation Commands block once over the plan bytes before the first review round, and record the outcomes in the Validation preamble."
- `agents/skills/plans/validation-authoring-rules.md` rule 29's opening sentence is replaced by: "Run every pinned validation command in the plan's own Validation Commands block over the plan bytes before the first review round:" with the existing mechanical-gate list introduced as members of that set, and the rule's exit-1 clause reads "the enumerated violation report on stderr" instead of "the first structural failure on stderr".
- `agents/skills/plans/SKILL.md`'s readiness-verdict sentence reads "naming every failed condition" where it reads "naming the first failed condition" today.

- [x] Preflight duty pointer: land the SKILL.md pointer sentence byte-identical to the prescribed snippet, adding no other operative restatement of the duty [class: IMPLEMENTATION_REQUIRED]
- [x] Rule 29 widening and narrowing-word deletion: land the replacement opening sentence and the exit-1 wording byte-identical to the prescribed snippets, deleting the superseded "cheap mechanical format gates" scoping in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Verdict-sentence widening: land the readiness-verdict sentence edit byte-identical to the prescribed snippet [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: the Validation Commands block's target-state pins for the two widened sentences and the pointer pass, the superseded-wording negation pin flips to its pass polarity, and the em-dash and hygiene scans stay green over the touched skill text [class: REPOSITORY_TEST]
- [x] Commit: `plans: authoring preflight duty covers every pinned validation command` [class: IMPLEMENTATION_REQUIRED]

## Execution record

Executed 2026-11-06 by sess_9bd4deb5-c924-4ff4-ac22-e5506e64d056 (zcode runtime) via stale-claim takeover: the original execution run (codex session 01a1acdb, claim updated 2026-11-05T23:42:20Z, no run manifest, no marked checkboxes) had landed all four task commits on the registered branch (2026-11-05-certification-gates-full-reporting) before going silent; the takeover adopted the registered worktree and branch unchanged, re-verified every pinned Validation Command green (readiness, staging-gate, runtime-capabilities suites; both embedded selftests; maintenance pins battery; em-dash and hygiene scans; pre-round gate; the five Task 4 target-state pins), marked the checkboxes, and proceeds to Phase 3 review. The RED-step observations were performed by the original run per its commit sequence (each task commit pairs its witnesses with the implementation).

Phase 3 (2026-11-06): exec r1 fresh-adversarial two-lens panel returned zero blocking findings (record .ai-playbook/reviews/2026-11-06-plan-review-certification-gates-full-violation-reporting-exec-r1{.md,.stats.json}); address round 16b8f5efc fixed the Low items (comment stub, exit-1 fence pins, migrate-skeleton row closure) and deferred two Mediums to durable rows. Scoping decision (skip notes): the notes name within-gate suppressions only; the four caller-side sidecar-dependent consumers are named in the deferred scope row, not the tuples. The exclusivity witness's RED claim is scoped to the enumeration/suppression witnesses; the mixed-input exclusivity witness is the deferred row's deliverable.

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-03-certification-gates-sequential-reporting-churn.md (covered origin): deleted at this execution landing; the plan's four tasks discharged the reporting defect family the row captured (readiness/staging full-violation enumeration, refusal contract naming, authoring preflight widening); two non-blocking review residuals were re-filed as their own rows (2026-11-06-readiness-indeterminate-mixed-input-witness.md, 2026-11-06-staging-skip-note-scope-caller-side-consumers.md) and the invocation-telemetry baseline red as 2026-11-06-invocation-telemetry-finalize-pin-recapture.md; the migrate-skeleton stdout-assertion row was closed in-run by the branch's 0f198bff3 fix.
