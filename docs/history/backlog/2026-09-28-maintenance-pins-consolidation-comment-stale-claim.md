Status: done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-pins-consolidation-comment-narrowed-claim.md, squash main 6251d8e2, exec review r1 ready=yes zero blocking)
Priority: high
Workflow: backlog
Class: formal (stale explanatory comment above a pin block; no pin keys on the comment text)
Driving force: code quality

# Pins-suite consolidation comment still claims the pre-work gate paragraph was retired

**Exact location:** `scripts/check_maintenance_pins.sh`, the comment block above the worktree-first consolidation pin group (the paragraph beginning "The 2026-09-28 consolidation replaced the blueprint's per-execution worktree paragraph and its per-run pre-work gate paragraph with references").

## Problem

The comment repeats the over-broad retirement claim that review round r4 (finding F8) already corrected in the worktree-first deviation entry: the consolidation replaced the per-execution worktree paragraph with references, but the per-run pre-work gate paragraph was rewritten to post-transfer-in scope, not retired with it. The comment text is the kind of prose a future pin author reads as ground truth when re-keying spans, so the stale claim can propagate into a wrong pin expectation. Comment-only: no pin keys on this text, and the suite is green with it present.

## Observed versus expected

- Observed: the comment says both paragraphs were replaced with references and the payload spans retired.
- Expected: the comment matches the actual transformation (worktree paragraph replaced by reference; pre-work gate paragraph rewritten, not removed).

## Suggested fix

Reword the comment block to the narrowed claim, mirroring the F8 deviation-entry wording; comment-only edit, verify with a pins-suite run.

## Source reference

Sibling observation recorded (out of the r4 staged set) during the address pass for review round r4 of docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r4.md, then re-verified against the working tree (comment block present verbatim at the pinned script's consolidation section); captured here per learn Step 1.8 because the address log is a gitignored session record and must not be the only record. Why not fixed now: content edits are outside this iteration's authorized review-fix commit scope. Capture hygiene: scan-public-hygiene --files pass.

Dedup probe: searched the open backlog corpus for consolidation comment, pre-work gate, and pin-block comment claims; the closest item is the s15 re-key item (a different pin, keyed anchor, not comment prose); no overlap.

Origin class: self-serving
