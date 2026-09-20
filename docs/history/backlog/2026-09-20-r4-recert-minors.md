# Backlog: r4 re-cert minors (merge-landing-lock-grouping)

- Status: open
- Origin: Phase 3 r4 targeted re-cert (fold diff 567451c1...f7ecd76c); verdict backlogged-candidates, zero blocking
- Driving force: the r3 rollback duty hardened one arm; these minors close the remaining interpreter-dependent edges and the unpinned rollback literals.

## Items

1. Route a refused inverse-CAS rollback explicitly (release, keep worktree/branch, strand-report, never rewrite) even though the lock protocol closes the window.
2. Pre-commit revert duty: add index hygiene (unstage the task's paths) so the "no half-landed bytes" claim is not interpreter-dependent.
3. Next pin generation: needles for the r3 rollback literals (`git reset --soft <pre-commit-tip>`, the pathspec restore, the inverse-CAS rollback).
4. Move the "record the pre-commit tip" duty into the landing sequence rather than the verification-failure branch (placement nit).
