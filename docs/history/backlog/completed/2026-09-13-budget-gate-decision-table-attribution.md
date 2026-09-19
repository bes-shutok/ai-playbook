# Backlog: budget-gate decision-table outcome attribution

Status: done (executed via docs/plans/completed/2026-09-15-budget-gate-decision-table-attribution.md, 2026-09-18)
Origin: review round r6 F1 (Low, non-blocking) of docs/reviews/2026-09-13-plan-review-budget-gate-quota-fixes-r6.md (plan docs/plans/2026-09-13-budget-gate-quota-fixes.md, certified digest ef8f7d281b093fafc0bc8069423961f2ddacfe9129f02295e9eb06c5bec7afb4; folding it would have broken the certification at the round cap, so it is captured here per the Backlog capture rule)
Date: 2026-09-13

## Finding

The Codex deny-envelope decision table (Ship-when drive in the budget-gate fixes plan and the decision table recorded in docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md once created) attributes outcomes to the budget-guard hook without isolating them from co-registered hooks and host-global marker state: the live `~/.codex/hooks.json` co-registers a matcher-`.*` hook (`require-luna.py`) whose denial can satisfy branch one (envelope accepted) without the budget-guard envelope being honored, and the host-global `budget-guard.fired` marker can be written by a concurrent automation-born or peer session during the drive window, satisfying branch two (envelope rejected) without the budget-guard hook emitting anything.

## Why bounded and self-correcting

A false branch-one verdict is re-exposed by the required real-pause Ship-when condition (one real budget pause completing end-to-end); a false branch-two verdict stalls loudly at the RED-pin step (the probed-accepted shape cannot be pinned because no probe produced one).

## When to act

Superseded by docs/plans/2026-09-15-budget-gate-decision-table-attribution.md: read-only isolation (session checks plus marker and hooks-trust baselines) is now mandatory pre-drive per the sibling item's procedure, while the hooks.json disable remains row-2-contingency-only; this item remains the historical record of the finding, as does the completed budget-gate-family-residuals plan's Ship-when line (the sibling item is currently the sole procedure home; docs/plans/2026-09-17-budget-gate-pause-mechanics-drive.md will fold it into the README). The imperative paragraph below is retained as historical record only: it is not a live instruction, and the sibling item's procedure is the only current isolation procedure.

If the Ship-when drive or the real-pause verification produces an outcome that contradicts the adapter-level fixture probes, isolate attribution before trusting the decision table: disable the co-registered matcher-`.*` hook for the drive, and record the fired marker's mtime/epoch before and after the drive to rule out a concurrent writer.
