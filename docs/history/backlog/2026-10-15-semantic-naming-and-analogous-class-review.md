# Backlog: review names for current meaning and clear parallels between analogous types

- **Filed:** 2026-10-15, after repeated readability corrections during a feature implementation and naming audit
- **Status:** open
- **Workflow:** skill text adjudication
- **Priority:** normal
- **Origin class:** user feedback
- **Class:** fix-class
- **Driving force:** quality + simplicity

## Problem

The review corpus has a general naming-consistency check, but this session exposed a more specific gap: names can be locally conventional and describe an individual function while still being stale, misleading about the current responsibility, or unhelpfully different from a counterpart that performs the same role in another domain. The user clarified that the concern was at the interface, implementation-class, and related-type level, not only method names. They asked for an audit of similar naming across the changed feature and then called out that review instructions, including the simplicity check, should give this dimension enough attention.

The existing quality catalog covers naming consistency and redundant words. The simplification catalog is about avoidable structure and shorter forms. The default panel has both quality and design-simplicity lenses, but focused reviews can omit design-simplicity. A recently completed callback-readability plan adds a shape-based lens-retention trigger for callbacks, method-local types, and method limits; it does not establish a duty to compare current semantic roles and names across analogous classes.

## Expected

Decide where semantic naming review belongs among the existing quality and design-simplicity lenses, and define an actionable check for names that express current responsibilities and reveal meaningful similarities across analogous interfaces, implementations, and related types. Define how to compare names without requiring artificial uniformity when responsibilities, ownership, lifecycle, or contracts differ. Determine when changed scope provides enough evidence to retain the relevant existing lens in a focused review. Prefer extending existing agent prompts and panel-selection conditions over adding another worker, review round, validator, or naming framework.

## Acceptance

- Read the existing naming duties in `agents/skills/review-agents/quality.md` and the ownership and checklist in `agents/skills/review-agents/simplification.md`; resolve overlap and assign one primary owner with any needed cross-reference.
- Compare the present full and focused panel rules with the session’s naming witnesses; specify when a focused review of paired or analogous types should retain the owning lens, without making every focused review broad.
- Define reviewable signals: names that describe an obsolete responsibility after a refactor, analogous interfaces or implementations with divergent role names, and misleading similarities between types whose responsibilities differ. Require evidence from declarations, callers, and relevant contracts before suggesting a rename.
- Assess the session examples at a sanitized level: parallel domain-specific application services/interfaces whose responsibilities were intended to be understood as counterparts; a method-only rename did not answer the user's class/interface naming concern; and a new metric family whose names had not yet been deployed was considered eligible for alignment. Do not include company names, ticket IDs, service names, or internal class identifiers.
- Inspect whether the existing callback-readability plan's changed-shape trigger can naturally cover this signal or whether an explicit semantic-naming trigger is needed; preserve that plan's callback and local-type scope without duplicating its rule.
- Prefer the smallest change to existing prompts and panel selection. Reject a new agent, universal panel expansion, or automated naming check unless concrete evidence establishes a recurring failure and a proportionate benefit.
- Verify the resulting review guidance against the session's positive case (analogous role names should communicate intended similarity), negative case (distinct responsibilities should not be renamed merely for symmetry), and timing case (pre-deployment names can be aligned without compatibility baggage).

## Origin

During one feature discussion, the user repeatedly asked for implementation and callback structure to be easier for a human to parse, questioned whether helper abstractions reduced or added reading cost, and preferred names that showed two domain implementations did similar work. After an initial method-level naming response, the user clarified that they meant implementation classes and their interfaces. They then asked for a branch-wide audit of outdated or irrelevant names and explicitly asked that review guidance and the simplicity-check agent cover this kind of issue. The concern is review practice, not a claim that every similar type must share a name.
