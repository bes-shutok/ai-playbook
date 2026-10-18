# corrections-graded freshness unusable post-squash

- date filed: 2026-10-07
- Priority: high
- Class: real
- Origin class: self-serving
- Status: open
- Cluster: docs/history/backlog/2026-10-07-archived-plan-review-records-missing.md

## Finding

The review-staging corrections-graded stale arm (validate_review_staging.py, the review-cert-graded-binding plan Task 5) requires a resolvable seal entry in `docs/history/review-certs/<artifact-slug>.md` whose round-start and round-close commits are ancestors of HEAD (corrections_record.py `verify_corrections` anchor leg), and whose text parses in the `## round N` / `key: value` block shape (`parse_seal`). Both requirements are unsatisfiable on this corpus today:

1. Every committed seal file uses the legacy prose one-line shape (`r4 | artifact ...`), which `parse_seal` reads as zero entries; the block-shape writer (`append_seal_entry`) exists only on the test ScratchRepo fixture.
2. Seal anchors name the authoring branch tip, which every squash landing orphans (`merge-base --is-ancestor` false), so even a migrated entry refuses.

Witness: executing plan 2026-10-07-review-round-cap-operator-gate (landed 10fb73bd), the post-execution box-flip delta classified fully exempt by `plan_delta_classifier.py` could not ride the corrections chain: declared-row run returned `readiness indeterminate: anchor leg refused` (legacy seal shape); the run fell back to the pre-flip certification pass plus the exempt-class evidence recorded in the exec-review record, the same shape as the done-readiness execution before it.

## Why it matters

The graded freshness machinery is fail-closed dead code on real landings: any post-review plan delta (the routine box-flip) forces either the legacy stale failure or an indeterminate refusal, so executions systematically bypass the graded path and rely on the older certify-then-flip convention.

## Fix shape

One plan, two tasks: Task 1 teaches `parse_seal` to read the legacy prose entry shape (or migrates committed seals to the block shape with a writer CLI), keeping the anchor and integrity legs unchanged; Task 2 widens the anchor leg's ancestry check to accept a seal entry whose commits are unorphanded via the landing squash (for example resolving the sealed bytes through the landed squash commit's tree or an explicit `landed_as` witness field), with fixture coverage for both the post-squash and pre-landing arms.

## Witness (2026-10-08, plan-directory-shape execution)

Three facts from a run that certified through a fresh round:

1. The block shape parses on the real corpus: the plan-directory-shape seal was restructured by hand into the bare `## round N` / `key: value` field form (narrative bullets moved above the round header) and `parse_seal` read it, so the Task 1 migration arm is mechanically feasible; the missing piece remains the writer CLI.
2. A third refusal class the finding did not list: the anti-tamper legs refuse post-hoc edits to an already-committed seal. A corrections-row append to a landed round 3 entry failed as "seal entry's introducing commit postdates the correction hops" (the `entry_introduce_commit` append-only witness plus the introduce-before-hop-evidence date ordering) even with the block shape and a touching evidence commit - by design: a landed seal is immutable, so a corrections row can never be appended to it.
3. The sanctioned post-landing correction route is a fresh round, not a seal edit: the run certified via a new round (verification probe over the folded bytes) whose machine-seal entry anchored on a witness commit whose blob equals the current artifact bytes. Requirement 2 still governs post-squash chain reads: the new round's anchors name branch commits the landing squash orphans, so Task 2's unorphaning (or a `landed_as` witness) remains the open need.

## Witness (2026-10-14, authoring-side certification seal)

1. The anchor trap now bites the authoring side too: an authoring session's r2 certification seal wrote both anchor fields on the pre-landing authoring branch tip; the squash landing orphaned them and the post-landing readiness pass refused twice ("round-close/round-start commit is not an ancestor of HEAD").
2. Authoring-time mitigation witnessed working: seal after the landing and anchor both fields on the landing commit itself - the landing carries the certified artifact bytes, so the digest leg passes, and the start-never-postdates-close ordering leg holds trivially. This unblocks fresh certifications but leaves Requirement 2 open for post-landing corrections chains; Task 2's unorphaning remains the fix of record.
3. Priority re-affirmed high at this append: the same refusal class has now cost a mid-run repair in two independent executions (exec-side 2026-10-08, authoring-side 2026-10-14), and the review-plan skill's round-close seal duty (its SKILL.md round-close seal paragraph) does not warn the author that pre-landing tips die in the squash.
