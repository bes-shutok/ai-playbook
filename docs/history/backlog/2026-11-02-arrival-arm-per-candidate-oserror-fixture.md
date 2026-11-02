# arrival arm per-candidate OSError classification lacks a TOCTOU fixture

Status: open
Workflow: backlog

Driving force: preservation (fail-closed regression net)

Cluster: docs/history/plans/completed/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md (the arrival arm this test gap guards)
Cluster: docs/history/backlog/2026-11-02-arrival-report-over-sample-limit-shape.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-run-marker-epoch-arm-tests-and-assertion-tightening.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-marker-reread-unconfirmed.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-mtime-backdate-ctime-bound.md (sibling arrival-mechanism hardening row)

`_foreign_by_default_split`'s arrival arm refuses a candidate whose `stat()` fails between enumeration and classification (done_sweep_gates_lib.py, `except OSError: refused.append`). No fixture exercises that arm: a regression that silently classifies on stat failure would ship uncaught. Remedy: a TOCTOU fixture unlinking a candidate before the write call, asserting refusal. Origin: Phase 3 r1 testing lens finding (testing#untested-branch, low), execute-plan run 2026-11-02.
