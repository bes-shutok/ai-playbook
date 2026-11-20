# Plan: Own the docs/tmp drain arms' promotion loop census

Backlog origins (scope of record):
- docs/history/backlog/2026-11-15-docs-tmp-drain-arms-promotion-loop-unowned.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-docs-tmp-drain-arms-promotion-loop-pfa144802-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list).
Authoring claim: 2026-11-15-docs-tmp-drain-arms-promotion-loop-unowned.md (session 07af1276-18ce-44fd-b2e9-984d418ccb9f)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (e3394f4a3adaaaa4e04b6d17799ea46132da444e)

## Terms

- **Drain arms:** the three bounded drain classes inside the done closeout's `docs-tmp-sweep` gate: never-synced scratch age bound (Arm 1), dead-root marker drain (Arm 2), and the execute-plan proof-family terminal-state bound (Arm 3).
- **Posture knob:** the facts-document key `docs_tmp_drain_arms` (`report-only` default, `on`, or `off`) gating whether the arms unlink or only report; resolved by `_docs_tmp_drain_posture` in `scripts/done_sweep_gates_lib.py`.
- **Sweep summary:** the gate's one-line report (`docs/tmp sweep: removed=..., skipped=..., kept=..., dead-root-drained=..., dead-root-kept=...`) emitted at every done closeout.
- **Full enumeration:** the unbounded per-entry report list the gate writes under `docs/tmp/done-session/gate-reports/` as `run-<run-id>-docs-tmp-sweep-full.txt` (the `run-<run-id>-` scope present when the closeout's run manifest resolves, else bare `docs-tmp-sweep-full.txt`).
- **Would-drain row:** a report line of the shape `<path> (would-drain: <reason>; posture report-only)` the arms print instead of unlinking while the posture is `report-only`.
- **Mispriced row:** a would-drain row whose entry class, re-derived from the entry's own state on disk, disagrees with the arm reason printed beside it.
- **Census-adjudication duty:** the new read-only survey duty this plan pins: resolve the newest full enumeration, adjudicate every would-drain row on it, write the census record, report the flip review on an adjudicated clean cycle, and census the uncovered families.
- **Census record:** the overwrite-style JSON record `docs/tmp/done-session/drain-arms-census.json` carrying `{date, run_id, report_surface, report_absent, would_drain_rows, mispriced_rows, clean_cycle, uncovered_families}`.
- **Clean cycle:** one adjudicated census cycle whose would-drain rows are all confirmed correctly priced; a zero-row cycle on a resolved report surface counts clean; a report-absent cycle is never clean.
- **Report-absent cycle:** a newest closeout whose report lines did not exceed the emission sample bound, leaving no durable full enumeration (the gate writes the list only above the bound; a full-list write failure degrading the join to stdout is the same no-durable-surface state).
- **Uncovered families:** the scratch directory families the three drain arms never reach: the protected review-loop telemetry, code-review, and handoff scratch classes and the kept-side classes the sweep reports keep.
- **Promotion flip review:** the operator-gated review the duty reports on a clean cycle: flipping `docs_tmp_drain_arms` from `report-only` to `on` in the facts document.
- **Interrupted-census precedent:** the existing survey arm state file `docs/tmp/done-session/interrupted-census.json` whose overwrite semantics this plan's census record mirrors.

## Why

The retention redesign landed three drain arms behind a report-only default and pinned its own promotion criterion (one clean census cycle flips the knob), but pinned no duty to run that cycle. Fourteen days later the knob key is still absent from the facts file, no text reads the sweep's would-drain reports, and the 2026-11-15 operator-directed prune bypassed the arms entirely, removing the would-drain data before any cycle adjudicated it.

## Gist & Examples

TLDR: Pin one read-only census-adjudication duty in the daily maintenance survey so the landed drain-arms promotion criterion finally has a consumer, the done closeout's sweep report feeding an adjudication that records the clean cycle and reports the operator-gated posture flip instead of leaving the report-only default unpromoted indefinitely.

Before: every done closeout emits a docs-tmp-sweep summary and would-drain rows that no duty reads; the promotion criterion sits unconsumed; the posture stays report-only forever while operators resort to manual interactive censuses and manual prunes that bypass the arms.

After: each survey turn runs the census-adjudication duty over the newest sweep report surface, adjudicates every would-drain row on it as correctly priced or mispriced against the entry's on-disk state, overwrites the census record, and on an adjudicated clean cycle reports the promotion flip review for the operator's approval; the same census answers which scratch families the arms never reach. The knob itself is never flipped by the loop.

Edge cases: a first survey turn or a lost census record takes the no-predecessor path (the record only ever holds the latest cycle); a mispriced row is a warning-only survey finding, never a blocked turn, and suppresses the flip report for that cycle; a zero-row cycle on a resolved report surface counts clean vacuously; a report-absent cycle (the newest closeout's report lines at or under the emission sample bound, or a full-list write failure degrading the join to stdout) records `report_absent: true` with `clean_cycle: false` and never fires the flip review; the resolution rule reads the newest run-scoped full list by the run-id timestamp in its name, a bare unscoped name by its file mtime.

## Outcome

The landed retention promotion loop has an owning consumer: the survey adjudicates the sweep's would-drain reports every turn and surfaces the flip point to the operator.

- The maintenance survey gains one read-only census-adjudication arm over the newest docs-tmp-sweep report surface.
- The census record makes the promotion criterion's witness durable and inspectable across turns.
- The done skill's drain-arms paragraph names the census arm as the summary's consumer, so both sides attest the same contract.
- The knob flip stays operator-gated: the loop reports, the operator decides.

Gate delta: no gate, validator, refusal class, lock, ledger, or schema field is added or removed; the one addition is a read-only survey duty (a prose-only requirement), priced by its witnessed incident (origin docs/history/backlog/2026-11-15-docs-tmp-drain-arms-promotion-loop-unowned.md: the fourteen-day unpromoted posture and the operator-directed manual bypass); machinery surfaces stay byte-identical.

## Assumptions

- The sweep report surface at HEAD is the adjudication input: the summary line plus the full enumeration under `docs/tmp/done-session/gate-reports/`; the gate writes that enumeration only when its report lines exceed the emission sample bound (`SAMPLE_LIMIT = 10`), so a durable surface exists exactly for above-bound cycles; basis: `bounded_report_lines` and `bounded_inline_listing` in `scripts/done_sweep_gates_lib.py` (write only above the bound; a write failure degrades the join to stdout plus one warning line), read 2026-11-15, and the observed gate output in run-20261115T165950Z-a09160fb70f6's report (294 report lines, above-bound).
- The posture knob key `docs_tmp_drain_arms` is absent from `.ai-playbook/facts.md` today and the gate falls back to `report-only`; basis: work-tree grep and `git grep docs_tmp_drain_arms HEAD -- .ai-playbook` re-run 2026-11-15 (review-record hits only).
- The census record mirrors the interrupted-census record's overwrite semantics (exactly the last record survives; no-predecessor path on first turn or lost file); basis: the interrupted-manifest classification arm in `agents/skills/maintenance/survey-arms.md`, read 2026-11-15.
- The survey's read and audit arms run even in survey-only lane classes, so a survey-only turn still adjudicates; basis: the class-guard text in `agents/skills/maintenance/SKILL.md`, read 2026-11-15.
- The clean-cycle predicate is the retention plan's promotion criterion verbatim (one census cycle whose would-drain rows are all confirmed correctly priced); basis: the completed plan's assumption line in `docs/history/plans/completed/2026-11-01-docs-tmp-retention-redesign.md`, read 2026-11-15.
- Byte-budget posture: `agents/skills/maintenance/survey-arms.md` sits over its Part 4 pilot target (84,023 bytes against 46,080, 2026-11-15) in the advisory ratchet class, not a blocking ceiling breach; the blocking gate stays exit 0 and this plan records, never pays by forced deletion, that advisory posture; `agents/skills/done/SKILL.md` has no caps entry (advisory notice only); basis: `python3 scripts/skill_text_budget.py --check` run 2026-11-15.
- The origin row's "monitor step" wording maps to the survey: the repo's own Integration Points vocabulary binds "the monitor step" to Step 3's rolling prompt log duties, whose predicate is log processing, while this duty is read-only discovery and adjudication, the survey arms module's character and the home of the interrupted-census precedent; basis: `agents/skills/maintenance/SKILL.md` Integration Points and `agents/skills/maintenance/survey-arms.md`, read 2026-11-15.

Decision points requiring a grill: census-duty home (origin wording "monitor step" versus the survey Step 1 home): pinned to the Step 1 survey arms module, source: the Integration Points binding of "monitor step" to Step 3 rolling-log duties and the interrupted-census precedent living in survey-arms.md, 2026-11-15, affected: Outcome and Task 1 (maintenance-selected standing authorization); census record shape: overwrite-style JSON beside the interrupted-census record, source: survey-arms.md precedent, 2026-11-15, affected: Task 1 (maintenance-selected standing authorization).

## Standing constraints

- Add no gate, validator, script change, lock, ledger, or state field; the duty is read-only skill text, and its only mutation is the census record write, the interrupted-census precedent's own class.
- The knob flip is operator-owned: no automated turn edits `docs_tmp_drain_arms`; the duty reports the flip review and stops.
- Land the rule, not the story: each operative surface cites the origin row in at most one line.
- Keep the byte-budget gate exit 0 on both edited files; the survey-arms.md advisory pilot overage is recorded posture, never a trigger for forced deletions.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the arm states the input surface, the adjudication predicate, the record shape and path, the clean-cycle predicate, the operator-gated flip report, and the uncovered-families census line, each once.
- pin coverage: each inserted span has its own dedicated presence check that fails when the span is absent.
- consistency: the done skill's drain-arms paragraph names the census arm as the consumer, so the surfacing point and the duty attest one contract from both sides.
- simplicity: the final diff adds no machinery; the sweep gate, its script, and the facts document stay byte-identical.

**Done when:**
- the survey arms module carries the census-adjudication arm with its adjudication predicate, census record, clean-cycle predicate, flip-review report, uncovered-families census line, and warning-only mispricing posture, citing the origin row once;
- the done skill's drain-arms paragraph names the census arm as the summary's consumer;
- the byte-budget, pin, hygiene, and no-em-dash checks pass;
- the diff adds no new machinery.

**Ship when:** the operator, after a witnessed clean cycle, flips `docs_tmp_drain_arms` to `on` in the facts document (human-owned; prose only; never a task of this plan).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/survey-arms.md` (Task 1)
- `agents/skills/done/SKILL.md` (Task 2)

**Tests:**
- none; no test file is added or changed by this plan.

**Plan-related extension:** implementation and review may change files not listed above when a finding is causally related to the pinned census duty or the consumer pointer it pins. If that link is weak or speculative, drop the finding with a one-line reason.

**Documentation:** the two skill files are the sole operative surfaces in scope. Do not duplicate the census duty in the maintenance SKILL.md router, the rolling logs' preambles, or a new document.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py`; reason: the machinery stays byte-identical; the duty consumes its reports.
- `.ai-playbook/facts.md`; reason: the posture knob flip is operator-owned, never plan work.
- `agents/skills/maintenance/SKILL.md`; reason: no router change; the arm lives in the Step 1 module it already dispatches.
- `docs/tmp/` state files; reason: runtime artifacts, never tracked surfaces.

## Validation Commands

Validation preamble (authoring record, rule 29): `python3 scripts/plan_readiness.py --pre-round` passed (structural checks clean, exit 0, OUTCOME: pass) with five warning-only FILES-COVERAGE WARNING lines naming runtime-artifact paths quoted inside acceptance items (`docs/tmp/done-session/gate-reports/`, `run-<run-id>-docs-tmp-sweep-full.txt`, `docs-tmp-sweep-full.txt`, `docs/tmp/done-session/drain-arms-census.json`); all five paths are runtime artifacts the Review Scope lists out of scope, never edit targets, so the warnings are recorded posture, not defects. `bash scripts/check-no-em-dash.sh touched` passed with zero substitutions from the write-time fixer (`python3 scripts/fix_plan_em_dashes.py` over the plan bytes: total 0 substitutions). `bash scripts/scan-public-hygiene.sh` passed with no hygiene findings. `python3 scripts/skill_text_budget.py --check` passed (0 ceiling breaches, blocking posture; the survey-arms.md Part 4 pilot overage is advisory per the Assumptions). Rule 19 RED-today evidence: all twelve presence pins executed against the current tree (worktree at branch point fc66bb897; the original ten on 2026-11-15, the two rule-fold additions on 2026-11-16) and are absent in their target files (`grep -cF` returned 0 for each), flipping GREEN exactly when Tasks 1 and 2 land. Rule 22 pin-vs-prescription audit: each pinned span is quoted verbatim from this plan's own prescribed task text (Task 1 items 1, 3, 4, 6, 7, 8, 9, 10 and Task 2 item 1; the over-cap record-shape criterion was split into the shape item and the run-id/posture item after the fold, both halves keeping their pinned spans); no forbidden-phrase sweeps are prescribed, so no scope simulation was needed. The Validation Commands block passed `bash -n` (re-run after the r1 fold). Review round r1 (2026-11-15, record 2026-11-15-plan-review-docs-tmp-drain-arms-promotion-loop-pfa144802-r1.md, full five-worker panel) staged three Medium and one Low findings, one blocking, all folded in this revision: F1 pinned the report-surface resolution rule and the report-absent cycle state (the gate writes the full enumeration only above its emission sample bound, so a no-durable-surface cycle records `clean_cycle: false` and fires no flip review), F2 added the entry-class derivation clause (re-derived from the entry's on-disk state, never from the printed reason), F3 extended the census record with `report_surface` and `report_absent` and pinned the null-`run_id` case, and F4 added the two record-contract pins. `bash scripts/check_maintenance_pins.sh` (worktree cwd) reports one pre-existing failure, `prompt log has no all-served (stale) entry`: `check_prompt_log_origins.py` exits 1 from the worktree naming exactly one STALE entry, `maintenance-integrity-stop-scope-and-retry` (its origins deleted in the execution landing 8f2bcd3b1; the prune is the monitor duty's, pre-existing at the branch point fc66bb897 and recorded by the sibling sweep-entry authoring run the same day); both of this plan's own entries read LIVE, and none of this plan's files is a pins-suite gate target, so the failure is recorded posture, not a launch block. The budget gate probe at the r1 boundary returned `pause_decision: continue` (binding primary), so the round launched.

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
test "$(grep -cF 'Docs-tmp drain-arms census arm' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "census arm bullet name pin missing or duplicated"; exit 1; }
test "$(grep -cF 'a row is correctly priced when its entry class matches the printed arm reason' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "adjudication predicate pin missing or duplicated"; exit 1; }
test "$(grep -cF 'drain-arms-census.json' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "census record path pin missing or duplicated"; exit 1; }
test "$(grep -cF 'whose would-drain rows are all confirmed correctly priced, a zero-row cycle counting clean' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "clean-cycle predicate pin missing or duplicated"; exit 1; }
test "$(grep -cF 'the survey never flips the knob itself' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "operator-gated polarity pin missing or duplicated"; exit 1; }
test "$(grep -cF 'records them in `uncovered_families`' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "uncovered-families census line pin missing or duplicated"; exit 1; }
test "$(grep -cF 'A mispriced row is a survey finding reported warning-only' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "warning-only mispricing pin missing or duplicated"; exit 1; }
test "$(grep -cF 'would_drain_rows' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "census record shape keys pin missing or duplicated"; exit 1; }
test "$(grep -cF 'exactly the last record survives' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "overwrite no-predecessor pin missing or duplicated"; exit 1; }
test "$(grep -cF '2026-11-15-docs-tmp-drain-arms-promotion-loop-unowned.md' agents/skills/maintenance/survey-arms.md)" -eq 1 || { echo "origin citation must appear exactly once"; exit 1; }
test "$(grep -cF 'feed the docs-tmp drain-arms census arm' agents/skills/done/SKILL.md)" -eq 1 || { echo "done-skill consumer pointer pin missing or duplicated"; exit 1; }
test "$(grep -cF 'operator-gated docs_tmp_drain_arms promotion flip' agents/skills/done/SKILL.md)" -eq 1 || { echo "done-skill flip-review pin missing or duplicated"; exit 1; }
```

### Task 1: Pin the census-adjudication arm in the survey

Context surface: the plan's Terms, this task, Standing constraints, and `agents/skills/maintenance/survey-arms.md` Step 1.

Files:
- `agents/skills/maintenance/survey-arms.md`

- [ ] Add one survey bullet named `Docs-tmp drain-arms census arm` that runs one read-only census-adjudication duty over the newest done closeout's docs-tmp-sweep report surface: the newest full enumeration under `docs/tmp/done-session/gate-reports/` (the newest `run-<run-id>-docs-tmp-sweep-full.txt` by the run-id timestamp in its name; a bare `docs-tmp-sweep-full.txt` by its file mtime). [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a newest closeout whose report lines did not exceed the emission sample bound, the gate wrote no durable full enumeration, so the bullet records a report-absent cycle with `clean_cycle: false` and `report_absent: true` and fires no flip review: a report-absent cycle is never clean. [class: IMPLEMENTATION_REQUIRED]
- [ ] The same bullet adjudicates every `would-drain` row on the resolved surface: a row is correctly priced when its entry class matches the printed arm reason, and the duty re-derives each entry class from the entry's own state on disk (the arm's keep-side preconditions, checked read-only), never from the printed reason itself; a row whose class and reason disagree is mispriced. [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet overwrites `docs/tmp/done-session/drain-arms-census.json` with one record `{date, run_id, report_surface, report_absent, would_drain_rows, mispriced_rows, clean_cycle, uncovered_families}` (exactly the last record survives; a first turn or a lost file takes the no-predecessor path, the interrupted-census record's own semantics). [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a newest closeout whose run manifest did not resolve, the record's `run_id` is null and `report_surface` names the adjudicated file path or `none` on a report-absent cycle. [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet states the clean-cycle predicate as the retention plan's promotion criterion: one census cycle whose would-drain rows are all confirmed correctly priced, a zero-row cycle counting clean; the predicate reads only an adjudicated cycle from a resolved report surface, never a report-absent one. [class: IMPLEMENTATION_REQUIRED]
- [ ] On a clean cycle the bullet reports the promotion flip review for the operator's approval (flipping the facts knob `docs_tmp_drain_arms` from `report-only` to `on`); the survey never flips the knob itself. [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's census answers which scratch directory families the three drain arms never reach (the protected review-loop telemetry, code-review, and handoff scratch classes and the kept-side classes) and records them in `uncovered_families`. [class: IMPLEMENTATION_REQUIRED]
- [ ] A mispriced row is a survey finding reported warning-only through the existing finding channel, never a blocked turn; the knob-flip report fires only on a clean cycle. [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet cites the origin row in one line and no other surface repeats the citation. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the byte-budget gate exit 0 on the edited file (the advisory pilot overage posture per the Assumptions). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands block and confirm the ten survey pins pass and the byte-budget gate reports no ceiling breach. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: pin the docs-tmp drain-arms census arm in the maintenance survey` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Name the census consumer at the surfacing point

Context surface: the plan's Terms, this task, Standing constraints, and `agents/skills/done/SKILL.md`'s drain-arms paragraph.

Files:
- `agents/skills/done/SKILL.md`

- [ ] Extend the drain-arms paragraph's final sentence so the sweep summary and its full list feed the docs-tmp drain-arms census arm in the maintenance survey: that arm adjudicates the would-drain rows each survey turn, records the clean cycle in `docs/tmp/done-session/drain-arms-census.json`, and reports the operator-gated docs_tmp_drain_arms promotion flip for approval. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the byte-budget gate exit 0 on the edited file. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands block and confirm the two done-skill pins pass. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: name the census consumer at the docs-tmp-sweep surfacing point` [class: IMPLEMENTATION_REQUIRED]
