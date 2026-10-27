# Plan: Extend weekly skill review to the live prose corpus

Backlog origin: docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md
Authoring claim: docs/tmp/authoring-claims/2026-10-04-maintenance-doc-hygiene-review.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-maintenance-doc-hygiene-review[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.0h total, largest task 1.5h

## Terms

- **Origin class:** the backlog row eligibility classification; this origin’s non-enum value is treated as survey-time `unknown` and left unchanged.
- **`rotation_cursor`:** the existing weekly-skill-review state value naming the next review unit.
- **Live prose corpus:** tracked Markdown files in skill directories except `synced/`, open top-level backlog Markdown files, and Markdown files under `docs/maintenance/`; archived backlog and plan trees are excluded.
- **Review unit:** one top-level skill directory, one live Markdown file under `docs/maintenance/`, or one open top-level backlog Markdown file. The rolling prompt logs are not review units because the maintenance router processes them separately.
- **SOT:** source of truth; the single canonical file that owns a topic under `agents/skills/doc-hierarchy/content-ownership.md`.

## Why

The repository has repeated, witnessed em-dash cleanup cost, while the existing weekly review does not cover live maintenance docs or open backlog rows and does not consume the repetition and byte-budget reports it already has. Extending its current rotation and cleaning the measured residue closes that gap without adding another audit lane.

## Gist & Examples

TLDR: Clean the current prose residue and extend the existing weekly review to cover live docs, open backlog rows, and its read-only hygiene reports, reducing repeated operator cleanup.

Before: the seven-day audit rotates only over skill directories, while the live docs and backlog corpus can retain prose defects and the duplication and byte-budget tools have no weekly consumer.

After: a six-run rotation reviews skill, maintenance-doc, and open-backlog units; every run records em-dash, duplication, byte-budget, source-of-truth placement, and standing prose-rule findings in the existing skill-review log.

Edge cases: `synced/`, archived history, and the two rolling prompt logs stay outside the review-unit rotation; quarantined rows remain proposals for an operator batch decision.

## Outcome

The existing weekly review regularly reports hygiene and source-of-truth placement findings across the live corpus without adding a blocker or a second audit lane.

- The 21 measured current em-dash hits are removed with meaning preserved.
- Every review unit is examined in a six-run rotation, while the full-corpus diagnostics run on each weekly audit.
- The existing log records path-based findings from the semantic prose review and the reports from the read-only em-dash, duplication, and byte-budget checks.

Gate delta: no new blocking gates, refusal classes, locks, lanes, state fields, or validators; the change reuses the existing weekly audit and rotation cursor, expands its review inputs, and adds read-only diagnostics to its existing report. The existing machinery inventory baseline is already red and this plan adds no machinery.

## Assumptions

- The 2026-10-04 origin is eligible under the personal profile because its two witnessed certification recerts are recovered time cost; its non-enum `Origin class:` value remains survey-time `unknown` and is not normalized.
- Reuse `weekly-skill-review` rather than create a new recurring task. It already has the seven-day cadence, a six-run cursor, and a report sink; a separate task would add another audit dispatch, cursor, and report flow for the same prose review.
- Keep the existing skill-directory units first and in their current lexicographic order, then append `docs/maintenance/` Markdown paths in path order, then open top-level backlog Markdown paths in basename order. The current numeric cursor therefore still names the same next skill unit; the revised batch is `ceil(total units / 6)` and covers the full combined corpus within six successful runs.
- Run the em-dash scan over the full live prose corpus each audit; run the duplication measure over `agents/skills/` and `docs/maintenance/` (the script excludes `docs/history/` and `synced/`); run the byte-budget report over the skill corpus. For each selected review batch, check source-of-truth placement against `doc-hierarchy` and the standing prose rules in section 39 of the configured agent workflow guidelines, including globish; record findings with path-and-line evidence. The semantic review remains bounded to the selected rotation batch.
- Keep the recurring audit read-only over source files. It reports evidence with path and line, uses the existing backlog capture and quarantine-batch rules, and does not auto-fix, move, or reclassify documents. The initial cleanup is this plan's bounded exception over the exact 21 measured hits.
- The budget gate's no-breach, non-increasing-total sunset window begins when the expanded weekly audit first consumes and records its report.
- Machinery stays non-blocking; the cadence is one diagnostic/report set per seven-day weekly audit. Findings can be false positives only as review suggestions, with no lane refusal or source mutation; review the consumer and registry claims on 2027-01-27.

Decision points requiring a grill: none remain. Maintenance-selected authorization chooses the existing weekly review lane and cursor because this covers the origin without a second audit task or new state field.

## Standing constraints

- Preserve the current `weekly-skill-review` quarantine presentation, backlog dedupe, report append, commit, and state-advance rules; this plan adds only the live corpus inputs and compact hygiene summary.
- Use `agents/skills/doc-hierarchy/content-ownership.md` and the repository's `AGENTS.md` skill text anti-growth rules by reference. Do not restate their prose or introduce a broad new rule catalog.
- Treat scanner and report output as evidence. Do not edit source during the recurring audit or auto-classify a document's lifecycle state.

## Evaluation Criteria

**Quality dimensions:**

- Coverage: every review unit appears once per six successful runs, with cursor continuation preserving the same next skill unit for an existing cursor value.
- Correctness: each weekly log entry distinguishes current em-dash hits, duplication findings, byte-budget breaches, and semantic findings by path and line where available.
- Safety: the recurring audit never edits source files, never changes a quarantine disposition, and never blocks a lane.
- Simplicity: the existing audit task, cursor, output log, and registry slot are reused; no task, state field, script, gate, or lock is added.

**Done when:**

- The scoped first-pass em-dash scan is clean after the measured 21 hits are repaired.
- The weekly task's combined corpus ordering, batch size, read-only diagnostics, report record, and existing state advance are explicit and pass repository readiness checks.
- The machinery registry names the real weekly consumer and its measured sunset; the inventory check gains no new finding from this change.

**Ship when:**

- The next completed `weekly-skill-review` run records the combined corpus size, selected batch, three diagnostic summaries, and path-and-line evidence for semantic findings in `docs/maintenance/skill-review-log.md`.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

**Tests:**

**Docs:**
- `agents/skills/agterm/SKILL.md` (Task 1)
- `agents/skills/agterm/cookbook.md` (Task 1)
- `agents/skills/agterm/examples.md` (Task 1)
- `agents/skills/agterm/reference.md` (Task 1)
- `agents/skills/agterm/troubleshooting.md` (Task 1)
- `agents/skills/doc-hierarchy/content-ownership.md` (Task 1)
- `agents/skills/doc-hierarchy/instruction-templates.md` (Task 1)
- `agents/skills/execute-plan/agent-logs.md` (Task 1)
- `agents/skills/execute-plan/runtime-contract.md` (Task 1)
- `agents/skills/how-to-write-skills/references/skill-structure.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (Task 1)
- `agents/skills/review-agents/SKILL.md` (Task 1)
- `agents/skills/tdd-guide/SKILL.md` (Task 1)
- `agents/skills/tdd-guide/java-kotlin.md` (Task 1)
- `docs/history/backlog/2026-10-09-scheduler-turn-boundary-stops-live-lanes.md` (Task 1)
- `docs/history/backlog/2026-10-10-completed-archive-prose-form-anchors-rider.md` (Task 1)
- `docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md` (Task 1)
- `docs/history/backlog/2026-10-13-quarantine-intake-dead-lettered.md` (Task 1)
- `docs/maintenance/development_lessons.md` (Task 1)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (Task 1)
- `docs/maintenance/operator-directives.md` (Task 1)
- `docs/maintenance/recurring-tasks/weekly-skill-review.md` (Task 2)
- `scripts/machinery_registry.json` (Task 2)

**Read-only:**
- `docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md` (review-only)
- `agents/skills/doc-hierarchy/SKILL.md` (review-only)
- `agents/skills/doc-hierarchy-upkeep/SKILL.md` (review-only)
- `scripts/check-no-em-dash.sh` (review-only)
- `scripts/skill_text_duplication.py` (review-only)
- `scripts/skill_text_budget.py` (review-only)
- `docs/maintenance/recurring-tasks/weekly-measurement-rider.md` (review-only)
- `scripts/machinery_inventory.py` (review-only)

**Plan-related extension:** findings on these paths are in scope when they correct a defect introduced by the two tasks or complete the stated report and registry wiring.

**Out of scope; reject unless plan-related:**
- Archived plans and backlog, vendored `agents/skills/synced/`, rolling prompt logs, scheduler state schema, additional recurring-task entries, and new scan scripts; the origin does not require changing these surfaces.

## Validation Commands

- Run the full plan readiness gate on the final reviewed bytes and the pre-round readiness gate before each review round.
- At implementation, rerun the scoped em-dash scan over the exact live corpus and require zero hits after Task 1; record the duplicate-report and byte-budget outputs from Task 2.
- Run the repository public-hygiene scan and all repo-mandated checks for any edited skill surface. For `agents/skills/review-agents/SKILL.md`, run the required portability and review-agent doors checks.
- Run `scripts/machinery_inventory.py --check` before and after Task 2; compare findings and require no new finding caused by this plan. The known baseline is red and is not represented as a passing exit.

### Task 1: Clean the measured live em-dash residue

Context surface: the plan's Terms, this task, and `## Standing constraints`; the origin's Witness updates and the live scan define the evidence, and `agent_workflow_guidelines.md` section 39.1 defines the comma substitution.

Files:
- `agents/skills/agterm/SKILL.md`
- `agents/skills/agterm/cookbook.md`
- `agents/skills/agterm/examples.md`
- `agents/skills/agterm/reference.md`
- `agents/skills/agterm/troubleshooting.md`
- `agents/skills/doc-hierarchy/content-ownership.md`
- `agents/skills/doc-hierarchy/instruction-templates.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/how-to-write-skills/references/skill-structure.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/review-agents/SKILL.md`
- `agents/skills/tdd-guide/SKILL.md`
- `agents/skills/tdd-guide/java-kotlin.md`
- `docs/history/backlog/2026-10-09-scheduler-turn-boundary-stops-live-lanes.md`
- `docs/history/backlog/2026-10-10-completed-archive-prose-form-anchors-rider.md`
- `docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md`
- `docs/history/backlog/2026-10-13-quarantine-intake-dead-lettered.md`
- `docs/maintenance/development_lessons.md`
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md`
- `docs/maintenance/operator-directives.md`

- [x] Replace only each of the 21 em-dash hits measured at authoring with the section 39.1 comma form where it is prose punctuation; keep each sentence's meaning and any literal code/data meaning intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the complete live-corpus scan has zero em-dash hits after the edits, with archived and synced paths still excluded; confirm no unmeasured residue was silently added to scope. [class: REPOSITORY_TEST]
- [x] Run repository hygiene and the required review-agent checks for the changed `review-agents` skill; record results before landing. [class: REPOSITORY_TEST]
- [x] Commit the bounded punctuation cleanup with a why-first message. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Make the existing weekly review consume the live hygiene corpus

Context surface: the plan's Terms, this task, and `## Standing constraints`; the current weekly task owns its cursor, output, and state advance, while the machinery registry owns admission and sunset claims.

Files:
- `docs/maintenance/recurring-tasks/weekly-skill-review.md`
- `scripts/machinery_registry.json`

- [x] Extend the ordered review units by retaining the current lexicographic skill-directory list first, then adding live maintenance Markdown files in path order, then open top-level backlog Markdown files in basename order; exclude prompt logs, archived backlog rows, and vendored synchronized copies. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the current `rotation_cursor` meaning for existing skill positions, set each successful batch to `ceil(total_units / 6)` units, wrap deterministically, and advance only on the existing end-to-end completion condition. Given an old cursor that points into the skill list, expect the same next skill unit; across six successful runs, expect every combined review unit to have appeared. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a full-corpus em-dash scan, the existing duplication report over skills and live maintenance docs, and the warning-only byte-budget report to each audit run; each is read-only and none changes the audit outcome or lane dispatch. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the existing aggregate-record contract with the combined corpus size and selected batch, diagnostic summaries, and path-and-line evidence for surfaced findings. Keep the existing quarantine presentation, backlog dedupe, commit, failure advance, and state write rules intact; the audit never edits source files or finalizes quarantine dispositions. [class: IMPLEMENTATION_REQUIRED]
- [x] For each selected semantic batch, review source-of-truth placement against `doc-hierarchy` and the standing prose rules in section 39 of the configured agent workflow guidelines, including globish; record findings with path-and-line evidence in the existing aggregate record. Keep this review read-only and advisory. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the duplication and byte-budget machinery registry notes to name weekly-skill-review as the actual consumer, cite the evidenced hygiene incidents and weekly catch frequency, keep false-positive cost non-blocking, and align each sunset with six weekly-skill-review windows after the expanded audit first records that report (zero consumers for duplication; no breaches and non-increasing totals for byte budget). Add no machinery registry row. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the consumer and registry correction with a why-first message. [class: IMPLEMENTATION_REQUIRED]
- [x] After the commit, run the machinery registry inventory and compare it with the baseline; if the committed edits introduce a finding, repair it, commit the repair, and rerun the check. Verify the weekly procedure names no new task, state field, gate, lock, or script. [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- Origin row docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md: covered by this plan (executed and landed 2026-10-27, execute-plan run maintenance-doc-hygiene-review; both tasks implemented, r1 focused panel address + r2 clean verification, record pair 2026-10-27-plan-review-maintenance-doc-hygiene-review-p47541118-r3). Ship when remains the post-landing external condition: the next completed weekly-skill-review run records the combined corpus size, selected batch, three diagnostic summaries, and path-and-line findings in docs/maintenance/skill-review-log.md.
- Residual em-dash hits and the literal-data exception: captured at docs/history/backlog/2026-10-27-emdash-residuals-open-rows-and-literal.md (open).
- Diagnostics-script docstring wording lag: captured at docs/history/backlog/2026-10-27-diagnostics-script-docstring-wording-lag.md (open).
