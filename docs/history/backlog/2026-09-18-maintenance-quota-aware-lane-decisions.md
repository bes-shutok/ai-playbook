# Backlog: lane decisions do not weigh the 5h quota budget (percent left, minutes to reset)

Status: open
Priority: high (user direction 2026-09-18)
Workflow: backlog
Source: scheduler turn 2026-09-18 ~20:22 local recorded "Decision: execution no-op" (lane over-subscription) while the primary window was fresh (~0% used, roughly 3h to reset); the user challenged the decision because quota capacity was plentiful and unrecorded. The decision mechanism never sees the quota numbers, so it can neither cite them when they would change the call nor be audited for ignoring them.

## Problem

Step 3 (decision) gates the lanes on guards, coverage, and dependency order only. Step 4 (quota leg) runs after the decision and shapes only the fire time (defer/pause/pricing). Two blind spots follow:

1. The recorded decision carries no quota dimension. `decision_reason` strings never state the primary window's percent used or the minutes to the next reset, so a dispatch, a deferral, or a no-op cannot be audited against the budget that was actually available.
2. No branch of the decision table consumes quota state. Near-reset or low-budget windows should bias which lane acts (a multi-hour execution fired into 40 remaining minutes is a guaranteed mid-run pause, while a 30-120 minute authoring child may still fit), and a fresh window is exactly when a bare D3 no-op on a free lane with dispatchable work deserves extra scrutiny.

## Required behavior

1. Every lane decision records the quota state at decision time: primary window percent used and minutes to the next reset (from the probe when usable, otherwise the pricing cache or `unknown`), alongside the existing `decision_reason` entries.
2. The decision table gains quota-aware branches:
   - when minutes-to-reset at the realistic start of work is less than the child-kind runtime estimate (execution 1-4h, authoring 30-120m per the fire-time item), D1 defers the execution dispatch to the reset and records the reason, while D2 may still dispatch the authoring lane when its smaller estimate fits;
   - when the window is fresh (for example under ~25% used with well over an hour left), a D3 no-op on a free lane with dispatchable work must cite an explicit non-quota reason, so "plenty of quota" can never silently coexist with an unexplained idle lane.
3. Reuse the runtime estimates and probe vocabulary already pinned by the related items below; add no new constants where one exists.

## Scope

- `agents/skills/maintenance/SKILL.md` (Step 3 decision rules, Step 4 quota leg)
- `agents/skills/maintenance/zcode.md` (Quota leg overlay)
- `scripts/check_maintenance_pins.sh` (pins for the recorded quota fields and the fresh-window no-op rule)
- state-file schema: extend the decision record (or add a `quota_at_decision` field) under a schema bump

## Related

- 2026-09-16-quota-aware-fire-time.md (compares child runtime against remaining minutes for the fire time; this item adds the decision-layer input and the per-lane bias)
- 2026-09-16-peak-window-dispatch-discipline.md (price axis of the same quota leg)
