# Backlog: self-heal disposition taxonomy is enumerated only on the consumer side

- **Filed:** 2026-10-27, execute-plan Task 1 intermediate review (self-heal-before-workflow-stop)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-finding
- **Class:** fix-class (cross-skill contract-drift prevention)
- **Driving force:** consistency (contract restated in multiple places with diverging granularity); secondary: reliability
- **Skill/step:** `agents/skills/self-heal/SKILL.md` Recovery steps 4-5; consumers `agents/skills/plans/SKILL.md` and `agents/skills/done/SKILL.md` self-heal handoff paragraphs

## Problem

Both consumer skills' new self-heal handoffs enumerate a three-value recovery disposition (recovered, preserved for a user decision, no authorized recovery), while self-heal, the provider that records the disposition, never states that enumeration; its own outcome space folds "preserved for a user decision" and "no authorized recovery" into one step-5 branch. The operative no-duplicate-call rule is unaffected under either reading.

## Suggested investigation

Either have self-heal name its disposition outcomes in Recovery steps 4-5, or have the consumers drop the parenthetical enumeration and reference "one recorded recovery disposition" per the provider.

## Source

Execute-plan intermediate review finding, plan docs/history/plans/2026-10-27-self-heal-before-workflow-stop.md; plan Terms define the three values.
