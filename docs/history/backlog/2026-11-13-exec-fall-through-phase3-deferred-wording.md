# Backlog: decisions.md follow-ups from the exec-plans-segment-fall-through execution review

- **Filed:** 2026-11-13, execute-plan Phase 3 of the exec-plans-segment-fall-through execution run (commit 2bb10c9b9); three lens workers returned blocking-clean with these valid non-blocking findings, captured here per the Phase 3 exit contract instead of a byte-changing fix round
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** wording-hygiene (all findings are one-clause text tightenings in agents/skills/maintenance/decisions.md; no behavior change)
- **Cluster:** docs/history/backlog/2026-11-19-authoring-dry-exit-conversion-fall-through.md (the authoring-side fall-through gap this row's exec-side clause mirrors; filed 2026-11-19)
- **Skill/step:** `agents/skills/maintenance/decisions.md` (the Exec-mode selection rule bullet's fall-through clause landed by docs/history/plans/completed/2026-11-13-exec-plans-segment-fall-through.md Task 1; the continue-loop condition Witnesses sentence)
- **Origin:** docs/history/plans/completed/2026-11-13-exec-plans-segment-fall-through.md (the covering plan's completed twin; this row carries its Phase 3 deferred findings)

## Problem

Four non-blocking wording defects survived the execution review (all verified fresh from disk, none blocking):

1. The payment-span replacement at the in-session authoring chaining bullet says "when the condition does not hold" with no antecedent for "the condition" in that leg; the continue-loop condition's home paragraph declares other sites reference it by name, and this site no longer does. Fix: restore "when the continue-loop condition does not hold" (+14 bytes, priced per the anti-growth payment rules).
2. The landed clause says "when both segments resolve empty" while the bullet's Ordering contract defines three segments and the covering plan's Terms say "all resolve empty". Fix: "when all segments resolve empty" (-1 byte).
3. The clause says "the switched lane is starved" where the covering plan's Terms say "the switched authoring lane"; the exec-lane reading is vacuously true at that point. Fix: "the switched authoring lane" (+10 bytes) if any wording pass touches the clause.
4. The continue-loop condition's Witnesses sentence cites two dead paths (the deleted backlog row `2026-09-28-maintenance-autonomous-pipeline.md` and the superseded living plan path); the durable citations live in `docs/history/plans/completed/2026-09-28-maintenance-autonomous-pipeline.md`. Pre-existing rot concentrated by the P1 payment span, not introduced by it. Fix: repoint both citations to the completed twin per the covered-row citation rule.
5. Secondary (lower confidence, capture only): the P9 payment deleted the D-2 panel-route provenance pointer whose durable home is the completed 2026-10-06 two-mode-loop-policy plan's Terms (the directives home's D-2 record carries no panel-route line); and "consulted before any terminal exit" reads broader than the both-segments-empty stand-down it scopes (vacuous on the other D-18 exits).

## Expected

A single priced wording pass over decisions.md applies fixes 1-4 with the byte-payment duty (equivalent-bytes deletion in the same change, pins-quoted literals and pins-counted tokens avoided), and decides 5 explicitly. No behavior change; the pins suite and budget gate stay green.
