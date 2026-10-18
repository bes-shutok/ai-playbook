# Plan: pre-round gate runs the plan-private executability probes

Backlog origin: docs/history/backlog/2026-10-12-full-gate-plan-private-dimensions-pre-round.md
Driving force: efficiency
Plan review record: the staging series docs/history/reviews/2026-10-12-plan-review-pre-round-gate-dimension-parity-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- pre-round gate: the structural-only authoring invocation `python3 scripts/plan_readiness.py --pre-round <plan-path>` (plans skill rule 29), run before the first review round launches.
- full gate: the certification-time readiness invocation `python3 scripts/plan_readiness.py <plan-path>` over the assembled review series; it owns the step 9 executability parity check today.
- step 9: the extraction-rule executability parity step inside `evaluate_readiness` in `scripts/plan_readiness.py`, positioned there by the contract-single-sourcing landing.
- bounded-evidence envelope: the per-criterion 512-byte item cap and the per-task 4096-byte aggregate cap on acceptance-criteria evidence, single-homed in `scripts/runtime_capabilities.py` (`MAX_EVIDENCE_ITEM_BYTES`, `MAX_EVIDENCE_BYTES`), enforced inside the evidence-criterion-ids check of the extraction-rule executability probes (the canonical partition; the Gist and the prescribed rule 29 text cite this form).
- extraction-rule executability probes: the three shared-module checks step 9 runs over each derived task section (checklist action classification, checklist action derivation, evidence criterion ids) plus the named refusal wrapper.
- plan-private dimension: a gate check derivable solely from the plan file bytes, never from a review record.
- named refusal shape: the task-attributed refusal text the create boundary and step 9 print for envelope breaches, built by `execute_plan_runtime._named_evidence_limit_error`.
- create boundary: the execute-plan driver's Phase 0 discovery that refuses unexecutable plans at execution start.
- clone-signature component: the one step 9 input derived from discovery-produced verification commands, not derivable from plan bytes; the documented create-boundary-only residual.
- derived task section: a `### Task N:` section body whose acceptance criteria and checklist actions `runtime_capabilities.derive_plan_checklist_actions` extracts.
- OUTCOME contract: the four-outcome vocabulary of `scripts/OUTCOME_CONTRACT.md` (pass, fail, indeterminate, tool_error), read as exit code plus final line.

## Why

Certified plans still refuse at the done boundary on checks that read only the plan bytes: step 9 runs only at certification, while the authoring-time pre-round gate skips it. The boundary-reliability plan passed pre-round, certified, then burned review rounds 11 through 13 on a 597-byte evidence criterion and over-cap aggregates, and the execution side hit the same defect class with a 558-byte criterion. Running the plan-private subset at pre-round turns those refusals into authoring-time fixes.

## Gist & Examples

TLDR: the authoring-time pre-round gate gains the full gate's plan-private probes (the extraction-rule executability checks whose evidence-criterion-ids arm enforces the bounded-evidence envelope), so plan-derivable refusals surface before round one instead of after certification; driving force efficiency.

Before: a plan whose evidence criterion is 597 bytes passes `--pre-round`, survives review and certification, then refuses at the done boundary with "evidence criterion exceeds UTF-8 item byte limit"; recovering costs fresh review rounds over a one-line fix.

After: the same plan fails `--pre-round` before round one with the byte-identical named refusal; the author splits the criterion and no review round is spent.

Edge cases: a plan with no review record still gets the full probe set because the probes never consult one; a derived task section with no acceptance criteria stays skipped exactly as step 9 skips it (the create boundary's discovery refuses that class first); the clone-signature component remains outside the pre-round set.

## Outcome

A plan author sees the full gate's plan-private refusals at authoring time, before the first review round launches.

- Evidence criteria over the 512-byte item cap or the 4096-byte aggregate cap refuse at `--pre-round` with the same named label the full gate and the create boundary print.
- Checklist action classification defects refuse at `--pre-round` instead of surfacing at certification or Phase 0; the derivation arm stays a create-boundary discovery-path residual beside the clone-signature component.
- The full gate's verdicts and refusal strings stay identical; the pre-round mode remains review-record-blind and keeps its outcome contract.

Gate delta: one existing gate's refusal surface grows (the pre-round mode gains the step 9 refusal classes); no new gate, validator, ledger, schema field, fence, or protocol layer; the full gate's behavior is unchanged. Pricing: completed-integrity-failure witness (a certified plan refused at the done boundary and burned rounds twice in the 2026-10-10 to 2026-10-12 window; origin row docs/history/backlog/2026-10-12-full-gate-plan-private-dimensions-pre-round.md and lesson 36 in docs/maintenance/development_lessons.md); the origin row's rejected-alternatives record prices the alternatives. Measured corpus refusal rate at authoring time (r1 review panel probe over the plans corpus, docs/history/reviews/2026-10-12-plan-review-pre-round-gate-dimension-parity-r1.md): 7 of 16 existing plans refuse on the extended probes, 3 of 4 deferred plans, active-plan headroom as thin as 501 of 512 item bytes and 4048 of 4096 aggregate bytes; every refusal is a true positive under the envelope the create boundary already enforces. Guard liveness ledger at authoring time (`python3 scripts/gate_liveness_ledger.py show`, 2026-10-12): plan-readiness catches=0 incidents=1.

## Assumptions

- assume the step 9 derived-task loop is extracted into one module-level helper in `scripts/plan_readiness.py` that both step 9 and `run_pre_round` call, rather than duplicated; basis: the probes stay single-homed by construction and the origin prompt forbids duplicating the shared-module probes.
- assume the shared-module helpers are called verbatim and the 512/4096 constants are never retuned; basis: `scripts/runtime_capabilities.py` pins the constants as single-homed and the origin prompt forbids retuning.
- assume the pre-round probe set is exactly the plan-derivable subset of step 9 (the three extraction-rule components; the clone-signature component remains create-boundary-only); basis: step 9's position comment records that residual explicitly.
- assume the full gate's verdicts are unchanged: the refactor only re-homes the loop into a helper with byte-identical refusal strings, proven by `scripts/test_plan_readiness.py`'s `ExtractionRuleParityTest` staying green unmodified; basis: the origin prompt's outcome contract.
- assume Phase 1 confirmation is satisfied by the operator's standing pre-authorization for authoring runs, with the PLAN-PROMPTS entry prompt as the scope of record; basis: interactive operator directive 2026-10-12 ("keep authoring plans one by one") and the authoring dispatch template's standing pre-authorization.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: for the same plan bytes, the pre-round refusal text on an envelope breach is byte-identical to step 9's label (same wrapper, same task attribution).
- review blindness: the pre-round mode never reads the reviews home or any sidecar; the OK line keeps its "(review record not consulted)" suffix.
- parity: every plan step 9 refuses on the plan-private arms reachable from plan bytes (the three envelope grounds plus the classification arm) fails `--pre-round` with the same named condition, and every plan step 9 passes keeps passing.
- outcome contract: `--pre-round` keeps exit 0 with the OK line and exit 1 with the first `readiness PRE-ROUND FAILED:` line on stderr; budget warnings still emit only after every probe passes.

**Done when:**
- `python3 scripts/plan_readiness.py --selftest` passes with the new fixtures: an over-cap criterion plan fails `--pre-round` with the named envelope label, sibling fixtures refuse on the aggregate and count grounds with their own labels, and a conforming plan still prints the OK line; the classification and derivation labels are witnessed at unit level over the extracted helper, mirroring `scripts/test_plan_readiness.py`'s classification parity test.
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-12-pre-round-gate-dimension-parity.md` prints OK over the landed plan bytes.
- `agents/skills/plans/SKILL.md` rule 29 names the added probe set and the clone-signature residual, and the readiness-boundary summary names the new defect class (the per-site split Task 2 prescribes).
- `python3 scripts/test_plan_readiness.py ExtractionRuleParityTest` passes unmodified: the existing step 9 parity fixtures are the witness that no `evaluate_readiness` step's verdict or refusal string changed.

**Ship when:** none; the change is repository-verifiable only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`

**Documentation:**
- `agents/skills/plans/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/runtime_capabilities.py`; reason: the constants and probe helpers are single-homed read-only reuse here; a finding there is a separate change.
- `scripts/execute_plan_runtime.py`; reason: the named-refusal wrapper is imported read-only; its behavior is the create boundary's contract.
- `docs/maintenance/development_lessons.md`; reason: lesson 36 is the landed record of the motivating incident and is cited, not edited.

## Validation Commands

Authoring-time rule 29 record: the no-em-dash scan, the public-hygiene scan, the readiness pre-round invocation, the rule 19 RED-today probes, and the rule 22 mechanical audit (each pinned span exactly once in its owning snippet, plus `bash -n` over this block) run over these bytes before round 1, and their outcomes append below as Recorded lines.

Recorded 2026-10-12 (authoring session sess_17e58dd5, over the committed v1 bytes on branch authoring/pre-round-gate-dimension-parity): fix_plan_em_dashes.py 0 substitutions; `bash scripts/check-no-em-dash.sh touched` exit 0; public-hygiene scan final line `OUTCOME: pass`; `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-12-pre-round-gate-dimension-parity.md` exit 0 `OUTCOME: pass` (after the gate caught two untagged Commit items in the v1 draft, fixed in the same authoring pass); rule 19 RED-today evidence: all three pinned SKILL.md greps fail against the unamended `agents/skills/plans/SKILL.md`, and a scratch copy of this plan with one Task 1 criterion inflated by 600 characters passes `--pre-round` today (exit 0) while the shared-module probe refuses the same bytes with `evidence criterion exceeds UTF-8 item byte limit`, which is the witnessed gap this plan closes; rule 22 mechanical audit PASS (each pinned span exactly once in the Validation Commands block and once in its Task 2 prescribed snippet, twice in the whole file) with `bash -n` PASS; the first audit run FAILed on echo-message and quoted-grep duplication of the pinned spans and was fixed in the same pass. Round-start state for r1: the bytes at the commit carrying this preamble.

Recorded 2026-10-12, r1 fold re-run (sess_17e58dd5, over the post-fold bytes): the r1 panel's ten staged findings folded (the verbatim amendment texts moved out of checkbox items into prescribed snippet lines; the parity suite added to the GREEN line and Validation Commands; the classification and derivation labels re-homed to a unit-level witness; the Done-when reworded per-site; the aggregate and count fixtures added; the measured corpus rate recorded in the Gate delta; the import-placement and framing clauses added; the Terms and Gist partition aligned). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene `OUTCOME: pass`; `--pre-round` over the plan exit 0 `OUTCOME: pass`; self-application probe PASS (worst item 425 of 512 bytes, worst aggregate 2651 of 4096, every task section accepted by `evidence_criterion_ids`; the first post-fold run caught a 530-byte implementation item, split in the same pass); rule 22 audit PASS over the new pin geometry with `bash -n` PASS; all three SKILL.md greps still RED-today. Round-start state for r2: the bytes at the fold commit carrying this preamble.

```bash
python3 scripts/plan_readiness.py --selftest

python3 scripts/test_plan_readiness.py ExtractionRuleParityTest

python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-12-pre-round-gate-dimension-parity.md

grep -q "extraction-rule executability parity probes" agents/skills/plans/SKILL.md || { echo "rule 29 enumeration omits the added probe set"; exit 1; }

grep -q "the clone-signature component stays create-boundary-only" agents/skills/plans/SKILL.md || { echo "rule 29 does not name the clone-signature residual"; exit 1; }

grep -q "and extraction-rule-executability defects" agents/skills/plans/SKILL.md || { echo "the readiness-boundary summary omits the new defect class"; exit 1; }
```

### Task 1: run the plan-private step 9 probes at pre-round

Context surface: the plan's Terms, this task, and the origin row's problem statement; referenced, never restated.

Files:
- `scripts/plan_readiness.py`

Primary class anchors:
- `run_pre_round` in `scripts/plan_readiness.py`

- [x] `run_pre_round` delivers pre-round executability parity: given a single-task plan whose one evidence criterion exceeds the 512-byte item cap, expects `--pre-round` to exit 1 printing `readiness PRE-ROUND FAILED:` with the same named envelope label the full gate's step 9 prints for the same bytes [class: IMPLEMENTATION_REQUIRED]
- [x] given sibling fixtures breaching the 4096-byte aggregate (one task with nine sub-cap criteria) and the receipt item-count limit (one task with 101 short criteria), expects `--pre-round` to refuse each with its own named ground, byte-identical to step 9's [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a plan with no review record and no reviews-home entry whose task carries an over-cap criterion, expects `--pre-round` to refuse on the envelope label without reading the reviews home or any sidecar [class: IMPLEMENTATION_REQUIRED]
- [x] given the extracted helper over synthetic item dicts mirroring `scripts/test_plan_readiness.py`'s classification parity test, expects the classification and derivation labels byte-identical to step 9's at unit level (those labels are seeding-shape grounds not expressible as plan files; the plan-bytes fixtures cover the three envelope grounds) [class: IMPLEMENTATION_REQUIRED]
- [x] given a conforming plan over every probe, expects the OK line unchanged with its `(review record not consulted)` suffix and budget warnings still suppressed on the failure path [class: REPOSITORY_TEST]
- [x] Run → expect RED: the new in-file selftest fixtures refuse against today's tree, where a plan that step 9 refuses on the envelope passes `--pre-round` clean (the witnessed gap) [class: REPOSITORY_TEST]
- [x] Write minimal implementation: extract step 9's derived-task loop verbatim into a module-level helper returning the named problem or None, keeping the `execute_plan_runtime` import inside the except arm so the deployment-degradation shape is unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] call the shared helper from step 9 (refusal strings byte-identical, existing parity fixtures stay green unmodified) and from `run_pre_round` after the five structural probes and before the budget warnings; update the `run_pre_round` docstring probe enumeration [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` passes including the new fixtures, `python3 scripts/test_plan_readiness.py ExtractionRuleParityTest` passes unmodified, the `--pre-round` with `--selftest` mutual exclusion still refuses, and `--pre-round` over this plan's own bytes exits 0 (self-application: the criteria these bytes derive stay under the caps at this task point) [class: REPOSITORY_TEST]
- [x] Commit: `feat: pre-round gate runs the plan-private executability probes` [class: IMPLEMENTATION_REQUIRED]

### Task 2: prescribe the extended invocation in plans rule 29

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/plans/SKILL.md`

Prescribed verbatim texts, inserted exactly:

- rule 29 parenthetical tail: `and the extraction-rule executability parity probes (the bounded-evidence envelope, enforced inside the evidence-criterion-ids check, and the checklist action classification and derivation checks over derived task sections; the plan-private subset of step 9; the clone-signature component stays create-boundary-only)`
- rule 29 follow-on sentence, inserted after the amended parenthetical: `The envelope caps are authoring policy: acceptance criteria stay under the 512-byte item cap and the 4096-byte task aggregate, and the executability refusals print step 9's verbatim create-boundary framing at pre-round too.`
- readiness-boundary summary enumeration replacement: `decision-trailer, Review Scope, plan-ownership, classification-tag, Primary-class-anchors-grammar, and extraction-rule-executability defects`

- [x] Run → expect RED today: the three SKILL.md validation greps in the Validation Commands block fail against the unamended file (verified at authoring time and recorded in the Validation preamble) [class: REPOSITORY_TEST]
- [x] rule 29's probe enumeration names the added set: given the prescribed rule 29 parenthetical tail and follow-on sentence inserted verbatim, expects the first two pinned greps from the Validation Commands block to pass over `agents/skills/plans/SKILL.md` with the rest of the rule 29 block untouched [class: IMPLEMENTATION_REQUIRED]
- [x] the readiness-boundary summary gains the defect class: given the prescribed enumeration replacement replacing the sentence that today reads `decision-trailer, Review Scope, plan-ownership, classification-tag, and Primary-class-anchors-grammar defects`, expects the third pinned grep from the Validation Commands block to pass [class: IMPLEMENTATION_REQUIRED]
- [x] the rule 29 outcome-contract wording (the tolerated no-review-artifact failure class, the four-outcome vocabulary sentences, the deployed-symlink sentence) is left byte-identical by the amendment [class: REPOSITORY_TEST]
- [x] Commit: `docs: rule 29 prescribes the extended pre-round probe set` [class: IMPLEMENTATION_REQUIRED]
