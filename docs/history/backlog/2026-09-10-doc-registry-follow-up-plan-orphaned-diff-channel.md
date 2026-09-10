# Follow-up plan still pins the retired `--diff` channel (r4 F9)

Status: open
Workflow: backlog

## Problem

The certified, unexecuted follow-up plan `docs/plans/2026-09-09-doc-registry-freeze-move-licensing-fold.md` references the retired `check-writes --diff` channel in its Terms, Why, Before/After, fixture spec (line ~116), and implement bullet (line ~118); five-plus references. The `--diff` flag was removed in the r2 fix round of `2026-09-08-doc-ownership-lifecycle` (it now exits 2, pinned by `test_removed_diff_channel_fails_closed`); staged moves are observed via the porcelain stdin channel instead. Executing that plan as written produces an unrunnable fixture spec against the current validator.

Evidence: `grep -n -- '--diff' docs/plans/2026-09-09-doc-registry-freeze-move-licensing-fold.md` → lines 12, 34, 36, 38, 116, 118.

## Why not fixed now

The follow-up plan is peer-owned, certified at its own digest, and unexecuted; editing a certified plan body outside its own execution flow is out of scope for the r4 receiving-review pass (source: review staging doc `docs/reviews/2026-09-10-2026-09-08-doc-ownership-lifecycle-code-review-r4.md`, finding F9; disposition agreed with the round instructions, 2026-09-10).

## Suggested fix

Before executing the follow-up plan, re-derive its staged-move premise to the porcelain stdin channel: the successor-row licensing fixture becomes a `check-writes --stdin` fixture fed `R  old -> new` porcelain lines (note: since r4, the porcelain channel already gates the rename old side as a deletion and licenses the registered new side, so part of the follow-up's premise is now covered by the main validator; re-scope the fixture accordingly, possibly folding the successor-row licensing test into the existing selftest block, and mark the follow-up superseded with a registry row if fully absorbed).

## Source

- Staging: docs/reviews/2026-09-10-2026-09-08-doc-ownership-lifecycle-code-review-r4.md, round r4, finding F9 (Medium, non-blocking)
- Recorded: 2026-09-10, r4 receiving-review pass
