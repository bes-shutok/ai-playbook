# Backlog: bounded-read and reclaim-fence pin hardening (task 5 residuals)

- **Status:** open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; pin hardening + portability note (microsecond-window adversary). Revive on a regression wedges the suite, or a Windows port happens, or a project-priority-profile change.)
- **Origin:** execute-plan task 5 intermediate review (Step 1.2b, testing + correctness lenses, 2026-09-20)

## Findings

1. `test_read_plan_bounded_refuses_fifo_without_open` fails-by-hang (no per-test timeout) on a regression to a blocking read; the plan specified exactly this pin shape. Add a per-test timeout or a watchdog so the regression fails cleanly instead of wedging the suite.
2. The finished-state reclaim arms (`complete`/`terminal`) reuse `explicit-abort` as `reason_code` and the witnesses do not pin it; the distinguishing evidence names the state. Either pin the current reuse explicitly or introduce a dedicated reason code, and pin whichever is chosen.
3. Windows portability note: `os.O_NONBLOCK`/`os.O_CLOEXEC` raise `AttributeError` at call time on Windows; the repo is posix-scoped today. Record only, or guard if a port ever happens.

## Driving force

A blocking-read regression would wedge the whole unittest run instead of failing one witness, and an unpinned `reason_code` on the finished-state reclaim arms lets the envelope vocabulary drift silently; both weaken exactly the fail-closed guarantees Task 5 landed.
