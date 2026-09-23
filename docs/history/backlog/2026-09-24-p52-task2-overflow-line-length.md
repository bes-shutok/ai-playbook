# Backlog: P52 Task 2 - breakpoint-overflow line is markedly longer than sibling lines

- Date: 2026-09-24
- Status: open
- Origin: execute-plan Step 1.2b intermediate review, task 2 worker (contract-docs), finding 2
- Driving force: simplicity (secondary: code-quality)

## Concern

The Task 2 replacement line in agents/skills/agents-best-practices/references/prompt-caching-and-cost.md packs the budget rule, the quoted overflow literal, and the consequence chain into one ~260-character line, hurting scannability versus the text block's short sibling lines. Future edits must preserve all four mandated spans, which discourages splitting the line.

## Suggested remedy

When the reference doc is next edited, split the overflow line into two lines (budget+signature; consequence+400 contract) while preserving the four pinned spans across the two lines.
