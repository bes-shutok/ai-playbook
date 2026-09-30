# Backlog: done pre-docs docs-tmp-sweep removes the run's execute-plan session dir before Step 2's worktree migration

Cluster: docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md
Cluster: docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md
Cluster: docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md
Cluster: docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md
Cluster: docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md
Cluster: docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md
Cluster: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md
Cluster: docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md


Driving force: reliability

Witnessed 2026-09-29 (p79 execution closeout): the done skill's ordering is pre-docs sweep gates BEFORE Step 2 (which owns the ad-hoc-worktree migration of review staging docs and session logs to the main checkout). When the run's plan is already archived at that point, the docs-tmp-sweep gate deletes the whole `docs/tmp/execute-plan/<plan-slug>/` directory (Plan Lifecycle cleanup: owning plan archived), destroying the closeout baseline JSON, agent logs, and any unmigrated run artifacts before the migration step runs. The closeout-baseline capture then no longer matches disk and `worktree_closeout_migrate.py migrate` cannot run its baseline diff.

Candidate remedies (pick one in the fix): (a) exempt the current run's `docs/tmp/execute-plan/<plan-slug>/` from the sweep when a linked-worktree done session is still open (session-window witness), mirroring the ACTIVE-execute-plan exemption; (b) move the worktree migration ahead of the sweep gates; (c) have the sweep keep the directory when a closeout-baseline.json for it exists on disk. Also note the execute-plan Worktree-first standard's transfer-out step (lifecycle step 5) already mandates migration before worktree removal, so the skill-level contract exists; the gate just runs first and eats the inputs.
