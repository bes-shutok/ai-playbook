# Backlog: no placement pin quotes the done advisory's direct-commit threshold sentence after the 2026-10-20 re-aim; re-aim comments outgrow the one-clause convention

- **Filed:** 2026-10-20, Phase 3 r1 Low findings F3 and F4 of the done-immediate-commit-single-homing execution
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-loop deferred candidates (one round, two findings on the same rows)
- **Class:** fix-class
- **Skill/step:** `scripts/check_maintenance_pins.sh` (placement rows for `$PD`, lines near 3598-3606); `agents/skills/done/SKILL.md` (Direct-landing advisory, line 114)
- **Driving force:** reliability (drift in the advisory's thresholds should stay visible)

## Problem

The plan retargeted the row quoting `exceeds the direct-commit class bounds` to the measurement-clause span. Afterwards no placement row quotes any span of the advisory's threshold sentence (`a behavior, API, or schema change, or more than four files`); a mangled threshold in the done skill passes the suite, demonstrated on a scratch copy where all four done-file pins stayed green. The thresholds' owner (`agents/skills/execute-plan/worktree-first.md`) keeps its own pins, so the gap is the done skill's restatement only. Separately, the two `# Re-aimed 2026-10-20` comments run 278 and 255 bytes against the adjacent 184-byte one-clause convention, each re-narrating a plan Task 1 bullet the cited plan already carries.

## Expected

Either one additional presence row on `$PD` for a distinctive threshold fragment (the family's warning-only grep, no new mechanism), or a recorded decision that the owner file's pins suffice; and the two comments trimmed to the citation plus one relocation clause. Both changes delete or keep bytes net.

## Why not fixed now

Both are below the plan's Done-when and were deferred as Low at triage; landing them inside the execution would have been an unreviewed fix round.

## Source

- `.ai-playbook/reviews/2026-10-20-done-immediate-commit-single-homing-code-review-r1.md` F3 (testing#missing-gate-needle) and F4 (design-simplicity#shrink-re-aimed-comment-narrative); landing cfb909995.
