# Backlog: done sweep-gates review-staging gate validates `.stats.json` sidecars as markdown staging docs

- **Filed:** 2026-09-30
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** skill-defect (company): the fault traces to the done sweep-gates lib's staging-candidate classification, not to consumer-project code.
- **Driving force:** reliability; secondary simplicity

## Problem

The done skill's Step 0 run-manifest writer requires every staging candidate on disk to be classified owned-or-foreign, and a done run that owns its own review sidecars must claim them (`--owned-review docs/reviews/<...>.stats.json`). The review-staging gate then feeds each owned candidate to `validate_review_staging.py` as a MARKDOWN staging document. For a `.stats.json` path this fails on three wrong-shape checks:

1. the sidecar JSON is parsed as staging markdown and flagged for missing `- Last fix commit:` and `- Record kind:` Metadata lines (they exist as JSON fields, not Metadata lines);
2. the validator demands a `.stats.stats.json` twin (`missing required stats sidecar: <...>.stats.stats.json`);
3. the paired markdown/sidecar agreement checks run against the JSON instead of the markdown twin.

Witness: a done run whose manifest claimed six `.stats.json` sidecars (all schema-valid via `validate_review_staging.py --hard <...>.md` over the markdown twins) failed the review-staging gate on exactly these three error classes per sidecar; re-running the identical write with the sidecars unclaimed (foreign-preserved, the de facto pattern every prior session's sidecars follow in this repo) passed the gate unchanged.

## Expected behavior

A claimed `.stats.json` candidate is validated as a SIDECAR: run the pair validation over its markdown twin (the existing `--hard <md>` path already covers sidecar schema, agreement, and digest), or exclude sidecar paths from the markdown staging validation while still requiring their markdown twin to be owned. The current behavior makes the documented Step 0 flow (claim your own staging docs) unsatisfiable for any run whose reviews produce sidecars, pushing every run toward the unclaimed-sidecar workaround.

## Suspected root area

`scripts/done_sweep_gates_lib.py`, review-staging gate scope derivation: the candidate filter imports `is_staging_review_path` (which accepts `.stats.json`) but the validation call does not branch on candidate kind; the markdown validator is the wrong tool for a sidecar-path candidate.

## Environment

Playbook repo, 2026-09-30, post 864c3216. Reproduced with the repo-local lib and the deployed `validate_review_staging.py`; the markdown twins validate OK standalone in both locations.
