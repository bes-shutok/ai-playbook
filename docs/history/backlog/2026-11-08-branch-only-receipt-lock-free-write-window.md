# Backlog: branch-only receipt write is a lock-free read-modify-write against the migrate lock discipline

Cluster: docs/history/backlog/2026-11-08-branch-only-closeout-receipt-plan-certification-residuals.md; docs/history/backlog/2026-11-08-branch-only-receipt-version-skew-keyguard.md; docs/history/backlog/2026-11-08-branch-only-retention-conservative-forever-edges.md (same branch-only closeout receipt contract; distinct producer, compatibility, and retention findings remain separately scoped)

- **Filed:** 2026-11-08, execution review r1 (correctness+risk echo) of docs/history/plans/completed/branch-only-closeout-gate-report-retention-completed
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (Low, non-blocking, deferred; revisit on witness per the machinery admission protocol)
- **Class:** fix-class
- **Driving force:** correctness
- **Body:** cmd_gate_removal's branch-only receipt/stamp write is a read-modify-whole-file os.replace outside the worktree-closeout-migrate merge lock, while migrate appends under the lock; an append landing inside the read-to-replace window loses one side's update. Bounded today (a lost receipt degrades to pre-change retention; never an unsafe prune — the terminal consult also requires the ref gone; a lost migrate append is the real exposure). Precedent: _append_authoring_strand_identity_row already writes the manifest unlocked in the same command. Taking the migrate lock in gate-removal would violate the plan's no-new-lock admission; candidate remedies: narrow lock acquisition around the write only, or an atomic-merge helper shared with migrate.
