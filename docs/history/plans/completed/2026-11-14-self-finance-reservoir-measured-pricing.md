# Plan: self-finance-reservoir-measured-pricing

Backlog origins (scope of record):
- docs/history/backlog/2026-11-14-self-finance-reservoir-priced-by-assumption.md

Driving force: code-quality + efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-14-plan-review-self-finance-reservoir-measured-pricing-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 0.5h total, largest task 0.25h
Executed: yes (executed 2026-11-19, commit d573065ea; rule landed as 47 — the plan's prescribed 46 was stale vs disk-truth, rule 46 Interpreter-per-extension landed after authoring)
Authoring claim: 2026-11-14-self-finance-reservoir-priced-by-assumption.md (session sess_cea6d8a2-37bf-4769-ae40-a2d99f04115e)

## Terms

- Self-finance: the byte-budget pay-for-growth duty shape where a file takes its own insertion's bytes out of its existing text in the same change (compression, not duty removal).
- Compression-pay commitment: a plan's declared commitment that a same-change insertion into a file is paid by compressing equivalent bytes of that file in the same change.
- Reservoir: the witness-safe compression pool a compression-pay commitment draws on; a reservoir priced by assumption (never measured) is the witnessed failure mode.
- Byte-budget gate: `python3 scripts/skill_text_budget.py --check`; blocking on the single-read ceiling class, advisory on per-file ratchet caps.
- Single-read ceiling: `SINGLE_READ_CEILING` in `scripts/skill_text_budget.py`, 100000 bytes (measured 2026-11-14 at commit c6c978995).
- Validation Commands authoring rules: `agents/skills/plans/validation-authoring-rules.md`, the numbered rule list that `agents/skills/plans/plan-format.md`'s Validation Commands section points to as the owner of those rules.
- Declared check: a verification a review worker runs because the plan's Validation Commands declare it, as opposed to narrating the commitment.
- Provenance form: rule 39's recorded derivation (the command, the derivation date, and the upstream source state beside a pinned value), so drift is provable by comparison in one step.
- Pins suite: `bash scripts/check_maintenance_pins.sh`, which pins literal spans in guarded skill modules including both target files.

## Why

A plan declared a compression-pay commitment without measuring the witness-safe reservoir or the byte-budget gate's ceiling headroom; three certification rounds passed the commitment narratively, and execution then found the reservoir smaller than assumed and the first re-price crossing the blocking single-read ceiling, spending three focused re-certification rounds. The missing instrument is mechanical: nothing asks the plan's Validation Commands to carry the reservoir arithmetic, so the reviewers had no declared check to run.

## Gist & Examples

TLDR: compression-pay commitments carry measured reservoir arithmetic in Validation Commands and review workers verify it as a declared check, so an underpriced pay-for-growth plan stops passing certification on narrative.

Before: a plan declares "compress equivalent bytes in the same change" with no measured numbers; certification rounds accept the posture; execution finds the witness-safe reservoir smaller than assumed and the re-price crossing the single-read ceiling, forcing re-certification rounds after landing. After: the same plan's Validation Commands carry the measured numbers (target file byte count, the owning gate's blocking ceiling class and value, the committed residual bound), and each certification worker re-measures the byte count and verifies the arithmetic before accepting the commitment, so the shortfall surfaces at authoring time instead of after landing.

## Outcome

Compression-pay feasibility is verified by arithmetic at authoring and certification time, not by narrative posture.

- A plan committing to same-change compression carries the measured numbers in its Validation Commands.
- Review workers verify the arithmetic as a declared check, so an underpriced reservoir blocks at the review boundary instead of costing re-certification rounds after landing.
- The byte-budget gate's posture stays byte-unchanged (`scripts/skill_text_budget.py` untouched).
- Follow-up disposition: no candidate leads are anticipated; the Ship-when operations condition below is the only post-landing obligation, and a witnessed gap in it files a new backlog origin per the standing capture convention.

Gate delta: +1 authoring rule row (rule 46 in `agents/skills/plans/validation-authoring-rules.md`; prose-only advisory requirement, no refusal surface, no checked-set growth) and +1 review-layer worker duty (the declared arithmetic check in `agents/skills/plans/plan-quality-gate.md`'s worker template; review-time duty, not a gate, its blocking weight riding the witnessed incident the origin row records: three unmeasured certification rounds plus three re-certification rounds); removed: none (no refusal, check, or field is removed); no gate or fence added, so no liveness-ledger citation; no new machinery.

## Assumptions

- assume the authoring rule's home is `validation-authoring-rules.md` (rule 46), not `plan-format.md`'s Validation Commands section; basis: the origin row's exact-location pointer ("plan-format.md, the Validation Commands authoring rules") resolves through the plans skill's module dispatch, where plan-format.md's section is a pointer paragraph naming the module the owner of the authoring rules, so the rule list is the single home and a plan-format.md copy would duplicate it
- assume the worker check's home is `plan-quality-gate.md`'s sub-agent prompt template, not the review-plan skill; basis: the plans skill composes each review round's worker prompts from plan-quality-gate.md's template, so the declared check reaches every plan-review worker through it, and the origin's price line names exactly this surface ("the plan-quality-gate's review workers verify the arithmetic as a declared check")
- assume the driving force translation: the origin row records reliability (primary), efficiency (secondary); the closed taxonomy in plan-format.md has no reliability tag, so reliability maps to code-quality (the duty makes certification verify substance); the origin's efficiency (fewer wasted re-certification rounds) maps to the taxonomy's literal efficiency tag, the consumed resource being the review-round spend; basis: the plan-format.md closed taxonomy
- assume this plan commits to no compression-pay itself (both target files sit far under the 100000-byte single-read ceiling with no ratchet caps rows), so rule 46 does not bind this plan's own insertions; the measured arithmetic still stands in Validation Commands as the authoring-time feasibility evidence; basis: byte counts 42845 and 41048 measured 2026-11-14 at commit c6c978995
- assume the ceiling value is cited in rule 46 by role (the owning gate's blocking ceiling class and value) without hardcoding 100000 into the rule text, so the rule does not chase the constant; basis: the byte-budget gate's own calibration history (the ceiling moved once already, 27432-token calibration noted in its docstring)
Decision points requiring a grill: rule home selection resolved by decision receipt (home = validation-authoring-rules.md rule 46; source: the entry self-finance-reservoir-measured-pricing, 2026-11-14; affected: Task 1); worker-check home resolved by decision receipt (home = plan-quality-gate.md sub-agent prompt template; source: the same entry, 2026-11-14; affected: Task 2)

## Standing constraints

- No new gate, validator, lock, ledger, or required ceremony: both tasks edit existing operative text only; `scripts/skill_text_budget.py` stays byte-unchanged.
- The pins suite and the byte-budget gate must stay green after both edits; both target files carry pins-suite spans (count-1 and placement pins), so no pinned span is edited or duplicated, and any pin row the edits touch gets its pin row updated in the same change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the pins suite exits 0 after both edits; the byte-budget gate exits 0 (no blocking ceiling breach)
- compliance: rule 46 carries the three measured numbers (byte count, ceiling class and value, residual bound) and rule 39's provenance form; the worker template carries the declared-check sentence
- completeness: both homes the entry's prompt names (the Validation Commands authoring rules; the quality-gate worker duties) receive exactly one insertion each

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0
- `python3 scripts/skill_text_budget.py --check` exits 0
- grep over `agents/skills/plans/validation-authoring-rules.md` finds rule 46's measurement rule; grep over `agents/skills/plans/plan-quality-gate.md` finds the declared-check sentence
- `git diff HEAD -- scripts/skill_text_budget.py` is empty

**Ship when:**
- (OPERATIONS_FOLLOW_UP) the next authoring plan carrying a compression-pay commitment states the three measured numbers in its Validation Commands and its certification round runs the declared check; evidence owner: the next authoring session with a self-finance commitment; measurable closure condition: one witnessed plan whose Validation Commands carry the arithmetic and whose review record shows the check ran; evidence sources: that plan's Validation Commands block and its review staging record, each tracing to Task 1's and Task 2's landed text.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/validation-authoring-rules.md` (Task 1)
- `agents/skills/plans/plan-quality-gate.md` (Task 2)

**Tests:**
- none; both tasks are operative-text edits verified by the pins suite, the byte-budget gate, and grep checks

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/skill_text_budget.py`; reason: the gate's posture stays byte-unchanged by the origin row's own admission line
- `agents/skills/plans/SKILL.md`; reason: the derive-at-composition sentence in the Writing paragraph stays unextended; the discipline extends through the rule list, the single home the router names, and a SKILL.md edit would duplicate it
- `agents/skills/plans/plan-format.md`; reason: same single-home reasoning as SKILL.md; the Validation Commands section is a pointer paragraph and the rule list is the operative surface

## Validation Commands

Measured arithmetic (provenance per rule 39; derivation command `wc -c < <target-file>` over each target file at authoring time 2026-11-14 at commit c6c978995): `agents/skills/plans/validation-authoring-rules.md` 42845 bytes; `agents/skills/plans/plan-quality-gate.md` 41048 bytes; the owning gate is `scripts/skill_text_budget.py`, blocking class the single-read ceiling, value 100000 bytes (`SINGLE_READ_CEILING`, measured at the same commit); committed residual bound: each edited file's post-change byte count stays at least 50000 bytes under the 100000-byte ceiling (insertion bound 800 bytes per file; observed headroom 57155 and 58952 at authoring). This plan carries no compression-pay commitment itself, so rule 46 does not bind these numbers; they stand as the authoring-time feasibility evidence for the two insertions.

Authoring-time recording (rule 29; first run 2026-11-14T18:00Z from the authoring worktree at commit c6c978995): pins suite exit 0 (`OUTCOME: pass`; one pre-existing unrelated PIN WARN advisory over the EXEC-PROMPTS prune-range clause); byte-budget gate exit 0 (`OUTCOME: pass`, 0 ceiling breaches, 3 advisory ratchet lines); public hygiene scan exit 0; pre-round gate exit 0 (structural checks clean after two per-item byte-cap splits; four advisory Files-coverage warnings recorded, the quoted scripts being validation commands, not task-owned files); the two count greps and the join-seam grep RED-today, the expected authoring-time state, their closure condition being the post-execution landed text; the gate-script cleanliness check exit 0; em-dash fixer 0 substitutions at every plan write; the r1 review pair validated (name probe pass, staging `--preflight` pass, sidecar source digest matching the plan bytes). The mechanical audit recorded: the Validation Commands block passes `bash -n`, and each prescribed pin span occurs exactly once in its owning task snippet (the rule 22 mirror carve-out applied: each span also occurs once in its matching grep line). The rule 46 join-seam pin is a composed-span regression guard checked against the executed file's post-change bytes (rule 22's regression-guard carve-out), not against a single task snippet, because the two prescribed spans join across items 1 and 2.

```bash
bash scripts/check_maintenance_pins.sh || { echo "MISS: pins suite"; exit 1; }
python3 scripts/skill_text_budget.py --check || { echo "MISS: byte-budget gate"; exit 1; }
test "$(grep -oF "the measured reservoir arithmetic instead of the posture" agents/skills/plans/validation-authoring-rules.md | wc -l | tr -d ' ')" -eq 1 || { echo "MISS/COUNT: rule 46 measurement rule"; exit 1; }
test "$(grep -oF "verify the number against the stated ceiling" agents/skills/plans/plan-quality-gate.md | wc -l | tr -d ' ')" -eq 1 || { echo "MISS/COUNT: worker declared check"; exit 1; }
grep -qF "kept after the change; the numbers carry rule 39's provenance form" agents/skills/plans/validation-authoring-rules.md || { echo "MISS: rule 46 join seam"; exit 1; }
git diff --quiet HEAD -- scripts/skill_text_budget.py || { echo "FAIL: byte-budget gate script edited"; exit 1; }
```

### Task 1: Rule 46, measured reservoir arithmetic, in the Validation Commands authoring rules

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/validation-authoring-rules.md`

Evidence:
- the derive-at-composition discipline's existing sentence (agents/skills/plans/SKILL.md Writing paragraph: derive the cap from its owning validator at execution time, never from memory, and split or tighten at composition time rather than at gate time) extends to checklist caps but not to compression-pay commitments
- the witnessed unmeasured commitment (origin row docs/history/backlog/2026-11-14-self-finance-reservoir-priced-by-assumption.md): the 2026-11-14 stop-boundary-rederivation plan declared pay-for-growth without measured numbers; three certification rounds passed it; execution measured the witness-safe reservoir smaller than assumed and the first re-price crossed the blocking single-read ceiling, forcing three focused re-certification rounds
- plan-format.md's Validation Commands section is a pointer paragraph naming this module the owner of the authoring rules, so the rule list is the single home

- [ ] Append rule 46 after rule 45, exactly: `46. **Measured reservoir arithmetic for compression-pay commitments:** when a plan commits to same-change compression paying for an insertion into a file (self-finance), the plan's Validation Commands carry the measured reservoir arithmetic instead of the posture: the target file's byte count measured at authoring time, the owning gate's blocking ceiling class and value, and the committed residual bound kept after the change;` [class: IMPLEMENTATION_REQUIRED]
- [ ] Complete rule 46 as one rule with a provenance tail clause reading exactly: `the numbers carry rule 39's provenance form, so an execution-time mismatch is provable as source drift and the re-pin runs through a plan correction, never an edit of the landed text to chase the count.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `bash scripts/check_maintenance_pins.sh`; the suite exits 0, no pinned span in the file edited or duplicated; update any pin row the edit touches in the same change [class: REPOSITORY_TEST]
- [ ] Run `python3 scripts/skill_text_budget.py --check`; exit 0, no blocking ceiling breach, and the file's post-change byte count stays at least 50000 bytes under the 100000-byte single-read ceiling (authoring-time baseline 42845 bytes, 2026-11-14 at commit c6c978995) [class: REPOSITORY_TEST]

### Task 2: Worker declared-check sentence in the review template

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/plan-quality-gate.md`

Evidence:
- plan-quality-gate.md's sub-agent prompt template is the per-round worker prompt source the plans skill composes each review round from, so a sentence there reaches every plan-review worker
- the witnessed cost (origin row): reviewers had no declared check to run, so the underpriced commitment passed certification and the shortfall surfaced only at execution, costing three re-certification rounds
- the dispatch entry's prompt line names this surface exactly (docs/history/backlog/PLAN-PROMPTS.md, the self-finance-reservoir-measured-pricing entry: "the plan-quality-gate's review workers verify the arithmetic as a declared check")

- [ ] In the sub-agent prompt template's paragraph opening on "Read the actual source files referenced in the plan", after that sentence, insert exactly: `When the plan's Validation Commands declare a compression-pay measurement, run the declared check: re-measure the target file's byte count and verify the number against the stated ceiling and committed residual bound, recording the re-measured numbers in the finding record instead of accepting the commitment narratively.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `bash scripts/check_maintenance_pins.sh` and `python3 scripts/skill_text_budget.py --check`; both stay green, no pinned span in the file edited or duplicated (count-1 pins over the cross-task sweep clauses and the gist phrases; the insertion touches neither), any pin row the edit touches updated in the same change [class: REPOSITORY_TEST]
- [ ] Check the file's post-change byte count stays at least 50000 bytes under the 100000-byte single-read ceiling (authoring-time baseline 41048 bytes, 2026-11-14 at commit c6c978995) [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-14-self-finance-reservoir-priced-by-assumption.md: covered by this plan's execution (commit d573065ea); disposition folded here, origin row deleted in the same landing.
