# Consolidate duplicated rolling-log recovery plan text
Cluster: docs/history/backlog/2026-11-10-rolling-log-recovery-plan-terms-first-use.md

- Filed: 2026-11-10, review-fix cycle R21 F5
- Status: open
- Priority: low
- Workflow: backlog
- Origin class: self-serving
- Driving force: simplicity
- Class: fix-class
- Source: `.ai-playbook/reviews/2026-11-10-plan-review-rolling-log-write-residue-recovery-recipe-p29d8406e-r21.md`, F5 (Low, nonblocking)
- Skill/step: review-plan R21; `docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md`
- Dedup probe: searched open backlog filenames and Problem bodies for `unbalanced operative-text growth`, `plan text growth`, and `operative recovery rules`. Nearest items are `docs/history/backlog/2026-10-27-execute-plan-skill-mirror-growth-unbalanced.md` and `docs/history/backlog/2026-10-31-stop-boundary-skill-text-growth-residual.md` (deleted covered by the 2026-11-16 trim landing; its EXEC-PROMPTS prune receipt the durable witness), which concern growth in specific skill files, plus `docs/history/backlog/2026-11-07-operative-files-exceed-read-tool-single-read-cap.md`, which concerns tool read limits; none covers duplication in this plan's operative sections.
- Capture hygiene: `bash scripts/scan-public-hygiene.sh --files docs/history/backlog/2026-11-10-rolling-log-recovery-plan-text-consolidation.md` returned `OUTCOME: pass`.

## Problem

The plan is 54,087 bytes against 27,596 bytes for the same path on `main` before this review fold, a 26,491-byte increase. It repeats the same normative recovery rules across Terms, Gist & Examples, Outcome, Standing constraints, Evaluation Criteria, task bodies, and validation pins. The repeated instructions increase maintenance cost and create several places where authorization or recovery ordering can drift.

## Exact location

`docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md`: Terms; Gist & Examples; Outcome; Standing constraints; Evaluation Criteria; Tasks 1–5; Validation Commands.

## Suggested fix

Keep the transaction state and per-path disposition rules in one canonical section. Shorten explanatory summaries to point to that section, while retaining acceptance criteria and exact command pins that prove distinct behavior. Pay for every new operative sentence with equivalent deletion in the same plan edit.

## Why not fixed now

This Low finding is outside the current plan execution boundary. The current pass is correcting and implementing the three R21 recovery and validation blockers while preserving Task 1's accepted handoff scope. A broad text consolidation would change many plan surfaces and needs its own focused review; the repeated text does not prevent the plan's recovery procedure from being executed after the R21 blockers are corrected.

## Acceptance

- The plan has one canonical home for each operative recovery invariant, and summary sections point to it instead of restating it.
- Exact task acceptance criteria and validation pins still cover distinct behavior and remain reachable from the prescribed task text.
- The plan's operative text has no unbalanced growth, demonstrated by the before/after byte delta and a fresh review with no `simplification#shrink` finding for this duplication.
- Public hygiene scan passes.
