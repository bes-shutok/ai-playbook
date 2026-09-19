# Backlog: learn/done workflow updates plan r5 review residuals

Status: open
Priority: medium

Workflow: backlog
Source: review r5 (blind correctness-completeness certification round) of docs/plans/2026-09-16-learn-done-workflow-updates.md, 2026-09-16. The round reported ready=yes with zero blocking findings at the round cap, so these non-blocking findings are backlogged per the capture rule instead of forcing a sixth review round. Full detail in docs/reviews/2026-09-16-plan-review-learn-done-workflow-updates-r5.md.

## Findings to fold (fold at execution start if a re-cert fires, else fix with the plan's execution)

1. (Medium, quality#edge-case-unpinned-holder) done Step 0 Variant B documents only the pinned-holder branch. When no long-lived process is identifiable, the helper's PPID default records the dying one-shot shell, and dead-holder recovery reclaims the lock after the default 5s grace, silently voiding the origin-2 preserved-lock criterion for that branch. Fold: Variant B gains an explicit unpinned-branch warning plus the operator stale-clean escape.
2. (Low, testing#unpinned-acceptance-criteria) G1/G6 pin census: the `Status: open` / `Priority: high` creation marking and the Variant B interruption-cleanup obligation have no gate pin, so the plan's "every acceptance criterion maps to a named gate" claim overstates. Fold: add the two missing pins.
3. (Low, consistency#stale-cross-reference) execute-plan SKILL's anti-pattern row "done is the only commit path during Phase 1" carries an exclusivity form of the retired learn-never-commits contract and sits outside the plan's G10 four-file sweep. Fold: reword the row to the split boundary or add the file to the sweep.
4. (Overflow nits) the Gist example depicts creating the already-existing origin-2 backlog file (rename the example date or mark it as the witness that motivated the item); the G9b fixture skips temp cleanup on the fail path (wrap in a cleanup trap).

## Notes

- The plan file itself is digest-bound to r5 (source_digest 6699802656f15a0e1ded1be1cf1e9cd482dfa47adba24d662f5509220fa16d94); folding any of these changes the digest and requires a fresh certification round per the plans skill's fold rules.
