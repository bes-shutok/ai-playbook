# Clocked-order reconcile resurrects a trimmed terminal row for a discharged+resolved order

Phase 3 residual from 2026-11-11-clocked-order-payload-session-execution (fix commit 7be63288f, re-review round 2 clean): the reconcile restore arm gates on `carrier.armed is True`, but discharge never disarms the carrier, so a keep-last-20-trimmed terminal-outcome child row of a discharged order whose recovery already resolved is rebuilt on every due scan (trim→resurrect churn; bounded, no cap/lane misbehavior).

Closing it deliberately requires either re-pinning `test_stale_step6_child_removed_or_reset_restored_from_order_record` to an unresolved discharge or keying the restore gate on the recorded disposition instead of carrier armed-ness. Operator decision; recorded non-blocking.
