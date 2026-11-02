# foreign-by-arrival boundary trusts mtime against deliberate backdating

Status: open
Workflow: backlog

Driving force: preservation (hardening)

Cluster: docs/history/plans/completed/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md
Cluster: docs/history/backlog/2026-11-02-arrival-arm-per-candidate-oserror-fixture.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-report-over-sample-limit-shape.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-run-marker-epoch-arm-tests-and-assertion-tightening.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-marker-reread-unconfirmed.md (sibling arrival-mechanism hardening row)

The arrival boundary is mtime-only: a candidate staged with a backdated mtime (`touch -t`, `rsync -a` from an older source) classifies foreign-by-arrival instead of refusing. No git primitive backdates, and the gates model honest-but-fallible agents, so this is a hardening item, not an observed pass. Remedy if ever wanted: additionally require st_ctime strictly older than the epoch (a utime backdate refreshes ctime; legitimately transferred docs keep ctime < epoch, keeping liveness). Origin: Phase 3 r1 security lens finding (security#mtime-backdate-dodge, low), execute-plan run 2026-11-02.
