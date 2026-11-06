# Backlog: invocation-telemetry finalize stdout pins drifted behind the marking-honesty emission

- Status: open
- Priority: P2
- Class: fix-class
- Origin-class: baseline-red (5 failing tests on main, first observed 2026-11-06 during the certification-gates takeover run)

Driving force: correctness (primary), efficiency (secondary)

Concern: the landing `998d1dade` (done-finalize-resume-marking-honesty, 2026-11-06) added the `done_run finalize: finalization: run_id=... marking=...` line to the finalize exit path, but the five pinned stdout/stderr literals in `scripts/test_invocation_telemetry.py` (`PINNED_NO_LEDGER_STDOUT` and siblings) were not re-captured, so `test_finalize_*` fails 5/24 on main (witnessed 2026-11-06T10:40Z, primary checkout and the certification-gates worktree alike); the landing's GREEN evidence named the wrapper suite and sweep gates, not this pin battery.

Direction: re-capture the five finalize-path pins at a fresh main tip (preserving the pin provenance-header discipline per `docs/history/backlog/2026-10-29-telemetry-pin-provenance-headers.md`), keep the finalization line as a pinned byte, and record in the test header which landing the line belongs to; regreen the suite on main.

Evidence:
- 2026-11-06T10:40Z: `python3 -m pytest scripts/test_invocation_telemetry.py -q` on main 27edda0f0: 5 failed, 19 passed; identical set in the certification-gates worktree before any of its changes (branch clean baseline).
