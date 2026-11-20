Status: open
Workflow: backlog
Priority: low
Class: fix-class (a caller that holds the merge lock before calling the landing helper deadlocks it for the full bounded wait)
Origin class: session-witnessed (Claude Code, 2026-11-20, landing the first of two plan branches)
Driving force: reliability
Added: 2026-11-20

# `land_squash.sh land-worktree` takes the merge lock itself; no skill text says a caller must not pre-acquire it

## Problem

A caller that ran `done-lock.sh merge-acquire` before `land_squash.sh land-worktree` held the lock while the helper's swap critical section waited on that same lock. The helper's pre-lock gates ran, then it polled every 30 seconds and timed out after 300 seconds with `refuse: the swap-critical-section merge lock is held after the bounded wait`. The holder named in its output was the caller's own label and a live PID. The caller released its lock and re-ran the helper without pre-acquiring; the landing then passed at once. The helper's `land-worktree` usage paragraph already says the caller must not hold a merge lock around the invocation, but the execute-plan landing step (`agents/skills/execute-plan/worktree-first.md`, step 4) says only "under the repository's merge-landing-lock discipline", so a caller that reads the skill and not the usage paragraph acquires the lock first.

## Observed vs expected

Expected: the landing contract says the helper owns the merge lock for its swap span and a caller never pre-acquires it, or the helper refuses fast when the lock it is about to wait on is held by the invoking session. Observed: a silent 5 minute wait, then a refusal that blames a foreign holder.

## Ship when

The execute-plan landing step states in one sentence that the worktree landing helper takes and releases the merge lock itself and a caller never holds one around it.

Dedup probe: searched backlog for `land-worktree`, `merge-acquire`, `pre-acquire`; the 14 land-worktree rows cover guard wording, staged desync, and rename blindspots, none covers lock ownership.
