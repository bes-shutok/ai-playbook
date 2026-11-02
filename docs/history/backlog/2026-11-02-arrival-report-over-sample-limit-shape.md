# arrival report above-SAMPLE_LIMIT shape untested at the write-manifest call site

Status: open
Workflow: backlog

Driving force: preservation (reporting channel)

Cluster: docs/history/plans/completed/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md
Cluster: docs/history/backlog/2026-11-02-arrival-arm-per-candidate-oserror-fixture.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-run-marker-epoch-arm-tests-and-assertion-tightening.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-marker-reread-unconfirmed.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-mtime-backdate-ctime-bound.md (sibling arrival-mechanism hardening row)

Every arrival fixture classifies 1-3 candidates, so the >SAMPLE_LIMIT branch of the arrival report line at the write-manifest call site (count header, full-list file under the run's gate-reports home, stderr warning relay) never runs in tests; the shared helper's bounding shape is pinned only via the pre-existing docs-tmp-sweep consumer. Remedy: one fixture classifying more than SAMPLE_LIMIT candidates asserting the full-list file and warning. Origin: Phase 3 r1 testing lens finding (testing#untested-branch, low), execute-plan run 2026-11-02.
