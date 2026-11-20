# Plan: Pin red entry-checker baseline disposition at emission

Backlog origins (scope of record):
- docs/history/backlog/2026-11-15-sweep-entry-emission-checker-pass.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-sweep-entry-emission-checker-pass-p18eea05e-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list).
Authoring claim: 2026-11-15-sweep-entry-emission-checker-pass.md (session 8d877557-27c5-40d7-bb66-a0c16944385d)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (1e8e1534e199e537922e5c783e7a31302496929f)

## Terms

- **Entry checker:** `scripts/check_investigate_entries.py`, the structural-minimum validator (non-empty rejected alternatives, evidence-cited dispositions) every rolling-log entry write passes before its write is committed.
- **Red baseline:** the entry checker reporting standing violations in the destination log beyond the emitting turn's own entry.
- **Emitting turn:** the session turn whose log write commits the entry.
- **Completion-record sweep entry:** the closeout record entry an exec session appends to a rolling prompt log (the `EXEC-PROMPTS-record sweep` heading shape).
- **Harvest tail:** the learn Step 1.9 closeout leg: the backlog-row capture and its same-run investigate invocation.
- **Manual follow-up:** the learn failure-semantics disposition that reports a failure as an explicit non-blocking drop.
- **Repair scope:** what the baseline rule's within its repair scope branch means: a mechanical, evidence-cited block addition derivable from the violating entry's own recorded origins; content-bearing repairs take the loud-report arm.
- **Warning-only sweep-gate check:** the priced and rejected machinery alternative: the done sweep gate also running the entry checker and warning on violations.

## Why

Four completion-record sweep entries landed without the required Rejected alternatives field between 2026-11-13 and 2026-11-14, growing the EXEC log's checker baseline from one standing violation to five before the 2026-11-15 operator-directed repair restored exit 0. The checker duty is already pinned at the emission owner; what went wrong twice more the same day is the disposition: two harvests re-derived the red baseline and each first deferred it instead of repairing or loudly reporting it.

## Gist & Examples

TLDR: Pin that a red entry-checker baseline is repaired or loudly reported in the emitting turn, never silently deferred, so the emission hygiene stays inside the loop's own turns instead of accruing until an operator directs a repair.

Before: an emitting turn sees checker violations beyond its own entry, reports them as a manual follow-up or nothing, and the baseline accrues until an operator-directed repair lands.

After: the emitting turn repairs the in-scope violations in the same log write, or loudly reports the red baseline in its emitted entry or closeout record when they are outside its repair scope; the harvest-tail vocabulary no longer parks a red baseline under the manual-follow-up disposition; the warning-only sweep-gate check is priced with its admission fields and rejected.

Edge cases: a violating entry outside the emitting turn's repair scope stays reportable and is never silently dropped; the machinery rejection is re-priced at its recorded review date (2026-12-15) only on a witnessed post-landing accrual episode.

## Outcome

Rolling-log entry emissions keep the checker baseline clean or loudly red, without operator-directed repairs.

- The Stage 4 checker bullet carries the baseline disposition rule: repair in-scope violations in the same log write, or loudly report the baseline; silent deferral is unsanctioned.
- The Stage 4 pin defines the repair-scope predicate (a mechanical, evidence-cited block addition derivable from the violating entry's own recorded origins) and reconciles the write-mechanics bullet's targeted-section-edit scope and drift fallbacks with the repair arm.
- The learn harvest tail can no longer dispose of a red entry-checker baseline as a manual follow-up or an invocation failure.
- The warning-only sweep-gate check alternative is priced (incident, warning-only first, promotion after one true catch, review 2026-12-15) and rejected with its rationale recorded.

Gate delta: no gate, validator, lock, ledger, state field, refusal class, or blocking review duty is added or removed; the warning-only sweep-gate check alternative is priced and rejected, leaving the machinery surface unchanged.

## Assumptions

- The prompt-emission owner for both rolling logs is investigate Stage 4; basis: the EXEC-PROMPTS.md preamble line "Prompt-emission owner: agents/skills/investigate/SKILL.md, Stage 4", read 2026-11-15.
- The harvest-tail deferral vocabulary home is learn step-1-extract.md (the Investigate invocation and Failure semantics bullets); basis: the two 2026-11-15 harvest emission commits (944214027, 9d2565fe9) reported the standing violations "as manual follow-up" in their own emission records, read 2026-11-15.
- The zero-machinery arm justifies rejecting the warning-only sweep-gate check: the emitting turn's own ordered checker run already detects the red baseline (both harvests caught it that way); the witnessed failure was disposition, and a warning-only check emits into the same closeout reports that deferred twice; basis: the origin row and the repair landing 657b8b8e7, read 2026-11-15.
- Skill byte-budget compliance is measured by the existing blocking repository gate; any growth above a file cap is paid by an equivalent deletion in the same file; basis: investigate/SKILL.md measured 19353 bytes against its 22203-byte cap on 2026-11-15; learn/step-1-extract.md has no cap entry (advisory notice only).

Decision points requiring a grill: machinery alternative (warning-only sweep-gate check) versus zero-machinery pins: rejected the gate, admission fields recorded (incident docs/history/backlog/2026-11-15-sweep-entry-emission-checker-pass.md; warning-only first; promotion after one true catch; review date 2026-12-15), source: the entry prompt's decision rule and the origin row, 2026-11-15, affected: Assumptions and Outcome (maintenance-selected standing authorization).

## Standing constraints

- Add no blocking gate, validator, lock, ledger, or new ceremony; the entry checker stays the emission-time duty it already is.
- Land the rule, not the story: each operative surface cites the incident row in at most one line.
- Never weaken the checker's structural minimum; no exemption for completion-record entries (rejected upstream, evidence basis: scripts/check_investigate_entries.py).
- Keep each edited skill file within its existing byte cap; pay for any growth with same-file deletions in the same change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both operative surfaces state repair-or-loud-report with silent deferral excluded.
- pin coverage: each inserted span has its own dedicated presence check that fails when the span is absent.
- byte balance: the blocking byte-budget gate passes with no cap breach.
- simplicity: the final diff adds no gate, validator, lock, ledger, or state field.

**Done when:** the Stage 4 checker bullet states the baseline disposition rule with its repair-scope definition and reconciled write-mechanics scope and drift fallbacks, and cites the incident once; the learn harvest-tail bullet excludes the manual-follow-up and invocation-failure dispositions for red baselines; the machinery pricing and rejection are recorded in this plan; the byte-budget, pin, hygiene, and no-em-dash checks pass; and the diff adds no new machinery.

**Ship when:** none (repository-only skill change).

## Documentation Impact Assessment

Update only the two operative skill surfaces this plan names; both already own the duties they pin, so no new document, README row, or registry change is needed: the skill names, paths, and invocations do not change.

## Design Invariants

Investigate Stage 4 owns rolling-log entry emission (the EXEC-PROMPTS preamble names it the prompt-emission owner for both logs), so the baseline disposition extends its existing checker bullet; a separate section cannot improve ownership and would duplicate the same duty. Learn Step 1.9 owns the harvest-tail capture and its same-run investigate invocation, so the vocabulary exclusion extends its existing bullets. The plan records the machinery pricing and rejection rather than any code: the entry checker and the done sweep gates stay byte-identical.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/investigate/SKILL.md` (Task 1)
- `agents/skills/learn/step-1-extract.md` (Task 2)

**Tests:**
- none; no test file is added or changed by this plan.

**Plan-related extension:** implementation and review may change files not listed above when a finding is causally related to the pinned baseline-disposition rule or the harvest-tail vocabulary it corrects. If that link is weak or speculative, drop the finding with a one-line reason.

**Documentation:** the two skill files are the sole operative surfaces in scope. Do not duplicate the baseline rule in the rolling logs' preambles, the maintenance skill, or the learn SKILL.md router.

**Out of scope; reject unless plan-related:**
- `scripts/check_investigate_entries.py`; reason: the checker's structural minimum stays byte-identical.
- `scripts/done_sweep_gates_lib.py`; reason: the machinery alternative is priced and rejected, so the sweep gates stay unchanged.
- `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md` entry bodies; reason: no entry bytes change (landing riders excepted).
- `agents/skills/maintenance/`; reason: no maintenance payload, lane, or scheduling surface is in scope.
- `agents/skills/learn/SKILL.md` (the router); reason: Step 1.9's own module owns the harvest-tail vocabulary.

## Validation Commands

Validation preamble (authoring record, rule 29): `python3 scripts/plan_readiness.py --pre-round` passed (structural checks clean) after one over-cap acceptance criterion was split (558 bytes over the 512 cap; the split preserved acceptance coverage). `bash scripts/check-no-em-dash.sh touched` passed with zero substitutions from the write-time fixer; `bash scripts/check-no-em-dash.sh added-lines --base 6435bbeac` passed. `bash scripts/scan-public-hygiene.sh` passed with two report-only existing-path notices and no hygiene findings. `bash scripts/check_maintenance_pins.sh` reports one pre-existing failure, "prompt log has no all-served (stale) entry": `check_prompt_log_origins.py` exits 1 on the primary checkout at the branch point (2026-11-15, the stale maintenance-integrity-stop-scope-and-retry entry awaiting its prune on main); the failure is unrelated to this plan's files, none of which the pins script gates, and none of this plan's own pins fail. Review round r1 (2026-11-15, record 2026-11-15-plan-review-sweep-entry-emission-checker-pass-p18eea05e-r1.md) staged five Medium findings, one blocking, all folded in this revision: pin literals realigned with prescribed criterion wording, the repair-scope predicate defined, the silent-deferral and write-mechanics pins added, and the Failure-semantics re-parking seam closed. Review round r2 (2026-11-15, record 2026-11-15-plan-review-sweep-entry-emission-checker-pass-p18eea05e-r2.md) returned ready=yes over the post-fold digest with zero blocking and one fold-introduced Medium, the write-mechanics criterion's drift-fallback statement unpinned, folded in this revision as the seventh pin. Rule 19 RED-today evidence: all seven presence pins were executed 2026-11-15 against the current tree after the folds and are absent in their target files (grep -c returned 0), flipping GREEN exactly when Tasks 1 and 2 land. Rule 22 pin-vs-prescription audit: each pinned span is quoted from this plan's own prescribed task text (Task 1 criterion 1, the repair-scope definition criterion, the silent-deferral criterion, the incident-row citation criterion, the write-mechanics reconciliation criterion sourcing both its pins, Task 2 criterion 1); no forbidden-phrase sweeps are prescribed, so no scope simulation was needed. The Validation Commands block passed `bash -n`.

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
test "$(grep -cF 'repair the in-scope violations in the same log write when' agents/skills/investigate/SKILL.md)" -eq 1 || { echo "Stage 4 repair-arm pin missing or duplicated"; exit 1; }
test "$(grep -cF 'a mechanical, evidence-cited block addition derivable from the violating entry' agents/skills/investigate/SKILL.md)" -eq 1 || { echo "Stage 4 repair-scope definition pin missing or duplicated"; exit 1; }
test "$(grep -cF 'silent deferral is unsanctioned' agents/skills/investigate/SKILL.md)" -eq 1 || { echo "Stage 4 silent-deferral pin missing or duplicated"; exit 1; }
test "$(grep -cF 'own section plus each in-scope repaired entry' agents/skills/investigate/SKILL.md)" -eq 1 || { echo "Stage 4 write-mechanics reconciliation pin missing or duplicated"; exit 1; }
test "$(grep -cF 're-derive pending repairs after the fresh read' agents/skills/investigate/SKILL.md)" -eq 1 || { echo "Stage 4 drift-fallback pin missing or duplicated"; exit 1; }
test "$(grep -cF '2026-11-15-sweep-entry-emission-checker-pass.md' agents/skills/investigate/SKILL.md)" -eq 1 || { echo "incident citation must appear exactly once"; exit 1; }
test "$(grep -cF 'is never a `manual follow-up` disposition and never an invocation failure' agents/skills/learn/step-1-extract.md)" -eq 1 || { echo "harvest-tail vocabulary pin missing or duplicated"; exit 1; }
```

### Task 1: Pin the baseline disposition in investigate Stage 4

Context surface: the plan's Terms, this task, Standing constraints, and `agents/skills/investigate/SKILL.md` Stage 4.

Files:
- `agents/skills/investigate/SKILL.md`

- [x] Given the entry checker reports, for the destination log, standing violations beyond this emission's own entry, the Stage 4 checker bullet orders the emitting turn to repair the in-scope violations in the same log write when the violating entries are within its repair scope, or to loudly report the red baseline in the emitted entry or its closeout record when they are not. [class: IMPLEMENTATION_REQUIRED]
- [x] The same Stage 4 sentence defines within its repair scope in one clause: a mechanical, evidence-cited block addition derivable from the violating entry's own recorded origins; content-bearing repairs take the loud-report arm. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the same red baseline, the Stage 4 pin states silent deferral is unsanctioned, names filing the baseline as an unowned manual follow-up a deferral shape, and cites the witnessed incident row in one line. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the same red baseline, the Stage 4 write-mechanics bullet's targeted-section-edit parenthetical reads `the entry's own section plus each in-scope repaired entry's section`, and the bullet states the drift fallbacks re-derive pending repairs after the fresh read, taking the loud-report disposition when only the append path fires. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the edited file within its existing byte cap; pay for any growth with same-file deletions in this change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block and confirm the six Stage 4 pins pass and the byte-budget gate reports no cap breach. [class: REPOSITORY_TEST]
- [x] Commit: `docs: pin red entry-checker baseline disposition in investigate Stage 4` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Exclude the manual-follow-up disposition for red baselines at the harvest tail

Context surface: the plan's Terms, this task, Standing constraints, and `agents/skills/learn/step-1-extract.md` Step 1.9.

Files:
- `agents/skills/learn/step-1-extract.md`

- [x] Given a red entry-checker baseline the Step 1.9 investigate invocation's checker run reports, the Investigate invocation bullet states the baseline is never a `manual follow-up` disposition and never an invocation failure for the Failure-semantics bullet: the emitting turn repairs the in-scope violations or loudly reports the baseline in the emitted entry, per the Stage 4 baseline rule. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the edited file within its existing byte cap; pay for any growth with same-file deletions in this change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block and confirm the harvest-tail pin passes and the byte-budget gate reports no cap breach. [class: REPOSITORY_TEST]
- [x] Commit: `docs: exclude manual-follow-up disposition for red entry-checker baselines at the harvest tail` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-15-sweep-entry-emission-checker-pass.md: covered by this plan (execution landing; both tasks implemented, intermediate reviews and Phase 3 r1 ready=yes with one Low accepted, no machinery added).
