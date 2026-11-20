# Backlog: share the quota-wake carrier repair transition

- **Filed:** 2026-11-09, execute-plan Phase 3 code review r2, finding F3 (design-simplicity)
- **Status:** covered (docs/history/plans/completed/2026-11-15-quota-wake-lifecycle-boundaries.md; landing ad7c4217fe)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** simplicity; secondary: maintainability
- **Severity and source:** Low, `.ai-playbook/reviews/2026-11-09-codex-maintenance-quota-reset-wake-code-review-r2.md`, r2, F3
- **Capture hygiene:** `bash scripts/scan-public-hygiene.sh --files ...` passed
- **Why not fixed now:** The two recovery paths currently behave correctly; no drift or failed recovery was observed. The personal project profile defers this formal-hardening cleanup, and extracting shared logic from this safety-sensitive transition would add review scope after the behavior review.
- **Dedup probe:** Searched open backlog filenames and problem bodies for `carrier repair`, `carrier-consume`, `quota wake repair`, and `duplicated receipt`; nearest match was `docs/history/backlog/2026-10-25-machinery-inventory-check-preexisting-red.md`, which tracks inventory-check preexisting-red handling, not duplicate quota-wake carrier repair. No existing row covers this transition.

Cluster: docs/history/backlog/2026-11-09-quota-wake-lifecycle-boundary.md (same Codex quota-wake scheduler lifecycle; this row covers shared repair transitions, sibling covers the broader scheduler boundary)

## Problem

`CodexQuotaWakeScheduler.fire()` in `scripts/execute_plan_resume_watcher.py` (around line 1415) and `_repair_pending_carrier_receipts()` (around line 1295) each restore a missing sentinel, verify carrier consumption, map the prior queue outcome to `queued` or `queued-but-unconfirmed` (otherwise `operator-required`), and persist the repair result. The duplicate recovery transition can drift if receipt-state handling changes.

## Suggested fix

Extract the common carrier-repair transition into a helper while keeping each caller's lock ordering and response shape. Add focused coverage for both callers and prove the helper preserves the prior queue outcome.

## Acceptance

Both recovery entry points use the same transition implementation, and tests prove queued, queued-but-unconfirmed, and unresolved outcomes retain their current dispositions.
