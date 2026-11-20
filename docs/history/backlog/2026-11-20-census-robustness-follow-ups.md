# Census robustness follow-ups (post-fire arm code review r1)

Cluster: docs/history/backlog/2026-11-20-census-simplification-and-docs-precision.md; docs/history/backlog/2026-11-20-census-test-pin-follow-ups.md
Status: open
Priority: low
Class: defect-hardening
Origin class: review-finding
Driving force: execute-plan Phase 3 code review r1 (record .ai-playbook/reviews/2026-11-20-post-fire-verification-arm-zero-executions-code-review-r1.md, verdict yes, zero blocking) staged three Low robustness findings on the new census surface; all non-blocking, deferred to this row.

## Items
- F1: a store row with NULL automation_id crashes census_members (TypeError in the member sort) instead of the exit-0 unknown verdict; live column is NOT NULL, defensive gap only (scripts/maintenance_fire_outcomes.py:572). Code-review r2 extends this item with sibling crash sites: int(scheduled_at) in the grouping loop (line 566-568) and a valid-JSON non-object --state surface (state.get("notes") at 441-449, probe-verified AttributeError).
- F2: a content-corrupted but readable index yields all-absent correction states and unwired true with eligible members present (scripts/maintenance_fire_outcomes.py:452-466); the Terms' never-a-false-unwired intent wants a content-degradation unknown.
- F3: correction-trace startswith prefix matching can read a digit-superset key's line as the member's own trace (scripts/maintenance_fire_outcomes.py:596-598); inherited idiom from the frozen read_correction, direction safe.

## Acceptance
- Each item lands with a census cell pinning the corrected behavior; the pinned -k census and whole-file suites stay green.
