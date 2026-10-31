# Backlog: the worktree removal gate adjudicates prior-run manifest rows, so a drained gitignored artifact permanently refuses a later run's teardown

- **Cluster:** docs/history/backlog/completed/2026-10-30-execute-plan-teardown-staging-record-mirror.md (the gate-removal machinery this row extends), docs/history/plans/completed/2026-10-28-pending-receipt-removal-audit-promotion.md (the witness run), docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md (same gate-removal surface; that row owns branch-only completion, this row owns manifest-row scoping)
- **Cluster:** docs/history/backlog/2026-10-31-gate-removal-shared-slug-second-witness.md (second witnessed instance, 2026-10-31 exec run session-status-facts-parse-shape-gap; same mechanism, worktree-plus-branch pair held then released under operator direction)
- **Filed:** 2026-10-31, learn Step 1.9 over the pending-receipt-removal-audit-promotion completion-pass session (session zcode-exec-20261031-praudit)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** execution-run finding
- **Class:** fix-class

## Problem

`scripts/worktree_closeout_migrate.py migrate` **appends** to the shared session dir's `closeout-migration.json` (the canonical session slug strips the plan's date, so consecutive runs of the same plan extend one manifest), and `gate-removal` checks **every** verified destination in the manifest, not just the authoritative last branch record's own rows. A prior run's closeout installed gitignored `docs/tmp/done-session/` artifacts that a later sanctioned tmp sweep drained; the rows stay verified, their destinations no longer exist, and the gate refuses the later run's teardown with `migrated artifact(s) missing under the target` even though the later run's own migration is fully intact. Witnessed 2026-10-31: the completion-pass run's teardown was refused over one Oct-28 gate-report file removed by the sweep; the worktree and branch had to be preserved under the gate's fail disposition.

## Expected

The gate's missing-destination check scopes to the rows of the branch record it adjudicates (the manifest's last element, per the resolver's own authoritative-binding rule), or provides a sanctioned way for a later run to supersede drained-destination rows (for example a migrate operation that re-verifies and retires rows whose destinations were legitimately removed by the documented tmp-sweep lifecycle), so a prior run's drained scratch can never permanently block a later run's worktree removal. Any repair keeps the fail-closed posture for genuinely missing migrations.
