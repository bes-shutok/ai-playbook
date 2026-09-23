# Backlog: dfm r6 residual — boundary gate misfiled under Task 2 gates comment

- Backlog origin: docs/reviews/2026-09-23-plan-review-plan-driving-force-and-gist-tldr-metadata-r6.md F1 (Low, non-blocking, deferred)
- Driving force: external (execute-plan 2026-09-19-plan-driving-force-and-gist-tldr-metadata r6 re-cert deferral default)
- Status: open

## Problem

In `docs/plans/2026-09-19-plan-driving-force-and-gist-tldr-metadata.md` Validation Commands, the boundary gate `grep -q "declared driving force that contradicts" "$REV"` (sixth blocker family, from the r5 F1 fold) sits inside the block commented `# Task 2 gates: authoring blueprint fills both, deviation registered.`, whose other gates all target `$TMPL`. Task 3's witness bullet claims only "the three dedicated Task 3 greps", so a coverage audit either concludes the r5 F1 fold is unwitnessed or misattributes a `$REV` gate to Task 2. No functional impact.

## Suggested fix

Move the boundary gate below the `# Task 3 gates:` comment (or add a dedicated comment above it) and update the Task 3 witness bullet to "the four dedicated Task 3 greps (findings list, default pricing, contradiction pricing, boundary sixth family)". Only applies at the next natural edit of the plan (retrofit rule; the plan is archived post-execution, so this likely lands as documentation-only guidance or is closed as moot).
