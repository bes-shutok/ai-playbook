# Pay-trim guidance thinning in doing-code-review Step 4.2 family

Cluster: review-sop-target-lifecycle exec r1 residuals

Driving force: docs/history/plans/completed/2026-10-28-review-sop-target-lifecycle.md (exec r1, landed 2026-11-01)

Two Low, non-blocking findings from the exec r1 fresh-adversarial round over the procedure-applicability change (commit 47941d13a). Both observe the plan-mandated pay-for-growth trims, not defects in the new bullet; captured rather than fixed because restoring bytes would breach the byte-balance the plan requires.

- docs#1 (Low): the error-handling trim in Step 4.2 (`agents/skills/doing-code-review/SKILL.md` ~line 313, 213 B) removed the only concrete outcome signatures for the retained "trace what the caller does with each outcome" directive (safe-default masking infrastructure failure; throw propagating to a handler). Operative rule survives verbatim; guidance thinned.
- docs#2 (Low): the 4.11 Rationale line (~line 476, 79 B) now restates the rule ("Only report EXISTING debt when the PR significantly compounds the problem.") instead of justifying it, partially duplicating the EXISTING-debt bullet above.

Fix shape when picked: reword the retained sentences to carry one concrete signature each, paying the bytes elsewhere; or accept as-is and close with a note that the thinning is the priced trade. Watchlist only; no witness of misreview yet.
