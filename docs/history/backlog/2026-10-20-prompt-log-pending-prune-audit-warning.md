# Backlog: warn when pending prompt-log changes remove a foreign prune receipt

- **Filed:** 2026-10-20, split from `docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md`
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** execution-run finding
- **Class:** fix-class

## Problem

The existing prune audit examines committed log-touching changes and misses receipt removals still in the index or working tree. The 2026-10-19 executor-landing-helper-routing-gap review caught a neighboring landing receipt inside an otherwise correctly anchored prune range while the audit stayed green. The originating incident and detailed evidence remain in `docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md` and development lesson 111.

## Admission and promotion boundary

- Incident: the 2026-10-19 neighboring-receipt loss at a correctly anchored range tail, detailed in `docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md`.
- Expected catch frequency: uncommon; a pending prune only catches when a selected range contains a foreign receipt, though every landing or monitor prune can expose the condition.
- False-positive cost: one report line and operator ownership review; the warning-only detector changes no exit outcome or log bytes.
- Review date: 2027-01-20.
- Promotion: warning-only until a production true catch is recorded in the guard-liveness ledger; a separate reviewed change must then decide promotion and include the pre-registered removal row. Until then blocking promotion is prohibited.

## Expected

The existing audit reports pending foreign receipt-line removals in either rolling prompt log, without changing its exit outcome. It binds the observation to stable inputs and identifies the receipt slug and log path. The new detection remains warning-only until its own production true catch is recorded. Any blocking promotion requires a separate reviewed change after that catch and follows the repository machinery admission protocol.

## Fix shape

Extend the existing audit invocation to inspect staged and unstaged log changes and compare removed receipt lines against independently established authorization evidence. Isolate test subprocesses from inherited Git repository and config overrides. Register the incident, expected catch frequency, false-positive cost, review date, promotion criteria, and pre-registered removal row before landing the warning-only detector. Do not add a second landing gate or persistent state.
