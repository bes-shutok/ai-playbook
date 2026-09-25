# Backlog: add the `migration audit` marker to the shadow plan's six reconciled registry rows

- **Status:** open
- **Captured:** 2026-09-26, P65 execution review r1 (Major): the registry row reconciling the docs-branch shadow plan's six origins (docs/maintenance/document-registry.md, the `fold-then-delete reconcile` row) carries `user-approved` but not the `migration audit` marker, so the new origins-checker registry consult cannot resolve those six origins and the corpus scan still warns on all six of them.

## Why

P65 Task 4's landing note anticipates exactly this shape: rows landed by an earlier plan without the marker leave the consult inert for their origins, and marker compliance is a recorded follow-up before the consult can resolve them. This item is that record.

## Fix shape

Append the `migration audit` marker to the notes cell of the shadow plan's reconcile row (cell-content edit, not a format change), then re-run `python3 scripts/check_plan_origins_closed.py` and confirm the six remaining warns naming those origins resolve while the two genuine-straggler faces (`2026-09-25-rearm-form-field-writer-attribution.md`, `2026-09-25-stale-branch-diff-restaging-reverse-squash-guard.md`) still fire.
