# Backlog: dispatch admission candidate-side conservatism

Status: covered-pending-execution (docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md)
Priority: low
Cluster: parallel-execution-landing-serialization-blockers
Cluster: docs/history/backlog/2026-11-05-dispatch-admission-outstanding-manifest-recovery.md
Cluster: docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md
Driving force: correctness

Origin: Task 1 intermediate review (Step 1.2b, testing lens), off-plan observation on `scripts/dispatch_admission.py`.

A `--candidate-manifest` whose owned-path fields are all empty is admitted vacuously (exit 0 pass against a non-empty outstanding run), while the outstanding side treats an empty recorded set conservatively (treat as intersecting). The `--plan` derivation arm fails closed on an empty derivation, but the manifest arm does not. The plan's degenerate criteria name only outstanding-run cases, so the asymmetry shipped intentionally scoped; a symmetric conservative arm for the candidate side (or an explicit rationale for the asymmetry) should be considered once the admission check has a true catch or a false-positive witness.

Second witness (Step 1.4b design review, finding A2): `owned_paths_from_manifest` also silently drops non-string list items and non-list fields, so a partially foreign-shaped manifest yields a disjoint subset and exits 0 pass on partially parsed evidence; the outcome contract reserves partial-evidence uncertainty for exit 2 `indeterminate`. Fold candidate-side strictness (partial parse -> indeterminate, or a named rationale for the lenient parse) together with the empty-set arm above.
