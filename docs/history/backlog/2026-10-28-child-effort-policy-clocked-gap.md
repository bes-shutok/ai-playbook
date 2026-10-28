# Child dispatch effort policy cannot bind clocked children; EXEC-PROMPTS work needs High effort

Added: 2026-10-28 (operator ask: "executions of the plans can be with low effort while plan authoring and executing EXEC-PROMPTS.md should be of HIGH effort")

## Problem

The Child model and effort policy (`agents/skills/maintenance/zcode.md` "Child model and effort policy", 2026-10-06 rewrite) already pairs mode to effort: author-mode children run at High, exec-mode at Low with escalation. But the runtime limitation recorded in the same section (verified 2026-09-15) still holds: the clocked scheduling primitive (`CronCreate`) carries no model/effort fields, so every clocked-dispatched child inherits the host default and the policy is unenforceable on the primary dispatch path. Only the idle-time primitive (`OffPeakCreate`) takes `model`/`thoughtLevel`, and it has no clock. Consequence: effort is effectively random for clocked children.

Policy delta requested by the operator 2026-10-28: EXEC-PROMPTS entries run as ad-hoc executions under exec mode, so the current pairing gives them Low effort; the operator wants EXEC-PROMPTS execution (like plan authoring) at High effort. This contradicts the mode-coupled default and needs an explicit surface: ad-hoc/EXEC-PROMPTS dispatches (the Ad-hoc backlog arm and ready-EXEC-PROMPTS leg of the exec-mode selection rule) pair to High effort regardless of their exec-mode binding, while routine plan executions stay Low.

## Expected outcome

- A dispatch path where every child carrier (clocked and idle) carries an explicit model/effort, either because the runtime exposes the fields on the clocked primitive or because the payload template pins the effort instruction the child session applies at launch.
- The effort-pairing rule updated so EXEC-PROMPTS/ad-hoc execution work pairs to High effort; routine plan execution stays Low.
- The "Child model and effort policy" section updated to name the EXEC-PROMPTS carve-out and the enforcement surface once available.

## Non-goals

- No change to the model pin (GLM-5.3-Flash stays the child model; cost multipliers unchanged).
- No new machinery beyond the effort field/template pin; no admission-protocol gate.

## Witness

- Operator ask 2026-10-28 (this row's Added line); `agents/skills/maintenance/zcode.md` lines 127-130 (policy and runtime limitation); tonight's 22:00 exec run where the dispatched children's effort could not be set.
