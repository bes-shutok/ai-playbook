# Backlog: merge-lock session-content discrimination fixture

Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; test-fixture content pin. Revive on the merge lock is next reworked under a live plan, or a project-priority-profile change.)

- Status: open
- Origin: Task 1 intermediate review (r1 F1) of 2026-09-20-merge-landing-lock-grouping; verdict backlogged-candidates
- Driving force: the merge selftest fixtures assert only `.ai-playbook/merge-lock.session` presence; a mis-parameterized `write_lock_session` writing `DONE_LOCK_*` keys into the merge session would pass every merge fixture, and no fixture probes session-fence matching with content. Done fixture 15 pins this shape for the done mode; the merge analog is missing.

## Acceptance

- A merge selftest fixture asserts the merge session file carries exactly the 2 `MERGE_LOCK_*` keys (mirroring done fixture 15's shape pin), so key-name drift fails the suite.
- Optional: a `merge-wait-acquire` fixture covering the wait path.
