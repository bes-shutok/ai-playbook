# Backlog: quota probe --write-flag guard should catch the ValueError class, not only OSError

Status: open
Origin: review r5 CC-R5-1 (execute-plan runtime guardrails; round-cap deferral, zero blocking)
Discovered: 2026-09-12

In `scripts/quota_window_probe.py` `main()`, the `write_flag_if_paused` call is guarded by `except OSError` only, while the adjacent `detect_runtime` guard catches `Exception` (r4). An in-process caller can hit ValueError (embedded NUL path) and lose the JSON report to a traceback. Fix: widen the guard to `(OSError, ValueError)` (or `Exception`, matching detect_runtime) so the report is always printed; shell reachability is nil, hence Low.

Witness: the fail-open suite pins report-always-printed for transports; no witness covers the flag-write guard class.
