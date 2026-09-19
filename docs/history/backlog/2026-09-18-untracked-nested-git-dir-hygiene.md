# Backlog: surface untracked nested git directories at done time

Status: open
Priority: medium

Workflow: backlog
Source: 2026-09-18 repoA/repoB fixture incident; done session investigation same day.

## The gap, precisely

Untracked nested `.git` directories are invisible to `git status`, to every hygiene gate the done flow runs, and render in GUI graph views as detached commits from an unrelated history. A leftover scratch repo can persist indefinitely with no signal to any lane or to the user (witnessed 2026-09-18: `repoA/` and `repoB/` sat in the repo root for half a day before a human noticed; a peer lane's leftover worktree under /tmp held the learn-done branch checked out the whole time, which also blocks plain `git worktree add` of that branch).

## Suggested fix

Add a cheap detection surface that runs at done time in the project repo, hosted repo-locally (alongside `check_backlog_inbox_location.py` in the pre-docs-branch validation cluster) so the vendored done skill needs no re-vendor:

- `find . -maxdepth 3 -name .git -not -path './.git*'`, then subtract registered worktrees (`git worktree list --porcelain`), submodules (gitdir links into `$GIT_COMMON_DIR/modules`), and gitignored runtime paths.
- Warn loudly, naming each remaining path; never auto-delete: classification before removal per the foreign-path discipline (a peer lane may own it).
- The warning names the likely owner class (scratch fixture, interrupted lane, GUI-visible detached commits) so the human can decide in one glance.

## Acceptance

- A repo holding an untracked nested `.git` produces a named warning during done.
- Registered worktrees, submodules, and gitignored runtime dirs do not trip it.
