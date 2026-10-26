# Backlog: the Worktree-first survey arm's live-peer-hold signal misses a clean worktree holding unlanded commits

- **Filed:** 2026-10-26, learn Step 1.8 over the 2026-10-26 interactive exec mandate session (self-witness: the session that landed the ad-hoc survey sentence)
- **Status:** open
- **Priority:** medium
- **Workflow:** backlog
- **Class:** fix-class (one clause on the survey arm's hold signal; no gate proposed)
- **Origin class:** skills-corpus defect (the landed sentence names only the uncommitted-edits hold signal)
- **Skill/step:** `agents/skills/execute-plan/worktree-first.md` lifecycle step 1, the survey arm's ad-hoc sentence ("a same-subject worktree holding uncommitted edits is a live peer hold")

## Observed versus expected

An exec-mode session arriving while two sibling sessions ran the same rolling-log mandate found both peers' same-subject worktrees already present, each clean (`git status --porcelain` empty) and each holding committed, unlanded work in the post-review pre-landing state, with HEAD commits minutes old. Under the landed hold signal (uncommitted edits) both read as not held; the session established they were live only by reading the host session store for recently updated sessions carrying the same mandate title, then skipped both targets. Expected: the survey arm's hold signal also names the clean-but-live shape so a reader without a session-store probe reaches the same skip.

## Reproduction evidence

Worktree list showed two same-subject worktrees whose branch tips were not ancestors of the base branch and whose HEAD commits were dated after the worktrees' creation (the re-point witness project lesson 233's third conjunct names); both landed on the base branch within the following hour. No claim file existed on either side.

## Environment

Runtime: interactive session, 2026-10-26, repo copy of the vendored skill; three parallel sessions on one mandate.

## Suspected root area

The ad-hoc survey sentence was written from a witnessed uncommitted-edits collision and never extended to the committed-unlanded shape the same session class produces between its review rounds and its landing.

## Requested arm

One clause on the survey arm's ad-hoc sentence: a same-subject worktree holding uncommitted edits, or whose HEAD commit postdates the worktree's creation and is not yet an ancestor of the base branch (project lesson 233's re-point witness), is a live peer hold; the run skips the target and reports.
