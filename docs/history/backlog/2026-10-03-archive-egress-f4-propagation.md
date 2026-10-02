# Backlog: propagate the sideways-rename egress extension into the plan Terms and the landing-lane trigger

- **Status:** open
- **Origin:** execution review r1 (docs/reviews/2026-10-03-exec-review-archive-ceremony-gate-universal-r1.md) finding 1, non-blocking
- **Driving force:** consistency - residual F4 extended the guard's egress to any rename whose source is a plans-root file and whose destination leaves the root, but the plan body's Terms/Outcome and the execute-plan landing leg's trigger condition still enumerate only archive-state renames and deletions, so a lane following the execute-plan sentence literally skips the check-archive invocation for a sideways rename (the plans-skill closeout checks unconditionally and is unaffected)

## Outcome

The execute-plan landing leg's trigger sentence names the sideways-rename shape beside the archive-state shapes, and the plan Terms' Plan-egress change definition matches the implemented guard semantics.

Ship when: the trigger sentence names sideways renames; a grep pins the shape in execute-plan/SKILL.md.
