# Backlog: quota probe wait_minutes unbounded under threshold overrides

Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; override-only CLI bound (defaults safe; own tests drove the extreme). Revive on an operator actually overrides the thresholds, or a project-priority-profile change.)
Origin: execute-plan run 2026-09-20-quota-aware-scheduling-semantics, Task 1 Step 1.2b r1 (risk lens finding 2, accepted-deferred)
Driving force: the new wait-for-reset ride-through instructs an in-session wait of the reported wait_minutes; with threshold overrides (--minutes-before has no upper validation, --min-protocol-minutes only >= 0) the reported wait can reach hours or days, silently converting a recoverable pause into an effectively unbounded lane stall; with defaults the arm is capped at ~21 minutes (minutes_remaining < min(20, 10) + 2), so the exposure is override-only, but the CLI's own tests previously drove --minutes-before 999.

Proposed direction: either an upper sanity bound on --minutes-before / --min-protocol-minutes at CLI validation, or a documented cap on wait_minutes with the excess falling back to the pause protocol. Decision logic (evaluate_pause) should stay untouched; this is a CLI/validation-surface fix plus a discriminating test.

Found 2026-09-21 by the Task 1 risk lens worker; deferred per the backlog-deferral default (non-blocking).
