# docs-branch floor preflight review residuals

- Class: IMPLEMENTATION_REQUIRED
- Driving force: code-quality
- Origin: execute-plan r1 intermediate review (backlogged-candidates BC-1/BC-2), plan docs/history/plans/2026-10-28-docs-branch-supported-python-runtime.md (Task 1)
- Surface: scripts/docs_branch_sync.sh

## Findings
- BC-1: the preflight's `local` declaration omits `version_q`, which is assigned via `printf -v` immediately before use. Cosmetic; declare it for consistency.
- BC-2: a zero-padded version component (e.g. `Python 3.08`) trips bash octal arithmetic and degrades to the old raw `tomllib` failure instead of the preflight diagnostic. Unreachable with real CPython output. Fix: `10#${BASH_REMATCH[1]} * 100 + 10#${BASH_REMATCH[2]}`. Durable lesson recorded: docs/maintenance/development_lessons.md #334.
