# Backlog: top-level closeout helper help omits routed commands

- **Filed:** 2026-10-24, learn capture from closeout command discovery
- **Status:** covered (docs/history/plans/2026-10-24-closeout-helper-command-discovery.md)
- **Workflow:** backlog
- **Priority:** high
- **Severity:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** reliability; secondary: maintainability
- **Skill/step:** `scripts/worktree_closeout_migrate.py`, top-level help and command dispatch (`build_parser`, `main`)
- **Source reference:** learn Step 1.8, current interactive session; `scan-public-hygiene --files` passed.
- **Environment:** playbook repo source copy, interactive session, 2026-10-24
- **Suspected root area:** the generic parser's command catalog is separate from the early command-routing table.
- **Consumer urgency:** consumer sessions using the shared closeout helper need to discover its supported removal commands; do not defer this as formal-hardening for the skills repository alone.

## Problem

The helper's unqualified `--help` lists only `capture`, `migrate`, and `verify-records`, while `main()` routes `gate-removal`, `owned-files-clean`, and `sweep` through dedicated parsers before it reaches that help parser. During a closeout, the incomplete list led the agent to report that the required commands were unavailable. Direct calls to `gate-removal --help` and `owned-files-clean --help` showed that they work. The misleading command list creates avoidable diagnosis and may cause an agent to stop or report a false deployment gap.

## Expected

The top-level help lists every supported command and points to each command's detailed help, while preserving the existing per-command routing, outcome classification, and error behavior.

## Suggested direction

Expose `gate-removal`, `owned-files-clean`, and `sweep` in the top-level help text without changing their dedicated dispatch or parser semantics. Add focused help-output coverage alongside the existing subcommand help checks.

## Evidence and deduplication

- In this session, `python3 scripts/worktree_closeout_migrate.py --help` listed only three commands; the direct `gate-removal --help` and `owned-files-clean --help` calls both returned their usage text.
- `scripts/worktree_closeout_migrate.py` documents all six commands, but `build_parser()` registers only the three legacy subcommands, and `main()` routes the other three before calling that parser.
- Dedup probe: searched open backlog and both rolling prompt logs for `top-level help`, `command discovery`, `subcommand help`, and `worktree_closeout_migrate.py --help`. The nearest result is `docs/history/backlog/completed/2026-10-08-gate-removal-usage-doubled-token.md`; it fixed a duplicated token in the dedicated gate help and does not cover the incomplete top-level list. `docs/history/backlog/2026-10-21-gate-removal-empty-owned-set-remedy.md` concerns an unattainable refusal remedy, not command discovery.

## Alternatives

- Change only the closeout skill to tell agents which exact subcommand help to invoke: rejected because it leaves the incomplete command list and the witnessed false diagnosis for any direct caller (`scripts/worktree_closeout_migrate.py`, `build_parser`).
- Merge the specialized parsers into one dispatch structure: rejected because help discoverability can be fixed without changing the custom outcome and error contracts in `main()` (`scripts/worktree_closeout_migrate.py`, `main`).
- Add a blocking preflight that verifies command availability: rejected because the commands already execute through direct routing; there is no witnessed incident of command unavailability to justify another gate (`scripts/worktree_closeout_migrate.py`, `main`).
- Keep the current top-level help: rejected because the session's command discovery produced a false report of missing tooling (`scripts/worktree_closeout_migrate.py`, `build_parser`).

## Why not fixed now

The issue is a valid follow-up outside the closeout work's scoped implementation. The closeout used the existing commands and completed without changing the helper.

## Work-type note

This is plan-worthy under the maintenance Ad-hoc backlog arm's tracked-path eligibility test: the named helper is a guard-bearing closeout script, which that arm excludes even though the proposed change is limited to command help and its tests.
