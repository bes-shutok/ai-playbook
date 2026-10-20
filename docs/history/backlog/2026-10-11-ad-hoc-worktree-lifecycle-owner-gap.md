# Backlog: worktree creation and cleanup lack one lifecycle owner

- **Filed:** 2026-10-11, plan-origin execution and closeout
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed temporary-worktree cleanup delay
- **Class:** worktree lifecycle ownership gap
- **Driving force:** reliability + operator time
- **Cluster:** docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md (same defect class: terminal-state artifacts the closing boundary leaves behind; investigate 2026-10-20 roster)
- **Cluster:** docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md (same artifact class: a run's worktree and claim outliving their session; investigate 2026-10-20 roster)
- **Skill/step:** `agents/skills/plans/SKILL.md`, Final Step authoring closeout; `agents/skills/execute-plan/SKILL.md`, Step 0.1 and Phase 5; `agents/skills/done/SKILL.md`, worktree transfer-out and removal

## Problem

Two temporary worktrees remained registered until the operator asked for cleanup. One was the plan-execution worktree created by the documented Worktree-first setup. After the plan landed, it still held a newer ignored runtime-state timestamp, a dirty intermediate checker edit, and a temporary symlink. The other was a clean detached scratch checkout at a commit already ancestral to main; no tracked run record explains why it was created. Two recovery refs also remained after the corrected squash had landed. The content was recoverable, but cleanup and ownership reconciliation happened only after another operator direction.

## Evidence

- `agents/skills/execute-plan/SKILL.md` Step 0.1 creates an execution worktree unless the configured primary-placement route applies; Phase 5 names migration, verification, and deletion as the closeout sequence.
- `agents/skills/done/SKILL.md` requires transfer before removal and a gated removal check. The automatic residue sweep in `scripts/worktree_closeout_migrate.py` recognizes a narrower sibling-worktree shape, so it is not a catch-all for a worktree under an agent-managed worktree home or an arbitrary scratch path.
- `docs/tmp/execute-plan/plan-origins-coverage-parse/retired-worktree-cleanup.md` records the transferred runtime-state update, preserved intermediate patch, and the scratch checkout's already-landed base.
- The plan-execution artifact-loss incident is separately recorded in `docs/history/plans/completed/2026-10-11-execute-plan-boundary-reliability.md`; this item concerns delayed ownership reconciliation and cleanup, not reconstruction of the missing worker log.
- Re-witnessed 2026-10-19: after an authoring plan had landed and its worktree artifacts were migrated and verified, the closeout gate passed and authorized both removals. The operator requested worktree removal first, then separately requested branch deletion; the branch was removed only after the worktree registration was gone. This confirms the post-landing cleanup still needed operator follow-up, while the preservation gate itself worked as designed. Priority remains medium: the repeat cost is rediscovery and cleanup delay, with no lost implementation or evidence.
- Re-witnessed 2026-10-20 (pause-and-resume execution run): an operator-ordered mid-closeout pause kept the worktree, branch, and claim deliberately for a scheduled resume, with the owner and the full resume-and-cleanup procedure recorded in the run manifest; the resuming carrier completed transfer-out, worktree and branch removal, and claim release without operator direction. The operator still asked afterwards whether the worktree and branch had been deleted: a resumable pause window reads as this row's residue from outside unless the pause report names the retained resources, their cleanup owner, and the step that removes them. Priority remains medium; the positive half (cleanup completed unprompted once the run reached its closeout) narrows the gap to interrupted and abandoned runs plus the pause-report wording.

## Expected

Every temporary worktree and recovery branch has a named run or operation owner, a purpose, and one terminal cleanup owner. On success, that owner verifies transfer, removes the worktree and its unneeded branch, and reports any retained artifact. On interruption, the recorded owner or next closeout reports and resumes that cleanup without requiring the operator to rediscover the resources. A scratch worktree without a recoverable purpose is reported as unowned rather than silently treated as disposable.

## Suggested direction

Trace the provisioning and closeout paths for both worktrees and the recovery refs. Determine why the existing execute-plan transfer-out and done removal procedures did not complete automatically, and whether the current owner can be made a single, simpler closeout action. Compare the default worktree route with the authorized primary-checkout route. Do not add a generic Git hook or another cleanup ledger unless evidence shows the existing owner cannot reliably run its closeout; such a hook must not remove an active or unverified worktree.

## Alternatives

- **Remove Worktree-first execution:** rejected for now because the execution skill already allows a configured primary-checkout route, while this incident shows a cleanup failure rather than evidence that isolation itself caused the failure.
- **Add a global cleanup hook:** rejected for now because it cannot infer whether a registered worktree is active or owned, and an automatic removal has a high false-positive cost; the existing closeout gate already expresses the safe deletion boundary.
- **Keep the procedures unchanged:** rejected as the final resolution because they did not produce timely cleanup in this run. The investigation should first identify whether the miss came from orchestration, worktree ownership metadata, or the sweep's intentionally narrow candidate shape.

## Machinery assessment

No new gate or hook is admitted by this backlog. The expected catch frequency is not established beyond these two session observations, and the false-positive cost of deleting a live worktree is high. Reassess only after tracing the missed existing procedure; if a new blocking mechanism is proposed, apply the repository machinery-admission protocol with a concrete incident, catch-frequency estimate, false-positive cost, and sunset.

## Witness 2026-10-20 (learn capture, scheduled authoring run)

Two certified authoring plans closed out in one run: `gate-removal` refused `empty owned set` for both (the plans cite no `Plan review record:` header) until a `--claims` file named their records, then passed and left the worktree and branch registered; both removals ran by hand. Operating rule recorded as lesson 139 in `docs/maintenance/development_lessons.md`; this row still owns the terminal-ownership fix.
