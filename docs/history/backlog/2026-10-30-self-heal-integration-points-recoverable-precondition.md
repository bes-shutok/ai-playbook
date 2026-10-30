# self-heal Integration Points map still carries the superseded recoverability precondition

- **Filed:** 2026-10-30, execute-plan Step 1.2b capture (run self-heal-before-unknown-remedy, contract-docs worker finding #1)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** consumer projects share these skills; leaving the superseded recoverability precondition in self-heal's peer map lets callers re-import the twice-witnessed prove-recoverability-first failure this run's plan just removed.
- **Origin class:** self-serving
- **Class:** fix-class
- **Severity:** Medium
- **Dedup probe:** searched open backlog names and findings for `self-heal`, `integration points`, `recoverable precondition`; no open row covers the self-heal/using-skills caller-map drift.

Driving force: correctness — the caller-trigger correction in plan docs/history/plans/completed/2026-10-29-self-heal-before-unknown-remedy.md removed the "recoverable" precondition from the `plans` and `done` handoffs, but `agents/skills/self-heal/SKILL.md` (Integration Points, ~lines 33-34) still describes both callers as invoking "for recoverable authoring stops" / "on a recoverable closeout failure". A future editor or caller can reconcile the corrected handoffs back toward the map and resurrect the twice-witnessed "prove recoverability before recovery" failure the plan fixes.

Scope: update the two Integration Points entries in `agents/skills/self-heal/SKILL.md` to the trigger-before-judgment shape; also in scope: the frontmatter description's recoverable-obstacle phrase (same file, lines 4-6), the line-32 Integration Points entry (`using-skills` routes any recoverable skill-workflow stop here), and the matching recoverable-blocker shape in `agents/skills/using-skills/SKILL.md:42` ("Before stopping a skill workflow on a recoverable blocker, invoke `self-heal`"); text-balance discipline applies.

Origin: execute-plan run self-heal-before-unknown-remedy (2026-10-30), Task 1 Step 1.2b contract-docs worker finding #1; path deliberately left out of that plan's Review Scope ("report any causally necessary path before editing it").
