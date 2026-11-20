# Backlog: the landed retirement pass has never fired while the memory index reads eleven times over its trigger (operator-decision request via the audit lane)

- **Filed:** 2026-11-13, 24h session-pattern harvest learn run (learn Step 1.9 project-issue capture; filed per the memory-index-audit lane's Filing rule)
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Class:** fix-class
- **Origin class:** self-serving (audit-lane filing; the witnessed defect is this workspace's own index, not a consumer project's)
- **Surface:** the memory-index-audit lane file (`docs/maintenance/recurring-tasks/memory-index-audit.md`, the Retirement pass member) and the memory-write convention home (`agents/skills/maintenance/zcode.md`)
- **Cluster:** docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md (same index surface; that row's retirement-pass design landed executed d7b39fe425ee7ee2958c675af56a3d4dd9f5b5c1; this row files the execution request the lane's own Filing rule prescribes)
- **Investigate disposition:** entry emission skipped; the verdict rests on a recorded instrument, the audit lane's Filing rule (an operator-gated lane run with a dry-run gate, never a dispatch entry)

## Observed versus expected

**Observed:** (measured 2026-11-13 ~02:05 WET): the memory index reads 883 lines and about 227 KB; the retirement pass member's trigger is a measured byte count above the 20,000-byte proxy target, and the whole-load witness truncates at load (the warning fires in every session; older tail records fall out of loaded context). The pass member has not run since its landing run, and the index grows by roughly 25 to 30 records per day, so the trigger has been standing red for days with no lane cadence firing it. A pass that exists but never runs does not bound the growth the consolidation chartered.

**Expected:** per the lane's Filing rule this row requests the operator approve a retirement pass run inside a lane-quiet window (the pass retires terminal records only under its standing rule; the dry-run gate requires per-row operator approval before any store mutation; live markers, pending re-arms, and in-doubt entries stay untouched). The row also states the open question for the authoring lane: whether the lane cadence needs a wiring change so a standing-red trigger actually fires, since the arm's design already landed.

## Reproduction evidence (trimmed)

- Executed 2026-11-16 ~11:55 WET by the dispatched audit-lane run: the standing Retirement pass member fired on its trigger (255,134 B) and retired 486 terminal records (364 with git-verified landing homes, 122 time-superseded one-shot scheduling records; no live marker, feedback line, or in-doubt entry touched); index now 122,454 B / 503 lines, still over the 20,000 B target, so the second-window request below stays live. Discrepancy for the operator: this row reads a dry-run gate onto the pass, while the pass member's own text carries none (the dry-run gate lives in the operator-approved consolidation run's prune arm); the full pre-image is digest-verified at the store's dated backup sibling and one command restores it if the operator rules the pass unauthorized.
- Measured 883 lines / 227,024 bytes at 2026-11-13 ~02:05 WET; the truncation warning present in every session's injected context across the witnessed window; the 20,000-byte trigger and the pass member verified in the lane file before filing.
- Re-measured 2026-11-14 ~02:05 WET (second harvest pass): 917 lines / ~227 KB; the window's fired one-shot armed lines (the previous afternoon's author carriers scheduled 20:43 and 22:00) still read `scheduled not executed` with no fire-outcome corrections appended; the pass remains unfired.

## Environment context

The lane file and convention are in this repository; the index itself lives in the runtime memory store outside this repository (referenced here by role, never by machine-specific path).

## Why not fixed now

Store mutation is operator-gated by the pass's own dry-run gate, and the cadence-wiring question is an authoring-lane design choice; both exceed this harvest run's authority.
