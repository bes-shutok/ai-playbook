- **Filed:** 2026-09-30
- **Status: done (2026-10-01; executed+landed docs/history/plans/completed/2026-10-01-entry-marker-floor-tightening.md, squash main e5299697, exec review r1 ready=yes zero blocking; origin p93 pointer corrected to p88 in the plan)(docs/history/plans/2026-10-01-entry-marker-floor-tightening.md)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving (execute-plan Step 1.2b intermediate review backlogged candidates, investigate-stage3 run)
- **Class:** fix-class
- **Driving force:** correctness (evidence-floor precision); the structural floor stays, the precision rises

# Investigate entry evidence-basis marker floor admits directory paths and free-text tails

## Problem

The `check_investigate_entries.py` marker floor (deliberately structural) admits two shapes a future reviewer should not accept as evidence without a look:

1. A bare directory path such as `docs/history/backlog/` passes the path marker while pointing at the corpus itself, not a witness for the specific disposition (live instance: the p93 entry's basis line).
2. A real path with trailing free text appended (`docs/...md scope decision`) passes because the path-prefix marker matches the span prefix; the tail is unverified prose.

## Expected behavior

Tighten the floor without raising machinery: prefer file paths over bare directories (require a `.md` suffix or an existing file), and cap or anchor the free-text tail (for example, the citation parenthetical ends the line). The marker list stays a superset floor; review judgment stays the gate above it.

## Location

- `scripts/check_investigate_entries.py` (the path-marker branch and citation-paren parsing).
- `docs/history/backlog/PLAN-PROMPTS.md` p93 entry basis line (the live directory-path instance).
