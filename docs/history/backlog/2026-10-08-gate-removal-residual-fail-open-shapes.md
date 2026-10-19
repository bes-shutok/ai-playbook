# gate-removal residual fail-open and wording shapes

- **Cluster:** docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md; docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md; docs/history/plans/completed/2026-10-18-closeout-gate-series-token-infix.md; docs/history/backlog/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md; docs/history/backlog/2026-10-19-gate-removal-manifest-lookup-skips-branch-closeout.md

Driving force: correctness
Date filed: 2026-10-08
Origin: Phase 3 round 3 verification (worktree-removal-migration-gate run), non-blocking residuals

## Finding

Two low residual shapes in the gate-removal subcommand, both verified live:

1. A worktree created INSIDE an external (absolute-facts) reviews home still passes the gate when the plan header cites worktree-subtree paths: the r2 home-inside-worktree guard compares the resolved home against --worktree, and here the worktree is inside the home, not the reverse. Requires three simultaneous misconfigurations (absolute external facts home + worktree inside the home + worktree-subtree citation), none witnessed.
2. Doc surfaces say the extraction region ends at "the first markdown heading"; the code bounds at any #-prefixed line. Error direction is region-narrowing (fail-closed).

## Suggested direction

Extend the operand/home guard to the worktree-inside-home direction when facts resolve absolutely (or refuse an in-home worktree outright); align the doc wording to "#-prefixed line".

## Evidence

- Phase 3 round 3 verification, 2026-10-08, wt-wrmg-exec (live probes both shapes)
