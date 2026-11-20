# Backlog: survey-arms missed-leg consult text lags the clocked-order lease skip

Driving force: reliability

agents/skills/maintenance/survey-arms.md line ~27 (missed-leg consult: "marks every order whose requested epoch passed undischarged missed") no longer matches the discharge operation's live-lease skip introduced by the clocked-order handoff lease (plan docs/history/plans/2026-11-08-clocked-order-payload-session-execution.md Task 1). The skill text is outside that plan's Files lists, so no planned task owns the update. Align the consult text with the lease semantics (skip a live lease; missed classification only after expiry).
