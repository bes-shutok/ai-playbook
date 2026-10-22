# Backlog: maintenance skill plan citations resolve to pre-archive paths

- **Filed:** 2026-10-22, execute-plan run maintenance-occupied-target-fallthrough Phase 3 r3 (design-simplicity lens, existing-debt capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** consumer-pet
- **Class:** fix-class
- **Driving force:** code-quality
- **Skill/step:** `agents/skills/maintenance/decisions.md` (and the sibling citations sharing the shape)

## Problem

Several plan citations inside `agents/skills/maintenance/decisions.md` name plans-root paths that exist only under `docs/history/plans/completed/` after the archive move (for example `docs/history/plans/2026-10-05-near-reset-defer-directive-hierarchy.md`; five more citations share the shape). A reader following the citation hits a missing path and must re-locate the dossier by basename. Witnessed 2026-10-22 in the run worktree at r3; the citation class is byte-identical to main (pre-existing), and the r2 witness-tail sheds made the retained pointer the sole in-skill anchor for its witness.

## Expected

Citations whose target lives under the completed archive resolve, or the citation names the archive path (or the convention's canonical resolution rule) so the pointer is followable; a single sweep over the file's plan citations closes the class.

## Suggested fix

One pass over `agents/skills/maintenance/decisions.md` (and any sibling file with the same citation shape): resolve each plans-root citation against the tree; where the target moved to `completed/`, cite the archive path or the canonical resolution. Byte balance per the anti-growth rules is trivial here (path prefixes only).
