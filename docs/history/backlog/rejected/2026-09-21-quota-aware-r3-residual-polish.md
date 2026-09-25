# Backlog: quota-aware scheduling semantics r3 residual polish

Status: rejected (2026-09-26; archived-record residuals: checkbox wording, ledger note, unpinned arms; no behavioral defect)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; wording/pin residuals on an executed plan. Revive on the surfaces are next reworked under a live plan, or a project-priority-profile change.)
Origin: execute-plan run 2026-09-20-quota-aware-scheduling-semantics, Phase 3 round 3 focused re-review (clean, four Low/info non-blocking findings deferred per the backlog-deferral default)
Driving force: each item below is a small consistency or pin gap left after the r2 fix pass; none is behavior-affecting, but each can mislead a future reader or let a specific regression pass green.

Items:
1. docs/plans/2026-09-20-quota-aware-scheduling-semantics.md Task 5 checkbox text still prescribes the superseded D2 wording ("decision is not pause"); the landed rule (r1 review finding) is "decision is continue" / dispatch out on "not continue". The plan is archived as certified history; if this origin is ever re-worked, the operative wording lives in agents/skills/maintenance/SKILL.md D2.
2. agents/skills/maintenance/SKILL.md Revisions ledger 2026-09-20 entry was corrected in place (r2 fix) without the ledger's review-address sub-note convention (cf. the provider-429 entry), so the 2026-09-21 wording correction reads as part of the original change.
3. scripts/test_quota_window_probe.py: no test pins wave_recommendation == "full" for the fractional exact-fit case (78.2 used / 21.8 cost), so a revert of the wave-sizing 1e-9 tolerance stays green (the decision arm is pinned; the sizing arm is not).
4. scripts/quota_window_probe.py split arm (plan_cost_percent / 2 <= remaining) lacks the 1e-9 margin; unreachable in consumer-affecting paths (full arm always fires on continue; recommendations are outranked by pause/wait decisions), note-only.

Found 2026-09-21, Phase 3 r3; deferred per the backlog-deferral default.
