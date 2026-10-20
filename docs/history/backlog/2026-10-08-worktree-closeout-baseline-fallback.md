# Backlog: recover worktree closeout when its artifact baseline is missing

- **Filed:** 2026-10-08, during a done closeout
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-10-08-done-closeout-placement-and-ceremony-overhead.md; docs/history/plans/completed/2026-10-08-done-closeout-ceremony-friction.md
- **Cluster:** docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md (same surface: the closeout baseline's digest matching in worktree_closeout_migrate.py)
- **Cluster:** docs/history/backlog/2026-10-19-reviews-home-migration-collision-twins.md (same tool, closeout-migration family)
- **Cluster:** docs/history/backlog/2026-10-21-closeout-baseline-dirs-omit-review-certs.md (same surface: the execute-plan Step 0.4 baseline capture set)
- **Cluster:** docs/history/backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md (same script: the collision arm renames the run's own boundary mirrors)
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

2026-10-18 recurrence datum (authoring closeout, plan review-runtime-sibling-module-deployment): `migrate` ran against a valid baseline but surfaced only the docs/tmp delta (one file), while the run's ten staging records and seal under the worktree's reviews and certs homes required the documented manual scoped-copy fallback with re-read checksum verification. The worktree's migrate manifest was lost with the sanctioned teardown, so the under-copy mechanism (baseline coverage versus worktree-cwd resolution) is not established from a manifest; the manual recovery again landed the records correctly.

2026-10-18 third witness (plan-authoring closeout): `done_run.sh commit` captured a fresh worktree-migration baseline immediately before `migrate`, after 24 session review artifacts already existed. Its manifest therefore recorded no review-home transfers, and `gate-removal` refused on the missing cited series. Re-running against the session's Phase-0 `closeout-baseline.json` transferred 31 new or changed files and verified all 24 review artifacts byte-for-byte; a post-finalize transfer also preserved the newly appended telemetry. The cause is now established for this witness: the late baseline excludes artifacts created earlier in the run.

## Why not fixed now

The 2026-10-18 witnesses now establish two under-copy paths: a migration can use a valid baseline that predates only some artifact writes, or `done_run.sh` can take its baseline too late to include any earlier review artifacts. The session recovered by migrating against its Phase-0 baseline and verifying the primary copies. Keep the baseline refusal when neither a valid baseline nor a valid skip record exists; investigate how the done and plan closeout steps should share one run-start baseline before choosing the smallest fix. No new blocking machinery is proposed.

## Source

- Observed 2026-10-08 while closing `review-policy-scope-complexity-cap-checkpoints`.
- Observed 2026-10-18 while closing the `review-runtime-sibling-module-deployment` authoring worktree; second instance of the closeout-migration coverage family.
