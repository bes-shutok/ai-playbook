# parked done-target-state v9 polish landing never fired

Driving force: reliability
Date filed: 2026-10-17
Origin: 2026-10-17 worktree/branch sweep witness

## Finding

The done-target-state-learn-commit-closeout rider commit (`a5a7656f7`) records that the "r8-certified v9 polish landing parks on branch tip 1ef081c27 behind the peer's staged index entry and lands as the follow-up when the index clears". The index long since cleared, but no follow-up landing exists on main and no record of a supersession either; the branch `wt-done-target-state-closeout-authoring` (tip `1ef081c27`, "wip: plan v9 readiness byte-limit splits of the four over-limit criteria, the two r7-deferred prose residues folded") is the only copy of that certified work. A parked landing whose unblock condition has passed but whose follow-up has no owner is stranded certified work: nothing will ever land it, and the branch is one sweep away from destruction.

## Expected

Either the parked polish lands (after re-deriving the v9 delta against current main, since the done/closeout surfaces moved after 2026-10-11), or its supersession is recorded and the branch deleted; the indefinite-park state is the defect. The unblock condition ("when the index clears") is verifiable from disk and long satisfied.

## Evidence

- `a5a7656f7` rider commit message (the park record and its unblock condition)
- branch wt-done-target-state-closeout-authoring tip `1ef081c27` (the only copy of the v9 fold)
- `git log main` carries no landing naming the v9 polish or its supersession (re-derived 2026-10-17)
