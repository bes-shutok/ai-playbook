# Backlog: unify successor-row and override-row licensing for freeze moves in doc-registry check-writes

Status: done
Workflow: backlog
Origin: Plan-review r8 Low (plausible-edge, hypothesis confidence) on `docs/plans/2026-09-08-doc-ownership-lifecycle.md`, digest 33bf86f3
Severity: Low
Scope: `scripts/doc_registry_validator.py` (Task 1 of the doc-ownership-lifecycle plan) and the Task 1 fixture contract
Related: plan `docs/plans/2026-09-08-doc-ownership-lifecycle.md`; backlog `2026-09-08-document-ownership-and-archive-lifecycle.md`

## Problem

The plan's `check-writes` contract pins only the ADR-0001 corruption-override row as a license for a write under a completed-history path. A legitimate freeze move (archive `git mv` plus its successor registry row, per the lifecycle Task 5 prescribes) produces a path change the validator must also license, but no fixture pins the successor-row licensing shape. Today only the `--diff` channel can observe staged moves at all, which keeps the gap Low; the argv and stdin channels see post-move paths that simply look like additions.

## Suggested fix

When implementing plan Task 1, extend the fixture contract: `test_check_writes_successor_row_licenses_move`; given a move out of an immutable dir whose registry row carries a successor/superseded relation with date and reason, `check-writes` expects exit 0; and a move with no such row expects exit 1. If the implementing plan defines successor-row licensing as out of scope for the first cut, record the decision in the validator's usage text instead of leaving the behavior unpinned.

## Acceptance

- The licensing shape for freeze moves (successor row) is either fixture-pinned or explicitly documented as unpinned in the validator usage text.
- No ambiguity remains between the corruption-override row and the successor-row path.
