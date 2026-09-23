# Backlog: done-pending recovery transition — Phase 3 r1 Low findings (F1-F3)

Driving force: reliability (the findings sit on the new `recover-done-pending` transition's evidence boundary: an unvalidated receipt field and a launch-identity anchor that skips the codebase's own group-resolution convention; both are latent-only today but erode the recovery receipt's standing as immutable, validated evidence).

Origin: Phase 3 review round r1 of the 2026-09-24-execute-plan-recover-stuck-done-pending-claims execution (staging doc `docs/reviews/2026-09-24-execute-plan-recover-stuck-done-pending-claims-code-review-r1.md`, gitignored; verdict ready=yes, zero blocking, three Low deferred per the backlog-deferral default).

## F1 — requeue arm records unvalidated backlog_evidence

`scripts/execute_plan_runtime.py`, `recover_done_pending` requeue arm: the optional `backlog_evidence` CLI payload field is recorded into the immutable `done-pending-recovery` receipt without validation, while `runtime-contract.md` documents backlog evidence as riding "for a defer" only. Fix: drop the field on the requeue arm or validate it through the same `_safe_relative_path` + `docs/history/backlog/` gate the defer arm uses.

## F2 — terminal-evidence anchors skip group launch-record resolution

Same method, terminal-evidence identity gate: anchors read only `claim.launch_record` and do not resolve through the claim's group via `_claim_launch_evidence`, so a session-less group-member done-pending claim in a non-active group cannot be recovered by naming the true group launch identity. Latent only (real done-pending tasks carry `session_id`). Fix: route anchor extraction through `_claim_launch_evidence`.

## F3 — informational: bare-string evidence normalization

The implementation accepts a bare evidence string where the contract documents "a non-empty list"; deliberate normalization, record-only. Fold into the same docs touch if F1/F2 work edits the contract's recovery subsection.

## Disposition

Deferred at execution closeout 2026-09-24; not blocking (verdict ready=yes). Fix path: one small change touching `recover_done_pending` anchors/receipt validation plus the contract's `Terminal-worker done-pending recovery` subsection.
