# Backlog: verify-digest recomputes over current HEAD and staleness-refuses records after additive post-landing commits

- **Filed:** 2026-10-27, learn Step 1.9 over the self-heal-before-workflow-stop execute-plan session
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** witnessed defect (machinery contract disagreement)
- **Class:** fix-class
- **Cluster:** docs/history/backlog/2026-10-22-producer-review-findings-followups.md
- **Skill/step:** `scripts/review_record_selection.py verify-digest` (`--expect-head` operand semantics beside the recompute leg)

## Observed vs expected

Observed: after a peer strand-drain landed the reviewed delta and the owning session then committed three record-capture-only backlog rows on the base branch, `verify-digest --base <base> --expect-head <landing>` recomputed the reviewed-scope digest over `base...<current HEAD>` (including the additive backlog commit), got a different digest than the record's `source_digest`, and refused the record as stale ("run a fresh round on the recomputed digest or re-bind it through the staging validator's corrections arm") even though zero plan-scope bytes changed and the record named the exact landing head. The session recovered through a manual corrections re-bind: verifying the post-landing delta touched only record-capture files, then updating the record's digest line and the sidecar.

Expected: either the recompute leg honors `--expect-head` as the recompute endpoint when passed (with current HEAD only as the default), or the refusal distinguishes an additive no-plan-scope-change delta (auto re-bindable with a recorded delta-path proof) from a genuine scope change, so a record-capture commit never forces a manual re-bind or a spurious fresh round.

## Evidence

- Session 2026-10-27: verify-digest over the r1 record refused with sidecar digest vs "recomputed reviewed-scope digest ... over c63064b52...69163788e"; the delta `ea5e3c6f4..69163788e` was exactly the three backlog capture files; after re-binding to the recomputed digest the same invocation returned `outcome: fresh`.
- The refusal text itself routes to the corrections arm, so the behavior is workable but every additive commit on the base branch between landing and verification re-prices the record.

## Suggested investigation

Decide the intended endpoint semantics (operand-honoring recompute vs current-HEAD-always), then either change the recompute endpoint or add a no-plan-scope-delta auto re-bind arm with its delta-path witness recorded; keep the fail-closed refusal for genuine scope drift.

## Source

learn Step 1.9, execute-plan session self-heal-before-workflow-stop (r1 record re-bind witnessed 2026-10-27).
