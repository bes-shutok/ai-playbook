# Backlog: make the docs-branch runner select a supported Python runtime

- **Filed:** 2026-10-11, maintenance execution of plan 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** automation
- **Severity:** low; the sync can be completed by selecting the configured Python 3.14 environment, but the documented canonical command fails with the host's default Python 3.9.
- **Cluster:** `docs/history/backlog/2026-10-11-done-sensitive-scan-neutral-token-assignment.md`; `docs/history/backlog/2026-10-11-done-target-state-learn-commit-closeout.md` (closeout-path friction; this row is interpreter selection, the sibling is a scan false positive).
- **Source:** `scripts/docs_branch_sync.sh`, canonical runner startup; observed during done Step 2.

## Problem

The canonical `bash scripts/docs_branch_sync.sh` command invokes `python3` directly and imports `tomllib`. On this host, `python3` resolves to Python 3.9, which has no `tomllib`, so docs-branch sync aborts before validating roots or updating the docs ref. The configured isolated tools environment provides Python 3.14 and completes the same canonical runner successfully when placed first on `PATH`.

## Expected

Make the supported Python floor explicit and ensure the canonical runner either selects an available supported interpreter or fails before work with an actionable diagnostic naming the required version. Preserve the single canonical sync path and avoid changing global Python configuration.

## Evidence

- Default invocation failed with `ModuleNotFoundError: No module named 'tomllib'`.
- The same canonical command succeeded when the configured isolated tools environment’s Python 3.14 was first on `PATH`; it landed docs commit `570ac1e94ac956e2347e7e05b47cad5740684903`.

## Dedup probe

Searched existing docs-branch backlog entries. `2026-10-09-docs-branch-witness-contract-and-recovery-test.md` covers caller-neutral witness wording and CAS recovery testing, not interpreter selection or runtime compatibility, so this is a separate issue.

## Suggested direction

Document the minimum Python version alongside the canonical runner and add a small preflight that reports the detected interpreter version before importing `tomllib`; if multiple interpreters are supported, resolve the configured runtime from facts rather than hardcoding an environment path.

## Why not fixed now

The sync completed by selecting the already configured supported interpreter. Changing the canonical runner was unrelated to the plan being landed and was deferred to a focused fix.

## Dedup probe

Searched open backlog filenames and problem text for docs-branch interpreter selection and Python version support. Existing docs-branch recovery and runtime rows cover other failure modes, not the default interpreter's missing `tomllib` support.
