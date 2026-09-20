# Backlog: fire-at midnight-crossing tail-band test hardening

Status: open
Origin: execute-plan run 2026-09-20-quota-aware-scheduling-semantics, Task 2 Step 1.2b r1 (testing lens, two minor off-plan suggestions)
Driving force: the F9 anchor semantics are pinned only on the fit path; a tail-band fire whose deferred weekday slot is too short never exercises the defer-reset rung with the anchored slot, and the 23:30 tail-threshold boundary test asserts peak/verdict but not the defer_to anchor, so an anchor regression on that exact boundary would pass.

Proposed direction: add one test driving a midnight-crossing tail fire with a need_minutes that does not fit the deferred Monday 04:30 slot (asserts defer-reset with the anchored slot), and extend the 23:30 half of the minute-boundary test with the defer_to anchor assert.

Found 2026-09-21; deferred per the backlog-deferral default (non-blocking, cosmetic hardening).
