# Backlog: Pin stale Codex hook capability documentation with a named test

Captured: 2026-09-23 (source: plan review r15, finding 1)
Status: rejected (2026-09-27; test-naming precision on an already-covered green criterion)
Priority: low

Workflow: backlog

## Problem statement

Task 6 updates the plan-readiness and Codex model-guard READMEs and asks for a regression check against an obsolete hook-capability statement, but it does not name the test method or assertion. This leaves the documentation check's owner and acceptance evidence less precise than the surrounding test requirements.

## Exact location

- `docs/plans/2026-09-22-codex-execute-plan-runtime-reconciliation.md`, Task 6 stale-hook documentation checklist item and GREEN criterion.
- `agents/hooks/plan-readiness/README.md` and `agents/hooks/codex-model-guard/README.md`.
- Candidate test owner: `scripts/test_codex_model_guard.py`.

## Suggested fix

In a future plan or Task 6 implementation refinement, name a specific test such as `test_docs_distinguish_hook_decisions_from_unsupported_matchers`, assert the obsolete capability claim is absent and the supported/unsupported distinction is documented, and include that test in the Task 6 GREEN criterion.

## Severity and source

- Severity: Low, non-blocking verification precision gap.
- Source: `docs/reviews/2026-09-23-plan-review-codex-execute-plan-runtime-reconciliation-r15.md`, F1.
- Capture hygiene: `scan-public-hygiene.sh --files` pass on 2026-09-23.

## Why not fixed now

The current plan's overall acceptance and Task 6 GREEN suite already cover the documentation change, and this issue only asks for a more explicit test name and assertion. It does not block implementation or the plan's correctness gate; defer this refinement to avoid another plan mutation/review cycle.

## Driving force

Primary: testability. Secondary: docs.
