# Backlog: modern-plan cap-closure test arm's fixture recipe omits post-fence gate obligations

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: correctness

## Problem

Task 1's fixture recipe says every CapClosureReadinessTest arm keeps sidecar and filename dates below the fences, but `test_gate_accepts_cap_closure_on_modern_plan_with_structural_gates` deviates (dates on/after `DECISION_MARKER_MIN_DATE`, example `2026-09-26`). A post-fence date silently un-exempts gate families the recipe never mentions for this arm: the four `V1_EXTENDED_REQUIRED_FIELDS`, the `record_kind` fence, the four Markdown freshness meta lines, the Review Scope gate (from 2026-09-09), and the plan-structure plus classification probes (from 2026-09-19). Measured with the plan's own recipe, the arm fails at the sidecar schema gate ("missing extended field 'review_mode'"), not at the verdict or trailer reasons its mechanism assumes, so a faithful implementation cannot reach GREEN without improvising fixture machinery.

## Observed versus expected

- Observed: r7 testing worker re-measured the failure string directly; correctness-completeness independently mapped the five fence families (two deduplicated findings, both Low).
- Expected: the recipe carves out the modern-date arm with one sentence: its sidecar additionally carries the four extended fields and `record_kind`, its round Markdown Metadata carries the four freshness lines, and its plan bytes carry a well-formed `## Review Scope` section and a classification-tagged task item; or the example date becomes exactly `2026-09-08` (only the trailer probe fires).

## Suggested fix

Apply the recipe carve-out (or the date change) to Task 1 before execution, or to the landed test in a follow-up.

## Environment

r7 execution-time re-cert round, 2026-09-27; deferred per the backlog-deferral default.
