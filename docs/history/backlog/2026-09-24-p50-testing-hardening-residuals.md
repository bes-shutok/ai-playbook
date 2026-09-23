# Backlog: P50 testing-hardening residuals (six unpinned cells)

Driving force: code-quality

Captured 2026-09-24 during the P50 scheduler state-durability leftovers plan execution (Phase 3 code-review r1, testing lens + Step 1.2b panels; zero blocking). All six cells are Low, plan-related, deferred per the backlog-deferral default. Suggested work home: a focused hardening pass on scripts/test_execute_plan_resume_watcher.py.

- Pin the `cas_refused` None/empty arms (scripts/execute_plan_resume_watcher.py:1315): a mutation collapsing them to `== "stale-attempt"` survives the 76-test suite; add one stub-driven case (adapter returning a blocked result with no reason_code, asserting the stale boundary and watcher-cas-stale).
- Witness the supersede-classification stale machine-trail cell (watcher:1376-1377 feeding the shared trail append): no test drives a refused supersede-classification boundary through run_cli_watcher_operation asserting machine-reason=stale-attempt.
- Pin the runtime watcher-schedule malformed path (shared arm; reachable only via a slugless hand-edited manifest): one-case pin if that path ever becomes reachable.
- Replace the tautological four-documented-fields set assert in test_schedule_fresh_state_documented_payload_schedules with an assertion derived from the driver's documented payload source.
- Patch or accept-and-document the ambient wall clock in the three CLI-driven new tests (scheduled_at_epoch/updated_at unpinned; in-file precedent at test_plans_authoring_watcher_cli_operations).
- Make ConcurrentWriteAdapter subclass WatcherStateAdapter so instantiation enforces surface completeness.
