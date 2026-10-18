# Backlog: recover worktree closeout when its artifact baseline is missing

- **Filed:** 2026-10-08, during a done closeout
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-10-08-done-closeout-placement-and-ceremony-overhead.md; docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md
- **Cluster:** docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md (same surface: the closeout baseline's digest matching in worktree_closeout_migrate.py)
- **Cluster:** docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md (same surface: worktree run-artifact homes and the closeout migration; that row's parked run holds its gitignored state only inside its worktree)
- **Origin class:** observed recovery gap
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, worktree closeout; `scripts/worktree_closeout_migrate.py`
- **Driving force:** reliability

## Problem

A plan execution worktree reached done closeout without `closeout-baseline.json`. Its session record contained `closeout-baseline-skip.json` with the reason that Phase 0 capture was absent and the stated fallback `scoped-copy enumeration at closeout`. The migration helper correctly refuses to proceed without a baseline, while the execute-plan skill documents a scoped manual copy with digest verification. Closeout proceeded by reconciling owned records from the manifests; no data loss is known. The recurrence and hands-on recovery time are not measured, so the open question is whether this manual recovery creates enough recurring cost to justify a helper or clearer capture path.

## Expected

First establish observed recurrence and recovery effort from existing run records and history, distinguishing hands-on work from waiting and reporting only evidence that exists. Then decide whether the smallest useful response is to keep and clarify the documented manual scoped-copy fallback, improve baseline capture, or add an executable helper. Preserve the existing ownership, collision, digest, and manifest checks. Do not infer an empty baseline or copy a broad artifact root. The current fail-closed behavior remains appropriate when neither a baseline nor a valid skip record exists.

## Evidence

During the 2026-10-08 closeout, `python3 scripts/worktree_closeout_migrate.py migrate --baseline .../closeout-baseline.json ...` refused with “baseline file not found” and warned against an implicit empty baseline. The worktree had a `closeout-baseline-skip.json` recording the sanctioned scoped-copy fallback, but no baseline JSON. The main checkout needed this plan's owned review records and session logs before docs-branch sync.

## Why not fixed now

The current closeout continued by reconciling the owned review paths from the done manifest and execute-plan run manifest against the primary checkout, then verifying their bytes and citations. The skill already documents a manual scoped-copy fallback. No recurring cost or elapsed hands-on recovery time has been established, so a generic baseline-less migration mode is not yet justified. Keep the baseline refusal when no valid skip record exists.

## Source

- Observed 2026-10-08 while closing `review-policy-scope-complexity-cap-checkpoints`.
