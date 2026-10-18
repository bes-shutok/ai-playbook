# Backlog: keep credential scans from rejecting neutral token variables

- **Filed:** 2026-10-11, maintenance execution of plan 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** simplicity
- **Severity:** low; the pre-commit gate can be passed by choosing a neutral local name, but the scan currently rejects ordinary parser code.
- **Cluster:** `docs/history/backlog/2026-10-11-docs-branch-python-runtime-floor.md`; `docs/history/backlog/2026-10-11-done-target-state-learn-commit-closeout.md` (closeout-path friction; this row is a scan false positive, the sibling is interpreter selection).
- **Source:** `scripts/done_sweep_gates_lib.py`, `DIFF_CONTENT_PATTERNS`; reproduced by the Task 1 pre-commit scan.

## Problem

The sensitive-data scan rejected the benign assignment `token = parts[0]` in parser code as credential-shaped content. The diff contains no credential; the match comes from a local variable name and an ordinary file path. A prior backlog item records an earlier generation of this false-positive family, but was rejected after assignment-shaped patterns landed; this reproduction shows the current pattern still has a neutral-variable false positive.

## Expected

Keep detection of credential assignments while allowing ordinary domain variables such as parsed path tokens. Add a focused regression case for a neutral local assignment and retain a positive case for a credential-like assignment carrying a value.

## Evidence

- `bash scripts/done_sweep_gates.sh pre-commit` reported a match in the added line `token = parts[0]` in `scripts/check_plan_origins_closed.py`.
- Renaming the local to `candidate` removes the match without changing parser behavior.
- Related history: `docs/history/backlog/rejected/2026-09-22-done-sensitive-data-scan-credential-shaped-patterns.md`.

## Dedup probe

The rejected predecessor covers assignment-shaped credential detection and an earlier set of neutral terms. This item records a new, specific regression where a common path-parser variable name matches the active scanner; its expected fixture is narrower than reopening that historical item wholesale.

## Suggested direction

Refine the detection boundary or its rule context so a variable name alone does not imply a credential. Keep the scanner focused on actual secret-shaped values and avoid broad exemptions for whole files or domains.

## Why not fixed now

Renaming the local variable allowed the plan work to pass the existing scanner. Changing the shared scanner would be an independent fix outside the plan's reviewed scope.

## Dedup probe

Searched open backlog filenames and problem text for sensitive scan false positives and token-variable matches. The rejected predecessor addresses an earlier assignment-shaped pattern; this row records the active scanner matching a neutral path-parser variable.
