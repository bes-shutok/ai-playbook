# Backlog: authoring child payload omits the claim-file duty

- **Status:** open
- **Date:** 2026-09-22
- **Origin:** authoring run of docs/plans/2026-09-22-project-priority-profiles.md (automation-197f75a7); captured per learn Step 1.8 (skills-corpus workflow gap, not a lesson)

## Skill and step

`agents/skills/maintenance/prompt-templates.md`, "Authoring child (plans skill)" blueprint: the AUTHORING CLAIM duty paragraph sits before the "Schedule at {schedule_time} the following task:" payload sentence, and the payload tail carries only the plans-skill task, pre-authorization, session constraints, and landing steps.

## Observed versus expected

Observed: the session born from the scheduled payload performs the entire authoring run (plan writes, review rounds, done handoff) without ever learning the claim duty: it never writes `docs/tmp/authoring-claims/<item>.md`, never refreshes `updated:` at phase boundaries, and never deletes the claim at closeout. The G1a discovery arm (maintenance Step 2) reads exactly those claim files to classify authoring-lane occupancy, so a payload-born run is invisible to the lane guard for its whole life. Witness: the automation-197f75a7 session wrote its claim file only during the done step, retroactively, after the plan was already certified. The claim duties are also split confusingly: the write and foreign-claim gate sit in the blueprint body (dispatcher side), while the refresh and delete duties target authoring activity (child side), so neither session owns the lifecycle end to end.

Expected: the claim lifecycle is owned by the session that authors. Either the payload tail carries a compact claim duty (write before any plan work in the primary checkout's `docs/tmp/authoring-claims/`, refresh at boundaries, delete at closeout), or the blueprint explicitly assigns the whole lifecycle to one session with the mechanical anchor the G1a arm reads. A related sibling item, docs/history/backlog/2026-09-21-durability-review-residuals.md, already owns the claim protocol's internal races; this item owns only the payload-omission gap and should not fold into it.

## Suggested fix

Append a claim paragraph to the payload tail of the authoring blueprint (between the session constraints and the landing paragraph): one compact write-before-plan-work sentence, one refresh-at-boundaries sentence, one delete-at-closeout sentence, addressed to the primary checkout's `docs/tmp/authoring-claims/` in explicit-rooted form, mirroring the duty paragraph's frontmatter shape. Alternatively, if the intended owner is the dispatcher, move the refresh/delete duties out of the child's reach and say so, accepting that the G1a arm keys on dispatcher-written claims only.

## Environment

ZCode runtime, 2026-09-22, repo copy of prompt-templates.md (this skills repo); run records in docs/tmp/authoring/ under the plan slug.
