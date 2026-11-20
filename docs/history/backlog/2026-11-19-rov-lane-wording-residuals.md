# Read-only verification lane wording residuals
Cluster: docs/history/backlog/2026-11-19-rov-lane-frontmatter-and-caps.md
- **Cluster:** docs/history/backlog/2026-11-19-execution-blueprint-lane-arm.md; docs/history/backlog/2026-11-19-rov-lane-frontmatter-and-caps.md

Status: open

Priority: low
Class: fix-class
Origin class: execute-plan phase-3 residual (plan docs/history/plans/2026-11-19-execute-plan-read-only-verification-lane.md, r2 record)
Driving force: simplicity

## Problem statement

Grouped low-severity wording residuals from the r2 focused panel: (a) the lane module's "each retained duty follows its owning module unchanged" sentence conflicts with the checkbox-marking digest leg that depends on vacated worker-dispatch machinery; (b) the lane's Phase 2 command-set composition is unnamed after vacating the suite-policy resolution machinery; (c) the lane's archive-check/leg naming drifts from the owning modules' names; (d) the dispatch-bullet abstract's "retained duty list ending in" does not match the module's paragraph boundaries; (e) a resumed run after a stop-rule stop re-enters the lane with the no-tracked-edit invariant already breached and no re-route trigger; (f) the executed plan's own Task 1 acceptance item and Assumption parenthetical still describe the compound entry test the shipped module deliberately split, and the plan preamble's "a new regression cannot hide behind the baseline" sentence overclaims for post-gate pins cells.

## Exact location

- `agents/skills/execute-plan/read-only-verification-lane.md`: condition, placement, retained-duties, receipt paragraphs.
- `agents/skills/execute-plan/SKILL.md`: the read-only-verification-lane dispatch bullet.
- `docs/history/plans/completed/2026-11-19-execute-plan-read-only-verification-lane.md`: acceptance item, Assumption 1, validation preamble (post-archive path).

## Suggested fix

One wording pass: scope the "unchanged" sentence, name the Phase 2 command-set composition (the plan's declared Validation Commands block), align the archive-check naming with the owning modules, adjust the bullet abstract, name the post-stop resume posture, and amend the plan-record sentences.

## Severity and source reference

Severity: Low. Source: `.ai-playbook/reviews/2026-11-19-execute-plan-read-only-verification-lane-code-review-r2.md` findings 2 and 3 (and its overflow rows). Capture hygiene: scan-public-hygiene pass; no em dashes.
