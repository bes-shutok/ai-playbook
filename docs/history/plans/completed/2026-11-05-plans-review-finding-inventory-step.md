# Plan: Review-driven plans close the source-finding inventory

Backlog origin: docs/history/backlog/2026-11-03-plans-review-finding-inventory.md
Driving force: code-quality
Plan review record: the staging series {reviews_dir}/YYYY-MM-DD-plan-review-plans-review-finding-inventory-step-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (f6ca1a6a38fa3e05ea56531527ab434f825fe30b)
Authoring claim: 2026-11-03-plans-review-finding-inventory.md (session sess_cae8da77-41fe-494e-a47c-2699c92d0025)

## Terms

- Review-driven plan: a plan whose origin request is explicitly based on feedback from a multi-finding code review (a review record or review thread naming more than one finding).
- Phase 1: the plans skill's requirements discovery phase, the region this plan edits.
- Tracker and linked-contract sources step: the existing conditional Phase 1 source-reading step for tracker-linked requests, the insertion point's sibling.
- Requirements buffer: the Phase 1 authoring scratch record ({tmp_dir}/plan-requirements-<slug>.md) where discovery facts and decisions are recorded before tasks are written.
- Source-finding inventory: the enumeration the new Phase 1 step produces: every finding carried by the driving review records, each classified and then mapped into plan scope or excluded.
- Snapshot status: the classification of a finding against the reviewed source; the four classes are present in the reviewed snapshot, introduced later, conditional or unverified, and invalid.
- Evidence-based exclusion: a recorded exclusion of a finding from plan scope that names the evidence settling it; for a valid finding outside the plan's requested scope, the evidence is the recorded scope-extension grill decision (defer-to-backlog).

## Why

Plans drafted from multi-finding review feedback have omitted actionable findings from their scope, and plan review then needed a corrective round before the plan represented the requested work. Closing every source finding against the reviewed source during authoring moves that check to where it is cheapest, so review validates mapping quality instead of discovering omissions.

## Gist & Examples

TLDR: review-driven plans close the source-finding inventory into plan scope or recorded exclusions during authoring, so plan scope matches the requested review feedback without a corrective review round.

Before: a plan addressing a multi-finding review was drafted from the request text alone; a later plan review found one actionable finding absent from the inventory and the worker sample, and certification waited on a corrective amendment (witness: review record F3 over the 2026-11-02 review-freshness plan, cited in the origin item).

After: the authoring session reads every finding in the driving review records, classifies each against the reviewed snapshot, and maps each actionable one to a task and an observable acceptance scenario or records an evidence-based exclusion; the plan carries the source-finding inventory, and plan review validates mapping quality rather than completeness.

Edge cases: single-finding review feedback does not fire the step; a finding the reviewed snapshot already fixed upstream is classified and excluded with evidence; a finding judged invalid is classified invalid with the reason; review records that combine comments never support inferred comment counts or authorship, so the inventory enumerates behaviors, never counts.

## Outcome

Authoring sessions producing plans from multi-finding review feedback close every source finding into mapped scope or recorded exclusion before the plan is drafted.

- The plans skill's Phase 1 carries one conditional, prose-only source-finding inventory step for review-driven plans.
- Every actionable finding maps to a task and an observable acceptance scenario, or carries an evidence-based exclusion, in the authored plan.
- No validator, gate, worker, or review round is added; the step is authoring prose only.

Gate delta: one authoring-blocking prose condition added to Phase 1 (the finding-closure duty rides the plans skill's existing requirements-validated hard gate); no machine-enforced gate, refusal class, fence, protocol layer, or schema field added or removed; no dispatch-pausing condition introduced. Growth pricing: one bold-lead paragraph of new operative text with no compensating deletion available (no overlapping sibling text exists to delete), priced by the completed-integrity-failure witness: the corrective review round recorded in the origin item (an actionable finding omitted from the plan inventory was caught at review, r16 F3) is the integrity failure this requirement prevents.

## Assumptions

- assume the step renders as one conditional prose step directly beside the Tracker and linked-contract sources step in Phase 1; basis: the origin item's Exact location names two regions ("Phase 1 requirements discovery and Exploration discipline"), and the single Phase 1 sibling step is the simpler-design selection over splitting the duty across both regions, keeping one home for source-record reading duties (comparison recorded in the requirements buffer).
- assume scope stays limited to plans derived from multi-finding review feedback; basis: the origin item's Fix shape fixes that limitation, and a broader trigger (every plan) would add unpriced authoring overhead without a witnessed failure.
Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the step fires only for review-driven plans (multi-finding review feedback) and its classification vocabulary matches the origin item's four snapshot statuses
- simplicity: prose only; no validator, gate, worker, or review round added; the insertion lands beside the existing conditional source steps without restructuring Phase 1
- maintainability: the step reads as a sibling of the Tracker and linked-contract sources step and cites its witness in at most one line, naming the incident by record id and date

**Done when:**
- agents/skills/plans/SKILL.md carries the new conditional step in Phase 1 directly after the Tracker and linked-contract sources step
- the step requires reading the complete relevant review and thread records and comparing each finding's behavior against the identified source snapshots
- the step carries the four-way snapshot classification (present in the reviewed snapshot, introduced later, conditional or unverified, or invalid) and states that it classifies temporal status only, never scope routing
- each actionable finding maps to plan work and an observable acceptance scenario, or carries an evidence-based exclusion; a valid finding outside the requested scope routes through the existing scope-extension grill, and a finding with neither mapping, exclusion, nor grill decision blocks plan writing
- the step forbids inferring exact comment counts or authorship when review records combine comments
- the working-tree diff for this plan touches only agents/skills/plans/SKILL.md (no validator, gate, worker, or review-round bytes)
- the Validation Commands below pass

**Ship when:**
- none: repository-local skill-text change with no deployed or cross-team surface

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- agents/skills/plans/SKILL.md (Task 1)

**Tests:**
- none (prose-only change; no validator or test surface is touched)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- scripts/ validators, gates, and test files; reason: the origin item's Fix shape explicitly adds no validator, gate, worker, or review round
- docs/history/plans/completed/2026-11-02-review-freshness-and-code-coverage-gaps.md; reason: archived plan, cited as witness only, never edited by this plan

## Validation Commands

```bash
bash scripts/check-no-em-dash.sh file agents/skills/plans/SKILL.md
bash scripts/scan-public-hygiene.sh
python3 scripts/check_maintenance_pins.sh 2>/dev/null || bash scripts/check_maintenance_pins.sh
git status --short  # agents/skills/plans/SKILL.md must be the only changed path
git diff HEAD --stat
```

### Task 1: Add the source-finding inventory step to Phase 1

Context surface: the plan's Terms, this task, and the origin item as the scope of record; referenced, never restated.

Files:
- agents/skills/plans/SKILL.md

Evidence:
- Origin item: docs/history/backlog/2026-11-03-plans-review-finding-inventory.md (the scope of record; its Observed versus expected and Fix shape sections define the step's content)
- Witness: the 2026-11-03 r16 F3 corrective round recorded in the origin item's Source reference
- Insertion point: directly after the Tracker and linked-contract sources (tracker-linked requests) step in the Phase 1 source-rules region, as a sibling conditional source-reading step

Acceptance:
- [x] The new step renders as one bold-lead prose paragraph in Phase 1 directly after the Tracker and linked-contract sources step, triggered only when the plan is explicitly based on feedback from a multi-finding code review [class: IMPLEMENTATION_REQUIRED]
- [x] The step requires reading the complete relevant review and thread records and comparing each finding's behavior against the identified source snapshots before any task is written [class: IMPLEMENTATION_REQUIRED]
- [x] The step classifies each finding into the four-way snapshot vocabulary (present in the reviewed snapshot, introduced later, conditional or unverified, or invalid), records the classification with its evidence in the requirements buffer, and states that the vocabulary classifies temporal status only, never scope routing [class: IMPLEMENTATION_REQUIRED]
- [x] The step maps every actionable finding to plan work and an observable acceptance scenario (the mapped classification landing in the plan's task acceptance scenarios, never a new plan section), or records an evidence-based exclusion riding the existing Assumptions or Decision-points receipts [class: IMPLEMENTATION_REQUIRED]
- [x] The step routes a valid finding outside the requested scope through the existing scope-extension grill with the recorded decision as the exclusion's evidence, and blocks plan writing when a finding carries neither mapping, exclusion, nor grill decision [class: IMPLEMENTATION_REQUIRED]
- [x] The step forbids inferring exact comment counts or authorship when review records combine comments; the inventory enumerates behaviors, never counts [class: IMPLEMENTATION_REQUIRED]
- [x] The step's one-line witness citation names the incident by record id and date (for example, "witness: the 2026-11-03 r16 F3 corrective round") and never carries a literal `.ai-playbook/reviews/` runtime path [class: IMPLEMENTATION_REQUIRED]
- [x] The working-tree diff touches only agents/skills/plans/SKILL.md; no validator, gate, worker, or review round is added [class: REPOSITORY_TEST]
- [x] The Validation Commands pass (em-dash check, public hygiene scan, pins suite) [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-03-plans-review-finding-inventory.md: covered by this plan (flipped to its covered witness by the execution landing; see the origins-gate receipt in the execution run record).
