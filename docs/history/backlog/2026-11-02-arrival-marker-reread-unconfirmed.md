# arrival epoch re-reads the bound marker without re-confirmation

Status: open
Workflow: backlog

Driving force: preservation (safety margin)

Cluster: docs/history/plans/completed/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md
Cluster: docs/history/backlog/2026-11-02-arrival-arm-per-candidate-oserror-fixture.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-report-over-sample-limit-shape.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-run-marker-epoch-arm-tests-and-assertion-tightening.md (sibling arrival-mechanism hardening row)
Cluster: docs/history/backlog/2026-11-02-arrival-mtime-backdate-ctime-bound.md (sibling arrival-mechanism hardening row)

`_run_marker_epoch` re-reads the bound marker with plain read_text after `_run_marker_binding_refusal` validated it earlier in the same invocation, with git subprocesses in between; a concurrent writer swapping the marker in that window can move the epoch and widen the auto-foreign arm. Bounded today (done-lock exclusivity covers legitimate writers; the realistic victim is the already-priced transfer-window false-positive class), so this is hardening, not an observed pass. Remedy: pass the window-parsed, already-confirmed RunMarker epoch into the split, or re-verify the digest token inside the helper; also fixes the mislabeled config-error rendering of a non-UTF-8 marker. Origin: Phase 3 r1 security lens finding (security#arrival-marker-reread-unconfirmed, low), execute-plan run 2026-11-02.
