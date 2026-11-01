# Backlog: consultative prune-audit holds 23 standing REMOVED-WITHOUT-WITNESS flags since the receipt convention landed, with no owning row or repair route

- **Filed:** 2026-11-01, learn Step 1.9 over the 11:00 auth carrier's scheduler turn
- **Status:** covered (docs/history/plans/2026-11-01-prune-audit-standing-flags-unowned-accumulation.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** the landing prune-audit leg (`scripts/check_prompt_log_origins.py --prune-audit`), the receipt-convention surfaces (the EXEC-PROMPTS-PRUNE receipt, the in-log receipt ledger line, the in-commit receipt)
- **Cluster:** docs/history/backlog/2026-10-29-prune-audit-same-branch-receipt-rewrite-flag.md (same checker, distinct class: that row owns the net-add rewrite false positive, this row owns standing flags and their unowned accumulation)
- **Cluster:** docs/history/backlog/2026-10-28-landing-gate-prune-audit-wiring.md (covered; the landing leg this row's triage question re-examines)
- **Skill/step:** `scripts/check_prompt_log_origins.py --prune-audit`, the consultative survey arm's report-only recording surface
- **Class:** diagnostic-class
- **Origin class:** session witness (scheduler turn, 2026-11-01)

## Problem

The consultative prune-audit, run at the 2026-11-01 tip against the receipt convention's landing commit (3c7917dad, 2026-10-28), reports 23 standing flags across 43 removals in 139 log-touching commits (17 removals witnessed by log ledger). Three subclasses:

- **A, covered-row deletions with no receipt on any surface (4 flags):** done-closeout-gates-trio (eebc930c0), self-heal-caller-map-recoverability-drift-and-review-question-scope (c5c31e9d6), hygiene-scanner-frozen-arm-and-report-residuals (830119aff), untrack-operand-residual-trio (66255a68d). Each landing deleted its learn-produced origin row per the covered-row rule but wrote neither an EXEC-PROMPTS-PRUNE receipt nor the in-log ledger line the checker parses (the lesson 44 duty, skipped entirely rather than mis-surfaced).
- **B, ledger rewrites that ate existing receipt lines (18 flags):** 30fc2342b removed sixteen prior receipt lines in one commit (its first flag, drain-veto-destination-resolution-arm, was recorded report-only in the scheduler state on 2026-10-31 and never routed); a5024b396 removed two more.
- **C, receipt written but not resolving (1 flag):** plan-prompts-stub-rewrite-origin at 312c53122, whose commit message claims "receipt ledger line added" while the checker still flags the removal; the line's surface or its witness token does not resolve.

The routing gap (lesson 349): survey turns re-recorded subsets report-only (2026-10-31 13:04 one flag; 2026-11-01 10:17 two flags; the 2026-11-01 11:00 turn's record five), and no backlog row owned the class, so nothing routed the flags to repair and every turn re-paid the derivation.

## Triage question

Pick a per-subclass combination before any checker or landing-procedure edit: (1) repair the standing receipts in the lesson 44 parser-derived grammar and re-run the audit to green; (2) admit a covered-row-deletion excusal class to the checker (the origins side already admits served covered-row deletions); (3) widen or re-window the landing leg so a receipt-less covered-row deletion is caught at landing time; (4) a write-once rule for receipt-ledger lines (a later commit may not remove a receipt line without its own receipt). Subclass C needs its own diagnosis first: why the claimed ledger line does not resolve.
