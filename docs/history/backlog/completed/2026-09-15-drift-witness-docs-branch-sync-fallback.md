# Backlog: drift-witness docs-branch sync-commit fallback for gitignored corpora

**Captured:** 2026-09-15 (review-loop r1 of the maintenance dispatch-ladder span; contract-docs, testing, and correctness lenses converged on the closure of docs/history/backlog/completed/2026-09-14-drift-witness-gitignored-corpus-fallback.md)
**Status:** done
Done by: docs/plans/completed/2026-09-16-learn-done-workflow-updates.md (executed 2026-09-18)
**Priority:** medium
**Origin:** contract#drift-witness-closure-overstates (three-lens echo; staged finding F13, non-blocking, backlogged per the capture rule)

## Finding

The closed item (2026-09-14 drift-witness-gitignored-corpus-fallback) records Status done via "done SKILL items 4a/6 now carry the lesson-scope-audit body line on the drift path; verified on main dded309c". At HEAD, done SKILL 4a and item 6 bind the witness to the commit message body of the Step 3 commit that stages the corpus change, and done Step 3 item 4 routes gitignored corpora to the docs branch only, so no Step 3 commit exists on the gitignored path; no docs-branch sync-commit body line exists anywhere in done or docs-branch SKILL. The item's own candidate direction (carry the line in the docs-branch sync commit message body instead) is therefore unimplemented, while the item sits under completed/ outside the maintenance survey's open-item surface.

## Suggested fix

Either implement the fallback in the done skill's docs-branch step (the docs-branch sync commit message body carries the lesson-scope-audit witness line when the changed corpus is gitignored), or amend the closed item's Status to record partial coverage with this residual explicitly open. This item intentionally does not edit the peer-authored closed document; the fix decides which side moves.

## Verified feasibility facts

- done SKILL 4a and 6 carry the witness on the working-branch Step 3 commit only (verified at HEAD by the contract lens with line references).
- The docs-branch skill owns the sync-commit message; adding a conditional body line there is the natural implementation site.
- The closed item is peer-authored; this loop's capture rule (valid findings become durable items, not forced edits of peer state) produced this item instead of an in-place rewrite.

## Open decisions for the plan author

- Implement the docs-branch body line versus annotate the closed item (which side of the closure moves).
- Whether the witness line format for docs-branch sync commits should match the Step 3 body line byte-for-byte so the audit-note scan can grep one pattern.
