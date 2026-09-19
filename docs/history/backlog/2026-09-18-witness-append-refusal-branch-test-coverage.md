# Backlog: executable coverage for docs_branch_witness_append refusal branches

Status: open
Priority: medium

Workflow: backlog
Source: code review r1 of plan `docs/plans/2026-09-16-learn-done-workflow-updates.md` (finding F3, 2026-09-18); staging doc `docs/reviews/2026-09-16-learn-done-workflow-updates-code-review-r1.md`.
Severity: Low (test-gap-only; the behavior itself is correct and its happy path plus wrong-prefix refusal are pinned)

## The gap, precisely

The plan's G9b gate extracts `docs_branch_witness_append()` from `agents/skills/docs-branch/SKILL.md` and executes it in a throwaway repo, but only two paths get executable coverage:

1. wrong-prefix refusal (a line not starting with `lesson-scope-audit:` returns 1)
2. the happy path (a canonical line commits to the `docs` branch and is greppable)

The three other refusal branches the function documents in its own failure semantics have no executable coverage (two further defensive refusals, the mktemp-failure guard added by the r2 subshell rewrite and the detached-worktree guard, are also uncovered; a future fixture should sweep all five, e.g. detached via pointing `refs/heads/docs` at a non-branch commit, mktemp via an unwritable TMPDIR):

- **Missing docs-branch refusal**: when `refs/heads/docs` does not exist, the function must return non-zero with the loud message ("no docs branch; run a sync first") instead of overstating coverage. Nothing fails if a regression silently commits elsewhere or returns 0.
- **Worktree-add failure**: when `git worktree add "$_wt" docs` fails (for example a leaked prior worktree already holds the `docs` branch checked out, or an interrupted append left a stale registration), the function must return non-zero loudly. Nothing fails if a regression swallows the error or leaves the worktree behind.
- **Commit failure**: when the append's `git commit` fails (for example an empty commit ident: unset `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL`/`user.name`/`user.email` forces the commit to fail), the function must return non-zero with its loud message ("witness commit failed"). A regression that swallows the rc would overstate coverage: the caller (done Step 3 item 6) would treat the append as landed and skip the manual follow-up it owes on append failure.

## Suggested fix

A future plan editing the G9b block in the plan's Validation Commands (a plan-file digest change, hence out of scope for the review-fix round that raised this item) extends the fixture subshell with these assertions:

1. Missing-branch refusal: source the function right after `git commit -q --allow-empty -m init` and BEFORE creating the `docs` branch ref, then assert refusal:

   ```bash
   if docs_branch_witness_append "lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run"; then
     echo "VALIDATION FAIL: witness append accepted a missing docs branch" >&2
     exit 1
   fi
   ```

2. Worktree-add failure: after creating `refs/heads/docs`, register a second worktree on the same branch first (`_blk="$(mktemp -d)"; git worktree add "$_blk" docs`), assert `docs_branch_witness_append` with the canonical line returns non-zero, then `git worktree remove --force "$_blk"` so the later happy-path assertion runs against a clean state. This also exercises the recovery path (`git worktree prune` hint) for a leaked worktree holding `docs`.

3. Commit-failure refusal: with `refs/heads/docs` present, unset every identity variable (`env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u GIT_COMMITTER_NAME -u GIT_COMMITTER_EMAIL -u GIT_AUTHOR_DATE -u GIT_COMMITTER_DATE git -c user.name= -c user.email= ...` shape, or a fixture env without identity) and assert `docs_branch_witness_append` with the canonical line returns non-zero with the "witness commit failed" message, then restore identity for the happy-path assertion.

4. Caller-trap sentinel (pins the r2 subshell trap/variable scope property): in a `bash -c` caller that arms a sentinel trap before sourcing and invoking the function (`trap 'echo sentinel' EXIT`; call; assert the sentinel trap survives the call and still fires at caller exit), a regression that reverts to a caller-shell-level cleanup trap plus `trap -` reset fails this assertion. The r3 round verified the property manually with this sketch; the gate should pin it permanently.

5. Placement and teardown: create every fixture repo under `mktemp -d` (never the repo root) and remove the scratch dirs before the gate exits; repo-root fixtures outlive every sweep because foreign-path refusal protects them (witnessed 2026-09-18: a manual run of this recipe left `repoA/` and `repoB/` in the repo root for half a day).

A future plan owning the gate block should also refresh the plan's Task 6 embedded function block (docs/plans/2026-09-16-learn-done-workflow-updates.md, Task 6 code fence) to the implemented subshell-wrapped version, so the plan's record of the function matches what actually runs.

## Why not fixed now

The G9b gate text lives inside the plan file's Validation Commands block; editing it changes the plan digest, which the addressing round for this review explicitly excluded (the plan file is frozen scope of record for the run; review finding F3 recorded disposition "backlog"). The fix belongs to a future plan that owns the gate block.
