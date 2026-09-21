# Backlog: merge dirt backup/restore lacks a regression gate against new HEAD

- **Status:** done (delivered by docs/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-gates.md, executed 2026-09-22)
- **Date:** 2026-09-21
- **Origin:** peer-dirt forensics session 2026-09-21 (done-lock.sh dirt = stale Sep-4 deployed copy riding the execute-plan-mechanics squash merge's backup/restore; lesson #406 is the principle capture, this item owns the mechanical fix)

## Skill and step

`agents/skills/execute-plan/SKILL.md` Phase 4/5 merge sub-agent dispatch template (the "known peer-dirt files must not be committed" instruction), the `done` skill's shared-checkout pre-commit guard (Step 3 item 1), and the dirt-preservation dance used by every gated squash merge.

## Observed versus expected

Observed: merge dispatch prompts verify dirt by file LIST only ("git status --porcelain should show only the two known peer-dirt files"), and the backup/restore around `git merge --squash` faithfully re-preserves whatever bytes were dirty, regardless of whether those bytes regress content HEAD gained since the run's merge-base. Witnessed 2026-09-21: a byte-identical revert of the committed merge-lock common-dir keying (181af6cc) to the stale Sep-4 deployed copy rode three successive merges untouched, because every check compared paths, never diff direction.

Expected: preserving dirt is conditional on the dirt being forward work. After the squash commit and dirt restore, the merge/done agent runs `git diff HEAD -- <restored files>` and classifies each hunk; any hunk that removes lines present in HEAD (added since the run's merge-base) marks that file a dirt REGRESSION: restore the file from HEAD, drop the backup, and report the regression in the merge agent's final summary instead of re-dirtying the tree.

## Suggested fix

1. Add the regression-gate step to the execute-plan Phase 4/5 merge dispatch template right after the tree-identical gate: the diff-direction check described above, with the restore-from-HEAD remedy and a required summary line per restored file.
2. Add the same check to the `done` skill Step 3 item 1 pre-commit guard (it already detects a leaked staged revert; extend it to unstaged dirt that regresses HEAD).
3. Pin it with a fixture in the done-lock/runtime test suite: seed dirt that removes a hunk from HEAD, run the gate, assert the file is restored from HEAD and the regression is named; assert forward-looking dirt still passes untouched.
4. Deploy-freshness half: deployed runtime copies under `~/.ai-playbook/scripts/` refresh only on manual deploy (done-lock.sh was Sep 4 while main had three later rewrites). Either deploy on landing (skill-landing closeout step) or stamp deployed copies with their source commit and let the regression gate cite the stamp as provenance evidence.
