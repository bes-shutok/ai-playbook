# Dirt gate tree-mode operating assumptions absent from OUTCOME_CONTRACT and docstring

- **Cluster:** docs/history/backlog/completed/2026-10-20-done-dirt-regression-correction-block.md (introduced by the correction-set landing's `--tree` mode)
- Status: open
- Priority: normal
- Age: new (2026-10-23)

## What is owed

The landed tree mode of `scripts/dirt_regression_gate.py` adds new path semantics (repo-relative tree keys, unresolvable `--tree` = tool error, tree-absent and HEAD-absent path = tool error), but the module docstring's assumption paragraph and its authoritative surface `scripts/OUTCOME_CONTRACT.md` (the `dirt_regression_gate.py` row) still declare only the worktree-mode assumptions. Callers consulting the declared authority get worktree-only semantics for a landing gate.

## Witness

2026-10-23 Task 1 intermediate review of the done-dirt-regression-valid-correction-path run (contract-docs lens, Medium; file sits outside that plan's Review Scope, so it fell through unowned).

## Suggested shape

One bounded docs pass: declare the mode split in the docstring assumption sentence and the OUTCOME_CONTRACT row (worktree assumptions bind `--base`-only mode; tree mode assumes `--tree` resolves to a tree object and repo-relative tree keys, tool error otherwise).

## Round-2 addition (2026-10-23, same run)

The machine handoff line `dirt REGRESSION PATH:` is line-oriented and not byte-faithful for newline-bearing paths (truncation can alias a prefix path, latent fail-open while the capture fence refuses quoted paths). Fold into the same byte-fidelity rework family: `-z`/NUL-delimited enumeration and handoff, or a documented quoting contract.
