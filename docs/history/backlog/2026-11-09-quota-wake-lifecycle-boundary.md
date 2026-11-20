# Backlog: define lifecycle boundaries for quota wakes

- **Filed:** 2026-11-09, execute-plan Phase 3 code review r6, finding F3 (design-simplicity)
- **Status:** covered (docs/history/plans/completed/2026-11-15-quota-wake-lifecycle-boundaries.md; landing ad7c4217fe)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** maintainability; secondary: simplicity
- **Severity and source:** Low, `.ai-playbook/reviews/2026-11-09-codex-maintenance-quota-reset-wake-code-review-r6.md`, r6, F3; capture hygiene: `scan-public-hygiene --files` pass
- **Why not fixed now:** This is a valid maintainability concern beyond the plan's carrier behavior scope. The operator chose to defer it for backlog and investigation; no lifecycle extraction is included in this safety-sensitive behavior change.
- **Dedup probe:** Searched open backlog filenames and Problem bodies for `quota wake lifecycle`, `scheduler responsibilities`, `carrier repair transition`, and `god-class`. Nearest match is `docs/history/backlog/2026-11-09-quota-wake-carrier-repair-transition-duplication.md`, which covers one duplicated repair transition; this item covers the scheduler's broader scheduling, fire, repair, and retry responsibility boundary, so retain separately and investigate shared scope.

Cluster: docs/history/backlog/2026-11-09-quota-wake-carrier-repair-transition-duplication.md (same Codex quota-wake scheduler lifecycle; this row covers its broad responsibility boundary, sibling covers shared repair transition logic)

## Problem

`CodexQuotaWakeScheduler` in `scripts/execute_plan_resume_watcher.py` (approximately lines 1128-2001) combines carrier scheduling, delivery/fire handling, receipt repair, and retry transitions. This broad responsibility surface makes safety-sensitive state transitions harder to isolate and increases the chance that changes to one lifecycle path affect another. The review found a maintainability risk, not a demonstrated incorrect result.

## Suggested fix

Investigate the lifecycle responsibilities and their shared state/locking contracts. Consider extracting the smallest cohesive collaborator(s) while preserving behavior and lock ordering; retain the single scheduler if evidence shows extraction would merely move state without reducing coupling.

## Acceptance

The lifecycle boundaries and their contracts are documented by the investigation; any follow-up implementation can change one lifecycle responsibility without requiring unrelated scheduler paths to move, or the investigation records why the existing class boundary is the smaller safe design.
