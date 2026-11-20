# Backlog: an interactive exec pick treated date order as the full candidate set and reported "only two candidates" while 22 open plans carried Executed: no

- **Filed:** 2026-11-19, interactive $maintenance exec turn (post-stand-down operator challenge)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** witnessed selection-integrity miss (one incident; a wrong exclusion claim was asserted to the operator as a completed survey)
- **Skill/step:** the exec lane's plan-selection step in the interactive dispatch and one-shot execution payloads (urgency-order selection before claim and admission vetting), versus the survey's full-corpus enumeration duty in `agents/skills/maintenance/survey-arms.md`
- **Cluster:** docs/history/plans/completed/2026-11-19-maintenance-foreign-idle-child-outcome-continuity.md (the foreign-idle-child backlog item was completed by this plan; this row owns the picker's under-vetted candidate set)

## Problem

Witnessed sequence, all legs on disk:

1. An interactive `$maintenance exec` turn surveyed `docs/history/plans/` and vetted only the two newest dated plans (2026-11-19) for `Executed:` state, execution-claim presence, and dispatch admission, using date order as the urgency proxy.
2. The turn reported to the operator that "there were only two Executed: no candidates from the urgency-ordered survey", while a post-hoc per-file grep (2026-11-19, same session) shows 22 open plans carrying `Executed: no` (2026-11-13 through 2026-11-18 inclusive) plus one `Executed: yes`. The twenty older plans were never individually checked for a live execution claim, a dependency block, or an admission conflict; "only two candidates" was a date-filter artifact asserted as a survey result.
3. Harm class: a wrong exclusion claim to the operator. An operator reading it concludes the queue is nearly empty; a near-empty reading suppresses the full-queue verification the pick step exists to perform, and any plan skipped this way is silently deprioritized by recency rather than by a stated urgency rule.

## Suggested direction

- Make the exec pick's candidate set explicit before selection: enumerate every open plan with `Executed: no`, then per-plan record claim state, dependency block, and admission verdict, and report the counts ("N eligible of M open") rather than an unqualified candidate list.
- Require the urgency rule to be stated when it is a proxy (recency, backlog driving force, origin-row priority) so a proxy ordering is visible as a proxy.
- Fit: a payload-text or checklist tightening in the execution templates' pick step; no new gate machinery.

## Evidence

- Session transcript of the challenged turn and the correction turn (2026-11-19, zcode interactive exec, run sess_6e95d093; plan pick and stand-down recorded in `docs/tmp/execute-plan/codex-incomplete-run-owner-status-unavailable/manifest.md`).
- The per-file `Executed:` grep output showing 22 `no` rows (2026-11-19).
