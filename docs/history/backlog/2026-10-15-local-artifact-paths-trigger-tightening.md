# Backlog: tighten the local-artifact-paths lens bullet's second trigger arm

- **Filed:** 2026-10-15, execute-plan Phase 3 review of docs/history/plans/2026-10-15-configurable-artifact-paths-in-docs.md (correctness-completeness worker finding)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** consumer-company
- **Class:** formal-hardening
- **Driving force:** code-quality
- **Skill/step:** `agents/skills/review-agents/documentation.md` (the `documentation#prose-local-artifact-paths` bullet)
- **Consumer urgency:** none observed yet; file only if live reviews misfire on the arm.

## Problem

The bullet's trigger has two arms: "a configurable artifact home's concrete value" and "a temporary configuration detail". The defining parenthetical (resolves from per-user/per-repository facts configuration; owned by a shared workflow skill) grammatically attaches to the first arm only; the second arm is undefined and unqualified, inviting overreach to documented defaults, environment variables, or install prefixes far from the witnessed shape. A related Low observation: the bullet's scope vocabulary ("durable project documentation") deliberately differs from the host section's "living Layer 1/2 documentation"; one clause tying them would remove the ambiguity.

## Expected

A future touch of the bullet attaches the facts-configuration and owned-by-skill predicates to both trigger arms (or drops the second arm), and optionally one clause linking the bullet's scope to the host section's living-doc scope. Phase 3 review r1 judged the wording self-limiting (the disposition demands citing an owning facts source or skill that spurious matches lack), so this is tightening, not a defect fix.

## Evidence

Phase 3 focused-panel review 2026-10-15, worktree 2026-10-15-exec-config-artifact-paths, findings `quality#undefined-trigger-arm` and `quality#scope-vocabulary-mismatch`; the precedence concern from the same review was folded into the landed bullet in-run.
