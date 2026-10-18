# Plan: the authoring cross-task trace sweep

Backlog origins (scope of record):
- docs/history/backlog/2026-10-10-plan-review-traces-outcome-timing-and-paths.md
- docs/history/backlog/2026-10-10-plan-ship-condition-task-evidence-alignment.md
- docs/history/backlog/2026-10-10-plan-ship-when-ownership-contract.md
- docs/history/backlog/2026-10-10-plan-pre-review-validation-evidence.md
- docs/history/backlog/2026-10-10-plan-in-session-pre-review-gist-timing.md
- docs/history/backlog/2026-10-10-plan-validation-touched-path-coverage.md
- docs/history/backlog/2026-10-12-plan-review-cutover-invariant-recurrence.md

Driving force: reliability (primary) + efficiency (secondary)

Plan review record: the staging series {reviews_dir}/2026-10-13-plan-review-plan-review-cross-task-lifecycle-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 1.5h total, largest task 1h

## Terms

- `claim-to-task ownership sweep`: the existing authoring-time bullet in the plans skill's Plan Quality Gate structural-failure list (currently at `agents/skills/plans/SKILL.md` line 672): before the first review round, every claim in the four claim sections must trace to an owning task checkbox.
- `cross-task trace sweep`: this plan's broadened form of that sweep: the same authoring-time boundary, four named trace dimensions, still prose discipline with no enforcement code.
- `trace dimension`: one of the four sweep checks: outcome trace, Ship-when trace, validation trace, shared-state trace (defined in Task 1).
- `Ship-when class`: the two Ship-when-only classification names the readiness validator owns (`EXTERNAL_RELEASE_GATE`, `OPERATIONS_FOLLOW_UP`), written in Ship when prose per the plans skill's classification rule.
- `scoped changed file`: a file listed in a task's `Files:` block or the plan's Review Scope must-fix list.

## Why

Seven review findings across two plans traced to one authoring-time hole: the claims sweep checks that claims have owning tasks, but nothing at the same boundary traces outcomes to producer paths and timing, Ship-when conditions to owners and task-produced evidence, or the validation battery to every scoped changed file - so each gap surfaced only as a mid-loop review finding, each costing a full extra round.

## Gist & Examples

TLDR: the authoring claim-to-task sweep grows four named trace dimensions at the same pre-review boundary, so outcome timing, Ship-when ownership and evidence, validation coverage, and shared-state wording are checked by the author before the first review round instead of by reviewers (reliability + efficiency).

Before (today): a plan promises visibility before review but its only emission point is the closeout that runs after review (witnessed r10-r13 of the gist-surface plan, four extra rounds); a Ship-when condition demands a report no task produces (r9) or names no owner or closure witness (r8); a scoped script sits outside both the em-dash scan and the hygiene scan's default roots (r13); a cutover correction to one task leaves another task describing a different lifecycle state (the adapter-removal recurrence).

After (this plan): the author runs one sweep at the existing pre-review boundary and each class is caught before the digest: every outcome names its producer path, emission point, implementing location, and verification pin; every Ship-when condition names its class, evidence owner, measurable closure, and task-produced evidence; every scoped changed file appears in the validation battery with the right scan mode; every shared lifecycle state term reads the same in every task section.

Edge cases: an outcome with no timing dependence states `none` for the emission-point check rather than inventing a deadline; a Ship-when condition with a single evidence source names that one source; a plan with no scoped scripts skips the files-mode clause; a shared-state term that legitimately changes state across tasks (a cutover) is swept for state-wording consistency per task phase, never flattened to one state.

## Outcome

Authoring catches the six authoring-side witnessed cross-task drift classes at the existing pre-review sweep boundary, before a review digest exists; the seventh witnessed recurrence is exec-side and out of scope per Assumption 2.

- Outcome trace: each user-visible outcome traces to its producer path, its emission point relative to the decision that consumes it, its implementing file and section, and a scoped verification pin.
- Ship-when trace: each Ship-when condition names its accepted class, its evidence owner, a measurable closure condition, and evidence sources that trace to explicit task outputs.
- Validation trace: every scoped changed file appears in the validation battery, with an explicit em-dash scan and a public-hygiene scan (files mode, repository root set) for each scoped non-Markdown path.
- Shared-state trace: the plans skill's fold contract-term rule (grep the whole plan for a superseded term, re-derive every matching bullet) is applied at the sweep boundary to every shared lifecycle state term across all task sections, so a correction to one task cannot leave another describing a different state.

Gate delta: no new gate, refusal class, fence, protocol layer, validator, ledger, mandatory round, or approval ask. One existing authoring-time prose bullet (the claim-to-task ownership sweep) gains four named check clauses at the same boundary; the sweep stays advisory authoring discipline exactly like the bullet it extends, priced by the seven witnessed review-round costs in the origins (each a full extra round). The readiness validator's enforcement surface is unchanged; two pins are added to the existing maintenance pins suite (the suite's normal use), pinning the sweep bullet's Ship-when and validation clauses against silent drift. No removal.

## Assumptions

- assume prose discipline suffices: the sweep is the same kind of authoring checklist bullet as the existing claim-to-task sweep, whose witness (a fence hoist found only at r1) shows the class is catchable by authoring discipline; basis: the entry's no-new-machinery arm and the machinery-admission protocol's no-incident-no-gate rule (the incidents witness reviewer-caught misses, not authoring-discipline failures).
- assume the exec-side cutover recurrence stays out of scope: the adapter-removal drift lives across five execute-plan task documents reviewed by intermediate reviews, not inside one authoring plan; execute-plan's intermediate reviews and the existing review-reconciliation churn triggers own that surface; this plan changes only the plans-skill authoring sweep; basis: the scope-arms rule to keep defects that do not share one contract separate.
- assume the sweep bullet's growth fits the skill-text byte budget: the four clauses add roughly one kilobyte to `agents/skills/plans/SKILL.md`; the fleet budget gate is warning-only and currently passes with headroom, and Task 1 validates the gate after the edit; basis: `scripts/skill_text_budget.py --check` OUTCOME: pass at the 2026-10-13 tip.
- assume no readiness-validator change: the sweep is authoring-side; `scope_classification_problem` owns the Ship-when class vocabulary and refuses the Ship-when-only classes on task checklist items while exempting Ship when prose (it checks no Ship-when prose content), so the sweep's Ship-when trace clause is the only authoring-time check for evidence owner and closure; this plan adds no second checker; basis: the classification vocabulary's Ship-when-only classes in `scripts/plan_readiness.py`.

Decision points requiring a grill: none remain.

## Standing constraints

- Plan scripts and validators run under `python3` (3.14); all commands stay repo-relative with no machine-specific absolute paths.
- The edit target is a guard-bearing skill file: run the maintenance pins suite and the skill-text budget gate after every edit, and keep every existing pin's expected span intact (the pins grep literal spans; a reworded span breaks its pin).
- Committed text carries no em-dashes and no absolute paths.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each of the six authoring-side witnessed findings is answerable by exactly one sweep clause, and a sweep run on the gist-surface plan's v1 bytes (mental exercise, recorded in the task) would have caught each of them before r1; the seventh (exec-side) row is disposed by Assumption 2, never claimed as a sweep catch.
- simplicity: the four clauses extend one existing bullet at one boundary; no second sweep, no per-dimension subsections, no enforcement code.
- compatibility: every existing pin on `agents/skills/plans/SKILL.md` stays green; the budget gate stays at OUTCOME: pass.

**Done when:**
- the sweep bullet carries the four named dimensions with the witnesses priced in the Gate delta.
- the two new pins pass and no pin on a touched span fails; the suite's pre-existing unrelated failures (21 maintenance-skill pin failures red at the 2026-10-13 tip, peer-owned resume-carrier spans) are reported, not fixed.
- `skill_text_budget.py --check` still reports OUTCOME: pass with no new advisory breach line for the edited file (the gate is warning-only and cannot fail; the check is the recorded growth evidence, not a pass/fail gate).

**Ship when:**
- landed on main with its dispatch entry pruned by the landing rider per the log's prune rule and all seven origin rows closed through the existing lifecycle.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (the claim-to-task ownership sweep bullet region only)

**Tests:**
- `scripts/check_maintenance_pins.sh` (new pin rows beside the existing plans-skill pins)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The landing's own riders (the frozen entry's prune line, origin-row status flips, the PLAN-PROMPTS-PRUNE receipt) ride the landing branch per the log charter. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/` task-review text; reason: the exec-side cutover recurrence is owned by intermediate reviews and the existing reconciliation triggers (Assumption 2), a separate contract.
- `scripts/plan_readiness.py`; reason: no validator change is admitted (Assumption 4; Gate delta).
- `agents/skills/review-reconciliation/` or review-agents panel text; reason: the entry's reconciliation arm resolves to reuse of existing triggers, not new text.
- Any new fixture, sample file, or checker script; reason: the r12 fixture lesson belongs to the gist-surface plan's own landed scope (its `scripts/fixtures/authoring-gist-sample.md`), not to this prose sweep.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
python3 scripts/fix_plan_em_dashes.py agents/skills/plans/SKILL.md
python3 scripts/fix_plan_em_dashes.py scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files scripts/check_maintenance_pins.sh
```

The hygiene scan runs from the repository root per the user facts document's public hygiene scan script key; the em-dash fence operands are both edited files (the skill file and the pins script; the fence reports the write-time count, and a nonzero substitution count on either operand before commit is a task failure). The pins suite carries 21 pre-existing maintenance-skill failures red at the base tip (peer-owned spans); the pins criterion in this plan is scoped to the touched spans and the two new rows, never a whole-suite green.

### Task 1: Extend the sweep bullet with the four trace dimensions

Files:
- agents/skills/plans/SKILL.md

- [x] Broaden the claim-to-task ownership sweep bullet (line 672 region) into the cross-task trace sweep at the same pre-review boundary; keep the existing claim-sections sentence and its witness byte-identical. Add the outcome-trace clause: each outcome names its producer path, emission point before the consuming decision (the word none when there is no timing dependence), implementing file and section, and a scoped verification pin. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the Ship-when trace clause: a Ship-when condition the author classifies as a release gate or operations follow-up names its accepted class (EXTERNAL_RELEASE_GATE or OPERATIONS_FOLLOW_UP), its evidence owner, a measurable closure condition, and evidence sources that each trace to an explicit task output; a routine completion condition states none for the class and keeps the evidence-owner and closure checks. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the validation trace clause: every scoped changed file appears in the validation battery, with an explicit em-dash scan and a public-hygiene scan (files mode, repository root set) for each scoped non-Markdown path. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the shared-state trace clause: the plans skill's own fold contract-term rule (a fold that changes a contract term must grep the whole plan for the superseded term and re-derive every matching bullet) is applied at this sweep boundary to every shared lifecycle state term across all task sections, per task phase for a legitimate multi-state cutover, so a correction to one task cannot leave another task describing a different state. [class: IMPLEMENTATION_REQUIRED]
- [x] Record in the task completion evidence the row-by-row mental-exercise result for the six authoring-side findings: running the four clauses against the gist-surface plan's pre-review bytes catches r8 (owner), r9 (evidence), r10 (timing and paths), r11 (emission point), r12 (validation scope), and r13 (scan scope); the seventh row (the adapter-removal cutover recurrence) is disposed by Assumption 2 as exec-side surface, not claimed as a sweep catch. [class: IMPLEMENTATION_REQUIRED]

Evidence: the edited bullet reads as one bullet with the four named clauses; the existing claim-sections sentence and witness are byte-identical; no pin whose span this plan touched breaks and the two new pins pass; the budget gate still reports OUTCOME: pass (warning-only) with no new advisory breach line for the edited file.

### Task 2: Pin the new clauses

Files:
- scripts/check_maintenance_pins.sh

- [x] Add exactly two pins beside the existing plans-skill pins: one pinning that the sweep bullet names Ship-when evidence tracing to task outputs, one pinning that it names the per-file em-dash and public-hygiene scans for scoped non-Markdown paths; each pin's fragment is a distinctive multi-word span verified unique in agents/skills/plans/SKILL.md (the plans skill's Validation distinctiveness bar), and each pin carries a provenance comment naming this plan. [class: IMPLEMENTATION_REQUIRED]

Evidence: the two new pins pass and no pin whose span this plan touched fails; the suite's pre-existing failures (21 maintenance-skill pins red at the base tip, unrelated resume-carrier spans owned by other skills) are recorded in the completion evidence as peer-owned baseline red, never repaired here; each new pin's fragment greps exactly one hit in the target file.
