# Plan: Expose all closeout helper commands in top-level help
Backlog origin: docs/history/backlog/2026-10-24-closeout-helper-command-discovery.md
Driving force: code-quality; secondary: efficiency
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-closeout-helper-command-discovery-r*.md
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-24-closeout-helper-command-discovery.md (session 6ec9316b-3ef0-430f-9b21-419a8810f212)

## Terms

- **Generic help catalog:** The command list produced by running the helper with `--help` and no subcommand.
- **Specialized command:** `gate-removal`, `owned-files-clean`, or `sweep`, each of which is routed by `main()` to its own parser before the generic parser runs.

## Why

The helper's generic help lists three commands even though its dispatcher supports six. A caller who starts with `--help` can miss the three dedicated closeout commands and mistakenly report that required tooling is unavailable.

## Gist & Examples

TLDR: List all six routed closeout commands in generic help, reducing false missing-tool diagnoses through code-quality.

**Before (today):** A maintainer runs `python3 scripts/worktree_closeout_migrate.py --help` before cleanup. The output names `capture`, `migrate`, and `verify-records`, so the maintainer cannot discover `gate-removal`, `owned-files-clean`, or `sweep` from the command catalog.

**After (this plan):** The same command lists all six supported commands and their short descriptions. The maintainer can then run each command's own `--help` to see its detailed options; the three specialized commands still reach their existing parsers and outcome handling.

## Outcome

The generic help accurately lists every command that the helper already supports.

- All six existing commands are visible in the generic help output.
- Direct command help remains usable through the current parser routes.
- Operational dispatch, exit codes, error classes, and `OUTCOME:` lines remain unchanged.

Gate delta: none; the change exposes existing routes in help and adds no refusal class, hard gate, fence, protocol, schema, state field, or dispatch pause, and removes none.

## Assumptions

- `main()` continues to route `gate-removal`, `owned-files-clean`, and `sweep` before invoking `build_parser()`; the current implementation verifies this separation.
- The specialized parsers remain the source of detailed usage and operational behavior. Preserve their current help output, including the existing doubled `sweep` token in its usage line.
- Map the origin's reliability force to `code-quality`, with `efficiency` secondary: the change corrects a misleading CLI contract and prevents avoidable diagnosis work.

Decision points requiring a grill: add help-only registrations for the three specialized commands in the generic parser and preserve their early dispatch; the maintenance standing authorization selects this smaller change based on the source topology and the origin's rejected alternatives; date: 2026-10-24; affected plan sections: Gate delta, Task 1, and Evaluation Criteria.

## Standing constraints

- Keep each specialized command's parser and direct route unchanged.
- Keep legacy `capture`, `migrate`, and `verify-records` parsing and exit behavior unchanged.
- Do not merge parser implementations, add an availability preflight, or add other blocking machinery.
- Leave the doubled `sweep` usage token for a separate scope decision.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: generic help names all six commands, and direct `--help` calls still print usable usage text.
- Compatibility: existing command dispatch, exit codes, error classes, and outcome lines remain unchanged.
- Maintainability: the help catalog identifies specialized commands without duplicating their parser behavior or options.

**Done when:**
- Focused assertions cover all six names in generic help and verify that each direct `--help` route exits successfully with usage text.
- Existing closeout helper tests still pass, including coverage of specialized and legacy error behavior.

**Ship when:** none; this is a repository-local help and regression-test change.

## Review Scope

**Explicit must-fix: findings on this path are always in scope.**

**Production code:**
- `scripts/worktree_closeout_migrate.py`

**Tests:**
- Focused regression assertions for the generic command catalog and direct help routes, discovered in the existing suite at execution.

**Plan-related extension:** implementation and review may change supporting tests when causally required to cover these help behaviors or prevent a regression in the existing route contracts.

**Out of scope; reject unless plan-related:**
- `scripts/OUTCOME_CONTRACT.md`; no outcome contract changes are intended.
- Other helper commands, closeout procedures, skill prose, and the existing `sweep` usage wording; none is required to complete the selected goal.

## Validation Commands

```bash
python3 scripts/worktree_closeout_migrate.py --help
python3 scripts/worktree_closeout_migrate.py capture --help
python3 scripts/worktree_closeout_migrate.py migrate --help
python3 scripts/worktree_closeout_migrate.py verify-records --help
python3 scripts/worktree_closeout_migrate.py gate-removal --help
python3 scripts/worktree_closeout_migrate.py owned-files-clean --help
python3 scripts/worktree_closeout_migrate.py sweep --help
```

### Task 1: Expose the specialized command catalog and pin help behavior

Context surface: the plan's Terms, Outcome, and Standing constraints.

Files:
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `build_parser` in `scripts/worktree_closeout_migrate.py`
- `main` in `scripts/worktree_closeout_migrate.py`

- [ ] Given the generic `--help` invocation, expose `gate-removal`, `owned-files-clean`, and `sweep` alongside the existing three commands through help-only catalog entries; do not add new runtime dispatch or option parsing to these entries. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given each direct command `--help` invocation, expect successful usage output from that command's existing parser; preserve the current `sweep` usage spelling. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep `main()`'s specialized dispatch before the generic parser and retain the existing legacy parser behavior. Given an invalid specialized or legacy invocation, expect its current exit class and `OUTCOME:` behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add focused regression assertions that generic help names all six supported commands and all six direct `--help` routes remain usable, without rewriting the existing operational contract tests. [class: REPOSITORY_TEST]
- [ ] Run the focused closeout-helper test scope selected from the repository's current test harness and confirm the existing relevant tests remain green. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: list all closeout helper commands in help` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

No README or skill catalog changes: the helper already supports all six commands, and this plan changes only its command-help catalog and regression coverage.
