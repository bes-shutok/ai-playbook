# Backlog: P50 contract-docs completeness residuals

- Status: rejected (2026-09-27; docstring/sentence polish plus a new count pin with no witnessed failure)

Driving force: code-quality

Captured 2026-09-24 during the P50 execution (Phase 3 r1 contract-docs + correctness lenses; zero blocking; all Low, plan-related, deferred).

- scripts/execute_plan_resume_watcher.py run_cli_watcher_operation docstring: schedule bullet predates the malformed boundary / watcher-receipt-invalid outcome; add one sentence when the function is next edited.
- agents/skills/execute-plan/runtime-contract.md:839 envelope sentence enumerates carrier_teardown "null on install and stale boundaries"; the new malformed boundary also returns none (extend to "install, stale, and malformed"; the span is pinned, reconcile pin and text in one edit).
- agents/skills/maintenance/SKILL.md writer-join parenthetical names only two of the arm's three state writes (omits the no-carrier leg's parent_automation_id recording; the trailing delegation covers it).
- Gate-26 span (the two writer-join entries, count==2) has no standing pin in scripts/check_maintenance_pins.sh; after the plan closes, a future edit deleting one entry leaves the pins suite green. Add a count==2 pin mirroring gate 26.
