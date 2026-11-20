# Plan: scheduler-dark monitor-substitute continuity

Backlog origin: docs/history/backlog/2026-11-19-scheduler-dark-converter-prune-dependency.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-19-plan-review-scheduler-dark-converter-prune-dependency-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (e472c29f17ed0a03974148afa51eef329c30f5ed)
Authoring claim: 2026-11-19-scheduler-dark-converter-prune-dependency.md (session sess_f1bfba81-c78f-4645-b6cc-c1260a7e7488)

## Terms

- Missed-fire listing shape: a scheduler-parent carrier listing whose `lastRunAt` is older than the carrier's own scheduled interval (its cron cadence) while `nextRunAt` has advanced past the missed slot; when the fire-outcome ledger resolves the missed slot it supplements the listing read.
- Scheduler-liveness conjunct: the precondition this plan adds to the `loop-exit:queue-empty` recording duty: the recording exit reads the scheduler parent's fire liveness first.
- Dark-scheduler classification: the missed-fire listing shape together with the absent-parent and unreadable-listing states (the carrier-liveness operation's unknown family), all treated as converter-owner darkness for the conjunct.
- Blocked-retry successor: D-18's existing blocked-exit arm; one bounded retry successor armed through the occupied-lane chaining duty's arm shape and coverage consult; the missed-fire repair payload re-derives its repair from disk (the recurring recipe's re-arm in `agents/skills/maintenance/zcode.md`, or the dispatch ladder's park path).
- Monitor-substitute unit: the priced-and-rejected alternative (one prune or convert action bound to payload closeouts); named here only as the disposition of record.
- One-listing budget: the exit's existing single automation-listing read (the coverage consult's shape), reused for this conjunct.

## Why

The intake duties (entry conversion, entry prune, freeze-clear) run only inside the scheduler turn, and the carrier-liveness verdict runs only inside its surveys. When the scheduler carrier misses a fire (witnessed 2026-11-18: the daily scheduler last ran 2026-11-17 11:00 WET and next fired 2026-11-19 11:00 WET), no surface detects the miss, and a dry maintenance exit records lane-local emptiness while the converter is dark.

## Gist & Examples

TLDR: every maintenance exit reads the scheduler parent's fire liveness before recording queue-empty, and a dark-scheduler classification (missed fire, absent parent record, or unreadable listing) routes through the existing blocked-retry arm, so a dark scheduler never masquerades as an empty loop.

Before: a payload session with a dry lane records `loop-exit:queue-empty` while the scheduler parent sits dark; the intake stays unowned for a full cadence with no outside detection.

After: the same exit reads the scheduler parent's state first; a dark-scheduler classification records `loop-exit:blocked-retry` with the repair successor named; a healthy scheduler keeps every existing exit disposition unchanged.

## Outcome

Maintenance exits distinguish "no work" from "the converter's owner is dark" without operator presence.

- A dark-scheduler classification at a dry exit records `loop-exit:blocked-retry` and arms the existing bounded retry successor instead of recording queue-empty.
- A scheduler listing within one cadence keeps today's D-17/D-18 dispositions byte-intact.
- No new gate, validator, primitive, or schema field: the conjunct reads the existing listing surface and composes the existing D-18 tokens.

Gate delta: none. No refusal class, hard gate, fence, protocol layer, or schema field is added or removed; the change extends one existing recording duty's precondition with a read over existing surfaces and names no removed refusal, check, or field. Blocking review-layer duties: none added.

## Assumptions

- assume the carrier listing and the scheduler state file's `parent_automation_id` are sufficient to classify a missed fire; basis: the carrier-liveness verdict already reads the same listing inside surveys (`scripts/execute_plan_runtime.py`).
- assume the blocked-retry arm's existing shape covers the repair action (re-arm per the recurring recipe or the park path); basis: D-18's blocked class and `agents/skills/maintenance/zcode.md` ("Recurring automation recipe").
- assume the sibling conversion plan's execution lands first; basis: the seam rule below.
- Seam rule adjudication: this plan and the sibling `docs/history/plans/2026-11-19-maintenance-dry-exit-conversion-fall-through.md` (authored, `Executed: no` at this authoring) share file sections. Disposition: strictly sequenced execution dependency; this plan's execution waits for the sibling's execution landing and rebases onto its landed text before Task 1 edits; the anchors above name sections the sibling extends, not byte spans, so the rebase composes by union of intents.
Decision points requiring a grill: none remain.

## Standing constraints

- Follow the repository skill-text anti-growth rules; operative text cites the incident row (`docs/history/backlog/2026-11-19-scheduler-dark-converter-prune-dependency.md`) at most once.
- Preserve D-17's preserved stops (primary quota pause, empty-queue stop behind the new conjunct, operator stop) and D-18's token vocabulary byte-intact.
- No new machinery: the conjunct reads the existing listing surface; the pins suite and the byte-budget gate stay green.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a dark-scheduler classification (missed-fire shape, absent parent record, unreadable listing) classifies the blocked-retry routing; a scheduler listing within its cadence classifies every existing disposition unchanged.
- continuity: every dry exit records its D-18 line (token or standing-carrier exemption), now including the dark-scheduler case.

**Done when:**
- the scheduler-liveness conjunct appears at every `loop-exit:queue-empty` recording site the task names, with the blocked-retry routing on a dark-scheduler classification.
- `python3 scripts/skill_text_budget.py --check` exits 0; `bash scripts/scan-public-hygiene.sh` exits 0; `git diff --check` exits 0.

**Ship when:** a maintenance session exiting with a dry lane while the scheduler parent's listing shows a missed-fire shape records `loop-exit:blocked-retry` naming its armed successor, verified from a live exit report or an equivalent recorded rehearsal; evidence owner: the maintenance lane's own closing reports.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `docs/maintenance/operator-directives.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (Task 1)
- `agents/skills/maintenance/SKILL.md` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/quota-policy.md` and the 5h wall arms; reason: the reset-anchored successor is out of this row's scope per the origin row.
- `agents/skills/maintenance/decisions.md`'s continue-loop condition and converter predicate; reason: that surface is the sibling plan's landed scope; this plan only records beside it.
- script additions or changes under `scripts/`; reason: no new primitive per the Machinery admission protocol in `AGENTS.md`.

## Design Invariants (CR Guard)

- The 2026-11-10 continuity contract stands: every exit arms its successor or records its exemption; this plan adds a precondition to one recording class and never a new exit class (D-18, `docs/maintenance/operator-directives.md`).
- The sibling conversion plan owns the converter predicate and the corpus unit; this plan's liveness read composes after it and never duplicates or weakens it (`docs/history/plans/2026-11-19-maintenance-dry-exit-conversion-fall-through.md`, Design Invariants).

## Validation preamble

- `bash scripts/check-no-em-dash.sh added-lines --base 75f7bddce`: pass.
- `bash scripts/scan-public-hygiene.sh`: pass.
- `bash scripts/check_maintenance_pins.sh`: fail in the current worktree on the unrelated `Step 1.2 pre-prompt task-scope digest record (region-scoped)` pin. Source inspection at the recorded branch base confirms the required phrase is absent in `agents/skills/execute-plan/SKILL.md`, and the completed `execute-plan` read-only verification plan records the same pin as a pre-existing baseline red. This plan does not change that file. The checker stops at this pin, so it cannot serve as an acceptance check for this scope. Do not edit or bypass the checker here; the owning execute-plan work remains separate.
- `python3 scripts/skill_text_budget.py --check`: pass, with advisory ratchet messages and zero ceiling breaches.
- `git diff --check`: pass.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-19-scheduler-dark-converter-prune-dependency.md --pre-round`: pass.
- Validation-authoring rule 19 RED-today evidence: not applicable; the plan has no forbidden-phrase sweep. Rule 22 exact-text mechanical audit: not applicable; the plan has no validation span pinned against prescribed task text.

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
git diff --check
```

### Task 1: Add the scheduler-liveness conjunct to the queue-empty recording sites

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/maintenance/operator-directives.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/SKILL.md`

Primary class anchors:
- `D-18` in `docs/maintenance/operator-directives.md`
- `FINAL STEP` in `agents/skills/maintenance/template-authoring.md`
- `FINAL STEP` in `agents/skills/maintenance/template-execution.md`
- `Starvation switch` in `agents/skills/maintenance/SKILL.md`

- [x] `D-18`'s loop-scoped pin records the scheduler-darkness conjunct: given a dry exit whose scheduler-parent read resolves to a dark-scheduler classification, expects `loop-exit:blocked-retry` with the repair successor named instead of `loop-exit:queue-empty` [class: IMPLEMENTATION_REQUIRED]
- [x] The authoring closeout exit (`FINAL STEP` in `agents/skills/maintenance/template-authoring.md`) and the execution-side closeout exit (`FINAL STEP` in `agents/skills/maintenance/template-execution.md`) carry the same conjunct without duplicated duty text: given the same dark-scheduler classification at either surface, expects the same blocked-retry disposition, with each additional surface naming the conjunct's home in one line [class: IMPLEMENTATION_REQUIRED]
- [x] A scheduler listing within one cadence keeps every existing disposition: given `lastRunAt` inside one cadence period, expects today's queue-empty, standing-carrier, quota-wall, operator-stop, and directive-cap records unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] The conjunct reuses the exit's one-listing budget: given a coverage consult already spent one listing read in the same exit, expects the same listing read reused for the conjunct, never a second call [class: IMPLEMENTATION_REQUIRED]
- [x] Integration Points reciprocity: the maintenance module's exit duty and the directives D-18 record name each other's conjunct in one line each [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the sibling plan's `Executed:` metadata flip before Task 1 edits: given the sibling `docs/history/plans/2026-11-19-maintenance-dry-exit-conversion-fall-through.md` still reading `Executed: no`, expects this plan's execution waits per the Assumptions seam [class: REPOSITORY_TEST]
- [x] Run the Validation Commands and confirm each listed check's outcome, recording the pins-suite baseline verdict verbatim when a pre-existing unrelated pin is red [class: REPOSITORY_TEST]
- [x] Commit: `fix: route dark-scheduler exits through blocked-retry` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-19-scheduler-dark-converter-prune-dependency.md` (the origin row) is covered by this plan and is deleted in this completion pass; the scheduler-darkness conjunct landed across D-18's loop-scoped pin and the two FINAL STEP surfaces with the SKILL.md reciprocity line, and the D-18 line records the exit-token duty this run's own closing report carries.
- `docs/history/backlog/2026-11-19-scheduler-dark-plan-cadence-phrasing-residual.md` stays open: the certification residual row owns the cadence-boundary phrasing alignment for the plan text's next natural edit.
