Status: open
Priority: medium
Class: fix-class
Origin class: review-finding (panel r1, ad-hoc landing 2026-11-15 receiving-review-focused-panel-follow-through)

# doing-code-review lacks the provider-side Integration Points entry for the receiving-review panel consumer

## Problem

The receiving-review-focused-panel-follow-through ad-hoc landing (2026-11-15) made `agents/skills/receiving-review/SKILL.md` a consumer of `doing-code-review`'s focused-panel workflow (completed-fix handoff paragraph plus the consumer-side integration note in its `With doing-code-review` section). The provider side gained no matching entry: `agents/skills/doing-code-review/SKILL.md`'s `## Integration Points` section documents execute-plan, execute-plan-stack, and maintenance consumers but not receiving-review. The repository guidelines' cross-cutting rule requires the integration documented in both directions.

## Suggested fix

Add one paragraph to `agents/skills/doing-code-review/SKILL.md`'s `## Integration Points` section, parallel to the maintenance entry: the receiving-review completed-fix handoff as consumer (focused panel over the exact final diff, same-cycle exception for already-panel-covered bytes). Verify the consumer-side wording against receiving-review's landed paragraph before writing.

## Why not fixed now

`agents/skills/doing-code-review/SKILL.md` is on the ad-hoc backlog arm's mechanical denylist (panel of record; plan route only), so this fix cannot ride an ad-hoc landing; it needs the ordinary plan or review route.

## Driving force

reliability + maintainability
