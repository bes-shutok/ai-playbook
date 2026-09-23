# Backlog: P52 Task 1 - no validation pins guard the greenfield rerun-loop severance surfaces

- Date: 2026-09-24
- Status: open
- Origin: execute-plan Step 1.2b intermediate review, task 1 worker (contract-docs), finding F4
- Driving force: code-quality (secondary: efficiency)

## Concern

P52 Task 1's Validation Commands pins cover the greenfield rule spans but none covers the Recovery-rerun exception sentence or the final-bullet deference; a regression deleting the loop-severance mechanism ("greenfield doc-layout ask awaiting the user ..." exception or the final-bullet deference) would still exit 0. The unbounded non-interactive rerun-loop guarantee is enforced only by prose review, not by the plan's own green gate.

## Suggested remedy

When docs/plans/ or a successor plan next touches the bootstrap greenfield rule, add file-wide pins for `greenfield doc-layout ask awaiting the user` and the final-bullet deference span to the Validation Commands block.

## Evidence

agents/skills/bootstrap-ai-playbook/SKILL.md Recovery rerun exception and final Discovery-rules bullet; docs/plans/2026-09-23-p52-script-harness-tail.md Validation Commands (Task 1 pin list).
