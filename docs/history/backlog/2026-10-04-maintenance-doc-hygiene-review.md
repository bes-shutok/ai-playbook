# Backlog: standing maintenance documentation-hygiene review (em-dashes, repetition, SOT violations, standing prose rules)

- **Filed:** 2026-10-04, operator-directed (split out of the review-cert-graded-binding interview: the em-dash guarantee question asked for a guarantee the text is em-dash free; the operator directed the live-residue cleanup and ongoing prose hygiene into a maintenance task, as a separate backlog item)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (the residue is real and recurring: em-dash cleanup has cost the operator's loops repeatedly, twice as witnessed certification recerts)
- **Origin class:** operator-directed design change (witnessed residue)
- **Class:** standing-hygiene review arm
- **Driving force:** automation (removes recurring manual direction: prose-hygiene defects surface today only through operator flares and pre-commit scans that detect but never clean)

Cluster: docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md (same defect class, prose growth without a counter-signal; this row's standing review arm is the consumer home for that row's growth telemetry and duplication report)

## Problem

The repo's prose-hygiene enforcement is detect-only and rule-scoped. `scripts/check-no-em-dash.sh` scans but never fixes, and it runs only at pre-commit, done-sweep, and CI boundaries (policy `agent_workflow_guidelines.md` §39.4); nothing scans for repetition, source-of-truth (SOT) placement violations, or drift from the other standing prose rules (globish §39.2, doc-hierarchy placement). The residue on live surfaces as of 2026-10-04: 22 live skill files under `agents/skills/` carry em-dashes, 3 open backlog rows carry them, and plans certified after the 2026-09-06 authoring-scan mandate still landed with violations (the two witnessed em-dash recerts, 2026-09-04 and 2026-09-05, are the certification-side cost of the same gap). Archives (`completed/`, `deferred/`, `rejected/`) and vendored syncs (`agents/skills/synced/`) are out of scope by design: archives are immutable history, synced files follow upstream.

## Expected

A standing maintenance arm (scheduler-turn monitor or per-cycle duty) reviews live documentation prose on a cadence: live skill files, open backlog rows, and live docs under `docs/maintenance/`, never archives or `synced/` vendored files. Checks: em-dashes (clean and record, or auto-fix per the certification entry's substitution rule once it lands), repetition (duplicated guidance across files, the merge-don't-duplicate rule), SOT violations (content contradicting doc-hierarchy placement rules or duplicating a canonical home), and the repo's other standing prose rules as they accumulate. Findings fix forward with a record, or file as their own rows when the fix is a mechanism change. The repetition check's measure is scripts/skill_text_duplication.py (the Part 2 method: per-file repeated-span percentage, top duplicated sentences, cross-file intersections), consumed by this standing arm on its cadence with its exclusions (archives, `synced/`) unchanged; the script never gates. The byte-budget gate's growth-telemetry leg joins this consumer line at whichever sibling landing is second (owner: this standing arm, triggered by the budget gate's landing; scripts/skill_text_budget.py not tracked at the repetition measure's landing, so this line is scoped to the repetition measure and records the join as pending), neither landing deleting the other's measure. The first pass cleans the witnessed live residue (the 22 skill files and 3 backlog rows).

## Ship when

- A routine maintenance turn surfaces em-dash, repetition, and SOT findings by path without operator prompting; the witnessed live residue is cleaned in the first pass; the arm's contract names its excluded surfaces (archives, `synced/`) and its cadence.

## Witness updates

- 2026-10-25 (worktree-closeout exec run, Task 2 boundary): `docs/maintenance/development_lessons.md`, a live `docs/maintenance/` surface inside this arm's scan scope, carries 9 committed em-dash lines as of the witness date (corpus lines 2363, 2365, 3312, 3328, 3335, 3350, 3485, 3487, 3519; lesson #107's witness prose onward). The residue surfaced as a parked `check-no-em-dash.sh touched` hit only because the corpus file was dirty with a parallel learn pass's appends; on a committed clean tree the touched leg scans zero files (the vacuous-leg shape tracked in `2026-10-17-rearm-ladder-guards-certification-residuals.md`, which owns the scanner leg while this row owns the residue), so committed corpus prose reaches the operator only through this arm's per-cycle sweep or an explicit-file-set invocation. Priority re-affirmed: medium.
