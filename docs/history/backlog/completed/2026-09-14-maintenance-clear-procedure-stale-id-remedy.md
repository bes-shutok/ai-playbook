# Backlog: maintenance clear procedure stale-id remedy

**Captured:** 2026-09-14 (execute-plan Phase 3, review round r8 of the maintenance-scheduler-skill plan; staged finding F1 in docs/reviews/2026-09-14-2026-09-13-maintenance-scheduler-skill-code-review-r8.md)
**Status:** done (2026-09-15) — the suggested split-remedy fix landed as the duplicate-parent tripwire's self-heal arm plus the restricted deletion remedy in the review r1 fix pass (commit 77c09f34): when the recorded `parent_automation_id` is absent from the listing and exactly one ENABLED span match exists, the turn adopts that id and clears the turn error instead of paging a human; the human deletion remedy now applies only when the recorded id is still present in the listing. Kept as a link target.
**Priority:** low
**Origin:** security#recovery-procedure-mismatch (risk lens, r8 focused round)

## Finding

The maintenance skill's human clear procedure (agents/skills/maintenance/SKILL.md, "State file" section) offers one remedy for a `duplicate-parent-candidate` alert: "delete or disable the duplicate automation named by the `duplicate-parent-candidate` reason after confirming it targets this repository". That remedy is destructive and wrong for the stale-id trip variant: when the recorded `parent_automation_id` is stale (points at a deleted automation) the ONLY repo-targeting span-matching automation in the listing IS the live parent, so following the procedure to the letter disables the freshly re-armed parent and silently kills the loop (recoverable only via the last_run_at staleness rail). The correct remedy for that variant, updating the recorded id, lives only in agents/skills/maintenance/zcode.md "Recurring automation recipe" (re-arm hygiene) and is not cross-referenced from the clear procedure.

## Suggested fix

Split the remedy by variant in the SKILL.md clear procedure: if the recorded `parent_automation_id` is stale (its automation no longer exists), update it to the live parent's id instead of deleting anything; only when two or more live repo-targeting scheduler automations exist, delete or disable the extra after confirming it targets this repository. Cross-reference zcode.md's re-arm hygiene. Update the corresponding validation pin span in the archived plan only if the pinned wording changes.

## Verified feasibility facts

- Both trip variants are real: genuine duplicates (two ENABLED repo-root-scoped scheduler-span automations) and stale recorded id after a re-arm (zcode.md documents the stale-id behavior explicitly).
- turn_error stores only the reason string, not an id, so the alert/turn_error surface cannot disambiguate the variants today.

## Open decisions for the plan author

- Whether to also carry an id field in the turn_error reason (structured reason) or keep the string and key the branch on the recorded id's existence.
