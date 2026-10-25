# Backlog: wrapper-level rc=2 (raised helper) no-catch arm for description-length

Driving force: automation (review r1 residual, description-length-gate-catch-promotion run)

Plan Task 1 requires rc=2 and rc=3 results to refuse without a catch; the wrapper suite covers rc=3 directly (`test_classified_tool_error_refusal_records_no_catch`) but the rc=2 arm (raised gate helper traversing `cmd_commit`) is covered only at the sweep-lib layer. The shell trigger is strictly `rc == 1` and both bracketing arms are mutation-proven, so risk is small. Remedy: a wrapper test pinning `DESCRIPTION_LENGTH_CHECK_SCRIPT` to a non-executable path to force a raised helper, asserting refusal with zero ledger rows.
