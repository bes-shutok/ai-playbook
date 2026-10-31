# Untrack ignore-scan robustness residuals

Driving force: code-quality

Cluster: docs/history/backlog/2026-10-31-untrack-ignore-scan-robustness-residuals.md, docs/history/backlog/2026-10-31-untrack-wrapper-test-coverage-residuals.md, docs/history/backlog/2026-10-31-untrack-minor-usage-and-expectedref-residuals.md

Source: plan docs/history/plans/2026-10-27-done-run-untrack-ignored-path.md Phase 3 code-review r1 non-blocking findings (record docs/tmp/execute-plan/done-run-untrack-ignored-path/phase3-code-review.log.md).

- Both new ignore rescans (done_run.sh untrack preflight changed-blob scan and captured-tree 1c scan) fail open for dash-prefixed path names (`git check-ignore` exits 129 on `-dash.conf`-style operands, read as "not ignored") and for C-quoted names under default `core.quotePath` (diff listings emit quoted names check-ignore does not resolve). A changed tracked-ignored blob under such an exotic name, declared via `--stage` beside `--untrack`, can land. Remedy shape: `-z` output plus `--` separator plus treating rc>1 as refusal.
- A directory-shaped `--untrack` operand passes all four preflight checks; a `[ -f ]` check would match the exact-file contract (no unsafe landing reachable).
- The captured-tree 1c scan's HEAD baseline is read before the commit parent is captured, so a concurrent backward HEAD move in that microsecond window can land an added ignored blob the scan misses (pre-existing structural property; capture head identity once before 1c).
