# Backlog: Amend the Wrong Location lead clause alongside the project-local convention

Status: covered (docs/history/plans/2026-11-02-wrong-location-lead-clause-contradiction.md)
Workflow: backlog
Priority: medium
Origin class: self-serving
Class: fix-class
Driving force: consistency

## Problem

The plan `docs/history/plans/2026-11-02-private-project-skills-codex-discovery.md` documents `.agents/skills/` as the tracked project-local skill path in the "4. Wrong Location" section of `agents/skills/how-to-write-skills/SKILL.md` and tasks the amendment of the section's "document the convention in user or repo facts, not in generic skill bodies" clause (line 428). Its review round r2 (staging record `2026-11-02-plan-review-private-project-skills-codex-discovery-pa691cca6-r2.md`, finding F1, non-blocking at the certification round) flagged the section's lead Solution line (line 424, "do not hardcode one vendor directory as canonical in skill text") as left unamended beside the new vendor-path convention: two plausible readings can send a reader back to per-project facts.

## Expected

When the plan's Task 1 executes, the lead Solution line is amended in the same edit so neither reading contradicts the new convention; given the amended section, expects no clause in it to direct readers away from the documented project-local path convention.

## Suggested change

Extend the plan's clause-amendment task bullet (or the executing session's scope, as a plan-related extension) to cover the lead Solution line of the Wrong Location section, keeping the facts-document rule scoped to installation-specific values.

## Dedup probe

Searched open backlog rows for `Wrong Location`, `lead clause`, and `vendor directory`; no other open row covers this residual. Source: certification round r2 finding F1 of the plan above.
