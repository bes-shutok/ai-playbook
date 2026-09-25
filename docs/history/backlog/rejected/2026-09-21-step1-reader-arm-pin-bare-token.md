# Backlog: Step 1 pending_rearm reader-arm pin checks the bare field token only

Status: rejected (2026-09-26; unwitnessed hardening: pin-strength hardening with a non-discriminating needle)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; pin robustness (bare-token needle). Revive on the Step 1 region is next reworked, or a project-priority-profile change.)
Driving force: primary test robustness (a future sentence elsewhere in the Step 1 region that names the field re-satisfies the pin after the reader arm is deleted, unguarding the mechanical re-arm dispatch path with a green suite: the same vacuous-canary shape the HOST CAVEAT count-pin precedent exists to prevent).
Origin: code review r1 of docs/plans/2026-09-21-scheduler-maintenance-state-durability.md, staging doc docs/reviews/2026-09-21-scheduler-maintenance-state-durability-code-review-r1.md, finding F16 (Low, non-blocking; moved to overflow per the per-worker non-blocking budget; testing#non-discriminating-pin).

The Step 1 region pin (`if "pending_rearm" not in step1`) holds today because all three in-region occurrences live inside the "- Pending re-arm:" bullet (measured 2026-09-22; the suite now also asserts that invariant mechanically), but the needle is not a distinctive multi-word span.

Candidate fix: pin a distinctive sub-span of the bullet region-scoped to Step 1, e.g. "Pending re-arm: when `pending_rearm` is set", keeping the token check as a secondary floor.
