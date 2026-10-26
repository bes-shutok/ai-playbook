# Backlog: distinguish cross-run recurrence from adjacent workflow follow-ups

- **Filed:** 2026-10-26, operator-directed assessment of workflow improvement and recent repository history
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (current evidence shows many follow-ups but does not prove the same root cause recurred across separate runs; below the active release, lock, and resource-cleanup incidents)
- **Origin class:** self-serving (the affected workflow is this repository's shared agent process)
- **Class:** fix-class
- **Driving force:** simplicity (primary), efficiency (secondary)
- **Skill/step:** `agents/skills/investigate/SKILL.md`, Stage 2 issue archaeology and Stage 3 possibility space
- **Source:** 2026-10-26 operator assessment of whether recent workflow landings represent improvement or a repeat-fix loop
- **Dedup probe:** searched open backlog rows and recent plans for investigation recurrence, cross-run follow-ups, and skill-prose duplication. `docs/history/backlog/2026-10-25-review-plan-nonconvergence-recovery.md` is covered by `docs/history/plans/2026-10-25-review-plan-nonconvergence-disposition.md` and concerns recurrence within one plan review; completed plan `docs/history/plans/completed/2026-09-18-execute-plan-phase3-process-reconciliation-trigger-and-archive-safety.md` tracks recurrence within one execution run; deferred `docs/history/backlog/deferred/2026-10-08-investigate-renewal-trigger-on-row-rescope.md` concerns re-investigating a materially changed origin; `docs/history/backlog/2026-10-19-dated-record-stamp-audit-arm.md` records a repeated date-stamp error after a lesson landed but proposes a narrow read-only audit for that field family; `docs/history/backlog/2026-10-22-adhoc-landing-sentence-omits-land-squash-helper.md` records a repeated landing-route omission but owns that specific consumer-skill wording; open `docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md` already owns cross-file prose duplication and source-of-truth hygiene. None covers the general cross-run comparison of a new incident with the outcome of a prior landed fix.

## Problem

The October 5–26 history review found several follow-ups soon after large workflow landings. Those records mix new capabilities, residual review findings, and operational defects; timing alone does not show that a fix reintroduced the same bug. One adjacent example is the October 25 closeout landing (`058bbb7e0`) followed on October 26 by `3005cda9b`, which added release of the acquired done lock on setup classification stops. That follow-up is a missing recovery complement in the same workflow area, not evidence that the original lock fix was reintroduced. The review-round and execute-plan recurrence rules compare evidence within a run. `investigate` Stage 2 traces a mechanism's introduction and dependents, but does not explicitly require deciding whether a later report repeats a previously fixed root, is a missing complement, or is a separate neighboring issue. This leaves the operator's cross-run “are we looping?” question to ad hoc synthesis.

## Expected

For a new backlog item that plausibly overlaps earlier workflow work, the investigation compares its evidence with relevant earlier backlog rows, plans, and later commits. Record in the existing Orientation or recommendation whether it is a recurrence after a fix, a regression introduced by the fix, a missing complementary path, or a separate root. A recurrence claim names the earlier fix and later witness; an inconclusive comparison says so. Reuse existing repository history and prompt-entry fields; add no ledger, telemetry, validator, gate, or required ceremony. If current Stage 2 already supports this at adequate cost, record that disposition and leave the skill unchanged.

## Why not fixed now

The recent history reviewed so far does not establish that the closeout and lock follow-ups share a root. The investigation should verify whether a specific cross-run decision is missing and whether a small Stage 2 instruction would improve that decision before any skill edit is chosen.
