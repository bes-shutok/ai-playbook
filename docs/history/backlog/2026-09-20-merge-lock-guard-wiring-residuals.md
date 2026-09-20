# Backlog: merge-lock guard wiring residuals (Tasks 2-4 intermediate review)

- Status: open
- Origin: Tasks 2-4 intermediate review (r1 F1, F2) of 2026-09-20-merge-landing-lock-grouping; verdict backlogged-candidates
- Driving force: G3b reads the merge lock but two prose sites were not wired to know it, so the guard's defer/crash-evidence semantics are discoverable from only one direction and the State-file note undercounts the joint-state safety sources.

## Items

1. SKILL.md State-file scoping note enumerates joint-state safety sources as "the runtime's automation listing, the done-lock, and claim checks"; the merge lock (read by G3b) is a fourth source the note omits. Add it.
2. SKILL.md Step 5 final-slot precondition bullet names only G1e/G1a; G3b's defer effect lives only in Step 2. Add the G3b arm to the Step 5 bullet so the cross-lane case (landing hold while the other lane dispatches) is wired from both directions.
