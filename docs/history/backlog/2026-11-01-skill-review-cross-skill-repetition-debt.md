# Backlog: cross-skill single-homing debt - the same contracts restated across skill files (40 findings)

- **Filed:** 2026-11-01, weekly skill-review lane run 1 (batched cluster origin over the 46-skill rotation batch)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** audit-lane finding (advisory review suggestions, read-only, batched)
- **Class:** maintainability

## Problem

The run-1 rotation batch surfaced 40 repetition-class findings: contracts and rules stated in two to five homes each, mostly within execute-plan, doing-code-review, docs-branch, confluence-page-sync, bootstrap-ai-play-doc-hierarchy family, review-plan, review-loop, review-confluence-doc, receiving-review, review-agents, slack-message, jira-workflow, tdd-design, rfc-design, plans, learn, done/investigate, and the doc-hierarchy trio. The full enumerated list with file:line evidence lives in the aggregates record. Each individual restatement is small; the class-level cost is drift: one home gets updated and its silent twins keep the retired wording (the confluence-page-sync stale rule numbering (finding 21) and the maintenance stance staleness (its own row) are the class's first two landed drift instances).

## Expected

One home per contract, other sites as pointers, so a wording update cannot strand silent copies; the skill text anti-growth rules' name-the-home discipline applied to the existing restatements.

## Suggested direction

Advisory consolidation backlog, not one landing: work the list opportunistically - when a landing already touches one member of a restated pair, fold the single-homing edit into that landing (pay-for-growth discipline applies per file). No dedicated plan; the aggregates record is the worklist, and future weekly runs track the class count as the trend line.

## Evidence

- Weekly skill-review run 1 aggregates record, findings 2-20, 22-27, 32, 34-49 (docs/maintenance/skill-review-log.md), each with file:line evidence; duplication report headline (agents-best-practices intersections 7-147 repeated spans).
