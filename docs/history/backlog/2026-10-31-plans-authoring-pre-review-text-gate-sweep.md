# Backlog: Plans authoring lacks the pre-review repository text-policy gate sweep

- **Filed:** 2026-10-31, learn Step 1.8 (interactive authoring session)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (costs one wasted certification round per incident; fail-visible, never silent)
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** efficiency
- **Skill/step:** `agents/skills/plans/SKILL.md` authoring phases (and the maintenance authoring payload in `agents/skills/maintenance/template-authoring.md`), between the last plan-file write and the first `review-plan` round launch
- **Dedup probe:** searched `docs/history/backlog/` top level for `pre-review`, `text-policy`, `em-dash gate`, `authoring gate sweep`: nearest hit is lesson #36 in `docs/maintenance/development_lessons.md` (the rule exists as a lesson; no open row owns the plans-skill authoring flow's missing gate step); no open row owns this family
- **Source:** session output of the 2026-10-31 authoring closeout (four review rounds, then `scripts/check-no-em-dash.sh added-lines` refused 3 plan lines at the landing gates)

## Problem

The plans skill's authoring flow validates plan text through review rounds (lens catalogs) and the readiness gate, but no step runs the repository's mechanical text-policy gates over the authored bytes before the first review round: the em-dash added-lines gate (`scripts/check-no-em-dash.sh added-lines`), the public hygiene scan, and the pins suite where skill text is touched. The review lens catalogs own defect classes, not a repository's text policy, so every worker passed a plan that the one-second em-dash gate refused at closeout - after certification, forcing a fix commit plus a fresh certification round (lesson #36's third witness).

## Expected

The authoring flow runs the repository's mechanical text-policy gates over the plan bytes (and any authored sibling text) before launching the first review round, the way it already runs the readiness structural checks; a text-policy refusal is fixed pre-review, never discovered post-certification.

## Suggested direction

Add one authoring-phase step (plans skill authoring phases; mirror one line in the maintenance authoring payload's pre-review duties) that runs, from the placement root: `bash scripts/check-no-em-dash.sh added-lines` (working-tree insertions), the public hygiene scan, and the pins suite when the change touches pinned files; gate the first review launch on their exit codes. Keep it read-only otherwise; no new machinery beyond the existing scripts (the admission protocol prices no new gate - this composes existing ones at an earlier boundary).

## Why not fixed now

The harvesting session's mandate ended at the pick boundary by operator direction; the change touches the plans skill's authoring phases and deserves its own reviewed edit rather than an unreviewed ride on this session's learn commits.
