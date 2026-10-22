# Backlog: unattributed mid-run deletion of an untracked record from a worktree reviews home

- **Filed:** 2026-10-22 (learn capture over the 2026-10-21 scheduled execution run)
- **Status:** open
- **Priority:** medium
- **Workflow:** backlog
- **Origin class:** review-residual (learn Step 1.9 project issue)
- **Class:** investigate-then-fix (producer unattributed)
- **Driving force:** reliability
- **Skill/step:** the done-run commit stage's closeout legs (`scripts/done_run.sh`, `scripts/docs_branch_sync.sh`); `agents/skills/done/SKILL.md` Step 3; cross-referenced as lessons 166 and 167 in `docs/maintenance/development_lessons.md`
- **Environment:** playbook repo, execution worktree with a gitignored reviews home, 2026-10-21
- **Suspected root area:** an unknown mechanism deleted an untracked gate-required record mid-run; the two candidate passes the run record blamed are exonerated by code reading, so the producer is either a third leg or the record was never written where recalled
Cluster: docs/history/backlog/2026-10-09-docs-branch-witness-contract-and-recovery-test.md, docs/history/backlog/2026-10-09-docs-branch-step2-selector-test.md, docs/history/backlog/2026-10-11-docs-branch-python-runtime-floor.md (same surface: the docs-branch sync and its runner)

## Observed vs expected

Observed: during a done-run commit stage inside an execution worktree, an untracked landing-gate-required exec backfill record present in the worktree reviews home was later reported missing by the landing gate ("record missing"), forcing a same-run recreate from session state. The run's closeout record blamed the docs-branch sync's restore pass (`restored ... from refs/heads/docs`). Expected: either the producer is identified and scoped, or the record was never durably written where recalled; in both cases the closeout discipline should make the loss impossible to repeat silently.

## Evidence and archaeology (2026-10-22)

- `scripts/docs_branch_sync.sh` `restore_files` (line ~665) is create-only: it opens with `O_EXCL`, skips existing files, and prints the `restored ... from refs/heads/docs` line; no unlink/rmtree/remove exists on worktree paths in the script.
- `scripts/done_run.sh`'s deletion legs are bounded: the stale-checkout adjudication's `git checkout -- <path>` and the revert path's `git checkout HEAD -- <path>` (line ~1052) operate on tracked classified paths, and all `rm -rf` hits target the stage scratch directory.
- No `git clean` leg exists in either script.
- The record was recreated in the same run from session state, so no evidence was ultimately lost, but the recovery depended on the session still being alive.

## Scope to resolve

Identify the actual producer: enumerate every write between the record's last observed existence and the gate refusal (session-side tools, parallel sessions sharing the worktree, the docs-branch sync's `removed`/prune accounting, worktree operations), or establish the record was never written to the recalled path. Then decide the smallest hardening: a pre-stage mirror step in the done skill text (lesson 167's first arm), a loudness arm when a restore/prune pass observes a reviews-home change, or no change if the record was never written.

## Alternatives to assess

- Change the scripts to guard untracked reviews-home paths: premature while the producer is unattributed; a guard aimed at an exonerated pass protects nothing.
- Add the mirror-before-closeout step to the done skill text: cheap and producer-agnostic; the leading candidate regardless of the producer finding.
- Leave as-is with lesson 166 only: rejected as the default because the witnessed cost (a gate refusal mid-landing plus a from-memory recreate) recurs whenever untracked records exist at a closeout boundary, but the investigation must first rule out the never-written hypothesis before any script surface is touched.

## Disposition (2026-10-22 producer-enumeration ad-hoc run)

Outcome: unresolved - the producer is not attributed and the never-written hypothesis cannot be ruled out; the row stays open with the enumerated interval recorded below, and the mirror-before-closeout sentence landed in `agents/skills/done/SKILL.md` Step 3 as the producer-agnostic hardening arm.

Enumerated interval (last observed existence -> landing-gate missing-record refusal), every writer over the worktree reviews home in that window:

- `scripts/docs_branch_sync.sh` `restore_files`: exonerated by code reading - create-only (`O_EXCL`, skips existing), no unlink/rmtree/remove over worktree paths (row Evidence, re-derived 2026-10-22).
- `scripts/done_run.sh` commit-stage legs: exonerated - the checkout legs operate on tracked classified paths and the `rm -rf` targets are the stage scratch directory only; no `git clean` leg exists.
- `scripts/worktree_closeout_migrate.py` transfer (`_cmd_migrate_transfer`): exonerated - copy-only (`copy2` plus digest verify), never moves or deletes sources.
- Parallel sessions: the worktree reviews home is worktree-local and unshared, so primary-checkout peers cannot reach it; no second claim on the run's worktree is recorded.
- Worktree operations: exonerated structurally - the residue sweep's admin-dir rmtree releases stale registrations only (it refuses any candidate holding an on-disk worktree and deletes `.git/worktrees/<id>` metadata, never worktree files), and the gate-sanctioned `git worktree remove --force` runs at closeout after migration verification, past the interval that ends at the mid-landing gate refusal.
- Session-side file tools of the run session itself: not exonerable from disk - no transcript or per-write log of the original write survives (the run worktree was deleted after landing), so a session-side deletion and a never-durably-landed original write are indistinguishable in retrospect.

The surviving exec-r1 backfill record in the primary reviews home is the same-run recreation, so all disk evidence postdates the loss. Remaining follow-up (why the row stays open): a loudness arm when a closeout pass observes a gate-required record disappear between two of its own reads, which needs a machinery-admission case of its own.
