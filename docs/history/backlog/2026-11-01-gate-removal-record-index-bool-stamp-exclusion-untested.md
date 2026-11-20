# gate-removal record_index bool-stamp exclusion is untested
Cluster: docs/history/backlog/2026-11-01-gate-removal-formal-residues.md; docs/history/backlog/2026-11-01-gate-removal-multi-record-gate-report-conjunction-test.md; docs/history/backlog/2026-11-01-gate-removal-note-newline-sanitization.md; docs/history/backlog/2026-11-01-gate-removal-resolver-verified-destinations-derivation.md (same-day review family)

Driving force: correctness

The scoped missing-destination hold recognizes a row stamp only when `record_index` is an int (bool excluded), but no test feeds a hand-authored row with `"record_index": true` or a non-int stamp. In a two-record manifest such a row is silently treated as legacy (unattributed note) even at the adjudicated index. Production behavior matches the plan clause (`_append_manifest` only ever writes real ints), so this arises only from hand-authored manifests.

Fix: one authored-manifest test asserting a `record_index: True` row lands in the unattributed note while an int-stamped adjudicated row still holds. Witness: Task 1 Step 1.2b testing-lens review of plan docs/history/plans/2026-11-01-gate-removal-inherited-manifest-rows.md (2026-11-01).
