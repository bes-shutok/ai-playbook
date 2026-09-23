# Backlog: close the three remaining batch-2 phase-2 origin items after the merge

Status: closed (executed by the 2026-09-22 executed-origin strays and landing gaps plan; both open siblings closed and moved, deferred sibling recorded; verified 2026-09-23)
Priority: low
Workflow: backlog
Date: 2026-09-19
Class: housekeeping follow-through

## Problem

Batch-2 phase-2 (contract prose) closes four of its five origins in living
surfaces, but only origin 1 (archived sidecar claim) receives an explicit
disposition in its backlog item. The other three origin items remain open
with now-fixed problem statements:

- `2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`
- `2026-09-18-execute-plan-contract-requiredness-wording.md`
- `2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`

(the fourth, `2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md`,
is closed by Task 5's shipped block plus follow-through).

## Suggested direction

When the batch-2 phase-2 squash lands on main, flip each item to
`Status: closed (fixed by batch-2 phase-2)` with a one-line pointer to the
landed change.

Disposition (2026-09-22): the third sibling,
`docs/history/backlog/deferred/2026-09-18-execute-plan-contract-requiredness-wording.md`,
was deferred at the review round cap and its close-as-fixed instruction
lapses: it stays in `deferred/` untouched. The two open siblings were closed
as fixed by batch-2 phase-2 squash 7334dd25 (2026-09-20) and moved under
`docs/history/backlog/completed/`.
