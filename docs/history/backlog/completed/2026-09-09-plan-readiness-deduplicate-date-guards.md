# Deduplicate the gated-probe date guards and reason wrappers in plan_readiness.py

- **Status:** done
- **Workflow:** pre-plan backlog item; promote via the `plans` skill when scheduled, move to `backlog_completed_dir` on completion.

## Problem

`evaluate_readiness` in `scripts/plan_readiness.py` (steps 6 and 7) duplicates the same shape twice, once per gated probe (`decision_marker_problem`, `review_scope_problem`): a sidecar-date guard (`re.fullmatch(r"\d{4}-\d{2}-\d{2}")` + lexicographic `>= MIN_DATE`), a shared conditional decode of the plan bytes, and a reason wrapper embedding the probe output plus round number and date. The two blocks can drift on future edits; a third gated probe would copy the shape a third time. A tiny helper (date-guard predicate + reason wrapper) would make the shared malformed-or-missing-date exemption semantics structural instead of copy-pasted.

Evidence: code review r1 of branch `2026-09-08-plan-authoring-tooling-polish`, design-simplicity worker overflow finding (pattern `simplification#shrink`, anchor "evaluate_readiness date guards", Low, strong-evidence).

## Location

`scripts/plan_readiness.py`, `evaluate_readiness`, the `trailer_gated` / `scope_gated` blocks (the step 6 and step 7 comments).

## Suggested fix

Extract a shared helper, e.g. `_gated_probe_problem(payload, min_date)` returning the exact date predicate, and a reason-wrapping helper taking the probe name/output/round/date; keep the r2-F2 decode-sharing constraint (decode only when at least one guard fires; an undecodable plan whose round is date-exempt must not newly fail).

## Severity and source

- Severity: Low
- Source: `docs/reviews/2026-09-09-plan-authoring-tooling-polish-code-review-r1.md`, round r1, overflow manifest (F12 deferral)
- Why not fixed now: deferred by standing instruction during the r1 fix round: no structural refactor of a working gate late in a fix round; the residual is drift risk only, no behavioral defect.
