# Backlog: rolling-log prune receipts accumulate in the log files and push every read past tool output caps

- **Filed:** 2026-11-19, 24h session-pattern harvest learn run (learn Step 1.9 project-issue capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** session-witnessed recurring waste (five sessions in one 24h window)
- **Skill/step:** the `PLAN-PROMPTS-PRUNE:` / `EXEC-PROMPTS-PRUNE:` receipt append duty (the Prune rule in `docs/history/backlog/PLAN-PROMPTS.md` Standing rules, mirrored in `docs/history/backlog/EXEC-PROMPTS.md`) and the receipt-retention contract that keeps every historical receipt in the log file itself
- **Cluster:** docs/history/backlog/2026-11-10-known-red-gates-retriage-tax.md (same rolling-log surface: the advisory-size known-red these sessions re-triage)

## Problem

The prune-receipt append duty keeps every historical landing receipt inside the rolling log files. `docs/history/backlog/EXEC-PROMPTS.md` reached 309.8KB, past the 262KB tool-output hard cap, and `docs/history/backlog/PLAN-PROMPTS.md` carries a receipt preamble plus per-entry receipts across 647 lines. Five sessions in the window paid for it directly: full-file and head-range reads of the exec log persisted as oversize outputs (309.8KB, 78.8KB, 71.6KB, 50.4KB), each consuming a turn and a re-read at narrower range, and the oversize advisory itself was re-triaged per session. The receipts are durable landing records (the prune audit consumes them), so they cannot simply be dropped; the cost is their location, not their existence.

## Expected

Receipts stay durable and machine-checkable while the live entry body of each log fits comfortably under tool caps: either receipts relocate to a dedicated receipt ledger (one append-only file the prune audit also reads), or the Standing rules add a compaction duty that moves receipts older than a bounded window to the ledger, with the audit's input surfaces extended in the same change.

## Suggested direction

Plan-worthy because the relocation changes the prune audit's inputs (a guard-bearing checker) and has open design choices: single ledger versus per-log ledgers, the retention window, and whether the audit gains a `-ledger` operand or reads both files by convention. The smallest arm is one append-only receipts file per log plus a Standing-rules amendment naming it as the receipt home and an audit input; no entry-body change.

## Evidence

- Oversize persisted reads of the exec log witnessed in five window sessions (session ids on file in the harvesting run's investigate entry; the largest single read 309.8KB).
- `wc -c docs/history/backlog/EXEC-PROMPTS.md` at filing: over the 262KB cap; the advisory appears in at least two sessions' gate output verbatim.
- The prune-audit (`scripts/check_prompt_log_origins.py --prune-audit`) greps receipts from the log files, so any relocation must migrate its input contract in the same change.

## Dedup probe

Searched open backlog for prune-receipt relocation, log-size, and oversize-read coverage: the known-red-gates row records the oversize advisory as a re-triaged known-red but owns the re-triage tax, not the size cause; no row owns receipt relocation.
