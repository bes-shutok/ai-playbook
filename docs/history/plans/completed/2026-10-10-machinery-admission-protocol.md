# Plan: Machinery admission protocol as durable machinery (guidelines home, investigate admission arm, quarantine routing, D-12 supersession)

Backlog origin: docs/history/backlog/2026-10-10-machinery-admission-protocol.md (the PLAN-PROMPTS entry `machinery-admission-protocol` carries the operator's root-cause prompt; the operator's 2026-10-10 question "can we update instruction skill, etc to make it less probable" covers authoring dispatch)
Driving force: automation
Design input: docs/maintenance/machinery-blocker-audit-2026-10-09.md (Part 5 items 1, 2, 3, and 4; the 2026-10-10 Reconciliation section)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-machinery-admission-protocol-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 45m
Authoring claim: docs/tmp/authoring-claims/2026-10-10-machinery-admission-protocol.md (session sess_96f4788f-79eb-4f93-a2f7-006692f56eb8)

## Terms

- Machinery: a gate, validator, lock, ledger, or required ceremony — anything whose breach can block, refuse, or record a lane.
- Admission test: the four-field statement a machinery-adding change must carry — the concrete incident it prevents (with a link), the expected catch frequency, the false-positive cost, and a sunset or review date — plus the no-incident-no-blocking-gate rule and the warning-only-then-promote path.
- Machinery-internal row: an open backlog row whose value outcome is machinery itself (no user-facing fix, no feature, no measured cost reduction). The survey's existing origin-class token `self-serving` is its operative signal; no new classification pass is added.
- Quarantine routing: the `machinery-quarantine` skip that keeps a machinery-internal row out of every dispatch path — the span set Task 3 names (the survey's origin-token/skip area, the D2 selection rules, the ad-hoc arm's three operative spans, and the log-mediated authoring path: the monitor investigate duty's skip clause, the per-cycle harvest duty's selection, the dispatch duty's entry hold) — and carries it to the operator's weekly batch review. The row carries a `Quarantine:` header line in place — no new list file, no new ledger.
- Vendored twin: `~/.agents/skills` is a symlink to this repository's PRIMARY checkout's `agents/skills` directory (re-derived 2026-10-10), so skill-file edits reach the runtime registry when this plan's branch lands in that checkout: the merge-locked landing is the deploy, and until it lands the live loop keeps loading the pre-landing files (old behavior, no breakage).

## Why

The machinery audit's Part 5 prescribed the admission test, but it lived only in audit prose: no operative contract referenced it. The witnessed failure is 2026-10-10 — three routed plan entries added machinery (one a hard-exit gate, two tracking surfaces) with zero admission wording, caught only because the operator read the routing by hand. The root cause the operator asked about: a governance protocol with no operative home binds nobody. This plan gives the protocol its four homes — the citable guidelines text, the authoring-time arm where recommendations form, the routing that stops machinery-internal rows from auto-becoming plans, and the directive record re-pointed at the durable home — while obeying the protocol itself: this plan lands prose and routing only, no new gate, validator, lock, or ledger.

## Gist & Examples

TLDR: land the machinery admission test as a repository-guidelines section, give the investigate skill's Stage 3 an admission step and Stage 4 an admission line, route machinery-internal backlog rows to the operator's weekly batch review instead of the authoring lane, and re-point D-12's admission subordination clause at the durable home.

Before: an investigation recommends a new validator; Stage 3 prices the witnessed cost and picks the smallest arm but never asks the admission questions; the entry emits with evidence-cited dispositions and zero admission wording; the plan lands a blocking gate; the operator catches it by hand.

After: the same recommendation cannot emit a valid entry without the four admission fields or an explicit rejection of the machinery arm (the skill text requires it — no script gate is added); the guidelines carry the citable test so every session and review panel has one home to check; a machinery-internal backlog row is skipped by the span set Task 3 names (the survey, D2 selection, the ad-hoc arm's spans, and the log-mediated selection spans) with reason `machinery-quarantine` and surfaces in the operator's weekly batch instead of consuming an authoring cycle.

Edge cases: a recommendation whose machinery arm has no incident routes that arm as rejected with the missing-incident absence named — the entry itself stays valid; a group whose members split between machinery-internal and operator-value routes per member (the existing composition rule), not per group; a row carrying `Consumer urgency:` (or a consumer/pet origin) is operator-value by construction and never quarantined by this routing; the weekly batch review disposes rows in one operator decision (cover, reject, keep open) recorded in the rows themselves.

## Outcome

- The repository guidelines (the repo-root `AGENTS.md`) carry a new `## Machinery admission protocol` section: the admission test, the no-incident rule, the warning-only landing with first-true-catch promotion and the pre-registered machinery-registry removals row, deletion as a first-class outcome, and the bounded-repair rule.
- `agents/skills/investigate/SKILL.md` Stage 3 carries the admission step (a machinery-adding recommendation states the four fields in the entry or routes the arm as rejected); Stage 4's entry contract carries the admission line for such entries.
- `agents/skills/maintenance/SKILL.md` skips machinery-internal rows with skip reason `machinery-quarantine` across the span set Task 3 names (the survey, D2 selection, the ad-hoc arm's spans, and the log-mediated selection spans) and refreshes the row's `Quarantine:` header line; the existing `weekly-skill-review` registry task (`docs/maintenance/recurring-tasks/weekly-skill-review.md`, audit kind, 7-day cadence) gains one review step presenting quarantined rows to the operator as one batch decision.
- Directive D-12's admission subordination clause (`docs/maintenance/operator-directives.md`) cites the guidelines section as the protocol's durable home.
- Bounded repair lands as citable guidelines text (Task 1); operative lane routing of gate-block responses is deliberately out of scope — the loop's existing bounded-retry, skip-with-report, and park-for-operator arms already embody the rule, and this plan adds no new lane text for it.

Gate delta: prose and routing only. No new gate, validator, lock, ledger, or required ceremony lands; no state-schema change; no script bytes change except pin re-aims beside provenance in `scripts/check_maintenance_pins.sh` when a Task 2 or Task 3 insertion moves an anchor (`scripts/check_investigate_entries.py` stays untouched — the admission requirement is skill-text contract, the rejected validator alternative stays rejected); prose sections are not registered machinery, so the machinery registry gains no row. The machinery inventory check is a consultative delta check in this plan, not an exit-0 gate (the baseline is already red; see Validation Commands). The plan itself demonstrates the admission wording it lands: the quarantine routing extends the survey's existing skip-reason family, the D2 selection rules, the ad-hoc arm's existing spans, and the log-mediated selection spans (the investigate duty's skip clause, the harvest duty's selection, the dispatch duty's entry hold) — their predicates classify priority, gating, and coverage, none classifies value outcome — and it is warning-shaped by construction (a skip with a recorded reason, nothing that blocks).

## Assumptions

- The general home is a dedicated top-level section in the repository guidelines, placed directly after `## Agent-Specific Runtime Safety`; the guidelines are the one instruction surface every session and review panel already loads. Basis: the origin row's Expected item 1 ("the admission test in the repository guidelines as its general home").
- The machinery-internal signal is the survey's existing origin-class token `self-serving`, judged from the row's `Origin class:` header or body per the survey's existing rules; no second classification vocabulary is introduced. Basis: the survey's origin-token paragraph (`agents/skills/maintenance/SKILL.md` Step 1) and the audit's Part 5 item 1 definition of machinery-internal value.
- The weekly batch review rides the existing `weekly-skill-review` registry task as one added review step, not a new task, lane, or ledger. Basis: the registry file on disk (`docs/maintenance/recurring-tasks/weekly-skill-review.md`, id, cadence 7, kind audit; re-derived 2026-10-10) and the entry's no-new-surface constraint.
- The investigate skill edit keeps every pinned span intact or re-aims pins beside their provenance in the same change. Basis: the pins suite covers the investigate skill's eligibility and privacy contract (the entry prompt's constraint), and insertion of new bullets leaves existing spans in place.
- The D-12 re-point is a one-clause edit plus a dated corrections line in the record; the directive stays active until the landing, per the home's supersession convention (a directive lift is a one-file commit to the home). Basis: `docs/maintenance/operator-directives.md` D-12's own expiry note ("the durable forms ... route through the plan prompts").
- The anti-growth-rule-set plan (a sibling of this one, in authoring in parallel) also edits the repository guidelines; the two landings serialize under the merge landing lock and the later landing reconciles adjacent-section drift; neither plan gates on the other. Basis: the audit Reconciliation section naming both as children of Parts 4-5, and the merge-lock landing discipline.
- The machinery inventory check is red at the authoring tip and stays consultative here: `python3 scripts/machinery_inventory.py --check` exits 1 with 16 pre-existing failures (15 unregistered script files plus the `state-field:queued_execution` finding) on the primary checkout and this clean worktree alike, re-derived 2026-10-10; the maintenance survey already treats the check's non-zero exit as a consultative finding, never a blocked turn. Basis: the executed run at the tip and the survey's machinery-consult arm semantics.
- Machinery-internal rows already open at landing are quarantined by the first survey turn after it (the routing is survey-time; no bulk migration task). Basis: the routing's operative home is the survey's per-item read.

Decision points requiring a grill: none remain (the operator's 2026-10-10 root-cause question ordered the durable fix; the entry records the operator go and the audit's Part 5 items 1-2 fix the shape; the open placement and classification questions are carried as stated assumptions above).

## Standing constraints

- The plan obeys the protocol it lands: procedural text and routing only — no new gate, validator, lock, ledger, or required ceremony; nothing here can block a lane before any catch (the routing is a skip with a recorded reason; the skill contract binds authoring-time text).
- Every pinned span in an edited file stays intact or is re-aimed beside its provenance in the same change; the pins suite, the public hygiene scan, and the parallel-work regressions suite (`python3 scripts/test_plan_review_boundary_examples.py`) stay green at each task landing; a red suite at a task boundary stops the task for reconciliation, never a weakened check.
- Skill edits reach the runtime at landing (the twin symlink); no separate deploy step, nothing pushed to origin, no machine-specific absolute paths in any edited file.
- The maintenance skill edit touches only the survey's origin-token/skip area, the D2 selection rules, the ad-hoc arm's three operative spans (the Ad-hoc backlog arm eligibility test, the Exec-mode selection rule's candidate set, the Ad-hoc candidate consults skip list), and the log-mediated authoring path's spans (the monitor investigate duty's skip clause, the per-cycle harvest duty's selection, the dispatch duty's entry hold) — no lane-guard, no failure-cap, no state-schema bytes move.
- Suite discipline: the pins suite, the hygiene scan, and the parallel-work regressions suite are hard gates (a red run stops the task for reconciliation); the machinery inventory check is exempt from that rule — it is the consultative delta check the Validation Commands define, and its already-red baseline never blocks a task.
- Rollback arm: revert the offending task's commit (pure prose and routing reverts restore the prior tree exactly); the D-12 clause restores to its pre-point text; no machine-local deploys exist to hand-clean.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every repository-state fact the landed text asserts (file paths, section names, registry task id and cadence, the survey token names) re-derived from disk at write time; the four admission fields named exactly as the audit's Part 5 item 2 states them; every cross-reference resolves on the executed tree.
- regression safety: the pins suite, the hygiene scan, and the parallel-work regressions suite pass before and after each landing; the machinery inventory check's post-landing failure set is a subset of its pre-landing baseline (16 failures at the 2026-10-10 tip per the Assumptions — this plan registers no machinery, so the set must not grow).
- scope discipline: the changes touch only `AGENTS.md`, `agents/skills/investigate/SKILL.md`, `agents/skills/maintenance/SKILL.md`, `docs/maintenance/operator-directives.md`, and `docs/maintenance/recurring-tasks/weekly-skill-review.md` (plus conditional pin re-aims in `scripts/check_maintenance_pins.sh`).

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- An investigation recommending a new gate cannot emit a valid entry without the admission wording or an explicit arm rejection (the Stage 3/Stage 4 text requires it).
- Machinery-internal open rows record skip reason `machinery-quarantine` at the next survey and carry the `Quarantine:` line.

**Ship when:**
- The origin row's ship-when holds on the executed tree: the guidelines carry the test, D-12 cites the durable home, and machinery-internal rows route to the weekly operator batch instead of the authoring lane.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `AGENTS.md` (Task 1, new section)
- `agents/skills/investigate/SKILL.md` (Task 2, Stage 3 bullet + Stage 4 line)
- `agents/skills/maintenance/SKILL.md` (Task 3, survey skip + D2 selection routing + ad-hoc arm spans + log-mediated path spans)
- `docs/maintenance/recurring-tasks/weekly-skill-review.md` (Task 3, batch review step)

**Tests:**
- `scripts/check_maintenance_pins.sh` (conditional pin re-aims beside provenance if a Task 2 or Task 3 insertion moves an anchor; otherwise bytes unchanged)

**Docs:**
- `docs/maintenance/operator-directives.md` (Task 4, D-12 clause re-point + corrections line)
- `docs/history/backlog/2026-10-10-machinery-admission-protocol.md` (read-only this plan; the landing rider deletes it in the landing change naming this plan as the covering witness, per the repository guidelines' commit rule — not a task)

**Read-only (referenced, never edited):**
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (the protocol's origin prose)
- `scripts/check_investigate_entries.py`, `scripts/machinery_inventory.py` (validators; bytes unchanged)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-10-machinery-admission-protocol.md (Status: open; the landing rider deletes the row in the landing change, naming this plan as the covering witness per the repository guidelines' commit rule)

## Validation Commands

- `bash scripts/check_maintenance_pins.sh` (exit 0)
- the public hygiene scan from the repository guidelines (exit 0) over the changed files
- `python3 scripts/test_plan_review_boundary_examples.py` (exit 0)
- `python3 scripts/machinery_inventory.py --check` (consultative delta, never an exit-0 gate: the failure set over the executed tree must be a subset of the pre-landing baseline recorded in the Assumptions — 16 failures at the 2026-10-10 tip; the set must not grow)
- `grep -c "Machinery admission protocol" AGENTS.md` equals 1 (the section exists exactly once)
- `grep -c "machinery-quarantine" agents/skills/maintenance/SKILL.md` is at least 1 (the skip reason of record is spelled)
- `git grep -c "Machinery admission protocol" docs/maintenance/operator-directives.md` is at least 1 (D-12 cites the durable home)

### Task 1: guidelines home — the admission test section

- [x] Insert one new top-level section into `AGENTS.md` directly after the `## Agent-Specific Runtime Safety` section, before `## Vendored Asset Sync Rules`, with exactly the text of the code block below this checklist item. [class: IMPLEMENTATION_REQUIRED]

The section text (the audit's Part 5 items 2, 3, and 4 restated as checkable rules; item 1's quarantine routes as Task 3's operative routing, not guidelines text; no other guidelines section is edited):

```markdown
## Machinery admission protocol

- Any plan or change that adds a gate, validator, lock, ledger, or required ceremony states, in the plan or the change itself: the concrete incident it prevents (with a link), the expected catch frequency, the false-positive cost, and a sunset or review date. No incident, no blocking gate.
- New machinery lands warning-only or read-only and is promoted to blocking only after its first true catch, with a pre-registered machinery-registry removals row naming the surface, its sunset, and its promotion criteria.
- Deletion is a first-class outcome: every machinery plan names what it removes or simplifies; a plan that grows net machinery requires operator approval.
- Bounded repair: when a gate blocks a lane, the allowed responses are a bounded retry, skip-with-report, or park-for-operator. Editing a gate or validator mid-lane to unblock oneself is forbidden without a plan.
```

- [x] Run the pins suite and the public hygiene scan green before the edit and again after the commit; land this task as its own commit on the authoring branch. [class: REPOSITORY_TEST]

### Task 2: investigate skill — the authoring-time admission arm

- [x] Make two insertions into `agents/skills/investigate/SKILL.md`, both additive bullets that leave every existing span byte-identical (re-aim any pin whose anchor the insertion moves, beside its provenance, in the same change): the Stage 3 admission bullet and the Stage 4 admission-line bullet, with exactly the text of the two code blocks below. [class: IMPLEMENTATION_REQUIRED]

1. In `### Stage 3: possibility space`, append one bullet to the existing list, after the smallest-arm bullet:

```markdown
- Admission step: a recommended resolution that adds a gate, validator, lock, ledger, or required ceremony carries the machinery admission test in the entry — the concrete incident it prevents (with a link), the expected catch frequency, the false-positive cost, and a sunset or review date — or routes that arm as rejected with the missing-incident absence named in checker-passing form ("no witnessed incident", which carries the evidence-basis marker the entry checker requires; the protocol's durable home is the repository guidelines' Machinery admission protocol section); removal-shaped recommendations need no admission wording.
```

2. In `### Stage 4: log entry emission`, append one bullet after the existing entry-carries bullet:

```markdown
- An entry whose recommendation adds machinery carries the admission line: the four admission fields of the guidelines' Machinery admission protocol section, or the explicit rejection of the machinery arm with the missing-incident absence named. An entry omitting both is not a valid emission. An open item whose survey record carries skip reason `machinery-quarantine` is not eligible for entry emission: the work-type verdict records the quarantine skip instead of routing the item to either log.
```

No checker script is edited or added: the contract is the skill text (the validator-script alternative is rejected in the dispatching PLAN-PROMPTS entry `machinery-admission-protocol`, citing the audit's Part 5 item 5).

- [x] Run the pins suite green after the insertions (re-aimed pins included); land this task as its own commit on the authoring branch. [class: REPOSITORY_TEST]

### Task 3: quarantine routing — maintenance survey/D2 skip and the weekly batch step

- [x] Edit `agents/skills/maintenance/SKILL.md` across the ad-hoc and authoring selection surfaces — the Step 1 survey's origin-token area, the D2 selection rules, the ad-hoc arm's operative spans (the Ad-hoc backlog arm bullet's eligibility test, the bullet that declares itself the arm's one home; the Exec-mode selection rule's candidate-set construction; the Ad-hoc candidate consults skip list), and the log-mediated authoring path (the monitor investigate duty's skip clause gains the `machinery-quarantine` skip, so no entry is emitted for a quarantined row; the per-cycle harvest duty's selection states the same exclusion over the class — a machinery-internal row is never a harvest-pass selection candidate whether or not a survey has recorded the skip yet; the dispatch duty holds any PLAN-PROMPTS entry whose origins are exclusively open rows recorded `machinery-quarantine`, and when the operator-driven batch turn records a reject disposition for an entry's origins, the same turn prunes the held entry under the log's write discipline, while the duty's next-distinct-entry scan never hides a distinct untaken entry behind a quarantine hold): an open item whose origin token is `self-serving` (machinery-internal value per the guidelines' Machinery admission protocol section) is recorded with skip reason `machinery-quarantine` in the survey output, is never an authoring or ad-hoc dispatch candidate — the exclusion stated in each of those spans so no lane path re-admits the row — and the routing session adds or refreshes the row's `Quarantine:` header line (naming the date) as a targeted row edit. The skip is shaped like `profile-deferred`: recorded, never blocking, never a turn error. A row carrying a `Consumer urgency:` header, or Priority critical/high with Scope naming shared skills under `agents/skills/`, or a consumer/pet origin is never quarantined — both legs of the existing shared-skill consumer-urgency exception stay in parity with this skip. Text stays inside the existing survey, D2, ad-hoc, and monitor-duty spans — no new top-level arm, no lane-guard or state-schema edit. [class: IMPLEMENTATION_REQUIRED]
- [x] Edit `docs/maintenance/recurring-tasks/weekly-skill-review.md`: insert one new section between `## Defect classes` and `## Output discipline` — the quarantine batch presentation. The run reads the open top-level backlog rows carrying a `Quarantine:` header line and records one batch presentation (row list plus one-line value summaries) as an operator-facing quarantine section appended to `docs/maintenance/skill-review-log.md` beside the run's aggregates record; amend the Output discipline's aggregates-only rule in the same edit to name this section. The task body runs verbatim in a fresh unattended session, so the run stages proposed dispositions marked as proposals, never final: a row's quarantine disposition (cover by a named plan, reject, or keep open) is recorded in the row only by an operator-driven turn acting on the presented batch. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite and the hygiene scan green after both edits (re-aim any pin whose anchor a Task 3 insertion moved, beside its provenance, in the same change); land this task as its own commit on the authoring branch. [class: REPOSITORY_TEST]

### Task 4: D-12 supersession re-point

- [x] In `docs/maintenance/operator-directives.md`, edit D-12's `admission subordination` clause to cite the durable home: the clause keeps its warning-only/promotion/removals-row content and gains the citation "the protocol's durable home is the repository guidelines' Machinery admission protocol section (landed by docs/history/plans/completed/2026-10-10-machinery-admission-protocol.md), which this clause defers to on conflict", and the record's witness section gains one dated corrections line naming the re-point and this plan. No other D-record is touched. [class: IMPLEMENTATION_REQUIRED]
- [x] Run every command in `## Validation Commands` on the executed tree, confirm the origin row's three ship-when bullets, record the receipts, and land this task as its own commit on the authoring branch. [class: REPOSITORY_TEST]
