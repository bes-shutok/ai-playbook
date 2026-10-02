# Backlog: archive-egress keying misses nested non-state subdirectories under a plans root

- **Status:** open
- **Origin:** execution review r1 (docs/reviews/2026-10-03-exec-review-archive-ceremony-gate-universal-r1.md) finding 2, non-blocking
- **Driving force:** correctness gap - deletions and rename-sources key on top-level plans-root detection, so a plan file inside a non-state nested directory under docs/history/plans/ can be deleted or renamed out ungated, diverging from the Terms' plans-root letter

## Outcome

Egress source detection covers plan files at any depth under a plans root outside the state subdirectories, with a nested-dir boundary test.

Ship when: a nested deletion refuses; the test suite pins it.
