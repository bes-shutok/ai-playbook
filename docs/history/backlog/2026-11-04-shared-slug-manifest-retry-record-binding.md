# Backlog: shared-slug manifest binds only the last branch record, so an earlier strand's branch-only retry is refused

- **Filed:** 2026-11-04, plan-review r2 certification residual (agent-resource-cleanup-disposition, overflow row 3)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** plan-review residual
- **Class:** fix-class
- **Dedup probe:** searched open backlog filenames and bodies for branch-only retry, record binding, and shared manifest. `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md` covers the branch-only completion signal, not record selection among multiple branch records. `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` owns the cross-turn disposition gap and witnessed the authoring strand's lost manifest; it does not cover the last-record binding. `docs/history/backlog/2026-11-01-gate-removal-multi-record-gate-report-conjunction-test.md` covers multi-record gate-report conjunction in the hold scoping, not identity binding. None covers the retry binding gap.
- **Cluster:** `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` (owns the cross-turn disposition and retry surface); `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` (second-strand witness)

## Problem

Plan 2026-11-04-agent-resource-cleanup-disposition folds the authoring strand's branch identity row into the primary slug home's existing migration manifest (no second evidence surface). The gate resolves the manifest's branch list by taking the LAST record as the authoritative binding (scripts/worktree_closeout_migrate.py `_resolve_closeout_reference_state`, and the exact-branch identity checks bind the recorded branch of that last record only). Once the authoring strand's row is appended, a branch-only retry naming an earlier strand's branch hits the exact-branch identity-mismatch refusal, and no record selector exists (the explicit --migration-manifest operand names a path, not a record), so that branch's automated retry can never pass; it stays retained for operator resolution. Retention keeps behavior safe, but the evidence the fold preserved cannot be used for the earlier strand, and the plan's own edge-case sentence promises the retry "reads the primary-slug manifest identity" for the strand - which holds only for the most recently transferred strand.

## Expected

State how a branch-only retry selects among multiple branch records in the shared manifest: either the retry operand gains a record selector (for example the recorded source path or a record index), or the adjudication matches the --branch operand against every record and adjudicates the matching one, so each strand's preserved evidence stays usable after a later strand's transfer appends.

## Evidence

- `scripts/worktree_closeout_migrate.py`: the resolver takes `records[-1]` as the authoritative binding; worktree- and branch-only modes refuse on identity mismatch against that record; the run-attribution stamping machinery already contemplates multi-record manifests for hold scoping but not for identity binding.
- Origin witness: the quota-governor cleanup left the execution branch unresolved while the authoring strand's evidence was lost - the two-strand shape where this binding matters.
