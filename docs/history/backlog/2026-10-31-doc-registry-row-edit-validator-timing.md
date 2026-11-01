# Backlog: malformed doc-registry rows land on main when the validator runs only at a later landing's sweep

- **Filed:** 2026-10-31, learn Step 1.9 over the exec carrier session zcode-exec-20261031-statusfacts
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** witnessed defect
- **Class:** fix-class
- **Cluster:** docs/history/backlog/completed/2026-10-31-machinery-registry-canonical-serializer-round-trip.md (the same registry's row-shape machinery)

## Problem

Commit `c63419139` (2026-10-31 20:17, clearing a licensed archive write's audit note) left the `plan-authoring-stand-down-before-charter` registry row with 8 of 9 cells — the trailing empty-cell pipe was dropped by the hand edit. The malformed row sat on `main` for roughly two hours until a different session's landing sweep ran `doc-registry validate` and hard-refused; the repairing session then fixed it as a side change riding its own landing (`0cda7cc45`, landed in `bc227e63e`). The landing-time validator caught the defect only at the NEXT session's landing, not at the edit's own commit.

## Direction (pre-scoping; not a verdict)

The candidate arms: run `doc_registry_validator.py validate` in the same commit path that edits a registry row (a done commit-stage duty or a pre-commit expectation named in the skill text), or a serializer/round-trip helper for row edits. Any arm that adds a gate carries the machinery admission protocol's incident fields.
