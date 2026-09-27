# Queue-drain execution review r1 Lows (two wording residuals)

- **Created:** 2026-09-25
- **Priority:** low
- Status: rejected (2026-09-27; self-described non-blocking wording/taxonomy naming polish)
- **Driving force:** code-quality

## Findings (review r1 of plan 2026-09-25-execution-lane-queue-drain-continuation, both non-blocking)

1. `agents/skills/execute-plan/SKILL.md` queue-drain paragraph presents the densified claim-refresh triggers ("at every task completion inside the implementation loop, and at every review-round iteration", plus recreate-on-takeover) under the name of the procedure of record (`agents/skills/maintenance/prompt-templates.md` EXECUTION CLAIM paragraph), which carries only "refresh `updated:` at every phase boundary". The insert is currently the only corpus carrier of the densified duty; either reword it as a chained-start addition on top of the record, or land the densification in the EXECUTION CLAIM surface (maintenance skill).
2. Same paragraph uses "one-execution-child guard", not a corpus term of art; the asserted-unchanged guard family is G1e plus the P54 fleet cap. Name them explicitly.

## Suggested resolution

Small prose edit to the execute-plan queue-drain paragraph (unpinned spans; only the taxonomy sentence is parity-pinned, and neither finding touches it), plus optionally the maintenance prompt-template densification and a `$E` addition to the pins script header file-existence loop (review info finding).
