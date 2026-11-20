# Backlog: two conservative-forever retention edges in the branch-only receipt consumption

Cluster: docs/history/backlog/2026-11-08-branch-only-closeout-receipt-plan-certification-residuals.md; docs/history/backlog/2026-11-08-branch-only-receipt-lock-free-write-window.md; docs/history/backlog/2026-11-08-branch-only-receipt-version-skew-keyguard.md (same branch-only closeout receipt contract; distinct producer, compatibility, and retention findings remain separately scoped)

- **Filed:** 2026-11-08, execution review r1 (correctness solo; design solo) of docs/history/plans/completed/branch-only-closeout-gate-report-retention-completed
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review findings (Low, non-blocking, deferred)
- **Class:** fix-class
- **Driving force:** correctness
- **Body:** (1) mixed-history manifests: the receipt marker and terminal consult key on the single recorded (latest) branch, so a manifest stamped by an earlier branch-only record whose later record completed worktree-mode — or an unbound attempt stamped against a different branch's lifecycle — retains its aged destinations forever (keep-direction, never data loss; the exact shape the plan rejected for the uniform-keep arm). Candidate remedy: per-record discriminator, plan-level design. (2) malformed-entry silence: the writer preserves unrecognized entry shapes and reports success while the reader fail-closes the whole section on any malformed entry, so one corrupted entry retains the report indefinitely with no operator-visible line; the read-error/shape-error arms warn, this state does not. Candidate remedy: a sweep warning when a marker manifest's terminal condition fails.
