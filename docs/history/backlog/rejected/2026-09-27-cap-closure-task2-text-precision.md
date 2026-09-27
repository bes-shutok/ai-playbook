# Backlog: Task 2 text precision (frozen-except area label; review-state ban "exemption list" referent)

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: correctness

## Problem

Two Task 2 prescriptions reference structures imprecisely. (1) The Frozen-except qualifier "in the plans skill's Plan Quality Gate loop rules area" covers six regions, two of which live elsewhere: the Plan Format template meta-rule sits under `## Plan Format` (plans SKILL.md:251/266) and the Final Step precondition under `## Final Step: Run done` (:812/816). An implementer arbitrating scope by the frozen list could treat those edits as out-of-bounds. (2) The review-plan bullet says "extend the reviewer-side review-state ban's exemption list", but the ban (review-plan SKILL.md:132) is one sentence with no exemption list; the executor must improvise the amendment's placement and form.

## Observed versus expected

- Observed: r7 contract-docs findings (both Low, non-blocking); the Task 2 bullets name both targets explicitly and the presence gates pin the literals, keeping execution risk low.
- Expected: (1) reword the trailing qualifier to "in the plans skill" or enumerate per-region areas; (2) reword to "amend the reviewer-side review-state ban with a cap-closure exemption: stale-disposition findings about the `## Residual findings (cap closure)` section stay valid, and the staging record remains authoritative for verdicts and round chains".

## Suggested fix

Apply the two rewordings to the plan's Task 2 before execution, or to the landed skill text in a follow-up.

## Environment

r7 execution-time re-cert round, 2026-09-27; deferred per the backlog-deferral default.
