# comparability gate needle hardening

Status: open
Priority: low
Class: testing
Origin class: deferred-review-finding
Cluster: review-loop validation-block coverage
Driving force: review (execute-plan Phase 3 r1 of docs/history/plans/2026-11-17-comparable-round-residual-polish-group.md, testing lens)

## Summary

The comparability plan's Validation Commands block leaves four prescribed fragments without a discriminating pin, so a future re-execution or partial amendment could land a weakened span while every gate stays green. Clustered findings F1-F4 (staged ids 1-4) of the r1 focused review:

- F1 (Medium): the Span B qualification "After a baseline exists" -> "After a comparable baseline exists" has no pin in either direction (two pins would close it: expect_absent 'After a baseline exists' + expect_count 'After a comparable baseline exists' 1 on review-plan SKILL.md).
- F2 (Medium): the Span B skip clause's pivot ("when the current round is not a comparable round") and tail ("and the loop continues one round under the same guards as the baseline-establishment sentence") are unpinned; a dropped continuation clause passes (pins: expect_count of each fragment 1).
- F3 (Low): G1's presence pin is a strict prefix of the prescribed phrase; the possessive tail "'s staged findings" is unpinned; a truncated landing passes G1.
- F4 (Low): G6's two absent pins are evadable by a rephrased appositive restatement (for example "which runs over the latest comparable rounds") while the count-1 presence pin passes - the exact drift class the audit-note origin reported.

Current tree is verified correct byte-for-byte; this row hardens the durable regression gate only.

## Expected

The listed pins join the block (or a successor gate surface) the next time the plan's validation block is legitimately amended; no mid-run gate edits.

## Evidence

Worktree 2026-11-17-comparable-round-residual-polish, r1 staging record .ai-playbook/reviews/2026-11-19-comparable-round-residual-polish-group-code-review-r1.md, measured substring checks recorded by the testing lens.
