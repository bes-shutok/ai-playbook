# Backlog: doc-registry plan certification prose residuals (r2 F1, r2 F2)

- **Filed:** 2026-11-07, terminal certification duties of the doc-registry-row-edit-validator-timing authoring run
- **Status:** open
- **Priority:** low
- **Workflow:** backlog
- **Origin class:** witnessed defect
- **Class:** fix-class
- **Cluster:** docs/history/plans/2026-11-07-doc-registry-row-edit-validator-timing.md (the certified plan whose prose carries the residuals; this row owns the post-certification prose corrections, that plan owns the registry header expectation)

## Problem

Two non-blocking certification residuals from review round r2 were routed to durable capture per the certification-residual routing (non-blocking findings at the certification round never force a re-round or a plan fold):

1. The plan's Evaluation Criteria correctness bullet still carries the superseded rationale "(the note lives inside the HTML comment the table parser ignores)"; the validator's row scan reads pipe-leading lines even inside the comment (r2 F1, Medium, fold defect: the r1 fold fixed the Edge cases and Task 1 surfaces but missed this sibling bullet). Consequence: an executor reasoning from the stale rationale burns a validate fix round; the criterion itself (validate exits 0) stays correct and Task 1's corrected items keep execution self-correcting.
2. The plan's Assumptions mis-attribute two citations: the quoted "origin row out-of-scope line" lives in the completed 2026-10-27 phase0-baseline plan, not the origin row; the pre-commit-hook rejection is recorded in the PLAN-PROMPTS entry's rejected alternatives, not "in the origin row itself" (r2 F2, Low). The substantive claims hold independently under both corrections.

## Suggested fix

A small plan-update round on docs/history/plans/2026-11-07-doc-registry-row-edit-validator-timing.md: reword the Evaluation Criteria parenthetical to the row-scan hazard shape the Task items already carry, and correct the two citation attributions in Assumptions. Digest re-binding per the corrections-chain rules applies (a corrections row or a fresh focused round per the delta classifier).
