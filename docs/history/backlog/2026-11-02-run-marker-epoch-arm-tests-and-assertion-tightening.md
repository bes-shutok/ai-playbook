# _run_marker_epoch unreadable and unparseable arms untested; epoch assertion and docstring precision

Status: open
Workflow: backlog

Driving force: correctness (pin precision)

Cluster: docs/history/plans/completed/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md
Cluster: docs/history/backlog/2026-11-02-arrival-arm-per-candidate-oserror-fixture.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-report-over-sample-limit-shape.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-marker-reread-unconfirmed.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-mtime-backdate-ctime-bound.md (sibling arrival-mechanism hardening row)

Three polish gaps from the Phase 3 r1 panel: the helper's unreadable-file arm (read OSError) and unparseable-token arm have no direct test (the latter is reachable only under a TOCTOU marker mutation between binding and arrival read); the nan-arm assertion (`"epoch" in err.lower()`) cannot distinguish the non-finite refusal from an unparseable one (tighten to the named reason token); the plan's Terms define the epoch as "the integer Unix timestamp" while the parser accepts any finite float token (vocabulary looseness only; the writer emits `date -u +%s`). Origin: Phase 3 r1 testing lens findings (info), execute-plan run 2026-11-02.
