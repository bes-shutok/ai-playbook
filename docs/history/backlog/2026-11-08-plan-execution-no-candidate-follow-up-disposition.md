# Plan and execution skills omit durable follow-up disposition for no-candidate outcomes

- **Filed:** 2026-11-08
- **Status:** covered-pending-execution (docs/history/plans/2026-11-08-plan-execution-no-candidate-follow-up-disposition.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** skill-text
- **Driving force:** reliability
- **Origin:** `docs/history/plans/completed/2026-11-07-test-suite-runtime-reduction-follow-up.md`, Tasks 2-3

The plan's candidate-selection branch correctly rejected parallelism because the measured median gain did not exceed observed variation, rejected same-process reuse because it leaked a caller environment value and showed no gain beyond variation, and deferred a language prototype because Python-specific cost was unmeasured. Its done criteria allowed an evidence-backed stopping point and recommendation to satisfy the task, and its only declared output was a feature note. The note then named concrete next investigations, but no durable backlog row or dispatch prompt was created before the origin was folded and deleted. `execute-plan` already requires valid unfixed review findings to be backlogged, but a failed-to-qualify candidate or unmet quantitative objective can be treated as an experiment result rather than a finding, so that rule did not capture these next steps.

## Suggested correction

Review the plans authoring and execute-plan closure contracts, plus the repository-level instruction home, to make the no-candidate path explicit when a plan has an unmet objective or a user-requested follow-up outcome. Require the authored plan to define how deferred candidate work will be dispositioned, and require execution to convert concrete, still-viable follow-up work from an inconclusive/rejected-candidate result into a backlog origin with a ready-to-dispatch investigation or plan prompt before archive. Preserve an explicit rejected/no-follow-up disposition for options whose evidence rules them out. Reuse the existing backlog and investigation lifecycle; do not add a new registry, gate, or ceremony, and do not require every failed experiment to spawn work.

The fix should clarify ownership between `agents/skills/plans/SKILL.md` and `agents/skills/execute-plan/SKILL.md` and decide whether `AGENTS.md` needs a single cross-workflow rule or should simply point to the owning skills. Keep any operative wording within the repository's skill-text anti-growth rule by removing equivalent bytes in the same change.
