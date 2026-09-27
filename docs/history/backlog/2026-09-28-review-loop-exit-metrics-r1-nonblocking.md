# 2026-09-28 review-loop-exit-metrics r1 non-blocking findings

Priority: Low
Status: open
Origin: docs/history/plans/completed/2026-09-28-review-loop-exit-condition-metrics.md (r1 review, ready=yes, 0 blocking / 5 non-blocking; staging record docs/reviews/2026-09-28-code-review-review-loop-exit-condition-metrics-r1.md)

## Driving force

The r1 review round exited blocking-clean by the blocking-only exit rule; these ordinary findings are recorded, not chased with new rounds.

## Findings

1. N1 plan Validation Commands item 8: `grep -qF "--metrics-markdown"` parses the pattern as an option; the pin needs `grep -qF -e "--metrics-markdown"` to be runnable as written.
2. N2 summarize_review_stats.py: per-band ready-rate Markdown column dumps raw floats while the overall table and cap shares use two-decimal formatting.
3. N3 summarize_review_stats.py: blocking counts record 0 for legacy counts-only sidecars; the caveat lives only in a docstring, not in the report legend.
4. N4 maintenance SKILL.md + script: the rider's `<report-home>` is undefined for metrics and `_atomic_write_private` does not mkdir parents, so a fresh tmp fails the metrics write (fail-open; section never lands).
5. N5 review-loop/plans wording: the personal strict-package sentence sits under review-loop's "no new mechanical gate" advisory label while review-plan/execute-plan render it mechanical; plans' Ready-for-execution cap-closure exception stays class-unqualified (plan-authored text, executed verbatim).
