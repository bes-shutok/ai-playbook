# Backlog: handle plan edits before a new plan has a Git baseline

- **Filed:** 2026-10-28, plan-authoring recovery
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** observed workflow tool error
- **Class:** fix-class
- **Driving force:** simplicity; secondary: correctness
- **Skill/step:** `agents/skills/plans/SKILL.md`, review-loop fold classification; `scripts/plan_delta_classifier.py`
- **Cluster:** docs/history/backlog/2026-10-18-plan-fold-unclassified-authorization-record.md; docs/history/backlog/2026-10-18-plan-delta-classifier-scope-fold.md
- **Dedup probe:** searched the two open classifier-related backlog rows and both rolling prompt logs for `plan_delta_classifier`, `plan-delta classifier`, and `plan delta classifier`; they cover unclassified tracked-plan hunks and authorization evidence, while this witness is the distinct new-plan path absent at the baseline commit.

## Problem

The plan-delta classifier refuses with a tool error when a newly authored plan path is not present in the selected `--since` commit. A fold in the new plan therefore cannot be classified against that commit, even though semantic edits still receive a fresh review. This leaves the authoring workflow without the prescribed classifier result and turns a missing baseline blob into an opaque tool error.

## Expected

Handle a newly authored plan that has no blob at the loop's start commit with an explicit, evidence-backed classification path. Keep semantic plan changes on the fresh-review route, and preserve the current review gate without adding a new blocker or unnecessary checkpoint ceremony.

## Suggested direction

Investigate the smallest safe way to classify changes after a plan's first draft: determine whether the initial draft can supply an exact baseline through existing artifacts or whether the classifier should represent the absent-before path explicitly. Compare that with continuing to require a fresh full review after every authored-plan edit. Do not weaken semantic review or invent a script-verified correction row for an absent baseline.

## Evidence

- As witnessed during plan authoring, `scripts/plan_delta_classifier.py` returned `OUTCOME: tool_error` with `the plan path docs/history/plans/2026-10-28-runtime-scripts-home-reconcile-and-retire.md is not tracked at the --since commit 8476e10347173f0fef888bdb1bc354b7d59bf9fe`.
- At the re-derived `HEAD`, the plan path was untracked (`git status --short` reported `??`) and absent from the commit tree (`git ls-tree HEAD -- <path>` printed no entry); the classifier source exists in both the working tree and `HEAD`.
- The authoring run recovered by issuing a fresh full-panel review after each semantic plan edit. The final reviewed digest passed `scripts/plan_readiness.py`; this workaround preserves review coverage but does not provide a classifier result for the pre-commit folds.

## Why not fixed now

The active plan concerns runtime-script inventory and deployment. Changing shared plan-classification behavior would widen its scope and needs its own investigation and reviewed plan. The current safe recovery is to retain the fresh review rounds and avoid editing or bypassing the classifier.
