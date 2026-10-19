# gate-removal --help prints a doubled subcommand token

- **Cluster:** docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md; docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md; docs/history/plans/completed/2026-10-18-closeout-gate-series-token-infix.md; docs/history/backlog/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md; docs/history/backlog/2026-10-19-gate-removal-manifest-lookup-skips-branch-closeout.md

Driving force: quality
Date filed: 2026-10-08
Origin: Task 2 intermediate review (worktree-removal-migration-gate) backlog capture

## Finding

`python3 scripts/worktree_closeout_migrate.py gate-removal --help` prints `usage: worktree_closeout_migrate.py gate-removal gate-removal`: the standalone parser's prog string already contains the subcommand name and the argparse routing appends it again (scripts/worktree_closeout_migrate.py, build_gate_removal_parser, the `prog=` argument). Cosmetic usage-text typo only; the prescribed invocation runs correctly.

## Suggested direction

Fix the doubled token by deleting the redundant subparser dispatch layer rather than trimming the prog string: `main()` already routes the `gate-removal` tokens to the standalone parser before the legacy parser, so that inner `add_subparsers` hop is what makes argparse append the subcommand a second time. Rebuild `build_gate_removal_parser` as one flat parser (keep `prog="worktree_closeout_migrate.py gate-removal"`, register the gate arguments directly on it, `set_defaults(func=cmd_gate_removal)`); one dispatch suffices, and the flat parser keeps the usage-override class (`_GateRemovalUsageParser.error` still exits 3 with the final `OUTCOME: tool_error` line). Add a help-text assertion to the suite pinning `usage: worktree_closeout_migrate.py gate-removal` with a single trailing token.

## Evidence

- Task 2 review pass, 2026-10-08, wt-wrmg-exec
