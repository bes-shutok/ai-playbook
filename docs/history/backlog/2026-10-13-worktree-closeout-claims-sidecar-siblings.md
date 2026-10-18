# Backlog: worktree closeout claims name record paths only, stranding stats sidecar siblings

- **Filed:** 2026-10-13, authoring-lane done closeout staging classification
- **Status:** covered
- **Coverage witness:** docs/history/plans/2026-10-16-worktree-closeout-claim-sibling-completeness.md (r3-certified landing; the gate derives and refuses on the destruction condition, and the machinery admission's pre-registered condition stands verbatim: a witnessed false refusal narrows the record grammar rather than removing the arm; removing the arm re-opens the witnessed loss and requires an operator decision recorded here)
- **Workflow:** done (Step 2 worktree migration and gated removal) / worktree_closeout_migrate.py
- **Priority:** high
- **Origin class:** observed execution friction; cleanup-claim completeness gap
- **Class:** fix-class
- **Skill/step:** `agents/skills/done/SKILL.md` Step 2 gated removal check (`worktree_closeout_migrate.py gate-removal` with the newline-delimited claims file of review-record paths); sibling contract in the authoring closeout recipes
- **Driving force:** reliability

Cluster: covered artifact-home consolidation witnessed by docs/history/plans/completed/2026-10-13-skill-audit-artifact-ignore-default.md (this row covers claim completeness at teardown).

## Problem

The gated removal check verifies exactly the paths the claims file names before allowing worktree removal. The contract never requires the claim set to include each claimed record's required siblings, so a claims file naming only the `.md` staging records passes the gate while the records' `.stats.json` sidecars stay behind and die with the removed worktree. Afterward the records fail staging validation as owned corpus entries (missing required stats sidecar), and the residue is permanent because the workspace is gone.

## Evidence

- Witnessed 2026-10-13: an authoring worktree closeout claimed two review records' markdown paths only; their sidecars were never migrated, the worktree was removed, and `validate_review_staging.py` now reports `missing required stats sidecar` for both records in the primary reviews home.
- The sidecars exist nowhere else: absent from the primary home and from the docs orphan branch (the sync never saw them).
- The gate behaved as written: it verified the claimed paths and allowed the removal; the gap is that the claim set is the whole preservation inventory and nothing requires it to be complete.
- Environment: repo-local `scripts/` copies at the 2026-10-13 tip, python3.14 runtime; the migration and removal ran through the repo-local closeout scripts.

## Expected

Either the gated removal contract requires (and the gate verifies) each claimed record's co-named sibling artifacts in the target home before removal allows, or the claims-composition recipe names the sibling-enumeration step explicitly. The two stranded records are re-sidecared through the sanctioned round-close tooling, or their residue is recorded here and they stay permanently foreign in closeout classification. Decide any rebuild arm against the no-fabrication rule: a sidecar is binding metadata re-derived from the record's own fields and verified by the staging validator, never reconstructed plausibly.

## Suspected root area

The claims file's shape is a bare path list with no completeness requirement, and the removal gate's verification scope equals the claim list rather than the record family it preserves.
