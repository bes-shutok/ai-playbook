# Backlog: r4 re-cert minors (merge-landing-lock-grouping)

Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; rollback-duty polish (lock protocol already closes the window). Revive on the lock protocol is next reworked, or a project-priority-profile change.)

Status: rejected (2026-09-26; unwitnessed hardening: rollback-duty hardening for a window the landed lock protocol already closes)
- Origin: Phase 3 r4 targeted re-cert (fold diff 567451c1...f7ecd76c); verdict backlogged-candidates, zero blocking
- Driving force: the r3 rollback duty hardened one arm; these minors close the remaining interpreter-dependent edges and the unpinned rollback literals.

## Items

1. Route a refused inverse-CAS rollback explicitly (release, keep worktree/branch, strand-report, never rewrite) even though the lock protocol closes the window.
2. Pre-commit revert duty: add index hygiene (unstage the task's paths) so the "no half-landed bytes" claim is not interpreter-dependent.
3. Next pin generation: needles for the r3 rollback literals (`git reset --soft <pre-commit-tip>`, the pathspec restore, the inverse-CAS rollback).
4. Move the "record the pre-commit tip" duty into the landing sequence rather than the verification-failure branch (placement nit).
