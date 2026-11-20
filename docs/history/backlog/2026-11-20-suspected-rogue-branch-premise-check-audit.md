# Backlog: suspected wrongly created branch - premise-check audit over every local and remote ref

- **Filed:** 2026-11-20, operator-reported suspected rogue branch during the origin-rewind follow-up
- **Status:** closed - investigate premise-check skip (no qualifying branch found, no entry emitted, removal refused on live-lane evidence); operator identified the reported ref as origin/main in its published state, reconciled by the same-day rewind (the origin-rewind row); nothing further is removable while main is the repository's default branch
- **Priority:** high
- **Origin class:** operator premise-check over the branch inventory
- **Class:** record / audit
- **Dedup probe:** no open row covers branch-inventory auditing; the nearest kin is the same-day origin-rewind attribution row (records only, different mechanism).

## Audit

The operator reported one "wrongly created" branch and ordered analyze, backlog, investigate, remove. Each ref audited with its owning record, re-derived on disk 2026-11-20:

- `main` - the primary checkout; ahead 668 of the rewound origin/main (`284f89a7`) by design after the same-day rewind.
- `2026-11-15-seal-leg-diagnostics-separation` - not rogue: execution lane for the authored plan `docs/history/plans/2026-11-15-plan-readiness-seal-leg-diagnostics-separation.md` (`Executed: no`); a paused run per the durable record, with Task 1 uncommitted in the worktree (`M scripts/corrections_record.py`, `M scripts/test_corrections_record.py`) and a resume carrier scheduled 17:38 WET 2026-11-20; the zero-unique-commits appearance is the uncommitted Task 1, and the record says do not redo or delete the worktree or claim.
- `2026-11-16-nondescript-refs-disposition` - completion-pass lane for the landed nondescript plan (completed twin `docs/history/plans/completed/2026-11-16-nondescript-orphan-lineage-backup-refs.md`; original landing `a134f40f679` 2026-11-17); one unlanded disposition commit `e554e6af6` (2026-11-20 13:50) plus an uncommitted lessons edit - active today.
- `2026-11-20-claude-maintenance-indefinite-loop` - live authoring: frozen PLAN-PROMPTS entry with a live authoring claim.
- `2026-11-20-plan-review-gate-hook-round-tie` - live authoring wip (`c081629f5`).
- `2026-11-20-self-heal-recovery-direction-and-evidence` - live execution: frozen entry with a live claim, wip commit `73eb515f1`.
- `2026-11-20-capture-hygiene-private-owning-repo` - live ad-hoc run (in-flight record; covered-row deletion commit `b484ef81d` on the branch).
- `authoring/2026-11-19-maintenance-dry-exit-conversion-fall-through` - pending-execution coverage record for the landed maintenance plan.
- `docs` - the standing docs-branch sync target.
- `refs/pull/1/head` (origin) - merged PR #1 (`codex/config-inventory-sot`, created 2026-10-10, state MERGED); its head branch is already deleted on the remote and the pull ref is GitHub-managed, so nothing is removable repository-side.

## Verdict

No branch qualifies as wrongly created: every local ref carries an owning record (authored plan, frozen entry, live claim, or standing role), and the two candidates that look like residue on a zero-diff glance are live lanes holding uncommitted work with explicit do-not-delete records. Removal is refused on that evidence; lifecycle tracking already lives in the plans root, the frozen entries, and the paused-run records. No machinery proposed (no witnessed incident of a branch causing harm - the premise itself failed the audit).

## Re-open condition

The audit re-opens only if the operator names a specific ref missing from the list above (for example one seen in another clone or a GUI); the named ref then takes the same owning-record check before any removal.
