# Plan: no-candidate follow-up disposition contract

Backlog origins (scope of record):
- docs/history/backlog/2026-11-08-plan-execution-no-candidate-follow-up-disposition.md

Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-plan-execution-no-candidate-follow-up-disposition-p237ca1a5-r*.md (the highest rN for this source-plan path is authoritative)
Execution budget: 1h total, largest task 0.5h
Executed: no
Authoring claim: 2026-11-08-plan-execution-no-candidate-follow-up-disposition.md (session sess_2ef2f7d4-cfc2-4dac-8d4b-fde95273bf35)

## Terms

- no-candidate outcome: an execution result in which every measured candidate failed to qualify, or the quantitative objective ended at an evidence-backed stopping point.
- follow-up disposition: the recorded decision for candidate work a run named but did not select: a durable backlog origin carrying a ready-to-dispatch investigation or plan prompt, or a rejected disposition with its ruling evidence.
- user-requested follow-up outcome: an execution outcome whose deliverable is follow-up work the user explicitly requested, rather than a plan-selected objective.
- still-viable follow-up work: concrete next work named by the run's own outputs (a feature note, a recommendation, an unmet objective) that the recorded evidence has not ruled out.
- feature note: the free-form output document a plan's execution may declare as its only artifact; the artifact class the origin row's witness incident orphaned.
- rejected disposition: the explicit no-follow-up decision for an option, recorded with the evidence that rules it out in the durable home Task 2 names.

## Why

An execution that ends in a no-candidate outcome can still leave concrete, viable next work named in its own outputs. Today no durable backlog origin or ready-to-dispatch prompt is created for that work before the origin folds: the witness archive's disposition names the option areas without any dispatch surface, because the existing review-findings backlogging rule reads unselected candidates as experiment results, not findings.

## Gist & Examples

TLDR: authoring and execution closure gain an explicit follow-up disposition duty, so no-candidate runs leave durable dispatchable origins or recorded rejections instead of orphaned feature notes, for reliability.

Before: a runtime-reduction plan ends with all candidates rejected and a feature note naming three next investigations; the plan archives, the origin folds, and the note's leads become unreachable.

After: the same plan declared its disposition rule at authoring, and its execution closed with each still-viable lead either promoted to a backlog origin with a ready prompt (entering the normal investigate/authoring lanes) or recorded as rejected with its evidence.

## Outcome

A plan whose Done-when criteria allow an evidence-backed stopping point, whose tasks name candidate rejection, or whose outcome is a user-requested follow-up declares its disposition rule at authoring; an execution ending in a no-candidate outcome or a user-requested follow-up outcome converts each item of still-viable follow-up work named in its own outputs into a durable backlog origin or a recorded rejected disposition before archive.

- The closure contract requires, prose-only with no gate or refusal, a recorded disposition for still-viable follow-up work before archive, for runs that follow the execute-plan contract; the manual execution lane takes the same conversion through the manual-execution paragraph's pointer (Task 1).
- The rejected option keeps its explicit no-follow-up exit, so the duty never forces every failed experiment to spawn work.
- No new registry, gate, or ceremony: both duties reuse the existing backlog lifecycle and archive flow.

Gate delta: two prose duties added (the authoring-time declaration duty in the plans skill: the Outcome-region rule, the manual-lane pointer, the Integration Points sentence, and the disposition-section admission; the closure-time conversion duty in the execute-plan skill: the conversion placement, the capture-source composition with its capture-hygiene precondition and its finding-shaped field remapping, the receipt refresh, the park-time credit and parked-note materialization, the rejected-disposition home, the provider-side capture-source sentences, and the Integration Points sentence), priced by the origin row's completed-integrity-failure witness (docs/history/backlog/2026-11-08-plan-execution-no-candidate-follow-up-disposition.md, recording the 2026-11-07 runtime-reduction run whose viable leads died with its archive; skill-text citations name the incident descriptively in at most one line without the living backlog path, the durable citation home being the archived completed record the completion pass creates); no gate, validator, refusal class, schema field, or dispatch condition is added; both duties reuse the existing backlog lifecycle (the receiving-review Backlog capture shape) and the existing Phase 4 archive flow.

## Assumptions

- assume ownership splits by actor: the plans skill owns the authoring-time declaration (the plan states the disposition rule while it is written) and the execute-plan skill owns the closure-time conversion (execution performs it before archive); basis: the origin row's suggested correction names both contracts, and each duty sits at the actor that already owns that phase of the lifecycle.
- assume the repository instruction home takes no new rule: AGENTS.md carries no cross-workflow follow-up rule; the executing session reads the execute-plan skill, which will carry the duty, and a duplicated AGENTS.md rule adds operative bytes against the skill-text anti-growth rules; basis: the origin row's own boundary ("do not add a new registry, gate, or ceremony") plus the repository guidelines' anti-growth section.
- assume the duty binds only concrete, still-viable follow-up work named by the run's own outputs: an option whose recorded evidence rules it out takes the rejected disposition and spawns nothing; basis: the origin row's preserve-clause ("do not require every failed experiment to spawn work").
- assume the declaration rides the plan's existing Outcome region rather than a new plan section: the template's Outcome block already owns result statements, so the disposition rule composes there without template growth; basis: the plans skill's Plan Format owns section placement, and a new section would add template bytes without a new contract.
- assume byte payment rides the ratchet discipline, not the origin row's equivalent-bytes phrasing: the three edited files are verified far under their ratchet caps (plans 205336/246407; execute-plan 187793/390981; receiving-review 60790/72627 per scripts/skill_text_budget_caps.json), so the repository anti-growth rule's delete-equivalent-bytes duty (which binds past-cap growth) is not triggered; basis: the landed byte-budget gate is warning-only (breach lines never move the exit; scripts/skill_text_budget.py header; owning plan docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md), and the two-class single-read-ceiling taxonomy is proposed but unlanded (the origin row's equivalent-bytes phrasing echoes the repository anti-growth rule, not this taxonomy) (docs/history/plans/2026-11-07-operative-file-read-budget-gate.md, Executed: no), so if that sibling plan lands first, execution re-reads the caps and re-prices this delta.
- assume the manual execution lane is covered by pointer, not by restatement: the plans skill's manual-execution path gains one sentence directing the completion pass to perform the same conversion duty execute-plan's Phase 4 carries; basis: the origin row names both contracts and its reuse clause (reuse the existing backlog and investigation lifecycle; no new registry, gate, or ceremony), with the repository skill-design guidelines' rule against duplicated concepts across overlapping skills.

Decision points requiring a grill: ownership split plans-vs-execute-plan: no-grill, maintenance-selected receipt (actor alignment per origin row), 2026-11-08, Assumptions; AGENTS.md rule-vs-pointer: no-grill, maintenance-selected receipt (no-edit per anti-growth), 2026-11-08, Assumptions; trigger breadth: no-grill, maintenance-selected receipt (origin's two-arm predicate kept in full: no-candidate outcome and user-requested follow-up outcome), 2026-11-08, Assumptions; wording-evasion residual accepted: the duty arms on the run's own outcome classification, so a run classifying its outcome outside both arms while its result names still-viable work evades it, and no gate is added to catch that per the no-new-machinery receipt.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the two duties compose into one contract over the one two-arm outcome predicate per Terms (no-candidate outcome, user-requested follow-up outcome), stated as the three-arm authoring anticipation in Outcome and Task 1 and the realized two-arm form in Task 2, each naming the same two outcome classes, with no double duty at any single actor.
- anti-growth: the combined addition stays under the three edited files' ratchet caps (scripts/skill_text_budget_caps.json); no new gate, validator, or refusal class.
- executability: each task names its insertion site as a verified current heading and neighbor, not an invented path.

**Done when:**
- the plans skill's Outcome composition prose carries the declaration duty with its authoring trigger in the anticipatory form Task 1 states (Done-when criteria allowing an evidence-backed stopping point, tasks naming candidate rejection, or a user-requested follow-up) and plan-specific disposition content.
- the execute-plan skill's Phase 4 archive intro carries the closure conversion duty ordered before the receipt composition step, with the rejected-disposition arm stated with its durable home.
- `bash scripts/check_maintenance_pins.sh` exits 0 and `python3 scripts/skill_text_budget.py --check` reports no new breach on the three edited files (the budget gate is advisory by construction; the anti-growth evidence is the recorded baseline byte counts 205336/187793/60790 against caps 246407/390981/72627, a wc -c delta on the three files).

**Ship when:**
- none (repository-internal contract text; no external release condition).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `agents/skills/receiving-review/SKILL.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the repository root `AGENTS.md`; reason: the ownership receipt holds the repository-level instruction home at no-edit; a finding there routes to a separate row, not this plan (`docs/AGENTS.md` is the user-level cross-project canon, outside this repository-internal plan).

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: plans authoring-time disposition declaration

Context surface: the plan's Terms, this task, and the plans skill's Plan Format Outcome region.

Files:
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `## Outcome` in `agents/skills/plans/SKILL.md`

- [ ] The Outcome composition prose in the Plan Format region carries the declaration duty: given a plan whose Done-when criteria allow an evidence-backed stopping point, whose tasks name candidate rejection, or whose outcome is a user-requested follow-up, expects the plan's Outcome region to state the plan-specific follow-up disposition rule before review. [class: IMPLEMENTATION_REQUIRED]
- [ ] The disposition rule's content and phrasing: the anticipated candidate leads it names and the route each takes (promoted to a durable backlog origin, or recorded as rejected), stated in the region's plain-word self-contained phrasing. [class: IMPLEMENTATION_REQUIRED]
- [ ] The manual-execution paragraph gains one sentence directing a manual run's completion pass to perform the same conversion duty the execute-plan skill's Phase 4 carries, ordered to precede the manual lane's archive move under the plans skill's completion pass, referenced by skill name and phase, not restated, the manual lane carrying the duty prose-only with no fail-closed net. [class: IMPLEMENTATION_REQUIRED]
- [ ] The plans skill's Integration Points entry for execute-plan gains one sentence naming the disposition contract (the declaration duty here, the conversion duty in execute-plan's Phase 4). [class: IMPLEMENTATION_REQUIRED]
- [ ] The completion-pass disposition bullet in the plans skill's Plan Lifecycle region is extended so the archived plan's existing disposition section also admits rejected follow-up rulings: rows inside the section body, heading unchanged, each marked as a rejected ruling with its ruling evidence and no former-origin path claim. [class: IMPLEMENTATION_REQUIRED]
- [ ] The same bullet's section-append trigger widens so the section is appended whenever rejected rulings exist even with zero promoted items, and the archive-egress clause's inline section naming in the same region covers the rejected-only arm. [class: IMPLEMENTATION_REQUIRED]
- [ ] The heading stays literal per the archive consult's anchor rule; rejected rulings read as the section's non-migrated arm, never a reason to rename the heading. [class: IMPLEMENTATION_REQUIRED]
- [ ] The completion-pass disposition bullet also gains one cross-reference clause pointing at the manual-execution paragraph's conversion duty as ordered before the archive move (prose-only, no fail-closed net). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the maintenance pins suite, the skill byte-budget gate (with its check mode), and the public-hygiene scan over the changed tree, expects all green (exit 0 with OUTCOME: pass; the pre-existing baseline PIN WARN lines and advisory lines are unrelated) with no new breach on the file. [class: REPOSITORY_TEST]
- [ ] Commit: `plans: require a follow-up disposition rule for stopping-point objectives` [class: IMPLEMENTATION_REQUIRED]

### Task 2: execute-plan closure-time follow-up conversion

Context surface: the plan's Terms, this task, and the execute-plan skill's Phase 4 archive intro.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:
- `## Phase 4: Archive Plan` in `agents/skills/execute-plan/SKILL.md`

- [ ] The Phase 4 archive intro carries the conversion duty: given a run ending in a no-candidate outcome or a user-requested follow-up outcome whose result leaves still-viable follow-up work named in its own outputs, expects each item to reach a durable backlog origin with a ready-to-dispatch prompt or a recorded rejected disposition. [class: IMPLEMENTATION_REQUIRED]
- [ ] The conversion is a sanctioned non-finding capture source: given the receiving-review Backlog capture shape scoped to review findings, expects created rows to compose that shape's required-content list in full, including the Driving force, Class, Dedup probe, and Origin class lines. [class: IMPLEMENTATION_REQUIRED]
- [ ] The finding-shaped fields remap for a non-finding lead: Problem statement composed as the investigation lead with its evidence pointer, Exact location pointed at the run outputs naming the lead, Suggested fix as the ready-to-dispatch prompt. [class: IMPLEMENTATION_REQUIRED]
- [ ] Why-not-fixed-now is replaced by the chosen route (promotion or rejection) with its evidence, and the run's own outputs with the archived plan path substitute for the finding-shaped severity and source-reference fields; the capture hygiene scan runs before an item counts as captured. [class: IMPLEMENTATION_REQUIRED]
- [ ] The conversion duty is placed before the pre_archive_receipt composition step: given a disposition completed after the receipt was written, expects the receipt refreshed before the commit is requested, so created origin paths are captured in filed_row_paths and declared_paths. [class: IMPLEMENTATION_REQUIRED]
- [ ] The receipt's plan_digest is re-captured over the final plan bytes the archive commit will carry for the archived path after any same-commit plan body edit (the rejected-disposition rows and the promoted-backlog disposition section alike; appended before the move). [class: IMPLEMENTATION_REQUIRED]
- [ ] The rejected-disposition arm names its durable home: the archived plan's disposition section, the same-commit body edit the archive flow already governs, so the ruling evidence survives session-tmp removal (the section is the one Task 1's extension appends whenever rejected rulings or promotions exist); the composed rejection rows pass the same capture hygiene scan before the body edit. [class: IMPLEMENTATION_REQUIRED]
- [ ] A follow-up disposition already filed at a pause counts as recorded only where the Park-time record filing paragraph's worktree arm committed the record with its tracked landing path; remaining still-viable follow-up work is verified for coverage rather than re-filed. [class: IMPLEMENTATION_REQUIRED]
- [ ] A primary-placement parked-run filing note is an outstanding obligation, not a recorded disposition: the conversion materializes it (verifies the named record in the tree, or files the durable origin or rejected ruling itself, recording the vehicle) before the receipt refresh. [class: IMPLEMENTATION_REQUIRED]
- [ ] The execute-plan skill's Integration Points entry for the plans skill gains one sentence naming the disposition contract (the conversion duty here, the declaration duty in the plans skill's Outcome composition). [class: IMPLEMENTATION_REQUIRED]
- [ ] The receiving-review skill's Backlog capture Capture sources line and its execute-plan Integration Points entry name the Phase 4 follow-up conversion as the Capture sources line's third entry and its first non-finding one, one sentence each, provider-side by reference. [class: IMPLEMENTATION_REQUIRED]
- [ ] The section's Scope line gains the matching carve-out naming the conversion as composing the item shape outside the review-findings scope (mirroring the learn Step 1.8 disjointness carve-out). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the maintenance pins suite, the skill byte-budget gate (with its check mode), and the public-hygiene scan over the changed tree, expects all green (exit 0 with OUTCOME: pass; the pre-existing baseline PIN WARN lines and advisory lines are unrelated) with no new breach on its two files. [class: REPOSITORY_TEST]
- [ ] Commit: `execute-plan: convert viable follow-up work to durable origins before archive` [class: IMPLEMENTATION_REQUIRED]
