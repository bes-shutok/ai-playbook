Status: open
Priority: high
Class: fix-class
Origin class: skills-corpus audit (learn Step 4.5 placement-time cross-reference duty, 2026-11-05 harvest pass)

# Ten recent corpus lessons are orphaned or unwired; learn's placement-time cross-reference duty never fires

## Problem

A 2026-11-05 citation audit over the project lessons corpus: of twenty recently captured lessons audited, only #104 is cited from an instruction or skill file. Five lessons have zero inbound references of any kind (#336, #365, #385, #395, #399), five more are cited nowhere outside the corpus itself (#333, #335, #383, #384, #398), and the five newest (#395-#399) carry no skill or instruction wiring at all. `learn` Step 4.5 ("Add Cross-References for Lesson Discoverability") states the duty at placement time, but no capture pass in the audited window executed it: the corpus grows, discoverability does not, and a lesson the corpus already holds gets re-witnessed by workers who never see it (witnessed same day: project lesson #271's macOS path-resolve arm was re-bitten by a test fixture worker on 2026-11-05 01:46Z).

## Observed vs expected

Observed: lessons land in the corpus and stop there; findability depends on luck or on a later session grepping the corpus unprompted.
Expected: each new lesson lands with at least one discoverability anchor (an owning-surface citation where the lesson is load-bearing for a skill step, or a See-also from its family sibling where it is consult-at-need reference material); the current orphan set gets an explicit disposition (cite, cross-link, or retire/merge if superseded), under the repository's anti-growth rules: additions pay with equivalent deletions, and a citation is added only where load-bearing, never as unpriced decoration.

## Evidence (trimmed)

- Fresh greps 2026-11-05: `#336`, `#365`, `#385`, `#395`, `#399` return zero matches outside `docs/maintenance/development_lessons.md` (repo-wide, tracked instruction and skill surfaces); heading lines confirmed at corpus lines 5142-5998.
- Placement-time non-execution witness: lessons #395-#399 landed 2026-11-04 in two certified landings; neither landing's diff touches a skill or instruction file beyond the corpus itself.
- Re-bite witness: the 01:46-02:09Z implement worker on 2026-11-05 recreated lesson #271 arm (2)'s exact failure (raw `/var/...` vs resolved `/private/var/...` path keys in a worktree fixture) before self-correcting.

## Suspected root area

`agents/skills/learn/step-2-placement.md` Step 4.5 and the learn run's completion checklist: the duty is stated but never enforced, hinted at write time, or priced; the sweep row owns the remediation pass over the current orphan set, and a one-sentence placement-time hint in the owning skill (priced under the anti-growth rules) is the prevention arm.

## Ship when

Every lesson in the audited orphan set carries an explicit disposition line (cite / cross-link / retire, with the reason), the net corpus growth respects the anti-growth rules, and a re-run of the citation audit shows zero fully-orphaned lessons in the set.
