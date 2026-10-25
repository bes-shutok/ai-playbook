# Backlog: worktree creation and cleanup lack one lifecycle owner

- **Filed:** 2026-10-11, plan-origin execution and closeout
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed temporary-worktree cleanup delay
- **Class:** worktree lifecycle ownership gap
- **Driving force:** reliability + operator time
- **Cluster:** docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md (same defect class: terminal-state artifacts the closing boundary leaves behind; investigate 2026-10-20 roster)
- **Cluster:** docs/history/plans/completed/2026-10-21-dead-run-resume-claim-conversion.md (same artifact class: a run's worktree and claim outliving their session; the origin row landed covered and was deleted at landing per the plan's disposition)
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
- Re-witnessed 2026-10-21 (short-lived Codex worktree): `create_worktree` completed and `archive_worktree` returned queued; the artifact listing then reported the checkout archived. A later filesystem check found no registered checkout at that path, only the empty named parent directory and its zero-byte `.codex-worktree-name` marker. The archive cleaned the checkout but left its parent container behind, a small residue outside the Git worktree and the existing closeout gate. The operator cleanup removed the marker and used non-recursive `rmdir` on the now-empty parent; no branch, checkout, or user data was removed.

## Expected

Every temporary worktree and recovery branch has a named run or operation owner, a purpose, and one terminal cleanup owner. On success, that owner verifies transfer, removes the worktree and its unneeded branch, and reports any retained artifact. On interruption, the recorded owner or next closeout reports and resumes that cleanup without requiring the operator to rediscover the resources. A scratch worktree without a recoverable purpose is reported as unowned rather than silently treated as disposable.

## Suggested direction

Trace the provisioning and closeout paths for both worktrees and the recovery refs. Determine why the existing execute-plan transfer-out and done removal procedures did not complete automatically, and whether the current owner can be made a single, simpler closeout action. For a completed archive, also let its existing owner attempt a non-recursive removal of the exact empty name-parent after verifying the checkout is gone; preserve and report the parent if it contains anything else. Compare the default worktree route with the authorized primary-checkout route. Do not add a generic Git hook, age/prefix sweep, or cleanup ledger; the new witness needs only exact-path empty-directory cleanup, and a broad remover could delete active or unverified work.

## Alternatives

- **Remove Worktree-first execution:** rejected for now because the execution skill already allows a configured primary-checkout route, while this incident shows a cleanup failure rather than evidence that isolation itself caused the failure.
- **Add a global cleanup hook:** rejected for now because it cannot infer whether a registered worktree is active or owned, and an automatic removal has a high false-positive cost; the existing closeout gate already expresses the safe deletion boundary.
- **Keep the procedures unchanged:** rejected as the final resolution because they did not produce timely cleanup in this run. The investigation should first identify whether the miss came from orchestration, worktree ownership metadata, or the sweep's intentionally narrow candidate shape.

## Machinery assessment

No new gate or hook is admitted by this backlog. The expected catch frequency is not established beyond these two session observations, and the false-positive cost of deleting a live worktree is high. Reassess only after tracing the missed existing procedure; if a new blocking mechanism is proposed, apply the repository machinery-admission protocol with a concrete incident, catch-frequency estimate, false-positive cost, and sunset.

## Witness 2026-10-20 (learn capture, scheduled authoring run)

Two certified authoring plans closed out in one run: `gate-removal` refused `empty owned set` for both (the plans cite no `Plan review record:` header) until a `--claims` file named their records, then passed and left the worktree and branch registered; both removals ran by hand. Operating rule recorded as lesson 139 in `docs/maintenance/development_lessons.md`; this row still owns the terminal-ownership fix.

## Witness 2026-10-23 (operator-directed investigation, pre-landing authoring husk)

The authoring worktree and same-named branch for the still-open reviewer-sized plan parts origin (`docs/history/backlog/2026-10-22-reviewer-sized-dependent-plan-parts.md`) were found registered a day after the session that froze its PLAN-PROMPTS entry ended, with no durable record naming the worktree as the reserved authoring surface or its cleanup owner; the operator had to ask whether the pair was removable. New angle inside this row's remaining interrupted-and-abandoned gap: because landings squash onto `main`, a pre-landing authoring branch never advances — the ref is a husk from birth, so `git merge-base --is-ancestor` emptiness proves nothing about whether the lane is done. Removed only after re-deriving that the tip was a `main` commit and the worktree was clean. No new machinery: this witness strengthens the existing ownership-record disposition (a frozen entry or pause report naming the reserved worktree, its owner, and the removal step). Durability of the authored artifacts themselves was the sibling row's record-durability arm (same session-death shape), covered by the plans skill's certification-time checkpoint duty in the authoring round-close (the sibling row deleted as covered by this landing).

## Witness: authorized execution closeout

After a plan execution landed and its review records migrated, the owned-files preflight and `gate-removal` both passed; the gate reported an exact-tree-accounted branch and printed the worktree-removal command. The agent stopped to ask whether to complete cleanup despite the session's existing authorization. After correction, it reconciled the ignored and untracked inventory, released its execution claim, removed the exact worktree, deleted only the unchanged branch at the gate's captured OID, and verified the run's resources were gone. The current closeout procedures and gate succeeded without a new safety mechanism. This narrows the remaining gap to terminal ownership and continuation: a passing verdict is not the finish when the authorized sequence still has printed cleanup steps. Priority remains medium because the safeguards preserve artifacts and protect other work; the recurring cost is operator follow-up and delayed completion.

## Witness 2026-10-25 (two exec closeouts, same day, same operator question)

Two scheduled exec runs landed their plans, removed their worktrees, and retained the exact-tree husk branch per the done skill's "operator branch closeout is the only sanctioned deletion" doctrine. In both sessions the operator then asked whether all ad-hoc worktrees and branches had been removed, and in both the agent deleted the branch with a bare `git branch -D` after a tree-equality check instead of the sanctioned sequence (quiesce writers, `gate-removal` branch-only verdict, expected-OID `git update-ref -d`). The second session had a same-day feedback memory recording the first miss and still repeated it, because the memory was consulted after the deletion. Two readings for this row's fix: the operator treats a retained husk as unfinished cleanup, so the retain-for-operator doctrine produces the follow-up ask it was meant to avoid; and the sanctioned sequence is skipped under the ask because it is longer than the unsafe reflex. The open plan `docs/history/plans/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md` already carries the direction (the owning run completes the sanctioned branch closeout itself); this witness raises its urgency and adds the requirement that the closeout report print the one-step sanctioned command for any branch it does retain.

## Witness 2026-10-25 (operator sweep: landed-husk pair and a detached Codex checkout)

An operator-asked sweep over branches and worktrees found two landed husks: a completed exec run's origin worktree with its same-named branch (the branch tip's only unique commit flipped the status line of a backlog row the landing had already deleted on main; the worktree was clean), and a two-day-old detached Codex checkout whose sole commit was its landing's content (subject twin, byte-equal diff). Both were removed after re-deriving landedness per lesson #78's witness route; the two same-day worktrees still in use were left untouched after a liveness re-derivation. New angle: the sweep's main expense was session attribution for the operator (which live session to prompt), and the task index could not answer it; the mechanics are recorded as lesson 229. Priority remains medium; the residue cost stays rediscovery and cleanup delay.
