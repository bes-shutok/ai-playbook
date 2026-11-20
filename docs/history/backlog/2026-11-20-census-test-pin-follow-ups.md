# Census test-pin follow-ups (post-fire arm code review r1)

Cluster: docs/history/backlog/2026-11-20-census-robustness-follow-ups.md; docs/history/backlog/2026-11-20-census-simplification-and-docs-precision.md
Status: open
Priority: low
Class: test-coverage
Origin class: review-finding
Driving force: execute-plan Phase 3 code review r1 staged two Low test-gap findings on the census suite.

## Items
- F4: no census cell builds two automation_runs rows sharing one (automation_id, scheduled_at) key, so unknown_reason ambiguous and matched_run_ids are unpinned; a regression collapsing the leg passes green.
- F5a: the session_id-or-UNKNOWN mapping and dispatch_status passthrough are asserted in no census cell.
- r2 additions: unknown_reason precedence combo (aged-out record + nonterminal outcome) unpinned (swapping the elif arms passes); unwired trace-scope reading (all-members vs eligible-only) unpinned; window boundary inclusivity (>= vs >) unpinned.

## Acceptance
- Cells land under the pinned -k census naming contract; suites stay green.
