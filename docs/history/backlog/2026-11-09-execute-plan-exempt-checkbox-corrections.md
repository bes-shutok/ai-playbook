# Backlog: honor exempt plan checkbox corrections at readiness

Status: open
Workflow: backlog
Priority: high
Class: fix-class
Origin class: self-serving
Skill-step: agents/skills/execute-plan/SKILL.md Step 0.5
Consumer urgency: Consumer projects that run execute-plan need this correction; the skills-repo personal priority profile must not park or defer it as formal hardening for the skills repo alone.
Driving force: efficiency

## Observed versus expected

Observed: after Task 1's seven acceptance boxes were marked, the active plan digest changed and full readiness refused the ready r11 review as stale. Step 0.5 directs stale reviewed bytes to a fresh plan review, while the plans skill permits a script-verified checkbox-flip correction row with zero review rounds. The plan delta classifier verified this exact change as checkbox-only; after the row was recorded in the review sidecar, hard review validation and full readiness passed without another plan-review round.

Expected: Step 0.5 classifies plan-byte changes through the existing delta classifier and carries fully exempt changes through the latest review sidecar's verified corrections chain. A fresh review remains the route for unclassified or decision-bearing changes.

## Exact location

- `agents/skills/execute-plan/SKILL.md`, Step 0.5 stale-record readiness refusal.
- `agents/skills/plans/SKILL.md`, graded plan-delta rule 2 and exit digest rule 6.
- `agents/skills/review-staging/SKILL.md`, corrections sidecar extension.

## Suggested fix

Align Step 0.5 with the plans skill's existing graded correction route: re-derive the reviewed anchor from the seal, run `scripts/plan_delta_classifier.py`, and when all hunks are exempt, commit the plan delta, append the CLI-produced row to the latest sidecar's `extensions.corrections` under the existing advisory lock and compare-before-write discipline, then run hard staging validation and readiness. Send unclassified deltas to the fresh-review path. Do not rewrite the prior `source_digest`.

## Severity and source

Severity: Medium (the default instruction could cause an avoidable plan review and stall task continuation). Source: `docs/tmp/execute-plan/test-suite-runtime-residual-optimization-path/task-1-implement.log.md`, section "Plan digest recovery"; capture hygiene: explicit-path public-hygiene scan passed.

## Why not fixed now

The active plan's Task 6 covers Dev Quality Gates guidance. It does not own this execute-plan and plans freshness contract, so adding it there would widen reviewed scope. Keep this as a separate skills-plan candidate.

## Dedup probe

Searched open backlog filenames and bodies for checkbox flips, stale plan digests, correction rows, plan readiness and review refreshes. The nearest open entries are `docs/history/backlog/2026-11-06-exec-plan-checkbox-marking-primary-strand.md` (wrong checkout used for the checkbox write), `docs/history/backlog/2026-11-02-execute-plan-task-scope-digest-derivation-entry-point.md` (read-only digest API), and `docs/history/backlog/2026-10-31-execute-plan-missing-review-panel-selection.md` (worker selection); each has a different failure mode. The completed `docs/history/plans/completed/2026-10-29-execute-plan-plan-digest-handoff-drift.md` covers reconciling an accepted done-pending worker receipt, not the normal checkbox-only readiness transition. No open row covers this mismatch.
