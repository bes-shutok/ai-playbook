# Backlog: tracked-ignored warning fragments on Unicode line-separator path names

- **Filed:** 2026-10-24, Phase 3 review round r2 of plan ignored-audit-home-tracked-index-fence
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** correctness
- **Skill/step:** `scripts/done_sweep_gates_lib.py` (`_tracked_ignored_paths` splitlines + `_escape_control_chars`) and `scripts/land_squash.sh` probe tracked-ignored pass stdout (the r3 risk lens witnessed the same raw-separator rendering reach the probe's warning channel after the quotePath pin moved)
- **Cluster:** docs/history/plans/2026-10-23-ignored-audit-home-tracked-index-fence.md (the tracked-sibling report arm this row bounds); sibling row 2026-10-24-probe-branch-only-ignore-rule-gap.md (the probe arm's rule-source limit)

## Problem

Under the lib-wide `core.quotePath=false` pin, a tracked-ignored path whose name contains a Unicode line-separator character (U+2028, U+2029, or NEL U+0085) arrives raw, and Python's `splitlines()` fragments the row at those characters before `_escape_control_chars` runs (it covers only \n \r \v \f), so one path renders as two warning-prefixed lines, neither naming the real path. Witnessed by the r2 risk lens, 2026-10-24.

Bounding facts: no injection is possible (the `warning:` prefix is unconditional in the f-string) and the gate verdict never moves (the rows stay on the warnings channel); the miss is a mis-rendered human report.

## Outcome sought

Either a NUL-safe reader (`ls-files -z` consumed by a NUL-splitting reader, which makes every byte sequence except NUL representable in one row), or `quotePath=true` on this one arm plus octal decoding in `_unquote_porcelain_path` (quoting turns the separators into `\342\200\250`-style escapes that survive splitlines and decode back), plus a direct unit test for `_escape_control_chars` covering the separator class.

## Rejected alternatives

- Leave unhandled with a comment: rejected, a mis-render with no test is exactly the silent-drift class this corpus records instead of comments.
- Widen `_escape_control_chars` to cover U+2028/U+2029/U+0085: rejected, it does nothing about the `splitlines()` ordering that already dropped the fragment pairing before the escape runs.
