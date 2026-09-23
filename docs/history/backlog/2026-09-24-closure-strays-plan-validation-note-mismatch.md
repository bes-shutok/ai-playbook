# Backlog: closure-strays disposition plan's authoring-time execution note mischaracterizes pre-execution gate states

Captured: 2026-09-24 (source: plan-review r2 of docs/plans/2026-09-24-closure-strays-disposition-routing.md, finding F1, Low non-blocking; round verdict ready=yes zero blocking, so the finding was captured instead of folded per the clean-round precedent)
Status: open
Priority: low
Workflow: backlog

## Problem statement

The plan's Validation Commands closing paragraph ("Authoring-time execution note:") states that V2, V3, and V5 "pass vacuously or trivially" until the routing tasks create their targets, and that "each routing task runs its own subset (V5 after the move, V3 fragment after the row append)". Measured against the gate scripts, both claims are wrong: V2 exits 1 pre-execution (its `test -f` fails on the absent completed target) and V3 exits 1 pre-execution (identity count 0), so both fail closed rather than pass; and no task checklist in Tasks 2-7 encodes a V3 fragment step (each runs only V5 after the move). An auditor running the whole block early would see the fail-closed V2/V3 exits and could misread them as a defect; duplicate-identity rows are actually caught only at Task 8's whole-block V3 (per-task V5 does parse the registry, so malformed rows still surface before commit).

## Exact location

- `docs/plans/2026-09-24-closure-strays-disposition-routing.md`, Validation Commands section, the "Authoring-time execution note:" paragraph after the V6 block.
- Review record: `docs/reviews/2026-09-24-plan-review-closure-strays-disposition-routing-r2.md` finding F1 (consistency#validation-note-mismatch, Low, blocking=false, confidence verified).

## Suggested fix

At the plan's next natural edit (or immediately before its execution dispatch), rewrite the note to state that V2 and V3 fail closed pre-execution (exit 1 on the absent targets, which is the expected pre-execution state, not a defect), drop the unencoded per-task V3-fragment claim (per-task coverage is V5 only; V3 runs at Task 8), and keep the V1/V4/V6 authoring-time claims which were measured.

## Severity and source reference

Low. Source: plan-review r2 finding F1 (workers contract-docs + testing, verified by direct gate execution). Capture hygiene: public-hygiene scan pass at authoring.

## Why not fixed now

The round was already clean (ready=yes, zero blocking); folding a non-blocking Low would change the certified plan bytes and force a full re-certification round. The affected text is an authoring audit note, not a gate: Task 8's whole-block run is the only prescribed early-block execution point and its gates are self-explanatory on failure.

Driving force: docs (accuracy of authoring notes), secondary: code-quality
