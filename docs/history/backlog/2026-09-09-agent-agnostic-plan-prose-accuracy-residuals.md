# Agent-agnostic execute-plan plan prose accuracy residuals (post-execution errata)

Status: open
Workflow: backlog
Source: docs/reviews/2026-09-09-plan-review-agent-agnostic-execute-plan-r8.md (re-cert round r8), findings F1 + F3 + F5 + F6 (Medium/Low, non-blocking; deferred; plan fully executed, archive imminent)

## Problem

Residuals in the executed plan text `docs/plans/2026-09-09-agent-agnostic-execute-plan.md` (moves to `docs/plans/completed/` at archive). Relevant only when the plan text is next read as maintenance documentation or reopened:

1. **F1 (`quality#inconsistent-acceptance-witness`, Medium)**: the Task 2 checklist item (~line 195) states `test_evidence_and_fixtures_are_hermetic` runs "given injected filesystem roots, environment, clock, process runner, and adapter seams... no dependency on live host state". The actual test (`scripts/test_execute_plan_runtime.py:561`) injects none of those seams; it asserts only bounded-evidence redaction, secret absence, and manifest mode 0600. The environmental hermeticity assertions live in `test_runtime_replay_is_hermetic_to_fixture_root` (~lines 807-840). The plan attributes the wrong witnesses to the named test.
2. **F3 (`documentation#adapter-integration-coverage-overclaim`, Medium)**: the Task 5 hermeticity item's claim "activation and adapter integration are covered by their own boundary tests" over-reaches: codex adapter tests run on recorded host envelopes, and real-runtime exercise lives only in Ship-when prose ("exercised in its real runtime", ~line 68). The old wording's "assert no live installation is read" scoped this correctly.
3. **F5 (`consistency#task-validation-skips-named-test`, Low)**: Task 3's own GREEN gate runs only the two selftests; the named test `test_driver_entrypoint_owns_transitions` executes only via the global Validation Commands unittest discovery (it did run there: 42 tests OK at re-cert time).
4. **F6 (`consistency#task4-witnesses-unlisted-in-scope`, Low, hypothesis)**: Task 4's lock/hook race witnesses have no named home in the task Files list or Review Scope tests section (if embedded in `done-lock.sh selftest` / `hooks_probe.py --selftest`, the plan never says so).

## Location

- `docs/plans/2026-09-09-agent-agnostic-execute-plan.md` → `docs/plans/completed/` after archive (Task 2 item ~line 195; Task 5 item ~line 279; Task 3 gate ~line 233; Task 4 ~lines 239-255; Ship-when ~line 68).

## Suggested fix

On next touch of the plan text (or as a one-pass errata edit if the completed plan is reopened): align the Task 2 item's witness list with what `test_evidence_and_fixtures_are_hermetic` actually asserts; soften the Task 5 coverage claim to "activation and recorded-adapter integration" and keep real-runtime exercise in Ship-when; add the named test to Task 3's task-local gate; name the home of the Task 4 race witnesses.

## Severity

Medium (F1, F3), Low (F5, F6). Documentation-accuracy only; no behavior impact; the described tests exist and the suite is green.

## Why not fixed now

The plan is fully executed with all 77 checkboxes marked; editing executed checklist text would re-stale the readiness digest the resume flow just re-certified and force another review round for zero behavioral gain. Recorded as errata per the backlog-capture rule.
