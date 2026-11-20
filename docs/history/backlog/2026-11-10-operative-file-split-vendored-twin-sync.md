Status: open
Priority: medium
Class: fix-class
Origin class: execution residue (execute-plan run operative-file-read-budget-gate, 2026-11-10)
Driving force: efficiency

# Vendored runtime twins of the split operative files still hold the pre-split bodies

## Problem

The operative-file-read-budget-gate plan split four operative files load-on-dispatch in the repository (the maintenance runtime overlay, the plans skill, the execute-plan skill, and the agterm reference). The runtime-side twins under the agent skills registry were byte-identical before the split and now diverge: they still hold the pre-split single-file bodies, so a session loading the runtime copy keeps hitting the Read tool's single-read refusal the plan removed from the repository copy.

## Scope

- Sync the split routers and their module files to the runtime registry per the vendored sync rules (full bidirectional sync with deletions, diff first, hygiene scan after).
- The split-aware vendored-twin equality leg in scripts/test_done_sweep_gates_lib.py already accepts both states (pre-sync: router head plus modules equals the twin; post-sync: file-for-file); after the sync the pre-sync branch is dead and can be dropped.
- Review residuals riding this row: the plans router's dispatch entries do not declare the template headings inside plan-format.md and phase-1-requirements.md (discoverability only); two script comments still name the pre-split overlay file as a section home (they resolve through the router's dispatch table).

## Witness

Execution record: the archived plan docs/history/plans/completed/2026-11-07-operative-file-read-budget-gate.md and its Phase 3 code review records (r1 findings 5 and 6, deferred here).
