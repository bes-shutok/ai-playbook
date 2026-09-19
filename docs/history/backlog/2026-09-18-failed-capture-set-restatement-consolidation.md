# Backlog: consolidate the failed-capture set to one definition and reference it

Status: open
Priority: low

Workflow: backlog
Severity: low
Source: code review r3 of plan `docs/plans/2026-09-16-learn-done-workflow-updates.md` (finding F6, 2026-09-18); staging doc `docs/reviews/2026-09-16-learn-done-workflow-updates-code-review-r3.md`.

## Finding

The failed-capture set (learn-authored artifacts whose Step 1.8 commit learn reported as failed) is stated five times in `agents/skills/done/SKILL.md`: the frontmatter description's parenthetical, the Step 4 intro paragraph, Step 4 item 2's dirty-path check, Step 4 item 3's session-attributed classifier, and the Rules section's directory-wide-add line. done's Step 1 note adds a contradiction site: it still states the pre-extension property ("Step 4 sees only non-learn leftovers"), which the extended set invalidates. `agents/skills/learn/SKILL.md` carries the learn-side variant in its commit-boundary sentence's parenthetical (mirroring done's frontmatter exception). That is seven surfaces across two skills. The Step 4 rewrite AND the Step 1 note sentence are plan-prescribed text (the plan's Task 2 checklist items; frozen scope of record for the run); the Rules-line parenthetical, item 3's classifier clause, and the frontmatter parenthetical are execution-added (review-fix) text, and no Validation gate pins the failed-capture phrasing (grep-verified against the plan's checker literals), so a consolidation plan needs no gate-literal edit, but both plan-quoted sentences need the same-pass scope-of-record refresh. Drift risk: a future change to the set's definition must be replicated at seven sites across two skills and can miss one.

## Suggested fix

A future plan should define the failed-capture set once in done SKILL.md (one named sentence, for example in the Step 4 intro or Rules) and rewrite the remaining done sites (including the Step 1 note's contradiction) plus the learn variant to reference that definition. No validation pins quote the failed-capture phrasing, so no gate literals need updating; the plan-quoted sentences (the Task 2 Step 4 rewrite text and the Step 1 note sentence) should be updated in the same pass so the plan's scope of record matches the implemented text.

## Why not fixed now

The consolidation is a seven-surface cross-skill rewrite owned by a dedicated plan, not an in-run fix; a sibling-doc restatement converts to backlog per the receiving-review Phase 3 default (ADR-0002). (Inventory and plan-prescribed attribution corrected by review r4, 2026-09-18: five done restatement sites plus the Step 1 note contradiction plus the learn variant; only the Step 4 rewrite is plan-prescribed; no gate pins the phrasing.)
