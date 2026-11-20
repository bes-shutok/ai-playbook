# Backlog: apply the selected stack-plan workflow to every repository plan

- **Filed:** 2026-11-04, user correction during a cross-repository plan authoring task
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Consumer projects that request one cross-repository PR stack need every repository plan to follow the stack task shape; the skills-repo personal priority profile must not park or defer this as formal-hardening for the skills repo alone.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** automation + clarity
- **Skill/step:** `agents/skills/plan-stack/SKILL.md` Authoring contract, cross-repository plan clause; `agents/skills/plans/SKILL.md` Writing skill selection
- **Catch frequency:** witnessed once; a user correction was needed after the stack workflow was selected for only one repository.
- **False-positive cost:** an unnecessary prompt or catalog change could duplicate the already explicit cross-repository clause; the investigation must first establish whether the failure is in trigger discovery, skill composition, or run-level follow-through.
- **Review date:** 2026-12-04
- **Dedup probe:** searched open backlog names and bodies for `plan-stack`, stacked plans, cross-repository plans, and skill-selection misses. No existing open item covers applying the stack task shape consistently to every repository plan in a split cross-repository stack. The completed stack-plan execution plan defines the stack shape but does not cover this authoring-time selection miss.

## Problem

In a cross-repository task explicitly scoped as two plans for one ordered PR stack, the assistant initially assigned the `plan-stack` workflow only to the Platform plan and assigned the ordinary `plans` workflow to its companion repository plan. The user corrected this: both repository plans must use `plan-stack`. The current `plan-stack` authoring contract already says that every repository plan in a split cross-repository stack uses the stack task shape, so adding another generic reminder without finding why the existing instruction was missed risks redundant skill growth.

## Expected

When one agreed PR stack spans multiple repositories, every repository plan follows the `plan-stack` structure while each repository's `plans` workflow continues to own its plan lifecycle. The operator should not need to correct skill selection separately for each repository.

## Suggested investigation

Trace how the user request's stack intent is routed across repository-specific plans, including the `plan-stack` trigger, its cross-repository clause, `plans` skill-selection text, and the skill discovery path. Determine whether the smallest correction belongs in a trigger description, a single-home cross-skill routing sentence, or nowhere because the recorded event was an execution miss with no durable skill defect. Preserve the `plans` lifecycle ownership and avoid repeating the cross-repository rule in multiple skills.

## Evidence

- In the conversation, the assistant explicitly said it would use the stack skill for one repository's PR slices but the ordinary plans workflow for the companion repository plan.
- The user corrected that both repository plans belong to the stack workflow.
- `agents/skills/plan-stack/SKILL.md` already states that separate repository plans splitting one agreed cross-repository stack each use the stack task shape.
- The parent `plans` workflow says explicit stacked pull-request requests use `plan-stack`; both skill contracts were present in the repository when the correction occurred.
