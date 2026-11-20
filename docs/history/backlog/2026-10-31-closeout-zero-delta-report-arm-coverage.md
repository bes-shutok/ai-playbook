# Pin the zero-delta report's defensive arms with table-driven tests

Driving force: testability
Cluster: docs/history/backlog/2026-10-31-malformed-closeout-baseline-json-refusal.md (the clobber-guard cluster's 2026-11-01 row was deleted at its ad-hoc landing)
Origin: execute-plan Task 1 intermediate review finding T1-05 (run closeout-migrate-zero-delta-silence, 2026-10-31)

`_print_zero_delta_report` in `scripts/worktree_closeout_migrate.py` carries untested defensive arms: (a) `captured_at` present but non-string (e.g. null) takes the unknown arm; only the absent-key variant is tested; (b) the naive-`captured_at`-reads-as-UTC arm (capture never writes one) is untested; (c) the `baseline_path.resolve()` and per-file `resolve()` OSError exclusion fallbacks are untested. Pin them with table-driven tests so latent branch drift is caught.
