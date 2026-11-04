# Gate-removal prevented-clobbers attribution pin and reset residuals

Status: covered (docs/history/plans/2026-11-04-closeout-clobber-guard-review-residual-trio.md)
Driving force: code-quality

Origin: intermediate review of Task 4, execution of docs/history/plans/2026-11-02-closeout-migrate-clobber-guard-restore-arms.md (2026-11-04, verdict backlogged-candidates, nothing blocking).

Cluster: docs/history/backlog/2026-11-04-clobber-guard-phase3-review-residuals.md, docs/history/backlog/2026-11-04-clobber-guard-report-line-wording-residuals.md

Two low candidates on the new prevented-clobbers teardown reporting in scripts/worktree_closeout_migrate.py:

- F1: the stamp-less fallback arm of the prevented attribution (`attributed = len(records) == 1`, beside the identical missing-destination hold predicate) is unpinned in both directions — a mutation flipping stamp-less rows to always-foreign or always-attributed survives both landed pins because the landed rows are stamped. Remedy: one pin for a single-record unstamped prevented row (summary) and one for a two-record unstamped row (foreign note), or fold the duplicated predicate into one shared helper protecting both loops.
- F2: the resolver TypeError handler resets verified_destinations/verified_rows but not the new prevented_rows key, so a partial prevented collection survives in the state dict; unreachable today only because the gate unconditionally re-raises destinations_error before the prevented loop. Remedy: a symmetric one-line reset, or a comment naming the raise-ordering invariant so it is structural rather than ordering-dependent.

## Ship when

- The next review round over scripts/worktree_closeout_migrate.py's gate-removal machinery picks up both remedies (natural home: any follow-up touching the prevented-clobbers surface).
