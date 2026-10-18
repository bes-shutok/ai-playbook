# Backlog: add observable witnesses for sequential execute-plan behavior

- **Filed:** 2026-10-11, Phase 3 review of the sequential-only adapter-removal plan
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** self-serving
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md`, sequential delegation and timeout fallback
- **Source reference:** `docs/history/reviews/2026-10-11-execute-plan-sequential-only-adapter-removal-code-review-r2.md`, F3 (testing); capture hygiene: `scan-public-hygiene.sh` pass before commit
- **Driving force:** reliability
- **Severity:** low; current checks can pass on contract wording without observing launch/result/checkpoint order or safe handling of unknown worker liveness.

## Problem

`ReviewTrajectoryPolicyFixtureTest` checks for policy phrases in the execute-plan skill but does not prove an ordered implementation trace or that unknown worker liveness prevents edits and duplicate launches. The workflow is prompt-driven and has no executable orchestration driver that can emit those events for a focused trace test.

## Expected

When an executable workflow harness exists, add an assertion-bearing trace fixture proving `launch(task1) < result(task1) < checkpoint(task1) < launch(task2)` and proving an unknown-liveness trace contains no parent edit or relaunch. Keep contract phrase assertions as policy checks, not behavioral evidence.

## Evidence

- Review finding from the testing lens in `docs/history/reviews/2026-10-11-execute-plan-sequential-only-adapter-removal-code-review-r2.md`.
- The current workflow implementation is `agents/skills/execute-plan/SKILL.md`; no runtime driver owns these prompt-mediated transitions.

## Immediate workaround

For the current plan, use the durable task execution record (ordered worker result, checkpoint commit, then next-task launch) and review log as the behavioral witness. Keep the skill phrase assertions labeled as contract checks. For unknown liveness, rely on the explicit normative stop rule and record any real occurrence in the run log; do not claim an executable no-edit/no-relaunch test exists.

## Why not fixed now

Building a workflow harness is outside this plan's scope and would add a new executable orchestration surface without an existing driver to host it. The current plan preserves the sequential and safe-fallback contract, and the operator-authorized run provides a durable trace for the exercised sequential path. Revisit when a driver or harness is introduced.

## Dedup probe

Searched the open backlog for execute-plan sequential traces, launch/result/checkpoint ordering, and unknown-liveness tests. Existing rows cover evidence-envelope mismatches and orchestration continuation, not the missing behavioral witness for these transitions; keep this as one focused coverage item.

## Decision

The operator directed creation of an ai-playbook backlog item and continuation with a workaround. The limitation is recorded explicitly; the current run's durable task/checkpoint order is evidence only for the exercised sequential path.

## Follow-up from the adapter-removal landing

The plan `docs/history/plans/completed/2026-10-11-execute-plan-sequential-only-adapter-removal.md` removed the adapter-backed worker/runtime and retained sequential delegation and its stop-on-unknown-liveness contract. It did not add an executable orchestration harness or behavioral trace check; this row remains open for the same stated trigger, when such a harness exists.

## 2026-10-13 re-investigation (PLAN-PROMPTS entry discharge)

The authoring lane discharged the `execute-plan-sequential-trace-harness` prompt's no-driver arm at main f0fa4199a: no executable orchestration driver or other current consumer owns launch/result/checkpoint transitions. The adapter-backed runtime retired by commit e0d7d6961 was the last owner of these transitions; `scripts/` carries no driver, harness, or orchestration surface, and the workflow remains prompt-mediated through `agents/skills/execute-plan/SKILL.md`. The row stays open as the conditional record. The trigger that re-activates it is an executable orchestration driver or consumer owning task launch, result, and checkpoint transitions; the Expected section's trace fixture applies once that trigger exists.
