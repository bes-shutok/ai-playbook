# Backlog: systematic-debugging skill references files, skills, and a phase that do not exist
Cluster: docs/history/backlog/2026-11-01-skill-review-cross-skill-repetition-debt.md; docs/history/backlog/2026-11-01-skill-review-maintenance-stance-stale-cap-wording.md; docs/history/backlog/2026-11-01-skill-review-review-agents-portability-markers.md (same-day review family)

- **Filed:** 2026-11-01, weekly skill-review lane run 1 (batch unit: agents/skills/systematic-debugging/)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** audit-lane finding (advisory review suggestion, read-only)
- **Class:** fix-class

## Problem

Three internal references in `agents/skills/systematic-debugging/SKILL.md` dangle against the tracked tree: (1) lines 114 and 280-284 promise `root-cause-tracing.md`, `defense-in-depth.md`, and `condition-based-waiting.md` "in this directory" while the directory holds only LICENSE.txt and SKILL.md; (2) lines 179 and 287 point to a `/test-driven-development` skill that does not exist (the actual skills are `tdd-guide` and `tdd-design`); (3) line 232 says "see Phase 4.5" but no such phase exists (the referenced text is Phase 4 step 5 at line 199).

## Expected

Every cross-file and cross-skill reference in a shipped skill resolves: promised companion files either exist or the references are deleted; skill names match the catalog; phase anchors name real spans.

## Suggested direction

Bounded arms: restore the three promised reference files from their upstream source if the vendored sync dropped them, or delete the promises; repoint the TDD references at `tdd-guide`/`tdd-design`; fix the phase anchor to "Phase 4 step 5". Either arm is one file's edit plus a reference-resolution check.

## Evidence

- Weekly skill-review run 1 aggregates record, findings 28-30 (docs/maintenance/skill-review-log.md), with line-precise spans; directory listing shows LICENSE.txt and SKILL.md only.
