# Backlog: readiness gate mixed indeterminate-plus-failure exit-2 flip has no mixed-input witness

Status: open
Priority: medium
Class: fix-class
Origin class: phase3-testing-fidelity residual (2026-11-06 exec r1, certification-gates-full-violation-reporting run)
Cluster: docs/history/backlog/2026-11-06-staging-skip-note-scope-caller-side-consumers.md (same exec-r1 residual family)

Driving force: correctness (primary), token-usage (secondary)

Concern: the plan's one deliberate exit-code flip (mixed indeterminate-plus-failure input moves exit 1 → exit 2) is re-ordered correctly on the branch (indeterminate checked before deterministic errors; witnessed empirically by the r1 panel: parent rc=1 vs branch rc=2 for unresolvable seal + invalid reachability), but `test_graded_indeterminate_names_where_and_exits_2` (test_plan_readiness.py:4391) uses a fixture whose deterministic violation sits after the indeterminate return on both implementations, so the witness pins nothing about the flip and a reordering regression back to exit 1 would pass every pinned suite.

Direction: add a sibling fixture combining the unresolvable-seal indeterminate with an independent shared-gate error (e.g. malformed stats sidecar), asserting rc==2, the indeterminate prefix at position 0, exactly one indeterminate marker, and no schema-family text in the reason; this also makes the plan line's RED claim true for the exclusivity witness.

Evidence: 2026-11-06 r1 testing-fidelity lens, certification-gates-full-violation-reporting worktree tip f8fa77eaf+.
