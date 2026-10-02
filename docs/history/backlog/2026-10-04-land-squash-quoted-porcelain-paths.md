# Backlog: land_squash.sh snapshot/restore parsing does not unquote C-quoted porcelain paths

- **Status:** open
- **Origin:** squash-landing-failure-path-guard execution review r1 (docs/reviews/2026-10-04-exec-review-squash-landing-failure-path-guard-r1.md) finding 3, non-blocking
- **Driving force:** robustness - paths with spaces or non-ASCII bytes arrive C-quoted from `git status --porcelain` and are not unquoted before the helper's per-path restore, so such a path fails its restore into the declared exit-2 unrestored arm (fail-safe, never silent); the pre-refusals stay consistent because both sides quote identically; the class is unwitnessed (all fixture paths are quote-free)

## Outcome

The helper's snapshot and restore-set parsing unquotes C-quoted porcelain paths (or switches the plumbing to `-z` formats) so quote-bearing paths restore per-path like any other, with a fixture covering a space-bearing path through the merge-failure restore.

Ship when: a space-bearing path restores per-path in the merge-failure fixture; no regression in the 16 helper tests.
