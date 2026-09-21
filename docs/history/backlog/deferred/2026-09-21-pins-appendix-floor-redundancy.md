# Backlog: appendix-sourcing count floor cannot fire independently of the layered checks

Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; redundant gate floor removal (gate simplification). Revive on the pins are next reworked under a live plan, or a project-priority-profile change.)
Driving force: primary simplification (the appendix floor (count >= 3) equals what paras[0] membership + byte-identity parity + successor-region membership already guarantee, so the floor adds no independent failure direction; readers must reason about three layers to learn that). The sibling precheck floor was raised to the exact total 5 by review r1's F14 fix, which resolved that half; only the appendix floor remains.
Origin: code review r1 of docs/plans/2026-09-21-scheduler-maintenance-state-durability.md, staging doc docs/reviews/2026-09-21-scheduler-maintenance-state-durability-code-review-r1.md, finding F21 (Low, non-blocking; moved to overflow; simplification#shrink; tension with F14 resolved by the exact-count raise on the precheck floor only).

Candidate fix: either drop the appendix floor (the layered checks are strictly stronger) or restate it as the exact count 3 so any single deletion anywhere fails it; keep whichever the suite's minimum-prescription convention prefers.
