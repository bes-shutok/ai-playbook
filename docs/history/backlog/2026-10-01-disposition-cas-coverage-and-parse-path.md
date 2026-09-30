- **Filed:** 2026-10-01
- **Status: done (2026-10-01; executed+landed docs/history/plans/completed/2026-10-01-disposition-cas-coverage-and-parse-path.md, squash main 2faa5c50, exec review r1 ready=yes zero blocking)(docs/history/plans/2026-10-01-disposition-cas-coverage-and-parse-path.md)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving (execute-plan Step 1.2b intermediate review backlogged candidates, disposition-followups run)
- **Class:** fix-class
- **Driving force:** correctness (CAS coverage completeness; single parse path)

# Disposition stamp CAS: untested racing shapes and a divergent parse path

## Problem

Two follow-ups from the disposition stamp CAS:

1. Only the post-check-finalize racing shape has a suite arm. The post-check-adoption refusal and the dispositioned-race idempotent reprint — the other two shapes the CAS handles — are untested; regressions there would land silently.
2. The CAS's fresh payload read parses raw JSON directly, bypassing `_read_manifest_by_run_id`; parse-tolerance semantics could drift between the reader's contract and the CAS's fail-closed refusal.

## Expected behavior

Suite arms for the adoption-refusal and dispositioned-race shapes (same hook-the-read discipline the finalize arm uses), and the CAS re-read routed through (or explicitly anchored to) the reader's parse contract.

## Location

- `scripts/done_sweep_gates_lib.py` (`_cmd_disposition_manifest`, the CAS reads).
- `scripts/test_done_sweep_gates_lib.py` (the race-arm family).
