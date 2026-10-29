# Branch skip report identity and line integrity

- **Filed:** 2026-10-29, plan review r3 certification residuals
- **Status:** open
- **Workflow:** backlog
- **Priority:** low

## Problem

The pre-gate skip report can carry an incorrect branch OID or forged summary-looking lines. `_capture_branch_oid` resolves a short branch name with `git rev-parse --verify <name>` (`scripts/worktree_closeout_migrate.py`, `_capture_branch_oid`); if the branch ref disappears after enumeration while a same-named tag remains, the tag OID can be reported as the branch OID. Separately, `_live_session_evidence` inserts the filesystem-controlled claim filename into the skip reason without escaping (`scripts/worktree_closeout_migrate.py`, `_live_session_evidence`). A fresh claim file may have a newline in its filename, so forwarding that reason into `branch-report` and `done_run.sh`'s setup summary can create forged `remove:` or `OUTCOME:`-looking lines. The reviewer reproduced both cases.

## Exact location

- `scripts/worktree_closeout_migrate.py`, `_capture_branch_oid` (currently around lines 2504-2514): short-name ref resolution.
- `scripts/worktree_closeout_migrate.py`, `_live_session_evidence` (currently around lines 3095-3104): unescaped claim filename in the reason.
- `scripts/worktree_closeout_migrate.py`, `_sweep_branch_report_line`: renders branch and reasons into one line.
- `scripts/done_run.sh`, `cmd_setup` residue-sweep summary: forwards `branch-report:` lines.

## Suggested direction

Resolve only `refs/heads/<branch>` and report `unknown` when that exact ref is unavailable. Escape control characters in branch names and reason fields before emitting `branch-report` lines, and add focused regressions showing a disappearing branch ref cannot resolve through a same-named tag and a newline-bearing claim filename remains one non-spoofable output line. Preserve skip, fail-open, and removal-authority behavior.

## Why not fixed now

Both are valid, nonblocking Medium findings from the certification review. The reviewed plan's final full-panel round is already in progress; widening Task 2 now would require another implementation-plan review round beyond its declared three-round review budget. Preserve these findings for a follow-up plan rather than silently expanding the certified scope.

Driving force: security (primary; untrusted local names must not forge summary lines), reliability (secondary; branch identity reports must name the branch ref they observed).

Source reference: `.ai-playbook/reviews/2026-10-29-plan-review-gate-removal-task2-review-residues-pe374eb69-r3.md`, certification overflow findings `security#race-condition` and `security#log-injection`; capture hygiene: `scan-public-hygiene --files` pass.

Class: fence-class (a branch report can state a tag OID as the branch OID or contain forged summary-looking records; the follow-up corrects the wrong result and prevents output spoofing).

Dedup probe: searched open backlog filenames and Problem bodies for `same-named tag`, `branch OID`, `branch-report`, `claim filename`, and `log injection`. The nearest item is `docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md`, which records an earlier same-named-tag shadow at gate OID capture; that issue was downstream-fail-safe and did not cover pre-gate skip reporting or newline-based summary spoofing. Distinct follow-up, no merge.

Origin class: self-serving
