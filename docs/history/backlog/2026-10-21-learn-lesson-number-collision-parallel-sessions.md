# Backlog: learn's project-corpus lesson numbering collides under parallel sessions; the duplicate check is optional and warn-only

- **Filed:** 2026-10-21, learn pass over the certification-seal-landing-survival execution session
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed recovery gap
- **Class:** fix-class
- **Skill/step:** `agents/skills/learn/step-2-placement.md` (the project-corpus `#N` allocation at write time); `agents/skills/learn/step-6-instruction-updates.md` Step 6.6 (the "Project-tier dup check (warn-only, no script)" line); `scripts/lessons.py index` (the user-corpus validator whose `duplicate` category already exists)
- **Driving force:** reliability (a lesson number is the corpus's recall key; a collision silently splits every `See also #N` citation across two lessons)

## Problem

Several sessions append to `docs/maintenance/development_lessons.md` in one day, each allocating the next `#N` from the number it last read. Nothing re-reads the maximum immediately before the write, and the only duplicate guard is an optional, warn-only `grep | uniq -d` the skill text calls "no script". On 2026-10-21 the corpus carried four colliding pairs (142, 143, 151, 152) from three sessions, and the repair itself raced a live peer twice (161 and 164 were each claimed by two writers within minutes). Citations such as `See also #142` now point at whichever heading the reader finds first.

## Expected

1. Allocation re-derives `max(#N) + 1` from a fresh read immediately before the append, inside the same write step (the stale-read drift rule the rolling prompt logs already apply).
2. The project-tier check reuses the existing validator: Step 6.6 runs `lessons.py index` (or its `duplicate` category) over the project corpus too, blocking the learn run on a colliding heading the same way the user-corpus gate does, instead of the optional warn-only grep.
3. The learn commit rule's own-edit hunk check is applied to the corpus commit: a whole-file `git add` sweeps a peer's uncommitted lesson into the committer's commit (witnessed in this pass), which lesson 134 already names as the clobber class.

## Evidence

2026-10-21 corpus state before repair: `## 142.` at two headings (42a0a3b1f 03:20 and 0e531d4fb 12:17), `## 143.` likewise, `## 151.` (42a0a3b1f and 82693ea35 11:27), `## 152.` (42a0a3b1f and e8456ebf0 14:08). Repair commits 6eaa2c333 and d5077a0fc renumbered the later arrivals (160, 161, 162, 165); a peer session concurrently appended and renumbered its own lesson to 164 (c0b25a15e). The first repair commit also carried that peer's then-uncommitted heading because the corpus was staged whole-file.

## Why not fixed now

The allocation and gate edits are learn skill text plus a gate invocation change, which the learn run that witnessed it does not own (learn commits only its backlog items and lesson edits); the live peer race made further in-place repair unsafe this turn.

## Source

- Observed 2026-10-21 during the learn pass of the certification-seal-landing-survival execution session; the renumbered headings and the collided commits above are the witnesses.
