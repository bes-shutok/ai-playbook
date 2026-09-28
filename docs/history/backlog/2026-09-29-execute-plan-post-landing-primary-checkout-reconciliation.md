# Backlog: Reconcile live checkouts after every squash landing (stale-checkout witness and discriminator)

- **Filed:** 2026-09-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** incident (internal)
- **Driving force:** reliability
- **Source:** worker-lifecycle squash landing f4b110bb (2026-09-29 17:04) left `agents/skills/execute-plan/SKILL.md` stale in the primary checkout for roughly 90 minutes. The stale bytes looked like an ordinary local modification; restoring them required manual blob forensics, and committing them would have reverted three landed worker-lifecycle prose blocks (the receipt-fenced launched-handoff recovery row, the evidence-contract digest seeding sentences, and the driver child-prompt paragraph).

## Problem

The landing protocol is ref-level by design: a run lands from its ad-hoc worktree as a temp-index squash under the merge-landing lock, and moving the base branch's ref writes no working tree anywhere. That trade is accepted on the landing side (lesson 6 in `docs/maintenance/development_lessons.md`, "Land a Squash Only From a Tree Merged With the Current Default Branch", owns the clobber side), but the checkout side has no owner: nothing in the worktree-first canonical lifecycle, the done closeout, or the maintenance landing tails is responsible for bringing live checkouts of the base branch current after the ref moves.

The witnessed incident had three stacked failures:

1. The landing session performed a primary-checkout refresh at roughly 17:05, but it was partial: sixteen of the landing's seventeen changed paths were rewritten, and `agents/skills/execute-plan/SKILL.md` was skipped. The refresh had no completion check, so the partial result presented as done.
2. Git status then rendered the stale file as a normal local modification, indistinguishable from an intentional uncommitted edit. Sessions correctly treat foreign dirt as untouchable, so the safe behavior preserved the hazard: the stale state survived two session handoffs, one of which explicitly classified it as "likely a live peer's in-flight edit and left it alone".
3. No mechanical test anywhere distinguishes a stale-checkout artifact from a real edit. The discriminating evidence existed on disk the whole time (the working file's blob equaled the path's blob at an ancestor commit, and its mtime predated every commit it supposedly reverted), but recovering it required ad-hoc forensics that are documented nowhere.

A later session one step less careful would have committed the reversal, silently reverting landed recovery prose mid-execution-lane.

## Location

- `agents/skills/execute-plan/SKILL.md`, Worktree-first standard canonical lifecycle (step 4 "Land under the lock" and the surrounding landing duties).
- `agents/skills/execute-plan/SKILL.md`, tracked-dirt inversion check (between migration and removal), the existing dirt-classification site.
- The `done` skill's closeout dirt classification, and the maintenance payloads' landing tails (they repeat the landing pattern).
- `scripts/reverse_squash_guard.py`, the existing guard script for the landing-side sibling of this failure.

## Expected behavior

After any landing that moves a branch ref, every live checkout of that branch is either brought current or explicitly recorded as blocked, and any "modified" file that is actually a stale-checkout artifact is mechanically recognizable and restored rather than committed. A refresh that is not verified complete does not count as done.

## Acceptance

- The worktree-first canonical lifecycle gains a post-landing reconciliation duty: after releasing the merge-landing lock, the landing session fast-forwards every live checkout of the base branch (`git merge --ff-only <base>` or equivalent) and then verifies completion by confirming the synced paths carry no diff against the new base tip and git status shows no reverse-diff signature.
- When foreign local modifications block the fast-forward on a path the landing changed, the session records a named block (the stale paths plus the blocking witness) and reports it; it never force-resets, never steals the blocking file, and never leaves the block implicit.
- A documented mechanical discriminator distinguishes stale-checkout artifacts from intentional edits before any dirt is classified: compute the file's blob hash and compare it against the path's blob at ancestor commits (`git hash-object` versus `git rev-parse <commit>:<path>` over `git log --format=%h -- <path>`); an ancestor-blob match is a stale witness, restore it from the base tip and record the restoration, never commit it. The file's mtime predating the commits it reverses is a supporting signal, not the gate.
- The discriminator is wired into the existing dirt-classification sites (done closeout, tracked-dirt inversion check) so a stale witness found at any gate is handled by the same restore-and-record arm instead of being left as unexplained dirt.
- The witnessed incident shape is covered end to end: a working file whose blob equals an ancestor blob of the same path while HEAD has advanced past it is detected, classified stale, restored, and the restoration recorded, with the landed content verified present afterward.

## Rejected alternatives

- Force-resetting live checkouts after every landing: rejected; the primary checkout is shared, and force would destroy genuine concurrent work (a peer had files staged there during this very incident).
- Banning ref-level landings in favor of checked-out merges on the primary: rejected; it reintroduces the serialization the merge-landing lock and temp-index pattern removed, and lesson 6 already fixed the landing-side danger more cheaply.
- Relying on sessions noticing the dirt: rejected by the witness; two sessions encountered it and the correct don't-touch-foreign-dirt policy kept the hazard alive for 90 minutes.
- Mtime-based staleness detection as the gate: rejected; mtime survives unchanged under timestamp-preserving copies and races with git's stat cache, so it is at best a pre-filter.
