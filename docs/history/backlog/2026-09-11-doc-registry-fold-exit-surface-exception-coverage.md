# Doc-registry fold plan: pre-subcommand unknown-flag exit-2 path has no pinning fixture

Status: open
Workflow: backlog
Source: docs/reviews/2026-09-11-plan-review-doc-registry-freeze-move-licensing-fold-r7.md (round 7, finding F1, Low, non-blocking)

## Problem

`docs/plans/2026-09-09-doc-registry-freeze-move-licensing-fold.md` Task 2 widens the selftest net with seven CLI characterization fixtures, and its coverage exception names only the pre-subcommand `--stdin` paths as covered by the declared fail-closed delta and argparse-native rejection. The pre-subcommand unknown-flag position (for example `--bogus validate`) also exits 2 today (the hand-rolled pre-loop unknown-flag branch) and post-rewrite (argparse-native top-level rejection), but it has no pinning fixture and is not named in that exception sentence.

## Suggested fix

Either extend the coverage-exception sentence in the Gist and the Task 2 fixture bullet to name the pre-subcommand unknown-flag path alongside the `--stdin` paths, or add an eighth characterization fixture (given `run(["--bogus", "validate"])`, expects exit 2 with the `usage` substring) and update the count arithmetic (108 to 109) everywhere the plan states it.

## Why not fixed now

Deferred at the r7 closing round of the plan-review loop: the exit gate was already satisfied (ready=yes, zero unresolved blocking findings), the path is fail-closed in every implementation shape the plan admits, and folding it would force an eighth certification round for optional hardening (churn-control default: the regenerating exit-surface enumeration family is backlog-by-default).
