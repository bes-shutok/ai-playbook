# Backlog: landing-origin-row-deletion-registry-witness-sweep certification residuals (entries note-prose dead citations)

- **Filed:** 2026-11-15 (authoring lane closeout; durable capture per the certification-residual routing)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** certification residual (pre-existing debt adjudicated out of the plan's scope at review r3 and re-adjudicated at r6)
- **Class:** fix-class (citation re-point, lesson-312 sweep discipline)

Cluster: docs/history/plans/2026-11-14-landing-origin-row-deletion-registry-witness-sweep.md (the covering plan, execution pending)

## Problem

Three dead citations of the deleted living plan path `docs/history/plans/2026-11-12-maintenance-indefinite-operation-stop-gaps.md` sit in `scripts/machinery_registry.json` entries note prose (the entries for duty ids carrying the stop-gaps plan's admission and removal history; occurrence-measured 2026-11-14, count 5 total of which 2 belong to the duty family the covering plan's Task 1 re-points and 3 are this row's residual). The machinery inventory check validates witness refs only, so the check is green after the covering plan's Task 1 while these three note-prose citations stay dead - the lesson-312 defect class the covering plan's Task 2 sweep text lands against, applied to the one family that predates it.

The covering plan's scope boundary explicitly excludes them (measured, adjudicated at review r3: pre-existing debt, not an expectation error), and the r6 terminal reflection routed them here as the durable capture.

## Fix direction

A warning-first, prose-only re-point in the same change class as the covering plan's Task 1: the three note mentions re-point to the completed twin `docs/history/plans/completed/2026-11-12-maintenance-indefinite-operation-stop-gaps.md`, no validator or gate changes, inventory check stays green, pins suite green. The covering plan's Task 2 sweep text (once executed) is the standing rule future deletions follow; this row is the one-time catch-up for the pre-existing instances.

## Evidence

- Occurrence measurement 2026-11-14 (occurrence count via fixed-string grep): living stop-gaps path 5 in `scripts/machinery_registry.json`, decomposed 2 (removals row: witness ref + note citation; covered by the plan's Task 1) + 3 (entries note prose; this row).
- Review r3 blind-probe record and r6 terminal reflection paragraph (staging series for the covering plan).
