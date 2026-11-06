# Backlog: Deterministic anchor for the archive-twin battery family under a repo-inside TMPDIR

Driving force: robustness

Captured from: intermediate task review (Task 1, contract lens) of the run `review-staging-archived-plan-source-identity`, worktree branch `2026-11-06-review-staging-archived-source`, 2026-11-06.

The Task 1 archive-twin battery family relies on the battery tmp root not being inside a git repository; under a `TMPDIR` inside a repo, `_coverage_archive_twin`'s anchor would resolve to that repo and the trailing-twin assertions would fail spuriously. Optional hardening: `git init` a throwaway repository at the fixture root (the same mechanism the Task 2 identity-stability pin uses), making the anchor deterministic regardless of host TMPDIR placement.
