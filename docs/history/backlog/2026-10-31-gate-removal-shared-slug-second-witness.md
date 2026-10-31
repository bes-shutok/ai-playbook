# Backlog: second witness for gate-removal inherited manifest rows (exec run session-status-facts-parse-shape-gap)

- **Cluster:** docs/history/backlog/2026-10-31-gate-removal-inherited-manifest-rows.md (same mechanism, same gate; that row is the primary origin, this row is the second witnessed instance), docs/history/backlog/2026-10-30-gate-report-retention-sweep-polish-family.md (the drain side: the tmp sweep legitimately expires the cited gate reports)
- **Filed:** 2026-10-31, operator-directed investigate over the exec carrier session zcode-exec-20261031-statusfacts
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** execution-run finding
- **Class:** witness-class (no new mechanism proposed; joins the primary origin's plan-worthy entry)

## Witnessed sequence (2026-10-31 ~21:30-22:15, exec run 20261031T213047Z-2f934840eb77)

- The run's `migrate` leg extended the shared-slug `docs/tmp/execute-plan/session-status-facts-parse-shape-gap/closeout-migration.json` (the session dir pre-existed from the same plan's authoring closeout), merging the authoring run's rows, including destinations of foreign run 20261030T142451Z-15b9df919715 under `docs/tmp/done-session/gate-reports/` and `learn-receipts`.
- `gate-removal` refused teardown accounting: "migrated artifact(s) missing under the target: .../run-20261030T142451Z-15b9df919715-review-staging-full.txt". The destination had been expired from the primary checkout by the sanctioned docs/tmp sweep; the source worktree of the citing run no longer existed. Retry after a wait reproduced the refusal (not a transient).
- Resolution applied under explicit operator direction ("find a way to complete while persisting the change"): the three stale rows (all citing the one drained gate-report path) were pruned from the migration manifest with a recorded `stale_entry_disposition` note in that gitignored record, the durable disposition being this row; the gate then passed (branch exact-tree-accounted), the sanctioned `git worktree remove --force` ran, and the branch ref was deleted at its proven OID `0cda7cc453e642161e1cbf38f2f06e6f882069b7`.
- The landed branch had already squashed into main as `bc227e63e` before the teardown; no content was lost. The stale manifest row named no bytes of the adjudicated run.

## Disposition

Investigation finds the existing PLAN-PROMPTS entry `gate-removal-inherited-manifest-rows` already covering this defect class with a recommended keep-and-narrow arm (scope the missing-destination check to the adjudicated record's own verified destinations). This row adds the second witness, confirms the trigger is common (any plan re-run over a shared slug), and records that the manual manifest-prune workaround is operator-directed, not a standing remedy. No duplicate log entry is emitted; the primary entry's verdict (plan-worthy) stands.
