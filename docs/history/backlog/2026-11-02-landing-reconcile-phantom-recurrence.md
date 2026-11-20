Status: open
Priority: high
Class: tooling-gap
Origin class: learn Step 1.9 project issue capture (2026-11-01 two-pick exec carrier, lesson 249 third witness)

Cluster: scripts/worktree_closeout_migrate.py (same defect class: stale pre-landing bytes presenting as staged primary-checkout dirt; the 2026-11-01 clobber-guard cluster row was deleted at its ad-hoc landing, which owns the repair)
Cluster: docs/history/backlog/2026-10-26-landing-grammar-review-residue.md (same surface: the landing helper's post-landing tail)

## Observed versus expected

The landing helper (`scripts/land_squash.sh`) already runs a path-exclusive
post-landing reconcile that restores the primary checkout's index and
worktree for the landing's touched paths. Despite that pass, one two-pick
execution session hit the stale pre-landing-bytes phantom three times
(development_lessons.md #249 third witness): pre-edit corpus bytes staged
after the first landing, pre-edit skill-text bytes after the second, and a
staged registry-row deletion after a reconcile pass had already run for that
landing. Each phantom cleared only by a manual
`git status --porcelain --untracked-files=no` read plus
`git restore --source=HEAD --staged --worktree -- <paths>`.

Expected: after the helper's reconcile completes, the primary checkout holds
zero reversal-shaped staged entries for the landing's touched paths, and the
helper's tail verifies that (a status read as part of the landing output, not
a manual follow-up). Observed: phantoms survive or appear after the
reconcile, and the only detector is the run session's own discipline.

Suspected root area: the reconcile's snapshot-and-restore set is built from
the landing's diff paths, while the phantoms observed include paths staged
outside that set (bytes staged in the primary index between snapshot and
ref-move, or classified as peer state and deliberately left). The fix arm is
a deterministic verify-and-restore tail over reversal-shaped staged entries
for landing-touched paths, plus a test pin reproducing the between-snapshot
staging window; any new refusal or restore arm follows the machinery
admission protocol (incident: this row; expected catch: recurring per
worktree landing under a dirty primary index; false-positive cost: bounded to
landing-touched paths after diff verification; review: re-audit at the next
landing-helper defect row).

## Environment context

Runtime: ZCode automation session, worktree-planned execute-plan run, two
squash landings through the landing helper, primary checkout on the default
branch. Date: 2026-11-01/02.
