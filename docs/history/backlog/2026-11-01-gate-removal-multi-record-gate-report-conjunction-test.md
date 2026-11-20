# gate-removal expired-gate-report attribution conjunction is unwitnessed in multi-record manifests
Cluster: docs/history/backlog/2026-11-01-gate-removal-formal-residues.md; docs/history/backlog/2026-11-01-gate-removal-note-newline-sanitization.md; docs/history/backlog/2026-11-01-gate-removal-record-index-bool-stamp-exclusion-untested.md; docs/history/backlog/2026-11-01-gate-removal-resolver-verified-destinations-derivation.md (same-day review family)

Driving force: correctness

The expired-gate-report arm's classification conjunction (`attributed and _is_done_session_gate_report(destination)`) is only exercised in the single-record shape, where `attributed` is trivially true. Mutation-verified: detaching the classification from attribution leaves all attribution + gate-report tests green, so a regression that misfiles a prior-run gate report into the expired note (or shifts note counts) is unwitnessed. Both notes are report-only, so the consequence is informational mislabeling.

Fix: one two-record test whose run-1 artifact is a `gate-reports/run-*.txt` shape missing under the target, asserting the unattributed note text and counts (`attributed: 0; unattributed: 1`) and `assertNotIn` of the expired note; plus a stamped adjudicated gate-report row asserting the expired note. Witness: Phase 3 r1 testing lens (2026-11-01), mutation run.
