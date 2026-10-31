# Malformed closeout baseline JSON escapes as a traceback

- **Filed:** 2026-10-31, execution validation residual from the completed missing-baseline plan
- **Status:** open
- **Priority:** low
- **Workflow:** plan-worthy
- **Class:** fix-class
- **Origin class:** self-serving
- **Severity:** Low
- **Driving force:** observability
- **Source reference:** `docs/history/plans/completed/2026-10-27-plan-closeout-missing-phase0-baseline.md` and `docs/tmp/execute-plan/plan-closeout-missing-phase0-baseline/task-1-implement.log.md` (malformed-baseline case, exit 1 with `JSONDecodeError` traceback and no target copy)
- **Capture hygiene:** `scan-public-hygiene --files` pass

## Problem

`cmd_migrate` reads a present baseline with an unguarded `json.loads` at `scripts/worktree_closeout_migrate.py:1119`. A malformed JSON baseline exits with a Python traceback instead of the named refusal used for other invalid baseline inputs. The observed run did not copy files, so the migration remained fail-closed; the defect is the missing operator-facing refusal and diagnostic path.

## Evidence

- The completed plan's evaluation criteria require a malformed present baseline to retain migration refusal even when a valid sibling skip exists, while explicitly declining broader schema validation.
- Its realistic-context validation log records the malformed JSON case returning exit 1 with an uncaught `JSONDecodeError` traceback and no target copy (`docs/tmp/execute-plan/plan-closeout-missing-phase0-baseline/task-1-implement.log.md`, lines 34 and 38).
- The unguarded parse remains at `scripts/worktree_closeout_migrate.py:1119`; the ordinary missing/empty `dirs` refusal is a named exit-2 path immediately below it.

## Why not fixed now

The completed plan's owned scope was documentation and path-precedence behavior; its execution left the migration script unchanged. This follow-up should preserve present-baseline precedence and the no-copy result while making malformed-input reporting explicit.

## Suggested fix

Convert baseline read/decode failures into a concise named migration refusal with a stable nonzero refusal code. Keep a present malformed baseline from falling through to a sibling skip, and pin the refusal output and no-copy behavior with a focused regression case.

## Dedup probe

Searched open backlog filenames and Problem bodies, plus both rolling prompt logs, for malformed baseline JSON, baseline parse errors, `JSONDecodeError`, and `cmd_migrate`. The nearest rows are distinct: `2026-10-30-worktree-closeout-migration-test-env-hermeticity.md` covers an inherited test-process environment variable; `2026-10-25-closeout-skip-record-producer-residuals.md` covers skip-record idempotence and slug parity; `2026-10-31-closeout-zero-delta-report-arm-coverage.md` covers a different report helper; and `2026-10-27-closeout-mirror-residuals.md` covers migration mirror behavior.
