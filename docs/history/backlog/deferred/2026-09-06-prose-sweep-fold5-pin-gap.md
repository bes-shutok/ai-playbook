# Backlog: prose-sweep fold 5 lacks a validation pin

Status: open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)

Origin: docs/reviews/2026-09-06-certified-plan-prose-residue-sweep-code-review-r1.md (finding 1, testing lens, Low, non-blocking)

## Finding

The `## Validation Commands` block of `docs/plans/2026-09-05-certified-plan-prose-residue-sweep.md` pins folds 1-4 (positive `-eq 1` pins plus superseded-span guards) but has no positive pin and no superseded-span guard for fold 5 (the Task 1 second-checklist-bullet rationale reword: new span `the entry count depends on how many parsing passes`, old span `classifies \`legacy-panel-mode\`` / `exactly ONE entry`). A skipped, partial, or wrong fold-5 edit would still pass the block, and the plan's "each prescribed replacement text appears exactly once" correctness criterion is assertion-complete only for folds 1-4.

## Why deferred

The landed fold-5 edit was manually verified correct (new span present exactly once, old span absent), and the plan is executed; amending the validation block now would mutate the reviewed digest for zero tree effect.

## Fix when

If a successor plan ever re-opens the sweep plan's validation block (or a template rule requires assertion-complete fold coverage), add: `grep -cF 'the entry count depends on how many parsing passes' -eq 1` pin and a `! grep -qF 'exactly ONE entry'` guard to the Task 1 half.
